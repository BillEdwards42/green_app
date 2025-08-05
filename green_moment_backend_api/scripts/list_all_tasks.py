#!/usr/bin/env python3
"""List all tasks in the system organized by league"""

import asyncio
import sys
import os
from sqlalchemy import select

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.core.database import AsyncSessionLocal
from app.models.task import Task


async def list_all_tasks():
    async with AsyncSessionLocal() as db:
        result = await db.execute(
            select(Task).order_by(Task.league, Task.id)
        )
        tasks = result.scalars().all()
        
        current_league = None
        league_order = ['bronze', 'silver', 'gold', 'emerald', 'diamond']
        
        for league in league_order:
            league_tasks = [t for t in tasks if t.league == league]
            if league_tasks:
                print(f'\n{"="*60}')
                print(f'{league.upper()} LEAGUE - {len(league_tasks)} tasks')
                print(f'{"="*60}')
                
                for task in league_tasks:
                    status = "✅" if task.is_active else "❌"
                    print(f'\n{status} Task #{task.id}: {task.name}')
                    print(f'   Chinese: {task.name}')
                    print(f'   English: {task.description}')
                    print(f'   Type: {task.task_type}')
                    print(f'   Target: {task.target_value}')
                    print(f'   Points: {task.points}')


if __name__ == "__main__":
    asyncio.run(list_all_tasks())