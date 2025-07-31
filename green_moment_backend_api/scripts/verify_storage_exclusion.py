#!/usr/bin/env python3
"""
Verify that Storage is properly excluded from carbon intensity calculations
"""
import json
from pathlib import Path
import pandas as pd

def verify_json_output():
    """Check the carbon intensity JSON output"""
    json_path = Path("data/carbon_intensity_debug.json")
    
    if json_path.exists():
        with open(json_path, 'r') as f:
            data = json.load(f)
        
        current = data.get('current', {})
        total_gen = current.get('total_generation_mw', 0)
        generation_mw = current.get('generation_mw', {})
        generation_mix = current.get('generation_mix', {})
        
        # Calculate expected total (excluding Storage)
        expected_total = sum(mw for fuel, mw in generation_mw.items() if fuel != 'Storage')
        
        print("Carbon Intensity Output Verification")
        print("=" * 50)
        print(f"Total Generation (reported): {total_gen:.2f} MW")
        print(f"Total Generation (calculated without Storage): {expected_total:.2f} MW")
        
        if 'Storage' in generation_mw:
            print(f"Storage Generation: {generation_mw['Storage']:.2f} MW")
            print(f"Storage in generation_mix: {'Yes' if 'Storage' in generation_mix else 'No'}")
        
        # Verify the total matches expected
        if abs(total_gen - expected_total) < 0.01:
            print("\n✓ CORRECT: Total generation excludes Storage")
        else:
            print("\n✗ ERROR: Total generation includes Storage!")
        
        # Verify generation mix percentages
        if generation_mix:
            mix_total = sum(generation_mix.values())
            print(f"\nGeneration mix total: {mix_total:.2f}%")
            if abs(mix_total - 100) < 0.1:
                print("✓ CORRECT: Generation mix totals to 100%")
            else:
                print("✗ ERROR: Generation mix does not total to 100%")

def verify_calculation_log():
    """Check the carbon calculation log"""
    log_path = Path("logs/carbon_calculation_log.json")
    
    if log_path.exists():
        with open(log_path, 'r') as f:
            data = json.load(f)
        
        print("\n" + "=" * 50)
        print("Carbon Calculation Log Verification")
        print("=" * 50)
        
        summary = data.get('summary', {})
        fuel_details = data.get('fuel_details', {})
        
        if 'Storage' in fuel_details:
            storage = fuel_details['Storage']
            print(f"Storage in fuel_details: Yes")
            print(f"Storage emissions calculation: {storage.get('emissions_calculation', 'N/A')}")
            print(f"Storage note: {storage.get('note', 'N/A')}")
        else:
            print("Storage in fuel_details: No")
        
        # Check if Storage appears in regional breakdown
        regional = data.get('regional_breakdown', {})
        storage_found = False
        for region, fuels in regional.items():
            if 'Storage' in fuels:
                storage_found = True
                print(f"\n✗ Storage found in {region} regional breakdown!")
        
        if not storage_found:
            print("\n✓ CORRECT: Storage excluded from regional breakdowns")

def main():
    print("Storage Exclusion Verification")
    print("=" * 80)
    
    verify_json_output()
    verify_calculation_log()
    
    print("\n" + "=" * 80)
    print("Summary:")
    print("- Storage should NOT be in total_generation_mw")
    print("- Storage should NOT be in generation_mix percentages")
    print("- Storage should NOT be in regional_breakdown")
    print("- Storage CAN be in generation_mw for transparency")
    print("- Storage CAN be in fuel_details with 'EXCLUDED' note")

if __name__ == "__main__":
    # Change to backend API directory
    import os
    os.chdir(Path(__file__).parent.parent)
    main()