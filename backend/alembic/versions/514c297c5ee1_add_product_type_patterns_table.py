"""add_product_type_patterns_table

Revision ID: 514c297c5ee1
Revises: 58e8d549f72d
Create Date: 2025-11-07 08:14:56.898147

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '514c297c5ee1'
down_revision = '58e8d549f72d'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create product_type_patterns table for ML-based product type learning
    op.create_table(
        'product_type_patterns',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('pattern', sa.String(length=255), nullable=False),
        sa.Column('product_type', sa.String(length=100), nullable=False),
        sa.Column('confidence', sa.Float(), nullable=False, server_default='1.0'),
        sa.Column('source', sa.String(length=50), nullable=False, server_default='manual'),
        sa.Column('usage_count', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('created_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.Column('updated_at', sa.DateTime(), nullable=False, server_default=sa.text('CURRENT_TIMESTAMP')),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes for faster lookups
    op.create_index('idx_product_type_patterns_pattern', 'product_type_patterns', ['pattern'])
    op.create_index('idx_product_type_patterns_product_type', 'product_type_patterns', ['product_type'])
    op.create_index('idx_product_type_patterns_confidence', 'product_type_patterns', ['confidence'])


def downgrade() -> None:
    # Drop indexes first
    op.drop_index('idx_product_type_patterns_confidence', table_name='product_type_patterns')
    op.drop_index('idx_product_type_patterns_product_type', table_name='product_type_patterns')
    op.drop_index('idx_product_type_patterns_pattern', table_name='product_type_patterns')

    # Drop table
    op.drop_table('product_type_patterns')
