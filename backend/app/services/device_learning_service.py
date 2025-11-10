"""
機種学習サービス - ユーザーの手動変更から機種パターンを学習

ユーザーが手動で変更した機種情報をパターンとして保存し、
次回のインポート時に自動的に適用します。
"""

import logging
import re
from typing import Optional, Tuple, List, Dict
from sqlalchemy.orm import Session
from app.models.device_pattern import DevicePattern

logger = logging.getLogger(__name__)


class DeviceLearningService:
    """機種学習サービス"""

    def __init__(self, db: Session):
        self.db = db

    def learn_from_product_name(
        self,
        product_name: str,
        device_name: str,
        brand: str = None,
        source: str = "manual"
    ) -> Optional[DevicePattern]:
        """
        商品名から機種パターンを学習

        Args:
            product_name: 商品名（例: "スマQ いphone14Pro 対応 ケース"）
            device_name: 機種名（例: "iPhone 14 Pro"）
            brand: ブランド名（例: "iPhone"）
            source: 学習元（'manual' or 'auto'）

        Returns:
            学習されたDevicePatternオブジェクト、または既存のパターン
        """
        if not product_name or not device_name:
            logger.warning("商品名または機種名が空です")
            return None

        # パターンを抽出（商品名からキーワード抽出）
        pattern = self._extract_pattern(product_name, device_name)

        if not pattern:
            logger.warning(f"パターンを抽出できませんでした: {product_name}")
            return None

        # 既存のパターンを確認
        existing = self.db.query(DevicePattern).filter(
            DevicePattern.pattern == pattern,
            DevicePattern.device_name == device_name
        ).first()

        if existing:
            # 既存パターンの信頼度を上昇（最大1.0）
            if existing.confidence < 1.0:
                existing.confidence = min(existing.confidence + 0.05, 1.0)
                existing.usage_count += 1
                self.db.commit()
                logger.info(f"📚 機種パターン更新: {pattern} → {device_name} (信頼度: {existing.confidence:.2f})")
            return existing

        # 新規パターンを作成
        confidence = 0.9 if source == 'manual' else 0.7

        new_pattern = DevicePattern(
            pattern=pattern,
            device_name=device_name,
            brand=brand,
            confidence=confidence,
            source=source,
            usage_count=1
        )

        self.db.add(new_pattern)
        self.db.commit()
        self.db.refresh(new_pattern)

        logger.info(f"📚 機種パターン学習: {pattern} → {device_name} (ブランド: {brand}, 信頼度: {confidence})")

        return new_pattern

    def predict_device(self, product_name: str) -> Optional[Tuple[str, str, float, str]]:
        """
        商品名から機種を予測

        Args:
            product_name: 商品名

        Returns:
            (機種名, ブランド, 信頼度, 検出方法) のタプル、または None

        検出方法: "ml_manual" (手動学習) or "ml_auto" (自動学習)
        """
        if not product_name:
            return None

        # すべてのパターンを取得（信頼度が高い順）
        patterns = self.db.query(DevicePattern).order_by(
            DevicePattern.confidence.desc(),
            DevicePattern.usage_count.desc()
        ).all()

        # 商品名にパターンが含まれているかチェック（部分一致）
        for pattern_obj in patterns:
            if pattern_obj.pattern.lower() in product_name.lower():
                # 使用回数をインクリメント
                pattern_obj.usage_count += 1

                # 信頼度を微増（最大1.0）
                if pattern_obj.confidence < 1.0:
                    pattern_obj.confidence = min(pattern_obj.confidence + 0.05, 1.0)

                self.db.commit()

                method = f"ml_{pattern_obj.source}"
                logger.info(
                    f"🎯 機種予測成功: {product_name[:30]}... → {pattern_obj.device_name} "
                    f"(パターン: {pattern_obj.pattern}, 信頼度: {pattern_obj.confidence:.2f}, 方法: {method})"
                )

                return pattern_obj.device_name, pattern_obj.brand, pattern_obj.confidence, method

        logger.debug(f"機種予測失敗: {product_name[:50]}...")
        return None

    def get_all_patterns(self) -> List[DevicePattern]:
        """すべての学習パターンを取得"""
        return self.db.query(DevicePattern).order_by(
            DevicePattern.confidence.desc(),
            DevicePattern.usage_count.desc()
        ).all()

    def get_patterns_by_device(self, device_name: str) -> List[DevicePattern]:
        """特定の機種のパターンを取得"""
        return self.db.query(DevicePattern).filter(
            DevicePattern.device_name == device_name
        ).order_by(
            DevicePattern.confidence.desc()
        ).all()

    def delete_pattern(self, pattern_id: int) -> bool:
        """パターンを削除"""
        pattern = self.db.query(DevicePattern).filter(DevicePattern.id == pattern_id).first()
        if pattern:
            self.db.delete(pattern)
            self.db.commit()
            logger.info(f"🗑️ 機種パターン削除: {pattern.pattern} → {pattern.device_name}")
            return True
        return False

    def get_statistics(self) -> Dict:
        """学習統計を取得"""
        total_patterns = self.db.query(DevicePattern).count()
        manual_patterns = self.db.query(DevicePattern).filter(DevicePattern.source == 'manual').count()
        auto_patterns = self.db.query(DevicePattern).filter(DevicePattern.source == 'auto').count()
        total_usage = self.db.query(DevicePattern).with_entities(
            self.db.func.sum(DevicePattern.usage_count)
        ).scalar() or 0

        return {
            'total_patterns': total_patterns,
            'manual_patterns': manual_patterns,
            'auto_patterns': auto_patterns,
            'total_usage': total_usage
        }

    def _extract_pattern(self, product_name: str, device_name: str) -> Optional[str]:
        """
        商品名から機種パターンを抽出

        Args:
            product_name: 商品名（例: "スマQ いphone14Pro 対応 ケース"）
            device_name: 機種名（例: "iPhone 14 Pro"）

        Returns:
            抽出されたパターン（例: "いphone14Pro"）

        優先順位:
        1. 機種名そのものが含まれている場合 → 機種名
        2. 機種名の変形（スペースなし、ひらがななど）
        3. 商品名全体
        """
        if not product_name or not device_name:
            return None

        # 正規化（スペース削除、小文字化）
        product_lower = product_name.lower().replace(' ', '')
        device_lower = device_name.lower().replace(' ', '')

        # パターン1: 機種名そのものが含まれている
        if device_lower in product_lower:
            # 商品名から機種名部分を抽出
            idx = product_lower.find(device_lower)
            # 元の商品名から対応する部分を取得（大文字小文字を保持）
            product_no_space = product_name.replace(' ', '')
            pattern = product_no_space[idx:idx + len(device_lower)]
            return pattern

        # パターン2: ひらがな表記を探す（例: "いphone14Pro"）
        # device_nameの英数字部分を抽出（例: "14Pro"）
        device_numbers = re.findall(r'[0-9A-Za-z]+', device_name)
        for num_part in device_numbers:
            if len(num_part) >= 2:  # 2文字以上の英数字
                # 商品名内で該当する部分を探す（前後10文字）
                for match in re.finditer(num_part, product_name, re.IGNORECASE):
                    start = max(0, match.start() - 10)
                    end = min(len(product_name), match.end() + 5)
                    pattern_candidate = product_name[start:end].strip()
                    if len(pattern_candidate) >= 3:
                        return pattern_candidate

        # パターン3: 商品名から意味のある部分を抽出（最初の20文字）
        # 括弧やスペースを削除
        clean_name = re.sub(r'[\(\)\[\]\s]', '', product_name)
        if len(clean_name) > 20:
            return clean_name[:20]
        return clean_name if len(clean_name) >= 3 else None
