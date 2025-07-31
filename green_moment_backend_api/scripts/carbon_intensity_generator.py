"""
Carbon Intensity Generator
Main script that runs every X9 minute to generate carbon intensity data
Fetches directly from Taipower and CWA APIs
"""
import os
import sys
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
import csv
import schedule
import time
import argparse
import requests
import re
import pytz
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.cache_manager import CacheManager
from scripts.carbon_calculator import CarbonCalculator
from scripts.ml_inference import MLInferenceService

# Load environment variables
load_dotenv()

# API Configuration
TAIPOWER_API_URL = "https://www.taipower.com.tw/d006/loadGraph/loadGraph/data/genary.json"
CWA_API_URL = "https://opendata.cwa.gov.tw/api/v1/rest/datastore/O-A0003-001"
CWA_API_KEY = os.getenv("CWA_API_KEY", "CWA-498C56D4-B151-4539-992D-B2CB97042454")
TAIWAN_TZ = pytz.timezone('Asia/Taipei')

# Weather stations by region
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
    ]
}

# Plant to region mapping keywords
REGION_KEYWORDS = {
    'North': ['林口', '大潭', '新桃', '通霄', '協和', '石門', '翡翠', '桂山', '觀音', '龍潭', '北部'],
    'Central': ['台中', '大甲溪', '明潭', '彰工', '中港', '竹南', '苗栗', '雲林', '麥寮', '中部', '彰'],
    'South': ['興達', '大林', '南部', '核三', '曾文', '嘉義', '台南', '高雄', '永安', '屏東'],
    'East': ['和平', '花蓮', '蘭陽', '卑南', '立霧', '東部'], 
    'Other': ['汽電共生', '其他台電自有', '其他購電太陽能', '其他購電風力', '購買地熱', '台電自有地熱', '生質能']
}

