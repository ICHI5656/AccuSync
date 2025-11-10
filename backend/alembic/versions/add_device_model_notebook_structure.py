"""add device_model and notebook_structure to products

Revision ID: device_model_20251029
Revises: e5539ca4aa58
Create Date: 2025-10-29 23:35:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'device_model_20251029'
down_revision = 'e5539ca4aa58'
branch_labels = None
depends_on = None


def upgrade():
    # Add device_model column to products table
    op.add_column('products', sa.Column('device_model', sa.String(length=100), nullable=True, comment='対応機種: iPhone 14 Pro, Galaxy S23 など'))

    # Add notebook_structure column to products table
    op.add_column('products', sa.Column('notebook_structure', sa.String(length=100), nullable=True, comment='手帳構造: 両面印刷薄型, ベルト無し手帳型 など'))


def downgrade():
    # Remove columns
    op.drop_column('products', 'notebook_structure')
    op.drop_column('products', 'device_model')
