"""Add soft delete to users table

Revision ID: 002
Revises: 001
Create Date: 2025-07-31

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = '002'
down_revision = '001'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add deleted_at column for soft delete
    op.add_column('users', sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True))
    
    # Drop unique constraint on google_id to allow re-registration
    op.drop_constraint('users_google_id_key', 'users', type_='unique')
    
    # Create regular index on google_id for performance
    op.create_index('ix_users_google_id', 'users', ['google_id'])


def downgrade() -> None:
    # Drop the index
    op.drop_index('ix_users_google_id', 'users')
    
    # Recreate unique constraint on google_id
    op.create_unique_constraint('users_google_id_key', 'users', ['google_id'])
    
    # Remove deleted_at column
    op.drop_column('users', 'deleted_at')