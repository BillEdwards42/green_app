#!/usr/bin/env python3
"""
Setup notification test - handles integer user_id in database
"""

import asyncio
import sys
from datetime import datetime
from pathlib import Path
import json

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy import select, text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.models import User, NotificationSettings
from app.services.notification_service import NotificationService

# Create async engine
engine = create_async_engine(settings.DATABASE_URL, echo=False)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def setup_notification_for_scheduler(email: str, fcm_token: str):
    """Setup everything needed for notification scheduler"""
    
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
        
        # Save device token - use integer user_id as database expects
        try:
            # Delete existing test token
            await db.execute(text("""
                DELETE FROM device_tokens 
                WHERE user_id = :user_id AND device_id = :device_id
            """), {"user_id": user.id, "device_id": "scheduler_test"})  # Use integer directly
            
            # Insert new token with integer user_id
            device_id = f"{user.id}_scheduler_test"
            await db.execute(text("""
                INSERT INTO device_tokens 
                (id, user_id, token, platform, device_id, app_version, is_active, created_at, updated_at, last_used_at)
                VALUES 
                (:id, :user_id, :token, :platform, :device_id, :app_version, true, NOW(), NOW(), NOW())
            """), {
                "id": device_id,
                "user_id": user.id,  # Integer user_id
                "token": fcm_token,
                "platform": "android",
                "device_id": "scheduler_test",
                "app_version": "1.0.0"
            })
            
            print("✅ Device token saved")
            
            # Check/create notification settings (these use string user_id)
            result = await db.execute(
                select(NotificationSettings).where(
                    NotificationSettings.user_id == str(user.id)  # String for notification settings
                )
            )
            settings_obj = result.scalar_one_or_none()
            
            # Calculate next X0 minute mark
            now = datetime.now()
            current_minute = now.minute
            next_10_minute = ((current_minute // 10) + 1) * 10
            
            if next_10_minute >= 60:
                # Next hour
                next_hour = (now.hour + 1) % 24
                scheduled_time = f"{next_hour:02d}:00"
            else:
                scheduled_time = f"{now.hour:02d}:{next_10_minute:02d}"
            
            if not settings_obj:
                # Create settings
                settings_obj = NotificationSettings(
                    user_id=str(user.id),  # String for notification settings
                    enabled=True,
                    daily_recommendation=True,
                    scheduled_time=scheduled_time,
                    weather_updates=False
                )
                db.add(settings_obj)
                print(f"✅ Created notification settings for {scheduled_time}")
            else:
                # Update existing settings
                settings_obj.enabled = True
                settings_obj.daily_recommendation = True
                settings_obj.scheduled_time = scheduled_time
                print(f"✅ Updated notification time to {scheduled_time}")
            
            await db.commit()
            
            # Test immediate notification
            print("\n🔔 Sending test notification...")
            result = await NotificationService.send_notification(
                user_id=str(user.id),  # NotificationService expects string
                body="測試通知：通知系統已設置完成！",
                title=None,
                data={
                    'type': 'test',
                    'message': f'下次排程通知時間: {scheduled_time}'
                },
                notification_type='test_notification',
                db=db
            )
            
            if result['success']:
                print("✅ Test notification sent successfully!")
            else:
                print(f"❌ Failed to send test notification: {result.get('error', 'Unknown error')}")
            
            print(f"\n🎉 Setup complete!")
            print(f"📅 Next scheduled notification: {scheduled_time}")
            print(f"⏰ Current time: {datetime.now().strftime('%H:%M:%S')}")
            print(f"\n📝 Next steps:")
            print(f"1. Run the scheduler: python scripts/run_notification_scheduler.py")
            print(f"2. The scheduler will check every minute at X0 marks")
            print(f"3. You should receive a notification at {scheduled_time}")
            
            # Show device tokens for debugging
            print("\n🔍 Verifying device tokens:")
            tokens = await db.execute(text("""
                SELECT id, device_id, is_active, created_at 
                FROM device_tokens 
                WHERE user_id = :user_id
            """), {"user_id": user.id})
            
            for token in tokens:
                print(f"  - {token.device_id}: active={token.is_active}, created={token.created_at}")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            await db.rollback()


async def main():
    print("🔔 Green Moment Notification Scheduler Setup")
    print("=" * 50)
    print("\nThis will set up everything needed for the notification scheduler to work.")
    
    email = input("\n📧 Enter your Gmail address: ").strip()
    print("\n📱 Enter the FCM token from your phone")
    print("(You can find this in the app's dashboard - orange debug box)")
    token = input("Token: ").strip()
    
    if email and token:
        await setup_notification_for_scheduler(email, token)
    else:
        print("❌ Email and token are required!")


if __name__ == "__main__":
    asyncio.run(main())