#!/usr/bin/env python3
"""
Debug carbon (CO2e) calculations for a specific user
"""

import asyncio
import sys
import os
from datetime import datetime

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import AsyncSessionLocal
from sqlalchemy import select
from app.models.chore import Chore
from app.models.user import User
from app.services.carbon_calculator import DailyCarbonCalculator
from app.constants.appliances import APPLIANCE_POWER


async def debug_calculations():
    """Debug carbon (CO2e) calculations for edwards_test1"""
    
    calculator = DailyCarbonCalculator()
    
    async with AsyncSessionLocal() as db:
        # Get user and chores
        result = await db.execute(
            select(User).where(User.username == 'edwards_test1')
        )
        user = result.scalar_one()
        
        result = await db.execute(
            select(Chore)
            .where(Chore.user_id == user.id)
            .order_by(Chore.start_time)
        )
        chores = result.scalars().all()
        
        print("Carbon (CO2e) Calculation Debug")
        print("=" * 80)
        print(f"\nCarbon intensity data from CSV is in kg CO2e/kWh")
        print(f"Typical values: 0.4-0.6 kg CO2e/kWh\n")
        
        total_saved = 0.0
        
        for chore in chores:
            print(f"\n{chore.start_time.date()} - {chore.appliance_type}")
            print("-" * 60)
            
            # Get appliance power
            power_kw = APPLIANCE_POWER.get(chore.appliance_type, 1.0)
            duration_hours = chore.duration_minutes / 60.0
            energy_kwh = power_kw * duration_hours
            
            print(f"  Appliance: {chore.appliance_type}")
            print(f"  Power: {power_kw} kW")
            print(f"  Duration: {chore.duration_minutes} minutes ({duration_hours:.2f} hours)")
            print(f"  Energy used: {energy_kwh:.2f} kWh")
            
            # Calculate actual and worst case
            actual_intensity = calculator._calculate_period_carbon_intensity(
                chore.start_time, chore.end_time
            )
            worst_intensity = calculator._find_worst_continuous_period(
                chore.start_time.date(), chore.duration_minutes
            )
            
            print(f"  Actual carbon intensity: {actual_intensity:.3f} kg CO2e/kWh")
            print(f"  Worst case intensity: {worst_intensity:.3f} kg CO2e/kWh")
            print(f"  Difference: {worst_intensity - actual_intensity:.3f} kg CO2e/kWh")
            
            # Calculate carbon (CO2e) saved
            carbon_saved_kg = (worst_intensity - actual_intensity) * energy_kwh
            carbon_saved_g = carbon_saved_kg * 1000
            
            print(f"  Carbon (CO2e) saved: {carbon_saved_kg:.3f} kg ({carbon_saved_g:.0f} g)")
            
            total_saved += carbon_saved_kg
        
        print(f"\n{'=' * 80}")
        print(f"TOTAL CARBON (CO2e) SAVED: {total_saved:.3f} kg ({total_saved * 1000:.0f} g)")
        print(f"\nNote: The large savings are primarily due to EV charging (50 kW)")
        print(f"which uses a lot of energy even over short periods.")


if __name__ == "__main__":
    asyncio.run(debug_calculations())