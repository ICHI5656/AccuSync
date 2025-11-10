"""add_unique_constraint_to_device_attributes

Revision ID: 58e8d549f72d
Revises: add_device_attrs
Create Date: 2025-11-07 07:24:45.771092

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '58e8d549f72d'
down_revision = 'add_device_attrs'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add unique constraint on (brand, device_name) combination
    op.create_unique_constraint(
        'uq_device_attributes_brand_device_name',
        'device_attributes',
        ['brand', 'device_name']
    )


def downgrade() -> None:
    # Drop unique constraint
    op.drop_constraint(
        'uq_device_attributes_brand_device_name',
        'device_attributes',
        type_='unique'
    )
