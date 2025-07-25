from pydantic import BaseModel
from typing import Optional


class UsernameUpdateRequest(BaseModel):
    username: str


class UsernameUpdateResponse(BaseModel):
    success: bool
    message: str
    username: str


class UserProfileResponse(BaseModel):
    id: int
    username: str
    email: Optional[str] = None
    is_anonymous: bool
    current_league: str
    total_carbon_saved: float
    current_month_tasks_completed: int