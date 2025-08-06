#!/usr/bin/env python3
"""
League Promotion Scheduler
Runs daily at 5PM to check and process league promotions
For production: will run monthly on the 1st
"""

import asyncio
import schedule
import time
import csv
import sys
import os
from datetime import datetime, timedelta
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

# Add parent directory to path to import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import AsyncSessionLocal
from app.models.user import User
from app.models.task import Task, UserTask
from app.models.monthly_summary import MonthlySummary
from app.models.chore import Chore
from app.services.notification_service import NotificationService


class LeaguePromotionService:
    def __init__(self):
        self.notification_service = NotificationService()
        self.league_requirements = {
            "bronze": 3,    # 3 tasks to advance to silver
            "silver": 3,    # 3 tasks to advance to gold
            "gold": 3,      # 3 tasks to advance to emerald
            "emerald": 3,   # 3 tasks to advance to diamond
            "diamond": 3,   # Stay at diamond (max level)
        }
        self.league_progression = {
            "bronze": "silver",
            "silver": "gold",
            "gold": "emerald",
            "emerald": "diamond",
            "diamond": "diamond",  # Max level
        }

    async def calculate_monthly_carbon_savings(self, db: AsyncSession, user_id: int, month: int, year: int):
        """Calculate actual carbon savings for the user in the given month"""
        import csv
        from app.constants.appliances import APPLIANCE_POWER
        
        # Load actual carbon intensity historical data
        carbon_data = {}
        with open('logs/actual_carbon_intensity.csv', 'r') as f:
            reader = csv.DictReader(f)
            for row in reader:
                timestamp = datetime.fromisoformat(row['timestamp'])
                carbon_data[timestamp] = float(row['carbon_intensity_kgco2_kwh'])
        
        # Get all chores for the user in the specified month
        result = await db.execute(
            select(Chore).where(
                and_(
                    Chore.user_id == user_id,
                    # Extract month and year from start_time
                    func.extract('month', Chore.start_time) == month,
                    func.extract('year', Chore.start_time) == year
                )
            )
        )
        chores = result.scalars().all()
        
        total_carbon_saved = 0.0
        total_hours = 0.0
        appliance_usage = {}
        
        for chore in chores:
            # Get appliance power in kW
            appliance_kw = APPLIANCE_POWER.get(chore.appliance_type, 1.0)
            duration_hours = chore.duration_minutes / 60.0
            
            # Calculate actual carbon intensity for the chore period
            actual_carbon_intensity = self._calculate_period_carbon_intensity(
                carbon_data, chore.start_time, chore.end_time
            )
            
            # Calculate worst-case carbon intensity for the day
            worst_case_intensity = self._find_worst_continuous_period(
                carbon_data, chore.start_time.date(), chore.duration_minutes
            )
            
            # Carbon saved = (worst_case - actual) * kW * hours
            # Note: carbon intensity is already in kg CO2e/kWh
            carbon_saved = (worst_case_intensity - actual_carbon_intensity) * appliance_kw * duration_hours
            total_carbon_saved += max(0, carbon_saved)  # Only count positive savings
            total_hours += duration_hours
            
            # Track appliance usage
            if chore.appliance_type not in appliance_usage:
                appliance_usage[chore.appliance_type] = 0.0
            appliance_usage[chore.appliance_type] += duration_hours
        
        # Find most used appliance
        top_appliance = None
        top_hours = 0.0
        for appliance, hours in appliance_usage.items():
            if hours > top_hours:
                top_appliance = appliance
                top_hours = hours
        
        return {
            "total_carbon_saved": total_carbon_saved,  # Already in kg
            "total_chores_logged": len(chores),
            "total_hours_shifted": total_hours,
            "top_appliance": top_appliance,
            "top_appliance_usage_hours": top_hours
        }
    
    def _calculate_period_carbon_intensity(self, carbon_data, start_time, end_time):
        """Calculate average carbon intensity for a specific time period"""
        # Find all timestamps within the chore period
        relevant_intensities = []
        
        # Round start time down to nearest 10-minute interval
        current_time = start_time.replace(minute=(start_time.minute // 10) * 10, second=0, microsecond=0)
        
        while current_time <= end_time:
            # Look for exact match or closest timestamp
            if current_time in carbon_data:
                relevant_intensities.append(carbon_data[current_time])
            else:
                # Find closest timestamp
                closest_time = min(carbon_data.keys(), key=lambda x: abs(x - current_time))
                if abs(closest_time - current_time) < timedelta(hours=1):
                    relevant_intensities.append(carbon_data[closest_time])
            
            current_time += timedelta(minutes=10)
        
        # Calculate average
        if relevant_intensities:
            return sum(relevant_intensities) / len(relevant_intensities)
        else:
            # Default fallback if no data found
            return 0.500  # 500g CO2/kWh as kg
    
    def _find_worst_continuous_period(self, carbon_data, date, duration_minutes):
        """Find the worst continuous period of the day for the given duration"""
        # Filter data for the specific date
        day_data = {
            ts: intensity for ts, intensity in carbon_data.items()
            if ts.date() == date
        }
        
        if not day_data:
            return 0.600  # Default worst case if no data
        
        # Sort timestamps
        timestamps = sorted(day_data.keys())
        
        # Calculate number of 10-minute slots needed
        slots_needed = (duration_minutes + 9) // 10  # Round up
        
        worst_average = 0
        
        # Slide window across the day
        for i in range(len(timestamps) - slots_needed + 1):
            # Get intensities for this window
            window_intensities = []
            for j in range(slots_needed):
                if i + j < len(timestamps):
                    window_intensities.append(day_data[timestamps[i + j]])
            
            # Calculate average for this window
            if window_intensities:
                avg_intensity = sum(window_intensities) / len(window_intensities)
                worst_average = max(worst_average, avg_intensity)
        
        return worst_average if worst_average > 0 else 0.600

    async def check_and_promote_user(self, db: AsyncSession, user: User):
        """Check if user qualifies for promotion and process accordingly"""
        current_month = datetime.now().month
        current_year = datetime.now().year
        
        # For daily testing, we'll check current month's progress
        # In production, this would check the previous month
        if datetime.now().day == 1:
            # Production mode: check last month
            check_date = datetime.now() - timedelta(days=1)
            month = check_date.month
            year = check_date.year
        else:
            # Testing mode: check current month
            month = current_month
            year = current_year
        
        # Get user's tasks for the month
        result = await db.execute(
            select(UserTask).where(
                and_(
                    UserTask.user_id == user.id,
                    UserTask.month == month,
                    UserTask.year == year
                )
            )
        )
        user_tasks = result.scalars().all()
        
        # Calculate carbon savings
        carbon_data = await self.calculate_monthly_carbon_savings(db, user.id, month, year)
        
        # Check if user completed required tasks
        completed_tasks = sum(1 for task in user_tasks if task.completed)
        required_tasks = self.league_requirements.get(user.current_league, 3)
        
        # Determine if user gets promoted
        promoted = False
        new_league = user.current_league
        
        if completed_tasks >= required_tasks and user.current_league != "diamond":
            # User qualifies for promotion!
            promoted = True
            new_league = self.league_progression[user.current_league]
            user.current_league = new_league
        
        # Create or update monthly summary
        result = await db.execute(
            select(MonthlySummary).where(
                and_(
                    MonthlySummary.user_id == user.id,
                    MonthlySummary.month == month,
                    MonthlySummary.year == year
                )
            )
        )
        summary = result.scalar_one_or_none()
        
        if not summary:
            summary = MonthlySummary(
                user_id=user.id,
                month=month,
                year=year,
                league_at_month_start=user.current_league
            )
            db.add(summary)
        
        # Update summary
        summary.total_carbon_saved = carbon_data["total_carbon_saved"]
        summary.total_chores_logged = carbon_data["total_chores_logged"]
        summary.total_hours_shifted = carbon_data["total_hours_shifted"]
        summary.top_appliance = carbon_data["top_appliance"]
        summary.top_appliance_usage_hours = carbon_data["top_appliance_usage_hours"]
        summary.tasks_completed = completed_tasks
        summary.league_at_month_end = new_league
        summary.league_upgraded = promoted
        
        # Reset task counter for new month
        user.current_month_tasks_completed = 0
        
        # Update total carbon saved
        user.total_carbon_saved += carbon_data["total_carbon_saved"]
        
        await db.commit()
        
        # Send notification
        if promoted:
            await self._send_promotion_notification(user, new_league)
        else:
            await self._send_no_promotion_notification(user, completed_tasks, required_tasks)
        
        return {
            "user_id": user.id,
            "username": user.username,
            "promoted": promoted,
            "old_league": summary.league_at_month_start,
            "new_league": new_league,
            "tasks_completed": completed_tasks,
            "carbon_saved": carbon_data["total_carbon_saved"]
        }

    async def _send_promotion_notification(self, user: User, new_league: str):
        """Send promotion notification to user"""
        league_names = {
            "silver": "白銀",
            "gold": "黃金",
            "emerald": "翡翠",
            "diamond": "鑽石"
        }
        
        title = "🎉 聯盟晉級！"
        body = f"恭喜！您已晉級至{league_names.get(new_league, new_league)}聯盟！"
        
        try:
            # Notification service expects string user_id
            await self.notification_service.send_notification(
                user_id=str(user.id),
                title=title,
                body=body,
                data={"type": "league_promotion", "new_league": new_league}
            )
        except Exception as e:
            print(f"Failed to send promotion notification: {e}")

    async def _send_no_promotion_notification(self, user: User, completed: int, required: int):
        """Send notification when user doesn't get promoted"""
        title = "📊 月度總結"
        body = f"您完成了 {completed}/{required} 個任務。下個月繼續加油！"
        
        try:
            # Notification service expects string user_id
            await self.notification_service.send_notification(
                user_id=str(user.id),
                title=title,
                body=body,
                data={"type": "monthly_summary", "tasks_completed": str(completed)}
            )
        except Exception as e:
            print(f"Failed to send summary notification: {e}")

    async def reset_user_tasks(self, db: AsyncSession, user: User):
        """Reset tasks for the new month based on user's league"""
        current_month = datetime.now().month
        current_year = datetime.now().year
        
        # Get tasks for user's current league
        result = await db.execute(
            select(Task).where(
                and_(
                    Task.league == user.current_league,
                    Task.is_active == True
                )
            )
        )
        tasks = result.scalars().all()
        
        # Create new UserTask entries for the current month
        for task in tasks:
            # Check if task already exists for this month
            result = await db.execute(
                select(UserTask).where(
                    and_(
                        UserTask.user_id == user.id,
                        UserTask.task_id == task.id,
                        UserTask.month == current_month,
                        UserTask.year == current_year
                    )
                )
            )
            existing = result.scalar_one_or_none()
            
            if not existing:
                user_task = UserTask(
                    user_id=user.id,
                    task_id=task.id,
                    month=current_month,
                    year=current_year,
                    completed=False
                )
                db.add(user_task)
        
        await db.commit()

    async def process_all_users(self):
        """Process league promotions for all active users"""
        print(f"\n[{datetime.now()}] Starting league promotion check...")
        
        async with AsyncSessionLocal() as db:
            # Get all active users
            result = await db.execute(
                select(User).where(User.deleted_at.is_(None))
            )
            users = result.scalars().all()
            
            results = []
            for user in users:
                try:
                    # Process promotion check
                    result = await self.check_and_promote_user(db, user)
                    results.append(result)
                    
                    # Reset tasks for new month
                    await self.reset_user_tasks(db, user)
                    
                    print(f"✓ Processed {user.username}: {'Promoted!' if result['promoted'] else 'Not promoted'}")
                except Exception as e:
                    print(f"✗ Error processing user {user.username}: {e}")
            
            print(f"\n[{datetime.now()}] Completed processing {len(results)} users")
            promoted_count = sum(1 for r in results if r['promoted'])
            print(f"Promotions: {promoted_count}/{len(results)}")
            
            return results


async def run_promotion_check():
    """Run the promotion check"""
    service = LeaguePromotionService()
    await service.process_all_users()


def schedule_daily_check():
    """Schedule the promotion check to run daily at 5PM"""
    # For testing: run every minute
    # schedule.every(1).minutes.do(lambda: asyncio.run(run_promotion_check()))
    
    # For daily testing at 5PM
    schedule.every().day.at("17:00").do(lambda: asyncio.run(run_promotion_check()))
    
    print(f"[{datetime.now()}] League promotion scheduler started")
    print("Scheduled to run daily at 5:00 PM")
    print("Press Ctrl+C to stop\n")
    
    while True:
        schedule.run_pending()
        time.sleep(60)  # Check every minute


if __name__ == "__main__":
    import sys
    
    if "--test" in sys.argv:
        # Run immediately for testing
        print("Running promotion check immediately for testing...")
        asyncio.run(run_promotion_check())
    else:
        # Run on schedule
        try:
            schedule_daily_check()
        except KeyboardInterrupt:
            print("\n[{datetime.now()}] Scheduler stopped")