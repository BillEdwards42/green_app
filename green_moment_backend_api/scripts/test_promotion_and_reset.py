#!/usr/bin/env python3
"""
Test promotion script that:
1. Checks if user completed all tasks in their current league
2. Promotes if eligible
3. Resets tasks (removes old league tasks, assigns new ones)
4. Calculates last month's carbon saved from last chore
"""

import asyncio
import sys
import os
from datetime import datetime, timedelta
from sqlalchemy import select, and_, func, delete

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import AsyncSessionLocal
from app.models.user import User
from app.models.task import Task, UserTask
from app.models.chore import Chore
from app.models.monthly_summary import MonthlySummary
from app.constants.appliances import APPLIANCE_POWER


class PromotionTester:
    def __init__(self):
        self.league_progression = {
            "bronze": "silver",
            "silver": "gold",
            "gold": "emerald",
            "emerald": "diamond",
            "diamond": "diamond",  # Max level
        }
    
    async def check_user_promotion(self, username: str):
        """Check if user should be promoted and handle task reset"""
        async with AsyncSessionLocal() as db:
            # Get user
            result = await db.execute(
                select(User).where(User.username == username)
            )
            user = result.scalar_one_or_none()
            
            if not user:
                print(f"❌ User '{username}' not found!")
                return
            
            print(f"\n👤 User: {user.username}")
            print(f"📊 Current League: {user.current_league}")
            print(f"🌱 Total Carbon Saved: {user.total_carbon_saved:.2f} kg")
            
            # Get current month tasks for user's league
            current_month = datetime.now().month
            current_year = datetime.now().year
            
            # Get all user tasks for current month
            result = await db.execute(
                select(UserTask, Task).join(Task).where(
                    and_(
                        UserTask.user_id == user.id,
                        UserTask.month == current_month,
                        UserTask.year == current_year,
                        Task.league == user.current_league  # Only current league tasks
                    )
                )
            )
            user_tasks = result.all()
            
            print(f"\n📋 Current League Tasks ({user.current_league}):")
            completed_count = 0
            for user_task, task in user_tasks:
                status = "✅" if user_task.completed else "❌"
                print(f"  {status} {task.name} ({task.points} points)")
                if user_task.completed:
                    completed_count += 1
            
            total_tasks = len(user_tasks)
            print(f"\n📈 Progress: {completed_count}/{total_tasks} tasks completed")
            
            # Check if eligible for promotion
            promoted = False
            old_league = user.current_league
            if completed_count >= 3 and user.current_league != "diamond":
                # Promote!
                new_league = self.league_progression[user.current_league]
                user.current_league = new_league
                promoted = True
                print(f"\n🎉 PROMOTED to {new_league} league!")
            else:
                if user.current_league == "diamond":
                    print(f"\n💎 Already at maximum league (Diamond)")
                else:
                    print(f"\n📌 Not eligible for promotion ({3 - completed_count} more tasks needed)")
            
            # Calculate last month carbon saved from last chore
            result = await db.execute(
                select(Chore).where(
                    Chore.user_id == user.id
                ).order_by(Chore.start_time.desc()).limit(1)
            )
            last_chore = result.scalar_one_or_none()
            
            if last_chore:
                # Simple calculation using last chore
                appliance_kw = APPLIANCE_POWER.get(last_chore.appliance_type, 1.0)
                duration_hours = last_chore.duration_minutes / 60.0
                # Assume average savings of 0.1 kg CO2 per kWh
                carbon_saved = appliance_kw * duration_hours * 0.1
                
                print(f"\n🌿 Last Chore Carbon Calculation:")
                print(f"  Appliance: {last_chore.appliance_type}")
                print(f"  Duration: {last_chore.duration_minutes} minutes")
                print(f"  Carbon Saved: {carbon_saved:.3f} kg")
                
                # Update or create monthly summary
                last_month = datetime.now().month - 1 if datetime.now().month > 1 else 12
                last_year = datetime.now().year if datetime.now().month > 1 else datetime.now().year - 1
                
                result = await db.execute(
                    select(MonthlySummary).where(
                        and_(
                            MonthlySummary.user_id == user.id,
                            MonthlySummary.month == last_month,
                            MonthlySummary.year == last_year
                        )
                    )
                )
                summary = result.scalar_one_or_none()
                
                if not summary:
                    summary = MonthlySummary(
                        user_id=user.id,
                        month=last_month,
                        year=last_year,
                        total_carbon_saved=carbon_saved,
                        league_at_month_start=old_league,
                        league_at_month_end=user.current_league,
                        league_upgraded=promoted
                    )
                    db.add(summary)
                else:
                    summary.total_carbon_saved = carbon_saved
                    summary.league_upgraded = promoted
            
            # IMPORTANT: Clean up ALL old tasks before assigning new ones
            print(f"\n🧹 Cleaning up old tasks...")
            
            # Delete ALL user tasks for this user in current month
            await db.execute(
                delete(UserTask).where(
                    and_(
                        UserTask.user_id == user.id,
                        UserTask.month == current_month,
                        UserTask.year == current_year
                    )
                )
            )
            
            # Get tasks for user's (potentially new) league
            result = await db.execute(
                select(Task).where(
                    and_(
                        Task.league == user.current_league,
                        Task.is_active == True
                    )
                )
            )
            new_tasks = result.scalars().all()
            
            print(f"\n🆕 Assigning {user.current_league} league tasks:")
            for task in new_tasks:
                user_task = UserTask(
                    user_id=user.id,
                    task_id=task.id,
                    month=current_month,
                    year=current_year,
                    completed=False,
                    points_earned=0
                )
                db.add(user_task)
                print(f"  + {task.name} ({task.points} points)")
            
            # Reset monthly task counter
            user.current_month_tasks_completed = 0
            
            # Commit all changes
            await db.commit()
            
            print(f"\n✅ Task reset complete!")
            print(f"📊 Final League: {user.current_league}")
            
            return {
                "promoted": promoted,
                "old_league": old_league,
                "new_league": user.current_league,
                "tasks_completed": completed_count,
                "carbon_saved_last_chore": carbon_saved if last_chore else 0
            }


async def main():
    if len(sys.argv) < 2:
        print("Usage: python test_promotion_and_reset.py <username>")
        print("Example: python test_promotion_and_reset.py edwards_test1")
        sys.exit(1)
    
    username = sys.argv[1]
    tester = PromotionTester()
    
    print(f"🔄 Testing promotion for user: {username}")
    result = await tester.check_user_promotion(username)
    
    print("\n" + "="*50)
    print("📊 Summary:")
    print(f"  Promoted: {'Yes' if result['promoted'] else 'No'}")
    print(f"  League: {result['old_league']} → {result['new_league']}")
    print(f"  Tasks Completed: {result['tasks_completed']}")
    print(f"  Last Chore Carbon: {result['carbon_saved_last_chore']:.3f} kg")
    print("="*50)


if __name__ == "__main__":
    asyncio.run(main())