#!/usr/bin/env python3
"""
Test notification after user logs in with new token
"""

import asyncio
import sys
from pathlib import Path

sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy import select
from app.core.database import AsyncSessionLocal
from app.models.user import User
from app.models.notification import DeviceToken
from app.services.notification_service import NotificationService
from datetime import datetime


async def test_notification(username: str):
    """Test sending notification to user"""
    async with AsyncSessionLocal() as db:
        # Get user
        result = await db.execute(
            select(User).where(User.username == username)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            print(f"❌ User '{username}' not found")
            return
            
        print(f"📊 User: {user.username} (ID: {user.id})")
        
        # Check device tokens
        result = await db.execute(
            select(DeviceToken).where(
                (DeviceToken.user_id == user.id) & 
                (DeviceToken.is_active == True)
            )
        )
        tokens = result.scalars().all()
        
        if not tokens:
            print("❌ No active device tokens found")
            print("👉 Please log in with the Flutter app first")
            return
            
        print(f"📱 Found {len(tokens)} active device token(s)")
        for token in tokens:
            print(f"   - Token: {token.token[:50]}...")
            print(f"   - Updated: {token.updated_at}")
        
        # Send test notification
        notification_service = NotificationService()
        
        try:
            success = await notification_service.send_notification(
                user_id=user.id,
                body=f"測試通知 🎉 時間：{datetime.now().strftime('%H:%M')}",
                notification_type="test"
            )
            
            if success:
                print("✅ Notification sent successfully!")
            else:
                print("❌ Failed to send notification")
                
        except Exception as e:
            print(f"❌ Error: {e}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python test_notification_after_login.py <username>")
        sys.exit(1)
        
    username = sys.argv[1]
    asyncio.run(test_notification(username))