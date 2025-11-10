"""
サイズ学習パターンモデル

ユーザーが手動で変更したサイズ情報を学習し、次回のインポート時に自動適用します。
手帳型カバーのみが対象です。
"""

from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.sql import func
from app.core.database import Base


class SizePattern(Base):
    """サイズ学習パターン"""
    __tablename__ = "size_patterns"

    id = Column(Integer, primary_key=True, index=True)

    # 商品名のパターン（部分一致用）
    pattern = Column(String(255), nullable=False, index=True)

    # 検出されたサイズ（例: "L", "M", "i6", "特大"）
    size = Column(String(20), nullable=False, index=True)

    # 機種名（例: "iPhone 15 Pro"）- サイズと機種の組み合わせで学習
    device_name = Column(String(100), nullable=True, index=True)

    # ブランド名（例: "iPhone", "AQUOS"）
    brand = Column(String(50), nullable=True, index=True)

    # 信頼度（0.0-1.0）
    # 手動学習: 0.9、自動学習: 0.7
    confidence = Column(Float, nullable=False, default=1.0, index=True)

    # 学習元（'manual' or 'auto'）
    source = Column(String(50), nullable=False, default='manual')

    # 使用回数（パターンが適用された回数）
    usage_count = Column(Integer, nullable=False, default=0)

    # 作成日時
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # 更新日時
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<SizePattern(pattern='{self.pattern}', size='{self.size}', device='{self.device_name}', confidence={self.confidence})>"
