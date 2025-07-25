from sqlalchemy import Column, Integer, String, Float
from app.core.database import Base


class League(Base):
    __tablename__ = "leagues"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, unique=True, nullable=False, index=True)  # bronze, silver, gold, platinum, diamond
    min_carbon_saved = Column(Float, nullable=False)  # Minimum kg CO2 saved to reach this league
    max_carbon_saved = Column(Float, nullable=True)  # Maximum kg CO2 saved for this league (None for highest)
    display_name = Column(String, nullable=False)  # Display name in app
    color_hex = Column(String, nullable=False)  # Color for UI
    icon = Column(String, nullable=False)  # Icon identifier