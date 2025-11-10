"""add device_attributes table for offline device master

Revision ID: add_device_attrs
Revises:
Create Date: 2025-10-31 18:30:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'add_device_attrs'
down_revision = '1a78f5997177'  # Latest migration: Add product classification fields to OrderItem
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create device_attributes table for offline device master data
    op.create_table(
        'device_attributes',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('brand', sa.String(length=50), nullable=False, comment='ブランド名（iPhone, Galaxy, AQUOS等）'),
        sa.Column('device_name', sa.String(length=100), nullable=False, comment='機種名（iPhone 15 Pro, Galaxy A54等）'),
        sa.Column('size_category', sa.String(length=20), nullable=True, comment='サイズカテゴリ（L, i6, 特大等）'),
        sa.Column('attribute_value', sa.String(length=100), nullable=True, comment='その他属性値'),
        sa.Column('created_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.Column('updated_at', sa.DateTime(), server_default=sa.text('CURRENT_TIMESTAMP'), nullable=False),
        sa.PrimaryKeyConstraint('id')
    )

    # Create indexes for fast lookup
    op.create_index('idx_device_brand', 'device_attributes', ['brand'])
    op.create_index('idx_device_name', 'device_attributes', ['device_name'])
    op.create_index('idx_device_brand_name', 'device_attributes', ['brand', 'device_name'])


def downgrade() -> None:
    op.drop_index('idx_device_brand_name', table_name='device_attributes')
    op.drop_index('idx_device_name', table_name='device_attributes')
    op.drop_index('idx_device_brand', table_name='device_attributes')
    op.drop_table('device_attributes')
