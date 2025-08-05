# Database Migration Guide

## Running the Chore Table Migration

This migration simplifies the chore table to only store essential fields:
- `id`, `user_id`, `appliance_type`, `start_time`, `duration_minutes`, `end_time`, `created_at`

### Steps to Apply Migration:

1. **Ensure database is backed up** (if you have existing data):
   ```bash
   pg_dump green_moment > backup_$(date +%Y%m%d).sql
   ```

2. **Run the migration**:
   ```bash
   cd /home/bill/StudioProjects/green_moment_backend_api
   alembic upgrade head
   ```

3. **Verify the migration**:
   ```bash
   # Check migration status
   alembic current
   
   # Connect to database and verify schema
   psql -d green_moment -c "\d chores"
   ```

### If Migration Fails:

1. **Rollback**:
   ```bash
   alembic downgrade -1
   ```

2. **Check logs** for errors and fix any issues

## Monthly Carbon Calculation Recommendation

Based on your infrastructure and requirements, here's my recommendation:

### Use CRON JOB (Recommended) ✅

**Why Cron Job is Better for Your Case:**

1. **Simplicity**: 
   - Similar to your existing carbon intensity generator
   - No additional infrastructure (Celery/Redis) needed
   - Easy to understand and debug

2. **Consistency**: 
   - Runs reliably on schedule (1st of each month)
   - Simple logging to files like your generator
   - Can read the `actual_carbon_intensity.csv` directly

3. **Cloud-Ready**:
   - Easy to deploy: just add to crontab on server
   - Works on any Linux server
   - No complex container orchestration needed

### Implementation Plan:

1. **Create Monthly Calculator Script** (`scripts/monthly_carbon_calculator.py`):
   ```python
   # Similar structure to carbon_intensity_generator.py
   # Reads from: logs/actual_carbon_intensity.csv
   # Calculates carbon savings for previous month
   # Updates user statistics in database
   ```

2. **Add to Crontab**:
   ```bash
   # Run on 1st of each month at 2 AM
   0 2 1 * * /usr/bin/python3 /path/to/monthly_carbon_calculator.py
   ```

3. **Key Features**:
   - Process all users' chores from previous month
   - Read actual carbon intensity from CSV
   - Find worst consecutive periods for comparison
   - Update user leagues based on total savings
   - Generate monthly summaries

### Alternative: Celery (If Scaling Needed Later)

Use Celery only if you need:
- Distributed processing across multiple servers
- Real-time progress tracking in web UI
- Complex retry logic with exponential backoff
- Integration with other async tasks

For now, a cron job will be simpler and more maintainable.

## Next Steps:

1. Apply the migration
2. Create the monthly calculation script (cron job approach)
3. Test with sample data
4. Deploy to production