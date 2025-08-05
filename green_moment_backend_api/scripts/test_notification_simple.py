#!/usr/bin/env python3
"""
Simple script to test push notifications with your phone
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


async def test_with_real_token(user_email: str, fcm_token: str):
    """Test notification with real FCM token from your phone"""
    
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
        
        # Update or create device token
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
                user_id=str(user.id),  # Convert to string
                token=fcm_token,
                platform="android",
                device_id="android_phone_test",
                app_version="1.0.0"
            )
            db.add(device_token)
        
        await db.commit()
        
        # Send test notification
        print("\n🔔 Sending test notification...")
        
        result = await NotificationService.send_notification(
            user_id=str(user.id),
            body="測試通知：現在是低碳時段！快來使用高耗能家電吧 💚",
            title=None,  # No title as per app design
            data={
                'type': 'test',
                'optimal_hours': '[10, 14, 22]',
                'timestamp': datetime.now().isoformat()
            },
            notification_type='test_notification',
            db=db
        )
        
        print(f"\n📊 Result: {result}")
        
        if result['success']:
            print("✅ Notification sent successfully! Check your phone!")
        else:
            print("❌ Failed to send notification")


async def main():
    print("🚀 Green Moment Push Notification Test")
    print("=" * 50)
    
    print("\nThis script will send a test notification to your phone.")
    print("\nYou need:")
    print("1. Your Gmail account used to log in to the app")
    print("2. The FCM token from your phone (shown in the app)")
    
    print("\n" + "=" * 50)
    
    # Get user email
    email = input("\n📧 Enter your Gmail address: ").strip()
    
    # Get FCM token
    print("\n📱 Enter the FCM token from your phone")
    print("(You can find this in the app's dashboard - orange debug box)")
    token = input("Token: ").strip()
    
    if not email or not token:
        print("❌ Email and token are required!")
        return
    
    # Send test notification
    await test_with_real_token(email, token)


if __name__ == "__main__":
    asyncio.run(main())