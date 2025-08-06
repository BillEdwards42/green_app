from sqlalchemy import Column, Integer, String, DateTime, Boolean, Float, Date
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=True)  # Null for anonymous users
    google_id = Column(String, index=True, nullable=True)  # Not unique anymore, allows re-registration
    is_anonymous = Column(Boolean, default=False, nullable=False)
    current_league = Column(String, default="bronze", nullable=False)  # bronze, silver, gold, platinum, diamond
    total_carbon_saved = Column(Float, default=0.0, nullable=False)  # Total kg CO2e saved
    current_month_tasks_completed = Column(Integer, default=0, nullable=False)  # Tasks completed this month
    current_month_carbon_saved = Column(Float, default=0.0, nullable=False)  # Carbon (CO2e) saved this month
    last_carbon_calculation_date = Column(Date, nullable=True)  # Last date carbon was calculated
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())
    deleted_at = Column(DateTime(timezone=True), nullable=True)  # Soft delete timestamp

    # Relationships
    chores = relationship("Chore", back_populates="user", cascade="all, delete-orphan")
    user_tasks = relationship("UserTask", back_populates="user", cascade="all, delete-orphan")
    monthly_summaries = relationship("MonthlySummary", back_populates="user", cascade="all, delete-orphan")
    device_tokens = relationship("DeviceToken", back_populates="user", cascade="all, delete-orphan")
    notification_settings = relationship("NotificationSettings", back_populates="user", uselist=False, cascade="all, delete-orphan")
    notification_logs = relationship("NotificationLog", back_populates="user", cascade="all, delete-orphan")
    daily_carbon_progress = relationship("DailyCarbonProgress", back_populates="user", cascade="all, delete-orphan")