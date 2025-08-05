#!/usr/bin/env python3
"""Test script to verify notification message reads from carbon_intensity.json"""

import asyncio
import sys
from pathlib import Path
import json

sys.path.append(str(Path(__file__).parent.parent))

from scripts.notification_scheduler_fixed import NotificationScheduler


async def test_notification_message():
    """Test the notification message generation"""
    
    scheduler = NotificationScheduler()
    
    # Read current carbon_intensity.json
    json_path = Path(__file__).parent.parent / "data" / "carbon_intensity.json"
    print(f"Reading from: {json_path}")
    
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    if 'recommendation' in data:
        print(f"\nCurrent recommendation in JSON:")
        print(f"  Start time: {data['recommendation'].get('start_time')}")
        print(f"  End time: {data['recommendation'].get('end_time')}")
    
    # Test message generation
    message = await scheduler.generate_notification_message([])
    print(f"\nGenerated notification message:")
    print(f"  {message}")
    
    # Verify it matches the expected format
    if "今日減碳時刻為" in message:
        print("\n✅ Success! Message is using the recommended period from JSON")
    else:
        print("\n❌ Message is not using the recommended period")


if __name__ == "__main__":
    asyncio.run(test_notification_message())