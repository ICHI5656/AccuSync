"""Import Job model - インポートジョブ"""

from sqlalchemy import Column, String, Integer, DateTime, Text, JSON
from app.models.base import BaseModel


class ImportJob(BaseModel):
    """インポートジョブ

    CSV取込やバッチ処理のジョブ履歴を管理します
    """

    __tablename__ = "import_jobs"

    # ジョブ情報
    job_type = Column(String(50), nullable=True, default="file_import", comment="ジョブタイプ: file_import, invoice_generation")
    status = Column(String(20), nullable=False, default="pending", comment="ステータス: pending, processing, completed, failed")

    # アップロード情報
    upload_id = Column(String(100), nullable=True, comment="アップロードID")
    filename = Column(String(500), nullable=True, comment="ファイル名")
    file_type = Column(String(50), nullable=True, comment="ファイルタイプ: csv, excel, pdf, txt")

    # マッピング情報
    mapping_json = Column(JSON, nullable=True, comment="マッピング情報（JSON）")

    # 処理結果
    total_rows = Column(Integer, nullable=True, default=0, comment="総行数")
    processed_rows = Column(Integer, nullable=True, default=0, comment="処理済み行数")
    error_count = Column(Integer, nullable=True, default=0, comment="エラー行数")

    # 警告とエラー
    warnings = Column(JSON, nullable=True, default=list, comment="警告リスト")
    errors = Column(JSON, nullable=True, default=list, comment="エラーリスト")

    # 結果データ
    result_data = Column(JSON, nullable=True, comment="処理結果データ（JSON）")

    # エラー情報（後方互換性のため保持）
    error_report_url = Column(String(500), nullable=True, comment="エラーレポートURL")
    error_message = Column(Text, nullable=True, comment="エラーメッセージ")

    # 実行時間
    started_at = Column(DateTime, nullable=True, comment="開始日時")
    finished_at = Column(DateTime, nullable=True, comment="終了日時")
    completed_at = Column(DateTime, nullable=True, comment="完了日時")

    def __repr__(self):
        return f"<ImportJob(id={self.id}, filename='{self.filename}', status='{self.status}')>"
