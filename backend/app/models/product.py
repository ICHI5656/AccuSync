"""Product model - 商品"""

from sqlalchemy import Column, String, Numeric, Boolean, Integer
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class Product(BaseModel):
    """商品マスタ

    SKU/名称/標準単価/税区分を管理します
    """

    __tablename__ = "products"

    # 基本情報
    sku = Column(String(100), nullable=False, unique=True, index=True, comment="商品コード（SKU）")
    name = Column(String(500), nullable=False, comment="商品名")

    # 価格
    default_price = Column(Numeric(12, 2), nullable=False, comment="標準単価")

    # 税
    tax_rate = Column(Numeric(5, 4), nullable=False, default=0.10, comment="税率（例: 0.10 = 10%）")
    tax_category = Column(String(20), nullable=True, default="standard", comment="税区分: standard, reduced, exempt")

    # その他
    unit = Column(String(20), nullable=True, default="個", comment="単位")
    is_active = Column(Boolean, nullable=False, default=True, comment="有効フラグ")

    # 商品詳細情報
    device_model = Column(String(100), nullable=True, comment="対応機種: iPhone 14 Pro, Galaxy S23 など")
    notebook_structure = Column(String(100), nullable=True, comment="手帳構造: 両面印刷薄型, ベルト無し手帳型 など")

    # Relationships
    order_items = relationship("OrderItem", back_populates="product")
    invoice_items = relationship("InvoiceItem", back_populates="product")
    pricing_rules = relationship("PricingRule", back_populates="product")

    def __repr__(self):
        return f"<Product(id={self.id}, sku='{self.sku}', name='{self.name}')>"
