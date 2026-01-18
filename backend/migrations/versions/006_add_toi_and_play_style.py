"""Add time_on_ice to player_stats and play_style to teams

Revision ID: 006
Revises: 005
Create Date: 2026-01-17
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers
revision = '006'
down_revision = '005'
branch_labels = None
depends_on = None


def upgrade():
    # Add time_on_ice to player_stats (in seconds)
    op.add_column('player_stats', sa.Column('time_on_ice', sa.Integer(), nullable=True, server_default='0'))
    
    # Add play_style to teams (auto, trap, possession, dump_chase, rush, shoot_crash)
    op.add_column('teams', sa.Column('play_style', sa.String(length=20), nullable=True, server_default='auto'))


def downgrade():
    op.drop_column('player_stats', 'time_on_ice')
    op.drop_column('teams', 'play_style')
