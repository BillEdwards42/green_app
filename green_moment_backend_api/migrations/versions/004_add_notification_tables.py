"""add notification tables

Revision ID: 004
Revises: 003
Create Date: 2024-01-01 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '004'
down_revision: Union[str, None] = '003'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Create enum types (check if they exist first)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE platformtype AS ENUM ('android', 'ios');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    op.execute("""
        DO $$ BEGIN
            CREATE TYPE notificationstatus AS ENUM ('pending', 'sent', 'failed', 'delivered');
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
    """)
    
    # Create device_tokens table
    op.create_table('device_tokens',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('token', sa.Text(), nullable=False),
        sa.Column('platform', postgresql.ENUM('android', 'ios', name='platformtype', create_type=False), nullable=False),
        sa.Column('device_id', sa.String(), nullable=False),
        sa.Column('app_version', sa.String(), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=True, default=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.Column('last_used_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('token')
    )
    op.create_index(op.f('ix_device_tokens_id'), 'device_tokens', ['id'], unique=False)
    op.create_index('ix_device_tokens_user_device', 'device_tokens', ['user_id', 'device_id'], unique=False)
    
    # Create notification_settings table
    op.create_table('notification_settings',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('enabled', sa.Boolean(), nullable=True, default=True),
        sa.Column('scheduled_time', sa.String(), nullable=True, default='09:00'),
        sa.Column('daily_recommendation', sa.Boolean(), nullable=True, default=True),
        sa.Column('achievement_alerts', sa.Boolean(), nullable=True, default=True),
        sa.Column('weekly_summary', sa.Boolean(), nullable=True, default=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.Column('updated_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id')
    )
    op.create_index(op.f('ix_notification_settings_id'), 'notification_settings', ['id'], unique=False)
    
    # Create notification_logs table
    op.create_table('notification_logs',
        sa.Column('id', sa.String(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('device_token_id', sa.String(), nullable=True),
        sa.Column('title', sa.String(), nullable=True),
        sa.Column('body', sa.Text(), nullable=False),
        sa.Column('data', sa.Text(), nullable=True),
        sa.Column('notification_type', sa.String(), nullable=True, default='daily_recommendation'),
        sa.Column('status', postgresql.ENUM('pending', 'sent', 'failed', 'delivered', name='notificationstatus', create_type=False), nullable=True, default='pending'),
        sa.Column('sent_at', sa.DateTime(), nullable=True),
        sa.Column('delivered_at', sa.DateTime(), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('fcm_message_id', sa.String(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['device_token_id'], ['device_tokens.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_notification_logs_id'), 'notification_logs', ['id'], unique=False)
    op.create_index('ix_notification_logs_user_created', 'notification_logs', ['user_id', 'created_at'], unique=False)


def downgrade() -> None:
    # Drop tables
    op.drop_index('ix_notification_logs_user_created', table_name='notification_logs')
    op.drop_index(op.f('ix_notification_logs_id'), table_name='notification_logs')
    op.drop_table('notification_logs')
    
    op.drop_index(op.f('ix_notification_settings_id'), table_name='notification_settings')
    op.drop_table('notification_settings')
    
    op.drop_index('ix_device_tokens_user_device', table_name='device_tokens')
    op.drop_index(op.f('ix_device_tokens_id'), table_name='device_tokens')
    op.drop_table('device_tokens')
    
    # Drop enum types
    op.execute("DROP TYPE notificationstatus")
    op.execute("DROP TYPE platformtype")