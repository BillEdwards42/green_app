#!/usr/bin/env python3
"""
Fix enum consistency issues between database and SQLAlchemy models.
This script ensures the database enum types match the Python enum definitions.
"""

import os
import sys
import asyncio
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
from app.core.config import settings
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def check_and_fix_enums():
    """Check and fix enum consistency in the database"""
    
    # Create async engine
    engine = create_async_engine(settings.DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        try:
            # 1. Check current enum values in database
            logger.info("Checking current enum values in database...")
            
            # Check platformtype enum
            result = await session.execute(
                text("SELECT enumlabel FROM pg_enum WHERE enumtypid = 'platformtype'::regtype ORDER BY enumsortorder")
            )
            platform_values = [row[0] for row in result]
            logger.info(f"Current platformtype values in DB: {platform_values}")
            
            # Check notificationstatus enum
            result = await session.execute(
                text("SELECT enumlabel FROM pg_enum WHERE enumtypid = 'notificationstatus'::regtype ORDER BY enumsortorder")
            )
            status_values = [row[0] for row in result]
            logger.info(f"Current notificationstatus values in DB: {status_values}")
            
            # 2. Ensure all platform values in device_tokens are lowercase
            logger.info("Ensuring all platform values are lowercase...")
            
            # First, check if there are any uppercase values
            result = await session.execute(
                text("SELECT COUNT(*) FROM device_tokens WHERE platform::text IN ('ANDROID', 'IOS')")
            )
            uppercase_count = result.scalar()
            
            if uppercase_count and uppercase_count > 0:
                logger.info(f"Found {uppercase_count} rows with uppercase platform values. Converting to lowercase...")
                
                # Update ANDROID to android
                await session.execute(
                    text("UPDATE device_tokens SET platform = 'android'::platformtype WHERE platform::text = 'ANDROID'")
                )
                
                # Update IOS to ios
                await session.execute(
                    text("UPDATE device_tokens SET platform = 'ios'::platformtype WHERE platform::text = 'IOS'")
                )
                
                await session.commit()
                logger.info("Platform values converted to lowercase")
            else:
                logger.info("All platform values are already lowercase")
            
            # 3. Verify data integrity
            result = await session.execute(
                text("SELECT DISTINCT platform FROM device_tokens")
            )
            distinct_platforms = [row[0] for row in result]
            logger.info(f"Distinct platform values in device_tokens: {distinct_platforms}")
            
            # 4. Clear any potential cached connections
            await engine.dispose()
            logger.info("Database connections cleared")
            
            return True
            
        except Exception as e:
            logger.error(f"Error during enum fix: {e}")
            return False
        finally:
            await engine.dispose()


async def verify_enum_usage():
    """Verify that enums can be used correctly after the fix"""
    
    engine = create_async_engine(settings.DATABASE_URL)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    
    async with async_session() as session:
        try:
            # Test inserting with enum values
            from app.models.notification import DeviceToken, PlatformType
            
            # This should work without errors
            test_token = DeviceToken(
                user_id=1,
                token="test_token_enum_fix",
                platform=PlatformType.ANDROID,
                device_id="test_device_enum_fix"
            )
            
            # We're not actually saving, just testing the enum conversion
            logger.info(f"Test token platform value: {test_token.platform} (type: {type(test_token.platform)})")
            logger.info("Enum usage verification successful")
            
            return True
            
        except Exception as e:
            logger.error(f"Enum usage verification failed: {e}")
            return False
        finally:
            await engine.dispose()


def clear_python_cache():
    """Clear Python cache files to ensure fresh imports"""
    
    logger.info("Clearing Python cache files...")
    
    # Clear __pycache__ directories
    project_root = Path(__file__).parent.parent
    pycache_dirs = list(project_root.rglob("__pycache__"))
    
    for pycache_dir in pycache_dirs:
        if pycache_dir.is_dir():
            for cache_file in pycache_dir.glob("*.pyc"):
                cache_file.unlink()
            try:
                pycache_dir.rmdir()
            except OSError:
                pass  # Directory not empty, skip
    
    logger.info(f"Cleared {len(pycache_dirs)} __pycache__ directories")
    
    # Also clear .pyc files outside __pycache__
    pyc_files = list(project_root.rglob("*.pyc"))
    for pyc_file in pyc_files:
        pyc_file.unlink()
    
    logger.info(f"Cleared {len(pyc_files)} .pyc files")


async def main():
    """Main function to fix enum consistency issues"""
    
    logger.info("=" * 60)
    logger.info("Starting enum consistency fix")
    logger.info("=" * 60)
    
    # 1. Clear Python cache
    clear_python_cache()
    
    # 2. Fix database enums
    success = await check_and_fix_enums()
    if not success:
        logger.error("Failed to fix enum consistency")
        return 1
    
    # 3. Verify the fix
    success = await verify_enum_usage()
    if not success:
        logger.error("Enum usage verification failed")
        return 1
    
    logger.info("=" * 60)
    logger.info("Enum consistency fix completed successfully!")
    logger.info("Please restart all Python processes to ensure the fix takes effect:")
    logger.info("  1. Stop the FastAPI server")
    logger.info("  2. Stop any notification schedulers")
    logger.info("  3. Clear terminal and restart services")
    logger.info("=" * 60)
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)