"""add is_active to simulations

Revision ID: 001
Revises: 
Create Date: 2026-01-15 01:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Check if column already exists before adding
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [col['name'] for col in inspector.get_columns('simulations')]
    
    if 'is_active' not in columns:
        op.add_column('simulations', sa.Column('is_active', sa.Boolean(), nullable=True, server_default='true'))
        # Update any NULL values to True
        op.execute("UPDATE simulations SET is_active = TRUE WHERE is_active IS NULL")
        # Make column NOT NULL
        op.alter_column('simulations', 'is_active', nullable=False, server_default='true')


def downgrade():
    op.drop_column('simulations', 'is_active')
