"""
Design Master Model - デザインマスター（商品タイプマスター）

SKUNEW_v2.5のdesignsテーブルと同期するローカルマスターテーブル
"""

from sqlalchemy import Column, Integer, String, DateTime, func
from app.core.database import Base


class Design(Base):
    """デザインマスターテーブル"""

    __tablename__ = "designs"

    id = Column(Integer, primary_key=True, index=True)
    design_no = Column(String(100), unique=True, nullable=False, index=True, comment="デザイン番号（SKU）")
    design_name = Column(String(255), comment="デザイン名")
    case_type = Column(String(100), index=True, comment="商品タイプ（手帳型、ハードケース等）")
    material = Column(String(100), comment="素材")
    status = Column(String(20), default="有効", comment="ステータス（有効/無効）")

    # メタデータ
    created_at = Column(DateTime(timezone=True), server_default=func.now(), comment="作成日時")
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), comment="更新日時")

    def __repr__(self):
        return f"<Design(design_no={self.design_no}, case_type={self.case_type}, status={self.status})>"
