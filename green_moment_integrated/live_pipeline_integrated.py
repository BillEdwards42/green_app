# ==============================================================================
# SCRIPT: live_pipeline_integrated.py
# PURPOSE:
#   - Fetches power generation data from Taipower every 10 minutes
#   - Outputs regional CSVs with fuel types as columns
#   - Integrates with weather data from separate script
# ==============================================================================
import pandas as pd
from pathlib import Path
import sys, re, json, requests, pytz, time, fcntl
from datetime import datetime, timedelta
import numpy as np

# --- Configuration ---
BASE_DIR = Path(__file__).parent
STRU_DATA_DIR = BASE_DIR / "stru_data"
CONFIG_DIR = BASE_DIR / "config"
LOGS_DIR = BASE_DIR / "logs"

PLANT_MAP_FILE = CONFIG_DIR / "plant_to_region_map.csv"
STATE_FILE = LOGS_DIR / "last_run_units.json"
LOG_FILE = LOGS_DIR / "fluctuation_log.txt"
DEMAND_FILE = STRU_DATA_DIR / "electricity_demand.csv"

TAIWAN_TZ = pytz.timezone('Asia/Taipei')
DATA_URL = "https://www.taipower.com.tw/d006/loadGraph/loadGraph/data/genary.json"
DEMAND_URL = "https://www.taipower.com.tw/d006/loadGraph/loadGraph/data/loadpara.json"

# Fuel type mapping from Chinese to English
FUEL_TYPE_MAP = {
    '核能': 'Nuclear',
    '燃煤': 'Coal',
    '汽電共生': 'Co-Gen',
    '民營電廠-燃煤': 'IPP-Coal',
    '燃氣': 'LNG',
    '民營電廠-燃氣': 'IPP-LNG',
    '燃油': 'Oil',
    '輕油': 'Diesel',
    '水力': 'Hydro',
    '風力': 'Wind',
    '太陽能': 'Solar',
    '其它再生能源': 'Other_Renewable',
    '儲能': 'Storage'
}

# All fuel types for CSV columns
ALL_FUEL_TYPES = list(FUEL_TYPE_MAP.values())

# --- Helper Functions ---
def ensure_directories():
    """Create necessary directories if they don't exist."""
    STRU_DATA_DIR.mkdir(parents=True, exist_ok=True)
    LOGS_DIR.mkdir(parents=True, exist_ok=True)
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)

def sanitize_name(name):
    """Remove content within parentheses and sanitize invalid characters."""
    name_without_parentheses = re.sub(r'\(.*\)', '', name)
    return re.sub(r'[\\/*?:"<>|]', '_', name_without_parentheses).strip()

def infer_region_from_name(unit_name):
    """Infer region based on keywords in unit name."""
    region_keywords = {
        'North': ['林口', '大潭', '新桃', '通霄', '協和', '石門', '翡翠', '桂山', '觀音', '龍潭', '北部'],
        'Central': ['台中', '大甲溪', '明潭', '彰工', '中港', '竹南', '苗栗', '雲林', '麥寮', '中部', '彰'],
        'South': ['興達', '大林', '南部', '核三', '曾文', '嘉義', '台南', '高雄', '永安', '屏東'],
        'East': ['和平', '花蓮', '蘭陽', '卑南', '立霧', '東部'], 
        'Islands': ['澎湖', '金門', '馬祖', '塔山', '離島'],
        'Other': ['汽電共生', '其他台電自有', '其他購電太陽能', '其他購電風力', '購買地熱', '台電自有地熱', '生質能']
    }
    for region, keywords in region_keywords.items():
        if any(kw in str(unit_name) for kw in keywords): 
            return region
    return None

def load_plant_mapping():
    """Load plant to region mapping from CSV file."""
    if PLANT_MAP_FILE.exists():
        try:
            df_map = pd.read_csv(PLANT_MAP_FILE)
            # Clean any leading/trailing spaces from region names
            df_map['REGION'] = df_map['REGION'].str.strip()
            df_map['UNIT_NAME'] = df_map['UNIT_NAME'].str.strip()
            return dict(zip(df_map['UNIT_NAME'], df_map['REGION']))
        except Exception as e:
            print(f"❌ ERROR loading plant mapping: {e}")
    return {}

