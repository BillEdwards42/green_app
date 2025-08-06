from sqlalchemy import Column, String, Boolean, ForeignKey, DateTime, Text, Enum, Integer
from sqlalchemy.orm import relationship
from datetime import datetime
import enum

from app.core.database import Base


class PlatformType(str, enum.Enum):
    android = "android"  # Match database enum values
    ios = "ios"  # Match database enum values


class NotificationStatus(str, enum.Enum):
    PENDING = "pending"
    SENT = "sent"
    FAILED = "failed"
    DELIVERED = "delivered"


class DeviceToken(Base):
    """Store FCM device tokens for users"""
    __tablename__ = "device_tokens"
    
    id = Column(String, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    token = Column(Text, nullable=False, unique=True)
    platform = Column(Enum(PlatformType), nullable=False)
    device_id = Column(String, nullable=False)  # Unique device identifier
    app_version = Column(String)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    last_used_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="device_tokens")
    
    def __init__(self, **kwargs):
        if 'id' not in kwargs and 'user_id' in kwargs and 'device_id' in kwargs:
            # Convert user_id to string for composite ID
            kwargs['id'] = f"{kwargs['user_id']}_{kwargs['device_id']}"
        super().__init__(**kwargs)


class NotificationSettings(Base):
    """User notification preferences"""
    __tablename__ = "notification_settings"
    
    id = Column(String, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True)
    enabled = Column(Boolean, default=True)
    scheduled_time = Column(String, default="09:00")  # HH:MM format in user's timezone
    
    # Notification types
    daily_recommendation = Column(Boolean, default=True)
    achievement_alerts = Column(Boolean, default=True)
    weekly_summary = Column(Boolean, default=True)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="notification_settings")
    
    def __init__(self, **kwargs):
        if 'id' not in kwargs and 'user_id' in kwargs:
            # Convert user_id to string for ID
            kwargs['id'] = f"noti_settings_{kwargs['user_id']}"
        super().__init__(**kwargs)


class NotificationLog(Base):
    """Log of sent notifications"""
    __tablename__ = "notification_logs"
    
    id = Column(String, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    device_token_id = Column(String, ForeignKey("device_tokens.id", ondelete="SET NULL"), nullable=True)
    
    # Notification content
    title = Column(String)
    body = Column(Text, nullable=False)
    data = Column(Text)  # JSON string of additional data
    notification_type = Column(String, default="daily_recommendation")
    
    # Status tracking
    status = Column(Enum(NotificationStatus), default=NotificationStatus.PENDING)
    sent_at = Column(DateTime)
    delivered_at = Column(DateTime)
    error_message = Column(Text)
    
    # FCM response
    fcm_message_id = Column(String)
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="notification_logs")
    device_token = relationship("DeviceToken")
    
    def __init__(self, **kwargs):
        if 'id' not in kwargs:
            import uuid
            kwargs['id'] = f"noti_log_{uuid.uuid4().hex[:12]}"
        super().__init__(**kwargs)