#!/usr/bin/env python3
"""
Set up scheduled notification for testing
"""

import asyncio
import sys
from datetime import datetime, timedelta
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.models import User, DeviceToken, NotificationSettings

# Create async engine
engine = create_async_engine(settings.DATABASE_URL, echo=False)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def setup_scheduled_notification(user_email: str, fcm_token: str):
    """Set up user for scheduled notification testing"""
    
    async with AsyncSessionLocal() as db:
        # Find user by email
        result = await db.execute(
            select(User).where(User.email == user_email)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            print(f"❌ User with email {user_email} not found!")
            return
        
        print(f"✅ Found user: {user.username} (ID: {user.id})")
        
        # 1. Register device token
        device_token = await db.execute(
            select(DeviceToken).where(
                DeviceToken.user_id == str(user.id),
                DeviceToken.device_id == "android_phone_test"
            )
        )
        device_token = device_token.scalar_one_or_none()
        
        if device_token:
            print("📱 Updating existing device token...")
            device_token.token = fcm_token
            device_token.is_active = True
            device_token.updated_at = datetime.utcnow()
        else:
            print("📱 Creating new device token...")
            device_token = DeviceToken(
                user_id=str(user.id),
                token=fcm_token,
                platform="android",
                device_id="android_phone_test",
                app_version="1.0.0"
            )
            db.add(device_token)
        
        # 2. Set up notification settings for next X0 minute
        current_time = datetime.now()
        current_minute = current_time.minute
        
        # Calculate next X0 minute (00, 10, 20, 30, 40, 50)
        next_x0_minute = ((current_minute // 10) + 1) * 10
        if next_x0_minute >= 60:
            next_x0_minute = 0
            next_time = current_time.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
        else:
            next_time = current_time.replace(minute=next_x0_minute, second=0, microsecond=0)
        
        scheduled_time = next_time.strftime("%H:%M")
        
        # Update notification settings
        settings_result = await db.execute(
            select(NotificationSettings).where(
                NotificationSettings.user_id == str(user.id)
            )
        )
        notification_settings = settings_result.scalar_one_or_none()
        
        if notification_settings:
            print(f"⏰ Updating notification time to {scheduled_time}...")
            notification_settings.enabled = True
            notification_settings.scheduled_time = scheduled_time
            notification_settings.daily_recommendation = True
            notification_settings.updated_at = datetime.utcnow()
        else:
            print(f"⏰ Creating notification settings for {scheduled_time}...")
            notification_settings = NotificationSettings(
                user_id=str(user.id),
                enabled=True,
                scheduled_time=scheduled_time,
                daily_recommendation=True,
                achievement_alerts=True,
                weekly_summary=True
            )
            db.add(notification_settings)
        
        await db.commit()
        
        print("\n✅ Setup complete!")
        print(f"📱 Device token registered")
        print(f"⏰ Notification scheduled for: {scheduled_time}")
        print(f"⏰ That's at: {next_time.strftime('%H:%M:%S')}")
        print(f"⏰ Current time: {current_time.strftime('%H:%M:%S')}")
        
        time_until = (next_time - current_time).total_seconds()
        print(f"\n⏳ Notification will be sent in {int(time_until // 60)} minutes and {int(time_until % 60)} seconds")
        
        print("\n📋 Next steps:")
        print("1. Run the notification scheduler:")
        print("   cd /home/bill/StudioProjects/green_moment_backend_api/scripts")
        print("   python run_notification_scheduler.py")
        print(f"2. Wait until {scheduled_time}")
        print("3. Check your phone for the notification!")


async def main():
    print("🚀 Green Moment Scheduled Notification Setup")
    print("=" * 50)
    
    # Get user email
    email = input("\n📧 Enter your Gmail address: ").strip()
    
    # Get FCM token
    print("\n📱 Enter the FCM token from your phone")
    print("(You can find this in the app's dashboard - orange debug box)")
    token = input("Token: ").strip()
    
    if not email or not token:
        print("❌ Email and token are required!")
        return
    
    # Set up scheduled notification
    await setup_scheduled_notification(email, token)


if __name__ == "__main__":
    asyncio.run(main())