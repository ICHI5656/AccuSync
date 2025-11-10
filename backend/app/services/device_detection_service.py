"""
Device Detection Service - 機種検出サービス

正規表現とSupabase DBを使用して、CSVから機種情報を抽出します。
"""

import re
import logging
from typing import Optional, Dict, Tuple, List
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

# Device Master Service（ローカルDB + Supabase統合）
try:
    from app.services.device_master_service import DeviceMasterService
    DEVICE_MASTER_AVAILABLE = True
except ImportError:
    DEVICE_MASTER_AVAILABLE = False
    logger.warning("Device master service not available - DB size lookup will be disabled")

# Supabase Service（デザインマスター連携用）
try:
    from app.services.supabase_service import SupabaseService
    SUPABASE_SERVICE_AVAILABLE = True
except ImportError:
    SUPABASE_SERVICE_AVAILABLE = False
    logger.warning("Supabase service not available - design master lookup will be disabled")

# Design Master Service（ローカルデザインマスター）
try:
    from app.services.design_master_service import DesignMasterService
    DESIGN_MASTER_SERVICE_AVAILABLE = True
except ImportError:
    DESIGN_MASTER_SERVICE_AVAILABLE = False
    logger.warning("Design master service not available - local design lookup will be disabled")


class DeviceDetectionService:
    """機種検出サービス（正規表現ベース）"""

    # 機種検出パターン（優先度順）
    DEVICE_PATTERNS = [
        # iPhone系（柔軟なパターン + ひらがな対応）
        (r'[いi]?[Pp]hone\s*\d{1,2}(?:\s*(?:Pro(?:\s*Max)?|Plus|mini))?', 'iPhone'),
        (r'アイフォン\s*\d{1,2}(?:\s*(?:プロ|プラス|ミニ|マックス))?', 'iPhone'),
        (r'いふぉん\s*\d{1,2}', 'iPhone'),  # ひらがな

        # Galaxy系（ブランド名付き）
        (r'Galaxy\s*[A-Z]\d+(?:\s*(?:Ultra|Plus|\+|ウルトラ|プラス))?', 'Galaxy'),
        (r'ギャラクシー\s*[A-Z]?\d+(?:\s*(?:ウルトラ|プラス))?', 'Galaxy'),

        # Galaxy A シリーズ（A73, A54 など単独形式）
        (r'A\d{2}(?![0-9SH])', 'Galaxy'),

        # Samsung キャリアモデル番号（SC-, SCG-, SCV- 形式）
        (r'SC-\d+[A-Z]*', 'Galaxy'),
        (r'SCG\d+', 'Galaxy'),
        (r'SCV\d+', 'Galaxy'),

        # Xperia系（ブランド名付き）
        (r'Xperia\s*(?:\d+|[A-Z]+\s*\d+)(?:\s*(?:II|III|IV|V|VI))?', 'Xperia'),
        (r'エクスペリア\s*\d+', 'Xperia'),

        # Xperia キャリアモデル番号（SO-, SOG-, SOV- 形式）
        (r'SO-\d+[A-Z]*', 'Xperia'),
        (r'SOG\d+', 'Xperia'),
        (r'SOV\d+', 'Xperia'),

        # AQUOS系（ブランド名付き + ひらがな対応）
        (r'AQUOS\s*(?:sense|R|zero|wish|ゼロ|センス)\d*(?:\s*(?:plus|\+|プラス))?', 'AQUOS'),
        (r'アクオス\s*(?:sense|R|zero|wish|センス|ゼロ)?\d*', 'AQUOS'),
        (r'あくおす\s*(?:sense|R|zero|wish)?\d*', 'AQUOS'),  # ひらがな

        # AQUOS 単独モデル名（wish4, sense8, We2 など）
        (r'wish\s*\d+(?:\s*(?:plus|\+))?', 'AQUOS'),
        (r'sense\s*\d+(?:\s*(?:plus|\+|lite))?', 'AQUOS'),
        (r'zero\s*\d+', 'AQUOS'),
        (r'R\s*\d+', 'AQUOS'),
        (r'We\s*\d+', 'AQUOS'),
        (r'Be\s*\d+', 'AQUOS'),

        # AQUOS キャリアモデル番号（SH-, SHG-, SHV-, A-SH 形式）
        (r'SH-\d+[A-Z]*', 'AQUOS'),
        (r'SHG\d+', 'AQUOS'),
        (r'SHV\d+', 'AQUOS'),
        (r'A\d+SH', 'AQUOS'),

        # Pixel系
        (r'(?:Google\s*)?Pixel\s*\d+(?:\s*(?:Pro|a|XL))?', 'Pixel'),
        (r'ピクセル\s*\d+', 'Pixel'),

        # OPPO系
        (r'OPPO\s*(?:Reno|Find|A)\d+(?:\s*(?:Pro|\+))?', 'OPPO'),
        (r'オッポ\s*(?:Reno|Find|A)?\d+', 'OPPO'),

        # Xiaomi/Redmi系
        (r'(?:Redmi|Mi|Xiaomi)\s*(?:Note\s*)?\d+(?:\s*(?:Pro|\+))?', 'Xiaomi'),

        # arrows系
        (r'arrows\s*(?:We|Be|NX|N|F)\d*', 'arrows'),
        (r'アローズ\s*\d*', 'arrows'),

        # arrows キャリアモデル番号（F- 形式）
        (r'F-\d+[A-Z]*', 'arrows'),
    ]

    # 機種関連の列名キーワード
    DEVICE_COLUMN_KEYWORDS = [
        '機種', '機種名', '対応機種', '端末', '端末名', 'デバイス',
        'device', 'model', 'Device', 'Model', 'DEVICE', 'MODEL',
        '携帯機種', '対応端末', '機種情報'
    ]

    def __init__(self, db: Session):
        self.db = db
        # DeviceMasterServiceを使用（ローカルDB優先、Supabaseはオプション）
        self.device_master = DeviceMasterService(db) if DEVICE_MASTER_AVAILABLE else None
        # DesignMasterServiceを使用（ローカルデザインマスターDB）
        self.design_master = DesignMasterService(db) if DESIGN_MASTER_SERVICE_AVAILABLE else None
        # SupabaseServiceを使用（デザインマスター同期用）
        self.supabase_service = SupabaseService() if SUPABASE_SERVICE_AVAILABLE else None
        # RakutenSKUServiceを使用（楽天SKU管理システムDB連携）
        try:
            from app.services.rakuten_sku_service import RakutenSKUService
            self.rakuten_sku = RakutenSKUService()
            if self.rakuten_sku.is_available():
                logger.info("✅ 楽天SKU管理システムDB連携が有効です")
            else:
                self.rakuten_sku = None
        except Exception as e:
            logger.warning(f"⚠️ 楽天SKU管理システムDB連携が無効です: {e}")
            self.rakuten_sku = None

    def extract_device_from_options(self, options_text: str) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """
        選択肢テキストから機種名とサイズを抽出

        パターン例:
        - 楽天: 機種【iPhone】:iPhone 6[i6]
        - 楽天: 機種【AQUOS_2】:wish4(SH-52E)[3L]
        - ワーマ: 機種の選択(iPhone)=iPhone SE 第2世代 [i6]
        - ▼で始まるものは選択されていない（無視）

        Args:
            options_text: 選択肢テキスト（改行区切り）

        Returns:
            (device_name, size, brand) のタプル
        """
        if not options_text:
            return None, None, None

        # パターン1: 楽天形式 - 機種【ブランド】[:=]機種名[サイズ]
        # ▼や-で始まるものは選択されていないので除外
        pattern1 = r'機種【([^】]+)】[:=]([^▼\-\[\n\r&]+)\[([^\]]+)\]'
        matches = re.findall(pattern1, options_text, re.MULTILINE)

        for brand_label, device_name, size in matches:
            # デバイス名をクリーンアップ
            device_name = device_name.strip()
            size = size.strip()

            # ブランド判定
            brand = self._normalize_brand_label(brand_label)

            # 型番やカッコを削除（例: wish4(SH-52E) → AQUOS wish4）
            device_clean = re.sub(r'\([^)]+\)', '', device_name).strip()

            # ブランド名を追加（AQUOSやPixelなどブランド名が含まれていない場合）
            if brand and not device_clean.startswith(brand):
                device_full = f"{brand} {device_clean}"
            else:
                device_full = device_clean

            logger.info(f"📱 Extracted from options (Rakuten): {device_full} [Size: {size}, Brand: {brand}]")
            return device_full, size, brand

        # パターン2: ワーマ形式 - 機種の選択(ブランド)=機種名[サイズ]
        pattern2 = r'機種.*?\(([^)]+)\)=([^\[&\n\r]+)\[([^\]]+)\]'
        matches2 = re.findall(pattern2, options_text, re.MULTILINE)

        for brand_label, device_name, size in matches2:
            # デバイス名をクリーンアップ
            device_name = device_name.strip()
            size = size.strip()

            # ブランド判定
            brand = self._normalize_brand_label(brand_label)

            # ブランド名を追加（既に含まれていない場合）
            if brand and not device_name.startswith(brand):
                device_full = f"{brand} {device_name}"
            else:
                device_full = device_name

            logger.info(f"📱 Extracted from options (Wowma): {device_full} [Size: {size}, Brand: {brand}]")
            return device_full, size, brand

        return None, None, None

    def _normalize_brand_label(self, brand_label: str) -> Optional[str]:
        """ブランドラベルを正規化"""
        brand_label = brand_label.upper()

        if 'IPHONE' in brand_label:
            return 'iPhone'
        elif 'XPERIA' in brand_label:
            return 'Xperia'
        elif 'GALAXY' in brand_label:
            return 'Galaxy'
        elif 'AQUOS' in brand_label:
            return 'AQUOS'
        elif 'ARROWS' in brand_label:
            return 'arrows'
        elif 'PIXEL' in brand_label or 'GOOGLE' in brand_label or 'OPPO' in brand_label:
            return 'Pixel' if 'PIXEL' in brand_label or 'GOOGLE' in brand_label else 'OPPO'
        elif 'HUAWEI' in brand_label:
            return 'HUAWEI'
        else:
            # Other_1, Other_2 などはNone
            return None

    def detect_device_from_row(self, row: Dict[str, any]) -> Tuple[Optional[str], str, Optional[str]]:
        """
        CSV行データから機種を検出

        Args:
            row: CSV行データ（列名: 値の辞書）

        Returns:
            (機種名, 検出方法, ブランド名) のタプル
            検出方法: "options_column", "device_column", "product_name", "other_column", "not_found"
        """

        # ステップ0: 選択肢列から検出（最優先）
        for col_name, value in row.items():
            if value and ('選択肢' in col_name or 'options' in col_name.lower()):
                device, size, brand = self.extract_device_from_options(str(value))
                if device:
                    # サイズも一緒に返す（タプルの4番目の要素として）
                    return device, f"options_column:{col_name}", brand

        # ステップ1: 機種専用列から検出
        device, method, brand = self._detect_from_device_column(row)
        if device:
            return device, method, brand

        # ステップ2: 商品名列から検出
        device, brand = self._detect_from_product_name(row)
        if device:
            return device, "product_name", brand

        # ステップ3: その他の列から検出
        device, col_name, brand = self._detect_from_other_columns(row)
        if device:
            return device, f"other_column:{col_name}", brand

        # 検出失敗
        return None, "not_found", None

    def extract_size_from_product_name(
        self,
        product_name: str,
        product_type: str = None,
        brand: str = None,
        device: str = None,
        row: Dict[str, any] = None
    ) -> Tuple[Optional[str], str]:
        """
        商品名またはCSV行データからサイズ情報を抽出（手帳型のみ）

        優先順位:
        1. 選択肢列から抽出（row指定時）
        2. 正規表現で商品名から抽出
        3. Device Master DBから検索

        Args:
            product_name: 商品名
            product_type: 商品タイプ（extracted_memo）
            brand: ブランド名（Supabase検索用）
            device: 機種名（Supabase検索用）
            row: CSV行データ（選択肢列からの抽出用、オプション）

        Returns:
            (サイズ, 検出方法) のタプル
            検出方法: "options_column", "regex", "device_master_db", "not_found"

        例:
            選択肢列: 機種【iPhone】:iPhone 6[i6] → ("i6", "options_column")
            手帳型カバー/iPhone 8(mirror)_i6 → ("i6", "regex") (手帳型なのでサイズあり)
            ハードケース/wish4_特特大 → (None, "not_found") (ハードケースはサイズ不要)
            手帳型カバー/AQUOS wish4 → ("L", "device_master_db") (DBから取得)
        """
        # ハードケースの場合はサイズを返さない
        if product_type and 'ハードケース' in product_type:
            return None, "not_found"

        if product_name and 'ハードケース' in product_name:
            return None, "not_found"

        # ステップ0: 選択肢列から抽出（最優先）
        if row:
            for col_name, value in row.items():
                if value and ('選択肢' in col_name or 'options' in col_name.lower()):
                    _, size, _ = self.extract_device_from_options(str(value))
                    if size:
                        logger.info(f"📏 Size detected from options column: {size}")
                        return size, "options_column"

        # ステップ1: 楽天SKU管理システムDBからサイズを取得（商品番号/SKUから）
        if row and self.rakuten_sku:
            # SKU列を探す
            for col_name, value in row.items():
                if value and any(keyword in col_name.lower() for keyword in ['sku', '商品番号', '商品コード', '管理番号']):
                    sku_or_product_number = str(value).strip()
                    if sku_or_product_number:
                        # SKU番号で検索
                        size_from_sku = self.rakuten_sku.get_size_by_sku(sku_or_product_number)
                        if size_from_sku:
                            logger.info(f"📏 Size detected from 楽天SKU管理システム (SKU): {size_from_sku}")
                            return size_from_sku, "rakuten_sku_db"

                        # 商品番号で検索
                        size_from_pn = self.rakuten_sku.get_size_by_product_number(sku_or_product_number)
                        if size_from_pn:
                            logger.info(f"📏 Size detected from 楽天SKU管理システム (商品番号): {size_from_pn}")
                            return size_from_pn, "rakuten_sku_db"

        if not product_name:
            return None, "not_found"

        # ステップ2: "_" の後ろのサイズパターンを抽出（正規表現）
        size_pattern = r'_([0-9]?[LiM]+\d*|特{1,3}大|大|中|小|SS|LL|2L|3L)'
        match = re.search(size_pattern, product_name)
        if match:
            size = match.group(1)
            # 括弧の前まで（番号を除外）
            size = re.sub(r'\(.*?\)', '', size).strip()
            logger.info(f"🔍 Size detected by regex: {size}")
            return size, "regex"

        # ステップ3: 楽天SKU管理システムDBから機種名でサイズを検索
        if brand and device and self.rakuten_sku:
            size_from_device = self.rakuten_sku.get_size_by_device(brand=brand, device_name=device)
            if size_from_device:
                logger.info(f"📏 Size detected from 楽天SKU管理システム (機種名): {size_from_device}")
                return size_from_device, "rakuten_sku_device"

        # ステップ4: Device Master DBからサイズを検索（brandとdeviceが指定されている場合）
        # ローカルDB優先、Supabaseはオプション
        if brand and device and self.device_master:
            db_size = self.device_master.get_device_size(brand, device)
            if db_size:
                logger.info(f"📊 Size detected from Device Master DB: {db_size}")
                return db_size, "device_master_db"

        logger.debug(f"No size found for: {product_name}")
        return None, "not_found"

    def _detect_from_device_column(self, row: Dict) -> Tuple[Optional[str], str, Optional[str]]:
        """機種専用列から検出"""
        for col_name in row.keys():
            # 列名に機種キーワードが含まれているか
            if any(keyword in col_name for keyword in self.DEVICE_COLUMN_KEYWORDS):
                value = row.get(col_name)
                if value:
                    device, brand = self._extract_device_pattern(str(value))
                    if device:
                        logger.info(f"✓ Device detected from dedicated column '{col_name}': {device} (brand: {brand})")
                        return device, f"device_column:{col_name}", brand

        return None, "", None

    def _detect_from_product_name(self, row: Dict) -> Tuple[Optional[str], Optional[str]]:
        """商品名列から検出"""
        product_name_keys = ['商品名', 'product_name', '商品', 'product', 'Product', 'PRODUCT']

        for key in product_name_keys:
            if key in row and row[key]:
                device, brand = self._extract_device_pattern(str(row[key]))
                if device:
                    logger.info(f"✓ Device detected from product name: {device} (brand: {brand})")
                    return device, brand

        return None, None

    def _detect_from_other_columns(self, row: Dict) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """その他の列から検出"""
        # 優先順位付き列
        priority_columns = ['備考', 'notes', 'memo', '説明', 'description', '型番', 'model_number']

        # 優先列から検索
        for col_name in priority_columns:
            if col_name in row and row[col_name]:
                device, brand = self._extract_device_pattern(str(row[col_name]))
                if device:
                    logger.info(f"✓ Device detected from '{col_name}': {device} (brand: {brand})")
                    return device, col_name, brand

        # 全列を検索（優先列以外）
        for col_name, col_value in row.items():
            if col_name not in priority_columns and col_value:
                device, brand = self._extract_device_pattern(str(col_value))
                if device:
                    logger.info(f"✓ Device detected from '{col_name}': {device} (brand: {brand})")
                    return device, col_name, brand

        return None, None, None

    def _extract_device_pattern(self, text: str) -> Tuple[Optional[str], Optional[str]]:
        """テキストから機種パターンを抽出し、(機種名, ブランド名)を返す"""
        if not text or not isinstance(text, str):
            return None, None

        # ステップ1: テキストの前処理（ひらがな→英語変換）
        # これにより「いphone14Pro」→「iPhone14Pro」のように変換される
        normalized_text = self._pre_normalize_text(text)

        # ステップ2: すべてのパターンを試す
        for pattern, brand in self.DEVICE_PATTERNS:
            match = re.search(pattern, normalized_text, re.IGNORECASE)
            if match:
                device = match.group(0)
                # 最終正規化（ブランド名付加など）
                device = self._normalize_device_name(device, brand)
                return device, brand

        return None, None

    def _pre_normalize_text(self, text: str) -> str:
        """
        パターンマッチング前のテキスト前処理（ひらがな→英語変換）

        Amazon等の商品名で「いphone14Pro」のようなひらがな表記を正規化します。

        Args:
            text: 元のテキスト

        Returns:
            正規化されたテキスト
        """
        if not text:
            return text

        # ひらがな・カタカナ→英語変換
        replacements = {
            # ひらがな（商品名の誤表記対応）
            'いふぉん': 'iPhone',
            'あくおす': 'AQUOS',
            'えくすぺりあ': 'Xperia',
            'ぎゃらくしー': 'Galaxy',
            'ぴくせる': 'Pixel',
            # カタカナ
            'アイフォン': 'iPhone',
            'ギャラクシー': 'Galaxy',
            'エクスペリア': 'Xperia',
            'アクオス': 'AQUOS',
            'ピクセル': 'Pixel',
            'オッポ': 'OPPO',
            'アローズ': 'arrows',
        }

        for jp, en in replacements.items():
            text = text.replace(jp, en)

        # 先頭の「い」を「i」に変換（いPhone → iPhone）
        text = re.sub(r'^い([Pp]hone)', r'i\1', text)
        # 「スマQ いphone」のような途中の「い」も変換
        text = re.sub(r'\s+い([Pp]hone)', r' i\1', text)

        return text

    def _normalize_device_name(self, device: str, brand: str = None) -> str:
        """機種名を正規化してブランド名を付加"""
        # スペース統一
        device = re.sub(r'\s+', ' ', device.strip())

        # ひらがな・カタカナ→英語変換（念のため再度実行）
        replacements = {
            # ひらがな（商品名の誤表記対応）
            'いふぉん': 'iPhone',
            'あくおす': 'AQUOS',
            'えくすぺりあ': 'Xperia',
            'ぎゃらくしー': 'Galaxy',
            'ぴくせる': 'Pixel',
            # カタカナ
            'アイフォン': 'iPhone',
            'ギャラクシー': 'Galaxy',
            'エクスペリア': 'Xperia',
            'アクオス': 'AQUOS',
            'ピクセル': 'Pixel',
            'オッポ': 'OPPO',
            'アローズ': 'arrows',
            'プロ': ' Pro',
            'プラス': ' Plus',
            'ミニ': ' mini',
            'マックス': ' Max',
            'ウルトラ': ' Ultra',
        }

        for jp, en in replacements.items():
            device = device.replace(jp, en)

        # 先頭の「い」を削除（いPhone → iPhone）
        device = re.sub(r'^い([Pp]hone)', r'i\1', device)

        # 連続スペースを削除
        device = re.sub(r'\s+', ' ', device.strip())

        # ブランド名を追加（既にブランド名が含まれていない場合）
        if brand and brand not in ['iPhone', 'Pixel']:  # iPhone, Pixel は既にブランド名が含まれている
            # デバイス名の先頭にブランド名が既にあるかチェック
            if not device.upper().startswith(brand.upper()):
                device = f"{brand} {device}"

        return device

    def extract_notebook_structure(self, product_name: str) -> Optional[str]:
        """商品名から手帳構造タイプを抽出"""
        if not product_name:
            return None

        # 手帳タイプのパターン
        notebook_patterns = [
            '両面印刷薄型',
            '両面印刷厚いタイプ',
            '両面印刷厚い',
            'ベルト無し手帳型',
            'ベルト無し',
            'mirror',
            'ミラー付き',
        ]

        # 商品名が手帳系かチェック
        if not any(keyword in product_name for keyword in ['手帳', 'notebook', 'カバー', 'cover']):
            return None

        # パターンマッチング
        for pattern in notebook_patterns:
            if pattern in product_name:
                return pattern

        # "/" の後のテキストを抽出（例: "手帳型カバー / mirror"）
        if '/' in product_name:
            parts = product_name.split('/')
            if len(parts) >= 2:
                structure = parts[1].strip()
                # 括弧やデザイン名を除去
                structure = re.sub(r'\(.*?\)', '', structure).strip()
                if structure and len(structure) < 30:  # 長すぎる場合は除外
                    return structure

        return None

    def extract_design_number(self, product_name: str) -> Optional[str]:
        """
        商品名からデザイン番号を抽出

        Args:
            product_name: 商品名

        Returns:
            デザイン番号 または None

        パターン例:
            - betty-001-lec-bu
            - color_design_002-1
            - 花-001
            - rose-123
        """
        if not product_name:
            return None

        # デザイン番号パターン（優先度順）
        design_patterns = [
            # betty系（betty-001-lec-bu）
            r'betty-\d+-[a-z]+-[a-z]+',

            # color_design系（color_design_002-1）
            r'color_design_\d+-\d+',

            # 一般的な英数字パターン（rose-123, design-456）
            r'[a-zA-Z]+-\d+(?:-[a-zA-Z]+)?',

            # 日本語 + 番号（花-001）
            r'[ぁ-んァ-ヶー一-龠]+-\d+',
        ]

        for pattern in design_patterns:
            match = re.search(pattern, product_name)
            if match:
                design_no = match.group(0)
                logger.debug(f"🎨 Extracted design number: {design_no} from {product_name}")
                return design_no

        logger.debug(f"No design number found in: {product_name}")
        return None

    def get_product_type_from_design(self, product_name: str) -> Tuple[Optional[str], Optional[str]]:
        """
        商品名からデザイン番号を抽出し、デザインマスターから商品タイプを取得（ローカルDB優先）

        Args:
            product_name: 商品名

        Returns:
            (商品タイプ, デザイン番号) のタプル
        """
        # デザイン番号を抽出
        design_no = self.extract_design_number(product_name)
        if not design_no:
            return None, None

        # ローカルDBのデザインマスターから商品タイプを取得（優先）
        if self.design_master:
            product_type = self.design_master.get_product_type_by_design(design_no)
            if product_type:
                logger.info(f"🎨 Product type from local design master: {design_no} → {product_type}")
                return product_type, design_no

        logger.debug(f"No product type found for design: {design_no}")
        return None, design_no

    def get_product_type_by_sku(self, sku: str) -> Optional[str]:
        """
        商品番号（SKU）から直接デザインマスターで商品タイプを取得（ローカルDB優先）

        Args:
            sku: 商品番号（Amazon SKU等）

        Returns:
            商品タイプ または None
        """
        if not sku or not sku.strip():
            return None

        # ローカルDBのデザインマスターから商品タイプを取得（優先）
        if self.design_master:
            product_type = self.design_master.get_product_type_by_design(sku.strip())
            if product_type:
                logger.info(f"🎨 Product type from SKU (local DB): {sku} → {product_type}")
                return product_type

        logger.debug(f"No product type found for SKU: {sku}")
        return None

    def validate_all_rows(self, rows: List[Dict]) -> Tuple[List[Dict], List[Dict]]:
        """
        全行の機種検出を検証

        Args:
            rows: CSV行データのリスト

        Returns:
            (成功行リスト, エラー行リスト)
        """
        success_rows = []
        error_rows = []

        for idx, row in enumerate(rows):
            device, method = self.detect_device_from_row(row)

            if device:
                row['_detected_device'] = device
                row['_device_detection_method'] = method

                # 手帳構造タイプも抽出
                if '商品名' in row:
                    notebook_structure = self.extract_notebook_structure(row['商品名'])
                    row['_detected_notebook_structure'] = notebook_structure

                success_rows.append(row)
            else:
                error_rows.append({
                    'row_number': idx + 1,
                    'row_data': row,
                    'error': '機種情報を検出できませんでした'
                })

        return success_rows, error_rows
