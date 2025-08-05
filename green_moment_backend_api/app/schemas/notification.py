from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional, Dict, Any
from enum import Enum


class PlatformType(str, Enum):
    android = "android"
    ios = "ios"


class DeviceTokenCreate(BaseModel):
    token: str
    platform: PlatformType
    device_id: str
    app_version: Optional[str] = None


class DeviceTokenResponse(BaseModel):
    id: str
    user_id: int  # Changed from str to int to match model
    platform: PlatformType
    device_id: str
    app_version: Optional[str]
    is_active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class NotificationSettingsUpdate(BaseModel):
    enabled: Optional[bool] = None
    scheduled_time: Optional[str] = Field(None, pattern="^([0-1]?[0-9]|2[0-3]):[0-5][0-9]$")  # HH:MM format
    daily_recommendation: Optional[bool] = None
    achievement_alerts: Optional[bool] = None
    weekly_summary: Optional[bool] = None


class NotificationSettingsResponse(BaseModel):
    id: str
    user_id: int  # Changed from str to int to match model
    enabled: bool
    scheduled_time: str
    daily_recommendation: bool
    achievement_alerts: bool
    weekly_summary: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class NotificationSend(BaseModel):
    user_id: str  # Keep as string for API compatibility
    title: Optional[str] = None
    body: str
    data: Optional[Dict[str, Any]] = None
    notification_type: str = "daily_recommendation"


class NotificationResponse(BaseModel):
    success: bool
    message: str
    notification_id: Optional[str] = None
    error: Optional[str] = None