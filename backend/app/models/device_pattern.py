"""
機種学習パターンモデル

ユーザーが手動で変更した機種情報を学習し、次回のインポート時に自動適用します。
"""

from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.sql import func
from app.core.database import Base


class DevicePattern(Base):
    """機種学習パターン"""
    __tablename__ = "device_patterns"

    id = Column(Integer, primary_key=True, index=True)

    # 商品名のパターン（部分一致用）
    pattern = Column(String(255), nullable=False, index=True)

    # 検出された機種名（例: "iPhone 15 Pro", "AQUOS wish4"）
    device_name = Column(String(100), nullable=False, index=True)

    # ブランド名（例: "iPhone", "AQUOS", "Galaxy"）
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
        return f"<DevicePattern(pattern='{self.pattern}', device='{self.device_name}', brand='{self.brand}', confidence={self.confidence})>"
