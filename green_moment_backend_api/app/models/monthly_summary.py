from sqlalchemy import Column, Integer, Float, DateTime, ForeignKey, String, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class MonthlySummary(Base):
    __tablename__ = "monthly_summaries"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    month = Column(Integer, nullable=False)  # Month (1-12)
    year = Column(Integer, nullable=False)  # Year
    
    # Carbon metrics
    total_carbon_saved = Column(Float, default=0.0, nullable=False)  # kg CO2 saved this month
    total_chores_logged = Column(Integer, default=0, nullable=False)  # Number of chores
    total_hours_shifted = Column(Float, default=0.0, nullable=False)  # Total hours of appliance usage
    
    # Gamification metrics
    tasks_completed = Column(Integer, default=0, nullable=False)  # Tasks completed this month
    total_points_earned = Column(Integer, default=0, nullable=False)  # Points earned this month
    league_at_month_start = Column(String, nullable=False)  # League at start of month
    league_at_month_end = Column(String, nullable=False)  # League at end of month
    league_upgraded = Column(Boolean, default=False, nullable=False)  # Whether user upgraded league
    
    # Most used appliances (JSON or separate table if needed)
    top_appliance = Column(String, nullable=True)  # Most used appliance this month
    top_appliance_usage_hours = Column(Float, default=0.0, nullable=False)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="monthly_summaries")