#!/usr/bin/env python3
# ==============================================================================
# SCRIPT: generator_tracking.py
# PURPOSE:
#   - Fetches power generation data from Taipower every 10 minutes
#   - Tracks each individual generator as a separate column
#   - Handles dynamic addition/removal of generators
#   - Outputs a single CSV with all generators
# ==============================================================================

import pandas as pd
from pathlib import Path
import sys, re, json, requests, pytz, time, fcntl
from datetime import datetime, timedelta
import numpy as np

# --- Configuration ---
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "generator_data"
LOGS_DIR = BASE_DIR / "logs"

# Main output file
GENERATORS_FILE = DATA_DIR / "all_generators.csv"
LOG_FILE = LOGS_DIR / "generator_tracking.log"

TAIWAN_TZ = pytz.timezone('Asia/Taipei')
DATA_URL = "https://www.taipower.com.tw/d006/loadGraph/loadGraph/data/genary.json"

# --- Helper Functions ---
def ensure_directories():
    """Create necessary directories if they don't exist."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    LOGS_DIR.mkdir(parents=True, exist_ok=True)

def sanitize_name(name):
    """Remove content within parentheses and sanitize invalid characters."""
    name_without_parentheses = re.sub(r'\(.*\)', '', name)
    return re.sub(r'[\\/*?:"<>|]', '_', name_without_parentheses).strip()

def log_message(message):
    """Log message with timestamp."""
    timestamp = datetime.now(TAIWAN_TZ).strftime('%Y-%m-%d %H:%M:%S')
    with open(LOG_FILE, 'a', encoding='utf-8') as f:
        f.write(f"[{timestamp}] {message}\n")
    print(f"   {message}")

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


def fetch_generation_data():
    """Fetch power generation data from Taipower API."""
    log_message("Fetching generation data from Taipower...")
    timestamp_suffix = int(time.time())
    full_url = f"{DATA_URL}?_={timestamp_suffix}"
    
    try:
        resp = requests.get(full_url, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        
        # Get the data array
        live_data = data.get('aaData', [])
        if not live_data:
            log_message("ERROR: No aaData found in API response")
            return None, None
        
        # Process the raw data
        generators = {}
        
        for row in live_data:
            if len(row) < 5 or '小計' in row[2]:
                continue
                
            unit_name = row[2].strip()
            net_p_str = str(row[4]).replace(',', '')
            
            # Extract fuel type from HTML (for logging purposes)
            match = re.search(r'<b>(.*?)</b>', row[0])
            if not match or not unit_name or 'Load' in match.group(1):
                continue
            
            # Parse power value
            try:
                net_p = float(net_p_str) if re.match(r'^-?\d+(\.\d+)?$', net_p_str) else 0.0
            except:
                net_p = 0.0
            
            # Use sanitized name as key
            generator_key = sanitize_name(unit_name)
            generators[generator_key] = net_p
        
        if not generators:
            log_message("ERROR: No valid generator records found")
            return None, None
        
        log_message(f"Fetched data for {len(generators)} active generators")
        
        # Use current time rounded to 10 minutes
        current_time = datetime.now(TAIWAN_TZ)
        effective_minute = (current_time.minute // 10) * 10
        update_dt = current_time.replace(minute=effective_minute, second=0, microsecond=0)
        
        return generators, update_dt
        
    except Exception as e:
        log_message(f"ERROR fetching generation data: {e}")
        return None, None

def update_generator_data(current_generators, timestamp):
    """Update the generator CSV file with new data."""
    # Prepare row data for the new timestamp
    row_data = {'Timestamp': timestamp}
    
    # Update or create CSV file
    if GENERATORS_FILE.exists():
        try:
            # Read existing data
            existing_df = read_csv_with_lock(GENERATORS_FILE)
            existing_df['Timestamp'] = pd.to_datetime(existing_df['Timestamp'])
            
            # Check if this timestamp already exists
            if pd.Timestamp(timestamp) in existing_df['Timestamp'].values:
                log_message(f"Timestamp {timestamp} already exists, skipping update")
                return
            
            # Get all existing generator columns (excluding Timestamp and Total_Generation)
            existing_generators = [col for col in existing_df.columns if col not in ['Timestamp', 'Total_Generation']]
            
            # Add existing generators to row_data (0 if not currently active)
            for generator in existing_generators:
                row_data[generator] = current_generators.get(generator, 0.0)
            
            # Add any new generators
            new_generators = set(current_generators.keys()) - set(existing_generators)
            if new_generators:
                log_message(f"Found {len(new_generators)} new generators: {', '.join(sorted(new_generators))}")
                # Add new generators to existing dataframe with 0 for all previous rows
                for new_gen in new_generators:
                    existing_df[new_gen] = 0.0
                    row_data[new_gen] = current_generators[new_gen]
            
            # Check for removed generators
            inactive_generators = [gen for gen in existing_generators if gen not in current_generators]
            if inactive_generators:
                log_message(f"Generators not reporting ({len(inactive_generators)}): {', '.join(sorted(inactive_generators)[:5])}...")
            
            # Add total generation column
            row_data['Total_Generation'] = sum(current_generators.values())
            
            # Create new row dataframe with all columns
            all_columns = ['Timestamp'] + sorted([col for col in existing_df.columns if col not in ['Timestamp', 'Total_Generation']]) + ['Total_Generation']
            new_row_df = pd.DataFrame([row_data])
            
            # Ensure all columns exist in new row
            for col in all_columns:
                if col not in new_row_df.columns:
                    new_row_df[col] = 0.0
            
            # Reorder columns to match
            new_row_df = new_row_df[all_columns]
            
            # If we added new columns, we need to rewrite the entire file
            if new_generators:
                # Append the new row to existing dataframe
                existing_df = pd.concat([existing_df, new_row_df], ignore_index=True)
                # Write the entire dataframe
                write_csv_with_lock(existing_df, GENERATORS_FILE)
            else:
                # No new columns, just append the new row
                write_csv_with_lock(new_row_df, GENERATORS_FILE, mode='a')
            
            log_message(f"Appended data: {len(current_generators)} active generators, {len(all_columns)-2} total columns")
            
        except Exception as e:
            log_message(f"ERROR updating existing file: {e}")
            # If error, try to continue by creating row with current generators
            for gen, value in current_generators.items():
                row_data[gen] = value
            row_data['Total_Generation'] = sum(current_generators.values())
            new_df = pd.DataFrame([row_data])
            # Reorder columns: Timestamp, sorted generators, Total_Generation
            cols = ['Timestamp'] + sorted([c for c in new_df.columns if c not in ['Timestamp', 'Total_Generation']]) + ['Total_Generation']
            new_df = new_df[cols]
            write_csv_with_lock(new_df, GENERATORS_FILE)
            log_message("Created new generator tracking file")
    else:
        # Create new file with current generators
        for gen, value in current_generators.items():
            row_data[gen] = value
        row_data['Total_Generation'] = sum(current_generators.values())
        
        new_df = pd.DataFrame([row_data])
        # Reorder columns: Timestamp, sorted generators, Total_Generation
        cols = ['Timestamp'] + sorted([c for c in new_df.columns if c not in ['Timestamp', 'Total_Generation']]) + ['Total_Generation']
        new_df = new_df[cols]
        
        write_csv_with_lock(new_df, GENERATORS_FILE)
        log_message(f"Created new generator tracking file with {len(current_generators)} generators")

def main():
    """Main execution function."""
    run_time = datetime.now(TAIWAN_TZ)
    print(f"\n{'='*60}")
    print(f"[{run_time.strftime('%Y-%m-%d %H:%M:%S')}] Starting generator tracking...")
    
    # Ensure directories exist
    ensure_directories()
    
    # Fetch generation data
    current_generators, timestamp = fetch_generation_data()
    if current_generators is None:
        log_message("Failed to fetch generation data. Exiting.")
        return
    
    log_message(f"Data timestamp: {timestamp}")
    
    # Update generator tracking file
    update_generator_data(current_generators, timestamp)
    
    # Summary statistics
    total_generation = sum(current_generators.values())
    log_message(f"Total generation: {total_generation:.1f} MW")
    log_message(f"Active generators: {len(current_generators)}")
    
    print(f"[{datetime.now(TAIWAN_TZ).strftime('%Y-%m-%d %H:%M:%S')}] Generator tracking completed!")
    print(f"{'='*60}\n")

if __name__ == "__main__":
    main()