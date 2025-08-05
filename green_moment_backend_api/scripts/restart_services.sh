#!/bin/bash
# Script to properly restart all Green Moment backend services
# This ensures Python cache is cleared and all processes start fresh

echo "========================================"
echo "Green Moment Services Restart Script"
echo "========================================"

# Get the script directory
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
PROJECT_ROOT="$( cd "$SCRIPT_DIR/.." && pwd )"

echo "Project root: $PROJECT_ROOT"

# 1. Stop all related Python processes
echo ""
echo "1. Stopping all Green Moment Python processes..."
pkill -f "green_moment_backend_api" || true
pkill -f "uvicorn app.main:app" || true
pkill -f "notification_scheduler" || true
pkill -f "carbon_intensity_generator" || true
sleep 2

# 2. Clear Python cache
echo ""
echo "2. Clearing Python cache..."
find "$PROJECT_ROOT" -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find "$PROJECT_ROOT" -name "*.pyc" -delete 2>/dev/null || true
find "$PROJECT_ROOT" -name "*.pyo" -delete 2>/dev/null || true

# 3. Clear SQLAlchemy compiled cache if exists
echo ""
echo "3. Clearing SQLAlchemy cache..."
rm -rf "$PROJECT_ROOT/.mypy_cache" 2>/dev/null || true

# 4. Run database migration
echo ""
echo "4. Running database migrations..."
cd "$PROJECT_ROOT"
source venv/bin/activate
alembic upgrade head

# 5. Run enum consistency fix
echo ""
echo "5. Running enum consistency fix..."
python scripts/fix_enum_consistency.py

# 6. Start services (optional - uncomment if you want automatic restart)
echo ""
echo "6. Services can now be started fresh:"
echo "   - FastAPI: uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
echo "   - Carbon Generator: python scripts/carbon_intensity_generator.py --scheduled"
echo "   - Notification Scheduler: python scripts/run_notification_scheduler_fixed.py"

echo ""
echo "========================================"
echo "Restart process completed!"
echo "All Python caches cleared."
echo "Database migrations applied."
echo "Please start services manually."
echo "========================================"