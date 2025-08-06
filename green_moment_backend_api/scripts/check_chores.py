#!/usr/bin/env python3

import asyncio
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import AsyncSessionLocal
from sqlalchemy import select
from app.models.chore import Chore
from app.models.user import User

async def check():
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Chore, User).join(User).order_by(Chore.start_time)
        )
        rows = result.all()
        print(f"\nFound {len(rows)} chores:\n")
        for chore, user in rows:
            print(f'{user.username}: {chore.appliance_type} on {chore.start_time.date()} '
                  f'({chore.start_time.strftime("%H:%M")}-{chore.end_time.strftime("%H:%M")}) '
                  f'- {chore.duration_minutes} min')

asyncio.run(check())