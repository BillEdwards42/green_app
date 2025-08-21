# ==============================================================================
# SCRIPT: live_pipeline_tampered.py
# PURPOSE:
#   - A separate version for testing with a specific plant-to-region map.
#   - Data is stored in the 'tampered_data' directory.
# ==============================================================================
import pandas as pd
from pathlib import Path
import sys, re, json, requests, pytz, time, fcntl
from datetime import datetime, timedelta
import numpy as np

# --- Configuration ---
BASE_DIR = Path(__file__).parent
STRU_DATA_DIR = BASE_DIR / "tampered_data" # Correctly points to new data directory
CONFIG_DIR = BASE_DIR / "config"
LOGS_DIR = BASE_DIR / "logs"

PLANT_MAP_FILE = CONFIG_DIR / "plant_to_region_map_tampered.csv"
# --- MODIFIED LINES ---
# Give this version its own unique state and log files to prevent conflicts
STATE_FILE = LOGS_DIR / "last_run_units_tampered.json"
LOG_FILE = LOGS_DIR / "fluctuation_log_tampered.txt"
# --- END MODIFIED LINES ---
DEMAND_FILE = STRU_DATA_DIR / "electricity_demand.csv"

TAIWAN_TZ = pytz.timezone('Asia/Taipei')
DATA_URL = "https://www.taipower.com.tw/d006/loadGraph/loadGraph/data/genary.json"
DEMAND_URL = "https://www.taipower.com.tw/d006/loadGraph/loadGraph/data/loadpara.json"

# (The rest of the script is identical to the one you provided and is correct)
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
        'North': ['林口', '大潭', '新桃', '通霄', '協和', '石門', '翡翠', '桂山', '觀音', '龍潭', '北部', '桃園', '國光', '協和', '海湖', '新桃', '松山'],
        'Central': ['台中', '大甲溪', '明潭', '彰工', '中港', '竹南', '苗栗', '雲林', '麥寮', '中部', '彰', '中能', '水里'],
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
        
        live_data = data.get('aaData', [])
        if not live_data:
            print("❌ No aaData found in API response")
            return None, None
        
        records = []
        fuel_map = {
            '太陽能': 'Solar', '風力': 'Wind', '燃煤': 'Coal', '燃氣': 'LNG', '水力': 'Hydro',
            '核能': 'Nuclear', '汽電共生': 'Co-Gen', '民營電廠-燃煤': 'IPP-Coal', '民營電廠-燃氣': 'IPP-LNG',
            '燃油': 'Oil', '輕油': 'Diesel', '其它再生能源': 'Other_Renewable', '儲能': 'Storage',
            '太陽能(Solar)': 'Solar', '風力(Wind)': 'Wind', '燃煤(Coal)': 'Coal', '燃氣(LNG)': 'LNG',
            '水力(Hydro)': 'Hydro', '核能(Nuclear)': 'Nuclear', '汽電共生(Co-Gen)': 'Co-Gen',
            '民營電廠-燃煤(IPP-Coal)': 'IPP-Coal', '民營電廠-燃氣(IPP-LNG)': 'IPP-LNG', '燃油(Oil)': 'Oil',
            '輕油(Diesel)': 'Diesel', '其它再生能源(Other Renewable Energy)': 'Other_Renewable',
            '儲能(Energy Storage System)': 'Storage'
        }
        
        for row in live_data:
            if len(row) < 5 or '小計' in row[2]:
                continue
                
            unit_name = row[2].strip()
            net_p_str = str(row[4]).replace(',', '')
            
            match = re.search(r'<b>(.*?)</b>', row[0])
            if not match or not unit_name or 'Load' in match.group(1):
                continue
                
            fuel_type_zh = match.group(1)
            fuel_type = fuel_map.get(fuel_type_zh, fuel_type_zh)
            
            net_p = float(net_p_str) if re.match(r'^-?\d+(\.\d+)?$', net_p_str) else None
            
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
        
        print(f"   -> Fetched data for {len(records)} active power plant units.")
        print(f"   -> Fuel types found: {df['FUEL_TYPE'].value_counts().to_dict()}")
        
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
        
        if not demand_data.get('records') or not isinstance(demand_data['records'], list) or not demand_data['records']:
            print("  -> WARNING: 'records' array not found or is empty in demand data. Skipping.")
            return
            
        current_load_str = demand_data['records'][0].get('curr_load')
        
        if not current_load_str:
            print("  -> WARNING: 'curr_load' key not found in demand data records. Skipping.")
            return
            
        current_load_mw = float(current_load_str.replace(',', ''))
        
        demand_df = pd.DataFrame([{'DATETIME': timestamp, 'DEMAND_MW': current_load_mw}])
        
        demand_df.to_csv(DEMAND_FILE, mode='a', header=not DEMAND_FILE.exists(), index=False, encoding='utf-8-sig')
        print(f"   -> Saved current demand ({current_load_mw} MW) to {DEMAND_FILE.name}.")
            
    except Exception as e:
        print(f"  -> WARNING: Failed to fetch or process demand data: {e}")

