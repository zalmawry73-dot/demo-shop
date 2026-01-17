"""Add weight field to products table

Revision ID: 0007
Revises: 0006
Create Date: 2026-01-17
"""

from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = '0007'
down_revision = '0006'
branch_labels = None
depends_on = None


def upgrade():
    # Add weight column to products table
    op.add_column('products', sa.Column('weight', sa.Float(), nullable=True))


def downgrade():
    # Remove weight column
    op.drop_column('products', 'weight')
