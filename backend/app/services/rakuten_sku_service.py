"""
楽天SKU管理システム連携サービス

csv_sku.k プロジェクトのDBから商品属性（サイズ情報）を取得します。
手帳型商品のサイズ分類（i6, L, M, SS, S, LL, 2L, 3L など）を抽出します。
"""

import logging
import sqlite3
from typing import Optional, Dict
from pathlib import Path

logger = logging.getLogger(__name__)


class RakutenSKUService:
    """楽天SKU管理システムDB連携サービス"""

    def __init__(self, db_path: str = None):
        """
        Args:
            db_path: 楽天SKU管理システムのDBパス
                    デフォルト: /external_data/csv_sku.k/inventory.db (Docker環境)
                    フォールバック: /mnt/c/Users/info/Desktop/sin/csv_sku.k/data/inventory.db (ホスト環境)
        """
        if db_path is None:
            # デフォルトパス（Docker環境）
            docker_path = Path("/external_data/csv_sku.k/inventory.db")
            # フォールバックパス（ホスト環境）
            host_path = Path("/mnt/c/Users/info/Desktop/sin/csv_sku.k/data/inventory.db")

            if docker_path.exists():
                self.db_path = str(docker_path)
                logger.info(f"✅ 楽天SKU管理システムDB接続（Docker環境）: {self.db_path}")
            elif host_path.exists():
                self.db_path = str(host_path)
                logger.info(f"✅ 楽天SKU管理システムDB接続（ホスト環境）: {self.db_path}")
            else:
                self.db_path = None
                logger.warning("⚠️ 楽天SKU管理システムDBが見つかりません")
        else:
            self.db_path = db_path

    def get_size_by_sku(self, sku: str) -> Optional[str]:
        """
        SKU番号から手帳型のサイズを取得

        Args:
            sku: SKU番号（例: "sku_r00001"）

        Returns:
            サイズ分類（i6, L, M, SS, S, LL, 2L, 3L など）またはNone
        """
        if not self.db_path or not sku:
            return None

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # techo_productsテーブルからサイズを取得
            cursor.execute("""
                SELECT size_classification, techo_type, compatible_device
                FROM techo_products
                WHERE sku = ? AND is_active = 1
                LIMIT 1
            """, (sku,))

            result = cursor.fetchone()
            conn.close()

            if result:
                size, techo_type, device = result
                if size:
                    logger.info(
                        f"📏 楽天SKU管理システムからサイズ取得: "
                        f"{sku} → サイズ={size}, タイプ={techo_type}, 機種={device}"
                    )
                    return size

            logger.debug(f"楽天SKU管理システムでサイズが見つかりません: {sku}")
            return None

        except Exception as e:
            logger.error(f"❌ 楽天SKU管理システムDB検索エラー ({sku}): {e}")
            return None

    def get_product_info_by_sku(self, sku: str) -> Optional[Dict]:
        """
        SKU番号から手帳型商品の詳細情報を取得

        Args:
            sku: SKU番号

        Returns:
            商品情報（size_classification, techo_type, compatible_device, color_name など）
        """
        if not self.db_path or not sku:
            return None

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # techo_productsテーブルから詳細情報を取得
            cursor.execute("""
                SELECT
                    sku,
                    product_id,
                    techo_type,
                    size_classification,
                    compatible_device,
                    color_code,
                    color_name,
                    stock_quantity,
                    selling_price
                FROM techo_products
                WHERE sku = ? AND is_active = 1
                LIMIT 1
            """, (sku,))

            result = cursor.fetchone()
            conn.close()

            if result:
                info = {
                    'sku': result[0],
                    'product_id': result[1],
                    'techo_type': result[2],
                    'size_classification': result[3],
                    'compatible_device': result[4],
                    'color_code': result[5],
                    'color_name': result[6],
                    'stock_quantity': result[7],
                    'selling_price': result[8]
                }
                logger.info(f"📦 楽天SKU管理システムから商品情報取得: {sku} → {info}")
                return info

            logger.debug(f"楽天SKU管理システムで商品が見つかりません: {sku}")
            return None

        except Exception as e:
            logger.error(f"❌ 楽天SKU管理システムDB検索エラー ({sku}): {e}")
            return None

    def get_size_by_product_number(self, product_number: str) -> Optional[str]:
        """
        商品番号から手帳型のサイズを取得（product_mastersテーブル経由）

        Args:
            product_number: 商品番号（例: "ami_kaiser-A_1r-A"）

        Returns:
            サイズ分類（i6, L, M など）またはNone
        """
        if not self.db_path or not product_number:
            return None

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # product_mastersテーブルから商品情報を取得
            cursor.execute("""
                SELECT pm.available_sizes, pm.product_type, pm.product_name
                FROM product_masters pm
                WHERE pm.product_number = ? AND pm.is_active = 1
                LIMIT 1
            """, (product_number,))

            result = cursor.fetchone()
            conn.close()

            if result:
                available_sizes, product_type, product_name = result

                # 手帳型の場合のみサイズを返す
                if product_type and '手帳' in product_type:
                    if available_sizes:
                        # available_sizesはカンマ区切りの可能性がある
                        # 例: "i6,L,M" → 最初のサイズを返す
                        size = available_sizes.split(',')[0].strip()
                        logger.info(
                            f"📏 楽天SKU管理システム（商品番号）からサイズ取得: "
                            f"{product_number} → {size}"
                        )
                        return size

            logger.debug(f"楽天SKU管理システムでサイズが見つかりません: {product_number}")
            return None

        except Exception as e:
            logger.error(f"❌ 楽天SKU管理システムDB検索エラー ({product_number}): {e}")
            return None

    def get_size_by_device(self, brand: str = None, device_name: str = None) -> Optional[str]:
        """
        機種名からサイズを取得（devicesテーブル経由）

        Args:
            brand: ブランド名（例: "iPhone", "AQUOS"）
            device_name: 機種名（例: "iPhone 15 Pro", "AQUOS wish4"）

        Returns:
            サイズコード（i6, L, M, SS, S, LL, 2L, 3L など）またはNone
        """
        if not self.db_path or not device_name:
            return None

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # devicesテーブルとtecho_sizesテーブルをJOINして検索
            if brand:
                # ブランド名と機種名の両方で検索（完全一致）
                cursor.execute("""
                    SELECT ts.size_code, ts.size_name
                    FROM devices d
                    LEFT JOIN brands b ON d.brand_id = b.id
                    LEFT JOIN techo_sizes ts ON d.techo_size_id = ts.id
                    WHERE d.is_active = 1
                      AND (b.name = ? OR b.display_name = ?)
                      AND d.device_name = ?
                    LIMIT 1
                """, (brand, brand, device_name))

                result = cursor.fetchone()
                if result and result[0]:
                    size_code, size_name = result
                    conn.close()
                    logger.info(
                        f"📏 楽天SKU管理システム（機種）からサイズ取得: "
                        f"{brand} {device_name} → {size_code} ({size_name})"
                    )
                    return size_code

                # 部分一致で検索（機種名のみ）
                cursor.execute("""
                    SELECT ts.size_code, ts.size_name
                    FROM devices d
                    LEFT JOIN brands b ON d.brand_id = b.id
                    LEFT JOIN techo_sizes ts ON d.techo_size_id = ts.id
                    WHERE d.is_active = 1
                      AND (b.name = ? OR b.display_name = ?)
                      AND d.device_name LIKE ?
                    LIMIT 1
                """, (brand, brand, f'%{device_name}%'))

                result = cursor.fetchone()
                if result and result[0]:
                    size_code, size_name = result
                    conn.close()
                    logger.info(
                        f"📏 楽天SKU管理システム（機種・部分一致）からサイズ取得: "
                        f"{brand} {device_name} → {size_code} ({size_name})"
                    )
                    return size_code

            # ブランド名なしで機種名のみで検索
            cursor.execute("""
                SELECT ts.size_code, ts.size_name
                FROM devices d
                LEFT JOIN techo_sizes ts ON d.techo_size_id = ts.id
                WHERE d.is_active = 1
                  AND (d.device_name = ? OR d.device_name LIKE ?)
                LIMIT 1
            """, (device_name, f'%{device_name}%'))

            result = cursor.fetchone()
            conn.close()

            if result and result[0]:
                size_code, size_name = result
                logger.info(
                    f"📏 楽天SKU管理システム（機種のみ）からサイズ取得: "
                    f"{device_name} → {size_code} ({size_name})"
                )
                return size_code

            logger.debug(f"楽天SKU管理システムでサイズが見つかりません: {brand} {device_name}")
            return None

        except Exception as e:
            logger.error(f"❌ 楽天SKU管理システムDB検索エラー ({brand} {device_name}): {e}")
            return None

    def get_product_type_by_design_number(self, design_number: str) -> Optional[str]:
        """
        デザイン番号から商品タイプを取得（product_mastersテーブル経由）

        Args:
            design_number: デザイン番号/商品番号（例: "ami_kaiser-A_1r-A", "betty-001"）

        Returns:
            商品タイプ（手帳型, ハードケース など）またはNone
        """
        if not self.db_path or not design_number:
            return None

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # product_mastersテーブルから商品タイプを取得（完全一致）
            cursor.execute("""
                SELECT product_type, product_name
                FROM product_masters
                WHERE product_number = ? AND is_active = 1
                LIMIT 1
            """, (design_number,))

            result = cursor.fetchone()

            if result and result[0]:
                product_type, product_name = result
                conn.close()
                logger.info(
                    f"🎨 楽天SKU管理システムから商品タイプ取得: "
                    f"{design_number} → {product_type}"
                )
                return product_type

            # 部分一致で検索（デザイン番号の前方一致）
            cursor.execute("""
                SELECT product_type, product_name
                FROM product_masters
                WHERE product_number LIKE ? AND is_active = 1
                LIMIT 1
            """, (f'{design_number}%',))

            result = cursor.fetchone()
            conn.close()

            if result and result[0]:
                product_type, product_name = result
                logger.info(
                    f"🎨 楽天SKU管理システムから商品タイプ取得（部分一致）: "
                    f"{design_number} → {product_type}"
                )
                return product_type

            logger.debug(f"楽天SKU管理システムで商品タイプが見つかりません: {design_number}")
            return None

        except Exception as e:
            logger.error(f"❌ 楽天SKU管理システムDB検索エラー ({design_number}): {e}")
            return None

    def test_connection(self) -> bool:
        """接続テスト"""
        if not self.db_path:
            logger.error("❌ 楽天SKU管理システムDBパスが設定されていません")
            return False

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()

            # techo_productsテーブルの件数を取得
            cursor.execute("SELECT COUNT(*) FROM techo_products")
            count = cursor.fetchone()[0]

            conn.close()

            logger.info(f"✅ 楽天SKU管理システムDB接続成功: techo_products={count}件")
            return True

        except Exception as e:
            logger.error(f"❌ 楽天SKU管理システムDB接続失敗: {e}")
            return False

    def is_available(self) -> bool:
        """サービスが利用可能かチェック"""
        return self.db_path is not None
