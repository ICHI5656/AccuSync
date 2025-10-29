"""
Device Detection Service - 機種検出サービス

正規表現とSupabase DBを使用して、CSVから機種情報を抽出します。
"""

import re
import logging
from typing import Optional, Dict, Tuple, List
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

# Supabase統合は一時的にオプション（Dockerビルド問題解決後に有効化）
try:
    from app.services.supabase_service import SupabaseService
    SUPABASE_AVAILABLE = True
except ImportError:
    SUPABASE_AVAILABLE = False
    logger.warning("Supabase service not available - size lookup from DB will be disabled")


class DeviceDetectionService:
    """機種検出サービス（正規表現ベース）"""

    # 機種検出パターン（優先度順）
    DEVICE_PATTERNS = [
        # iPhone系（柔軟なパターン）
        (r'i?Phone\s*\d{1,2}(?:\s*(?:Pro(?:\s*Max)?|Plus|mini))?', 'iPhone'),
        (r'アイフォン\s*\d{1,2}(?:\s*(?:プロ|プラス|ミニ|マックス))?', 'iPhone'),

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

        # AQUOS系（ブランド名付き）
        (r'AQUOS\s*(?:sense|R|zero|wish|ゼロ|センス)\d*(?:\s*(?:plus|\+|プラス))?', 'AQUOS'),
        (r'アクオス\s*(?:sense|R|zero|wish|センス|ゼロ)?\d*', 'AQUOS'),

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
        self.supabase = SupabaseService() if SUPABASE_AVAILABLE else None

    def detect_device_from_row(self, row: Dict[str, any]) -> Tuple[Optional[str], str, Optional[str]]:
        """
        CSV行データから機種を検出

        Args:
            row: CSV行データ（列名: 値の辞書）

        Returns:
            (機種名, 検出方法, ブランド名) のタプル
            検出方法: "device_column", "product_name", "other_column", "not_found"
        """

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
        device: str = None
    ) -> Tuple[Optional[str], str]:
        """
        商品名からサイズ情報を抽出（手帳型のみ）
        正規表現で見つからない場合はSupabase DBから検索

        Args:
            product_name: 商品名
            product_type: 商品タイプ（extracted_memo）
            brand: ブランド名（Supabase検索用）
            device: 機種名（Supabase検索用）

        Returns:
            (サイズ, 検出方法) のタプル
            検出方法: "regex", "supabase_db", "not_found"

        例:
            手帳型カバー/iPhone 8(mirror)_i6 → ("i6", "regex") (手帳型なのでサイズあり)
            ハードケース/wish4_特特大 → (None, "not_found") (ハードケースはサイズ不要)
            手帳型カバー/AQUOS wish4 → ("L", "supabase_db") (DBから取得)
        """
        if not product_name:
            return None, "not_found"

        # ハードケースの場合はサイズを返さない
        if product_type and 'ハードケース' in product_type:
            return None, "not_found"

        # 商品名に「ハードケース」が含まれる場合もサイズ不要
        if 'ハードケース' in product_name:
            return None, "not_found"

        # ステップ1: "_" の後ろのサイズパターンを抽出（正規表現）
        size_pattern = r'_([0-9]?[LiM]+\d*|特{1,3}大|大|中|小)'
        match = re.search(size_pattern, product_name)
        if match:
            size = match.group(1)
            # 括弧の前まで（番号を除外）
            size = re.sub(r'\(.*?\)', '', size).strip()
            logger.info(f"🔍 Size detected by regex: {size}")
            return size, "regex"

        # ステップ2: Supabase DBからサイズを検索（brandとdeviceが指定されている場合）
        if brand and device and self.supabase:
            db_size = self.supabase.get_device_size(brand, device)
            if db_size:
                logger.info(f"📊 Size detected from Supabase DB: {db_size}")
                return db_size, "supabase_db"

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

        # すべてのパターンを試す
        for pattern, brand in self.DEVICE_PATTERNS:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                device = match.group(0)
                # 正規化
                device = self._normalize_device_name(device, brand)
                return device, brand

        return None, None

    def _normalize_device_name(self, device: str, brand: str = None) -> str:
        """機種名を正規化してブランド名を付加"""
        # スペース統一
        device = re.sub(r'\s+', ' ', device.strip())

        # カタカナ→英語変換
        replacements = {
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
