"""Customer Company model - 取引先会社"""

from sqlalchemy import Column, String, Text, Integer, Boolean
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class CustomerCompany(BaseModel):
    """取引先会社・個人

    請求先となる顧客（会社または個人）の情報を管理します
    """

    __tablename__ = "customer_companies"

    # 基本情報
    name = Column(String(255), nullable=False, index=True, comment="会社名/氏名")
    code = Column(String(50), nullable=False, unique=True, index=True, comment="会社コード")
    is_individual = Column(Boolean, nullable=False, default=False, index=True, comment="個人フラグ")

    # 連絡先情報
    postal_code = Column(String(20), nullable=True, comment="郵便番号")
    address = Column(Text, nullable=True, comment="住所")
    billing_address = Column(Text, nullable=True, comment="請求先住所（会社の場合、住所と異なる場合に使用）")
    phone = Column(String(50), nullable=True, comment="電話番号")
    email = Column(String(255), nullable=True, comment="メールアドレス")

    # 担当者情報（会社の場合）
    contact_name = Column(String(255), nullable=True, comment="担当者名")
    contact_email = Column(String(255), nullable=True, comment="担当者メールアドレス")

    # 支払条件
    payment_terms = Column(String(200), nullable=True, comment="支払条件（説明文）")
    closing_day = Column(Integer, nullable=True, comment="締め日（1-31、0=月末）")
    payment_day = Column(Integer, nullable=True, comment="支払い日（1-31、0=月末）")
    payment_month_offset = Column(Integer, nullable=True, default=1, comment="支払い月のオフセット（0=当月、1=翌月、2=翌々月）")
    tax_mode = Column(String(20), nullable=True, default="inclusive", comment="税区分: inclusive, exclusive")

    # その他
    notes = Column(Text, nullable=True, comment="備考")

    # Relationships
    orders = relationship("Order", back_populates="customer")
    invoices = relationship("Invoice", back_populates="customer")
    pricing_rules = relationship("PricingRule", back_populates="customer")
    mapping_templates = relationship("MappingTemplate", back_populates="customer")
    identifiers = relationship("CustomerIdentifier", back_populates="customer", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<CustomerCompany(id={self.id}, code='{self.code}', name='{self.name}')>"
