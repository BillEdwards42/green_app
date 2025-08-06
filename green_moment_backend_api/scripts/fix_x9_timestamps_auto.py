#!/usr/bin/env python3
"""
Fix X9 timestamps in actual_carbon_intensity.csv by converting them to X0 timestamps.
Auto-run version without user interaction.
"""

import csv
import os
import shutil
from datetime import datetime
from collections import OrderedDict

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
    
    with open(input_file, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            timestamp = row['timestamp']
            dt = datetime.strptime(timestamp, '%Y-%m-%d %H:%M:%S')
            
            if dt.minute % 10 == 9:
                x9_count += 1
            elif dt.minute % 10 == 0:
                x0_count += 1
    
    return x9_count, x0_count

def main():
    # Change to backend API directory
    os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    # File paths
    csv_file = 'logs/actual_carbon_intensity.csv'
    backup_file = f'logs/actual_carbon_intensity_backup_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    
    print("Carbon Intensity Timestamp Fix Tool (Auto-run)")
    print("=" * 60)
    
    # Analyze current state
    print("\nAnalyzing current file...")
    x9_before, x0_before = analyze_impact(csv_file)
    
    print(f"\nBefore fix:")
    print(f"  X9 timestamps: {x9_before}")
    print(f"  X0 timestamps: {x0_before}")
    print(f"  Total entries: {x9_before + x0_before}")
    
    # Create backup
    print(f"\nCreating backup: {backup_file}")
    shutil.copy2(csv_file, backup_file)
    
    # Fix timestamps
    print("\nFixing timestamps...")
    original_count, final_count = fix_timestamps(csv_file, csv_file)
    
    print(f"\nProcessing complete:")
    print(f"  Original entries: {original_count}")
    print(f"  Final entries: {final_count}")
    print(f"  Removed duplicates: {original_count - final_count}")
    
    # Verify the fix
    print("\nVerifying the fix...")
    x9_after, x0_after = analyze_impact(csv_file)
    
    print(f"\nAfter fix:")
    print(f"  X9 timestamps: {x9_after}")
    print(f"  X0 timestamps: {x0_after}")
    
    if x9_after == 0:
        print("\n✅ Success! All X9 timestamps have been converted to X0.")
    else:
        print("\n⚠️  Warning: Some X9 timestamps may still remain.")
    
    print(f"\nBackup saved to: {backup_file}")

if __name__ == "__main__":
    main()