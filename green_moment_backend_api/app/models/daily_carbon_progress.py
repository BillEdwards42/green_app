from sqlalchemy import Column, Integer, Float, Date, DateTime, ForeignKey
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class DailyCarbonProgress(Base):
    __tablename__ = "daily_carbon_progress"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    date = Column(Date, nullable=False, index=True)
    daily_carbon_saved = Column(Float, default=0.0, nullable=False)
    cumulative_carbon_saved = Column(Float, default=0.0, nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Relationships
    user = relationship("User", back_populates="daily_carbon_progress")