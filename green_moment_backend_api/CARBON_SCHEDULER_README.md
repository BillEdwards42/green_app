# Carbon Daily Scheduler

This system calculates daily carbon savings and manages monthly league promotions based on carbon reduction achievements.

## Overview

The scheduler runs daily at **5:50 PM** (will be changed to 12:00 AM in production) and performs:
1. **Daily**: Calculate yesterday's carbon savings for all users
2. **Monthly (1st of each month)**: Check and process league promotions based on previous month's carbon savings

## Components

### 1. Daily Carbon Calculator (`scripts/daily_carbon_calculator.py`)
- Calculates carbon saved for all users for a specific date
- Updates `daily_carbon_progress` table
- Maintains cumulative monthly totals that reset on month boundaries
- Uses `carbon_calculator_grams.py` service (all values in grams CO2e)

### 2. Carbon League Promotion (`scripts/carbon_league_promotion.py`)
- Checks users' monthly carbon savings against promotion thresholds:
  - Bronze → Silver: 100g CO2e
  - Silver → Gold: 500g CO2e
  - Gold → Emerald: 700g CO2e
  - Emerald → Diamond: 1000g CO2e
- Creates monthly summaries
- Updates user leagues

### 3. Combined Scheduler (`scripts/carbon_daily_scheduler.py`)
- Orchestrates daily calculations and monthly promotions
- Scheduled to run at 5:50 PM daily
- Logs all activities to `logs/carbon_scheduler.log`

## Usage

### Manual Testing

1. **Run for yesterday (default)**:
   ```bash
   python scripts/run_carbon_scheduler_manual.py
   ```

2. **Run for specific date**:
   ```bash
   python scripts/run_carbon_scheduler_manual.py --date 2025-08-31
   ```

3. **Force promotion check** (useful for testing):
   ```bash
   python scripts/run_carbon_scheduler_manual.py --force-promotion
   ```

4. **Test scheduler logic**:
   ```bash
   python scripts/test_carbon_scheduler.py
   ```

### Running the Scheduler

#### Option 1: Run directly (for testing)
```bash
# Run scheduler (will run at 5:50 PM daily)
python scripts/carbon_daily_scheduler.py

# Run scheduler and execute immediately
python scripts/carbon_daily_scheduler.py --run-now

# Run once and exit
python scripts/carbon_daily_scheduler.py --once
```

#### Option 2: Use systemd service (recommended for production)
```bash
# Install and start service
sudo ./scripts/setup_carbon_scheduler_service.sh install

# Check status
sudo ./scripts/setup_carbon_scheduler_service.sh status

# View logs
sudo ./scripts/setup_carbon_scheduler_service.sh logs

# Follow logs in real-time
sudo ./scripts/setup_carbon_scheduler_service.sh follow

# Stop service
sudo ./scripts/setup_carbon_scheduler_service.sh stop

# Uninstall service
sudo ./scripts/setup_carbon_scheduler_service.sh uninstall
```

## How It Works

### Daily Carbon Calculation
1. Runs every day at 5:50 PM
2. Calculates carbon saved for yesterday
3. Updates `daily_carbon_progress` table with:
   - `daily_carbon_saved`: Carbon saved on that specific day
   - `cumulative_carbon_saved`: Running total for the current month
4. Updates user's `current_month_carbon_saved` field

### Monthly Promotion Check
1. Runs on the 1st of each month at 5:50 PM
2. Checks previous month's carbon savings for all users
3. Promotes users who meet thresholds
4. Creates monthly summaries
5. Resets monthly counters

### Month Boundary Behavior
- Cumulative totals automatically reset on the 1st of each month
- Previous month's data is preserved in `monthly_summaries` table
- Users keep their total lifetime carbon saved

## Database Tables

### `daily_carbon_progress`
- `user_id`: Foreign key to users
- `date`: Date of the calculation
- `daily_carbon_saved`: Carbon saved on this day (grams CO2e)
- `cumulative_carbon_saved`: Running total for current month (grams CO2e)

### `users` (carbon-related fields)
- `current_month_carbon_saved`: Current month's total (grams CO2e)
- `total_carbon_saved`: Lifetime total (grams CO2e)
- `last_carbon_calculation_date`: Last date calculated
- `current_league`: User's current league

## Logs

All logs are stored in the `logs/` directory:
- `carbon_scheduler.log`: Main scheduler logs
- `carbon_scheduler_systemd.log`: Systemd service output
- `carbon_scheduler_systemd_error.log`: Systemd service errors

## Production Deployment

For production, change the schedule time to 12:00 AM:
1. Edit `scripts/carbon_daily_scheduler.py`
2. Change line: `schedule.every().day.at("17:50")` to `schedule.every().day.at("00:00")`
3. Restart the service: `sudo systemctl restart green-moment-carbon-scheduler`

## Troubleshooting

1. **Service won't start**: Check logs with `sudo journalctl -u green-moment-carbon-scheduler -n 100`
2. **Calculations missing**: Verify database connection and carbon intensity CSV exists
3. **Promotions not working**: Check if it's the 1st of the month and previous month has data
4. **Time issues**: Ensure system timezone is correct (`timedatectl status`)