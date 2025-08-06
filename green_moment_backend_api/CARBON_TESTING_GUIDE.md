# Carbon Calculation & League Promotion Testing Guide

This guide explains how to test the carbon calculation system and league promotion mechanism in Green Moment.

## Overview

The system tracks carbon savings at three levels:
1. **Daily Progress**: Calculates carbon saved each day based on chores
2. **Current Month**: Running total for the current month
3. **Monthly Summary**: Historical record with league status

## Testing Scripts

### 1. Check Daily Carbon Progress
Shows recent daily carbon savings and current month totals for all users.

```bash
cd green_moment_backend_api
source venv/bin/activate
python scripts/check_daily_carbon_progress.py
```

**What it shows:**
- Recent daily carbon entries (date, username, daily amount, cumulative)
- Current month totals for all users
- User's current league status

### 2. Calculate Daily Carbon (Manual Run)
Manually trigger daily carbon calculation for testing.

```bash
# Calculate for yesterday (default)
python scripts/daily_carbon_calculator.py

# Calculate for specific date
python scripts/daily_carbon_calculator.py 2025-08-05
```

**What it does:**
- Fetches all chores for the specified date
- Calculates carbon saved based on appliance usage and carbon intensity
- Updates daily_carbon_progress table
- Updates user's current_month_carbon_saved

### 3. Test League Promotion
Test if a user is eligible for promotion and simulate the process.

```bash
python scripts/test_promotion_and_reset.py <username>

# Example:
python scripts/test_promotion_and_reset.py testuser1
```

**What it shows:**
- User's current league and progress
- Task completion status
- Whether user is eligible for promotion
- Simulates promotion if eligible
- Resets tasks for new month

### 4. Check User Data
View comprehensive user data including carbon savings.

```bash
python check_user_data.py <username>

# Example:
python check_user_data.py testuser1
```

### 5. Run League Promotion Scheduler (Fixed Version)
Run the automated promotion checker.

```bash
python scripts/league_promotion_scheduler_fixed.py
```

**What it does:**
- Checks all users for promotion eligibility
- Promotes users who completed 3+ tasks
- Creates monthly summaries
- Resets tasks for new month

## Testing Workflow

### Step 1: Create Test Chores
First, create some chores for testing:

```bash
# Use the API or Flutter app to create chores
# Or use direct database insertion for testing
```

### Step 2: Run Daily Carbon Calculation
```bash
python scripts/daily_carbon_calculator.py
```

### Step 3: Check Progress
```bash
python scripts/check_daily_carbon_progress.py
```

### Step 4: Complete Tasks
Mark tasks as completed through the API:
```bash
# Example API call
curl -X PUT http://localhost:8000/api/v1/tasks/complete/{task_id} \
  -H "Authorization: Bearer YOUR_TOKEN"
```

### Step 5: Test Promotion
```bash
python scripts/test_promotion_and_reset.py <username>
```

## Carbon Calculation Formula

The system calculates carbon savings using:

```
carbon_saved = appliance_power_kw * duration_hours * carbon_intensity_difference
```

Where:
- `appliance_power_kw`: Power consumption from APPLIANCE_POWER constants
- `duration_hours`: Chore duration in hours
- `carbon_intensity_difference`: Difference between baseline (483 gCO2e/kWh) and actual intensity

## League Progression

- **Bronze** → **Silver** → **Gold** → **Emerald** → **Diamond**
- Requirement: Complete 3 tasks in current league
- Promotion happens at month boundary or when manually triggered

## Database Tables

### daily_carbon_progress
- `user_id`: Foreign key to users
- `date`: Date of calculation
- `daily_carbon_saved`: Carbon saved that day (grams)
- `cumulative_carbon_saved`: Running total for month

### users
- `current_month_carbon_saved`: Current month total (grams)
- `total_carbon_saved`: Lifetime total (grams)
- `current_league`: User's current league

### monthly_summaries
- `total_carbon_saved`: Total for that month
- `league_at_month_start`: League when month started
- `league_at_month_end`: League when month ended
- `league_upgraded`: Whether user was promoted

## Troubleshooting

### No Carbon Data Showing
1. Check if chores exist: `python verify_chores.py`
2. Run daily calculator: `python scripts/daily_carbon_calculator.py`
3. Check carbon intensity data: `cat data/carbon_intensity.json`

### Promotion Not Working
1. Verify task completion: `python scripts/test_promotion_and_reset.py <username>`
2. Check task assignment: `python scripts/list_all_tasks.py`
3. Fix task issues: `python scripts/fix_user_tasks.py <username>`

### Wrong League Tasks
1. Clean up tasks: `python scripts/fix_user_tasks.py <username>`
2. Reassign correct tasks based on current league

## Manual Database Queries

For direct database inspection:

```sql
-- Check daily progress
SELECT * FROM daily_carbon_progress 
WHERE user_id = (SELECT id FROM users WHERE username = 'testuser1')
ORDER BY date DESC LIMIT 10;

-- Check user carbon totals
SELECT username, current_month_carbon_saved, total_carbon_saved, current_league 
FROM users 
WHERE current_month_carbon_saved > 0;

-- Check task completion
SELECT u.username, t.name, ut.completed, t.league
FROM user_tasks ut
JOIN users u ON ut.user_id = u.id
JOIN tasks t ON ut.task_id = t.id
WHERE u.username = 'testuser1';
```

## Testing Tips

1. **Create Multiple Test Users**: Test promotion at different league levels
2. **Use Past Dates**: Test historical carbon calculation with specific dates
3. **Simulate Month Boundary**: Test monthly reset and promotion logic
4. **Check Logs**: Review logs in `logs/` directory for debugging

## Automated Testing

For continuous testing:

```bash
# Run all tests
python -m pytest tests/

# Run specific test
python -m pytest tests/test_carbon_calculator.py -v
```

Remember to restart the backend after making any changes to see the effects in the Flutter app!