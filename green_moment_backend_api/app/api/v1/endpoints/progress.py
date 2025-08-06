from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from datetime import datetime
from typing import List

from app.core.database import get_db
from app.api.dependencies import get_current_user
from app.models.user import User
from app.models.monthly_summary import MonthlySummary
from app.models.daily_carbon_progress import DailyCarbonProgress
from app.services.league_service import LeagueService

router = APIRouter()


@router.get("/summary")
async def get_progress_summary(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get user's progress summary including carbon (CO2e) saved and league info"""
    # Get last month's summary
    last_month = datetime.now().month - 1 if datetime.now().month > 1 else 12
    last_year = datetime.now().year if datetime.now().month > 1 else datetime.now().year - 1
    
    result = await db.execute(
        select(MonthlySummary).where(
            and_(
                MonthlySummary.user_id == current_user.id,
                MonthlySummary.month == last_month,
                MonthlySummary.year == last_year
            )
        )
    )
    last_month_summary = result.scalar_one_or_none()
    
    # Also check current month for recent promotions (for testing or early month promotions)
    current_month_result = await db.execute(
        select(MonthlySummary).where(
            and_(
                MonthlySummary.user_id == current_user.id,
                MonthlySummary.month == datetime.now().month,
                MonthlySummary.year == datetime.now().year
            )
        )
    )
    current_month_summary = current_month_result.scalar_one_or_none()
    
    # Get current month tasks
    league_service = LeagueService()
    current_tasks = await league_service.get_user_tasks(db, current_user.id)
    
    return {
        "username": current_user.username,
        "current_league": current_user.current_league,
        "total_co2e_saved_g": current_user.total_carbon_saved,  # Now in grams
        "current_month_co2e_saved_g": current_user.current_month_carbon_saved,  # In grams
        "last_month_co2e_saved_g": last_month_summary.total_carbon_saved if last_month_summary else None,  # In grams
        "current_month_tasks": current_tasks,
        "tasks_completed_this_month": sum(1 for task in current_tasks if task["completed"]),
        "should_show_league_upgrade": (
            (current_month_summary.league_upgraded if current_month_summary else False) or
            (last_month_summary.league_upgraded if last_month_summary else False)
        )
    }


@router.get("/tasks")
async def get_tasks(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get current month's tasks"""
    league_service = LeagueService()
    tasks = await league_service.get_user_tasks(db, current_user.id)
    
    # Ensure user has tasks assigned
    if not tasks:
        await league_service.assign_monthly_tasks(db, current_user.id)
        tasks = await league_service.get_user_tasks(db, current_user.id)
    
    return {
        "tasks": tasks,
        "completed_count": sum(1 for task in tasks if task["completed"]),
        "total_count": len(tasks)
    }


@router.get("/daily-carbon")
async def get_daily_carbon(
    date: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get carbon saved for a specific date"""
    try:
        target_date = datetime.strptime(date, "%Y-%m-%d").date()
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD")
    
    result = await db.execute(
        select(DailyCarbonProgress).where(
            and_(
                DailyCarbonProgress.user_id == current_user.id,
                DailyCarbonProgress.date == target_date
            )
        )
    )
    daily_progress = result.scalar_one_or_none()
    
    if daily_progress:
        return {
            "date": target_date.isoformat(),
            "carbon_saved": daily_progress.daily_carbon_saved,
            "cumulative_carbon_saved": daily_progress.cumulative_carbon_saved
        }
    else:
        return {
            "date": target_date.isoformat(),
            "carbon_saved": 0.0,
            "cumulative_carbon_saved": 0.0
        }


@router.get("/league")
async def get_league_info(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get user's league information and standings"""
    league_service = LeagueService()
    standings = await league_service.get_league_standings(db, current_user.current_league)
    
    # Find user's rank
    user_rank = next((i + 1 for i, u in enumerate(standings) if u["username"] == current_user.username), None)
    
    return {
        "current_league": current_user.current_league,
        "next_league": league_service.get_next_league(current_user.current_league),
        "tasks_required": LeagueService.TASKS_PER_LEAGUE,
        "tasks_completed": current_user.current_month_tasks_completed,
        "user_rank": user_rank,
        "top_users": standings[:10]  # Top 10 users in the league
    }


@router.post("/mark-league-upgrade-shown")
async def mark_league_upgrade_shown(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Mark that the league upgrade animation has been shown"""
    # Check both current and last month for the upgrade flag
    summaries_to_check = []
    
    # Current month
    current_result = await db.execute(
        select(MonthlySummary).where(
            and_(
                MonthlySummary.user_id == current_user.id,
                MonthlySummary.month == datetime.now().month,
                MonthlySummary.year == datetime.now().year,
                MonthlySummary.league_upgraded == True
            )
        )
    )
    current_summary = current_result.scalar_one_or_none()
    if current_summary:
        summaries_to_check.append(current_summary)
    
    # Last month
    last_month = datetime.now().month - 1 if datetime.now().month > 1 else 12
    last_year = datetime.now().year if datetime.now().month > 1 else datetime.now().year - 1
    
    last_result = await db.execute(
        select(MonthlySummary).where(
            and_(
                MonthlySummary.user_id == current_user.id,
                MonthlySummary.month == last_month,
                MonthlySummary.year == last_year,
                MonthlySummary.league_upgraded == True
            )
        )
    )
    last_summary = last_result.scalar_one_or_none()
    if last_summary:
        summaries_to_check.append(last_summary)
    
    # Mark all as shown
    for summary in summaries_to_check:
        summary.league_upgraded = False
    
    if summaries_to_check:
        await db.commit()
    
    return {"success": True}