"""Audit Log model - 監査ログ"""

from sqlalchemy import Column, String, Integer, Text, ForeignKey, JSON
from app.models.base import BaseModel
from sqlalchemy.orm import relationship


class AuditLog(BaseModel):
    """監査ログ

    誰が・いつ・何をしたかを記録します
    """

    __tablename__ = "audit_logs"

    # アクター
    actor_user_id = Column(Integer, ForeignKey("users.id"), nullable=True, index=True, comment="実行ユーザーID")

    # アクション
    action = Column(String(50), nullable=False, index=True, comment="アクション: create, update, delete, issue")

    # 対象
    target_table = Column(String(100), nullable=False, comment="対象テーブル名")
    target_id = Column(Integer, nullable=True, comment="対象レコードID")

    # 変更内容（JSON形式でBefore/After）
    diff_json = Column(JSON, nullable=True, comment="変更差分（JSON）")

    # Relationships
    actor = relationship("User", back_populates="audit_logs")

    def __repr__(self):
        return f"<AuditLog(id={self.id}, action='{self.action}', target_table='{self.target_table}')>"
