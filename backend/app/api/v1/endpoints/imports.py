"""
Import API endpoints for file upload and data import.
"""

import os
import uuid
import tempfile
import logging
from pathlib import Path
from typing import List
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session

from app.core.database import get_db

logger = logging.getLogger(__name__)
from app.models.import_job import ImportJob
from app.parsers.factory import FileParserFactory
from app.ai.factory import AIProviderFactory
from app.tasks.import_tasks import process_file_import
from app.services.import_service import ImportService
from app.services.device_detection_service import DeviceDetectionService
from app.services.product_type_learning_service import ProductTypeLearningService
from app.services.device_learning_service import DeviceLearningService
from app.services.size_learning_service import SizeLearningService
from app.services.supabase_service import SupabaseService
from app.schemas.import_job import (
    FileUploadRequest,
    FileUploadResponse,
    ImportJobCreateRequest,
    ImportJobResponse,
    ParsePreviewRequest,
    ParsePreviewResponse,
    ImportDataRequest,
    ImportDataResponse,
    ImportJobStatus,
)
from app.schemas.field_mapping import (
    STANDARD_FIELDS,
    AutoMappingResult,
    auto_map_columns,
)


router = APIRouter()


@router.post("/upload", response_model=FileUploadResponse)
async def upload_file(
    file: UploadFile = File(...),
    db: Session = Depends(get_db)
):
    """
    Upload file for import.
    Returns upload ID and presigned URL (or saves directly for simplicity).
    """
    try:
        # Validate file extension
        file_ext = Path(file.filename).suffix.lower()
        if not FileParserFactory.is_supported(Path(file.filename)):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file format: {file_ext}"
            )

        # Generate unique upload ID
        upload_id = str(uuid.uuid4())

        # Create temp directory for uploads
        upload_dir = Path(tempfile.gettempdir()) / "accusync_uploads"
        upload_dir.mkdir(exist_ok=True)

        # Save file
        file_path = upload_dir / f"{upload_id}{file_ext}"
        with open(file_path, "wb") as f:
            content = await file.read()
            f.write(content)

        # In production, would use S3 presigned URL
        # For now, return local path info
        return FileUploadResponse(
            upload_id=upload_id,
            upload_url=str(file_path),
            expires_at=datetime.utcnow() + timedelta(hours=1)
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Upload failed: {str(e)}"
        )


