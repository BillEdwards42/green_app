from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from datetime import datetime

from app.core.database import get_db
from app.models.user import User
from app.schemas.users import UsernameUpdateRequest, UsernameUpdateResponse, UserProfileResponse
from app.api.dependencies import get_current_user
from app.utils.profanity import is_username_clean

router = APIRouter()


@router.get("/profile", response_model=UserProfileResponse)
async def get_profile(current_user: User = Depends(get_current_user)):
    """Get user profile"""
    return UserProfileResponse.from_orm(current_user)


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


@router.delete("/me", status_code=status.HTTP_204_NO_CONTENT)
async def delete_account(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Hard delete user account - complies with App Store and Google Play policies
    
    This will permanently delete:
    - User account
    - All chores (via CASCADE)
    - All user tasks (via CASCADE)
    - All monthly summaries (via CASCADE)
    """
    # Store user info for logging before deletion
    user_id = current_user.id
    username = current_user.username
    
    # Delete the user - CASCADE will handle related records
    await db.delete(current_user)
    await db.commit()
    
    # Log the deletion for audit purposes (consider implementing a separate audit log table)
    print(f"User account deleted: ID={user_id}, Username={username}, Timestamp={datetime.now()}")
    
    # Return 204 No Content
    return None