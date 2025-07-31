#!/usr/bin/env python3
"""
Simple runner script for the Carbon Intensity Generator
For local testing - provides both manual and scheduled options
"""
import subprocess
import sys
import os

def main():
    print("Carbon Intensity Generator Runner")
    print("=" * 40)
    print("1. Run once (manual test)")
    print("2. Run scheduled (every X9 minute)")
    print("3. Exit")
    print("=" * 40)
    
    choice = input("Select option (1-3): ")
    
    # Change to backend API directory
    os.chdir(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    
    if choice == "1":
        print("\nRunning generator once...")
        subprocess.run([sys.executable, "scripts/carbon_intensity_generator.py", "--once"])
    elif choice == "2":
        print("\nStarting scheduled runs (every X9 minute)")
        print("Press Ctrl+C to stop")
        try:
            subprocess.run([sys.executable, "scripts/carbon_intensity_generator.py", "--scheduled"])
        except KeyboardInterrupt:
            print("\nScheduler stopped.")
    elif choice == "3":
        print("Exiting...")
        sys.exit(0)
    else:
        print("Invalid choice. Please run again.")

if __name__ == "__main__":
    main()