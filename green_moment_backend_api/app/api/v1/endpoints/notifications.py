from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, and_
from typing import List

from app.core.database import get_db
from app.api.dependencies import get_current_user
from app.models import User, DeviceToken, NotificationSettings
from app.schemas.notification import (
    DeviceTokenCreate,
    DeviceTokenResponse,
    NotificationSettingsUpdate,
    NotificationSettingsResponse,
)
from datetime import datetime

router = APIRouter()


@router.post("/device-token", response_model=DeviceTokenResponse)
async def register_device_token(
    token_data: DeviceTokenCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Register or update FCM device token for push notifications"""
    
    # Check if token already exists for another user
    existing_token = await db.execute(
        select(DeviceToken).where(
            and_(
                DeviceToken.token == token_data.token,
                DeviceToken.user_id != current_user.id
            )
        )
    )
    existing_token = existing_token.scalar_one_or_none()
    
    if existing_token:
        # Deactivate token for previous user
        existing_token.is_active = False
        db.add(existing_token)
    
    # Check if we already have a token for this user/device combination
    device_token = await db.execute(
        select(DeviceToken).where(
            and_(
                DeviceToken.user_id == current_user.id,
                DeviceToken.device_id == token_data.device_id
            )
        )
    )
    device_token = device_token.scalar_one_or_none()
    
    if device_token:
        # Update existing token
        device_token.token = token_data.token
        device_token.platform = token_data.platform
        device_token.app_version = token_data.app_version
        device_token.is_active = True
        device_token.updated_at = datetime.utcnow()
        device_token.last_used_at = datetime.utcnow()
    else:
        # Create new token record
        device_token = DeviceToken(
            user_id=current_user.id,
            token=token_data.token,
            platform=token_data.platform,
            device_id=token_data.device_id,
            app_version=token_data.app_version
        )
        db.add(device_token)
    
    await db.commit()
    await db.refresh(device_token)
    
    return device_token


@router.get("/settings", response_model=NotificationSettingsResponse)
async def get_notification_settings(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get user's notification settings"""
    
    settings = await db.execute(
        select(NotificationSettings).where(
            NotificationSettings.user_id == current_user.id
        )
    )
    settings = settings.scalar_one_or_none()
    
    if not settings:
        # Create default settings
        settings = NotificationSettings(
            user_id=current_user.id,
            enabled=True,
            scheduled_time="09:00",
            daily_recommendation=True,
            achievement_alerts=True,
            weekly_summary=True
        )
        db.add(settings)
        await db.commit()
        await db.refresh(settings)
    
    return settings


@router.put("/settings", response_model=NotificationSettingsResponse)
async def update_notification_settings(
    settings_update: NotificationSettingsUpdate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Update user's notification settings"""
    
    settings = await db.execute(
        select(NotificationSettings).where(
            NotificationSettings.user_id == current_user.id
        )
    )
    settings = settings.scalar_one_or_none()
    
    if not settings:
        # Create settings with updates
        settings = NotificationSettings(
            user_id=current_user.id
        )
        db.add(settings)
    
    # Update fields
    update_data = settings_update.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(settings, field, value)
    
    settings.updated_at = datetime.utcnow()
    
    await db.commit()
    await db.refresh(settings)
    
    return settings


@router.delete("/device-token")
async def remove_device_token(
    device_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Remove device token (e.g., on logout)"""
    
    device_token = await db.execute(
        select(DeviceToken).where(
            and_(
                DeviceToken.user_id == current_user.id,
                DeviceToken.device_id == device_id
            )
        )
    )
    device_token = device_token.scalar_one_or_none()
    
    if not device_token:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Device token not found"
        )
    
    # Soft delete by marking as inactive
    device_token.is_active = False
    device_token.updated_at = datetime.utcnow()
    
    await db.commit()
    
    return {"message": "Device token removed successfully"}


@router.get("/device-tokens", response_model=List[DeviceTokenResponse])
async def get_user_device_tokens(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    """Get all active device tokens for the current user"""
    
    tokens = await db.execute(
        select(DeviceToken).where(
            and_(
                DeviceToken.user_id == current_user.id,
                DeviceToken.is_active == True
            )
        ).order_by(DeviceToken.updated_at.desc())
    )
    tokens = tokens.scalars().all()
    
    return tokens