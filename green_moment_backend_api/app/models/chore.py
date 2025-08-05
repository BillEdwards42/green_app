from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class Chore(Base):
    __tablename__ = "chores"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    appliance_type = Column(String, nullable=False)  # washing_machine, dryer, etc.
    start_time = Column(DateTime(timezone=True), nullable=False)
    duration_minutes = Column(Integer, nullable=False)  # Duration in minutes
    end_time = Column(DateTime(timezone=True), nullable=False)  # Calculated from start_time + duration
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="chores")