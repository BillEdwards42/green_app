#!/usr/bin/env python3
"""
Check and fix notification setup for scheduler
"""

import asyncio
import sys
from datetime import datetime
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.models import User, NotificationSettings

# Create async engine
engine = create_async_engine(settings.DATABASE_URL, echo=False)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def check_database_schema():
    """Check the actual database schema"""
    
    async with AsyncSessionLocal() as db:
        print("🔍 Checking database schema...")
        
        # Check device_tokens table
        result = await db.execute(text("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'device_tokens'
            ORDER BY ordinal_position
        """))
        
        columns = result.fetchall()
        print("\n📊 device_tokens table schema:")
        for col in columns:
            print(f"  - {col.column_name}: {col.data_type}")
            
        # Check users table
        result = await db.execute(text("""
            SELECT column_name, data_type 
            FROM information_schema.columns 
            WHERE table_name = 'users' AND column_name = 'id'
        """))
        
        user_id_col = result.fetchone()
        print(f"\n👤 users.id column: {user_id_col.data_type if user_id_col else 'NOT FOUND'}")


async def check_user_notification_settings(email: str):
    """Check if user has notification settings"""
    
    async with AsyncSessionLocal() as db:
        # Find user
        result = await db.execute(
            select(User).where(User.email == email)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            print(f"❌ User with email {email} not found!")
            return None
            
        print(f"\n✅ Found user: {user.username} (ID: {user.id})")
        
        # Check notification settings
        result = await db.execute(
            select(NotificationSettings).where(
                NotificationSettings.user_id == str(user.id)
            )
        )
        settings = result.scalar_one_or_none()
        
        if settings:
            print(f"\n🔔 Notification settings:")
            print(f"  - Enabled: {settings.enabled}")
            print(f"  - Daily recommendation: {settings.daily_recommendation}")
            print(f"  - Scheduled time: {settings.scheduled_time}")
            print(f"  - Weather updates: {settings.weather_updates}")
        else:
            print("\n❌ No notification settings found")
            print("📝 Creating default notification settings...")
            
            # Create default settings
            new_settings = NotificationSettings(
                user_id=str(user.id),
                enabled=True,
                daily_recommendation=True,
                scheduled_time="09:00",  # Default 9 AM
                weather_updates=False
            )
            db.add(new_settings)
            await db.commit()
            print("✅ Default notification settings created")
            
        return user.id


async def setup_test_notification(email: str, fcm_token: str):
    """Setup everything needed for notification scheduler to work"""
    
    async with AsyncSessionLocal() as db:
        # Find user
        result = await db.execute(
            select(User).where(User.email == email)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            print(f"❌ User with email {email} not found!")
            return
            
        print(f"\n✅ Found user: {user.username} (ID: {user.id})")
        
        # Save device token using raw SQL to handle type conversion
        try:
            # Delete existing test token
            await db.execute(text("""
                DELETE FROM device_tokens 
                WHERE user_id = :user_id AND device_id = :device_id
            """), {"user_id": str(user.id), "device_id": "scheduler_test"})
            
            # Insert new token
            await db.execute(text("""
                INSERT INTO device_tokens 
                (id, user_id, token, platform, device_id, app_version, is_active, created_at, updated_at, last_used_at)
                VALUES 
                (:id, :user_id, :token, :platform, :device_id, :app_version, true, NOW(), NOW(), NOW())
            """), {
                "id": f"{user.id}_scheduler_test",
                "user_id": str(user.id),
                "token": fcm_token,
                "platform": "android",
                "device_id": "scheduler_test",
                "app_version": "1.0.0"
            })
            
            print("✅ Device token saved")
            
            # Check/create notification settings
            result = await db.execute(
                select(NotificationSettings).where(
                    NotificationSettings.user_id == str(user.id)
                )
            )
            settings = result.scalar_one_or_none()
            
            if not settings:
                # Create settings for next 10-minute mark
                now = datetime.now()
                next_10 = ((now.minute // 10) + 1) * 10
                if next_10 >= 60:
                    next_10 = 0
                    
                scheduled_time = f"{now.hour:02d}:{next_10:02d}"
                if next_10 == 0:
                    # Next hour
                    scheduled_time = f"{(now.hour + 1) % 24:02d}:00"
                
                settings = NotificationSettings(
                    user_id=str(user.id),
                    enabled=True,
                    daily_recommendation=True,
                    scheduled_time=scheduled_time,
                    weather_updates=False
                )
                db.add(settings)
                print(f"✅ Created notification settings for {scheduled_time}")
            else:
                # Update to next 10-minute mark for testing
                now = datetime.now()
                next_10 = ((now.minute // 10) + 1) * 10
                if next_10 >= 60:
                    next_10 = 0
                    
                scheduled_time = f"{now.hour:02d}:{next_10:02d}"
                if next_10 == 0:
                    # Next hour
                    scheduled_time = f"{(now.hour + 1) % 24:02d}:00"
                    
                settings.scheduled_time = scheduled_time
                settings.enabled = True
                settings.daily_recommendation = True
                print(f"✅ Updated notification time to {scheduled_time}")
            
            await db.commit()
            
            print(f"\n🎉 Setup complete!")
            print(f"📅 Notification scheduled for: {settings.scheduled_time}")
            print(f"⏰ Current time: {datetime.now().strftime('%H:%M')}")
            print(f"\n📝 Next steps:")
            print(f"1. Run the scheduler: python scripts/run_notification_scheduler.py")
            print(f"2. Wait for the next X0 minute mark")
            print(f"3. You should receive a notification at {settings.scheduled_time}")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            await db.rollback()


async def main():
    print("🔔 Green Moment Notification Setup Checker")
    print("=" * 50)
    
    # First check schema
    await check_database_schema()
    
    print("\n" + "=" * 50)
    print("\nOptions:")
    print("1. Check notification settings for a user")
    print("2. Setup everything for notification scheduler test")
    print("3. Exit")
    
    choice = input("\nSelect option (1-3): ").strip()
    
    if choice == "1":
        email = input("\n📧 Enter your Gmail address: ").strip()
        if email:
            await check_user_notification_settings(email)
            
    elif choice == "2":
        email = input("\n📧 Enter your Gmail address: ").strip()
        print("\n📱 Enter the FCM token from your phone")
        print("(You can find this in the app's dashboard - orange debug box)")
        token = input("Token: ").strip()
        
        if email and token:
            await setup_test_notification(email, token)


if __name__ == "__main__":
    asyncio.run(main())