"""add trophies table

Revision ID: 005
Revises: 004
Create Date: 2026-01-15 15:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '005'
down_revision = '004'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    table_names = inspector.get_table_names()
    if 'trophies' not in table_names:
        op.create_table(
            'trophies',
            sa.Column('id', sa.Integer(), primary_key=True),
            sa.Column('simulation_id', sa.Integer(), sa.ForeignKey('simulations.id', ondelete='CASCADE'), nullable=False),
            sa.Column('season', sa.Integer(), nullable=False),
            sa.Column('trophy_name', sa.String(length=100), nullable=False),
            sa.Column('trophy_type', sa.String(length=20), nullable=False),
            sa.Column('player_id', sa.Integer(), sa.ForeignKey('players.id'), nullable=True),
            sa.Column('team_id', sa.Integer(), sa.ForeignKey('teams.id'), nullable=True),
            sa.Column('created_at', sa.DateTime(), nullable=True, server_default=sa.func.now()),
        )
        
        # Create indexes for commonly queried columns
        op.create_index('idx_trophies_simulation_id', 'trophies', ['simulation_id'])
        op.create_index('idx_trophies_season', 'trophies', ['season'])
        op.create_index('idx_trophies_trophy_type', 'trophies', ['trophy_type'])
        op.create_index('idx_trophies_player_id', 'trophies', ['player_id'])
        op.create_index('idx_trophies_team_id', 'trophies', ['team_id'])


def downgrade():
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    table_names = inspector.get_table_names()
    if 'trophies' in table_names:
        op.drop_table('trophies')
