"""
Supabase Service - 機種マスターDB連携（オプション機能）

SKUNEW_v2.5V の device_attributes テーブルから機種情報を取得します。
注: Supabaseパッケージがインストールされていない場合は無効化されます。
"""

import os
import logging
from typing import Optional, Dict

logger = logging.getLogger(__name__)

# Supabaseパッケージがインストールされている場合のみインポート
try:
    from supabase import create_client, Client
    SUPABASE_AVAILABLE = True
except ImportError:
    logger.info("ℹ️ Supabase package not installed - service will be disabled")
    SUPABASE_AVAILABLE = False
    Client = None  # Type hint用


class SupabaseService:
    """Supabase機種マスターDBサービス"""

    def __init__(self):
        # Supabaseパッケージが利用可能かチェック
        if not SUPABASE_AVAILABLE:
            logger.info("ℹ️ Supabase package not available - service disabled")
            self.client = None
            self.design_master_client = None
            return

        # デバイスマスターDB用クライアント（device_attributes テーブル）
        url = os.getenv("SUPABASE_URL")
        key = os.getenv("SUPABASE_ANON_KEY")

        # 空文字列もNoneとして扱う
        if not url or not key or not url.strip() or not key.strip():
            logger.info("ℹ️ Supabase credentials not configured - using local DB only")
            self.client = None
        else:
            try:
                self.client = create_client(url, key)
                logger.info("✅ Supabase client (device master) initialized successfully")
            except Exception as e:
                logger.error(f"❌ Failed to initialize Supabase client: {e}")
                self.client = None

        # デザインマスターDB用クライアント（designs テーブル - SKUNEW_v2.5）
        design_url = os.getenv("DESIGN_MASTER_SUPABASE_URL")
        design_key = os.getenv("DESIGN_MASTER_SUPABASE_ANON_KEY")

        if not design_url or not design_key or not design_url.strip() or not design_key.strip():
            logger.info("ℹ️ Design master credentials not configured - design lookup disabled")
            self.design_master_client = None
        else:
            try:
                self.design_master_client = create_client(design_url, design_key)
                logger.info("✅ Supabase client (design master) initialized successfully")
            except Exception as e:
                logger.error(f"❌ Failed to initialize design master client: {e}")
                self.design_master_client = None

    def get_device_size(self, brand: str, device_name: str) -> Optional[str]:
        """
        機種マスターDBからサイズカテゴリを取得

        Args:
            brand: ブランド名（iPhone, AQUOS, Galaxy, etc.）
            device_name: 機種名（iPhone 15 Pro, AQUOS wish4, Galaxy A54, etc.）

        Returns:
            サイズカテゴリ（L, i6, 特大, etc.）またはNone
        """
        if not self.client:
            logger.debug("Supabase client not available, skipping DB lookup")
            return None

        try:
            # device_attributes テーブルからサイズカテゴリを検索
            # brand と device_name の両方でマッチング
            response = self.client.table('device_attributes') \
                .select('size_category') \
                .eq('brand', brand) \
                .ilike('device_name', f'%{device_name}%') \
                .limit(1) \
                .execute()

            if response.data and len(response.data) > 0:
                size = response.data[0].get('size_category')
                if size:
                    logger.info(f"📊 Found size in Supabase DB: {brand} {device_name} → {size}")
                    return size

            # ブランド名なしでも試行（デバイス名のみ）
            if ' ' in device_name:
                # "iPhone 15 Pro" → "15 Pro"
                device_only = ' '.join(device_name.split()[1:])
                response = self.client.table('device_attributes') \
                    .select('size_category') \
                    .eq('brand', brand) \
                    .ilike('device_name', f'%{device_only}%') \
                    .limit(1) \
                    .execute()

                if response.data and len(response.data) > 0:
                    size = response.data[0].get('size_category')
                    if size:
                        logger.info(f"📊 Found size in Supabase DB (partial match): {brand} {device_only} → {size}")
                        return size

            logger.debug(f"No size found in Supabase DB for: {brand} {device_name}")
            return None

        except Exception as e:
            logger.error(f"❌ Supabase query failed for {brand} {device_name}: {e}")
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
        if not self.client:
            return None

        try:
            response = self.client.table('device_attributes') \
                .select('brand, device_name, attribute_value, size_category') \
                .eq('brand', brand) \
                .ilike('device_name', f'%{device_name}%') \
                .limit(1) \
                .execute()

            if response.data and len(response.data) > 0:
                logger.info(f"📊 Found device info in Supabase DB: {response.data[0]}")
                return response.data[0]

            return None

        except Exception as e:
            logger.error(f"❌ Supabase query failed: {e}")
            return None

    def test_connection(self) -> bool:
        """Supabase接続テスト"""
        if not self.client:
            logger.error("❌ Supabase client not initialized")
            return False

        try:
            # device_attributes テーブルから1件取得してテスト
            response = self.client.table('device_attributes') \
                .select('brand, device_name') \
                .limit(1) \
                .execute()

            logger.info(f"✅ Supabase connection test successful: {len(response.data)} records")
            return True

        except Exception as e:
            logger.error(f"❌ Supabase connection test failed: {e}")
            return False

    def is_available(self) -> bool:
        """Supabaseサービスが利用可能かチェック"""
        return self.client is not None

    def get_product_type_by_design(self, design_no: str) -> Optional[str]:
        """
        デザインマスターDBから商品タイプ（ケースタイプ）を取得

        Args:
            design_no: デザイン番号（betty-001-lec-bu, color_design_002-1, Amazon SKU etc.）

        Returns:
            商品タイプ（手帳型、ハードケース etc.）またはNone
        """
        if not self.design_master_client:
            logger.debug("Design master client not available, skipping design lookup")
            return None

        try:
            # 1. 完全一致で検索
            response = self.design_master_client.table('designs') \
                .select('case_type, design_name, material, design_no') \
                .eq('design_no', design_no) \
                .eq('status', '有効') \
                .limit(1) \
                .execute()

            if response.data and len(response.data) > 0:
                case_type = response.data[0].get('case_type')
                if case_type:
                    logger.info(f"🎨 Found product type (exact match): {design_no} → {case_type}")
                    return case_type

            # 2. CSV側が長い場合の部分一致（前方一致）
            # 例: CSV=503-5494699-9639853, DB=503-5494699 の場合
            response = self.design_master_client.table('designs') \
                .select('case_type, design_name, material, design_no') \
                .eq('status', '有効') \
                .execute()

            if response.data:
                for design in response.data:
                    db_design_no = design.get('design_no', '')
                    # CSV商品番号がDBデザイン番号で始まる場合（前方一致）
                    if design_no.startswith(db_design_no) and len(db_design_no) > 3:
                        case_type = design.get('case_type')
                        if case_type:
                            logger.info(f"🎨 Found product type (prefix match): {design_no} → {db_design_no} → {case_type}")
                            return case_type

            # 3. DB側が長い場合の部分一致（後方一致）
            # 例: CSV=betty-001, DB=betty-001-lec-bu の場合
            response = self.design_master_client.table('designs') \
                .select('case_type, design_name, material, design_no') \
                .ilike('design_no', f'{design_no}%') \
                .eq('status', '有効') \
                .limit(1) \
                .execute()

            if response.data and len(response.data) > 0:
                case_type = response.data[0].get('case_type')
                db_design_no = response.data[0].get('design_no')
                if case_type:
                    logger.info(f"🎨 Found product type (suffix match): {design_no} → {db_design_no} → {case_type}")
                    return case_type

            logger.debug(f"No product type found in design master for: {design_no}")
            return None

        except Exception as e:
            logger.error(f"❌ Design master query failed for {design_no}: {e}")
            return None

    def get_device_by_design(self, design_no: str) -> Optional[str]:
        """
        デザインマスターDBから機種情報を取得

        Args:
            design_no: デザイン番号（betty-001-lec-bu, color_design_002-1, Amazon SKU etc.）

        Returns:
            機種名（iPhone 15 Pro, AQUOS wish4 etc.）またはNone
        """
        if not self.design_master_client:
            logger.debug("Design master client not available, skipping design lookup")
            return None

        try:
            # 1. 完全一致で検索
            response = self.design_master_client.table('designs') \
                .select('device_name, brand, design_name, design_no, case_type') \
                .eq('design_no', design_no) \
                .eq('status', '有効') \
                .limit(1) \
                .execute()

            if response.data and len(response.data) > 0:
                device_name = response.data[0].get('device_name')
                brand = response.data[0].get('brand')
                if device_name:
                    # ブランド名を追加（既に含まれていない場合）
                    if brand and not device_name.startswith(brand):
                        full_device = f"{brand} {device_name}"
                    else:
                        full_device = device_name
                    logger.info(f"📱 Found device (exact match): {design_no} → {full_device}")
                    return full_device

            # 2. CSV側が長い場合の部分一致（前方一致）
            response = self.design_master_client.table('designs') \
                .select('device_name, brand, design_name, design_no, case_type') \
                .eq('status', '有効') \
                .execute()

            if response.data:
                for design in response.data:
                    db_design_no = design.get('design_no', '')
                    # CSV商品番号がDBデザイン番号で始まる場合（前方一致）
                    if design_no.startswith(db_design_no) and len(db_design_no) > 3:
                        device_name = design.get('device_name')
                        brand = design.get('brand')
                        if device_name:
                            if brand and not device_name.startswith(brand):
                                full_device = f"{brand} {device_name}"
                            else:
                                full_device = device_name
                            logger.info(f"📱 Found device (prefix match): {design_no} → {db_design_no} → {full_device}")
                            return full_device

            # 3. DB側が長い場合の部分一致（後方一致）
            response = self.design_master_client.table('designs') \
                .select('device_name, brand, design_name, design_no, case_type') \
                .ilike('design_no', f'{design_no}%') \
                .eq('status', '有効') \
                .limit(1) \
                .execute()

            if response.data and len(response.data) > 0:
                device_name = response.data[0].get('device_name')
                brand = response.data[0].get('brand')
                db_design_no = response.data[0].get('design_no')
                if device_name:
                    if brand and not device_name.startswith(brand):
                        full_device = f"{brand} {device_name}"
                    else:
                        full_device = device_name
                    logger.info(f"📱 Found device (suffix match): {design_no} → {db_design_no} → {full_device}")
                    return full_device

            logger.debug(f"No device found in design master for: {design_no}")
            return None

        except Exception as e:
            logger.error(f"❌ Design master query failed for {design_no}: {e}")
            return None

    def fetch_all_devices(self) -> list:
        """
        Supabaseから全ての機種データを取得

        Returns:
            機種データのリスト [{"brand": "iPhone", "device_name": "iPhone 15 Pro", ...}, ...]
        """
        if not self.client:
            logger.warning("⚠️ Supabase client not available")
            return []

        try:
            # 全データを取得（ページネーション考慮）
            all_devices = []
            page_size = 1000
            offset = 0

            while True:
                response = self.client.table('device_attributes') \
                    .select('brand, device_name, size_category, attribute_value, created_at, updated_at') \
                    .range(offset, offset + page_size - 1) \
                    .execute()

                if not response.data:
                    break

                all_devices.extend(response.data)

                # 取得したデータが page_size より少ない場合は最後のページ
                if len(response.data) < page_size:
                    break

                offset += page_size

            logger.info(f"📊 Fetched {len(all_devices)} devices from Supabase")
            return all_devices

        except Exception as e:
            logger.error(f"❌ Failed to fetch devices from Supabase: {e}")
            return []

    def fuzzy_search_product_type(self, product_code: str) -> Optional[str]:
        """
        商品番号から商品タイプを曖昧検索（Supabase designsテーブル）

        Args:
            product_code: 商品番号（例: ami_kaiser-A_1r-A）

        Returns:
            商品タイプ または None
        """
        if not self.design_master_client or not product_code:
            return None

        try:
            # 1. 完全一致検索
            response = self.design_master_client.table('designs') \
                .select('case_type, design_no') \
                .eq('design_no', product_code) \
                .eq('status', '有効') \
                .limit(1) \
                .execute()

            if response.data and len(response.data) > 0:
                case_type = response.data[0].get('case_type')
                if case_type:
                    logger.info(f"🎯 Supabase fuzzy search (exact): {product_code} → {case_type}")
                    return case_type

            # 2. 部分一致検索（LIKE検索）
            # 例: ami_kaiser-A_1r-A → %kaiser% で検索
            keywords = self._extract_search_keywords(product_code)

            for keyword in keywords:
                if len(keyword) < 3:  # 短すぎるキーワードはスキップ
                    continue

                response = self.design_master_client.table('designs') \
                    .select('case_type, design_no') \
                    .ilike('design_no', f'%{keyword}%') \
                    .eq('status', '有効') \
                    .limit(5) \
                    .execute()

                if response.data and len(response.data) > 0:
                    case_type = response.data[0].get('case_type')
                    design_no = response.data[0].get('design_no')
                    if case_type:
                        logger.info(f"🎯 Supabase fuzzy search (partial): {product_code} → {design_no} (keyword: {keyword}) → {case_type}")
                        return case_type

            # 3. 前方一致検索
            # 例: ami_kaiser → ami_kaiser% で検索
            prefix = product_code.split('_')[0] if '_' in product_code else product_code.split('-')[0]
            if len(prefix) >= 3:
                response = self.design_master_client.table('designs') \
                    .select('case_type, design_no') \
                    .ilike('design_no', f'{prefix}%') \
                    .eq('status', '有効') \
                    .limit(5) \
                    .execute()

                if response.data and len(response.data) > 0:
                    case_type = response.data[0].get('case_type')
                    design_no = response.data[0].get('design_no')
                    if case_type:
                        logger.info(f"🎯 Supabase fuzzy search (prefix): {product_code} → {design_no} (prefix: {prefix}) → {case_type}")
                        return case_type

            logger.debug(f"No fuzzy match found in Supabase for: {product_code}")
            return None

        except Exception as e:
            logger.error(f"❌ Supabase fuzzy search failed for {product_code}: {e}")
            return None

    def _extract_search_keywords(self, product_code: str) -> list:
        """
        商品番号から検索キーワードを抽出

        Args:
            product_code: 商品番号（例: ami_kaiser-A_1r-A）

        Returns:
            キーワードのリスト（長い順）
        """
        keywords = []

        # アンダースコア区切り
        if '_' in product_code:
            parts = product_code.split('_')
            keywords.extend([p for p in parts if len(p) >= 3])

        # ハイフン区切り
        if '-' in product_code:
            parts = product_code.split('-')
            keywords.extend([p for p in parts if len(p) >= 3])

        # 全体
        if len(product_code) >= 3:
            keywords.append(product_code)

        # 重複削除 & 長い順にソート
        keywords = list(set(keywords))
        keywords.sort(key=len, reverse=True)

        return keywords
