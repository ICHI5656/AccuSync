"""Product Type Pattern Model - Machine Learning based product type classification"""

from sqlalchemy import Column, Integer, String, Float, DateTime
from sqlalchemy.sql import func
from app.core.database import Base


class ProductTypePattern(Base):
    """
    商品タイプのパターン学習テーブル

    ユーザーが手動で変更した商品タイプや、システムが学習した商品タイプのパターンを保存します。
    次回のインポート時に、同じパターンの商品名があれば自動的に商品タイプを適用します。

    例:
    - pattern: "ハードケース"
    - product_type: "ハードケース"
    - source: "manual"（ユーザーが手動で設定）

    - pattern: "手帳型カバー"
    - product_type: "手帳型カバー"
    - source: "auto"（システムが自動学習）
    """
    __tablename__ = "product_type_patterns"

    id = Column(Integer, primary_key=True, index=True)
    pattern = Column(String(255), nullable=False, index=True)
    product_type = Column(String(100), nullable=False, index=True)
    confidence = Column(Float, nullable=False, default=1.0, index=True)
    source = Column(String(50), nullable=False, default='manual')  # 'manual' or 'auto'
    usage_count = Column(Integer, nullable=False, default=0)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

    def __repr__(self):
        return f"<ProductTypePattern(pattern='{self.pattern}', product_type='{self.product_type}', source='{self.source}')>"
