from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db

router = APIRouter()


@router.get("/summary")
async def get_progress_summary(db: AsyncSession = Depends(get_db)):
    """Get user's progress summary"""
    # TODO: Implement progress summary
    return {"message": "Progress summary endpoint"}


@router.get("/tasks")
async def get_tasks(db: AsyncSession = Depends(get_db)):
    """Get current month's tasks"""
    # TODO: Implement tasks retrieval
    return {"message": "Tasks endpoint"}


@router.get("/league")
async def get_league_info(db: AsyncSession = Depends(get_db)):
    """Get user's league information"""
    # TODO: Implement league info
    return {"message": "League information endpoint"}