# Fuel type mapping
FUEL_TYPE_MAP = {
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
    # Also map full Chinese names that include English
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


class CarbonIntensityGenerator:
    def __init__(self):
        self.output_path = Path("data/carbon_intensity.json")
        self.csv_log_path = Path("logs/actual_carbon_intensity.csv")
        self.fluctuation_log_path = Path("logs/fluctuation_log.txt")
        self.weather_log_path = Path("logs/weather_analysis_log.txt")
        
        # Initialize services
        self.cache_manager = CacheManager()
        self.carbon_calculator = CarbonCalculator()
        self.ml_service = MLInferenceService()
        
        # Ensure directories exist
        os.makedirs("data", exist_ok=True)
        os.makedirs("logs", exist_ok=True)
        
        # Track previous generators for fluctuation logging
        self.previous_generators = self._load_previous_generators()
    
    def _load_previous_generators(self) -> dict:
        """Load previous generator state from fluctuation log"""
        # This would parse the last entry from fluctuation log
        # For now, return empty dict
        return {}
    
    def infer_region_from_name(self, unit_name):
        """Infer region based on keywords in unit name."""
        for region, keywords in REGION_KEYWORDS.items():
            if any(kw in str(unit_name) for kw in keywords):
                return region
        return 'Other'  # Default to Other if no match
    
    def fetch_generation_data(self):
        """Fetch power generation data from Taipower API."""
        print(f"   📡 Fetching generation data from Taipower...")
        timestamp_suffix = int(time.time())
        full_url = f"{TAIPOWER_API_URL}?_={timestamp_suffix}"
        
        try:
            resp = requests.get(full_url, timeout=30)
            resp.raise_for_status()
            data = resp.json()
            
            # Get the data array
            live_data = data.get('aaData', [])
            if not live_data:
                print("❌ No aaData found in API response")
                return None
            
            # Get update time from response
            update_time_str = data.get('更新時間', '')
            if not update_time_str:
                # Use current time rounded down to nearest 10 minutes
                now = datetime.now(TAIWAN_TZ)
                minutes = (now.minute // 10) * 10
                update_time = now.replace(minute=minutes, second=0, microsecond=0)
            else:
                # Parse the update time
                update_time = datetime.strptime(update_time_str, "%Y-%m-%d %H:%M")
                update_time = TAIWAN_TZ.localize(update_time)
            
            # Process data by region
            regional_data = {
                'North': {},
                'Central': {},
                'South': {},
                'East': {},
                'Other': {}
            }
            
            # Store detailed plant data for fluctuation logging
            detailed_plant_data = {}
            
            # Initialize fuel types for each region
            for region in regional_data:
                for fuel in FUEL_TYPE_MAP.values():
                    regional_data[region][fuel] = 0.0
            
            # Process each generator
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
                fuel_type_en = FUEL_TYPE_MAP.get(fuel_type_zh)
                
                if not fuel_type_en:
                    continue
                
                # Parse generation value
                try:
                    generation_mw = float(net_p_str)
                except ValueError:
                    continue
                
                # Determine region
                region = self.infer_region_from_name(unit_name)
                
                # Add to regional total
                regional_data[region][fuel_type_en] += generation_mw
                
                # Store detailed plant info
                detailed_plant_data[unit_name] = {
                    'fuel_type': fuel_type_en,
                    'region': region,
                    'generation': generation_mw
                }
            
            return regional_data, update_time, detailed_plant_data
            
        except Exception as e:
            print(f"❌ Error fetching generation data: {e}")
            return None
    
    def fetch_weather_data(self):
        """Fetch weather data from CWA API."""
        print(f"   📡 Fetching weather data from CWA...")
        params = {"Authorization": CWA_API_KEY}
        
        try:
            response = requests.get(CWA_API_URL, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            
            # Process stations by region
            regional_weather = {}
            stations_data = data.get('records', {}).get('Station', [])
            
            for region, station_names in STATIONS_BY_REGION.items():
                region_values = {
                    'AirTemperature': [],
                    'WindSpeed': [],
                    'SunshineDuration': [],
                    'Precipitation': []
                }
                
                for station in stations_data:
                    if station.get('StationName') in station_names:
                        elements = station.get('WeatherElement', {})
                        
                        # Extract values
                        temp = elements.get('AirTemperature')
                        wind = elements.get('WindSpeed')
                        sun = elements.get('SunshineDuration')
                        precip = elements.get('Now', {}).get('Precipitation')
                        
                        # Add valid values to lists
                        if temp and float(temp) > -90:
                            region_values['AirTemperature'].append(float(temp))
                        if wind and float(wind) >= 0:
                            region_values['WindSpeed'].append(float(wind))
                        if sun and float(sun) >= 0:
                            region_values['SunshineDuration'].append(float(sun))
                        if precip and float(precip) >= 0:
                            region_values['Precipitation'].append(float(precip))
                
                # Calculate averages
                regional_weather[region] = {}
                for metric, values in region_values.items():
                    if values:
                        regional_weather[region][metric] = np.mean(values)
                    else:
                        regional_weather[region][metric] = np.nan
            
            return regional_weather
            
        except Exception as e:
            print(f"❌ Error fetching weather data: {e}")
            return None
    
    def combine_data_for_cache(self, generation_data, weather_data, timestamp):
        """Combine generation and weather data for cache storage."""
        cache_data = {}
        
        for region, fuel_data in generation_data.items():
            cache_entry = {
                'Timestamp': timestamp.isoformat(),
                'cache_timestamp': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            
            # Add fuel generation data
            total_gen = 0
            for fuel, mw in fuel_data.items():
                cache_entry[fuel] = mw
                total_gen += mw
            cache_entry['Total_Generation'] = total_gen
            
            # Add weather data (except for Other region)
            if region != 'Other' and weather_data and region in weather_data:
                for metric, value in weather_data[region].items():
                    cache_entry[metric] = value
            else:
                # No weather for Other region
                cache_entry['AirTemperature'] = np.nan
                cache_entry['WindSpeed'] = np.nan
                cache_entry['SunshineDuration'] = np.nan
                cache_entry['Precipitation'] = np.nan
            
            cache_data[region] = cache_entry
        
        return cache_data
    
    def log_fluctuations(self, detailed_generation_data, timestamp: str):
        """Log generator additions and removals with plant names"""
        current_generators = {}
        
        # Build current state with plant names
        for plant_name, plant_info in detailed_generation_data.items():
            if plant_info['generation'] > 0:
                key = f"{plant_name}_{plant_info['fuel_type']}_{plant_info['region']}"
                current_generators[key] = {
                    'plant_name': plant_name,
                    'region': plant_info['region'],
                    'fuel': plant_info['fuel_type'],
                    'generation': plant_info['generation']
                }
        
        # Compare with previous state
        current_keys = set(current_generators.keys())
        previous_keys = set(self.previous_generators.keys())
        
        added = current_keys - previous_keys
        removed = previous_keys - current_keys
        changed = []
        
        # Check for generation changes in existing plants
        for key in current_keys.intersection(previous_keys):
            curr_gen = current_generators[key]['generation']
            prev_gen = self.previous_generators[key]['generation']
            if abs(curr_gen - prev_gen) > 0.1:  # Threshold to avoid logging tiny changes
                changed.append((key, prev_gen, curr_gen))
        
        # Log changes
        with open(self.fluctuation_log_path, 'a') as f:
            f.write(f"\n{'='*60}\n")
            f.write(f"Timestamp: {timestamp}\n")
            
            if added or removed or changed:
                if added:
                    f.write("\nGenerators ADDED (came online):\n")
                    for key in sorted(added):
                        gen = current_generators[key]
                        f.write(f"  - {gen['plant_name']} ({gen['fuel']}) in {gen['region']}: {gen['generation']:.2f} MW\n")
                
                if removed:
                    f.write("\nGenerators REMOVED (went offline):\n")
                    for key in sorted(removed):
                        gen = self.previous_generators[key]
                        f.write(f"  - {gen['plant_name']} ({gen['fuel']}) in {gen['region']}: {gen['generation']:.2f} MW\n")
                
                if changed:
                    f.write("\nGenerators CHANGED (significant MW change):\n")
                    for key, prev_mw, curr_mw in sorted(changed):
                        gen = current_generators[key]
                        change = curr_mw - prev_mw
                        f.write(f"  - {gen['plant_name']} ({gen['fuel']}) in {gen['region']}: "
                               f"{prev_mw:.2f} → {curr_mw:.2f} MW ({change:+.2f})\n")
            else:
                f.write("Status: COMPLETE - No significant changes in generator status\n")
        
        # Update state
        self.previous_generators = current_generators
    
    def log_weather_analysis(self, weather_data, timestamp: str):
        """Log weather data analysis for each region"""
        with open(self.weather_log_path, 'a') as f:
            f.write(f"\n{'='*60}\n")
            f.write(f"Timestamp: {timestamp}\n")
            f.write("Weather Data Analysis by Region:\n\n")
            
            if weather_data:
                for region, metrics in weather_data.items():
                    f.write(f"{region} Region:\n")
                    for metric, value in metrics.items():
                        if pd.isna(value):
                            f.write(f"  - {metric}: NULL\n")
                        else:
                            f.write(f"  - {metric}: {value:.2f}\n")
                    f.write("\n")
            else:
                f.write("No weather data available\n")
    
    def generate_carbon_intensity(self):
        """Main function to generate carbon intensity data"""
        timestamp = datetime.now()
        timestamp_str = timestamp.strftime('%Y-%m-%d %H:%M:%S')
        
        print(f"\n{'='*60}")
        print(f"Carbon Intensity Generation Started: {timestamp_str}")
        print('='*60)
        
        # Fetch generation data from Taipower
        gen_result = self.fetch_generation_data()
        if not gen_result:
            print("ERROR: Failed to fetch generation data")
            self._write_error_json("Failed to fetch generation data")
            return
        
        generation_data, update_time, detailed_plant_data = gen_result
        
        # Fetch weather data from CWA
        weather_data = self.fetch_weather_data()
        if not weather_data:
            print("WARNING: Weather data unavailable, using NaN values")
        
        # Calculate current carbon intensity
        # Convert generation data to format expected by calculator
        regional_dfs = {}
        for region, fuel_data in generation_data.items():
            df_data = {fuel: [mw] for fuel, mw in fuel_data.items()}
            regional_dfs[region] = pd.DataFrame(df_data)
        
        current_intensity, current_details = self.carbon_calculator.calculate_current_intensity(regional_dfs)
        
        print(f"\nCurrent Carbon Intensity: {current_intensity:.3f} kgCO2e/kWh")
        print(f"Total Generation: {current_details['total_generation_mw']:.2f} MW")
        print(f"Data Timestamp: {update_time}")
        
        # Log current intensity to CSV
        self._log_to_csv(timestamp_str, current_intensity)
        
        # Log fluctuations and weather
        self.log_fluctuations(detailed_plant_data, timestamp_str)
        self.log_weather_analysis(weather_data, timestamp_str)
        
        # Prepare and update cache
        cache_data = self.combine_data_for_cache(generation_data, weather_data, update_time)
        self.cache_manager.add_timestep_data(timestamp_str, cache_data)
        
        # Check cache status
        cache_status = self.cache_manager.get_cache_status()
        print(f"\nCache Status: {cache_status['ready']}")
        for region, status in cache_status['regions'].items():
            print(f"  {region}: {status['count']}/6 timesteps")
        
        # Generate forecast if cache is ready
        forecast_data = None
        if cache_status['ready']:
            print("\nGenerating 24-hour forecast...")
            try:
                forecast_data = self.ml_service.predict_all_regions(self.cache_manager)
                if forecast_data:
                    forecast_intensities = self.carbon_calculator.calculate_forecast_intensity(forecast_data)
                    print(f"Generated {len(forecast_intensities)} forecast points")
            except Exception as e:
                print(f"Error generating forecast: {e}")
        
        # Prepare output JSON
        output = self._prepare_output_json(
            current_intensity, 
            current_details, 
            cache_status, 
            forecast_data,
            update_time
        )
        
        # Convert to app format
        app_output = self._prepare_app_format_json(output)
        
        # Write app format as the main output
        with open(self.output_path, 'w') as f:
            json.dump(app_output, f, indent=2)
        
        # Also save the detailed format for debugging
        debug_path = self.output_path.parent / "carbon_intensity_debug.json"
        with open(debug_path, 'w') as f:
            json.dump(output, f, indent=2)
        
        print(f"\nOutput written to {self.output_path}")
        print('='*60)
    
    def _log_to_csv(self, timestamp: str, intensity: float):
        """Log carbon intensity to CSV file"""
        file_exists = self.csv_log_path.exists()
        
        with open(self.csv_log_path, 'a', newline='') as f:
            writer = csv.writer(f)
            if not file_exists:
                writer.writerow(['timestamp', 'carbon_intensity_kgco2_kwh'])
            writer.writerow([timestamp, f"{intensity:.6f}"])
    
    def _prepare_output_json(self, intensity, details, cache_status, forecast_data, update_time):
        """Prepare the output JSON structure"""
        # Calculate generation mix percentages
        # Storage is excluded from both total generation and mix percentages
        total_gen_excluding_storage = details['total_generation_mw']
        
        generation_mix = {}
        generation_mw_all = {}
        
        if total_gen_excluding_storage > 0:
            # Add all fuel types from calculator (excludes Storage)
            for fuel, mw in details['fuel_generation_mw'].items():
                generation_mix[fuel] = (mw / total_gen_excluding_storage) * 100
                generation_mw_all[fuel] = mw
            
            # Add Storage to generation_mw for transparency, but NOT to generation_mix
            storage_mw = details.get('storage_mw', 0)
            if storage_mw > 0:
                generation_mw_all['Storage'] = storage_mw
        
        output = {
            'last_updated': datetime.now().isoformat(),
            'status': 'complete' if cache_status['ready'] else 'building_cache',
            'current': {
                'carbon_intensity': round(intensity, 3),
                'timestamp': update_time.strftime('%Y-%m-%d %H:%M:%S'),
                'total_generation_mw': round(total_gen_excluding_storage, 2),
                'generation_mix': generation_mix,
                'generation_mw': {fuel: round(mw, 2) for fuel, mw in generation_mw_all.items()},
                'weather': self._get_latest_weather_from_cache()
            },
            'forecast': {
                'available': False,
                'reason': f"Building cache: {cache_status['regions']['North']['count']}/6 timesteps"
            },
            'errors': []
        }
        
        if forecast_data and cache_status['ready']:
            # Generate forecast timestamps (10-minute intervals)
            forecast_timestamps = []
            start_time = update_time + timedelta(minutes=10)
            for i in range(144):
                forecast_timestamps.append(
                    (start_time + timedelta(minutes=i*10)).strftime('%Y-%m-%d %H:%M:%S')
                )
            
            forecast_intensities = self.carbon_calculator.calculate_forecast_intensity(forecast_data)
            
            output['forecast'] = {
                'available': True,
                'start_time': forecast_timestamps[0],
                'end_time': forecast_timestamps[-1],
                'values': [round(v, 3) for v in forecast_intensities],
                'timestamps': forecast_timestamps
            }
        
        return output
    
    def _prepare_app_format_json(self, output):
        """Convert the output to match the Flutter app's expected format"""
        app_output = {
            'last_updated': output['last_updated'],
            'current_intensity': {
                'gCO2_kWh': int(output['current']['carbon_intensity'] * 1000),  # Convert kg to g
                'level': 'red'  # Will be calculated based on forecast
            },
            'forecast': [],
            'recommendation': {
                'message': '',
                'start_time': '',
                'end_time': ''
            }
        }
        
        # If forecast is available, format it and calculate levels
        if output['forecast'].get('available', False):
            values = output['forecast']['values']
            timestamps = output['forecast']['timestamps']
            
            # Convert all values to gCO2/kWh
            g_values = [int(v * 1000) for v in values]
            
            # Calculate percentiles for level assignment
            sorted_values = sorted(g_values)
            p33 = sorted_values[int(len(sorted_values) * 0.33)]
            p67 = sorted_values[int(len(sorted_values) * 0.67)]
            
            # Assign current level based on percentiles
            current_g = app_output['current_intensity']['gCO2_kWh']
            if current_g <= p33:
                app_output['current_intensity']['level'] = 'green'
            elif current_g <= p67:
                app_output['current_intensity']['level'] = 'yellow'
            else:
                app_output['current_intensity']['level'] = 'red'
            
            # Create forecast array with levels
            for i in range(len(g_values)):
                time_obj = datetime.fromisoformat(timestamps[i])
                time_str = time_obj.strftime('%H:%M')
                
                value = g_values[i]
                if value <= p33:
                    level = 'green'
                elif value <= p67:
                    level = 'yellow'
                else:
                    level = 'red'
                
                app_output['forecast'].append({
                    'time': time_str,
                    'gCO2_kWh': value,
                    'level': level
                })
            
            # Find best continuous period until 23:59
            now = datetime.fromisoformat(timestamps[0])
            today_end = now.replace(hour=23, minute=59, second=0)
            
            # Filter forecast entries that are before midnight
            today_forecast = []
            for i, ts in enumerate(timestamps):
                if datetime.fromisoformat(ts) <= today_end:
                    today_forecast.append((i, g_values[i]))
            
            # Find the longest continuous green period
            best_start = None
            best_end = None
            best_duration = 0
            
            i = 0
            while i < len(today_forecast):
                if today_forecast[i][1] <= p33:  # Green level
                    start = i
                    while i < len(today_forecast) and today_forecast[i][1] <= p33:
                        i += 1
                    end = i - 1
                    duration = end - start + 1
                    
                    if duration > best_duration:
                        best_duration = duration
                        best_start = start
                        best_end = end
                else:
                    i += 1
            
            # Set recommendation based on current level and best period
            current_level = app_output['current_intensity']['level']
            if current_level == 'green':
                app_output['recommendation']['message'] = '電網碳強度偏低，建議使用大型家電。'
            elif current_level == 'yellow':
                app_output['recommendation']['message'] = '電網碳密度適中，建議優先使用必要電器。'
            else:
                app_output['recommendation']['message'] = '電網碳密度偏高，建議避免使用大型耗電設備。'
            
            # Set recommended time period
            if best_start is not None and best_duration > 1:
                # We have a continuous green period
                start_time = datetime.fromisoformat(timestamps[today_forecast[best_start][0]])
                end_time = datetime.fromisoformat(timestamps[today_forecast[best_end][0]])
                # Add 10 minutes to end time since each slot is 10 minutes
                end_time = end_time + timedelta(minutes=10)
                app_output['recommendation']['start_time'] = start_time.strftime('%I:%M %p')
                app_output['recommendation']['end_time'] = end_time.strftime('%I:%M %p')
            elif best_start is not None and best_duration == 1:
                # Single green slot - extend to 1 hour minimum
                start_time = datetime.fromisoformat(timestamps[today_forecast[best_start][0]])
                end_time = start_time + timedelta(hours=1)
                app_output['recommendation']['start_time'] = start_time.strftime('%I:%M %p')
                app_output['recommendation']['end_time'] = end_time.strftime('%I:%M %p')
            else:
                # No green period found, find the best 2-hour window with lowest average intensity
                best_window_start = 0
                best_window_avg = float('inf')
                
                # Slide a 2-hour window (12 slots) across the day
                window_size = min(12, len(today_forecast))  # 2 hours or available data
                for i in range(len(today_forecast) - window_size + 1):
                    window_avg = sum(today_forecast[j][1] for j in range(i, i + window_size)) / window_size
                    if window_avg < best_window_avg:
                        best_window_avg = window_avg
                        best_window_start = i
                
                start_time = datetime.fromisoformat(timestamps[today_forecast[best_window_start][0]])
                end_time = start_time + timedelta(hours=2)
                app_output['recommendation']['start_time'] = start_time.strftime('%I:%M %p')
                app_output['recommendation']['end_time'] = end_time.strftime('%I:%M %p')
        else:
            # No forecast available, use defaults
            app_output['current_intensity']['level'] = 'yellow'
            app_output['recommendation']['message'] = '正在載入資料...'
            app_output['recommendation']['start_time'] = '--:--'
            app_output['recommendation']['end_time'] = '--:--'
        
        return app_output
    
    def _get_latest_weather_from_cache(self):
        """Get latest weather data from cache"""
        weather_data = {}
        try:
            if hasattr(self.cache_manager, 'cache_data'):
                for region in ['North', 'Central', 'South', 'East']:
                    if region in self.cache_manager.cache_data and self.cache_manager.cache_data[region]:
                        latest = self.cache_manager.cache_data[region][-1]
                        weather_data[region] = {
                            'air_temperature': latest.get('AirTemperature', None),
                            'wind_speed': latest.get('WindSpeed', None),
                            'sunshine_duration': latest.get('SunshineDuration', None),
                            'precipitation': latest.get('Precipitation', None)
                        }
        except Exception as e:
            print(f"Error getting weather from cache: {e}")
        return weather_data
    
    def _write_error_json(self, error_msg: str):
        """Write error JSON when generation fails"""
        output = {
            'last_updated': datetime.now().isoformat(),
            'status': 'error',
            'current': None,
            'forecast': {'available': False},
            'errors': [error_msg]
        }
        with open(self.output_path, 'w') as f:
            json.dump(output, f, indent=2)
    
    def run_scheduled(self):
        """Run on schedule at X9 minutes"""
        # Schedule for X9 minutes
        for minute in ['09', '19', '29', '39', '49', '59']:
            schedule.every().hour.at(f":{minute}").do(self.generate_carbon_intensity)
        
        print("Carbon Intensity Generator started. Scheduled for X9 minutes.")
        print("Press Ctrl+C to stop.")
        
        # Run once immediately
        self.generate_carbon_intensity()
        
        # Keep running
        while True:
            schedule.run_pending()
            time.sleep(1)
    
    def run_once(self):
        """Run once immediately"""
        self.generate_carbon_intensity()


def main():
    parser = argparse.ArgumentParser(description='Carbon Intensity Generator')
    parser.add_argument('--once', action='store_true', help='Run once and exit')
    parser.add_argument('--scheduled', action='store_true', help='Run on schedule')
    args = parser.parse_args()
    
    generator = CarbonIntensityGenerator()
    
    if args.once:
        generator.run_once()
    elif args.scheduled:
        generator.run_scheduled()
    else:
        print("Please specify --once or --scheduled")
        sys.exit(1)


if __name__ == "__main__":
    main()