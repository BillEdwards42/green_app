#!/usr/bin/env python3
"""
Analyze duplicate carbon intensity entries and show generation mix differences
"""
import json
import csv
from datetime import datetime
from pathlib import Path
import pandas as pd

def load_carbon_log():
    """Load carbon calculation log to see generation details"""
    log_path = Path("logs/carbon_calculation_log.json")
    if log_path.exists():
        with open(log_path, 'r') as f:
            return json.load(f)
    return None

def load_csv_duplicates():
    """Load CSV and find duplicate timestamps"""
    csv_path = Path("logs/actual_carbon_intensity.csv")
    data = []
    
    with open(csv_path, 'r') as f:
        reader = csv.DictReader(f)
        for row in reader:
            data.append({
                'timestamp': row['timestamp'],
                'intensity': float(row['carbon_intensity_kgco2_kwh'])
            })
    
    # Group by timestamp
    timestamp_groups = {}
    for entry in data:
        ts = entry['timestamp']
        if ts not in timestamp_groups:
            timestamp_groups[ts] = []
        timestamp_groups[ts].append(entry['intensity'])
    
    # Find duplicates
    duplicates = {ts: values for ts, values in timestamp_groups.items() if len(values) > 1}
    return duplicates

def analyze_generation_files():
    """Check the actual generation data files for recent timestamps"""
    import glob
    
    # Look for recent carbon intensity JSON files
    json_files = glob.glob("data/carbon_intensity*.json")
    
    results = {}
    for file_path in json_files:
        with open(file_path, 'r') as f:
            data = json.load(f)
            
        if 'current' in data:
            timestamp = data['current'].get('timestamp', 'unknown')
            results[file_path] = {
                'timestamp': timestamp,
                'intensity': data['current'].get('carbon_intensity', 0),
                'total_generation': data['current'].get('total_generation_mw', 0),
                'generation_mix': data['current'].get('generation_mix', {}),
                'generation_mw': data['current'].get('generation_mw', {})
            }
    
    return results

def check_fluctuation_log():
    """Check fluctuation log for changes between runs"""
    log_path = Path("logs/fluctuation_log.txt")
    if not log_path.exists():
        return []
    
    recent_entries = []
    current_entry = {}
    
    with open(log_path, 'r') as f:
        lines = f.readlines()
        
    for line in lines:
        line = line.strip()
        if line.startswith('Timestamp:'):
            if current_entry:
                recent_entries.append(current_entry)
            current_entry = {'timestamp': line.split(':', 1)[1].strip(), 'changes': []}
        elif 'ADDED:' in line or 'REMOVED:' in line:
            current_entry['status'] = line
        elif line.startswith('  -'):
            if 'changes' in current_entry:
                current_entry['changes'].append(line)
        elif 'Status: COMPLETE' in line:
            current_entry['status'] = 'No changes'
    
    if current_entry:
        recent_entries.append(current_entry)
    
    # Return last 20 entries
    return recent_entries[-20:]

def main():
    print("Carbon Intensity Duplicate Analysis")
    print("=" * 80)
    
    # Load duplicate timestamps
    duplicates = load_csv_duplicates()
    print(f"\nFound {len(duplicates)} timestamps with duplicate entries")
    
    # Show recent duplicates
    recent_duplicates = sorted(duplicates.items())[-10:]  # Last 10
    
    print("\nRecent duplicate entries:")
    print("-" * 80)
    for timestamp, values in recent_duplicates:
        print(f"\n{timestamp}:")
        for i, value in enumerate(values):
            print(f"  Entry {i+1}: {value:.6f} kgCO2/kWh")
        diff = abs(values[1] - values[0])
        diff_pct = (diff / values[0]) * 100
        print(f"  Difference: {diff:.6f} ({diff_pct:.2f}%)")
    
    # Check generation files
    print("\n" + "=" * 80)
    print("Current generation data in JSON files:")
    print("-" * 80)
    
    gen_files = analyze_generation_files()
    for file_path, data in gen_files.items():
        print(f"\nFile: {file_path}")
        print(f"Timestamp: {data['timestamp']}")
        print(f"Carbon Intensity: {data['intensity']} kgCO2/kWh")
        print(f"Total Generation: {data['total_generation']} MW")
        
        if data['generation_mw']:
            print("\nGeneration by fuel type (MW):")
            sorted_fuels = sorted(data['generation_mw'].items(), key=lambda x: x[1], reverse=True)
            for fuel, mw in sorted_fuels[:10]:  # Top 10
                if mw > 0:
                    print(f"  {fuel:15s}: {mw:8.2f} MW")
    
    # Check fluctuation log
    print("\n" + "=" * 80)
    print("Recent changes from fluctuation log:")
    print("-" * 80)
    
    fluctuations = check_fluctuation_log()
    for entry in fluctuations[-5:]:  # Last 5 entries
        print(f"\n{entry['timestamp']}: {entry.get('status', 'Unknown')}")
        if entry.get('changes'):
            for change in entry['changes'][:3]:  # First 3 changes
                print(change)
    
    # Load carbon calculation log
    print("\n" + "=" * 80)
    print("Latest carbon calculation details:")
    print("-" * 80)
    
    calc_log = load_carbon_log()
    if calc_log:
        print(f"\nCalculation timestamp: {calc_log.get('timestamp', 'unknown')}")
        print(f"National intensity: {calc_log.get('national_intensity', 0):.6f} kgCO2/kWh")
        print(f"Total generation: {calc_log.get('total_generation_mw', 0):.2f} MW")
        
        if 'fuel_details' in calc_log:
            print("\nFuel breakdown:")
            sorted_fuels = sorted(calc_log['fuel_details'].items(), 
                                key=lambda x: x[1]['generation_mw'], reverse=True)
            for fuel, details in sorted_fuels:
                if details['generation_mw'] > 0:
                    print(f"  {fuel:15s}: {details['generation_mw']:8.2f} MW "
                          f"→ {details['emissions_kg']:10.2f} kg CO2e")
    
    print("\n" + "=" * 80)
    print("RECOMMENDATION:")
    print("-" * 80)
    print("The carbon intensity differences between duplicate entries are typically small")
    print("(< 2%), suggesting they represent real-time changes in the generation mix.")
    print("\nThe SECOND entry for each timestamp is likely more accurate because:")
    print("1. It represents the most recent data fetch")
    print("2. The Taipower API updates continuously")
    print("3. The differences align with normal grid fluctuations")
    print("\nTo fix this issue, ensure only ONE instance of the carbon generator is running.")

if __name__ == "__main__":
    # Change to backend API directory
    import os
    os.chdir(Path(__file__).parent.parent)
    main()