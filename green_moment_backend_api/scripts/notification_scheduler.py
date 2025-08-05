#!/usr/bin/env python3
"""
Notification Scheduler - Runs every 10 minutes to send push notifications
Checks user scheduled times and sends notifications based on optimal carbon windows
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

from sqlalchemy import select, and_, or_, func
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

from app.core.config import settings
from app.models import User, NotificationSettings, CarbonIntensity
from app.services.notification_service import NotificationService

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
    """Handles scheduling and sending of push notifications"""
    
    def __init__(self):
        self.current_time = datetime.now()
        self.current_hour = self.current_time.strftime("%H:%M")
        
    async def get_users_for_notification(self, db: AsyncSession) -> List[Dict[str, Any]]:
        """Get users who should receive notifications at current time"""
        
        # Calculate time window (current time ± 5 minutes)
        time_format = "%H:%M"
        current_minutes = self.current_time.hour * 60 + self.current_time.minute
        
        # Get users with notification settings
        query = await db.execute(
            select(User, NotificationSettings).join(
                NotificationSettings,
                User.id == NotificationSettings.user_id
            ).where(
                and_(
                    NotificationSettings.enabled == True,
                    NotificationSettings.daily_recommendation == True,
                    User.deleted_at.is_(None)  # Exclude soft-deleted users
                )
            )
        )
        
        users_to_notify = []
        
        for user, settings in query:
            # Parse scheduled time
            try:
                scheduled_parts = settings.scheduled_time.split(':')
                scheduled_hour = int(scheduled_parts[0])
                scheduled_minute = int(scheduled_parts[1]) if len(scheduled_parts) > 1 else 0
                scheduled_minutes = scheduled_hour * 60 + scheduled_minute
                
                # Check if within 10-minute window (for X0 minute schedule)
                if abs(current_minutes - scheduled_minutes) <= 5:
                    users_to_notify.append({
                        'user': user,
                        'settings': settings
                    })
                    logger.info(f"User {user.id} scheduled for notification at {settings.scheduled_time}")
                    
            except Exception as e:
                logger.error(f"Error parsing scheduled time for user {user.id}: {e}")
                continue
        
        return users_to_notify
    
    async def get_optimal_hours(self, db: AsyncSession) -> Dict[str, List[int]]:
        """Get optimal hours for the next 24 hours based on carbon intensity"""
        
        # Get carbon intensity data for next 24 hours
        next_24h = self.current_time + timedelta(hours=24)
        
        query = await db.execute(
            select(CarbonIntensity).where(
                and_(
                    CarbonIntensity.timestamp >= self.current_time,
                    CarbonIntensity.timestamp <= next_24h
                )
            ).order_by(CarbonIntensity.timestamp)
        )
        
        carbon_data = query.scalars().all()
        
        if not carbon_data:
            logger.warning("No carbon intensity data available for next 24 hours")
            return {}
        
        # Group by region and find lowest intensity hours
        region_data = {}
        
        for data in carbon_data:
            if data.region not in region_data:
                region_data[data.region] = []
            
            region_data[data.region].append({
                'hour': data.timestamp.hour,
                'intensity': data.carbon_intensity,
                'timestamp': data.timestamp
            })
        
        # Find optimal hours for each region (lowest 6 hours)
        optimal_hours = {}
        
        for region, hours in region_data.items():
            # Sort by intensity
            sorted_hours = sorted(hours, key=lambda x: x['intensity'])
            
            # Get top 6 hours
            optimal = sorted_hours[:6]
            optimal_hours[region] = [h['hour'] for h in optimal]
            
            logger.info(f"Optimal hours for {region}: {optimal_hours[region]}")
        
        return optimal_hours
    
    async def generate_notification_message(self, user: User, optimal_hours: List[int]) -> str:
        """Generate personalized notification message"""
        
        if not optimal_hours:
            return "查看今日最佳用電時段，減少碳排放！"
        
        # Format hours for display
        current_hour = self.current_time.hour
        upcoming_hours = [h for h in optimal_hours if h > current_hour]
        
        if not upcoming_hours:
            # All optimal hours have passed, show tomorrow's first optimal hour
            first_optimal = min(optimal_hours)
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
        
        # Get optimal hours by region
        optimal_hours = await self.get_optimal_hours(db)
        
        # Prepare notifications
        notifications = []
        
        for user_data in users_to_notify:
            user = user_data['user']
            
            # Get user's region (default to 'North' if not set)
            # TODO: Add region to user model or determine from location
            user_region = 'North'
            
            # Get optimal hours for user's region
            region_optimal_hours = optimal_hours.get(user_region, [])
            
            # Generate message
            message = await self.generate_notification_message(user, region_optimal_hours)
            
            notifications.append({
                'user_id': str(user.id),
                'body': message,
                'data': {
                    'type': 'daily_recommendation',
                    'optimal_hours': json.dumps(region_optimal_hours),
                    'current_hour': self.current_time.hour
                }
            })
        
        # Send batch notifications
        if notifications:
            result = await NotificationService.send_batch_notifications(notifications, db)
            logger.info(f"Notification send result: {result}")
        
        logger.info("Notification scheduler completed")
    
    async def cleanup_tokens(self, db: AsyncSession):
        """Cleanup invalid tokens (run less frequently)"""
        
        # Only run cleanup once per day at midnight
        if self.current_time.hour == 0 and self.current_time.minute < 10:
            logger.info("Running token cleanup")
            invalid_count = await NotificationService.cleanup_invalid_tokens(db)
            logger.info(f"Cleaned up {invalid_count} invalid tokens")


async def main():
    """Main entry point for notification scheduler"""
    
    scheduler = NotificationScheduler()
    
    async with AsyncSessionLocal() as db:
        try:
            # Send notifications
            await scheduler.send_notifications(db)
            
            # Cleanup tokens if needed
            await scheduler.cleanup_tokens(db)
            
        except Exception as e:
            logger.error(f"Error in notification scheduler: {e}")
            raise


if __name__ == "__main__":
    asyncio.run(main())