def read_csv_with_lock(filepath):
    """Read CSV file with file locking."""
    with open(filepath, 'r') as f:
        fcntl.flock(f.fileno(), fcntl.LOCK_SH)
        try:
            return pd.read_csv(f)
        finally:
            fcntl.flock(f.fileno(), fcntl.LOCK_UN)

def write_csv_with_lock(df, filepath, mode='w'):
    """Write CSV file with file locking."""
    with open(filepath, mode) as f:
        fcntl.flock(f.fileno(), fcntl.LOCK_EX)
        try:
            df.to_csv(f, index=False, header=(mode != 'a'))
        finally:
            fcntl.flock(f.fileno(), fcntl.LOCK_UN)

def update_regional_data(df_generation, timestamp):
    """Update regional CSV files with generation data."""
    plant_map = load_plant_mapping()
    
    df_generation['REGION'] = df_generation['UNIT_NAME'].map(plant_map)
    
    unmapped_mask = df_generation['REGION'].isna()
    df_generation.loc[unmapped_mask, 'REGION'] = df_generation.loc[unmapped_mask, 'UNIT_NAME'].apply(infer_region_from_name)
    
    df_generation['REGION'] = df_generation['REGION'].fillna('Other')

    df_generation['REGION'] = df_generation['REGION'].str.strip()
    df_generation['UNIT_NAME'] = df_generation['UNIT_NAME'].str.strip()
    
    print(f"   -> Region distribution: {df_generation['REGION'].value_counts().to_dict()}")
    
    regional_summary = df_generation.groupby(['REGION', 'FUEL_TYPE'])['NET_P'].sum().reset_index()
    
    print(f"   -> Regional fuel summary:")
    for _, row in regional_summary.iterrows():
        print(f"      {row['REGION']:<8}- {row['FUEL_TYPE']:<16}: {row['NET_P']: >7.1f} MW")
    
    for region in df_generation['REGION'].unique():
        csv_path = STRU_DATA_DIR / f"{region}.csv"
        region_data = regional_summary[regional_summary['REGION'] == region]
        
        row_data = {'Timestamp': timestamp}
        
        for fuel_type in ALL_FUEL_TYPES:
            row_data[fuel_type] = region_data[region_data['FUEL_TYPE'] == fuel_type]['NET_P'].sum()
        
        row_data['Total_Generation'] = sum(row_data[ft] for ft in ALL_FUEL_TYPES)
        
        row_data['AirTemperature'] = None
        row_data['WindSpeed'] = None
        row_data['SunshineDuration'] = None
        
        new_df = pd.DataFrame([row_data])

        if csv_path.exists():
            try:
                existing_df = read_csv_with_lock(csv_path)
                existing_df['Timestamp'] = pd.to_datetime(existing_df['Timestamp'])
                
                if timestamp in existing_df['Timestamp'].values:
                    idx = existing_df[existing_df['Timestamp'] == timestamp].index[0]
                    for col in ALL_FUEL_TYPES + ['Total_Generation']:
                        existing_df.loc[idx, col] = new_df.loc[0, col]
                    write_csv_with_lock(existing_df, csv_path)
                    print(f"   ✅ Updated generation data for {region}")
                else:
                    write_csv_with_lock(new_df, csv_path, mode='a')
                    print(f"   ✅ Appended generation data for {region}")
            except Exception as e:
                print(f"   ❌ ERROR updating {region}: {e}")
                write_csv_with_lock(new_df, csv_path)
                print(f"   ✅ Created new file for {region} after error.")
        else:
            write_csv_with_lock(new_df, csv_path)
            print(f"   ✅ Created new file for {region}")

