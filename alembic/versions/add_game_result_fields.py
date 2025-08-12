"""Add game result fields

Revision ID: add_game_result_fields
Revises:
Create Date: 2024-12-19 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = 'add_game_result_fields'
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    # Add new columns to games table
    op.add_column('games', sa.Column('is_finished', sa.String(), nullable=True))
    op.add_column('games', sa.Column('result', sa.String(), nullable=True))
    op.add_column('games', sa.Column('termination', sa.String(), nullable=True))
    op.add_column('games', sa.Column('finished_at', sa.DateTime(), nullable=True))

    # Set default value for existing games
    op.execute("UPDATE games SET is_finished = 'false' WHERE is_finished IS NULL")


def downgrade():
    # Remove the new columns
    op.drop_column('games', 'finished_at')
    op.drop_column('games', 'termination')
    op.drop_column('games', 'result')
    op.drop_column('games', 'is_finished')
