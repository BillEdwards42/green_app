from fastapi import APIRouter

from app.api.v1.endpoints import auth, users, chores, carbon, progress, notifications, tasks

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(chores.router, prefix="/chores", tags=["chores"])
api_router.include_router(carbon.router, prefix="/carbon", tags=["carbon"])
api_router.include_router(progress.router, prefix="/progress", tags=["progress"])
api_router.include_router(notifications.router, prefix="/notifications", tags=["notifications"])
api_router.include_router(tasks.router, prefix="/tasks", tags=["tasks"])