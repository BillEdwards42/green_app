from sqlalchemy import Column, Integer, Float, DateTime, String, Boolean, UniqueConstraint
from sqlalchemy.sql import func
from app.core.database import Base


class CarbonIntensity(Base):
    __tablename__ = "carbon_intensity"

    id = Column(Integer, primary_key=True, index=True)
    timestamp = Column(DateTime(timezone=True), nullable=False, index=True)
    region = Column(String, nullable=False, index=True)  # Central, East, Islands, North, South, Other
    carbon_intensity = Column(Float, nullable=False)  # gCO2/kWh
    is_forecast = Column(Boolean, default=False, nullable=False)  # True for forecast data, False for actual
    created_at = Column(DateTime(timezone=True), server_default=func.now())

    # Unique constraint on timestamp + region to prevent duplicates
    __table_args__ = (
        UniqueConstraint('timestamp', 'region', name='unique_timestamp_region'),
    )