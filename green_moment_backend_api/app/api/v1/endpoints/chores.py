from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db

router = APIRouter()


@router.post("/log")
async def log_chore(db: AsyncSession = Depends(get_db)):
    """Log a new chore"""
    # TODO: Implement chore logging
    return {"message": "Chore logging endpoint"}


@router.post("/estimate")
async def estimate_savings(db: AsyncSession = Depends(get_db)):
    """Estimate carbon savings for a chore"""
    # TODO: Implement estimation
    return {"message": "Savings estimation endpoint"}


@router.get("/history")
async def get_chore_history(db: AsyncSession = Depends(get_db)):
    """Get user's chore history"""
    # TODO: Implement history retrieval
    return {"message": "Chore history endpoint"}