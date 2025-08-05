# Push Notification System Setup Guide

## Overview

The Green Moment push notification system runs independently from the carbon intensity generator, sending personalized notifications to users at their preferred times with optimal carbon usage windows.

## Architecture

- **Notification Scheduler**: Runs every 10 minutes at X0 (00, 10, 20, 30, 40, 50)
- **Carbon Generator**: Runs every 10 minutes at X9 (09, 19, 29, 39, 49, 59)
- **Backend API**: Handles device token registration and user preferences

## Prerequisites

1. Firebase Admin SDK credentials (`firebase-admin-sdk.json`) in project root
2. Firebase project configured with FCM
3. Backend API running with notification endpoints
4. PostgreSQL database with notification tables

## Installation

1. **Install dependencies** (if not already done):
   ```bash
   cd green_moment_backend_api
   source venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Run database migrations**:
   ```bash
   alembic upgrade head
   ```

3. **Verify Firebase setup**:
   - Ensure `firebase-admin-sdk.json` exists in `/home/bill/StudioProjects/`
   - Check `.env` file has correct path to Firebase credentials

## Running the Services

You need **THREE separate terminal windows**:

### Terminal 1: Backend API
```bash
cd green_moment_backend_api
source venv/bin/activate
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

### Terminal 2: Carbon Generator (X9 minutes)
```bash
cd green_moment_backend_api
source venv/bin/activate
python scripts/carbon_intensity_generator.py --scheduled
```

### Terminal 3: Notification Scheduler (X0 minutes)
```bash
cd green_moment_backend_api
source venv/bin/activate
python scripts/run_notification_scheduler.py
```

## How It Works

1. **Device Registration**: 
   - Flutter app sends FCM token to `/api/v1/notifications/device-token`
   - Token is stored with user ID and device info

2. **User Preferences**:
   - Users set notification time in app (e.g., 09:00)
   - Settings saved via `/api/v1/notifications/settings`

3. **Scheduling**:
   - Every 10 minutes at X0, scheduler checks for users to notify
   - Matches current time with user preferences (±5 minute window)

4. **Notification Content**:
   - Reads latest carbon intensity data
   - Identifies optimal usage hours for next 24h
   - Sends personalized message with best times

## Notification Message Examples

- **Current hour is optimal**: "現在是低碳時段！快來使用高耗能家電吧 💚"
- **Next optimal hour**: "下個低碳時段：14:00，準備好你的家電任務！"
- **Tomorrow's optimal**: "明日 7:00 是最佳用電時段，記得安排家電使用！"

## Monitoring

Check log files for status:
- API logs: Console output
- Notification scheduler: `logs/notification_scheduler.log`
- Runner logs: `logs/notification_runner.log`

## Troubleshooting

### "No module named 'firebase_admin'"
```bash
pip install firebase-admin==6.5.0
```

### "Firebase Admin SDK file not found"
- Verify `firebase-admin-sdk.json` exists in StudioProjects directory
- Check path in `.env` file

### No notifications being sent
1. Check if users have device tokens registered
2. Verify notification settings are enabled
3. Check scheduler logs for errors
4. Ensure current time matches user scheduled times

### Token validation errors
- Invalid tokens are automatically deactivated
- Users need to re-register device on next app launch

## Testing

1. **Test notification endpoint**:
   ```bash
   # Get auth token first, then:
   curl -X POST http://localhost:8000/api/v1/notifications/device-token \
     -H "Authorization: Bearer YOUR_TOKEN" \
     -H "Content-Type: application/json" \
     -d '{
       "token": "TEST_FCM_TOKEN",
       "platform": "android",
       "device_id": "test_device_123"
     }'
   ```

2. **Test scheduler manually**:
   ```bash
   cd scripts
   python notification_scheduler.py
   ```

## Production Deployment

For production, use systemd services or supervisord to manage the three processes:

1. Create service files for each component
2. Enable auto-restart on failure
3. Set up log rotation
4. Monitor service health

Example systemd service for notification scheduler:

```ini
[Unit]
Description=Green Moment Notification Scheduler
After=network.target postgresql.service

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/path/to/green_moment_backend_api/scripts
Environment="PATH=/path/to/venv/bin"
ExecStart=/path/to/venv/bin/python run_notification_scheduler.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

## Security Notes

- Firebase Admin SDK credentials should be kept secure
- Never commit `firebase-admin-sdk.json` to version control
- Use environment variables for sensitive configuration
- Implement rate limiting for notification endpoints