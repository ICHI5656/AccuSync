"""
Import API endpoints for file upload and data import.
"""

import os
import uuid
import tempfile
from pathlib import Path
from typing import List
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.import_job import ImportJob
from app.parsers.factory import FileParserFactory
from app.ai.factory import AIProviderFactory
from app.tasks.import_tasks import process_file_import
from app.services.import_service import ImportService
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
        for row in preview_data:
            # Get product name from various possible keys
            product_name = (
                row.get('product_name') or
                row.get('商品名') or
                row.get('品名') or
                row.get('製品名') or
                ''
            )
            if product_name:
                extracted_keywords = ImportService._extract_product_keywords(product_name)
                row['extracted_memo'] = extracted_keywords
            else:
                row['extracted_memo'] = ''

        # Add extracted_memo to columns if not present
        columns_with_memo = parse_result.columns.copy()
        if 'extracted_memo' not in columns_with_memo:
            columns_with_memo.append('extracted_memo')

        return ParsePreviewResponse(
            success=True,
            columns=columns_with_memo,
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
