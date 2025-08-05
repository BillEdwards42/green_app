"""
Shared dependencies for API endpoints
"""
from fastapi import Depends, HTTPException, status, Header
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from app.core.database import get_db
from app.models.user import User
from app.utils.jwt import verify_token


async def get_current_user(
    authorization: str = Header(None), 
    db: AsyncSession = Depends(get_db)
) -> User:
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
        select(User).where(
            User.id == token_data["user_id"],
            User.deleted_at.is_(None)
        )
    )
    user = result.scalar_one_or_none()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    return user