#!/usr/bin/env python3
"""
Send notification immediately to test if everything works
"""

import asyncio
import sys
from datetime import datetime
from pathlib import Path
import json

sys.path.append(str(Path(__file__).parent.parent))

from sqlalchemy import text
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
import firebase_admin
from firebase_admin import credentials, messaging

from app.core.config import settings

# Initialize Firebase
if not firebase_admin._apps:
    firebase_path = Path(__file__).parent.parent / settings.FIREBASE_CREDENTIALS_PATH
    cred = credentials.Certificate(str(firebase_path))
    firebase_admin.initialize_app(cred)

engine = create_async_engine(settings.DATABASE_URL, echo=False)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)


async def send_test_notification():
    async with AsyncSessionLocal() as db:
        # Get user's device token directly with SQL
        result = await db.execute(text("""
            SELECT token FROM device_tokens 
            WHERE user_id = 36 AND is_active = true
            LIMIT 1
        """))
        
        device_token = result.fetchone()
        if not device_token:
            print("❌ No active device token found for user 36")
            return
            
        fcm_token = device_token.token
        print(f"📱 Found device token: {fcm_token[:50]}...")
        
        # Get carbon intensity data
        result = await db.execute(text("""
            SELECT carbon_intensity, timestamp 
            FROM carbon_intensity 
            WHERE timestamp >= NOW() 
            ORDER BY timestamp 
            LIMIT 6
        """))
        
        carbon_data = result.fetchall()
        if carbon_data:
            current = carbon_data[0]
            print(f"🌿 Current carbon intensity: {current.carbon_intensity:.3f} kgCO2e/kWh")
            
            # Find lowest in next few hours
            lowest = min(carbon_data, key=lambda x: x.carbon_intensity)
            optimal_hour = lowest.timestamp.hour
            message = f"現在碳強度：{current.carbon_intensity:.3f}。最佳時段：{optimal_hour}:00 ({lowest.carbon_intensity:.3f}) 💚"
        else:
            message = "通知系統測試成功！現在可以接收碳排放提醒了 🎉"
        
        # Send notification directly with Firebase
        try:
            fcm_message = messaging.Message(
                notification=messaging.Notification(
                    body=message
                ),
                data={
                    'type': 'test',
                    'timestamp': datetime.now().isoformat()
                },
                token=fcm_token
            )
            
            response = messaging.send(fcm_message)
            print(f"✅ Notification sent successfully! Message ID: {response}")
            print(f"📝 Message: {message}")
            
        except Exception as e:
            print(f"❌ Failed to send notification: {e}")


if __name__ == "__main__":
    print("🔔 Sending test notification directly...")
    print(f"⏰ Time: {datetime.now().strftime('%H:%M:%S')}")
    asyncio.run(send_test_notification())