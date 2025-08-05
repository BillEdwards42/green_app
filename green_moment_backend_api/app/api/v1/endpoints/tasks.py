from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_, update
from datetime import datetime
from typing import List

from app.core.database import get_db
from app.api.dependencies import get_current_user
from app.models.user import User
from app.models.task import Task, UserTask
from app.schemas.task import TaskComplete, TaskResponse, UserTaskResponse

router = APIRouter()


@router.get("/", response_model=List[TaskResponse])
async def get_all_tasks(
    db: AsyncSession = Depends(get_db)
):
    """Get all available tasks"""
    result = await db.execute(
        select(Task).where(Task.is_active == True).order_by(Task.id)
    )
    tasks = result.scalars().all()
    return tasks


@router.get("/my-tasks", response_model=List[UserTaskResponse])
async def get_my_tasks(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get current user's tasks for the current month"""
    current_month = datetime.now().month
    current_year = datetime.now().year
    
    # First ensure user has tasks assigned for this month
    await ensure_user_has_monthly_tasks(db, current_user.id, current_month, current_year)
    
    # Get user tasks with task details
    result = await db.execute(
        select(UserTask, Task).join(Task).where(
            and_(
                UserTask.user_id == current_user.id,
                UserTask.month == current_month,
                UserTask.year == current_year
            )
        ).order_by(Task.id)
    )
    
    user_tasks = []
    for user_task, task in result:
        user_tasks.append({
            "id": user_task.id,
            "task_id": task.id,
            "name": task.name,
            "description": task.description,
            "points": task.points,
            "task_type": task.task_type,  # Add this field!
            "target_value": task.target_value,  # Add this field too!
            "completed": user_task.completed,
            "completed_at": user_task.completed_at,
            "points_earned": user_task.points_earned
        })
    
    return user_tasks


@router.post("/complete/{task_id}")
async def complete_task(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Mark a task as completed"""
    current_month = datetime.now().month
    current_year = datetime.now().year
    
    # Get the user task
    result = await db.execute(
        select(UserTask, Task).join(Task).where(
            and_(
                UserTask.user_id == current_user.id,
                UserTask.task_id == task_id,
                UserTask.month == current_month,
                UserTask.year == current_year
            )
        )
    )
    user_task_data = result.first()
    
    if not user_task_data:
        raise HTTPException(status_code=404, detail="Task not found for current month")
    
    user_task, task = user_task_data
    
    if user_task.completed:
        raise HTTPException(status_code=400, detail="Task already completed")
    
    # Mark as completed
    user_task.completed = True
    user_task.completed_at = datetime.utcnow()
    user_task.points_earned = task.points
    
    # Update user's monthly task counter
    current_user.current_month_tasks_completed += 1
    
    await db.commit()
    
    return {
        "message": "Task completed successfully",
        "points_earned": task.points,
        "total_tasks_completed": current_user.current_month_tasks_completed
    }


@router.post("/uncomplete/{task_id}")
async def uncomplete_task(
    task_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Mark a task as not completed (for testing purposes)"""
    current_month = datetime.now().month
    current_year = datetime.now().year
    
    # Get the user task
    result = await db.execute(
        select(UserTask).where(
            and_(
                UserTask.user_id == current_user.id,
                UserTask.task_id == task_id,
                UserTask.month == current_month,
                UserTask.year == current_year
            )
        )
    )
    user_task = result.scalar_one_or_none()
    
    if not user_task:
        raise HTTPException(status_code=404, detail="Task not found for current month")
    
    if not user_task.completed:
        raise HTTPException(status_code=400, detail="Task is not completed")
    
    # Mark as not completed
    user_task.completed = False
    user_task.completed_at = None
    user_task.points_earned = 0
    
    # Update user's monthly task counter
    current_user.current_month_tasks_completed = max(0, current_user.current_month_tasks_completed - 1)
    
    await db.commit()
    
    return {
        "message": "Task marked as incomplete",
        "total_tasks_completed": current_user.current_month_tasks_completed
    }


async def ensure_user_has_monthly_tasks(
    db: AsyncSession, 
    user_id: int, 
    month: int, 
    year: int
):
    """Ensure user has tasks assigned for the given month based on their league"""
    # Check if user already has tasks for this month
    result = await db.execute(
        select(UserTask).where(
            and_(
                UserTask.user_id == user_id,
                UserTask.month == month,
                UserTask.year == year
            )
        ).limit(1)
    )
    
    if result.scalar_one_or_none():
        return  # User already has tasks
    
    # Get the user to know their league
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    
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
    
    if not tasks:
        raise HTTPException(
            status_code=500, 
            detail=f"No tasks available for {user.current_league} league. Please run seed_league_tasks.py script."
        )
    
    # Create UserTask entries for this month
    for task in tasks:
        user_task = UserTask(
            user_id=user_id,
            task_id=task.id,
            month=month,
            year=year,
            completed=False,
            points_earned=0
        )
        db.add(user_task)
    
    await db.commit()