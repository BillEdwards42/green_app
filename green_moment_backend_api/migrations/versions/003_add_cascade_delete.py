"""Add CASCADE DELETE to foreign keys

Revision ID: 003
Revises: 002_add_soft_delete_to_users
Create Date: 2025-08-01

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers
revision = '003'
down_revision = '002'
branch_labels = None
depends_on = None


def upgrade():
    """Add CASCADE DELETE to all foreign key relationships"""
    
    # Drop existing foreign key constraints
    with op.batch_alter_table('chores') as batch_op:
        batch_op.drop_constraint('chores_user_id_fkey', type_='foreignkey')
        batch_op.create_foreign_key(
            'chores_user_id_fkey', 
            'users', 
            ['user_id'], 
            ['id'], 
            ondelete='CASCADE'
        )
    
    with op.batch_alter_table('user_tasks') as batch_op:
        batch_op.drop_constraint('user_tasks_user_id_fkey', type_='foreignkey')
        batch_op.create_foreign_key(
            'user_tasks_user_id_fkey', 
            'users', 
            ['user_id'], 
            ['id'], 
            ondelete='CASCADE'
        )
    
    with op.batch_alter_table('monthly_summaries') as batch_op:
        batch_op.drop_constraint('monthly_summaries_user_id_fkey', type_='foreignkey')
        batch_op.create_foreign_key(
            'monthly_summaries_user_id_fkey', 
            'users', 
            ['user_id'], 
            ['id'], 
            ondelete='CASCADE'
        )


def downgrade():
    """Remove CASCADE DELETE from foreign key relationships"""
    
    # Restore original foreign key constraints without CASCADE
    with op.batch_alter_table('chores') as batch_op:
        batch_op.drop_constraint('chores_user_id_fkey', type_='foreignkey')
        batch_op.create_foreign_key(
            'chores_user_id_fkey', 
            'users', 
            ['user_id'], 
            ['id']
        )
    
    with op.batch_alter_table('user_tasks') as batch_op:
        batch_op.drop_constraint('user_tasks_user_id_fkey', type_='foreignkey')
        batch_op.create_foreign_key(
            'user_tasks_user_id_fkey', 
            'users', 
            ['user_id'], 
            ['id']
        )
    
    with op.batch_alter_table('monthly_summaries') as batch_op:
        batch_op.drop_constraint('monthly_summaries_user_id_fkey', type_='foreignkey')
        batch_op.create_foreign_key(
            'monthly_summaries_user_id_fkey', 
            'users', 
            ['user_id'], 
            ['id']
        )