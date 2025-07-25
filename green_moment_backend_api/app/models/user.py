from sqlalchemy import Column, Integer, String, DateTime, Boolean, Float
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=True)  # Null for anonymous users
    google_id = Column(String, unique=True, index=True, nullable=True)  # Null for anonymous users
    is_anonymous = Column(Boolean, default=False, nullable=False)
    current_league = Column(String, default="bronze", nullable=False)  # bronze, silver, gold, platinum, diamond
    total_carbon_saved = Column(Float, default=0.0, nullable=False)  # Total kg CO2 saved
    current_month_tasks_completed = Column(Integer, default=0, nullable=False)  # Tasks completed this month
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    chores = relationship("Chore", back_populates="user", cascade="all, delete-orphan")
    user_tasks = relationship("UserTask", back_populates="user", cascade="all, delete-orphan")
    monthly_summaries = relationship("MonthlySummary", back_populates="user", cascade="all, delete-orphan")