@router.post("/preview", response_model=ParsePreviewResponse)
async def preview_parse(
    request: ParsePreviewRequest,
    db: Session = Depends(get_db)
):
    """
    Preview file parsing without creating import job.
    Shows first N rows to verify format.
    """
    try:
        # Reconstruct file path from upload_id
        upload_dir = Path(tempfile.gettempdir()) / "accusync_uploads"
        file_ext = Path(request.filename).suffix.lower()
        file_path = upload_dir / f"{request.upload_id}{file_ext}"

        if not file_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Upload not found or expired"
            )

        # Create AI provider
        ai_provider = AIProviderFactory.create()

        # Create parser
        parser = FileParserFactory.create_parser(
            file_path=file_path,
            ai_provider=ai_provider
        )

        if parser is None:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported file format: {file_ext}"
            )

        # Parse file (limit rows for preview)
        import asyncio
        parser_options = request.parser_options or {}

        parse_result = await parser.parse(
            file_path=file_path,
            **parser_options
        )

        if not parse_result.success:
            return ParsePreviewResponse(
                success=False,
                columns=[],
                data=[],
                row_count=0,
                errors=parse_result.errors,
                warnings=parse_result.warnings
            )

        # Limit data for preview
        preview_data = parse_result.data[:request.preview_rows]

        # Extract keywords from product name for each row
        # 機種検出とサイズ抽出を実行（デザインマスター連携も含む）
        device_detector = DeviceDetectionService(db)
        product_type_learning_service = ProductTypeLearningService(db)
        device_learning_service = DeviceLearningService(db)
        size_learning_service = SizeLearningService(db)
        supabase_service = SupabaseService()

        for row in preview_data:
            # Get product name from various possible keys
            product_name = (
                row.get('product_name') or
                row.get('商品名') or
                row.get('品名') or
                row.get('製品名') or
                ''
            )

            # 商品番号（SKU）から取得（Amazonの場合はこれがデザイン番号）
            product_code = (
                row.get('商品番号') or
                row.get('商品管理番号') or
                row.get('SKU') or
                row.get('sku') or
                row.get('商品コード') or
                row.get('管理番号') or
                row.get('product_code') or
                ''
            )

            # 商品タイプの抽出（優先順位順）
            product_type_from_design = None
            design_no = None

            # デバッグ: 商品番号を確認
            if product_code:
                logger.info(f"🔍 商品番号取得: {product_code.strip()[:50]}...")
            else:
                logger.info(f"⚠️ 商品番号が見つかりません")

            # 1. 商品番号（SKU）→ ローカルDB（デザインマスター）検索（最優先）
            if product_code and product_code.strip():
                logger.info(f"🔎 商品番号でローカルDB検索開始: {product_code.strip()}")
                product_type_from_design = device_detector.get_product_type_by_sku(product_code.strip())
                if product_type_from_design:
                    design_no = product_code.strip()
                    row['extracted_memo'] = product_type_from_design
                    row['design_number'] = design_no
                    row['product_type_source'] = 'local_db_sku'
                    logger.info(f"✅ ローカルDB（SKU）から商品タイプ取得: {design_no} → {product_type_from_design}")

            # 2. 商品番号（SKU）→ Supabase曖昧検索
            if not product_type_from_design and product_code and product_code.strip():
                logger.info(f"🔎 商品番号でSupabase曖昧検索: {product_code.strip()}")
                product_type_from_design = supabase_service.fuzzy_search_product_type(product_code.strip())
                if product_type_from_design:
                    design_no = product_code.strip()
                    row['extracted_memo'] = product_type_from_design
                    row['design_number'] = design_no
                    row['product_type_source'] = 'supabase_fuzzy'
                    logger.info(f"✅ Supabase曖昧検索から商品タイプ取得: {design_no} → {product_type_from_design}")

            # 2.5. 商品番号（デザイン番号）→ 楽天SKU管理システムDB
            if not product_type_from_design and product_code and product_code.strip():
                if hasattr(device_detector, 'rakuten_sku') and device_detector.rakuten_sku:
                    logger.info(f"🔎 楽天SKU管理システムで商品タイプ検索: {product_code.strip()}")
                    product_type_from_rakuten = device_detector.rakuten_sku.get_product_type_by_design_number(product_code.strip())
                    if product_type_from_rakuten:
                        design_no = product_code.strip()
                        row['extracted_memo'] = product_type_from_rakuten
                        row['design_number'] = design_no
                        row['product_type_source'] = 'rakuten_sku_db'
                        product_type_from_design = product_type_from_rakuten
                        logger.info(f"✅ 楽天SKU管理システムから商品タイプ取得: {design_no} → {product_type_from_rakuten}")

            # 3. 商品番号（SKU）→ 学習パターンから予測
            if not product_type_from_design and product_code and product_code.strip():
                logger.info(f"🔎 商品番号で学習パターン予測: {product_code.strip()}")
                prediction = product_type_learning_service.predict_product_type(product_code.strip())
                if prediction:
                    product_type_from_design, confidence, method = prediction
                    design_no = product_code.strip()
                    row['extracted_memo'] = product_type_from_design
                    row['design_number'] = design_no
                    row['product_type_source'] = method
                    logger.info(f"✅ 学習パターンから商品タイプ予測: {design_no} → {product_type_from_design} (信頼度: {confidence:.2f})")

            # 4. 商品名 → デザイン番号抽出 → デザインマスター検索
            if not product_type_from_design and product_name:
                logger.info(f"🔎 商品名からデザイン番号抽出: {product_name[:30]}...")
                product_type_from_design, design_no = device_detector.get_product_type_from_design(product_name)
                if product_type_from_design:
                    row['extracted_memo'] = product_type_from_design
                    row['design_number'] = design_no
                    row['product_type_source'] = 'design_master_name'
                    logger.info(f"✅ 商品名から商品タイプ取得: {design_no} → {product_type_from_design}")

            # 5. 商品名 → 学習パターンから予測
            if not product_type_from_design and product_name:
                logger.info(f"🔎 商品名で学習パターン予測: {product_name[:30]}...")
                prediction = product_type_learning_service.predict_product_type(product_name)
                if prediction:
                    product_type_from_design, confidence, method = prediction
                    row['extracted_memo'] = product_type_from_design
                    row['design_number'] = design_no if design_no else ''
                    row['product_type_source'] = method
                    logger.info(f"✅ 学習パターン（商品名）から商品タイプ予測: {product_name[:30]}... → {product_type_from_design} (信頼度: {confidence:.2f})")

            # 6. 正規表現による商品タイプ抽出（最終フォールバック）
            if not product_type_from_design and product_name:
                logger.info(f"🔎 正規表現による商品タイプ抽出（フォールバック）")
                extracted_keywords = ImportService._extract_product_keywords(product_name)
                row['extracted_memo'] = extracted_keywords
                row['design_number'] = design_no if design_no else ''
                row['product_type_source'] = 'regex'
                logger.info(f"✅ 正規表現による商品タイプ: {extracted_keywords}")
            elif not product_type_from_design:
                row['extracted_memo'] = ''
                row['design_number'] = ''
                row['product_type_source'] = 'not_found'
                logger.warning(f"⚠️ 商品タイプを検出できませんでした: {product_name[:50] if product_name else 'N/A'}...")

            # 機種検出（優先順位順）
            device = None
            method = None
            brand = None

            # 1. デザインマスターから機種を取得（商品番号から）
            if product_code and product_code.strip():
                device_from_design = supabase_service.get_device_by_design(product_code.strip())
                if device_from_design:
                    device = device_from_design
                    method = 'design_master'
                    # ブランド名を抽出（最初の単語）
                    brand = device.split()[0] if ' ' in device else device.split('/')[0] if '/' in device else None
                    logger.info(f"📱 デザインマスターから機種取得: {product_code.strip()} → {device}")

            # 2. 学習パターンから機種を予測（商品名から）
            if not device and product_name:
                prediction = device_learning_service.predict_device(product_name)
                if prediction:
                    device, brand, confidence, method = prediction
                    logger.info(f"🎯 学習パターンから機種予測: {product_name[:30]}... → {device} (信頼度: {confidence:.2f})")

            # 3. 通常の機種検出（選択肢列、機種専用列、商品名列、その他の列）
            if not device:
                device, method, brand = device_detector.detect_device_from_row(row)

            row['detected_device'] = device if device else '未検出'
            row['device_detection_method'] = method if device else 'not_found'
            row['detected_brand'] = brand if brand else '未検出'

            # サイズ抽出（手帳型カバーの場合のみ）
            product_name = (
                row.get('product_name') or
                row.get('商品名') or
                row.get('品名') or
                row.get('製品名') or
                ''
            )
            product_type = row.get('extracted_memo', '')

            # 手帳型カバーの場合のみサイズを抽出
            if product_type and '手帳' in product_type:
                size = None
                size_method = None

                if product_name:
                    # 1. 学習パターンから予測（最優先）
                    prediction = size_learning_service.predict_size(product_name, device_name=device)
                    if prediction:
                        size, confidence, size_method = prediction
                        logger.info(f"📏 学習パターンからサイズ予測: {product_name[:30]}... → {size} (信頼度: {confidence:.2f})")

                    # 2. 商品属性（_i6, _L など）から抽出
                    if not size:
                        size, size_method = device_detector.extract_size_from_product_name(
                            product_name,
                            product_type,
                            brand=brand,
                            device=device,
                            row=row  # 選択肢列からの抽出も可能にする
                        )
                        logger.info(f"📏 商品属性からサイズ抽出: {product_name[:30]}... → サイズ={size}, 方法={size_method}")

                    row['detected_size'] = size if size else '-'
                    row['size_detection_method'] = size_method if size else 'not_found'
                else:
                    row['detected_size'] = '-'
                    row['size_detection_method'] = 'not_found'
            else:
                # ハードケース等、手帳型以外はサイズ抽出しない
                row['detected_size'] = '-'
                row['size_detection_method'] = 'not_applicable'
                if product_type:
                    logger.info(f"ℹ️ サイズ抽出スキップ（手帳型以外）: 商品タイプ={product_type}")

        # Add extracted_memo, detected_brand, detected_device, detected_size to columns if not present
        columns_with_extras = parse_result.columns.copy()
        if 'extracted_memo' not in columns_with_extras:
            columns_with_extras.append('extracted_memo')
        if 'detected_brand' not in columns_with_extras:
            columns_with_extras.append('detected_brand')
        if 'detected_device' not in columns_with_extras:
            columns_with_extras.append('detected_device')
        if 'detected_size' not in columns_with_extras:
            columns_with_extras.append('detected_size')

        return ParsePreviewResponse(
            success=True,
            columns=columns_with_extras,
            data=preview_data,
            row_count=len(preview_data),
            total_rows_estimate=parse_result.row_count,
            warnings=parse_result.warnings,
            errors=parse_result.errors,
            metadata=parse_result.metadata
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Preview failed: {str(e)}"
        )


