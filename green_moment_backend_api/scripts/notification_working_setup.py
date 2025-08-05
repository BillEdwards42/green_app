#!/usr/bin/env python3
"""
Working notification setup that handles the Integer user_id correctly
This works with the ACTUAL database schema, not the incorrect models
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
from app.services.notification_service import NotificationService

# Create async engine
engine = create_async_engine(settings.DATABASE_URL, echo=False)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def setup_notifications_correctly(email: str, fcm_token: str):
    """Setup notifications working with the actual database schema"""
    
    async with AsyncSessionLocal() as db:
        try:
            # 1. Find user
            result = await db.execute(text("""
                SELECT id, username FROM users WHERE email = :email AND deleted_at IS NULL
            """), {"email": email})
            
            user = result.fetchone()
            if not user:
                print(f"❌ User with email {email} not found!")
                return
                
            user_id = user.id  # This is an INTEGER
            print(f"\n✅ Found user: {user.username} (ID: {user_id})")
            
            # 2. Create device token with proper types
            print("\n📱 Setting up device token...")
            
            # Delete existing
            await db.execute(text("""
                DELETE FROM device_tokens WHERE user_id = :user_id AND device_id = :device_id
            """), {"user_id": user_id, "device_id": "scheduler_test"})
            
            # Create composite string ID for the token record
            device_token_id = f"{user_id}_scheduler_test"
            
            # Insert with correct types - use literal for platform enum
            await db.execute(text("""
                INSERT INTO device_tokens 
                (id, user_id, token, platform, device_id, app_version, is_active, created_at, updated_at, last_used_at)
                VALUES 
                (:id, :user_id, :token, 'android', :device_id, :app_version, true, NOW(), NOW(), NOW())
            """), {
                "id": device_token_id,
                "user_id": user_id,  # INTEGER
                "token": fcm_token,
                "device_id": "scheduler_test", 
                "app_version": "1.0.0"
            })
            print("✅ Device token saved")
            
            # 3. Setup notification settings
            print("\n🔔 Setting up notification settings...")
            
            # Calculate next X0 minute
            now = datetime.now()
            current_minute = now.minute
            minutes_to_next_10 = (10 - (current_minute % 10)) % 10
            if minutes_to_next_10 == 0:
                minutes_to_next_10 = 10
                
            next_time = now.replace(second=0, microsecond=0)
            next_time = next_time.replace(minute=((current_minute + minutes_to_next_10) % 60))
            if current_minute + minutes_to_next_10 >= 60:
                next_time = next_time.replace(hour=(next_time.hour + 1) % 24)
            
            scheduled_time = next_time.strftime("%H:%M")
            
            # Check existing settings
            result = await db.execute(text("""
                SELECT id FROM notification_settings WHERE user_id = :user_id
            """), {"user_id": user_id})
            
            existing = result.fetchone()
            
            if existing:
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
                settings_id = f"settings_{user_id}"
                await db.execute(text("""
                    INSERT INTO notification_settings 
                    (id, user_id, enabled, scheduled_time, daily_recommendation, 
                     achievement_alerts, weekly_summary, created_at, updated_at)
                    VALUES 
                    (:id, :user_id, true, :scheduled_time, true, true, false, NOW(), NOW())
                """), {
                    "id": settings_id,
                    "user_id": user_id,  # INTEGER
                    "scheduled_time": scheduled_time
                })
                print(f"✅ Created notification settings for {scheduled_time}")
            
            # Add weather_updates column if it doesn't exist (might be missing)
            try:
                await db.execute(text("""
                    ALTER TABLE notification_settings 
                    ADD COLUMN IF NOT EXISTS weather_updates BOOLEAN DEFAULT false
                """))
            except:
                pass  # Column might already exist
            
            await db.commit()
            
            # 4. Send test notification
            print("\n🔔 Sending test notification...")
            
            # NotificationService expects string user_id
            result = await NotificationService.send_notification(
                user_id=str(user_id),  # Convert to string for the service
                body=f"通知設置成功！下次通知時間：{scheduled_time} 🎉",
                title=None,
                data={
                    'type': 'test_setup',
                    'scheduled_time': scheduled_time,
                    'current_time': datetime.now().strftime('%H:%M:%S')
                },
                notification_type='test_notification',
                db=db
            )
            
            if result['success']:
                print("✅ Test notification sent!")
            else:
                print(f"⚠️  Notification might have failed: {result}")
            
            # 5. Final verification
            print("\n🔍 Final verification:")
            
            # Verify token
            tokens = await db.execute(text("""
                SELECT device_id, is_active FROM device_tokens WHERE user_id = :user_id
            """), {"user_id": user_id})
            
            print("\n📱 Device tokens:")
            for token in tokens:
                print(f"  - {token.device_id}: active={token.is_active}")
            
            # Verify settings
            settings = await db.execute(text("""
                SELECT enabled, scheduled_time, daily_recommendation 
                FROM notification_settings WHERE user_id = :user_id
            """), {"user_id": user_id})
            
            setting = settings.fetchone()
            if setting:
                print(f"\n🔔 Notification settings:")
                print(f"  - Enabled: {setting.enabled}")
                print(f"  - Daily recommendations: {setting.daily_recommendation}")
                print(f"  - Scheduled time: {setting.scheduled_time}")
            
            print(f"\n✅ All set! The notification scheduler will send notifications at {scheduled_time}")
            print(f"⏰ Current time: {datetime.now().strftime('%H:%M:%S')}")
            print(f"⏱️  Time until next notification: ~{minutes_to_next_10} minutes")
            print(f"\n📝 Start the scheduler with:")
            print(f"   python scripts/run_notification_scheduler.py")
            
        except Exception as e:
            print(f"❌ Error: {e}")
            import traceback
            traceback.print_exc()
            await db.rollback()


async def main():
    print("🔔 Green Moment Notification Setup (Working Version)")
    print("=" * 50)
    print("\nThis version works with the actual database schema.")
    
    email = input("\n📧 Enter your Gmail address: ").strip()
    print("\n📱 Enter the FCM token from your phone")
    print("(You can find this in the app's dashboard - orange debug box)")
    token = input("Token: ").strip()
    
    if email and token:
        await setup_notifications_correctly(email, token)
    else:
        print("❌ Email and token are required!")


if __name__ == "__main__":
    asyncio.run(main())