def fetch_generation_data():
    """Fetch power generation data from Taipower API."""
    print(f"   📡 Fetching generation data...")
    timestamp_suffix = int(time.time())
    full_url = f"{DATA_URL}?_={timestamp_suffix}"
    
    try:
        resp = requests.get(full_url, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        
        # Get the data array
        live_data = data.get('aaData', [])
        if not live_data:
            print("❌ No aaData found in API response")
            return None, None
        
        # Process the raw data (same logic as original pipeline)
        records = []
        fuel_map = {
            '太陽能': 'Solar',
            '風力': 'Wind', 
            '燃煤': 'Coal',
            '燃氣': 'LNG',
            '水力': 'Hydro',
            '核能': 'Nuclear',
            '汽電共生': 'Co-Gen',
            '民營電廠-燃煤': 'IPP-Coal',
            '民營電廠-燃氣': 'IPP-LNG',
            '燃油': 'Oil',
            '輕油': 'Diesel',
            '其它再生能源': 'Other_Renewable',
            '儲能': 'Storage',
            # Also map the full Chinese names that include English
            '太陽能(Solar)': 'Solar',
            '風力(Wind)': 'Wind',
            '燃煤(Coal)': 'Coal', 
            '燃氣(LNG)': 'LNG',
            '水力(Hydro)': 'Hydro',
            '核能(Nuclear)': 'Nuclear',
            '汽電共生(Co-Gen)': 'Co-Gen',
            '民營電廠-燃煤(IPP-Coal)': 'IPP-Coal',
            '民營電廠-燃氣(IPP-LNG)': 'IPP-LNG',
            '燃油(Oil)': 'Oil',
            '輕油(Diesel)': 'Diesel',
            '其它再生能源(Other Renewable Energy)': 'Other_Renewable',
            '儲能(Energy Storage System)': 'Storage'
        }
        
        for row in live_data:
            if len(row) < 5 or '小計' in row[2]:
                continue
                
            unit_name = row[2].strip()
            net_p_str = str(row[4]).replace(',', '')
            
            # Extract fuel type from HTML
            match = re.search(r'<b>(.*?)</b>', row[0])
            if not match or not unit_name or 'Load' in match.group(1):
                continue
                
            fuel_type_zh = match.group(1)
            fuel_type = fuel_map.get(fuel_type_zh, fuel_type_zh)
            
            # Parse power value (same logic as original)
            net_p = float(net_p_str) if re.match(r'^-?\d+(\.\d+)?$', net_p_str) else None
            
            # Only include records with valid power values
            if net_p is not None:
                records.append({
                    'UNIT_NAME': sanitize_name(unit_name),
                    'FUEL_TYPE': fuel_type,
                    'FUEL_TYPE_ZH': fuel_type_zh,
                    'NET_P': net_p
                })
        
        if not records:
            print("❌ No valid generator records found")
            return None, None
        
        df = pd.DataFrame(records)
        
        # Debug: Print fuel types found
        print(f"   -> Fetched data for {len(records)} active power plant units.")
        print(f"   -> Fuel types found: {df['FUEL_TYPE'].value_counts().to_dict()}")
        
        # Use current time rounded to 10 minutes
        current_time = datetime.now(TAIWAN_TZ)
        effective_minute = (current_time.minute // 10) * 10
        update_dt = current_time.replace(minute=effective_minute, second=0, microsecond=0)
        
        df['DATETIME'] = update_dt
        return df, update_dt
        
    except Exception as e:
        print(f"❌ ERROR fetching generation data: {e}")
        return None, None

def fetch_demand_data(timestamp):
    """Fetch electricity demand data."""
    print(f"   📡 Fetching demand data...")
    try:
        timestamp_suffix = int(time.time())
        demand_url_with_bust = f"{DEMAND_URL}?_={timestamp_suffix}"
        
        resp = requests.get(demand_url_with_bust, timeout=20)
        resp.raise_for_status()
        demand_data = resp.json()
        
        # Check structure (same as original)
        if not demand_data.get('records') or not isinstance(demand_data['records'], list) or not demand_data['records']:
            print("  -> WARNING: 'records' array not found or is empty in demand data. Skipping.")
            return
            
        current_load_str = demand_data['records'][0].get('curr_load')
        
        if not current_load_str:
            print("  -> WARNING: 'curr_load' key not found in demand data records. Skipping.")
            return
            
        current_load_mw = float(current_load_str.replace(',', ''))
        
        # Save to CSV
        demand_df = pd.DataFrame([{
            'DATETIME': timestamp,
            'DEMAND_MW': current_load_mw
        }])
        
        # Append new data directly (same as original)
        demand_df.to_csv(DEMAND_FILE, mode='a', header=not DEMAND_FILE.exists(), index=False, encoding='utf-8-sig')
        print(f"   -> Saved current demand ({current_load_mw} MW) to {DEMAND_FILE.name}.")
            
    except Exception as e:
        print(f"  -> WARNING: Failed to fetch or process demand data: {e}")

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

def update_regional_data(df_generation, timestamp):
    """Update regional CSV files with generation data."""
    # Load plant mapping
    plant_map = load_plant_mapping()
    
    # Assign regions
    df_generation['REGION'] = df_generation['UNIT_NAME'].map(plant_map)
    
    # Use inference for unmapped plants
    unmapped_mask = df_generation['REGION'].isna()
    df_generation.loc[unmapped_mask, 'REGION'] = df_generation.loc[unmapped_mask, 'UNIT_NAME'].apply(infer_region_from_name)
    
    # Default to 'Other' for still unmapped
    df_generation['REGION'] = df_generation['REGION'].fillna('Other')
    
    # Clean up region names - remove leading/trailing spaces  
    df_generation['REGION'] = df_generation['REGION'].str.strip()
    
    # Also clean unit names to ensure consistent mapping
    df_generation['UNIT_NAME'] = df_generation['UNIT_NAME'].str.strip()
    
    # Debug: Print region assignment and check for East specifically
    print(f"   -> Region distribution: {df_generation['REGION'].value_counts().to_dict()}")
    
    # Check for any remaining problematic regions and consolidate
    unique_regions = df_generation['REGION'].unique()
    problematic_regions = [r for r in unique_regions if r != r.strip()]
    if problematic_regions:
        print(f"   -> WARNING: Found regions with spaces: {problematic_regions}")
        print(f"   -> Consolidating spaced regions...")
        
        # Fix any remaining spaced regions by mapping them to clean versions
        region_fixes = {}
        for region in unique_regions:
            cleaned = region.strip()
            if region != cleaned:
                region_fixes[region] = cleaned
        
        # Apply fixes
        for old_region, new_region in region_fixes.items():
            df_generation.loc[df_generation['REGION'] == old_region, 'REGION'] = new_region
            print(f"   -> Fixed: '{old_region}' -> '{new_region}'")
    
    # Debug East region specifically
    east_data = df_generation[df_generation['REGION'] == 'East']
    if not east_data.empty:
        print(f"   -> East region units: {len(east_data)}")
        print(f"   -> East fuel types: {east_data['FUEL_TYPE'].value_counts().to_dict()}")
        print(f"   -> East total power: {east_data['NET_P'].sum()} MW")
    else:
        print("   -> No East region data found!")
    
    # Group by region and fuel type
    regional_summary = df_generation.groupby(['REGION', 'FUEL_TYPE'])['NET_P'].sum().reset_index()
    
    # Debug: Print regional summary
    print(f"   -> Regional fuel summary:")
    for _, row in regional_summary.iterrows():
        print(f"      {row['REGION']} - {row['FUEL_TYPE']}: {row['NET_P']} MW")
    
    # Process each region
    for region in regional_summary['REGION'].unique():
        csv_path = STRU_DATA_DIR / f"{region}.csv"
        region_data = regional_summary[regional_summary['REGION'] == region]
        
        # Debug East region specifically
        if region == 'East':
            print(f"   -> Processing East region CSV...")
            print(f"   -> East region_data:")
            for _, row in region_data.iterrows():
                print(f"      {row['FUEL_TYPE']}: {row['NET_P']} MW")
        
        # Create row with timestamp and fuel columns
        row_data = {'Timestamp': timestamp}
        
        # Add fuel type columns - need to map from Chinese+English to English
        fuel_type_reverse_map = {
            'Solar': ['Solar', '太陽能(Solar)'],
            'Wind': ['Wind', '風力(Wind)'],
            'Coal': ['Coal', '燃煤(Coal)'],
            'LNG': ['LNG', '燃氣(LNG)'],
            'Hydro': ['Hydro', '水力(Hydro)'],
            'Nuclear': ['Nuclear', '核能(Nuclear)'],
            'Co-Gen': ['Co-Gen', '汽電共生(Co-Gen)'],
            'IPP-Coal': ['IPP-Coal', '民營電廠-燃煤(IPP-Coal)'],
            'IPP-LNG': ['IPP-LNG', '民營電廠-燃氣(IPP-LNG)'],
            'Oil': ['Oil', '燃油(Oil)'],
            'Diesel': ['Diesel', '輕油(Diesel)'],
            'Other_Renewable': ['Other_Renewable', '其它再生能源(Other Renewable Energy)'],
            'Storage': ['Storage', '儲能(Energy Storage System)']
        }
        
        for fuel_type in ALL_FUEL_TYPES:
            # Find matching fuel types from both English and Chinese names
            possible_names = fuel_type_reverse_map.get(fuel_type, [fuel_type])
            fuel_value = 0
            for name in possible_names:
                fuel_value += region_data[region_data['FUEL_TYPE'] == name]['NET_P'].sum()
            row_data[fuel_type] = fuel_value
        
        # Calculate total generation
        row_data['Total_Generation'] = sum(row_data[ft] for ft in ALL_FUEL_TYPES)
        
        # Initialize weather columns as null
        row_data['AirTemperature'] = None
        row_data['WindSpeed'] = None
        row_data['SunshineDuration'] = None
        
        # Check if file exists and if timestamp already exists
        if csv_path.exists():
            try:
                existing_df = read_csv_with_lock(csv_path)
                existing_df['Timestamp'] = pd.to_datetime(existing_df['Timestamp'])
                
                if timestamp in existing_df['Timestamp'].values:
                    # Update existing row - preserve weather data if exists
                    idx = existing_df[existing_df['Timestamp'] == timestamp].index[0]
                    for col in ALL_FUEL_TYPES + ['Total_Generation']:
                        existing_df.loc[idx, col] = row_data[col]
                    write_csv_with_lock(existing_df, csv_path)
                    print(f"   ✅ Updated generation data for {region}")
                else:
                    # Append new row
                    new_df = pd.DataFrame([row_data])
                    write_csv_with_lock(new_df, csv_path, mode='a')
                    print(f"   ✅ Appended generation data for {region}")
            except Exception as e:
                print(f"   ❌ ERROR updating {region}: {e}")
                # Create new file if read fails
                new_df = pd.DataFrame([row_data])
                write_csv_with_lock(new_df, csv_path)
                print(f"   ✅ Created new file for {region}")
        else:
            # Create new file
            new_df = pd.DataFrame([row_data])
            write_csv_with_lock(new_df, csv_path)
            print(f"   ✅ Created new file for {region}")

def log_fluctuations(current_units):
    """Log plant fluctuations between runs."""
    if STATE_FILE.exists():
        try:
            with open(STATE_FILE, 'r') as f:
                previous_units = set(json.load(f))
        except:
            previous_units = set()
    else:
        previous_units = set()
    
    added = current_units - previous_units
    removed = previous_units - current_units
    
    if added or removed:
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(f"\n--- Fluctuation Report @ {datetime.now(TAIWAN_TZ).strftime('%Y-%m-%d %H:%M:%S')} ---\n")
            if added:
                f.write(f"➕ ADDED ({len(added)}): {', '.join(sorted(added))}\n")
            if removed:
                f.write(f"➖ REMOVED ({len(removed)}): {', '.join(sorted(removed))}\n")
    
    # Save current state
    with open(STATE_FILE, 'w') as f:
        json.dump(list(current_units), f, ensure_ascii=False, indent=2)

def main():
    """Main execution function."""
    run_time = datetime.now(TAIWAN_TZ)
    print(f"\n{'='*60}")
    print(f"[{run_time.strftime('%Y-%m-%d %H:%M:%S')}] Starting integrated pipeline...")
    
    # Ensure directories exist
    ensure_directories()
    
    # Fetch generation data
    df_generation, timestamp = fetch_generation_data()
    if df_generation is None:
        print("❌ Failed to fetch generation data. Exiting.")
        return
    
    print(f"   ✅ Fetched {len(df_generation)} generation units")
    print(f"   ✅ Data timestamp: {timestamp}")
    
    # Update regional CSV files
    update_regional_data(df_generation, timestamp)
    
    # Fetch demand data
    fetch_demand_data(timestamp)
    
    # Log fluctuations
    current_units = set(df_generation['UNIT_NAME'].unique())
    log_fluctuations(current_units)
    
    print(f"[{datetime.now(TAIWAN_TZ).strftime('%Y-%m-%d %H:%M:%S')}] Pipeline completed successfully!")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    main()