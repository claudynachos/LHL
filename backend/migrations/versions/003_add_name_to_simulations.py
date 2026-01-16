"""add name to simulations

Revision ID: 003
Revises: 002
Create Date: 2026-01-15 03:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade():
    # Check if column already exists before adding
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [col['name'] for col in inspector.get_columns('simulations')]
    
    if 'name' not in columns:
        op.add_column('simulations', sa.Column('name', sa.String(length=100), nullable=True))


def downgrade():
    op.drop_column('simulations', 'name')
