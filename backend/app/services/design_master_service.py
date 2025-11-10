"""
Design Master Service - デザインマスター管理サービス

ローカルPostgreSQLのdesignsテーブルを優先、Supabaseは補完的に使用
"""

import logging
from typing import Optional, List, Dict
from sqlalchemy.orm import Session
from sqlalchemy import text

from app.models.design import Design

logger = logging.getLogger(__name__)


class DesignMasterService:
    """デザインマスター管理サービス（ローカルDB優先）"""

    def __init__(self, db: Session):
        self.db = db

    def get_product_type_by_design(self, design_no: str) -> Optional[str]:
        """
        デザイン番号から商品タイプを取得（ローカルDB優先）

        Args:
            design_no: デザイン番号（SKU）

        Returns:
            商品タイプ（手帳型、ハードケース etc.）またはNone
        """
        if not design_no or not design_no.strip():
            return None

        design_no = design_no.strip()

        try:
            # 1. 完全一致で検索
            design = self.db.query(Design).filter(
                Design.design_no == design_no,
                Design.status == '有効'
            ).first()

            if design and design.case_type:
                logger.info(f"🎨 Found product type (local DB, exact): {design_no} → {design.case_type}")
                return design.case_type

            # 2. CSV側が長い場合の部分一致（前方一致）
            # 例: CSV=503-5494699-9639853, DB=503-5494699
            designs = self.db.query(Design).filter(
                Design.status == '有効'
            ).all()

            for design in designs:
                db_design_no = design.design_no
                # CSV商品番号がDBデザイン番号で始まる場合（前方一致）
                if design_no.startswith(db_design_no) and len(db_design_no) > 3:
                    if design.case_type:
                        logger.info(f"🎨 Found product type (local DB, prefix): {design_no} → {db_design_no} → {design.case_type}")
                        return design.case_type

            # 3. DB側が長い場合の部分一致（後方一致）
            # 例: CSV=betty-001, DB=betty-001-lec-bu
            designs = self.db.query(Design).filter(
                Design.design_no.like(f'{design_no}%'),
                Design.status == '有効'
            ).all()

            if designs and len(designs) > 0:
                design = designs[0]
                if design.case_type:
                    logger.info(f"🎨 Found product type (local DB, suffix): {design_no} → {design.design_no} → {design.case_type}")
                    return design.case_type

            logger.debug(f"No product type found in local DB for: {design_no}")
            return None

        except Exception as e:
            logger.error(f"❌ Local DB query failed for {design_no}: {e}")
            return None

    def count_designs(self) -> int:
        """デザインマスターの件数を取得"""
        try:
            count = self.db.query(Design).filter(Design.status == '有効').count()
            return count
        except Exception as e:
            logger.error(f"❌ Failed to count designs: {e}")
            return 0

    def sync_from_supabase(self, supabase_service) -> Dict[str, any]:
        """
        Supabaseからデザインマスターを同期

        Args:
            supabase_service: SupabaseServiceインスタンス

        Returns:
            同期結果の辞書
        """
        if not supabase_service or not supabase_service.design_master_client:
            return {
                'success': False,
                'error': 'Supabase design master client not available',
                'synced_count': 0
            }

        try:
            # Supabaseから全デザインデータを取得
            logger.info("📥 Fetching designs from Supabase...")
            response = supabase_service.design_master_client.table('designs') \
                .select('design_no, design_name, case_type, material, status') \
                .eq('status', '有効') \
                .execute()

            if not response.data:
                return {
                    'success': True,
                    'synced_count': 0,
                    'message': 'No designs found in Supabase'
                }

            synced_count = 0
            errors = []

            for design_data in response.data:
                try:
                    design_no = design_data.get('design_no')
                    if not design_no:
                        continue

                    # UPSERT: 既存レコードを更新、なければ挿入
                    existing = self.db.query(Design).filter(Design.design_no == design_no).first()

                    if existing:
                        # 更新
                        existing.design_name = design_data.get('design_name')
                        existing.case_type = design_data.get('case_type')
                        existing.material = design_data.get('material')
                        existing.status = design_data.get('status', '有効')
                    else:
                        # 新規作成
                        new_design = Design(
                            design_no=design_no,
                            design_name=design_data.get('design_name'),
                            case_type=design_data.get('case_type'),
                            material=design_data.get('material'),
                            status=design_data.get('status', '有効')
                        )
                        self.db.add(new_design)

                    synced_count += 1

                except Exception as e:
                    error_msg = f"Failed to sync design {design_data.get('design_no')}: {str(e)}"
                    logger.error(f"❌ {error_msg}")
                    errors.append(error_msg)

            # コミット
            self.db.commit()

            logger.info(f"✅ Successfully synced {synced_count} designs from Supabase")

            return {
                'success': True,
                'synced_count': synced_count,
                'total_fetched': len(response.data),
                'errors': errors
            }

        except Exception as e:
            self.db.rollback()
            error_msg = f"Failed to sync from Supabase: {str(e)}"
            logger.error(f"❌ {error_msg}")
            return {
                'success': False,
                'error': error_msg,
                'synced_count': 0
            }

    def get_all_designs(self, limit: int = 100, offset: int = 0) -> List[Design]:
        """全デザインマスターを取得（ページネーション対応）"""
        try:
            designs = self.db.query(Design).filter(
                Design.status == '有効'
            ).offset(offset).limit(limit).all()
            return designs
        except Exception as e:
            logger.error(f"❌ Failed to fetch designs: {e}")
            return []