def log_fluctuations(df_generation):
    """
    Logs plant fluctuations with details (region, power).
    If no changes, logs a compact status line.
    The state file now stores a dictionary of unit details for richer comparison.
    """
    run_time = datetime.now(TAIWAN_TZ)
    
    previous_units_data = {}
    if STATE_FILE.exists():
        try:
            with open(STATE_FILE, 'r', encoding='utf-8') as f:
                previous_units_data = json.load(f)
        except json.JSONDecodeError:
            print(f"   -> WARNING: Could not read {STATE_FILE.name}. Assuming fresh start.")
            previous_units_data = {}
    
    previous_names = set(previous_units_data.keys())

    agg_df = df_generation.groupby(['UNIT_NAME', 'REGION'], as_index=False)['NET_P'].sum()
    current_units_data = agg_df.set_index('UNIT_NAME')[['REGION', 'NET_P']].to_dict('index')
    
    current_names = set(current_units_data.keys())
    
    added_names = current_names - previous_names
    removed_names = previous_names - current_names
    
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        if not added_names and not removed_names:
            f.write(f"[{run_time.strftime('%Y-%m-%d %H:%M')}] run no change\n")
        else:
            f.write(f"\n--- Fluctuation Report @ {run_time.strftime('%Y-%m-%d %H:%M:%S')} ---\n")
            if added_names:
                for name in sorted(list(added_names)):
                    details = current_units_data[name]
                    region = details.get('REGION', 'N/A')
                    net_p = details.get('NET_P', 0.0)
                    f.write(f"➕ ADDED: {name:<20} | Region: {region:<8} | Power: {net_p: >6.1f} MW\n")
            if removed_names:
                for name in sorted(list(removed_names)):
                    details = previous_units_data.get(name, {}) 
                    region = details.get('REGION', 'N/A')
                    last_net_p = details.get('NET_P', 0.0)
                    f.write(f"➖ GONE:  {name:<20} | Region: {region:<8} | Last Power: {last_net_p: >6.1f} MW\n")

    with open(STATE_FILE, 'w', encoding='utf-8') as f:
        json.dump(current_units_data, f, ensure_ascii=False, indent=2)

def main():
    """Main execution function."""
    run_time = datetime.now(TAIWAN_TZ)
    print(f"\n{'='*60}")
    print(f"[{run_time.strftime('%Y-%m-%d %H:%M:%S')}] Starting integrated pipeline...")
    
    ensure_directories()
    
    df_generation, timestamp = fetch_generation_data()
    if df_generation is None:
        print("❌ Failed to fetch generation data. Exiting.")
        return
    
    print(f"   ✅ Fetched {len(df_generation)} generation units")
    print(f"   ✅ Data timestamp: {timestamp}")
    
    update_regional_data(df_generation, timestamp)
    
    fetch_demand_data(timestamp)
    
    log_fluctuations(df_generation)
    
    print(f"[{datetime.now(TAIWAN_TZ).strftime('%Y-%m-%d %H:%M:%S')}] Pipeline completed successfully!")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    main()