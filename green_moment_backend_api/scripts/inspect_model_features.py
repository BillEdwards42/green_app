#!/usr/bin/env python3
"""
Model Feature Inspector for Green Moment
Shows the actual features that get fed into the ML models after preprocessing
"""
import pickle
import json
import numpy as np
import pandas as pd
import sys
from datetime import datetime
import argparse
import os

# Add parent directory to path to import ml_inference
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scripts.ml_inference import MLInferenceService

class NumpyEncoder(json.JSONEncoder):
    """Custom JSON encoder for numpy types"""
    def default(self, obj):
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        if isinstance(obj, np.generic):
            return obj.item()
        if isinstance(obj, pd.Timestamp):
            return obj.isoformat()
        return super().default(obj)

def inspect_model_features(cache_file='cache/generation_cache.pkl', export_json=False, json_file='model_features.json'):
    """
    Inspect the actual features that get fed into the ML models
    
    Args:
        cache_file: Path to the pickle cache file
        export_json: Whether to export to JSON
        json_file: Output JSON filename
    """
    try:
        # Load cache
        with open(cache_file, 'rb') as f:
            cache = pickle.load(f)
        
        # Initialize ML service to use its preprocessing
        ml_service = MLInferenceService()
        
        print("="*80)
        print("MODEL FEATURE INSPECTOR")
        print("="*80)
        
        # Define expected features for each region type
        print("\nExpected Model Input Features:")
        print("\nNorth/South/Central/East regions (22 features):")
        print("  Fuel types (12): Nuclear, Coal, Co-Gen, IPP-Coal, LNG, IPP-LNG,")
        print("                   Oil, Diesel, Hydro, Wind, Solar, Other_Renewable")
        print("  Weather (4): AirTemperature, WindSpeed, SunshineDuration, Precipitation")
        print("  Time (6): Year, Month, Day, DayOfWeek, Hour, Minute")
        
        print("\nOther region (18 features):")
        print("  Fuel types (12): Same as above")
        print("  Time (6): Year, Month, Day, DayOfWeek, Hour, Minute")
        print("  (No weather features)")
        
        regions = ['North', 'Central', 'South', 'East', 'Other']
        all_features_dict = {}
        
        # Collect all timestep data for fuel summaries
        all_timestep_data = []
        
        for region in regions:
            if region not in cache or len(cache[region]) == 0:
                continue
            
            print(f"\n{'-'*80}")
            print(f"{region.upper()} REGION")
            print(f"{'-'*80}")
            
            # Get cached data
            cache_data = list(cache[region])
            print(f"\nCached timesteps: {len(cache_data)}")
            
            if len(cache_data) >= 6:
                # Preprocess data to get model features
                print("\nPreprocessing data for model input...")
                
                # Convert to the format expected by preprocess_data
                preprocessed = ml_service.preprocess_data(cache_data, region)
                
                if preprocessed is not None:
                    # Get feature names based on region
                    fuel_columns = ml_service.fuel_columns  # 12 fuel types (no Storage)
                    
                    if region == 'Other':
                        feature_names = fuel_columns + ['Year', 'Month', 'Day', 'DayOfWeek', 'Hour', 'Minute']
                    else:
                        feature_names = fuel_columns + ['AirTemperature', 'WindSpeed', 'SunshineDuration', 
                                                       'Precipitation', 'Year', 'Month', 'Day', 'DayOfWeek', 
                                                       'Hour', 'Minute']
                    
                    print(f"\nModel input shape: {preprocessed.shape}")
                    print(f"Expected features: {len(feature_names)}")
                    
                    # Reshape to 2D for display (6 timesteps x features)
                    features_2d = preprocessed.reshape(6, -1)
                    
                    # Create DataFrame for better display
                    df = pd.DataFrame(features_2d, columns=feature_names)
                    
                    # Add timestamps for reference
                    timestamps = [pd.to_datetime(d['Timestamp']) for d in cache_data[-6:]]
                    df.insert(0, 'Timestamp', timestamps)
                    
                    print("\nRAW FUEL GENERATION DATA (MW):")
                    print("Note: These are the actual MW values from the cached data")
                    
                    # Create raw data DataFrame
                    raw_data = []
                    for i, entry in enumerate(cache_data[-6:]):
                        raw_row = {'Timestamp': entry['Timestamp']}
                        for fuel in fuel_columns:
                            raw_row[fuel] = round(float(entry.get(fuel, 0)), 1)
                        raw_data.append(raw_row)
                    
                    raw_df = pd.DataFrame(raw_data)
                    
                    # Show all fuel types
                    print("\nAll Fuel Types (MW):")
                    pd.set_option('display.max_columns', None)
                    pd.set_option('display.width', None)
                    print(raw_df.to_string(index=False))
                    pd.reset_option('display.max_columns')
                    pd.reset_option('display.width')
                    
                    if region != 'Other':
                        print("\nWeather Data:")
                        weather_data = []
                        for entry in cache_data[-6:]:
                            weather_data.append({
                                'Timestamp': entry['Timestamp'],
                                'Temp(C)': round(float(entry.get('AirTemperature', 0)), 1),
                                'Wind(m/s)': round(float(entry.get('WindSpeed', 0)), 1),
                                'Sunshine': round(float(entry.get('SunshineDuration', 0)), 2),
                                'Precip(mm)': round(float(entry.get('Precipitation', 0)), 1)
                            })
                        weather_df = pd.DataFrame(weather_data)
                        print(weather_df.to_string(index=False))
                    
                    # Get raw values before scaling for one timestep
                    latest_entry = cache_data[-1]
                    print(f"\nExample raw values (last timestep: {latest_entry['Timestamp']}):")
                    
                    # Show actual values
                    raw_df = pd.DataFrame([latest_entry])
                    raw_df['Year'] = pd.to_datetime(latest_entry['Timestamp']).year
                    raw_df['Month'] = pd.to_datetime(latest_entry['Timestamp']).month
                    raw_df['Day'] = pd.to_datetime(latest_entry['Timestamp']).day
                    raw_df['DayOfWeek'] = pd.to_datetime(latest_entry['Timestamp']).dayofweek
                    raw_df['Hour'] = pd.to_datetime(latest_entry['Timestamp']).hour
                    raw_df['Minute'] = pd.to_datetime(latest_entry['Timestamp']).minute
                    
                    print("\nFuel values (MW):")
                    for fuel in fuel_columns:
                        if fuel in latest_entry:
                            print(f"  {fuel}: {latest_entry[fuel]}")
                    
                    if region != 'Other':
                        print("\nWeather values:")
                        print(f"  AirTemperature: {latest_entry.get('AirTemperature', 'N/A')}°C")
                        print(f"  WindSpeed: {latest_entry.get('WindSpeed', 'N/A')} m/s")
                        print(f"  SunshineDuration: {latest_entry.get('SunshineDuration', 'N/A')}")
                        print(f"  Precipitation: {latest_entry.get('Precipitation', 'N/A')} mm")
                    
                    print("\nTime values:")
                    print(f"  Year: {raw_df['Year'].iloc[0]}")
                    print(f"  Month: {raw_df['Month'].iloc[0]}")
                    print(f"  Day: {raw_df['Day'].iloc[0]}")
                    print(f"  DayOfWeek: {raw_df['DayOfWeek'].iloc[0]} (0=Monday)")
                    print(f"  Hour: {raw_df['Hour'].iloc[0]}")
                    print(f"  Minute: {raw_df['Minute'].iloc[0]}")
                    
                    # Show fuel generation summary
                    print("\nFuel Generation Summary (MW):")
                    print("Timestep |         Timestamp          | Fuel Sum | Total Gen | Difference")
                    print("-" * 75)
                    
                    # Calculate fuel generation for each timestep
                    timestep_fuel_totals = []
                    for i, entry in enumerate(cache_data[-6:]):
                        fuel_sum = sum(float(entry.get(fuel, 0)) for fuel in fuel_columns)
                        total_gen = float(entry.get('Total_Generation', 0))
                        diff = total_gen - fuel_sum
                        print(f"    {i+1}    | {entry['Timestamp']} | {fuel_sum:8.2f} | {total_gen:9.2f} | {diff:10.2f}")
                        
                        # Collect detailed data for overall summary
                        timestep_data = {
                            'region': region,
                            'timestep': i + 1,
                            'timestamp': entry['Timestamp'],
                            'fuel_generation_mw': round(fuel_sum, 2),
                            'total_generation_mw': round(total_gen, 2),
                            'storage_mw': round(diff, 2)
                        }
                        # Add individual fuel values
                        for fuel in fuel_columns:
                            timestep_data[f'{fuel}_mw'] = round(float(entry.get(fuel, 0)), 2)
                        
                        timestep_fuel_totals.append(timestep_data)
                        all_timestep_data.append(timestep_data)
                    
                    print("\nNote: Difference = Total_Generation - Sum(12 fuel types)")
                    print("      This represents Storage + any uncategorized generation")
                    
                    # Store for export
                    all_features_dict[region] = {
                        'feature_names': feature_names,
                        'feature_count': len(feature_names),
                        'preprocessed_shape': list(preprocessed.shape),
                        'scaled_features': df.to_dict(orient='records'),
                        'latest_raw_values': {
                            'description': 'Raw values from the most recent timestep before any preprocessing',
                            'timestamp': latest_entry['Timestamp'],
                            'fuels_mw': {fuel: float(latest_entry.get(fuel, 0)) for fuel in fuel_columns},
                            'weather': {
                                'AirTemperature': float(latest_entry.get('AirTemperature', 0)),
                                'WindSpeed': float(latest_entry.get('WindSpeed', 0)),
                                'SunshineDuration': float(latest_entry.get('SunshineDuration', 0)),
                                'Precipitation': float(latest_entry.get('Precipitation', 0))
                            } if region != 'Other' else None,
                            'time': {
                                'Year': int(raw_df['Year'].iloc[0]),
                                'Month': int(raw_df['Month'].iloc[0]),
                                'Day': int(raw_df['Day'].iloc[0]),
                                'DayOfWeek': int(raw_df['DayOfWeek'].iloc[0]),
                                'Hour': int(raw_df['Hour'].iloc[0]),
                                'Minute': int(raw_df['Minute'].iloc[0])
                            }
                        },
                        'fuel_generation_summary': timestep_fuel_totals
                    }
                else:
                    print("ERROR: Could not preprocess data")
            else:
                print(f"WARNING: Only {len(cache_data)} timesteps cached (need 6)")
        
        # Show overall summary
        print(f"\n{'='*80}")
        print("OVERALL FUEL GENERATION SUMMARY")
        print(f"{'='*80}")
        
        if all_timestep_data:
            # Convert to DataFrame for easier analysis
            df_all = pd.DataFrame(all_timestep_data)
            
            # Get fuel columns
            fuel_columns = ml_service.fuel_columns
            
            # Get only the latest timestep data
            latest_timestamp = df_all['timestamp'].max()
            latest_data = df_all[df_all['timestamp'] == latest_timestamp]
            
            print(f"\n1. FUEL GENERATION FOR LATEST TIMESTEP: {latest_timestamp}")
            print("-" * 80)
            print(f"{'Fuel Type':<20} | {'Total MW':>12}")
            print("-" * 80)
            
            fuel_totals = {}
            for fuel in fuel_columns:
                col_name = f'{fuel}_mw'
                if col_name in latest_data.columns:
                    fuel_total = latest_data[col_name].sum()
                    fuel_totals[fuel] = fuel_total
                    print(f"{fuel:<20} | {fuel_total:>12.1f}")
            
            print("-" * 80)
            
            # Total generation
            grand_total = latest_data['fuel_generation_mw'].sum()
            print(f"{'TOTAL (12 fuels)':<20} | {grand_total:>12.1f}")
            
            print("\n" + "-" * 80)
            print(f"Total Generation (12 fuels): {grand_total:.1f} MW")
            print(f"Total Generation (with Storage): {latest_data['total_generation_mw'].sum():.1f} MW")
            print(f"Storage: {latest_data['storage_mw'].sum():.1f} MW")
            
            # 2. Summary Statistics
            print("\n2. CARBON INTENSITY")
            print("-" * 80)
            
            # Get the latest carbon intensity from the carbon_intensity.json file
            try:
                with open('data/carbon_intensity.json', 'r') as f:
                    carbon_data = json.load(f)
                print(f"Current Carbon Intensity: {carbon_data['current_intensity']['gCO2_kWh']} gCO2/kWh")
                print(f"Level: {carbon_data['current_intensity']['level'].upper()}")
            except:
                print("Carbon intensity data not available")
            
            # Store summary for export
            summary_data = {
                'fuel_totals': fuel_totals,
                'latest_timestep': latest_timestamp,
                'regional_latest': latest_data.to_dict(orient='index'),
                'all_timestep_data': all_timestep_data
            }
        
        # Export if requested
        if export_json:
            print(f"\n{'='*80}")
            print("EXPORTING MODEL FEATURES TO JSON...")
            
            # Add summary to export
            export_data = {
                'regions': all_features_dict,
                'summary': {
                    'description': 'Model feature inspection results with comprehensive fuel generation analysis',
                    'generated_at': datetime.now().isoformat(),
                    'cache_file': cache_file,
                    'fuel_generation_analysis': summary_data if 'summary_data' in locals() else None,
                    'notes': {
                        'scaled_features': 'Features after StandardScaler preprocessing (what the model sees)',
                        'latest_raw_values': 'Raw values from the most recent timestep before any preprocessing',
                        'fuel_generation_summary': 'Sum of 12 fuel types for each cached timestep',
                        'storage': 'Storage = Total_Generation - Sum(12 fuel types)',
                        'fuel_totals': 'Aggregated generation data by fuel type across all regions and timesteps'
                    }
                }
            }
            
            with open(json_file, 'w') as f:
                json.dump(export_data, f, indent=2, cls=NumpyEncoder)
            
            print(f"✓ Model features exported to: {json_file}")
            
            # Show file size
            import os
            size = os.path.getsize(json_file)
            print(f"  File size: {size:,} bytes ({size/1024:.1f} KB)")
        
        print(f"\n{'='*80}")
        
    except FileNotFoundError:
        print(f"ERROR: Cache file not found: {cache_file}")
        print("Make sure the carbon intensity generator has run at least once.")
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()

def main():
    parser = argparse.ArgumentParser(description='Inspect model features from cache')
    parser.add_argument('--export', '-e', action='store_true', 
                        help='Export features to JSON format')
    parser.add_argument('--output', '-o', default='model_features.json',
                        help='Output JSON filename (default: model_features.json)')
    parser.add_argument('--cache', '-c', default='cache/generation_cache.pkl',
                        help='Cache file path (default: cache/generation_cache.pkl)')
    
    args = parser.parse_args()
    
    inspect_model_features(
        cache_file=args.cache,
        export_json=args.export,
        json_file=args.output
    )

if __name__ == "__main__":
    main()