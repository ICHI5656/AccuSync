"""Product Type Learning Service - Machine Learning based product type prediction"""

import logging
import re
from typing import Optional, List, Tuple, Dict
from sqlalchemy.orm import Session
from sqlalchemy import text, desc

from app.models.product_type_pattern import ProductTypePattern

logger = logging.getLogger(__name__)


class ProductTypeLearningService:
    """
    商品タイプの学習・予測サービス

    ユーザーが手動で変更した商品タイプのパターンを学習し、
    次回のインポート時に自動的に商品タイプを予測します。

    学習方法:
    1. 商品名から特徴的なキーワードを抽出
    2. パターンとして保存（例: "ハードケース" → "ハードケース"）
    3. 次回のインポート時に、パターンマッチングで商品タイプを予測

    予測方法:
    1. 商品名に含まれるパターンを検索
    2. マッチしたパターンの中で最も信頼度が高いものを選択
    3. 使用回数をインクリメント
    """

    def __init__(self, db: Session):
        self.db = db

    def learn_from_product_name(
        self,
        product_name: str,
        product_type: str,
        source: str = 'manual'
    ) -> ProductTypePattern:
        """
        商品名から商品タイプのパターンを学習

        Args:
            product_name: 商品名（例: "手帳型カバー/mirror(刺繍風プリント)"）
            product_type: 商品タイプ（例: "手帳型カバー"）
            source: 'manual'（手動）または 'auto'（自動学習）

        Returns:
            作成または更新されたProductTypePattern
        """
        # 商品名から特徴的なパターンを抽出
        patterns = self._extract_patterns(product_name, product_type)

        # 最も代表的なパターンを選択（商品タイプそのもの）
        main_pattern = product_type

        # 既存のパターンを検索
        existing = self.db.query(ProductTypePattern).filter(
            ProductTypePattern.pattern == main_pattern,
            ProductTypePattern.product_type == product_type
        ).first()

        if existing:
            # 既存のパターンを更新（信頼度を上げる）
            existing.usage_count += 1
            existing.confidence = min(1.0, existing.confidence + 0.05)  # 最大1.0
            self.db.commit()
            self.db.refresh(existing)
            logger.info(f"✏️ Updated pattern: {main_pattern} → {product_type} (confidence: {existing.confidence:.2f})")
            return existing
        else:
            # 新しいパターンを作成
            new_pattern = ProductTypePattern(
                pattern=main_pattern,
                product_type=product_type,
                confidence=0.9 if source == 'manual' else 0.7,  # 手動は高信頼度
                source=source,
                usage_count=1
            )
            self.db.add(new_pattern)
            self.db.commit()
            self.db.refresh(new_pattern)
            logger.info(f"📚 Learned new pattern: {main_pattern} → {product_type}")
            return new_pattern

    def predict_product_type(self, product_name: str) -> Optional[Tuple[str, float, str]]:
        """
        商品名から商品タイプを予測

        Args:
            product_name: 商品名

        Returns:
            (product_type, confidence, detection_method) のタプル
            見つからない場合は None
        """
        if not product_name:
            return None

        # 商品名を正規化
        normalized_name = product_name.lower().strip()

        # すべてのパターンを取得（信頼度順）
        patterns = self.db.query(ProductTypePattern).order_by(
            desc(ProductTypePattern.confidence),
            desc(ProductTypePattern.usage_count)
        ).all()

        # パターンマッチング（部分一致）
        best_match = None
        best_confidence = 0.0

        for pattern_obj in patterns:
            pattern = pattern_obj.pattern.lower()

            if pattern in normalized_name:
                # マッチした場合
                if pattern_obj.confidence > best_confidence:
                    best_match = pattern_obj
                    best_confidence = pattern_obj.confidence

        if best_match:
            # 使用回数をインクリメント
            best_match.usage_count += 1
            self.db.commit()

            logger.info(f"🎯 Predicted: {product_name} → {best_match.product_type} (confidence: {best_confidence:.2f})")
            return (best_match.product_type, best_confidence, f'ml_{best_match.source}')

        return None

    def _extract_patterns(self, product_name: str, product_type: str) -> List[str]:
        """
        商品名から特徴的なパターンを抽出

        Args:
            product_name: 商品名
            product_type: 商品タイプ

        Returns:
            パターンのリスト
        """
        patterns = []

        # 1. 商品タイプそのもの
        patterns.append(product_type)

        # 2. 商品名の最初の部分（デザイン名より前）
        if '/' in product_name:
            first_part = product_name.split('/')[0].strip()
            if first_part and first_part != product_type:
                patterns.append(first_part)

        # 3. カッコ内を除去したもの
        cleaned = re.sub(r'\([^)]+\)', '', product_name).strip()
        if cleaned and cleaned != product_type:
            patterns.append(cleaned)

        return patterns

    def get_all_patterns(self) -> List[ProductTypePattern]:
        """すべての学習パターンを取得"""
        return self.db.query(ProductTypePattern).order_by(
            desc(ProductTypePattern.confidence),
            desc(ProductTypePattern.usage_count)
        ).all()

    def get_patterns_by_type(self, product_type: str) -> List[ProductTypePattern]:
        """特定の商品タイプのパターンを取得"""
        return self.db.query(ProductTypePattern).filter(
            ProductTypePattern.product_type == product_type
        ).order_by(
            desc(ProductTypePattern.confidence)
        ).all()

    def delete_pattern(self, pattern_id: int) -> bool:
        """パターンを削除"""
        pattern = self.db.query(ProductTypePattern).filter(
            ProductTypePattern.id == pattern_id
        ).first()

        if pattern:
            self.db.delete(pattern)
            self.db.commit()
            logger.info(f"🗑️ Deleted pattern: {pattern.pattern} → {pattern.product_type}")
            return True

        return False

    def get_statistics(self) -> Dict[str, any]:
        """学習パターンの統計情報を取得"""
        total_patterns = self.db.query(ProductTypePattern).count()

        manual_patterns = self.db.query(ProductTypePattern).filter(
            ProductTypePattern.source == 'manual'
        ).count()

        auto_patterns = self.db.query(ProductTypePattern).filter(
            ProductTypePattern.source == 'auto'
        ).count()

        total_usage = self.db.execute(
            text("SELECT SUM(usage_count) FROM product_type_patterns")
        ).scalar() or 0

        return {
            'total_patterns': total_patterns,
            'manual_patterns': manual_patterns,
            'auto_patterns': auto_patterns,
            'total_usage': total_usage
        }
