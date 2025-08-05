#!/usr/bin/env python3
"""
Direct notification test - bypasses device token lookup issues
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
from app.models import User, DeviceToken, NotificationSettings
import firebase_admin
from firebase_admin import credentials, messaging

# Create async engine
engine = create_async_engine(settings.DATABASE_URL, echo=False)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

# Initialize Firebase Admin SDK if not already initialized
if not firebase_admin._apps:
    # Resolve the path relative to the backend api directory
    firebase_path = Path(__file__).parent.parent / settings.FIREBASE_CREDENTIALS_PATH
    cred = credentials.Certificate(str(firebase_path))
    firebase_admin.initialize_app(cred)
    print("✅ Firebase Admin SDK initialized")


async def send_direct_notification(fcm_token: str):
    """Send notification directly using FCM token"""
    
    try:
        # Create the message
        message = messaging.Message(
            notification=messaging.Notification(
                body="測試通知：現在是低碳時段！快來使用高耗能家電吧 💚"
            ),
            data={
                'type': 'test',
                'optimal_hours': json.dumps([10, 14, 22]),
                'timestamp': datetime.now().isoformat()
            },
            token=fcm_token
        )
        
        # Send the message
        response = messaging.send(message)
        print(f"✅ Successfully sent message: {response}")
        return True
        
    except Exception as e:
        print(f"❌ Error sending message: {e}")
        return False


async def check_device_tokens(user_email: str):
    """Check device tokens in database"""
    
    async with AsyncSessionLocal() as db:
        # Find user
        result = await db.execute(
            select(User).where(User.email == user_email)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            print(f"❌ User with email {user_email} not found!")
            return None
        
        print(f"✅ Found user: {user.username} (ID: {user.id}, Type: {type(user.id)})")
        
        # Check device tokens with raw SQL to avoid type issues
        result = await db.execute(
            text("""
                SELECT id, user_id, token, device_id, is_active, created_at 
                FROM device_tokens 
                WHERE user_id = :user_id::text
                ORDER BY created_at DESC
            """),
            {"user_id": str(user.id)}
        )
        
        tokens = result.fetchall()
        
        if tokens:
            print(f"\n📱 Found {len(tokens)} device token(s):")
            for token in tokens:
                print(f"  - Device: {token.device_id}")
                print(f"    Active: {token.is_active}")
                print(f"    Created: {token.created_at}")
                print(f"    Token: {token.token[:50]}...")
        else:
            print("\n❌ No device tokens found for this user")
            
        return user.id


async def save_device_token_direct(user_id: int, fcm_token: str):
    """Save device token using direct SQL to avoid type issues"""
    
    async with AsyncSessionLocal() as db:
        try:
            # Delete existing token for this device
            await db.execute(
                text("""
                    DELETE FROM device_tokens 
                    WHERE user_id = :user_id::text 
                    AND device_id = :device_id
                """),
                {"user_id": str(user_id), "device_id": "test_device"}
            )
            
            # Insert new token
            await db.execute(
                text("""
                    INSERT INTO device_tokens 
                    (id, user_id, token, platform, device_id, app_version, is_active, created_at, updated_at, last_used_at)
                    VALUES 
                    (:id, :user_id::text, :token, :platform, :device_id, :app_version, true, NOW(), NOW(), NOW())
                """),
                {
                    "id": f"{user_id}_test_device",
                    "user_id": str(user_id),
                    "token": fcm_token,
                    "platform": "android",
                    "device_id": "test_device",
                    "app_version": "1.0.0"
                }
            )
            
            await db.commit()
            print("✅ Device token saved successfully")
            
        except Exception as e:
            print(f"❌ Error saving device token: {e}")
            await db.rollback()


async def main():
    print("🚀 Green Moment Direct Notification Test")
    print("=" * 50)
    
    print("\nThis script will send a test notification directly to your phone.")
    print("\nOptions:")
    print("1. Send notification directly (just need FCM token)")
    print("2. Check device tokens for a user")
    print("3. Save token and send notification")
    
    choice = input("\nSelect option (1-3): ").strip()
    
    if choice == "1":
        # Direct send
        print("\n📱 Enter the FCM token from your phone")
        print("(You can find this in the app's dashboard - orange debug box)")
        token = input("Token: ").strip()
        
        if token:
            print("\n🔔 Sending notification directly...")
            success = await send_direct_notification(token)
            if success:
                print("\n✅ Notification sent! Check your phone!")
            else:
                print("\n❌ Failed to send notification")
                
    elif choice == "2":
        # Check tokens
        email = input("\n📧 Enter your Gmail address: ").strip()
        if email:
            await check_device_tokens(email)
            
    elif choice == "3":
        # Save and send
        email = input("\n📧 Enter your Gmail address: ").strip()
        token = input("📱 Enter FCM token: ").strip()
        
        if email and token:
            user_id = await check_device_tokens(email)
            if user_id:
                print("\n💾 Saving device token...")
                await save_device_token_direct(user_id, token)
                
                print("\n🔔 Sending notification...")
                success = await send_direct_notification(token)
                if success:
                    print("\n✅ Notification sent! Check your phone!")
                else:
                    print("\n❌ Failed to send notification")


if __name__ == "__main__":
    asyncio.run(main())