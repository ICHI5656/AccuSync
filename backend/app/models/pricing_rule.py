"""Pricing Rule model - 単価ルール"""

from sqlalchemy import Column, Integer, Numeric, Date, ForeignKey
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class PricingRule(BaseModel):
    """単価ルール

    会社×商品の単価上書きルールを管理します
    期間・最小数量条件も設定可能
    """

    __tablename__ = "pricing_rules"

    # リレーション
    customer_id = Column(Integer, ForeignKey("customer_companies.id"), nullable=False, index=True, comment="取引先ID")
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, index=True, comment="商品ID")

    # 価格
    price = Column(Numeric(12, 2), nullable=False, comment="適用単価")

    # 条件
    min_qty = Column(Integer, nullable=True, comment="最小数量（この数量以上で適用）")
    start_date = Column(Date, nullable=True, comment="適用開始日")
    end_date = Column(Date, nullable=True, comment="適用終了日")

    # 優先度（複数ルールが該当する場合に使用）
    priority = Column(Integer, nullable=False, default=0, comment="優先度（高い値が優先）")

    # Relationships
    customer = relationship("CustomerCompany", back_populates="pricing_rules")
    product = relationship("Product", back_populates="pricing_rules")

    def __repr__(self):
        return f"<PricingRule(id={self.id}, customer_id={self.customer_id}, product_id={self.product_id}, price={self.price})>"
