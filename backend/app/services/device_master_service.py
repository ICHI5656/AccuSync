"""
Device Master Service - 機種マスターDB連携（ローカルDB + Supabase）

優先順位:
1. ローカルPostgreSQLのdevice_attributesテーブル（オフライン対応）
2. Supabaseクラウド（オプション・フォールバック）
"""

import os
import logging
from typing import Optional, Dict
from sqlalchemy.orm import Session
from sqlalchemy import text

logger = logging.getLogger(__name__)


class DeviceMasterService:
    """
    機種マスターDBサービス

    ローカルPostgreSQLを優先し、Supabaseはオプション機能として動作します。
    ネットワーク環境に依存せず、どこでも動作します。
    """

    def __init__(self, db: Session):
        self.db = db
        self._supabase_available = False

        # Supabaseはオプション機能として初期化
        # 環境変数が設定されていない場合は完全にスキップ
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_ANON_KEY")

        # 空文字列もNoneとして扱う
        if url and key and url.strip() and key.strip():
            try:
                # Supabaseパッケージがインストールされている場合のみインポート
                from supabase import create_client
                self.supabase_client = create_client(url, key)
                self._supabase_available = True
                logger.info("✅ Supabase client initialized (optional feature)")
            except ImportError:
                logger.info("ℹ️ Supabase package not installed - using local DB only")
                self.supabase_client = None
                self._supabase_available = False
            except Exception as e:
                logger.warning(f"⚠️ Supabase initialization failed: {e} - using local DB only")
                self.supabase_client = None
                self._supabase_available = False
        else:
            self.supabase_client = None
            self._supabase_available = False
            logger.info("ℹ️ Supabase not configured - using local DB only")

    def get_device_size(self, brand: str, device_name: str) -> Optional[str]:
        """
        機種マスターDBからサイズカテゴリを取得

        優先順位:
        1. ローカルPostgreSQL
        2. Supabase（利用可能な場合）

        Args:
            brand: ブランド名（iPhone, AQUOS, Galaxy, etc.）
            device_name: 機種名（iPhone 15 Pro, AQUOS wish4, Galaxy A54, etc.）

        Returns:
            サイズカテゴリ（L, i6, 特大, etc.）またはNone
        """
        # 1. ローカルDBから検索（優先）
        size = self._get_size_from_local_db(brand, device_name)
        if size:
            logger.info(f"📊 Found size in local DB: {brand} {device_name} → {size}")
            return size

        # 2. Supabaseから検索（オプション）
        if self._supabase_available:
            size = self._get_size_from_supabase(brand, device_name)
            if size:
                logger.info(f"📊 Found size in Supabase: {brand} {device_name} → {size}")
                return size

        logger.debug(f"No size found for: {brand} {device_name}")
        return None

    def _get_size_from_local_db(self, brand: str, device_name: str) -> Optional[str]:
        """ローカルPostgreSQLから検索"""
        try:
            # スペースを無視した正規化検索（優先）
            # iPhone14Pro -> iphone14pro, iPhone 14 Pro -> iphone14pro
            normalized_query = text("""
                SELECT size_category
                FROM device_attributes
                WHERE brand = :brand
                  AND REPLACE(LOWER(device_name), ' ', '') = :device_name_normalized
                LIMIT 1
            """)

            device_normalized = device_name.lower().replace(' ', '')
            result = self.db.execute(
                normalized_query,
                {"brand": brand, "device_name_normalized": device_normalized}
            ).fetchone()

            if result and result[0]:
                logger.info(f"📊 Matched (normalized): {device_name} → {result[0]}")
                return result[0]

            # 部分一致検索（フォールバック）
            partial_query = text("""
                SELECT size_category
                FROM device_attributes
                WHERE brand = :brand
                  AND device_name ILIKE :device_name
                LIMIT 1
            """)

            result = self.db.execute(
                partial_query,
                {"brand": brand, "device_name": f"%{device_name}%"}
            ).fetchone()

            if result and result[0]:
                logger.info(f"📊 Matched (partial): {device_name} → {result[0]}")
                return result[0]

            # デバイス名のみでの検索（"iPhone 14 Pro" → "14 Pro"）
            if ' ' in device_name:
                device_only = ' '.join(device_name.split()[1:])
                result = self.db.execute(
                    partial_query,
                    {"brand": brand, "device_name": f"%{device_only}%"}
                ).fetchone()

                if result and result[0]:
                    logger.info(f"📊 Matched (device only): {device_only} → {result[0]}")
                    return result[0]

            return None

        except Exception as e:
            logger.error(f"❌ Local DB query failed: {e}")
            return None

    def _get_size_from_supabase(self, brand: str, device_name: str) -> Optional[str]:
        """Supabaseから検索（オプション）"""
        if not self.supabase_client:
            return None

        try:
            response = self.supabase_client.table('device_attributes') \
                .select('size_category') \
                .eq('brand', brand) \
                .ilike('device_name', f'%{device_name}%') \
                .limit(1) \
                .execute()

            if response.data and len(response.data) > 0:
                return response.data[0].get('size_category')

            # 部分一致検索
            if ' ' in device_name:
                device_only = ' '.join(device_name.split()[1:])
                response = self.supabase_client.table('device_attributes') \
                    .select('size_category') \
                    .eq('brand', brand) \
                    .ilike('device_name', f'%{device_only}%') \
                    .limit(1) \
                    .execute()

                if response.data and len(response.data) > 0:
                    return response.data[0].get('size_category')

            return None

        except Exception as e:
            logger.warning(f"⚠️ Supabase query failed: {e}")
            return None

    def get_device_info(self, brand: str, device_name: str) -> Optional[Dict[str, str]]:
        """
        機種マスターDBから機種の詳細情報を取得

        Args:
            brand: ブランド名
            device_name: 機種名

        Returns:
            {brand, device_name, attribute_value, size_category} または None
        """
        try:
            query = text("""
                SELECT brand, device_name, attribute_value, size_category
                FROM device_attributes
                WHERE brand = :brand
                  AND device_name ILIKE :device_name
                LIMIT 1
            """)

            result = self.db.execute(
                query,
                {"brand": brand, "device_name": f"%{device_name}%"}
            ).fetchone()

            if result:
                return {
                    "brand": result[0],
                    "device_name": result[1],
                    "attribute_value": result[2],
                    "size_category": result[3]
                }

            return None

        except Exception as e:
            logger.error(f"❌ Device info query failed: {e}")
            return None

    def test_connection(self) -> Dict[str, bool]:
        """データベース接続テスト"""
        results = {
            "local_db": False,
            "supabase": False
        }

        # ローカルDB接続テスト
        try:
            query = text("SELECT COUNT(*) FROM device_attributes")
            count = self.db.execute(query).scalar()
            results["local_db"] = True
            logger.info(f"✅ Local DB connection OK: {count} records")
        except Exception as e:
            logger.error(f"❌ Local DB connection failed: {e}")

        # Supabase接続テスト（オプション）
        if self._supabase_available and self.supabase_client:
            try:
                response = self.supabase_client.table('device_attributes') \
                    .select('brand, device_name') \
                    .limit(1) \
                    .execute()
                results["supabase"] = True
                logger.info("✅ Supabase connection OK (optional)")
            except Exception as e:
                logger.warning(f"⚠️ Supabase connection failed: {e} (optional feature)")

        return results
