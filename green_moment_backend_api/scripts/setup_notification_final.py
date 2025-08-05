#!/usr/bin/env python3
"""
Final setup script for notifications - handles all type issues correctly
"""

import asyncio
import sys
from datetime import datetime
from pathlib import Path
import json

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.models import User
from app.services.notification_service import NotificationService

# Create async engine
engine = create_async_engine(settings.DATABASE_URL, echo=False)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def setup_notification_complete(email: str, fcm_token: str):
    """Complete notification setup handling all type issues"""
    
    async with AsyncSessionLocal() as db:
        try:
            # Find user using raw SQL to avoid ORM issues
            result = await db.execute(text("""
                SELECT id, username FROM users WHERE email = :email AND deleted_at IS NULL
            """), {"email": email})
            
            user = result.fetchone()
            if not user:
                print(f"❌ User with email {email} not found!")
                return
                
            user_id = user.id  # This is an integer
            print(f"\n✅ Found user: {user.username} (ID: {user_id})")
            
            # 1. Save device token (user_id as integer)
            print("\n📱 Setting up device token...")
            
            # Delete existing test token
            await db.execute(text("""
                DELETE FROM device_tokens 
                WHERE user_id = :user_id AND device_id = :device_id
            """), {"user_id": user_id, "device_id": "scheduler_test"})
            
            # Insert new token
            device_token_id = f"{user_id}_scheduler_test"
            await db.execute(text("""
                INSERT INTO device_tokens 
                (id, user_id, token, platform, device_id, app_version, is_active, created_at, updated_at, last_used_at)
                VALUES 
                (:id, :user_id, :token, :platform::platform_type, :device_id, :app_version, true, NOW(), NOW(), NOW())
            """), {
                "id": device_token_id,
                "user_id": user_id,  # Integer
                "token": fcm_token,
                "platform": "android",
                "device_id": "scheduler_test",
                "app_version": "1.0.0"
            })
            print("✅ Device token saved")
            
            # 2. Setup notification settings (user_id as integer)
            print("\n🔔 Setting up notification settings...")
            
            # Calculate next X0 minute
            now = datetime.now()
            current_minute = now.minute
            next_10_minute = ((current_minute // 10) + 1) * 10
            
            if next_10_minute >= 60:
                next_hour = (now.hour + 1) % 24
                scheduled_time = f"{next_hour:02d}:00"
            else:
                scheduled_time = f"{now.hour:02d}:{next_10_minute:02d}"
            
            # Check if settings exist
            result = await db.execute(text("""
                SELECT id FROM notification_settings WHERE user_id = :user_id
            """), {"user_id": user_id})
            
            existing = result.fetchone()
            
            if existing:
                # Update existing
                await db.execute(text("""
                    UPDATE notification_settings 
                    SET enabled = true, 
                        daily_recommendation = true, 
                        scheduled_time = :scheduled_time,
                        updated_at = NOW()
                    WHERE user_id = :user_id
                """), {"user_id": user_id, "scheduled_time": scheduled_time})
                print(f"✅ Updated notification settings for {scheduled_time}")
            else:
                # Create new
                settings_id = f"settings_{user_id}"
                await db.execute(text("""
                    INSERT INTO notification_settings 
                    (id, user_id, enabled, scheduled_time, daily_recommendation, achievement_alerts, weekly_summary, weather_updates, created_at, updated_at)
                    VALUES 
                    (:id, :user_id, true, :scheduled_time, true, true, false, false, NOW(), NOW())
                """), {
                    "id": settings_id,
                    "user_id": user_id,  # Integer
                    "scheduled_time": scheduled_time
                })
                print(f"✅ Created notification settings for {scheduled_time}")
            
            await db.commit()
            
            # 3. Send test notification
            print("\n🔔 Sending test notification...")
            
            # NotificationService expects string user_id, so convert
            result = await NotificationService.send_notification(
                user_id=str(user_id),  # Convert to string for service
                body=f"測試成功！下次通知時間：{scheduled_time} 🎉",
                title=None,
                data={
                    'type': 'test',
                    'scheduled_time': scheduled_time,
                    'current_time': datetime.now().strftime('%H:%M:%S')
                },
                notification_type='test_notification',
                db=db
            )
            
            if result['success']:
                print("✅ Test notification sent successfully!")
            else:
                print(f"❌ Failed to send test notification: {result.get('error', 'Unknown error')}")
            
            # 4. Verify setup
            print("\n🔍 Verifying setup:")
            
            # Check device tokens
            tokens = await db.execute(text("""
                SELECT device_id, is_active, created_at 
                FROM device_tokens 
                WHERE user_id = :user_id
            """), {"user_id": user_id})
            
            print("\n📱 Device tokens:")
            for token in tokens:
                print(f"  - {token.device_id}: active={token.is_active}, created={token.created_at}")
            
            # Check notification settings
            settings = await db.execute(text("""
                SELECT enabled, daily_recommendation, scheduled_time 
                FROM notification_settings 
                WHERE user_id = :user_id
            """), {"user_id": user_id})
            
            setting = settings.fetchone()
            if setting:
                print(f"\n🔔 Notification settings:")
                print(f"  - Enabled: {setting.enabled}")
                print(f"  - Daily recommendations: {setting.daily_recommendation}")
                print(f"  - Scheduled time: {setting.scheduled_time}")
            
            print(f"\n🎉 Setup complete!")
            print(f"⏰ Current time: {datetime.now().strftime('%H:%M:%S')}")
            print(f"📅 Next notification: {scheduled_time}")
            print(f"\n📝 To start the scheduler:")
            print(f"   python scripts/run_notification_scheduler.py")
            print(f"\nThe scheduler will run every minute and check for users")
            print(f"scheduled at X0 marks (00, 10, 20, 30, 40, 50)")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
            await db.rollback()


async def main():
    print("🔔 Green Moment Notification Setup (Final)")
    print("=" * 50)
    print("\nThis will properly set up notifications handling all type issues.")
    
    email = input("\n📧 Enter your Gmail address: ").strip()
    print("\n📱 Enter the FCM token from your phone")
    print("(You can find this in the app's dashboard - orange debug box)")
    token = input("Token: ").strip()
    
    if email and token:
        await setup_notification_complete(email, token)
    else:
        print("❌ Email and token are required!")


if __name__ == "__main__":
    asyncio.run(main())