"""Add takeaways and giveaways columns to player_stats

Revision ID: 007
Revises: 006
Create Date: 2025-01-18
"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '007'
down_revision = '006'
branch_labels = None
depends_on = None


def upgrade():
    # Add takeaways column
    op.add_column('player_stats', sa.Column('takeaways', sa.Integer(), nullable=True, server_default='0'))
    
    # Add giveaways column
    op.add_column('player_stats', sa.Column('giveaways', sa.Integer(), nullable=True, server_default='0'))


def downgrade():
    op.drop_column('player_stats', 'giveaways')
    op.drop_column('player_stats', 'takeaways')
