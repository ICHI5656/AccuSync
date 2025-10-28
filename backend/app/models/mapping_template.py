"""Mapping Template model - 列マッピングテンプレート"""

from sqlalchemy import Column, String, JSON, Boolean, Integer, ForeignKey
from sqlalchemy.orm import relationship
from app.models.base import BaseModel


class MappingTemplate(BaseModel):
    """列マッピングテンプレート

    ファイルインポート時の列マッピング設定を保存し、再利用できるようにします
    顧客ごとに異なるマッピングを保存可能
    """

    __tablename__ = "mapping_templates"

    # テンプレート情報
    template_name = Column(String(100), nullable=False, comment="テンプレート名")
    description = Column(String(500), nullable=True, comment="説明")

    # 顧客関連付け
    customer_id = Column(Integer, ForeignKey("customer_companies.id", ondelete="CASCADE"), nullable=True, index=True, comment="顧客ID（NULLの場合は汎用テンプレート）")

    # ファイルパターン（オプション）
    file_pattern = Column(String(200), nullable=True, comment="ファイル名パターン（例: order_*.csv）")
    file_type = Column(String(50), nullable=True, comment="ファイルタイプ: csv, excel, pdf, txt")

    # 列マッピング情報
    column_mapping = Column(JSON, nullable=False, comment="列マッピング設定（JSON）")

    # 設定
    is_default = Column(Boolean, nullable=False, default=False, comment="デフォルトテンプレートフラグ")
    is_active = Column(Boolean, nullable=False, default=True, comment="有効フラグ")

    # Relationships
    customer = relationship("CustomerCompany", back_populates="mapping_templates")

    def __repr__(self):
        return f"<MappingTemplate(id={self.id}, name='{self.template_name}', customer_id={self.customer_id})>"
