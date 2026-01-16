"""add ot_losses to standings

Revision ID: 002
Revises: affc9bf53f72
Create Date: 2026-01-15 02:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '002'
down_revision = 'affc9bf53f72'
branch_labels = None
depends_on = None


def upgrade():
    # Check if column already exists before adding
    conn = op.get_bind()
    inspector = sa.inspect(conn)
    columns = [col['name'] for col in inspector.get_columns('standings')]
    
    if 'ot_losses' not in columns:
        op.add_column('standings', sa.Column('ot_losses', sa.Integer(), nullable=True, server_default='0'))
        # Update any NULL values to 0
        op.execute("UPDATE standings SET ot_losses = 0 WHERE ot_losses IS NULL")
        # Make column NOT NULL with default
        op.alter_column('standings', 'ot_losses', nullable=False, server_default='0')


def downgrade():
    op.drop_column('standings', 'ot_losses')
