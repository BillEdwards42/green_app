#!/usr/bin/env python3
"""
Test script to set up and test push notifications
"""

import asyncio
import sys
from datetime import datetime
from pathlib import Path

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy import select
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.models import User, DeviceToken, NotificationSettings
from app.services.notification_service import NotificationService

# Create async engine
engine = create_async_engine(settings.DATABASE_URL, echo=False)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def setup_test_user():
    """Set up a test user with device token and notification settings"""
    
    async with AsyncSessionLocal() as db:
        # Find or create a test user
        result = await db.execute(
            select(User).where(User.username == "test_notification_user")
        )
        user = result.scalar_one_or_none()
        
        if not user:
            print("Creating test user...")
            user = User(
                username="test_notification_user",
                email="test@example.com",
                is_anonymous=False,
                current_league="bronze",
                total_carbon_saved=0.0
            )
            db.add(user)
            await db.commit()
            await db.refresh(user)
            print(f"Created user with ID: {user.id}")
        else:
            print(f"Found existing test user with ID: {user.id}")
        
        # Create/update device token
        device_token = await db.execute(
            select(DeviceToken).where(
                DeviceToken.user_id == user.id,
                DeviceToken.device_id == "test_device_001"
            )
        )
        device_token = device_token.scalar_one_or_none()
        
        if not device_token:
            print("Creating test device token...")
            device_token = DeviceToken(
                user_id=user.id,
                # This is a dummy token - replace with a real FCM token for actual testing
                token="TEST_FCM_TOKEN_12345",
                platform="android",
                device_id="test_device_001",
                app_version="1.0.0"
            )
            db.add(device_token)
        else:
            print("Updating existing device token...")
            device_token.is_active = True
            device_token.updated_at = datetime.utcnow()
        
        # Create/update notification settings
        settings_result = await db.execute(
            select(NotificationSettings).where(
                NotificationSettings.user_id == user.id
            )
        )
        notification_settings = settings_result.scalar_one_or_none()
        
        # Get current time for immediate testing
        current_time = datetime.now().strftime("%H:%M")
        
        if not notification_settings:
            print(f"Creating notification settings for {current_time}...")
            notification_settings = NotificationSettings(
                user_id=user.id,
                enabled=True,
                scheduled_time=current_time,  # Set to current time for immediate test
                daily_recommendation=True,
                achievement_alerts=True,
                weekly_summary=True
            )
            db.add(notification_settings)
        else:
            print(f"Updating notification settings to {current_time}...")
            notification_settings.enabled = True
            notification_settings.scheduled_time = current_time
            notification_settings.daily_recommendation = True
            notification_settings.updated_at = datetime.utcnow()
        
        await db.commit()
        
        print("\n✅ Test user setup complete!")
        print(f"User ID: {user.id}")
        print(f"Username: {user.username}")
        print(f"Device Token: {device_token.token[:20]}...")
        print(f"Notification Time: {notification_settings.scheduled_time}")
        print(f"Notifications Enabled: {notification_settings.enabled}")
        
        return user.id


async def test_send_notification(user_id: int):
    """Test sending a notification directly"""
    
    print("\n🔔 Testing direct notification send...")
    
    async with AsyncSessionLocal() as db:
        result = await NotificationService.send_notification(
            user_id=str(user_id),
            body="測試通知：現在是低碳時段！快來使用高耗能家電吧 💚",
            title=None,  # No title as per Flutter app requirement
            data={
                'type': 'test',
                'optimal_hours': '[10, 14, 22]',
                'test_timestamp': datetime.now().isoformat()
            },
            notification_type='test_notification',
            db=db
        )
        
        print(f"\nNotification send result: {result}")


async def main():
    """Main test function"""
    
    print("🚀 Green Moment Notification Test Script")
    print("=" * 50)
    
    # Step 1: Set up test user
    user_id = await setup_test_user()
    
    # Step 2: Test direct notification (optional)
    print("\nDo you want to test sending a notification directly? (y/n): ", end="")
    response = input().strip().lower()
    
    if response == 'y':
        await test_send_notification(user_id)
    
    # Step 3: Instructions for testing scheduler
    print("\n📋 Next Steps to Test Scheduler:")
    print("1. Make sure the backend API is running")
    print("2. Run the notification scheduler manually:")
    print("   cd /home/bill/StudioProjects/green_moment_backend_api/scripts")
    print("   python notification_scheduler.py")
    print("\n3. Or wait for the scheduled run (every X0 minutes)")
    print("4. Check logs at: logs/notification_scheduler.log")
    
    print("\n⚠️  Note: For real push notifications to work:")
    print("- Replace TEST_FCM_TOKEN_12345 with a real FCM token from your Flutter app")
    print("- Make sure Firebase Admin SDK is properly configured")
    print("- Device must have the app installed and notifications enabled")


if __name__ == "__main__":
    asyncio.run(main())