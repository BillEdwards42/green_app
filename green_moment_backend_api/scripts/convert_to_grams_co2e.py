#!/usr/bin/env python3
"""
Convert all carbon values from kg to grams throughout the system
"""

import asyncio
import sys
import os
from sqlalchemy import text, select

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import AsyncSessionLocal
from app.models.user import User
from app.models.daily_carbon_progress import DailyCarbonProgress
from app.models.monthly_summary import MonthlySummary


async def convert_database_to_grams():
    """Convert all carbon values in database from kg to grams"""
    
    async with AsyncSessionLocal() as db:
        print("🔄 Converting database values from kg CO2e to g CO2e...")
        
        try:
            # Convert users table
            print("\n1. Converting users table...")
            await db.execute(text("""
                UPDATE users 
                SET total_carbon_saved = total_carbon_saved * 1000,
                    current_month_carbon_saved = current_month_carbon_saved * 1000
                WHERE total_carbon_saved > 0 OR current_month_carbon_saved > 0
            """))
            
            # Convert daily_carbon_progress table
            print("2. Converting daily_carbon_progress table...")
            await db.execute(text("""
                UPDATE daily_carbon_progress 
                SET daily_carbon_saved = daily_carbon_saved * 1000,
                    cumulative_carbon_saved = cumulative_carbon_saved * 1000
                WHERE daily_carbon_saved > 0 OR cumulative_carbon_saved > 0
            """))
            
            # Convert monthly_summaries table
            print("3. Converting monthly_summaries table...")
            await db.execute(text("""
                UPDATE monthly_summaries 
                SET total_carbon_saved = total_carbon_saved * 1000
                WHERE total_carbon_saved > 0
            """))
            
            # Update column comments to reflect grams
            print("\n4. Updating column comments...")
            comments = [
                "COMMENT ON COLUMN users.total_carbon_saved IS 'Total g CO2e saved lifetime'",
                "COMMENT ON COLUMN users.current_month_carbon_saved IS 'g CO2e saved in current month'",
                "COMMENT ON COLUMN daily_carbon_progress.daily_carbon_saved IS 'g CO2e saved on this day'",
                "COMMENT ON COLUMN daily_carbon_progress.cumulative_carbon_saved IS 'Cumulative g CO2e saved in month up to this day'",
                "COMMENT ON COLUMN monthly_summaries.total_carbon_saved IS 'Total g CO2e saved in the month'"
            ]
            
            for comment_sql in comments:
                await db.execute(text(comment_sql))
                print(f"  ✅ {comment_sql.split(' IS ')[0].split('.')[-1]}")
            
            await db.commit()
            print("\n✅ Database conversion completed!")
            
            # Show sample data
            print("\n📊 Sample data after conversion:")
            result = await db.execute(
                select(User).where(User.username == 'edwards_test1')
            )
            user = result.scalar_one_or_none()
            if user:
                print(f"  User: {user.username}")
                print(f"  Total CO2e saved: {user.total_carbon_saved:.0f}g")
                print(f"  Current month CO2e: {user.current_month_carbon_saved:.0f}g")
            
        except Exception as e:
            await db.rollback()
            print(f"\n❌ Error converting database: {e}")
            raise


def update_carbon_intensity_csv():
    """Update the carbon intensity CSV to use g/kWh instead of kg/kWh"""
    csv_path = 'logs/actual_carbon_intensity.csv'
    
    if os.path.exists(csv_path):
        print("\n5. Converting carbon intensity CSV to g CO2e/kWh...")
        
        # Read all lines
        with open(csv_path, 'r') as f:
            lines = f.readlines()
        
        # Update header and convert values
        new_lines = []
        for i, line in enumerate(lines):
            if i == 0:
                # Update header
                new_lines.append('timestamp,carbon_intensity_gco2e_kwh\n')
            else:
                # Convert kg to g
                parts = line.strip().split(',')
                if len(parts) == 2:
                    timestamp = parts[0]
                    kg_value = float(parts[1])
                    g_value = kg_value * 1000
                    new_lines.append(f'{timestamp},{g_value:.3f}\n')
                else:
                    new_lines.append(line)
        
        # Write back
        with open(csv_path, 'w') as f:
            f.writelines(new_lines)
        
        print("  ✅ CSV converted to g CO2e/kWh")
    else:
        print("  ⚠️  CSV file not found")


async def main():
    """Run all conversions"""
    print("🌱 Converting System to Grams CO2e")
    print("=" * 60)
    
    # Convert database values
    await convert_database_to_grams()
    
    # Convert CSV
    update_carbon_intensity_csv()
    
    print("\n" + "=" * 60)
    print("📋 Next Steps:")
    print("1. Update league thresholds to grams (100g, 500g, 700g, 1000g)")
    print("2. Update all calculations to work with grams")
    print("3. Update API responses to show _g instead of _kg")
    print("4. Update Flutter app to expect grams")
    print("\n⚠️  IMPORTANT: This conversion should only be run ONCE!")


if __name__ == "__main__":
    response = input("This will convert all carbon values from kg to grams. Continue? (yes/no): ")
    if response.lower() == 'yes':
        asyncio.run(main())
    else:
        print("Conversion cancelled.")