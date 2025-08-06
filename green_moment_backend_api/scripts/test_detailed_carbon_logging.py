#!/usr/bin/env python3
"""
Test detailed carbon calculation logging
"""

import asyncio
import sys
import os
from datetime import date, timedelta

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import AsyncSessionLocal
from scripts.carbon_daily_scheduler import run_daily_tasks


async def test_logging():
    """Test the detailed logging"""
    print("🧪 Testing detailed carbon calculation logging")
    print("=" * 60)
    
    # Run the daily tasks which will show detailed logs
    await run_daily_tasks()


if __name__ == "__main__":
    asyncio.run(test_logging())