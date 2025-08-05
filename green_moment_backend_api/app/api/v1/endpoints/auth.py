from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from google.oauth2 import id_token
from google.auth.transport import requests
import os

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
from app.core.config import settings

router = APIRouter()


@router.post("/google", response_model=TokenResponse)
async def google_auth(request: GoogleAuthRequest, db: AsyncSession = Depends(get_db)):
    """Google OAuth authentication endpoint"""
    
    try:
        # Verify the Google ID token
        idinfo = id_token.verify_oauth2_token(
            request.google_token, 
            requests.Request(), 
            settings.GOOGLE_CLIENT_ID
        )
        
        # Extract user info from verified token
        google_id = idinfo['sub']  # Google user ID
        email = idinfo.get('email', '')
        
        print(f"🔍 Google auth - verified google_id: {google_id}")
        print(f"🔍 Google auth - email: {email}")
        
    except ValueError as e:
        # Invalid token
        print(f"❌ Google token verification failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="無效的 Google 認證令牌"
        )
    
    # Check if user exists (excluding soft deleted users)
    result = await db.execute(
        select(User).where(
            User.google_id == google_id,
            User.deleted_at.is_(None)
        )
    )
    user = result.scalar_one_or_none()
    
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
            # Generate a safe auto username from email
            email_prefix = email.split('@')[0] if email else f"user_{google_id[:8]}"
            base_username = email_prefix.replace('.', '_').replace('-', '_')
            counter = 1
            username = base_username
            
            # Ensure auto-generated username is unique
            while True:
                existing = await db.execute(
                    select(User).where(User.username == username)
                )
                if not existing.scalar_one_or_none():
                    break
                username = f"{base_username}{counter}"
                counter += 1
        
        user = User(
            username=username,
            email=email,
            google_id=google_id,
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
        "sub": str(user.id),  # JWT sub must be string
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
    
    # Check if username already exists (excluding soft deleted users)
    existing_user = await db.execute(
        select(User).where(
            User.username == username,
            User.deleted_at.is_(None)
        )
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
        "sub": str(user.id),  # JWT sub must be string
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
async def verify_auth_token(request: TokenVerifyRequest, db: AsyncSession = Depends(get_db)):
    """Verify JWT token"""
    print(f"🔐 Verifying token: {request.token[:20]}...")
    token_data = verify_token(request.token)
    
    if not token_data:
        print("❌ Token verification failed - invalid token")
        return TokenVerifyResponse(valid=False)
    
    # Check if user still exists and is not deleted
    result = await db.execute(
        select(User).where(
            User.id == token_data["user_id"],
            User.deleted_at.is_(None)
        )
    )
    user = result.scalar_one_or_none()
    
    if not user:
        print("❌ Token verification failed - user deleted or not found")
        return TokenVerifyResponse(valid=False)
    
    print(f"✅ Token verified for user: {token_data['username']} (ID: {token_data['user_id']})")
    return TokenVerifyResponse(
        valid=True,
        user_id=token_data["user_id"],
        username=token_data["username"],
        is_anonymous=token_data["is_anonymous"]
    )