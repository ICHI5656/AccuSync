"""Customer Identifier model - 顧客識別情報"""

from sqlalchemy import Column, String, Integer, ForeignKey, UniqueConstraint
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class CustomerIdentifier(BaseModel):
    """顧客識別情報

    複数の識別情報を紐付けて顧客を自動判別するためのテーブル
    CSVの名前、住所、電話番号、メールアドレスなど、
    様々な識別情報を記録して次回以降の自動判別に使用します
    """

    __tablename__ = "customer_identifiers"

    # リレーション
    customer_id = Column(
        Integer,
        ForeignKey("customer_companies.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        comment="取引先ID"
    )

    # 識別情報のタイプ
    identifier_type = Column(
        String(50),
        nullable=False,
        index=True,
        comment="識別情報タイプ（csv_name, phone, address, email, etc.）"
    )

    # 識別情報の値
    identifier_value = Column(
        String(500),
        nullable=False,
        index=True,
        comment="識別情報の値"
    )

    # Relationships
    customer = relationship("CustomerCompany", back_populates="identifiers")

    # ユニーク制約（同じ識別情報を複数の顧客に紐付けない）
    __table_args__ = (
        UniqueConstraint('identifier_type', 'identifier_value', name='uq_identifier_type_value'),
    )

    def __repr__(self):
        return f"<CustomerIdentifier(customer_id={self.customer_id}, type={self.identifier_type}, value={self.identifier_value[:20]})>"
