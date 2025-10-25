# ==============================================================================
# SCRIPT: fetch_weather_integrated.py
# PURPOSE:
#   - Fetches real-time weather observations for power generation-relevant stations
#   - Updates regional CSV files with weather data
#   - Synchronizes with generation data using timestamps
# ==============================================================================
import os
import requests
import json
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime
import csv
import time
import fcntl
import pandas as pd
import sys

# --- Configuration ---
load_dotenv()
CWA_API_KEY = os.getenv("CWA_API_KEY")
if not CWA_API_KEY:
    CWA_API_KEY = "CWA-172B1A42-2A07-46CB-BE7C-4B0F2C8A1525"

# API endpoint for real-time observations
BASE_API_URL = "https://opendata.cwa.gov.tw/api/v1/rest/datastore/O-A0003-001"

# Define paths
BASE_DIR = Path(__file__).parent
STRU_DATA_DIR = BASE_DIR / "stru_data"
LOGS_DIR = BASE_DIR / "logs"
WEATHER_LOG_FILE = LOGS_DIR / "10min_weather_log.csv"

# Stations relevant to power generation, grouped by region
# 北部地區 (North) - 涵蓋主要都會區、沿海地區（風力發電）及主要空港
# 中部地區 (Central) - 包含沿海風場、平原光電區、關鍵水力發電指標
# 南部地區 (South) - 集中在嘉南與高屏平原，台灣太陽能發電重鎮
# 東部地區 (East) - 涵蓋宜蘭平原與花東縱谷主要人口與農業區
# 離島地區 (Islands) - 獨立電網，應獨立看待
STATIONS_BY_REGION = {
    "North": [
        "基隆", "淡水", "新北", "新竹", "臺北", "新屋",
        "桃園農改", "文山茶改", "新埔工作站"
    ],
    "Central": [
        "臺中", "梧棲", "後龍", "古坑", "彰師大", "麥寮",
        "田中", "日月潭", "苗栗農改"
    ],
    "South": [
        "嘉義", "臺南", "高雄", "恆春", "永康",
        "臺南農改", "旗南農改", "高雄農改", "屏東"
    ],
    "East": [
        "宜蘭", "花蓮", "成功", "臺東", "大武"
    ],
    "Islands": [
        "澎湖", "金門", "馬祖", "東吉島", "蘭嶼"
    ]
}

# Fields to extract and average
TARGET_FIELDS = ["SunshineDuration", "AirTemperature", "WindSpeed", "Precipitation"]

# All fields to extract for comprehensive station data
ALL_STATION_FIELDS = ["AirTemperature", "WindSpeed", "SunshineDuration", "Precipitation", "UVIndex", "WindDirection"]

# --- Helper Functions ---
def ensure_directories():
    """Create necessary directories if they don't exist."""
    STRU_DATA_DIR.mkdir(parents=True, exist_ok=True)
    LOGS_DIR.mkdir(parents=True, exist_ok=True)

def safe_float_convert(value):
    """Safely converts a value to float, handling CWA's null identifiers."""
    try:
        if float(value) < -90:
            return None
        return float(value)
    except (ValueError, TypeError):
        return None

def fetch_weather_data():
    """Fetches the latest weather observation data from the CWA API."""
    params = {"Authorization": CWA_API_KEY}
    print(f"📡 [{datetime.now().strftime('%H:%M:%S')}] Fetching real-time weather data...")
    try:
        response = requests.get(BASE_API_URL, params=params, timeout=30)
        response.raise_for_status()
        print(f"✅ SUCCESS: API response received. Status: {response.status_code}")
        return response.json()
    except requests.exceptions.HTTPError as e:
        print(f"❌ HTTP ERROR: {e}")
    except Exception as e:
        print(f"❌ UNEXPECTED ERROR during fetch: {e}")
    return None

def read_csv_with_lock(filepath):
    """Read CSV file with file locking."""
    with open(filepath, 'r') as f:
        fcntl.flock(f.fileno(), fcntl.LOCK_SH)
        try:
            df = pd.read_csv(f)
            return df
        finally:
            fcntl.flock(f.fileno(), fcntl.LOCK_UN)

def write_csv_with_lock(df, filepath, mode='w'):
    """Write CSV file with file locking."""
    with open(filepath, mode) as f:
        fcntl.flock(f.fileno(), fcntl.LOCK_EX)
        try:
            if mode == 'w':
                df.to_csv(f, index=False)
            else:
                df.to_csv(f, index=False, header=False)
        finally:
            fcntl.flock(f.fileno(), fcntl.LOCK_UN)

