"""Carbon-only system migration

Revision ID: 007
Revises: 006
Create Date: 2025-08-05

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers
revision = '007'
down_revision = '006'


def upgrade():
    # Add carbon tracking fields to users table
    op.add_column('users', sa.Column('current_month_carbon_saved', sa.Float(), nullable=False, server_default='0.0'))
    op.add_column('users', sa.Column('last_carbon_calculation_date', sa.Date(), nullable=True))
    
    # Create daily_carbon_progress table
    op.create_table('daily_carbon_progress',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('daily_carbon_saved', sa.Float(), nullable=False, default=0.0),
        sa.Column('cumulative_carbon_saved', sa.Float(), nullable=False, default=0.0),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'date', name='unique_user_date')
    )
    op.create_index(op.f('ix_daily_carbon_progress_user_id'), 'daily_carbon_progress', ['user_id'])
    op.create_index(op.f('ix_daily_carbon_progress_date'), 'daily_carbon_progress', ['date'])
    
    # League thresholds will be defined in code, not in database


def downgrade():
    # Remove daily_carbon_progress table
    op.drop_index(op.f('ix_daily_carbon_progress_date'), table_name='daily_carbon_progress')
    op.drop_index(op.f('ix_daily_carbon_progress_user_id'), table_name='daily_carbon_progress')
    op.drop_table('daily_carbon_progress')
    
    # Remove carbon tracking fields from users
    op.drop_column('users', 'last_carbon_calculation_date')
    op.drop_column('users', 'current_month_carbon_saved')