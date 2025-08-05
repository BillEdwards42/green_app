#!/usr/bin/env python3
"""
Fixed Notification Scheduler - Works around the enum issue
"""

import asyncio
import logging
import sys
from datetime import datetime, timedelta
from pathlib import Path
import json
from typing import List, Dict, Any

# Add parent directory to path
sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
import firebase_admin
from firebase_admin import credentials, messaging

from app.core.config import settings

# Initialize Firebase
if not firebase_admin._apps:
    firebase_path = Path(__file__).parent.parent / settings.FIREBASE_CREDENTIALS_PATH
    cred = credentials.Certificate(str(firebase_path))
    firebase_admin.initialize_app(cred)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/notification_scheduler.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Create async engine
engine = create_async_engine(settings.DATABASE_URL, echo=False)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


class NotificationScheduler:
    """Fixed version that bypasses ORM enum issues"""
    
    def __init__(self):
        self.current_time = datetime.now()
        self.current_hour = self.current_time.strftime("%H:%M")
        
    async def get_users_for_notification(self, db: AsyncSession) -> List[Dict[str, Any]]:
        """Get users who should receive notifications at current time"""
        
        # Calculate time window (current time ± 5 minutes)
        current_minutes = self.current_time.hour * 60 + self.current_time.minute
        
        # Use raw SQL to avoid ORM issues
        query = await db.execute(text("""
            SELECT u.id, u.username, u.email, ns.scheduled_time, ns.enabled, ns.daily_recommendation
            FROM users u
            JOIN notification_settings ns ON u.id = ns.user_id
            WHERE ns.enabled = true 
                AND ns.daily_recommendation = true
                AND u.deleted_at IS NULL
        """))
        
        users_to_notify = []
        
        for row in query:
            # Parse scheduled time
            try:
                scheduled_parts = row.scheduled_time.split(':')
                scheduled_hour = int(scheduled_parts[0])
                scheduled_minute = int(scheduled_parts[1]) if len(scheduled_parts) > 1 else 0
                scheduled_minutes = scheduled_hour * 60 + scheduled_minute
                
                # Check if within 10-minute window (for X0 minute schedule)
                if abs(current_minutes - scheduled_minutes) <= 5:
                    users_to_notify.append({
                        'user_id': row.id,
                        'username': row.username,
                        'scheduled_time': row.scheduled_time
                    })
                    logger.info(f"User {row.id} scheduled for notification at {row.scheduled_time}")
                    
            except Exception as e:
                logger.error(f"Error parsing scheduled time for user {row.id}: {e}")
                continue
        
        return users_to_notify
    
    async def get_optimal_hours(self, db: AsyncSession) -> List[int]:
        """Get optimal hours based on carbon intensity"""
        
        # Get carbon intensity data for next 24 hours
        next_24h = self.current_time + timedelta(hours=24)
        
        query = await db.execute(text("""
            SELECT timestamp, carbon_intensity, region
            FROM carbon_intensity
            WHERE timestamp >= :now AND timestamp <= :next_24h
            ORDER BY carbon_intensity
            LIMIT 6
        """), {"now": self.current_time, "next_24h": next_24h})
        
        carbon_data = query.fetchall()
        
        if not carbon_data:
            logger.warning("No carbon intensity data available for next 24 hours")
            return []
        
        # Get the hours with lowest intensity
        optimal_hours = [data.timestamp.hour for data in carbon_data]
        unique_hours = list(dict.fromkeys(optimal_hours))  # Remove duplicates while preserving order
        
        logger.info(f"Optimal hours: {unique_hours}")
        return unique_hours[:6]  # Return top 6 hours
    
    async def send_notification_to_user(self, user_id: int, message: str, data: Dict[str, Any]) -> bool:
        """Send notification to a specific user"""
        
        async with AsyncSessionLocal() as db:
            # Get user's active device tokens
            result = await db.execute(text("""
                SELECT token FROM device_tokens
                WHERE user_id = :user_id AND is_active = true
            """), {"user_id": user_id})
            
            tokens = result.fetchall()
            
            if not tokens:
                logger.warning(f"No active device tokens found for user {user_id}")
                return False
            
            success_count = 0
            
            for token_row in tokens:
                try:
                    fcm_message = messaging.Message(
                        notification=messaging.Notification(body=message),
                        data={k: str(v) for k, v in data.items()},  # Convert all values to strings
                        token=token_row.token
                    )
                    
                    response = messaging.send(fcm_message)
                    logger.info(f"Notification sent to user {user_id}: {response}")
                    success_count += 1
                    
                except Exception as e:
                    logger.error(f"Failed to send notification to user {user_id}: {e}")
            
            return success_count > 0
    
    async def get_recommendation_from_json(self) -> Dict[str, str]:
        """Get the recommended period from carbon_intensity.json"""
        try:
            json_path = Path(__file__).parent.parent / "data" / "carbon_intensity.json"
            with open(json_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            if 'recommendation' in data:
                return {
                    'start_time': data['recommendation'].get('start_time', ''),
                    'end_time': data['recommendation'].get('end_time', '')
                }
            return {}
        except Exception as e:
            logger.error(f"Error reading carbon_intensity.json: {e}")
            return {}
    
    async def generate_notification_message(self, optimal_hours: List[int]) -> str:
        """Generate personalized notification message"""
        
        # Get recommendation period from carbon_intensity.json
        recommendation = await self.get_recommendation_from_json()
        
        if recommendation and recommendation.get('start_time') and recommendation.get('end_time'):
            # Use the recommended period from JSON
            start_time = recommendation['start_time']
            end_time = recommendation['end_time']
            return f"今日減碳時刻為{start_time} ~ {end_time}，請善用該時段用電。"
        
        # Fallback to original logic if recommendation not found
        if not optimal_hours:
            return "查看今日最佳用電時段，減少碳排放！"
        
        # Format hours for display
        current_hour = self.current_time.hour
        upcoming_hours = [h for h in optimal_hours if h > current_hour]
        
        if not upcoming_hours:
            # All optimal hours have passed, show tomorrow's first optimal hour
            first_optimal = min(optimal_hours) if optimal_hours else 0
            return f"明日 {first_optimal}:00 是最佳用電時段，記得安排家電使用！"
        
        # Get next optimal hour
        next_optimal = min(upcoming_hours)
        
        # Check if current hour is optimal
        if current_hour in optimal_hours:
            return "現在是低碳時段！快來使用高耗能家電吧 💚"
        
        # Show next optimal time
        return f"下個低碳時段：{next_optimal}:00，準備好你的家電任務！"
    
    async def send_notifications(self, db: AsyncSession):
        """Main method to send scheduled notifications"""
        
        logger.info(f"Starting notification scheduler at {self.current_time}")
        
        # Get users scheduled for notification
        users_to_notify = await self.get_users_for_notification(db)
        
        if not users_to_notify:
            logger.info("No users scheduled for notifications at this time")
            return
        
        logger.info(f"Found {len(users_to_notify)} users to notify")
        
        # Get optimal hours
        optimal_hours = await self.get_optimal_hours(db)
        
        # Generate message
        message = await self.generate_notification_message(optimal_hours)
        
        # Send notifications
        success_count = 0
        for user in users_to_notify:
            data = {
                'type': 'daily_recommendation',
                'optimal_hours': json.dumps(optimal_hours),
                'current_hour': self.current_time.hour
            }
            
            if await self.send_notification_to_user(user['user_id'], message, data):
                success_count += 1
        
        logger.info(f"Notification scheduler completed. Sent {success_count}/{len(users_to_notify)} notifications")


async def main():
    """Main entry point for notification scheduler"""
    
    scheduler = NotificationScheduler()
    
    async with AsyncSessionLocal() as db:
        try:
            await scheduler.send_notifications(db)
        except Exception as e:
            logger.error(f"Error in notification scheduler: {e}")
            raise


if __name__ == "__main__":
    asyncio.run(main())