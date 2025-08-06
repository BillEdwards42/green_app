from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
from datetime import datetime, timedelta
from typing import Optional

from app.core.database import get_db
from app.models.user import User
from app.models.chore import Chore
from app.schemas.chore import ChoreLogRequest, ChoreLogResponse, ChoreHistoryResponse, ChoreHistoryItem
from app.api.v1.endpoints.users import get_current_user
from app.constants.appliances import APPLIANCE_POWER

router = APIRouter()


@router.post("/log", response_model=ChoreLogResponse)
async def log_chore(
    request: ChoreLogRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Log a new chore activity"""
    # Validate appliance type
    if request.appliance_type not in APPLIANCE_POWER:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid appliance type: {request.appliance_type}"
        )
    
    # Calculate end time based on start time and duration
    end_time = request.start_time + timedelta(minutes=request.duration_minutes)
    
    # Create new chore entry with only essential fields
    chore = Chore(
        user_id=current_user.id,
        appliance_type=request.appliance_type,
        start_time=request.start_time,
        duration_minutes=request.duration_minutes,
        end_time=end_time
    )
    
    db.add(chore)
    await db.commit()
    await db.refresh(chore)
    
    return ChoreLogResponse.from_orm(chore)



@router.get("/history", response_model=ChoreHistoryResponse)
async def get_chore_history(
    limit: Optional[int] = 50,
    offset: Optional[int] = 0,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get user's chore history"""
    # Get total count
    count_query = select(func.count()).select_from(Chore).where(Chore.user_id == current_user.id)
    total_count_result = await db.execute(count_query)
    total_count = total_count_result.scalar()
    
    # Get chores with pagination
    query = (
        select(Chore)
        .where(Chore.user_id == current_user.id)
        .order_by(Chore.start_time.desc())
        .limit(limit)
        .offset(offset)
    )
    result = await db.execute(query)
    chores = result.scalars().all()
    
    # Convert to response format
    chore_items = [
        ChoreHistoryItem(
            id=chore.id,
            appliance_type=chore.appliance_type,
            start_time=chore.start_time,
            duration_minutes=chore.duration_minutes,
            created_at=chore.created_at
        )
        for chore in chores
    ]
    
    return ChoreHistoryResponse(
        chores=chore_items,
        total_count=total_count
    )


@router.get("/monthly-summary")
async def get_monthly_summary(
    year: int,
    month: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get monthly summary of chores"""
    # Calculate start and end of month
    start_date = datetime(year, month, 1)
    if month == 12:
        end_date = datetime(year + 1, 1, 1)
    else:
        end_date = datetime(year, month + 1, 1)
    
    # Query chores for the month
    query = (
        select(Chore)
        .where(
            Chore.user_id == current_user.id,
            Chore.start_time >= start_date,
            Chore.start_time < end_date
        )
    )
    result = await db.execute(query)
    chores = result.scalars().all()
    
    # Calculate summary statistics
    chore_count = len(chores)
    
    # Group by appliance type
    appliance_stats = {}
    for chore in chores:
        if chore.appliance_type not in appliance_stats:
            appliance_stats[chore.appliance_type] = {
                "count": 0,
                "total_hours": 0
            }
        appliance_stats[chore.appliance_type]["count"] += 1
        appliance_stats[chore.appliance_type]["total_hours"] += chore.duration_hours
    
    return {
        "year": year,
        "month": month,
        "chore_count": chore_count,
        "appliance_stats": appliance_stats
    }