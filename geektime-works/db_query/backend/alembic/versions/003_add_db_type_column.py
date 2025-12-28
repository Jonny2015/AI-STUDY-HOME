"""Add db_type column to databaseconnections.

Revision ID: 003
Revises: 002
Create Date: 2025-12-28

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '003'
down_revision: Union[str, None] = '002'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add db_type column to databaseconnections table."""
    # Add db_type column with default value
    op.add_column(
        'databaseconnections',
        sa.Column('db_type', sa.String(length=20), nullable=False, server_default='postgresql')
    )


def downgrade() -> None:
    """Remove db_type column from databaseconnections table."""
    op.drop_column('databaseconnections', 'db_type')
