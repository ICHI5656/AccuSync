"""Invoice models - 請求書"""

from sqlalchemy import Column, String, Integer, Date, Text, ForeignKey, Numeric
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class Invoice(BaseModel):
    """請求書ヘッダ

    集計結果から生成された請求書
    """

    __tablename__ = "invoices"

    # 請求書情報
    invoice_no = Column(String(100), nullable=False, unique=True, index=True, comment="請求書番号")

    # リレーション
    issuer_company_id = Column(Integer, ForeignKey("issuer_companies.id"), nullable=False, comment="発行会社ID")
    customer_id = Column(Integer, ForeignKey("customer_companies.id"), nullable=False, index=True, comment="取引先ID")

    # 期間
    period_start = Column(Date, nullable=False, comment="集計期間開始日")
    period_end = Column(Date, nullable=False, comment="集計期間終了日")
    issue_date = Column(Date, nullable=False, comment="発行日")
    due_date = Column(Date, nullable=False, comment="支払期限")

    # 金額
    subtotal_ex_tax = Column(Numeric(15, 2), nullable=False, comment="税抜合計")
    tax_amount = Column(Numeric(15, 2), nullable=False, comment="消費税額")
    total_in_tax = Column(Numeric(15, 2), nullable=False, comment="税込合計")

    # ステータス
    status = Column(String(20), nullable=False, default="draft", comment="ステータス: draft, issued, paid, void")

    # その他
    notes = Column(Text, nullable=True, comment="備考")
    pdf_url = Column(String(500), nullable=True, comment="PDF URL")

    # Relationships
    issuer_company = relationship("IssuerCompany", back_populates="invoices")
    customer = relationship("CustomerCompany", back_populates="invoices")
    items = relationship("InvoiceItem", back_populates="invoice", cascade="all, delete-orphan")

    def __repr__(self):
        return f"<Invoice(id={self.id}, invoice_no='{self.invoice_no}', status='{self.status}')>"


class InvoiceItem(BaseModel):
    """請求書明細

    請求書の品目明細
    """

    __tablename__ = "invoice_items"

    # リレーション
    invoice_id = Column(Integer, ForeignKey("invoices.id"), nullable=False, index=True, comment="請求書ID")
    product_id = Column(Integer, ForeignKey("products.id"), nullable=True, comment="商品ID（任意）")

    # 明細情報
    description = Column(String(500), nullable=False, comment="品目説明")
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
    invoice = relationship("Invoice", back_populates="items")
    product = relationship("Product", back_populates="invoice_items")

    def __repr__(self):
        return f"<InvoiceItem(id={self.id}, invoice_id={self.invoice_id}, description='{self.description}')>"
