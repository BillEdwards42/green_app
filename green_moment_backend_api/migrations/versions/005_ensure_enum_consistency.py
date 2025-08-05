"""ensure enum consistency

Revision ID: 005
Revises: 004
Create Date: 2025-08-03 00:00:00.000000

This migration ensures database enum values are consistent with the application.
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy import text

# revision identifiers, used by Alembic.
revision: str = '005'
down_revision: Union[str, None] = '004'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """
    Ensure all platform enum values in the database are lowercase.
    This migration is idempotent and safe to run multiple times.
    """
    
    # Since we can't use LOWER() on enum types, we need to cast to text first
    # Check if there are any rows that need updating
    result = op.get_bind().execute(text("""
        SELECT COUNT(*) FROM device_tokens 
        WHERE platform::text IN ('ANDROID', 'IOS')
    """))
    count = result.scalar()
    
    if count and count > 0:
        print(f"Found {count} rows with uppercase platform values. Converting to lowercase...")
        
        # Update ANDROID to android
        op.execute(text("""
            UPDATE device_tokens 
            SET platform = 'android'::platformtype 
            WHERE platform::text = 'ANDROID'
        """))
        
        # Update IOS to ios
        op.execute(text("""
            UPDATE device_tokens 
            SET platform = 'ios'::platformtype 
            WHERE platform::text = 'IOS'
        """))
    else:
        print("All platform values are already lowercase.")
    
    # Log the final state
    result = op.get_bind().execute(text("""
        SELECT COUNT(DISTINCT platform) as count, 
               array_agg(DISTINCT platform::text ORDER BY platform::text) as platforms 
        FROM device_tokens
    """))
    row = result.fetchone()
    if row:
        print(f"Platform values after migration: {row.platforms}")


def downgrade() -> None:
    """
    No downgrade needed as lowercase values are valid.
    The original migration already uses lowercase enum values.
    """
    pass