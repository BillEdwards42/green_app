from sqlalchemy import Column, Integer, String, DateTime, Float, ForeignKey, Boolean
from sqlalchemy.sql import func
from sqlalchemy.orm import relationship
from app.core.database import Base


class Chore(Base):
    __tablename__ = "chores"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    appliance_type = Column(String, nullable=False)  # washing_machine, dryer, etc.
    start_time = Column(DateTime(timezone=True), nullable=False)
    end_time = Column(DateTime(timezone=True), nullable=False)
    duration_hours = Column(Float, nullable=False)  # Duration in hours
    power_consumption_watts = Column(Float, nullable=False)  # Appliance power consumption
    
    # Real-time calculation (shown to user immediately)
    estimated_carbon_saved = Column(Float, nullable=False)  # kg CO2 saved (real-time estimate)
    average_carbon_intensity = Column(Float, nullable=False)  # Average CI during chore period
    peak_carbon_intensity = Column(Float, nullable=False)  # Peak CI for comparison
    
    # Monthly recalculation (calculated on 1st of each month)
    actual_carbon_emitted = Column(Float, nullable=True)  # Actual emission using real CI data
    hypothetical_peak_emission = Column(Float, nullable=True)  # Emission if done at peak
    actual_carbon_saved = Column(Float, nullable=True)  # Actual savings (monthly calculation)
    monthly_calculated = Column(Boolean, default=False)  # Whether monthly calculation is done
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), onupdate=func.now())

    # Relationships
    user = relationship("User", back_populates="chores")