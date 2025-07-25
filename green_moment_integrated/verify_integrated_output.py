# ==============================================================================
# SCRIPT: verify_integrated_output.py
# PURPOSE:
#   - Reads the integrated data from the 'stru_data' directory
#   - Finds the latest timestamp and aggregates the generation data
#   - Prints a formatted report of the current generation mix
#   - Checks data completeness (generation + weather)
# ==============================================================================
import pandas as pd
from pathlib import Path
import sys
from datetime import datetime
import pytz

# --- Configuration ---
BASE_DIR = Path(__file__).parent
STRU_DATA_DIR = BASE_DIR / "stru_data"
LOGS_DIR = BASE_DIR / "logs"
LOG_FILE = LOGS_DIR / "fluctuation_log.txt"

TAIWAN_TZ = pytz.timezone('Asia/Taipei')

# Fuel types for aggregation
FUEL_TYPES = ['Nuclear', 'Coal', 'Co-Gen', 'IPP-Coal', 'LNG', 'IPP-LNG', 
              'Oil', 'Diesel', 'Hydro', 'Wind', 'Solar', 'Other_Renewable', 'Storage']

# Chinese names for display
FUEL_TYPE_CHINESE = {
    'Nuclear': '核能(Nuclear)',
    'Coal': '燃煤(Coal)',
    'Co-Gen': '汽電共生(Co-Gen)',
    'IPP-Coal': '民營電廠-燃煤(IPP-Coal)',
    'LNG': '燃氣(LNG)',
    'IPP-LNG': '民營電廠-燃氣(IPP-LNG)',
    'Oil': '燃油(Oil)',
    'Diesel': '輕油(Diesel)',
    'Hydro': '水力(Hydro)',
    'Wind': '風力(Wind)',
    'Solar': '太陽能(Solar)',
    'Other_Renewable': '其它再生能源(Other Renewable Energy)',
    'Storage': '儲能(Energy Storage System)'
}

def verify_aggregation():
    """Finds, loads, and verifies the latest data entries from regional CSV files."""
    run_time = pd.Timestamp.now(tz=TAIWAN_TZ)
    print(f"[{run_time.strftime('%Y-%m-%d %H:%M:%S')}] --- Starting Verification Script ---")

    if not STRU_DATA_DIR.exists():
        print(f"🚨 ERROR: Data directory not found at '{STRU_DATA_DIR}'.")
        sys.exit(1)

    # Load all regional CSV files
    all_csv_files = list(STRU_DATA_DIR.glob('*.csv'))
    if not all_csv_files:
        print(f"🚨 ERROR: No CSV files found in '{STRU_DATA_DIR}'.")
        sys.exit(1)
        
    print(f"   -> Found {len(all_csv_files)} regional data files to analyze.")
    
    # Read and combine all regional data
    all_data = []
    for csv_file in all_csv_files:
        try:
            df = pd.read_csv(csv_file)
            df['Region'] = csv_file.stem  # Add region name from filename
            all_data.append(df)
        except Exception as e:
            print(f"⚠️ WARNING: Failed to read {csv_file.name}: {e}")
    
    if not all_data:
        print("🚨 ERROR: Could not read any data files.")
        sys.exit(1)
    
    # Combine all regional data
    combined_df = pd.concat(all_data, ignore_index=True)
    combined_df['Timestamp'] = pd.to_datetime(combined_df['Timestamp'])
    
    # Find the latest timestamp
    latest_timestamp = combined_df['Timestamp'].max()
    latest_df = combined_df[combined_df['Timestamp'] == latest_timestamp].copy()
    
    if latest_df.empty:
        print(f"🚨 ERROR: No data found for the latest timestamp ({latest_timestamp}).")
        sys.exit(1)

    # Aggregate fuel types across all regions
    fuel_sums = {}
    for fuel_type in FUEL_TYPES:
        if fuel_type in latest_df.columns:
            fuel_sums[fuel_type] = latest_df[fuel_type].sum()
        else:
            fuel_sums[fuel_type] = 0.0
    
    total_generation = sum(fuel_sums.values())

    # Check data completeness
    print("\n" + "="*50)
    print("📊 DATA COMPLETENESS CHECK")
    print("="*50)
    
    for _, row in latest_df.iterrows():
        region = row['Region']
        has_generation = row['Total_Generation'] > 0 if 'Total_Generation' in row else False
        has_weather = all(pd.notna(row.get(col)) for col in ['AirTemperature', 'WindSpeed', 'SunshineDuration'])
        
        status = "✅" if has_generation and has_weather else "⚠️"
        gen_status = "✓" if has_generation else "✗"
        weather_status = "✓" if has_weather else "✗"
        
        print(f"{status} {region}: Generation[{gen_status}] Weather[{weather_status}]")

    # Print generation report
    print("\n" + "="*50)
    print("台電系統各機組發電量（單位 MW）")
    print(f"更新時間 - {latest_timestamp.strftime('%Y-%m-%d %H:%M')}")
    print("\n各能源別即時發電量小計(每10分鐘更新)：")
    print(f"總計： {total_generation:,.1f} MW\n")

    # Define display order
    display_order = ['Nuclear', 'Coal', 'Co-Gen', 'IPP-Coal', 'LNG', 'IPP-LNG', 
                    'Oil', 'Diesel', 'Hydro', 'Wind', 'Solar', 'Other_Renewable', 'Storage']
    
    for fuel_type in display_order:
        if fuel_type in fuel_sums:
            total_mw = fuel_sums[fuel_type]
            percentage = (total_mw / total_generation) * 100 if total_generation > 0 else 0
            chinese_name = FUEL_TYPE_CHINESE.get(fuel_type, fuel_type)
            
            print(f"{chinese_name}")
            print(f"{total_mw:,.1f}")
            print(f"{percentage:.3f}%\n")
    
    # Display weather summary
    print("="*50)
    print("🌤️ WEATHER SUMMARY (Regional Averages)")
    print("="*50)
    
    weather_cols = ['AirTemperature', 'WindSpeed', 'SunshineDuration']
    for _, row in latest_df.iterrows():
        region = row['Region']
        if region == 'Other':
            continue  # Skip Other region for weather
        
        weather_data = []
        for col in weather_cols:
            if col in row and pd.notna(row[col]):
                if col == 'AirTemperature':
                    weather_data.append(f"Temp: {row[col]:.1f}°C")
                elif col == 'WindSpeed':
                    weather_data.append(f"Wind: {row[col]:.1f} m/s")
                elif col == 'SunshineDuration':
                    weather_data.append(f"Sunshine: {row[col]:.1f} hr")
        
        if weather_data:
            print(f"{region}: {' | '.join(weather_data)}")
        else:
            print(f"{region}: No weather data available")
    
    print("="*50 + "\n")
    print("✅ Verification report complete.")