@router.post("/jobs", response_model=ImportJobResponse, status_code=status.HTTP_201_CREATED)
async def create_import_job(
    request: ImportJobCreateRequest,
    db: Session = Depends(get_db)
):
    """
    Create import job and start processing asynchronously.
    """
    try:
        # Verify upload exists
        upload_dir = Path(tempfile.gettempdir()) / "accusync_uploads"
        file_ext = Path(request.filename).suffix.lower()
        file_path = upload_dir / f"{request.upload_id}{file_ext}"

        if not file_path.exists():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Upload not found or expired"
            )

        # Create import job record
        job = ImportJob(
            upload_id=request.upload_id,
            filename=request.filename,
            file_type=request.file_type,
            status=ImportJobStatus.PENDING,
            total_rows=0,
            processed_rows=0,
            error_count=0
        )
        db.add(job)
        db.commit()
        db.refresh(job)

        # Start async processing
        process_file_import.delay(
            job_id=job.id,
            file_path=str(file_path),
            filename=request.filename,
            apply_ai_mapping=request.apply_ai_mapping,
            apply_quality_check=request.apply_quality_check,
            target_fields=request.target_fields,
            parser_options=request.parser_options
        )

        return ImportJobResponse.from_orm(job)

    except HTTPException:
        raise
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Job creation failed: {str(e)}"
        )


