"""Issuer Company model - 請求書発行会社"""

from sqlalchemy import Column, String, Text
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class IssuerCompany(BaseModel):
    """請求書発行会社

    自社の情報を管理します。複数登録可能（支社/ブランド単位）
    """

    __tablename__ = "issuer_companies"

    # 基本情報
    name = Column(String(255), nullable=False, comment="会社名")
    brand_name = Column(String(255), nullable=True, comment="ブランド名")
    tax_id = Column(String(50), nullable=True, comment="適格請求書登録番号")

    # 連絡先
    address = Column(Text, nullable=True, comment="所在地")
    tel = Column(String(20), nullable=True, comment="電話番号")
    email = Column(String(255), nullable=True, comment="メールアドレス")

    # 振込先
    bank_info = Column(Text, nullable=True, comment="振込先情報（JSON形式）")

    # ファイル
    logo_url = Column(String(500), nullable=True, comment="ロゴファイルURL")
    seal_url = Column(String(500), nullable=True, comment="印影ファイルURL")

    # 請求書テンプレート設定
    invoice_notes = Column(Text, nullable=True, comment="請求書デフォルト備考")

    # Relationships
    orders = relationship("Order", back_populates="issuer_company")
    invoices = relationship("Invoice", back_populates="issuer_company")

    def __repr__(self):
        return f"<IssuerCompany(id={self.id}, name='{self.name}')>"
