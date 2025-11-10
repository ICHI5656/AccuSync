"""add_designs_table_for_product_type_master

Revision ID: 467cf28a806e
Revises: 514c297c5ee1
Create Date: 2025-11-10 06:59:13.747033

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '467cf28a806e'
down_revision = '514c297c5ee1'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create designs table for local design master
    op.create_table(
        'designs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('design_no', sa.String(length=100), nullable=False, comment='デザイン番号（SKU）'),
        sa.Column('design_name', sa.String(length=255), nullable=True, comment='デザイン名'),
        sa.Column('case_type', sa.String(length=100), nullable=True, comment='商品タイプ（手帳型、ハードケース等）'),
        sa.Column('material', sa.String(length=100), nullable=True, comment='素材'),
        sa.Column('status', sa.String(length=20), server_default='有効', nullable=True, comment='ステータス（有効/無効）'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True, comment='作成日時'),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True, comment='更新日時'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index('idx_designs_design_no', 'designs', ['design_no'], unique=True)
    op.create_index('idx_designs_case_type', 'designs', ['case_type'], unique=False)
    op.create_index('idx_designs_status', 'designs', ['status'], unique=False)


def downgrade() -> None:
    op.drop_index('idx_designs_status', table_name='designs')
    op.drop_index('idx_designs_case_type', table_name='designs')
    op.drop_index('idx_designs_design_no', table_name='designs')
    op.drop_table('designs')
