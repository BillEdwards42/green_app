#!/usr/bin/env python3
# ==============================================================================
# SCRIPT: test_integration.py
# PURPOSE:
#   - Test the integration between live_pipeline_integrated.py and fetch_weather_integrated.py
#   - Simulate both scripts running and verify timestamp synchronization
#   - Check data integrity and file locking mechanisms
# ==============================================================================
import subprocess
import sys
import time
import threading
from pathlib import Path
from datetime import datetime
import pandas as pd

BASE_DIR = Path(__file__).parent
STRU_DATA_DIR = BASE_DIR / "stru_data"

def run_pipeline():
    """Run the generation pipeline."""
    print("🔄 Running generation pipeline...")
    try:
        result = subprocess.run([
            sys.executable, 
            BASE_DIR / "live_pipeline_integrated.py"
        ], capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            print("✅ Generation pipeline completed successfully")
        else:
            print(f"❌ Generation pipeline failed: {result.stderr}")
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        print("⏰ Generation pipeline timed out")
        return False
    except Exception as e:
        print(f"❌ Error running generation pipeline: {e}")
        return False

def run_weather_fetch():
    """Run the weather fetch script."""
    print("🌤️ Running weather fetch...")
    try:
        result = subprocess.run([
            sys.executable, 
            BASE_DIR / "fetch_weather_integrated.py"
        ], capture_output=True, text=True, timeout=60)
        
        if result.returncode == 0:
            print("✅ Weather fetch completed successfully")
        else:
            print(f"❌ Weather fetch failed: {result.stderr}")
        return result.returncode == 0
    except subprocess.TimeoutExpired:
        print("⏰ Weather fetch timed out")
        return False
    except Exception as e:
        print(f"❌ Error running weather fetch: {e}")
        return False

def run_verification():
    """Run the verification script."""
    print("🔍 Running verification...")
    try:
        result = subprocess.run([
            sys.executable, 
            BASE_DIR / "verify_integrated_output.py"
        ], capture_output=True, text=True, timeout=30)
        
        print("📊 Verification output:")
        print(result.stdout)
        if result.stderr:
            print("⚠️ Verification warnings:")
            print(result.stderr)
        
        return result.returncode == 0
    except Exception as e:
        print(f"❌ Error running verification: {e}")
        return False

def check_file_structure():
    """Check if the expected file structure exists."""
    print("📁 Checking file structure...")
    
    expected_files = [
        STRU_DATA_DIR / "North.csv",
        STRU_DATA_DIR / "South.csv", 
        STRU_DATA_DIR / "Central.csv",
        STRU_DATA_DIR / "East.csv",
        STRU_DATA_DIR / "Islands.csv",
        STRU_DATA_DIR / "Other.csv"
    ]
    
    all_exist = True
    for file_path in expected_files:
        if file_path.exists():
            print(f"  ✅ {file_path.name}")
            
            # Check if file has data
            try:
                df = pd.read_csv(file_path)
                if len(df) > 0:
                    print(f"     📊 {len(df)} rows of data")
                    
                    # Check columns
                    required_cols = ['Timestamp', 'Nuclear', 'Coal', 'Total_Generation']
                    missing_cols = [col for col in required_cols if col not in df.columns]
                    if missing_cols:
                        print(f"     ⚠️ Missing columns: {missing_cols}")
                    else:
                        print(f"     ✅ All required columns present")
                else:
                    print(f"     ⚠️ File is empty")
                    all_exist = False
            except Exception as e:
                print(f"     ❌ Error reading file: {e}")
                all_exist = False
        else:
            print(f"  ❌ {file_path.name} (missing)")
            all_exist = False
    
    return all_exist

def test_concurrent_access():
    """Test concurrent access to the same files."""
    print("🔄 Testing concurrent access...")
    
    results = []
    
    def run_both():
        # Run both scripts simultaneously
        pipeline_thread = threading.Thread(target=lambda: results.append(('pipeline', run_pipeline())))
        weather_thread = threading.Thread(target=lambda: results.append(('weather', run_weather_fetch())))
        
        pipeline_thread.start()
        time.sleep(1)  # Slight delay to create overlap
        weather_thread.start()
        
        pipeline_thread.join()
        weather_thread.join()
    
    try:
        run_both()
        
        pipeline_success = any(name == 'pipeline' and success for name, success in results)
        weather_success = any(name == 'weather' and success for name, success in results)
        
        if pipeline_success and weather_success:
            print("✅ Both scripts completed successfully with concurrent access")
            return True
        else:
            print("❌ One or both scripts failed during concurrent access")
            return False
            
    except Exception as e:
        print(f"❌ Error during concurrent access test: {e}")
        return False

def test_data_consistency():
    """Test data consistency across regional files."""
    print("📊 Testing data consistency...")
    
    try:
        all_data = []
        for csv_file in STRU_DATA_DIR.glob("*.csv"):
            if csv_file.name == "electricity_demand.csv":
                continue
                
            df = pd.read_csv(csv_file)
            if len(df) > 0:
                df['Region'] = csv_file.stem
                all_data.append(df)
        
        if not all_data:
            print("❌ No data files found")
            return False
            
        combined_df = pd.concat(all_data, ignore_index=True)
        combined_df['Timestamp'] = pd.to_datetime(combined_df['Timestamp'])
        
        # Check for latest timestamp consistency
        latest_timestamp = combined_df['Timestamp'].max()
        latest_data = combined_df[combined_df['Timestamp'] == latest_timestamp]
        
        print(f"  📅 Latest timestamp: {latest_timestamp}")
        print(f"  📊 Regions with latest data: {len(latest_data)}")
        
        # Check for data completeness
        for _, row in latest_data.iterrows():
            region = row['Region']
            has_generation = row.get('Total_Generation', 0) > 0
            has_weather = pd.notna(row.get('AirTemperature'))
            
            status = "✅" if has_generation else "⚠️"
            weather_status = "🌤️" if has_weather else "❄️"
            print(f"    {status} {weather_status} {region}")
        
        return True
        
    except Exception as e:
        print(f"❌ Error checking data consistency: {e}")
        return False

def main():
    """Main test execution."""
    print("="*60)
    print("🧪 GREEN MOMENT INTEGRATION TEST")
    print("="*60)
    print(f"Test started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    test_results = []
    
    # Test 1: Sequential execution
    print("TEST 1: Sequential Execution")
    print("-" * 30)
    pipeline_success = run_pipeline()
    time.sleep(2)
    weather_success = run_weather_fetch()
    test_results.append(("Sequential Execution", pipeline_success and weather_success))
    print()
    
    # Test 2: File structure check
    print("TEST 2: File Structure")
    print("-" * 30)
    structure_ok = check_file_structure()
    test_results.append(("File Structure", structure_ok))
    print()
    
    # Test 3: Data consistency
    print("TEST 3: Data Consistency")
    print("-" * 30)
    consistency_ok = test_data_consistency()
    test_results.append(("Data Consistency", consistency_ok))
    print()
    
    # Test 4: Concurrent access
    print("TEST 4: Concurrent Access")
    print("-" * 30)
    concurrent_ok = test_concurrent_access()
    test_results.append(("Concurrent Access", concurrent_ok))
    print()
    
    # Test 5: Verification script
    print("TEST 5: Verification Script")
    print("-" * 30)
    verification_ok = run_verification()
    test_results.append(("Verification Script", verification_ok))
    print()
    
    # Summary
    print("="*60)
    print("📋 TEST RESULTS SUMMARY")
    print("="*60)
    
    total_tests = len(test_results)
    passed_tests = sum(1 for _, result in test_results if result)
    
    for test_name, result in test_results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\nOverall: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("🎉 All tests passed! Integration is working correctly.")
        return 0
    else:
        print("⚠️ Some tests failed. Please check the output above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())