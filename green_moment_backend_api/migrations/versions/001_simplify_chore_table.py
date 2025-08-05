"""Simplify chore table to only essential fields

Revision ID: 001
Revises: 
Create Date: 2025-07-31

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '001'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # First add duration_minutes column with a temporary default
    op.add_column('chores', sa.Column('duration_minutes', sa.Integer(), nullable=True))
    
    # Convert existing duration_hours to duration_minutes
    op.execute("""
        UPDATE chores 
        SET duration_minutes = CAST(duration_hours * 60 AS INTEGER)
        WHERE duration_hours IS NOT NULL
    """)
    
    # Now make duration_minutes not nullable
    op.alter_column('chores', 'duration_minutes', nullable=False)
    
    # Drop unnecessary columns from chores table
    op.drop_column('chores', 'power_consumption_watts')
    op.drop_column('chores', 'estimated_carbon_saved')
    op.drop_column('chores', 'average_carbon_intensity')
    op.drop_column('chores', 'peak_carbon_intensity')
    op.drop_column('chores', 'actual_carbon_emitted')
    op.drop_column('chores', 'hypothetical_peak_emission')
    op.drop_column('chores', 'actual_carbon_saved')
    op.drop_column('chores', 'monthly_calculated')
    op.drop_column('chores', 'updated_at')
    op.drop_column('chores', 'duration_hours')


def downgrade() -> None:
    # Add back removed columns
    op.add_column('chores', sa.Column('duration_hours', sa.Float(), nullable=False))
    op.add_column('chores', sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True))
    op.add_column('chores', sa.Column('monthly_calculated', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('chores', sa.Column('actual_carbon_saved', sa.Float(), nullable=True))
    op.add_column('chores', sa.Column('hypothetical_peak_emission', sa.Float(), nullable=True))
    op.add_column('chores', sa.Column('actual_carbon_emitted', sa.Float(), nullable=True))
    op.add_column('chores', sa.Column('peak_carbon_intensity', sa.Float(), nullable=False, server_default='0'))
    op.add_column('chores', sa.Column('average_carbon_intensity', sa.Float(), nullable=False, server_default='0'))
    op.add_column('chores', sa.Column('estimated_carbon_saved', sa.Float(), nullable=False, server_default='0'))
    op.add_column('chores', sa.Column('power_consumption_watts', sa.Float(), nullable=False, server_default='0'))
    
    # Remove duration_minutes column
    op.drop_column('chores', 'duration_minutes')