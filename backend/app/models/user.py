"""User model - ユーザー"""

from sqlalchemy import Column, String, Boolean, DateTime
from sqlalchemy.orm import relationship

from app.models.base import BaseModel


class User(BaseModel):
    """ユーザー

    システムにアクセスするユーザーを管理します
    """

    __tablename__ = "users"

    # 認証情報
    email = Column(String(255), nullable=False, unique=True, index=True, comment="メールアドレス")
    hashed_password = Column(String(255), nullable=False, comment="ハッシュ化パスワード")

    # ユーザー情報
    name = Column(String(255), nullable=False, comment="氏名")
    role = Column(String(50), nullable=False, default="viewer", comment="ロール: admin, accountant, viewer")

    # ステータス
    is_active = Column(Boolean, nullable=False, default=True, comment="有効フラグ")
    last_login_at = Column(DateTime, nullable=True, comment="最終ログイン日時")

    # Relationships
    audit_logs = relationship("AuditLog", back_populates="actor")

    def __repr__(self):
        return f"<User(id={self.id}, email='{self.email}', role='{self.role}')>"
