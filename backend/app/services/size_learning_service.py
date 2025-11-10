"""
サイズ学習サービス - ユーザーの手動変更からサイズパターンを学習

ユーザーが手動で変更したサイズ情報をパターンとして保存し、
次回のインポート時に自動的に適用します。
手帳型カバーのみが対象です。
"""

import logging
import re
from typing import Optional, Tuple, List, Dict
from sqlalchemy.orm import Session
from app.models.size_pattern import SizePattern

logger = logging.getLogger(__name__)


class SizeLearningService:
    """サイズ学習サービス"""

    def __init__(self, db: Session):
        self.db = db

    def learn_from_product_name(
        self,
        product_name: str,
        size: str,
        device_name: str = None,
        brand: str = None,
        source: str = "manual"
    ) -> Optional[SizePattern]:
        """
        商品名からサイズパターンを学習

        Args:
            product_name: 商品名（例: "手帳型カバー/iPhone 8(mirror)_i6"）
            size: サイズ（例: "i6", "L", "M"）
            device_name: 機種名（例: "iPhone 8"）
            brand: ブランド名（例: "iPhone"）
            source: 学習元（'manual' or 'auto'）

        Returns:
            学習されたSizePatternオブジェクト、または既存のパターン
        """
        if not product_name or not size:
            logger.warning("商品名またはサイズが空です")
            return None

        # パターンを抽出（商品名からキーワード抽出）
        pattern = self._extract_pattern(product_name, size, device_name)

        if not pattern:
            logger.warning(f"パターンを抽出できませんでした: {product_name}")
            return None

        # 既存のパターンを確認（パターン + 機種名 + サイズで一意）
        query = self.db.query(SizePattern).filter(
            SizePattern.pattern == pattern,
            SizePattern.size == size
        )

        if device_name:
            query = query.filter(SizePattern.device_name == device_name)

        existing = query.first()

        if existing:
            # 既存パターンの信頼度を上昇（最大1.0）
            if existing.confidence < 1.0:
                existing.confidence = min(existing.confidence + 0.05, 1.0)
                existing.usage_count += 1
                self.db.commit()
                logger.info(
                    f"📏 サイズパターン更新: {pattern} + {device_name or '機種なし'} → {size} "
                    f"(信頼度: {existing.confidence:.2f})"
                )
            return existing

        # 新規パターンを作成
        confidence = 0.9 if source == 'manual' else 0.7

        new_pattern = SizePattern(
            pattern=pattern,
            size=size,
            device_name=device_name,
            brand=brand,
            confidence=confidence,
            source=source,
            usage_count=1
        )

        self.db.add(new_pattern)
        self.db.commit()
        self.db.refresh(new_pattern)

        logger.info(
            f"📏 サイズパターン学習: {pattern} + {device_name or '機種なし'} → {size} "
            f"(ブランド: {brand}, 信頼度: {confidence})"
        )

        return new_pattern

    def predict_size(
        self,
        product_name: str,
        device_name: str = None
    ) -> Optional[Tuple[str, float, str]]:
        """
        商品名と機種名からサイズを予測

        Args:
            product_name: 商品名
            device_name: 機種名（オプション、指定すると精度が上がる）

        Returns:
            (サイズ, 信頼度, 検出方法) のタプル、または None

        検出方法: "ml_manual" (手動学習) or "ml_auto" (自動学習)
        """
        if not product_name:
            return None

        # すべてのパターンを取得（信頼度が高い順）
        query = self.db.query(SizePattern).order_by(
            SizePattern.confidence.desc(),
            SizePattern.usage_count.desc()
        )

        # 機種名が指定されている場合は、機種名でフィルタリング（優先）
        if device_name:
            device_patterns = query.filter(
                SizePattern.device_name == device_name
            ).all()

            for pattern_obj in device_patterns:
                if pattern_obj.pattern.lower() in product_name.lower():
                    # 使用回数をインクリメント
                    pattern_obj.usage_count += 1

                    # 信頼度を微増（最大1.0）
                    if pattern_obj.confidence < 1.0:
                        pattern_obj.confidence = min(pattern_obj.confidence + 0.05, 1.0)

                    self.db.commit()

                    method = f"ml_{pattern_obj.source}_device"
                    logger.info(
                        f"📏 サイズ予測成功（機種一致）: {product_name[:30]}... + {device_name} → {pattern_obj.size} "
                        f"(パターン: {pattern_obj.pattern}, 信頼度: {pattern_obj.confidence:.2f}, 方法: {method})"
                    )

                    return pattern_obj.size, pattern_obj.confidence, method

        # 機種名なしのパターンでも試す
        all_patterns = query.all()
        for pattern_obj in all_patterns:
            if pattern_obj.pattern.lower() in product_name.lower():
                # 使用回数をインクリメント
                pattern_obj.usage_count += 1

                # 信頼度を微増（最大1.0）
                if pattern_obj.confidence < 1.0:
                    pattern_obj.confidence = min(pattern_obj.confidence + 0.05, 1.0)

                self.db.commit()

                method = f"ml_{pattern_obj.source}"
                logger.info(
                    f"📏 サイズ予測成功: {product_name[:30]}... → {pattern_obj.size} "
                    f"(パターン: {pattern_obj.pattern}, 信頼度: {pattern_obj.confidence:.2f}, 方法: {method})"
                )

                return pattern_obj.size, pattern_obj.confidence, method

        logger.debug(f"サイズ予測失敗: {product_name[:50]}...")
        return None

    def get_all_patterns(self) -> List[SizePattern]:
        """すべての学習パターンを取得"""
        return self.db.query(SizePattern).order_by(
            SizePattern.confidence.desc(),
            SizePattern.usage_count.desc()
        ).all()

    def get_patterns_by_size(self, size: str) -> List[SizePattern]:
        """特定のサイズのパターンを取得"""
        return self.db.query(SizePattern).filter(
            SizePattern.size == size
        ).order_by(
            SizePattern.confidence.desc()
        ).all()

    def delete_pattern(self, pattern_id: int) -> bool:
        """パターンを削除"""
        pattern = self.db.query(SizePattern).filter(SizePattern.id == pattern_id).first()
        if pattern:
            self.db.delete(pattern)
            self.db.commit()
            logger.info(f"🗑️ サイズパターン削除: {pattern.pattern} → {pattern.size}")
            return True
        return False

    def get_statistics(self) -> Dict:
        """学習統計を取得"""
        total_patterns = self.db.query(SizePattern).count()
        manual_patterns = self.db.query(SizePattern).filter(SizePattern.source == 'manual').count()
        auto_patterns = self.db.query(SizePattern).filter(SizePattern.source == 'auto').count()
        total_usage = self.db.query(SizePattern).with_entities(
            self.db.func.sum(SizePattern.usage_count)
        ).scalar() or 0

        return {
            'total_patterns': total_patterns,
            'manual_patterns': manual_patterns,
            'auto_patterns': auto_patterns,
            'total_usage': total_usage
        }

    def _extract_pattern(
        self,
        product_name: str,
        size: str,
        device_name: str = None
    ) -> Optional[str]:
        """
        商品名からサイズパターンを抽出

        Args:
            product_name: 商品名（例: "手帳型カバー/iPhone 8(mirror)_i6"）
            size: サイズ（例: "i6"）
            device_name: 機種名（例: "iPhone 8"）

        Returns:
            抽出されたパターン（例: "手帳型カバー/iPhone 8"）

        優先順位:
        1. サイズが含まれている部分の前まで
        2. 機種名が含まれている部分まで
        3. 商品名全体の一部
        """
        if not product_name or not size:
            return None

        # パターン1: "_サイズ" の前まで
        size_pattern = f"_{size}"
        if size_pattern in product_name:
            idx = product_name.find(size_pattern)
            pattern = product_name[:idx]
            if len(pattern) >= 3:
                return pattern

        # パターン2: 機種名が含まれている場合、その部分まで
        if device_name and device_name in product_name:
            idx = product_name.find(device_name)
            # 機種名を含む部分まで
            end_idx = idx + len(device_name)
            pattern = product_name[:end_idx]
            if len(pattern) >= 3:
                return pattern

        # パターン3: 最初の30文字（括弧やスペースを削除）
        clean_name = re.sub(r'[\s]', '', product_name)
        if len(clean_name) > 30:
            return clean_name[:30]
        return clean_name if len(clean_name) >= 3 else None
