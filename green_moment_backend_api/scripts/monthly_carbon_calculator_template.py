#!/usr/bin/env python3
"""
Monthly Carbon Savings Calculator
Runs on the 1st of each month to calculate actual carbon savings from previous month
"""
import pandas as pd
import asyncio
from datetime import datetime, timedelta
from pathlib import Path
import logging
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker

# Add parent directory to path for imports
import sys
sys.path.append(str(Path(__file__).parent.parent))

from app.models.chore import Chore
from app.models.user import User
from app.models.monthly_summary import MonthlySummary
from app.constants.appliances import APPLIANCE_POWER
from app.core.config import settings

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('logs/monthly_calculation.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class MonthlyCarbonCalculator:
    def __init__(self):
        self.carbon_csv_path = Path("logs/actual_carbon_intensity.csv")
        self.engine = create_async_engine(settings.DATABASE_URL)
        self.AsyncSessionLocal = sessionmaker(
            self.engine, 
            class_=AsyncSession,
            expire_on_commit=False
        )
        
    async def calculate_monthly_savings(self):
        """Main function to calculate carbon savings for all users"""
        # Get previous month date range
        today = datetime.now()
        first_day_current = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        last_day_previous = first_day_current - timedelta(days=1)
        first_day_previous = last_day_previous.replace(day=1)
        
        logger.info(f"Calculating carbon savings for {last_day_previous.strftime('%B %Y')}")
        
        # Load carbon intensity data for the month
        carbon_data = self.load_carbon_data(first_day_previous, last_day_previous)
        
        async with self.AsyncSessionLocal() as session:
            # Get all users
            users = await session.execute(select(User))
            users = users.scalars().all()
            
            for user in users:
                await self.calculate_user_savings(
                    session, 
                    user, 
                    first_day_previous, 
                    last_day_previous,
                    carbon_data
                )
            
            await session.commit()
    
    def load_carbon_data(self, start_date, end_date):
        """Load carbon intensity data from CSV for the date range"""
        df = pd.read_csv(self.carbon_csv_path)
        df['timestamp'] = pd.to_datetime(df['timestamp'])
        
        # Filter for the month
        mask = (df['timestamp'] >= start_date) & (df['timestamp'] <= end_date)
        return df[mask].set_index('timestamp').sort_index()
    
    async def calculate_user_savings(self, session, user, start_date, end_date, carbon_data):
        """Calculate carbon savings for a single user"""
        # Get user's chores for the month
        chores_query = select(Chore).where(
            and_(
                Chore.user_id == user.id,
                Chore.start_time >= start_date,
                Chore.start_time <= end_date
            )
        )
        result = await session.execute(chores_query)
        chores = result.scalars().all()
        
        if not chores:
            logger.info(f"No chores found for user {user.username} in {start_date.strftime('%B %Y')}")
            return
        
        total_carbon_saved = 0
        total_hours_shifted = 0
        
        for chore in chores:
            # Calculate carbon saved for this chore
            carbon_saved = self.calculate_chore_carbon_saved(chore, carbon_data)
            total_carbon_saved += carbon_saved
            total_hours_shifted += chore.duration_minutes / 60
        
        # Update user's total carbon saved
        user.total_carbon_saved += total_carbon_saved
        
        # Create monthly summary
        summary = MonthlySummary(
            user_id=user.id,
            month=start_date.month,
            year=start_date.year,
            total_carbon_saved=total_carbon_saved,
            total_chores_logged=len(chores),
            total_hours_shifted=total_hours_shifted,
            league_at_month_start=user.current_league,
            league_at_month_end=user.current_league  # Will be updated by league calculator
        )
        
        session.add(summary)
        logger.info(f"User {user.username}: {total_carbon_saved:.2f} kg CO2 saved in {start_date.strftime('%B %Y')}")
    
    def calculate_chore_carbon_saved(self, chore, carbon_data):
        """Calculate carbon saved for a single chore"""
        # Get appliance power consumption
        appliance_kw = APPLIANCE_POWER.get(chore.appliance_type, 0)
        
        # Get actual carbon intensity during chore period
        chore_carbon = carbon_data[chore.start_time:chore.end_time]
        if chore_carbon.empty:
            logger.warning(f"No carbon data found for chore {chore.id}")
            return 0
        
        actual_intensity = chore_carbon['carbon_intensity_kgco2_kwh'].mean()
        
        # Find worst consecutive period of same duration on the same day
        day_start = chore.start_time.replace(hour=0, minute=0, second=0)
        day_end = chore.start_time.replace(hour=23, minute=59, second=59)
        day_carbon = carbon_data[day_start:day_end]
        
        worst_intensity = self.find_worst_period(
            day_carbon, 
            chore.duration_minutes
        )
        
        # Calculate carbon saved
        duration_hours = chore.duration_minutes / 60
        actual_emissions = duration_hours * actual_intensity * appliance_kw
        worst_emissions = duration_hours * worst_intensity * appliance_kw
        carbon_saved = worst_emissions - actual_emissions
        
        return max(0, carbon_saved)  # Ensure non-negative
    
    def find_worst_period(self, day_data, duration_minutes):
        """Find the worst consecutive period of given duration in the day"""
        if day_data.empty:
            return 0
            
        # Convert to 10-minute intervals if needed
        periods_needed = duration_minutes // 10
        
        worst_avg = 0
        for i in range(len(day_data) - periods_needed + 1):
            window = day_data.iloc[i:i + periods_needed]
            avg_intensity = window['carbon_intensity_kgco2_kwh'].mean()
            worst_avg = max(worst_avg, avg_intensity)
        
        return worst_avg


async def main():
    """Run the monthly calculation"""
    calculator = MonthlyCarbonCalculator()
    await calculator.calculate_monthly_savings()
    

if __name__ == "__main__":
    asyncio.run(main())