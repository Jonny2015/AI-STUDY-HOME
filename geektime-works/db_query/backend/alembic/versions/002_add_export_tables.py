"""Add export tasks and AI suggestion analytics tables.

Revision ID: 002
Revises: 001
Create Date: 2025-12-28

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '002'
down_revision: Union[str, None] = '001'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create export-related tables."""
    # Export tasks table
    op.create_table(
        'exporttasks',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('task_id', sa.String(length=36), nullable=False),
        sa.Column('user_id', sa.String(length=255), nullable=False),
        sa.Column('database_name', sa.String(length=255), nullable=False),
        sa.Column('sql_text', sa.Text(), nullable=False),
        sa.Column('export_format', sa.String(length=10), nullable=False),
        sa.Column('export_scope', sa.String(length=20), nullable=False),
        sa.Column('file_name', sa.String(length=255), nullable=True),
        sa.Column('file_path', sa.String(length=500), nullable=True),
        sa.Column('file_size_bytes', sa.Integer(), nullable=True),
        sa.Column('row_count', sa.Integer(), nullable=True),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('progress', sa.Integer(), nullable=False),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('started_at', sa.DateTime(), nullable=True),
        sa.Column('completed_at', sa.DateTime(), nullable=True),
        sa.Column('execution_time_ms', sa.Integer(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['database_name'], ['databaseconnections.name'], ),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('task_id'),
    )
    op.create_index('idx_exporttasks_user_id', 'exporttasks', ['user_id'], unique=False)
    op.create_index('idx_exporttasks_database_name', 'exporttasks', ['database_name'], unique=False)
    op.create_index('idx_exporttasks_status', 'exporttasks', ['status'], unique=False)
    op.create_index('idx_exporttasks_task_id', 'exporttasks', ['task_id'], unique=False)
    op.create_index('idx_exporttasks_created_at', 'exporttasks', ['created_at'], unique=False)
    op.create_index('idx_exporttasks_started_at', 'exporttasks', ['started_at'], unique=False)

    # AI suggestion analytics table
    op.create_table(
        'aisuggestionanalytics',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('suggestion_id', sa.String(length=36), nullable=False),
        sa.Column('database_name', sa.String(length=255), nullable=False),
        sa.Column('suggestion_type', sa.String(length=50), nullable=False),
        sa.Column('sql_context', sa.Text(), nullable=True),
        sa.Column('row_count', sa.Integer(), nullable=True),
        sa.Column('confidence', sa.String(length=10), nullable=True),
        sa.Column('suggested_format', sa.String(length=10), nullable=True),
        sa.Column('suggested_scope', sa.String(length=20), nullable=True),
        sa.Column('user_response', sa.String(length=20), nullable=False),
        sa.Column('response_time_ms', sa.Integer(), nullable=True),
        sa.Column('suggested_at', sa.DateTime(), nullable=False),
        sa.Column('responded_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('suggestion_id'),
    )
    op.create_index('idx_aisuggestionanalytics_database_name', 'aisuggestionanalytics', ['database_name'], unique=False)
    op.create_index('idx_aisuggestionanalytics_user_response', 'aisuggestionanalytics', ['user_response'], unique=False)
    op.create_index('idx_aisuggestionanalytics_suggested_at', 'aisuggestionanalytics', ['suggested_at'], unique=False)


def downgrade() -> None:
    """Drop export-related tables."""
    # Drop indexes
    op.drop_index('idx_aisuggestionanalytics_suggested_at', table_name='aisuggestionanalytics')
    op.drop_index('idx_aisuggestionanalytics_user_response', table_name='aisuggestionanalytics')
    op.drop_index('idx_aisuggestionanalytics_database_name', table_name='aisuggestionanalytics')

    # Drop AI suggestion analytics table
    op.drop_table('aisuggestionanalytics')

    # Drop indexes
    op.drop_index('idx_exporttasks_started_at', table_name='exporttasks')
    op.drop_index('idx_exporttasks_created_at', table_name='exporttasks')
    op.drop_index('idx_exporttasks_task_id', table_name='exporttasks')
    op.drop_index('idx_exporttasks_status', table_name='exporttasks')
    op.drop_index('idx_exporttasks_database_name', table_name='exporttasks')
    op.drop_index('idx_exporttasks_user_id', table_name='exporttasks')

    # Drop export tasks table
    op.drop_table('exporttasks')
