from typing import List, Dict, Optional
from datetime import datetime
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.task import Task, UserTask
from app.models.monthly_summary import MonthlySummary


class LeagueService:
    """Service for handling league-related operations"""
    
    LEAGUE_HIERARCHY = ["bronze", "silver", "gold", "emerald", "diamond"]
    TASKS_PER_LEAGUE = 3  # Number of tasks required to advance
    
    @staticmethod
    def get_next_league(current_league: str) -> str:
        """Get the next league in progression"""
        try:
            current_index = LeagueService.LEAGUE_HIERARCHY.index(current_league)
            if current_index < len(LeagueService.LEAGUE_HIERARCHY) - 1:
                return LeagueService.LEAGUE_HIERARCHY[current_index + 1]
        except ValueError:
            pass
        return current_league
    
    async def get_user_tasks(self, db: AsyncSession, user_id: int, month: Optional[int] = None, year: Optional[int] = None) -> List[Dict]:
        """Get user's tasks for a specific month"""
        if month is None:
            month = datetime.now().month
        if year is None:
            year = datetime.now().year
        
        # Get the user to know their current league
        user_result = await db.execute(
            select(User).where(User.id == user_id)
        )
        user = user_result.scalar_one_or_none()
        if not user:
            return []
        
        # Get tasks for user's current league with completion status
        query = select(Task, UserTask).join(
            UserTask,
            and_(
                Task.id == UserTask.task_id,
                UserTask.user_id == user_id,
                UserTask.month == month,
                UserTask.year == year
            ),
            isouter=True
        ).where(
            and_(
                Task.is_active == True,
                Task.league == user.current_league  # Filter by user's league
            )
        )
        
        result = await db.execute(query)
        tasks_data = result.all()
        
        tasks = []
        for task, user_task in tasks_data:
            tasks.append({
                "id": task.id,
                "name": task.name,
                "description": task.description,
                "points": task.points,
                "completed": user_task.completed if user_task else False,
                "completed_at": user_task.completed_at if user_task else None
            })
        
        return tasks
    
    async def assign_monthly_tasks(self, db: AsyncSession, user_id: int) -> List[UserTask]:
        """Assign tasks to a user for the current month"""
        current_month = datetime.now().month
        current_year = datetime.now().year
        
        # Get the user to know their current league
        user_result = await db.execute(
            select(User).where(User.id == user_id)
        )
        user = user_result.scalar_one_or_none()
        if not user:
            return []
        
        # Get tasks for user's current league
        result = await db.execute(
            select(Task).where(
                and_(
                    Task.is_active == True,
                    Task.league == user.current_league
                )
            )
        )
        tasks = result.scalars().all()
        
        user_tasks = []
        for task in tasks:
            # Check if already assigned
            existing = await db.execute(
                select(UserTask).where(
                    and_(
                        UserTask.user_id == user_id,
                        UserTask.task_id == task.id,
                        UserTask.month == current_month,
                        UserTask.year == current_year
                    )
                )
            )
            if not existing.scalar_one_or_none():
                user_task = UserTask(
                    user_id=user_id,
                    task_id=task.id,
                    month=current_month,
                    year=current_year
                )
                db.add(user_task)
                user_tasks.append(user_task)
        
        if user_tasks:
            await db.commit()
        
        return user_tasks
    
    async def get_league_standings(self, db: AsyncSession, league: str) -> List[Dict]:
        """Get standings for users in a specific league"""
        result = await db.execute(
            select(User).where(
                and_(
                    User.current_league == league,
                    User.deleted_at.is_(None)
                )
            ).order_by(User.total_carbon_saved.desc())
        )
        users = result.scalars().all()
        
        standings = []
        for i, user in enumerate(users):
            standings.append({
                "rank": i + 1,
                "username": user.username,
                "total_carbon_saved": user.total_carbon_saved,
                "tasks_completed": user.current_month_tasks_completed
            })
        
        return standings
    
    async def get_user_monthly_summary(self, db: AsyncSession, user_id: int, month: int, year: int) -> Optional[MonthlySummary]:
        """Get user's monthly summary"""
        result = await db.execute(
            select(MonthlySummary).where(
                and_(
                    MonthlySummary.user_id == user_id,
                    MonthlySummary.month == month,
                    MonthlySummary.year == year
                )
            )
        )
        return result.scalar_one_or_none()