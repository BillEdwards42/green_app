#!/usr/bin/env python3
"""
Update all CO2 references to CO2e throughout the system
"""
import json
import os
import re
from pathlib import Path

def update_json_keys(data):
    """Recursively update JSON keys from CO2 to CO2e"""
    if isinstance(data, dict):
        new_data = {}
        for key, value in data.items():
            # Update key if it contains CO2 but not CO2e
            new_key = key
            if 'CO2' in key and 'CO2e' not in key:
                new_key = key.replace('gCO2_kWh', 'gCO2e_kWh').replace('gCO2_kwh', 'gCO2e_kWh')
            new_data[new_key] = update_json_keys(value)
        return new_data
    elif isinstance(data, list):
        return [update_json_keys(item) for item in data]
    else:
        return data

def update_carbon_intensity_json():
    """Update carbon intensity JSON file to use CO2e"""
    json_path = Path("data/carbon_intensity.json")
    
    if json_path.exists():
        print("📄 Updating carbon intensity JSON...")
        with open(json_path, 'r') as f:
            data = json.load(f)
        
        # Update all keys
        updated_data = update_json_keys(data)
        
        # Write back
        with open(json_path, 'w') as f:
            json.dump(updated_data, f, indent=2)
        
        print("✅ Updated carbon intensity JSON to use CO2e")

def update_python_files():
    """Update Python files to use CO2e"""
    replacements = [
        # Update gCO2_kWh to gCO2e_kWh
        (r"gCO2_kWh", "gCO2e_kWh"),
        (r"gCO2_kwh", "gCO2e_kWh"),
        (r"gCO2/kWh", "gCO2e/kWh"),
        
        # Update kg CO2 to kg CO2e (in comments)
        (r"kg CO2(?!e)", "kg CO2e"),
        (r"kgCO2/kWh", "kgCO2e/kWh"),
        (r"kgCO2_kWh", "kgCO2e_kWh"),
        
        # Update carbon intensity comments
        (r"carbon intensity \(CO2\)", "carbon intensity (CO2e)"),
        (r"Carbon intensity: CO2", "Carbon intensity: CO2e"),
    ]
    
    files_to_update = [
        "scripts/carbon_intensity_generator.py",
        "scripts/inspect_model_features.py",
        "app/api/v1/endpoints/carbon.py",
        "scripts/test_league_promotion.py",
        "scripts/monthly_carbon_calculator_template.py",
        "scripts/analyze_duplicate_carbon_entries.py",
        "scripts/league_promotion_scheduler.py",
        "scripts/league_promotion_scheduler_fixed.py",
        "app/models/monthly_summary.py",
        "app/services/carbon_calculator.py",
        "check_user_data.py",
    ]
    
    for file_path in files_to_update:
        if Path(file_path).exists():
            print(f"📝 Updating {file_path}...")
            with open(file_path, 'r') as f:
                content = f.read()
            
            original_content = content
            for pattern, replacement in replacements:
                content = re.sub(pattern, replacement, content)
            
            if content != original_content:
                with open(file_path, 'w') as f:
                    f.write(content)
                print(f"✅ Updated {file_path}")
            else:
                print(f"⏭️  No changes needed in {file_path}")

def main():
    print("🌱 Updating System to use CO2e everywhere")
    print("=" * 60)
    
    # Update carbon intensity JSON
    update_carbon_intensity_json()
    
    # Update Python files
    print("\n📂 Updating Python files...")
    update_python_files()
    
    print("\n✅ System updated to use CO2e consistently!")
    print("\nNote: You may need to restart any running services for changes to take effect.")

if __name__ == "__main__":
    main()