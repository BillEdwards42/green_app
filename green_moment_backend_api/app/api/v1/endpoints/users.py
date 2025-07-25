from fastapi import APIRouter, Depends, HTTPException, status, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.core.database import get_db
from app.models.user import User
from app.schemas.users import UsernameUpdateRequest, UsernameUpdateResponse, UserProfileResponse
from app.utils.jwt import verify_token
from app.utils.profanity import is_username_clean

router = APIRouter()


async def get_current_user(authorization: str = Header(None), db: AsyncSession = Depends(get_db)):
    """Get current user from JWT token"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authorization header"
        )
    
    token = authorization.replace("Bearer ", "")
    token_data = verify_token(token)
    
    if not token_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token"
        )
    
    result = await db.execute(
        select(User).where(User.id == token_data["user_id"])
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return user


@router.get("/profile", response_model=UserProfileResponse)
async def get_profile(current_user: User = Depends(get_current_user)):
    """Get user profile"""
    return UserProfileResponse(
        id=current_user.id,
        username=current_user.username,
        email=current_user.email,
        is_anonymous=current_user.is_anonymous,
        current_league=current_user.current_league,
        total_carbon_saved=current_user.total_carbon_saved,
        current_month_tasks_completed=current_user.current_month_tasks_completed
    )


@router.put("/username", response_model=UsernameUpdateResponse)
async def update_username(
    request: UsernameUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update username with profanity check"""
    # Validate username
    if not is_username_clean(request.username):
        return UsernameUpdateResponse(
            success=False,
            message="Username contains inappropriate content",
            username=current_user.username
        )
    
    # Update username
    current_user.username = request.username
    
    try:
        await db.commit()
        await db.refresh(current_user)
        
        return UsernameUpdateResponse(
            success=True,
            message="Username updated successfully",
            username=current_user.username
        )
    except IntegrityError:
        await db.rollback()
        return UsernameUpdateResponse(
            success=False,
            message="Username already exists",
            username=current_user.username
        )