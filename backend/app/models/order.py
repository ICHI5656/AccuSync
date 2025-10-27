"""Order models - 受注"""

from sqlalchemy import Column, String, Integer, Date, Text, ForeignKey, Numeric
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class Order(BaseModel):
    """受注ヘッダ

    CSVまたは手動で登録された受注情報のヘッダ
    """

    __tablename__ = "orders"

    # 受注情報
    source = Column(String(50), nullable=False, comment="取込元: csv, manual, api")
    order_no = Column(String(100), nullable=False, index=True, comment="注文番号")
    order_date = Column(Date, nullable=False, index=True, comment="注文日")

    # リレーション
    customer_id = Column(Integer, ForeignKey("customer_companies.id"), nullable=False, index=True, comment="取引先ID")
    issuer_company_id = Column(Integer, ForeignKey("issuer_companies.id"), nullable=True, comment="発行会社ID")

    # その他
    currency = Column(String(3), nullable=False, default="JPY", comment="通貨コード")
    memo = Column(Text, nullable=True, comment="備考")

    # Relationships
    customer = relationship("CustomerCompany", back_populates="orders")
    issuer_company = relationship("IssuerCompany", back_populates="orders")
    items = relationship("OrderItem", back_populates="order", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Order(id={self.id}, order_no='{self.order_no}', customer_id={self.customer_id})>"


class OrderItem(BaseModel):
    """受注明細

    受注の品目明細
    """

    __tablename__ = "order_items"

    # リレーション
    order_id = Column(Integer, ForeignKey("orders.id"), nullable=False, index=True, comment="受注ID")
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False, comment="商品ID")

    # 数量と単価
    qty = Column(Integer, nullable=False, comment="数量")
    unit_price = Column(Numeric(12, 2), nullable=False, comment="単価")

    # 税と割引
    tax_rate = Column(Numeric(5, 4), nullable=False, default=0.10, comment="税率")
    discount = Column(Numeric(12, 2), nullable=True, default=0, comment="割引額")

    # 金額計算
    subtotal_ex_tax = Column(Numeric(15, 2), nullable=False, comment="税抜小計")
    tax_amount = Column(Numeric(15, 2), nullable=False, comment="消費税額")
    total_in_tax = Column(Numeric(15, 2), nullable=False, comment="税込合計")

    # Relationships
    order = relationship("Order", back_populates="items")
    product = relationship("Product", back_populates="order_items")

    def __repr__(self):
        return f"<OrderItem(id={self.id}, order_id={self.order_id}, product_id={self.product_id}, qty={self.qty})>"