def round_to_nearest_10min(dt):
    """Round datetime to nearest 10-minute interval."""
    # Round down to nearest 10 minutes
    minutes = (dt.minute // 10) * 10
    return dt.replace(minute=minutes, second=0, microsecond=0)

def save_all_stations_data(all_stations_data, obs_datetime):
    """Save comprehensive weather data for all stations in wide format."""
    all_stations_file = STRU_DATA_DIR / "all_stations_weather.csv"
    
    # Prepare data dictionary with DateTime as first column
    row_data = {"DateTime": obs_datetime}
    
    # Process each station
    for station in all_stations_data:
        station_name = station.get("StationName")
        if not station_name:
            continue
            
        elements = station.get("WeatherElement", {})
        
        # Extract all fields for this station
        for field in ALL_STATION_FIELDS:
            column_name = f"{station_name}_{field}"
            
            if field == "Precipitation":
                # Special handling for precipitation (nested in "Now")
                value = elements.get("Now", {}).get("Precipitation")
            else:
                value = elements.get(field)
            
            # Convert to float, handling null values
            float_value = safe_float_convert(value)
            row_data[column_name] = float_value if float_value is not None else ""
    
    # Create DataFrame with single row
    new_df = pd.DataFrame([row_data])
    
    # Check if file exists and append or create new
    if all_stations_file.exists():
        try:
            # Read existing data
            existing_df = read_csv_with_lock(all_stations_file)
            
            # Check if this timestamp already exists
            if obs_datetime in existing_df['DateTime'].values:
                print(f"⚠️ Data for {obs_datetime} already exists in all_stations_weather.csv. Skipping.")
                return
            
            # Append new row
            combined_df = pd.concat([existing_df, new_df], ignore_index=True)
            write_csv_with_lock(combined_df, all_stations_file)
            print(f"✅ Appended new data to all_stations_weather.csv")
        except Exception as e:
            print(f"❌ Error updating all_stations_weather.csv: {e}")
    else:
        # Create new file
        write_csv_with_lock(new_df, all_stations_file)
        print(f"✅ Created new all_stations_weather.csv with {len(row_data)-1} station metrics")

def get_latest_timestamp_from_csvs():
    """Get the most recent timestamp from regional CSV files."""
    latest_timestamp = None
    
    for region_file in STRU_DATA_DIR.glob("*.csv"):
        if region_file.name == "electricity_demand.csv":
            continue
            
        try:
            df = pd.read_csv(region_file)
            if not df.empty and 'Timestamp' in df.columns:
                df['Timestamp'] = pd.to_datetime(df['Timestamp'])
                file_latest = df['Timestamp'].max()
                if latest_timestamp is None or file_latest > latest_timestamp:
                    latest_timestamp = file_latest
        except Exception as e:
            print(f"⚠️ Could not read {region_file.name}: {e}")
    
    return latest_timestamp

def process_and_update_data(api_data):
    """Process weather data and update regional CSV files."""
    try:
        all_stations_data = api_data['records']['Station']
        if not all_stations_data:
            print("⚠️ WARNING: API response contains no station data.")
            return
    except KeyError:
        print("❌ ERROR: Could not find valid 'records' or 'Station' structure in API data.")
        return
    
    # Extract common observation datetime from first station
    obs_datetime = None
    if all_stations_data:
        first_station = all_stations_data[0]
        obs_time_str = first_station.get("ObsTime", {}).get("DateTime")
        if obs_time_str:
            try:
                # Parse the datetime string and format it consistently
                from datetime import datetime as dt
                obs_dt = dt.fromisoformat(obs_time_str.replace('+08:00', ''))
                obs_datetime = obs_dt.strftime('%Y-%m-%d %H:%M:%S')
            except:
                obs_datetime = obs_time_str
    
    # Save comprehensive data for all stations
    if obs_datetime:
        print("\n📊 Saving comprehensive station data...")
        save_all_stations_data(all_stations_data, obs_datetime)

    # Get the latest timestamp from existing CSV files
    target_timestamp = get_latest_timestamp_from_csvs()
    if target_timestamp is None:
        print("⚠️ No existing generation data found. Weather update skipped.")
        return
    
    print(f"📅 Updating weather data for timestamp: {target_timestamp}")

    # Process individual station data for logging
    log_rows = []
    processed_stations = {}

    for station in all_stations_data:
        station_name = station.get("StationName")
        if not any(station_name in sl for sl in STATIONS_BY_REGION.values()):
            continue

        obs_time_str = station.get("ObsTime", {}).get("DateTime")
        elements = station.get("WeatherElement", {})
        
        temp = safe_float_convert(elements.get("AirTemperature"))
        wind = safe_float_convert(elements.get("WindSpeed"))
        sunshine = safe_float_convert(elements.get("SunshineDuration"))
        
        # Extract precipitation from nested "Now" structure
        precip_value = elements.get("Now", {}).get("Precipitation")
        precip = safe_float_convert(precip_value)
        
        # Extract additional fields
        uv_index = safe_float_convert(elements.get("UVIndex"))
        wind_dir = safe_float_convert(elements.get("WindDirection"))
        
        has_null = any(v is None for v in [temp, wind, sunshine, precip])
        
        processed_stations[station_name] = {
            "AirTemperature": temp,
            "WindSpeed": wind,
            "SunshineDuration": sunshine,
            "Precipitation": precip,
            "UVIndex": uv_index,
            "WindDirection": wind_dir,
            "ObsTime": obs_time_str
        }

        log_rows.append({
            "Timestamp": obs_time_str,
            "StationName": station_name,
            "AirTemperature": temp if temp is not None else 'NULL',
            "WindSpeed": wind if wind is not None else 'NULL',
            "SunshineDuration": sunshine if sunshine is not None else 'NULL',
            "Precipitation": precip if precip is not None else 'NULL',
            "HasNullValue": has_null
        })

    if not log_rows:
        print("⚠️ No relevant stations found in the fetched data.")
        return

    # Log individual station data
    log_file_exists = WEATHER_LOG_FILE.exists()
    with open(WEATHER_LOG_FILE, 'a', newline='', encoding='utf-8') as csvfile:
        fieldnames = ["Timestamp", "StationName", "AirTemperature", "WindSpeed", "SunshineDuration", "Precipitation", "HasNullValue"]
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        if not log_file_exists:
            writer.writeheader()
        writer.writerows(log_rows)
    print(f"📝 {len(log_rows)} station records logged")

    # Update regional CSV files with weather data
    print("\n" + "="*60)
    print("STARTING REGIONAL PROCESSING WITH DEBUG OUTPUT")
    print("="*60)
    
    for region, station_list in STATIONS_BY_REGION.items():
        csv_path = STRU_DATA_DIR / f"{region}.csv"
        
        # Skip "Other" region as it doesn't have weather stations
        if region == "Other":
            continue
        
        # Calculate regional averages
        regional_averages = {}
        print(f"\n🔍 DEBUG: Processing {region} region")
        print(f"   Stations in region: {station_list}")
        sys.stdout.flush()
        
        for field in TARGET_FIELDS:
            print(f"\n   📊 Field: {field}")
            
            # Collect values with detailed logging
            station_values = []
            for s_name in station_list:
                if s_name in processed_stations:
                    value = processed_stations[s_name][field]
                    obs_time = processed_stations[s_name]['ObsTime']
                    station_values.append((s_name, value))
                    print(f"      - {s_name}: {value if value is not None else 'NULL'} (ObsTime: {obs_time})")
                else:
                    print(f"      - {s_name}: NOT FOUND in processed stations")
            
            # Filter out None values for average calculation
            valid_values = [v for name, v in station_values if v is not None]
            
            if valid_values:
                average = sum(valid_values) / len(valid_values)
                regional_averages[field] = round(average, 2)
                print(f"      ➡️  Average ({len(valid_values)} valid stations): {regional_averages[field]}")
            else:
                regional_averages[field] = None
                print(f"      ➡️  Average: None (no valid data)")

        # Update CSV file
        if csv_path.exists():
            try:
                df = read_csv_with_lock(csv_path)
                
                # Debug East region specifically
                if region == 'East':
                    print(f"   -> East.csv debug: {len(df)} rows, columns: {list(df.columns)}")
                    if not df.empty:
                        print(f"   -> East last row Total_Generation: {df.iloc[-1].get('Total_Generation', 'N/A')}")
                
                if df.empty:
                    print(f"⚠️ {region}.csv is empty. Skipping weather update.")
                    continue
                
                # Convert timestamps to datetime for comparison
                df['Timestamp'] = pd.to_datetime(df['Timestamp'])
                target_timestamp_dt = pd.to_datetime(target_timestamp)
                
                # Find the most recent row (last row) instead of exact timestamp match
                # This is more flexible and handles timezone/format differences
                last_idx = df.index[-1]  # Get last row
                
                # Update weather columns in the last row
                df.loc[last_idx, 'AirTemperature'] = regional_averages.get('AirTemperature')
                df.loc[last_idx, 'WindSpeed'] = regional_averages.get('WindSpeed') 
                df.loc[last_idx, 'SunshineDuration'] = regional_averages.get('SunshineDuration')
                df.loc[last_idx, 'Precipitation'] = regional_averages.get('Precipitation')
                
                # Debug output showing what values are being written
                print(f"\n   💾 Writing to CSV for {region}:")
                print(f"      - AirTemperature: {regional_averages.get('AirTemperature')}")
                print(f"      - WindSpeed: {regional_averages.get('WindSpeed')}")
                print(f"      - SunshineDuration: {regional_averages.get('SunshineDuration')}")
                print(f"      - Precipitation: {regional_averages.get('Precipitation')}")
                
                write_csv_with_lock(df, csv_path)
                print(f"✅ Updated weather data for {region} (last entry: {df.loc[last_idx, 'Timestamp']})")
                    
            except Exception as e:
                print(f"❌ ERROR updating {region}: {e}")
        else:
            print(f"⚠️ No generation data file found for {region}. Skipping weather update.")

def main():
    """Main execution function."""
    print("\n" + "="*60)
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Starting weather fetch...")
    
    ensure_directories()
    
    # Fetch and process weather data
    api_response_data = fetch_weather_data()
    if api_response_data:
        process_and_update_data(api_response_data)
    
    print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Weather fetch completed!")
    print("="*60 + "\n")

if __name__ == "__main__":
    main()