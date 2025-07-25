from fastapi import APIRouter

from app.api.v1.endpoints import auth, users, chores, carbon, progress

api_router = APIRouter()

# Include all endpoint routers
api_router.include_router(auth.router, prefix="/auth", tags=["authentication"])
api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(chores.router, prefix="/chores", tags=["chores"])
api_router.include_router(carbon.router, prefix="/carbon", tags=["carbon"])
api_router.include_router(progress.router, prefix="/progress", tags=["progress"])