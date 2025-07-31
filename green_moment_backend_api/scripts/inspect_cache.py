#!/usr/bin/env python3
"""
Cache Inspector for Green Moment Generation Data
Inspects the generation cache and optionally exports to JSON
"""
import pickle
import json
import numpy as np
import pandas as pd
import sys
from datetime import datetime
import argparse

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

def inspect_cache(cache_file='cache/generation_cache.pkl', export_json=False, json_file='cache_readable.json'):
    """
    Inspect generation cache and optionally export to JSON
    
    Args:
        cache_file: Path to the pickle cache file
        export_json: Whether to export to JSON
        json_file: Output JSON filename
    """
    try:
        # Load cache
        with open(cache_file, 'rb') as f:
            cache = pickle.load(f)
        
        print("="*80)
        print("GENERATION CACHE INSPECTOR")
        print("="*80)
        
        # Metadata
        meta = cache.get('metadata', {})
        print(f"\nCache Metadata:")
        print(f"  Created: {meta.get('created_at', 'Unknown')}")
        print(f"  Last Update: {meta.get('last_update', 'Unknown')}")
        print(f"  Total Updates: {meta.get('total_updates', 0)}")
        
        # Summary
        print(f"\nCache Summary:")
        regions = ['North', 'Central', 'South', 'East', 'Other']
        for region in regions:
            if region in cache:
                print(f"  {region}: {len(cache[region])}/6 timesteps cached")
        
        # Detailed regional data
        for region in regions:
            if region not in cache:
                continue
                
            print(f"\n{'-'*80}")
            print(f"{region.upper()} REGION - {len(cache[region])} timesteps")
            print(f"{'-'*80}")
            
            data = cache[region]
            
            if len(data) > 0:
                # Create DataFrame for better display
                df_data = []
                for i, entry in enumerate(data):
                    row = {
                        'Index': i + 1,
                        'Data_Time': entry['Timestamp'],
                        'Cache_Time': entry['cache_timestamp'],
                        'Coal': round(entry.get('Coal', 0), 1),
                        'LNG': round(entry.get('LNG', 0), 1),
                        'Solar': round(entry.get('Solar', 0), 1),
                        'Wind': round(entry.get('Wind', 0), 1),
                        'Nuclear': round(entry.get('Nuclear', 0), 1),
                        'Hydro': round(entry.get('Hydro', 0), 1),
                        'Total_Gen': round(entry.get('Total_Generation', 0), 1)
                    }
                    
                    # Add weather data if available
                    if region != 'Other':
                        row.update({
                            'Temp_C': round(entry.get('AirTemperature', 0), 1),
                            'Wind_mps': round(entry.get('WindSpeed', 0), 1),
                            'Sunshine': round(entry.get('SunshineDuration', 0), 2),
                            'Precip': round(entry.get('Precipitation', 0), 1)
                        })
                    
                    df_data.append(row)
                
                df = pd.DataFrame(df_data)
                print("\nGeneration Data (MW):")
                
                # Display main fuels
                main_cols = ['Index', 'Data_Time', 'Coal', 'LNG', 'Solar', 'Wind', 'Total_Gen']
                print(df[main_cols].to_string(index=False))
                
                # Display weather if available
                if region != 'Other':
                    print("\nWeather Data:")
                    weather_cols = ['Index', 'Data_Time', 'Temp_C', 'Wind_mps', 'Sunshine', 'Precip']
                    print(df[weather_cols].to_string(index=False))
                
                # Show other fuel types if significant
                other_fuels = ['Nuclear', 'Hydro', 'Oil', 'Diesel', 'Co-Gen', 'IPP-Coal', 'IPP-LNG', 'Other_Renewable']
                significant_fuels = []
                for fuel in other_fuels:
                    if fuel in entry and any(e.get(fuel, 0) > 0 for e in data):
                        significant_fuels.append(fuel)
                
                if significant_fuels:
                    print("\nOther Active Fuel Types (MW):")
                    for fuel in significant_fuels:
                        values = [round(e.get(fuel, 0), 1) for e in data]
                        if any(v > 0 for v in values):
                            print(f"  {fuel}: {values}")
        
        # Export to JSON if requested
        if export_json:
            print(f"\n{'-'*80}")
            print("EXPORTING TO JSON...")
            
            # Convert cache to JSON-serializable format
            cache_dict = {}
            for key, value in cache.items():
                if key == 'metadata':
                    cache_dict[key] = value
                else:
                    # Convert deque to list
                    cache_dict[key] = list(value)
            
            # Save as JSON
            with open(json_file, 'w') as f:
                json.dump(cache_dict, f, indent=2, cls=NumpyEncoder)
            
            print(f"✓ Cache exported to: {json_file}")
            
            # Show file size
            import os
            size = os.path.getsize(json_file)
            print(f"  File size: {size:,} bytes ({size/1024:.1f} KB)")
        
        print(f"\n{'='*80}")
        
    except FileNotFoundError:
        print(f"ERROR: Cache file not found: {cache_file}")
        print("Make sure the carbon intensity generator has run at least once.")
    except Exception as e:
        print(f"ERROR reading cache: {e}")
        import traceback
        traceback.print_exc()

def main():
    parser = argparse.ArgumentParser(description='Inspect Green Moment generation cache')
    parser.add_argument('--export', '-e', action='store_true', 
                        help='Export cache to JSON format')
    parser.add_argument('--output', '-o', default='cache_readable.json',
                        help='Output JSON filename (default: cache_readable.json)')
    parser.add_argument('--cache', '-c', default='cache/generation_cache.pkl',
                        help='Cache file path (default: cache/generation_cache.pkl)')
    
    args = parser.parse_args()
    
    inspect_cache(
        cache_file=args.cache,
        export_json=args.export,
        json_file=args.output
    )

if __name__ == "__main__":
    main()