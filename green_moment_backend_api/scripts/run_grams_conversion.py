#!/usr/bin/env python3
import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.convert_to_grams_co2e import main

if __name__ == "__main__":
    asyncio.run(main())