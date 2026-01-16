"""add playoff series table and game series_id

Revision ID: 004
Revises: 003
Create Date: 2026-01-15 12:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '004'
down_revision = '003'
branch_labels = None
depends_on = None


def upgrade():
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    table_names = inspector.get_table_names()
    if 'playoff_series' not in table_names:
        op.create_table(
            'playoff_series',
            sa.Column('id', sa.Integer(), primary_key=True),
            sa.Column('simulation_id', sa.Integer(), sa.ForeignKey('simulations.id'), nullable=False),
            sa.Column('season', sa.Integer(), nullable=False),
            sa.Column('round', sa.Integer(), nullable=False),
            sa.Column('higher_seed_team_id', sa.Integer(), sa.ForeignKey('teams.id'), nullable=False),
            sa.Column('lower_seed_team_id', sa.Integer(), sa.ForeignKey('teams.id'), nullable=False),
            sa.Column('higher_seed_wins', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('lower_seed_wins', sa.Integer(), nullable=False, server_default='0'),
            sa.Column('status', sa.String(length=20), nullable=False, server_default='in_progress'),
            sa.Column('winner_team_id', sa.Integer(), sa.ForeignKey('teams.id'), nullable=True),
            sa.Column('next_game_number', sa.Integer(), nullable=False, server_default='1'),
            sa.Column('created_at', sa.DateTime(), nullable=True),
        )

    columns = [col['name'] for col in inspector.get_columns('games')]
    if 'series_id' not in columns:
        op.add_column('games', sa.Column('series_id', sa.Integer(), sa.ForeignKey('playoff_series.id'), nullable=True))


def downgrade():
    conn = op.get_bind()
    inspector = sa.inspect(conn)

    columns = [col['name'] for col in inspector.get_columns('games')]
    if 'series_id' in columns:
        op.drop_column('games', 'series_id')

    table_names = inspector.get_table_names()
    if 'playoff_series' in table_names:
        op.drop_table('playoff_series')
