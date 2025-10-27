"""Mapping Template model - 列マッピングテンプレート"""

from sqlalchemy import Column, String, JSON, Boolean
from app.models.base import BaseModel


class MappingTemplate(BaseModel):
    """列マッピングテンプレート

    ファイルインポート時の列マッピング設定を保存し、再利用できるようにします
    """

    __tablename__ = "mapping_templates"

    # テンプレート情報
    template_name = Column(String(100), nullable=False, unique=True, comment="テンプレート名")
    description = Column(String(500), nullable=True, comment="説明")

    # ファイルパターン（オプション）
    file_pattern = Column(String(200), nullable=True, comment="ファイル名パターン（例: order_*.csv）")
    file_type = Column(String(50), nullable=True, comment="ファイルタイプ: csv, excel, pdf, txt")

    # 列マッピング情報
    column_mapping = Column(JSON, nullable=False, comment="列マッピング設定（JSON）")

    # 設定
    is_default = Column(Boolean, nullable=False, default=False, comment="デフォルトテンプレートフラグ")
    is_active = Column(Boolean, nullable=False, default=True, comment="有効フラグ")

    def __repr__(self):
        return f"<MappingTemplate(id={self.id}, name='{self.template_name}')>"
