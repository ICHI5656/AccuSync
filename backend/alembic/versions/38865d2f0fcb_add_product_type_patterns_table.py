"""add_product_type_patterns_table

Revision ID: 38865d2f0fcb
Revises: 467cf28a806e
Create Date: 2025-11-10 07:44:06.289078

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '38865d2f0fcb'
down_revision = '467cf28a806e'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 商品タイプパターン学習テーブル
    op.create_table(
        'product_type_patterns',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('pattern', sa.String(length=255), nullable=False, comment='商品番号のパターン'),
        sa.Column('product_type', sa.String(length=100), nullable=False, comment='商品タイプ'),
        sa.Column('confidence', sa.Float(), nullable=False, server_default='1.0', comment='信頼度（0.0-1.0）'),
        sa.Column('source', sa.String(length=50), nullable=False, server_default='manual', comment='manual or auto'),
        sa.Column('usage_count', sa.Integer(), nullable=False, server_default='0', comment='使用回数'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )

    # インデックス作成（高速検索用）
    op.create_index('idx_product_type_patterns_pattern', 'product_type_patterns', ['pattern'])
    op.create_index('idx_product_type_patterns_product_type', 'product_type_patterns', ['product_type'])
    op.create_index('idx_product_type_patterns_confidence', 'product_type_patterns', ['confidence'])


def downgrade() -> None:
    op.drop_index('idx_product_type_patterns_confidence', table_name='product_type_patterns')
    op.drop_index('idx_product_type_patterns_product_type', table_name='product_type_patterns')
    op.drop_index('idx_product_type_patterns_pattern', table_name='product_type_patterns')
    op.drop_table('product_type_patterns')
