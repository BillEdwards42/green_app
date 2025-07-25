from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from app.core.database import get_db
from app.models.user import User
from app.schemas.auth import (
    GoogleAuthRequest, 
    AnonymousAuthRequest, 
    TokenResponse,
    TokenVerifyRequest,
    TokenVerifyResponse
)
from app.utils.jwt import create_access_token, verify_token
from app.utils.profanity import is_username_clean

router = APIRouter()


@router.post("/google", response_model=TokenResponse)
async def google_auth(request: GoogleAuthRequest, db: AsyncSession = Depends(get_db)):
    """Google OAuth authentication endpoint"""
    # TODO: Verify Google token with Google's API
    # For now, simulate Google auth with email extraction
    
    # Simulate getting email from Google token (make unique per request)
    import hashlib
    unique_id = hashlib.md5(f"{request.google_token}_{request.username or ''}".encode()).hexdigest()[:16]
    fake_email = f"user_{unique_id}@gmail.com"
    fake_google_id = f"google_{unique_id}"
    
    # Check if user exists
    result = await db.execute(
        select(User).where(User.google_id == fake_google_id)
    )
    user = result.scalar_one_or_none()
    
    print(f"🔍 Google auth - fake_google_id: {fake_google_id}")
    print(f"🔍 Google auth - existing user: {user}")
    print(f"🔍 Google auth - requested username: {request.username}")
    
    if not user:
        # Create new user with safe auto-generated username
        if request.username:
            username = request.username
            # Validate custom username
            if not is_username_clean(username):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="用戶名稱包含不當內容，請使用其他名稱"
                )
        else:
            # Generate a safe auto username
            base_username = f"User_{fake_google_id[:8]}"
            counter = 1
            username = base_username
            
            # Ensure auto-generated username is clean and unique
            while not is_username_clean(username):
                counter += 1
                username = f"GreenUser{counter:04d}"
                if counter > 9999:  # Safety break
                    username = f"EcoUser{fake_google_id[:6]}"
                    break
        
        user = User(
            username=username,
            email=fake_email,
            google_id=fake_google_id,
            is_anonymous=False
        )
        
        try:
            db.add(user)
            await db.commit()
            await db.refresh(user)
        except IntegrityError:
            await db.rollback()
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="用戶名稱已存在，請使用其他名稱"
            )
    
    # Create JWT token
    token_data = {
        "sub": user.id,
        "username": user.username,
        "is_anonymous": user.is_anonymous
    }
    access_token = create_access_token(token_data)
    
    return TokenResponse(
        access_token=access_token,
        user_id=user.id,
        username=user.username,
        is_anonymous=user.is_anonymous
    )


@router.post("/anonymous", response_model=TokenResponse)
async def anonymous_auth(request: AnonymousAuthRequest, db: AsyncSession = Depends(get_db)):
    """Create anonymous session"""
    # Basic validation
    if not request.username or len(request.username.strip()) == 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用戶名稱不能為空"
        )
    
    username = request.username.strip()
    
    # Validate username
    if not is_username_clean(username):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用戶名稱包含不當內容，請使用其他名稱"
        )
    
    # Check if username already exists
    existing_user = await db.execute(
        select(User).where(User.username == username)
    )
    if existing_user.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="用戶名稱已存在，請使用其他名稱"
        )
    
    # Create anonymous user
    user = User(
        username=username,
        is_anonymous=True
    )
    
    try:
        db.add(user)
        await db.commit()
        await db.refresh(user)
    except IntegrityError as e:
        await db.rollback()
        print(f"Database error: {e}")  # Debug logging
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="建立帳戶失敗，請稍後重試"
        )
    except Exception as e:
        await db.rollback()
        print(f"Unexpected error: {e}")  # Debug logging
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="服務器內部錯誤，請稍後重試"
        )
    
    # Create JWT token
    token_data = {
        "sub": user.id,
        "username": user.username,
        "is_anonymous": user.is_anonymous
    }
    access_token = create_access_token(token_data)
    
    return TokenResponse(
        access_token=access_token,
        user_id=user.id,
        username=user.username,
        is_anonymous=user.is_anonymous
    )


@router.post("/verify", response_model=TokenVerifyResponse)
async def verify_auth_token(request: TokenVerifyRequest):
    """Verify JWT token"""
    token_data = verify_token(request.token)
    
    if not token_data:
        return TokenVerifyResponse(valid=False)
    
    return TokenVerifyResponse(
        valid=True,
        user_id=token_data["user_id"],
        username=token_data["username"],
        is_anonymous=token_data["is_anonymous"]
    )