#!/usr/bin/env python3
"""
Check notification logs for a user
"""
import asyncio
import sys
import os
from datetime import datetime, timedelta

# Add parent directory to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from sqlalchemy import select, and_, desc
from app.core.database import AsyncSessionLocal
from app.models.user import User
from app.models.notification import NotificationLog, NotificationStatus


async def check_notification_logs(username: str):
    """Check notification logs for a user"""
    async with AsyncSessionLocal() as db:
        # Get user
        result = await db.execute(
            select(User).where(User.username == username)
        )
        user = result.scalar_one_or_none()
        
        if not user:
            print(f"❌ User '{username}' not found")
            return
            
        print(f"\n📊 User: {user.username} (ID: {user.id})")
        
        # Check notification logs from the last 7 days
        seven_days_ago = datetime.utcnow() - timedelta(days=7)
        
        result = await db.execute(
            select(NotificationLog)
            .where(
                and_(
                    NotificationLog.user_id == user.id,
                    NotificationLog.created_at >= seven_days_ago
                )
            )
            .order_by(desc(NotificationLog.created_at))
        )
        logs = result.scalars().all()
        
        print(f"\n📬 Notification Logs (last 7 days, {len(logs)} total):")
        
        if not logs:
            print("  - No notifications found in the last 7 days")
        else:
            for log in logs:
                print(f"\n  📝 Log ID: {log.id}")
                print(f"     Title: {log.title}")
                print(f"     Body: {log.body}")
                print(f"     Type: {log.notification_type}")
                print(f"     Status: {log.status}")
                print(f"     Created: {log.created_at}")
                print(f"     Sent: {log.sent_at}")
                print(f"     Delivered: {log.delivered_at}")
                if log.error_message:
                    print(f"     ❌ Error: {log.error_message}")
                if log.fcm_message_id:
                    print(f"     FCM ID: {log.fcm_message_id}")
                if log.device_token_id:
                    print(f"     Device Token ID: {log.device_token_id}")
        
        # Check today's logs specifically
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        
        result = await db.execute(
            select(NotificationLog)
            .where(
                and_(
                    NotificationLog.user_id == user.id,
                    NotificationLog.created_at >= today_start
                )
            )
        )
        today_logs = result.scalars().all()
        
        print(f"\n📅 Today's Notifications ({len(today_logs)} total)")
        
        # Summary
        if logs:
            sent_count = sum(1 for log in logs if log.status == NotificationStatus.SENT)
            delivered_count = sum(1 for log in logs if log.status == NotificationStatus.DELIVERED)
            failed_count = sum(1 for log in logs if log.status == NotificationStatus.FAILED)
            pending_count = sum(1 for log in logs if log.status == NotificationStatus.PENDING)
            
            print(f"\n📊 Summary (last 7 days):")
            print(f"  - Sent: {sent_count}")
            print(f"  - Delivered: {delivered_count}")
            print(f"  - Failed: {failed_count}")
            print(f"  - Pending: {pending_count}")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python check_notification_logs.py <username>")
        sys.exit(1)
        
    username = sys.argv[1]
    asyncio.run(check_notification_logs(username))