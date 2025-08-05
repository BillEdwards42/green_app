"""Add league and task_type to tasks table

Revision ID: 002
Revises: 001
Create Date: 2025-08-03

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '006'
down_revision = '005'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add new columns to tasks table
    op.add_column('tasks', sa.Column('league', sa.String(), nullable=True))
    op.add_column('tasks', sa.Column('task_type', sa.String(), nullable=True))
    op.add_column('tasks', sa.Column('target_value', sa.Integer(), nullable=True))
    
    # Set default values for existing rows (if any)
    op.execute("UPDATE tasks SET league = 'bronze', task_type = 'other' WHERE league IS NULL")
    
    # Make league and task_type not nullable after setting defaults
    op.alter_column('tasks', 'league', nullable=False)
    op.alter_column('tasks', 'task_type', nullable=False)


def downgrade() -> None:
    # Remove the added columns
    op.drop_column('tasks', 'target_value')
    op.drop_column('tasks', 'task_type')
    op.drop_column('tasks', 'league')