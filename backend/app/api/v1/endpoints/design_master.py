"""
Design Master API Endpoints - デザインマスター管理API
"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Dict
import logging

from app.core.database import get_db
from app.services.design_master_service import DesignMasterService
from app.services.supabase_service import SupabaseService

logger = logging.getLogger(__name__)

router = APIRouter()


@router.get("/status")
def get_design_master_status(db: Session = Depends(get_db)):
    """
    デザインマスターの同期状態を取得

    Returns:
        {
            "local_db_count": 件数,
            "supabase_available": True/False,
            "last_sync": タイムスタンプ
        }
    """
    design_master_service = DesignMasterService(db)
    supabase_service = SupabaseService()

    local_count = design_master_service.count_designs()
    supabase_available = supabase_service.design_master_client is not None

    return {
        "success": True,
        "local_db": {
            "count": local_count
        },
        "supabase": {
            "available": supabase_available
        }
    }


@router.post("/sync")
def sync_design_master_from_supabase(db: Session = Depends(get_db)):
    """
    Supabaseからデザインマスターを同期

    Returns:
        同期結果
    """
    design_master_service = DesignMasterService(db)
    supabase_service = SupabaseService()

    if not supabase_service.design_master_client:
        raise HTTPException(
            status_code=503,
            detail="Supabase design master client not available. Please check DESIGN_MASTER_SUPABASE_* environment variables."
        )

    logger.info("🔄 Starting design master sync from Supabase...")
    result = design_master_service.sync_from_supabase(supabase_service)

    if not result['success']:
        raise HTTPException(status_code=500, detail=result.get('error', 'Sync failed'))

    logger.info(f"✅ Design master sync completed: {result['synced_count']} designs")

    return {
        **result,
        "message": f"Successfully synced {result['synced_count']} designs from Supabase"
    }


@router.get("/designs")
def get_all_designs(
    limit: int = 100,
    offset: int = 0,
    db: Session = Depends(get_db)
):
    """
    デザインマスターの一覧を取得

    Args:
        limit: 取得件数（デフォルト: 100）
        offset: オフセット（デフォルト: 0）

    Returns:
        デザインマスターのリスト
    """
    design_master_service = DesignMasterService(db)
    designs = design_master_service.get_all_designs(limit=limit, offset=offset)

    return {
        "success": True,
        "count": len(designs),
        "designs": [
            {
                "design_no": d.design_no,
                "design_name": d.design_name,
                "case_type": d.case_type,
                "material": d.material,
                "status": d.status
            }
            for d in designs
        ]
    }


@router.get("/search/{design_no}")
def search_design_by_number(design_no: str, db: Session = Depends(get_db)):
    """
    デザイン番号から商品タイプを検索

    Args:
        design_no: デザイン番号（SKU）

    Returns:
        商品タイプ情報
    """
    design_master_service = DesignMasterService(db)
    product_type = design_master_service.get_product_type_by_design(design_no)

    if not product_type:
        raise HTTPException(
            status_code=404,
            detail=f"Design number '{design_no}' not found in design master"
        )

    return {
        "success": True,
        "design_no": design_no,
        "product_type": product_type
    }
