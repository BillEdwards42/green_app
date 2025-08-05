from sqlalchemy import Column, Integer, String, Boolean, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class Task(Base):
    __tablename__ = "tasks"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, nullable=False)
    description = Column(String, nullable=False)
    points = Column(Integer, default=10, nullable=False)  # Points awarded for completion
    league = Column(String, nullable=False)  # bronze, silver, gold, emerald
    task_type = Column(String, nullable=False)  # firstAppOpen, carbonReduction, etc
    target_value = Column(Integer, nullable=True)  # For tasks with numeric targets
    is_active = Column(Boolean, default=True, nullable=False)  # Whether task is currently available
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user_tasks = relationship("UserTask", back_populates="task")


class UserTask(Base):
    __tablename__ = "user_tasks"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    task_id = Column(Integer, ForeignKey("tasks.id"), nullable=False)
    completed = Column(Boolean, default=False, nullable=False)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    month = Column(Integer, nullable=False)  # Month (1-12)
    year = Column(Integer, nullable=False)  # Year
    points_earned = Column(Integer, default=0, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="user_tasks")
    task = relationship("Task", back_populates="user_tasks")