@router.get("/jobs/{job_id}", response_model=ImportJobResponse)
async def get_import_job(
    job_id: int,
    db: Session = Depends(get_db)
):
    """
    Get import job status and details.
    """
    job = db.query(ImportJob).filter(ImportJob.id == job_id).first()

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Import job {job_id} not found"
        )

    return ImportJobResponse.from_orm(job)


@router.get("/jobs", response_model=List[ImportJobResponse])
async def list_import_jobs(
    skip: int = 0,
    limit: int = 100,
    status: ImportJobStatus = None,
    db: Session = Depends(get_db)
):
    """
    List import jobs with optional filtering.
    """
    query = db.query(ImportJob)

    if status:
        query = query.filter(ImportJob.status == status)

    jobs = query.order_by(ImportJob.created_at.desc()).offset(skip).limit(limit).all()

    return [ImportJobResponse.from_orm(job) for job in jobs]


@router.post("/jobs/{job_id}/import", response_model=ImportDataResponse)
async def import_data(
    job_id: int,
    request: ImportDataRequest,
    db: Session = Depends(get_db)
):
    """
    Import parsed data from job into database.
    """
    from app.services.import_service import ImportService

    job = db.query(ImportJob).filter(ImportJob.id == job_id).first()

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Import job {job_id} not found"
        )

    if job.status != ImportJobStatus.COMPLETED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Job not ready for import (status: {job.status})"
        )

    try:
        # Extract data from job result
        data = job.result_data.get('data_sample', []) if job.result_data else []

        if not data:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="No data available for import"
            )

        # Import data using ImportService
        result = ImportService.import_order_data(
            db=db,
            data=data,
            column_mapping=request.column_mapping,
            issuer_id=request.issuer_id,
            customer_id=request.customer_id
        )

        return ImportDataResponse(
            success=result['success'],
            imported_rows=result['imported_rows'],
            skipped_rows=result['skipped_rows'],
            error_rows=result['error_rows'],
            warnings=result['warnings'],
            errors=result['errors']
        )

    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Import failed: {str(e)}"
        )


@router.delete("/jobs/{job_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_import_job(
    job_id: int,
    db: Session = Depends(get_db)
):
    """
    Delete import job and associated data.
    """
    job = db.query(ImportJob).filter(ImportJob.id == job_id).first()

    if not job:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Import job {job_id} not found"
        )

    # Clean up uploaded file
    try:
        upload_dir = Path(tempfile.gettempdir()) / "accusync_uploads"
        file_ext = Path(job.filename).suffix.lower()
        file_path = upload_dir / f"{job.upload_id}{file_ext}"
        if file_path.exists():
            os.remove(file_path)
    except Exception:
        pass

    db.delete(job)
    db.commit()


@router.get("/mapping/fields")
async def get_standard_fields():
    """
    Get list of standard fields for mapping.
    """
    return {
        "fields": [field.dict() for field in STANDARD_FIELDS]
    }


@router.post("/mapping/suggest", response_model=AutoMappingResult)
async def suggest_column_mapping(
    columns: List[str],
    db: Session = Depends(get_db)
):
    """
    Suggest automatic column mapping based on source column names.

    Args:
        columns: List of source column names

    Returns:
        AutoMappingResult with suggested mappings
    """
    try:
        result = auto_map_columns(columns)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Mapping suggestion failed: {str(e)}"
        )
