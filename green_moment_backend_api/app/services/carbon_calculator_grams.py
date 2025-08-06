"""
Daily Carbon Calculator Service (Grams version)
Calculates daily carbon (CO2e) savings for users based on their chores
All values in grams CO2e
"""

import csv
from datetime import datetime, timedelta, date
from typing import Dict, List, Optional, Tuple
from sqlalchemy import select, and_, func
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.models.chore import Chore
from app.models.daily_carbon_progress import DailyCarbonProgress
from app.constants.appliances import APPLIANCE_POWER


class DailyCarbonCalculator:
    """Service for calculating daily carbon savings in grams CO2e"""
    
    def __init__(self):
        self.carbon_data_cache: Dict[datetime, float] = {}
        self._load_carbon_data()
    
    def _load_carbon_data(self):
        """Load historical carbon intensity data from CSV"""
        try:
            with open('logs/actual_carbon_intensity.csv', 'r') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    timestamp = datetime.fromisoformat(row['timestamp'])
                    # Handle both g/kWh and kg/kWh formats
                    if 'carbon_intensity_gco2e_kwh' in row:
                        self.carbon_data_cache[timestamp] = float(row['carbon_intensity_gco2e_kwh'])
                    elif 'carbon_intensity_kgco2e_kwh' in row:
                        # Convert kg to g
                        self.carbon_data_cache[timestamp] = float(row['carbon_intensity_kgco2e_kwh']) * 1000
                    else:
                        # Old format - convert kg to g
                        self.carbon_data_cache[timestamp] = float(row['carbon_intensity_kgco2_kwh']) * 1000
        except FileNotFoundError:
            print("Warning: actual_carbon_intensity.csv not found. Using default values.")
    
    async def calculate_daily_carbon_for_all_users(
        self, 
        db: AsyncSession, 
        target_date: Optional[date] = None
    ):
        """Calculate carbon savings for all users for a specific date"""
        if target_date is None:
            # Default to yesterday
            target_date = date.today() - timedelta(days=1)
        
        # Get all active users
        result = await db.execute(
            select(User).where(User.deleted_at.is_(None))
        )
        users = result.scalars().all()
        
        print(f"\n🌱 Calculating carbon (CO2e) savings for {target_date}")
        print(f"Processing {len(users)} users...")
        
        for user in users:
            try:
                await self.calculate_user_daily_carbon(db, user, target_date)
            except Exception as e:
                print(f"❌ Error processing user {user.username}: {e}")
        
        await db.commit()
        print("✅ Daily carbon (CO2e) calculation completed")
    
    async def calculate_user_daily_carbon(
        self, 
        db: AsyncSession, 
        user: User, 
        target_date: date
    ) -> float:
        """Calculate carbon (CO2e) savings for a specific user on a specific date"""
        print(f"\n{'='*60}")
        print(f"🧮 Calculating daily carbon for user: {user.username}")
        print(f"📅 Date: {target_date}")
        print(f"{'='*60}")
        
        # Get chores for the target date
        start_datetime = datetime.combine(target_date, datetime.min.time())
        end_datetime = datetime.combine(target_date, datetime.max.time())
        
        result = await db.execute(
            select(Chore).where(
                and_(
                    Chore.user_id == user.id,
                    Chore.start_time >= start_datetime,
                    Chore.start_time <= end_datetime
                )
            )
        )
        chores = result.scalars().all()
        
        if not chores:
            print("📋 No chores found for this date")
            return 0.0
        
        print(f"📋 Found {len(chores)} chores for this date\n")
        
        daily_carbon_saved = 0.0
        
        for i, chore in enumerate(chores, 1):
            print(f"Chore {i}/{len(chores)}:")
            carbon_saved = self._calculate_chore_carbon_saved(chore)
            daily_carbon_saved += carbon_saved
        
        # Calculate cumulative total
        if target_date.day == 1:
            # First day of month - cumulative equals daily
            cumulative_total = daily_carbon_saved
        else:
            # Get previous day's cumulative total
            previous_date = target_date - timedelta(days=1)
            result = await db.execute(
                select(DailyCarbonProgress).where(
                    and_(
                        DailyCarbonProgress.user_id == user.id,
                        DailyCarbonProgress.date == previous_date
                    )
                )
            )
            previous_progress = result.scalar_one_or_none()
            
            if previous_progress:
                # Check if we're in a new month
                if previous_date.month != target_date.month:
                    # New month started - reset cumulative
                    cumulative_total = daily_carbon_saved
                else:
                    # Same month - add to previous cumulative
                    cumulative_total = previous_progress.cumulative_carbon_saved + daily_carbon_saved
            else:
                # No previous entry - calculate from month start
                cumulative_total = await self._calculate_month_to_date(db, user, target_date)
        
        # Check if entry already exists
        result = await db.execute(
            select(DailyCarbonProgress).where(
                and_(
                    DailyCarbonProgress.user_id == user.id,
                    DailyCarbonProgress.date == target_date
                )
            )
        )
        existing_progress = result.scalar_one_or_none()
        
        if existing_progress:
            # Update existing entry
            existing_progress.daily_carbon_saved = daily_carbon_saved
            existing_progress.cumulative_carbon_saved = cumulative_total
        else:
            # Create new entry
            progress = DailyCarbonProgress(
                user_id=user.id,
                date=target_date,
                daily_carbon_saved=daily_carbon_saved,
                cumulative_carbon_saved=cumulative_total
            )
            db.add(progress)
        
        # Update user's current month total
        # If we're calculating for a date in the current month, update the user's total
        if target_date.month == date.today().month and target_date.year == date.today().year:
            user.current_month_carbon_saved = cumulative_total
        # If we're calculating for the first day of a new month, reset the user's total
        elif target_date.day == 1 and target_date > user.last_carbon_calculation_date:
            user.current_month_carbon_saved = daily_carbon_saved
        
        # Always update the last calculation date
        user.last_carbon_calculation_date = target_date
        
        print(f"\n📊 Daily Summary for {user.username}:")
        print(f"   - Daily carbon saved: {daily_carbon_saved:.1f}g CO2e")
        print(f"   - Cumulative for month: {cumulative_total:.1f}g CO2e")
        print(f"   - Updated current_month_carbon_saved: {user.current_month_carbon_saved:.1f}g")
        print(f"{'='*60}\n")
        
        return daily_carbon_saved
    
    def _calculate_chore_carbon_saved(self, chore: Chore) -> float:
        """Calculate carbon (CO2e) saved for a single chore in grams"""
        # Get appliance power in kW
        appliance_kw = APPLIANCE_POWER.get(chore.appliance_type, 1.0)
        duration_hours = chore.duration_minutes / 60.0
        
        # Calculate actual carbon intensity for the chore period (in g/kWh)
        actual_carbon_intensity = self._calculate_period_carbon_intensity(
            chore.start_time, chore.end_time
        )
        
        # Calculate worst-case carbon intensity for the day (in g/kWh)
        worst_case_intensity = self._find_worst_continuous_period(
            chore.start_time.date(), chore.duration_minutes
        )
        
        # Carbon (CO2e) saved in grams = (worst_case - actual) * kW * hours
        carbon_saved_g = (worst_case_intensity - actual_carbon_intensity) * appliance_kw * duration_hours
        
        # Log detailed calculation
        print(f"""
📊 Chore Carbon Calculation:
   - Chore ID: {chore.id}
   - User: {chore.user_id}
   - Appliance: {chore.appliance_type} ({appliance_kw} kW)
   - Start: {chore.start_time.strftime('%Y-%m-%d %H:%M')}
   - End: {chore.end_time.strftime('%Y-%m-%d %H:%M')}
   - Duration: {chore.duration_minutes} minutes ({duration_hours:.2f} hours)
   
   Intensity Calculation:
   - Actual avg intensity: {actual_carbon_intensity:.3f} g CO2e/kWh
   - Worst avg intensity: {worst_case_intensity:.3f} g CO2e/kWh
   
   Emission Calculation:
   - Actual emission: {actual_carbon_intensity:.3f} × {appliance_kw} × {duration_hours:.2f} = {actual_carbon_intensity * appliance_kw * duration_hours:.1f}g
   - Worst emission: {worst_case_intensity:.3f} × {appliance_kw} × {duration_hours:.2f} = {worst_case_intensity * appliance_kw * duration_hours:.1f}g
   - Carbon saved: {worst_case_intensity * appliance_kw * duration_hours:.1f} - {actual_carbon_intensity * appliance_kw * duration_hours:.1f} = {carbon_saved_g:.1f}g CO2e
        """)
        
        return max(0, carbon_saved_g)  # Only count positive savings
    
    def _calculate_period_carbon_intensity(self, start_time: datetime, end_time: datetime) -> float:
        """Calculate average carbon intensity for a specific time period in g/kWh"""
        # Ensure timezone-naive for comparison
        if start_time.tzinfo is not None:
            start_time = start_time.replace(tzinfo=None)
        if end_time.tzinfo is not None:
            end_time = end_time.replace(tzinfo=None)
        
        relevant_intensities = []
        
        # Round start time down to nearest 10-minute interval
        current_time = start_time.replace(minute=(start_time.minute // 10) * 10, second=0, microsecond=0)
        
        while current_time <= end_time:
            if current_time in self.carbon_data_cache:
                relevant_intensities.append(self.carbon_data_cache[current_time])
            else:
                # Find closest timestamp
                closest_intensity = self._find_closest_intensity(current_time)
                if closest_intensity is not None:
                    relevant_intensities.append(closest_intensity)
            
            current_time += timedelta(minutes=10)
        
        if relevant_intensities:
            return sum(relevant_intensities) / len(relevant_intensities)
        else:
            return 500.0  # Default 500g CO2e/kWh
    
    def _find_closest_intensity(self, target_time: datetime) -> Optional[float]:
        """Find the closest carbon intensity value for a given time"""
        if not self.carbon_data_cache:
            return None
        
        min_diff = None
        closest_intensity = None
        
        for ts, intensity in self.carbon_data_cache.items():
            diff = abs(ts - target_time)
            if min_diff is None or diff < min_diff:
                min_diff = diff
                closest_intensity = intensity
        
        # Only use if within 1 hour
        if min_diff and min_diff < timedelta(hours=1):
            return closest_intensity
        
        return None
    
    def _find_worst_continuous_period(self, target_date: date, duration_minutes: int) -> float:
        """Find the worst continuous period of the day for the given duration in g/kWh"""
        # Filter data for the specific date
        day_data = {}
        for ts, intensity in self.carbon_data_cache.items():
            if ts.date() == target_date:
                day_data[ts] = intensity
        
        if not day_data:
            return 600.0  # Default worst case 600g/kWh
        
        # Sort timestamps
        timestamps = sorted(day_data.keys())
        
        # Calculate number of 10-minute slots needed
        slots_needed = (duration_minutes + 9) // 10  # Round up
        
        worst_average = 0
        
        # Slide window across the day
        for i in range(len(timestamps) - slots_needed + 1):
            window_intensities = []
            for j in range(slots_needed):
                if i + j < len(timestamps):
                    window_intensities.append(day_data[timestamps[i + j]])
            
            if window_intensities:
                avg_intensity = sum(window_intensities) / len(window_intensities)
                worst_average = max(worst_average, avg_intensity)
        
        return worst_average if worst_average > 0 else 600.0
    
    async def _calculate_month_to_date(
        self, 
        db: AsyncSession, 
        user: User, 
        up_to_date: date
    ) -> float:
        """Calculate total carbon (CO2e) saved from month start up to a specific date in grams"""
        month_start = date(up_to_date.year, up_to_date.month, 1)
        
        result = await db.execute(
            select(func.sum(DailyCarbonProgress.daily_carbon_saved)).where(
                and_(
                    DailyCarbonProgress.user_id == user.id,
                    DailyCarbonProgress.date >= month_start,
                    DailyCarbonProgress.date <= up_to_date
                )
            )
        )
        total = result.scalar()
        
        return total if total else 0.0