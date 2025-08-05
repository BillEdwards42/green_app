#!/usr/bin/env python3
"""
Run notification scheduler every 10 minutes at X0 (00, 10, 20, 30, 40, 50)
Fixed version that changes to correct directory for .env file
"""

import schedule
import time
import subprocess
import os
from datetime import datetime
from pathlib import Path

# Change to backend API directory (parent of scripts)
backend_dir = Path(__file__).parent.parent
os.chdir(backend_dir)

# Log file
log_file = Path("logs/notification_runner.log")
log_file.parent.mkdir(exist_ok=True)


def log_message(message):
    """Log message with timestamp"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] {message}"
    
    print(log_entry)
    
    with open(log_file, "a") as f:
        f.write(log_entry + "\n")


def run_notification_scheduler():
    """Run the notification scheduler script"""
    try:
        log_message("Starting notification scheduler...")
        
        # Run the fixed scheduler from the backend directory
        result = subprocess.run(
            ["python3", "scripts/notification_scheduler_fixed.py"],
            capture_output=True,
            text=True,
            check=True,
            cwd=backend_dir  # Ensure we're in the right directory
        )
        
        if result.stdout:
            log_message(f"Scheduler output: {result.stdout}")
        
        if result.stderr:
            log_message(f"Scheduler errors: {result.stderr}")
            
        log_message("Notification scheduler completed successfully")
        
    except subprocess.CalledProcessError as e:
        log_message(f"ERROR: Notification scheduler failed with exit code {e.returncode}")
        log_message(f"STDOUT: {e.stdout}")
        log_message(f"STDERR: {e.stderr}")
        
    except Exception as e:
        log_message(f"ERROR: Unexpected error running notification scheduler: {e}")


def check_and_run():
    """Check if we should run (at X0 minutes) and run if needed"""
    current_minute = datetime.now().minute
    
    # Run at X0 minutes (0, 10, 20, 30, 40, 50)
    if current_minute % 10 == 0:
        run_notification_scheduler()


def main():
    """Main scheduler loop"""
    log_message("=" * 60)
    log_message("Notification Scheduler Runner Started (Fixed)")
    log_message(f"Working directory: {os.getcwd()}")
    log_message(f"Will run every 10 minutes at X0 (00, 10, 20, 30, 40, 50)")
    log_message("=" * 60)
    
    # Schedule to run every minute and check if it's X0
    schedule.every().minute.do(check_and_run)
    
    # Run once at startup if we're at X0
    check_and_run()
    
    # Keep running
    while True:
        schedule.run_pending()
        time.sleep(30)  # Check every 30 seconds


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        log_message("\nNotification scheduler runner stopped by user")
    except Exception as e:
        log_message(f"\nFATAL ERROR: {e}")
        raise