def display_latest_fluctuation_report():
    """Display the latest fluctuation report from the log file."""
    if not LOG_FILE.exists():
        print("\n--- Fluctuation Log ---")
        print("No fluctuation log found.")
        return

    with open(LOG_FILE, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    latest_report_lines = []
    found_latest = False
    for i in reversed(range(len(lines))):
        if "--- Fluctuation Report @" in lines[i]:
            found_latest = True
            latest_report_lines.insert(0, lines[i])
            break
        if found_latest or lines[i].strip():
            latest_report_lines.insert(0, lines[i])

    print("\n" + "="*50)
    print("--- Latest Fluctuation Report ---")
    if latest_report_lines:
        for line in latest_report_lines:
            print(line.strip())
    else:
        print("No fluctuation reports found.")
    print("="*50)

def check_data_sync():
    """Check timestamp synchronization between generation and weather data."""
    print("\n" + "="*50)
    print("🔄 TIMESTAMP SYNCHRONIZATION CHECK")
    print("="*50)
    
    for csv_file in STRU_DATA_DIR.glob('*.csv'):
        try:
            df = pd.read_csv(csv_file)
            df['Timestamp'] = pd.to_datetime(df['Timestamp'])
            
            # Get last 5 entries
            recent_df = df.tail(5)
            
            print(f"\n{csv_file.stem} (last 5 entries):")
            for _, row in recent_df.iterrows():
                timestamp = row['Timestamp'].strftime('%Y-%m-%d %H:%M')
                has_gen = row.get('Total_Generation', 0) > 0
                has_weather = pd.notna(row.get('AirTemperature'))
                
                gen_marker = "G" if has_gen else "-"
                weather_marker = "W" if has_weather else "-"
                
                print(f"  {timestamp} [{gen_marker}{weather_marker}]")
                
        except Exception as e:
            print(f"⚠️ Could not analyze {csv_file.stem}: {e}")
    
    print("\n[G=Generation, W=Weather, -=Missing]")
    print("="*50)

if __name__ == "__main__":
    verify_aggregation()
    display_latest_fluctuation_report()
    check_data_sync()