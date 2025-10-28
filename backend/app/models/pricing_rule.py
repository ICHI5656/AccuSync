"""Pricing Rule model - 単価ルール"""

from sqlalchemy import Column, Integer, Numeric, Date, ForeignKey, String
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class PricingRule(BaseModel):
    """単価ルール

    会社×商品タイプの単価上書きルールを管理します
    期間・最小数量条件も設定可能

    product_idまたはproduct_type_keywordのどちらか一方を設定します：
    - product_id: 個別商品に対する価格ルール（旧方式）
    - product_type_keyword: 商品タイプ（extracted_memo）に対する価格ルール（新方式）
    """

    __tablename__ = "pricing_rules"

    # リレーション
    customer_id = Column(Integer, ForeignKey("customer_companies.id"), nullable=False, index=True, comment="取引先ID")
    product_id = Column(Integer, ForeignKey("products.id"), nullable=True, index=True, comment="商品ID（個別商品指定の場合）")

    # 商品タイプキーワード（extracted_memoの値）
    product_type_keyword = Column(String(200), nullable=True, index=True, comment="商品タイプキーワード（extracted_memoの値、例: ハードケース、手帳型カバー/mirror）")

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
