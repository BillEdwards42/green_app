#!/usr/bin/env python3
"""
Fix X9 timestamps in actual_carbon_intensity.csv by converting them to X0 timestamps.
This ensures consistency with the new timestamp format where data represents X0 time slots.

IMPORTANT: This script handles the carbon calculation dependencies carefully:
1. Preserves intensity values (they remain accurate for the time period)
2. Handles duplicates by keeping the most recent value
3. Maintains chronological order for carbon calculations
4. Backs up the original file before making changes
"""

import csv
import os
import shutil
from datetime import datetime
from collections import OrderedDict
import sys

def convert_x9_to_x0(timestamp_str):
    """Convert X9 timestamp to X0 timestamp"""
    dt = datetime.strptime(timestamp_str, '%Y-%m-%d %H:%M:%S')
    
    # If minute ends in 9, change it to 0 (representing the X0 time slot)
    if dt.minute % 10 == 9:
        # Change X9 to X0 (e.g., 08:59 -> 08:50)
        new_minute = (dt.minute // 10) * 10
        dt = dt.replace(minute=new_minute)
    
    return dt.strftime('%Y-%m-%d %H:%M:%S')

def fix_timestamps(input_file, output_file):
    """Fix X9 timestamps in the CSV file"""
    # Read all data
    data = []
    with open(input_file, 'r') as f:
        reader = csv.DictReader(f)
        headers = reader.fieldnames
        
        for row in reader:
            timestamp = row['timestamp']
            # Convert X9 to X0
            new_timestamp = convert_x9_to_x0(timestamp)
            
            # Update the row with new timestamp
            row['timestamp'] = new_timestamp
            data.append(row)
    
    # Remove duplicates, keeping the last (most recent) entry for each timestamp
    # This is important because if we have both X9 and X0 entries, we want the latest data
    unique_data = OrderedDict()
    for row in data:
        unique_data[row['timestamp']] = row
    
    # Sort by timestamp to maintain chronological order
    sorted_data = sorted(unique_data.values(), key=lambda x: x['timestamp'])
    
    # Write the cleaned data
    with open(output_file, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()
        writer.writerows(sorted_data)
    
    return len(data), len(sorted_data)

def analyze_impact(input_file):
    """Analyze the impact of the timestamp changes"""
    x9_count = 0
    x0_count = 0
    duplicates = {}
    
    with open(input_file, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            timestamp = row['timestamp']
            dt = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
            
            if dt.minute % 10 == 9:
                x9_count += 1
            elif dt.minute % 10 == 0:
                x0_count += 1
            
            # Track potential duplicates after conversion
            converted = convert_x9_to_x0(timestamp)
            if converted not in duplicates:
                duplicates[converted] = []
            duplicates[converted].append({
                'original': timestamp,
                'intensity': float(row.get('carbon_intensity_kgco2e_kwh', row.get('carbon_intensity_kgco2_kwh', 0)))
            })
    
    # Find actual duplicates
    actual_duplicates = {k: v for k, v in duplicates.items() if len(v) > 1}
    
    return x9_count, x0_count, actual_duplicates

def main():
    # File paths
    csv_file = 'logs/actual_carbon_intensity.csv'
    backup_file = f'logs/actual_carbon_intensity_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    
    if not os.path.exists(csv_file):
        print(f"Error: {csv_file} not found!")
        sys.exit(1)
    
    print("Carbon Intensity Timestamp Fix Tool")
    print("=" * 60)
    
    # Analyze current state
    print("\nAnalyzing current file...")
    x9_count, x0_count, duplicates = analyze_impact(csv_file)
    
    print(f"\nCurrent statistics:")
    print(f"  X9 timestamps: {x9_count}")
    print(f"  X0 timestamps: {x0_count}")
    print(f"  Total entries: {x9_count + x0_count}")
    
    if duplicates:
        print(f"\nFound {len(duplicates)} timestamps that will have duplicates after conversion:")
        for ts, entries in list(duplicates.items())[:5]:  # Show first 5
            print(f"  {ts}:")
            for entry in entries:
                print(f"    - {entry['original']} -> {entry['intensity']:.6f} kgCO2e/kWh")
        if len(duplicates) > 5:
            print(f"  ... and {len(duplicates) - 5} more")
    
    # Ask for confirmation
    print("\nThis script will:")
    print("1. Convert all X9 timestamps to X0 (e.g., 08:59 -> 08:50)")
    print("2. Remove duplicates, keeping the most recent value")
    print("3. Maintain chronological order for carbon calculations")
    print("4. Create a backup of the original file")
    
    response = input("\nProceed with the fix? (y/N): ")
    if response.lower() != 'y':
        print("Operation cancelled.")
        sys.exit(0)
    
    # Create backup
    print(f"\nCreating backup: {backup_file}")
    shutil.copy2(csv_file, backup_file)
    
    # Fix timestamps
    print("Fixing timestamps...")
    original_count, final_count = fix_timestamps(csv_file, csv_file)
    
    print(f"\nComplete!")
    print(f"  Original entries: {original_count}")
    print(f"  Final entries: {final_count}")
    print(f"  Removed duplicates: {original_count - final_count}")
    
    # Verify the fix
    print("\nVerifying the fix...")
    x9_count_after, x0_count_after, _ = analyze_impact(csv_file)
    
    print(f"\nAfter fix:")
    print(f"  X9 timestamps: {x9_count_after}")
    print(f"  X0 timestamps: {x0_count_after + final_count - x0_count}")
    
    if x9_count_after == 0:
        print("\n✅ Success! All X9 timestamps have been converted to X0.")
    else:
        print("\n⚠️  Warning: Some X9 timestamps may still remain.")
    
    print(f"\nBackup saved to: {backup_file}")
    print("\nIMPORTANT: The carbon calculation logic will work correctly because:")
    print("- Intensity values are preserved (they represent the same time period)")
    print("- Chronological order is maintained")
    print("- Duplicates are resolved by keeping the most recent data")

if __name__ == "__main__":
    # Change to backend API directory
    os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    main()