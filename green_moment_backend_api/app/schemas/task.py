from pydantic import BaseModel
from datetime import datetime
from typing import Optional


class TaskBase(BaseModel):
    name: str
    description: str
    points: int


class TaskCreate(TaskBase):
    pass


class TaskResponse(TaskBase):
    id: int
    is_active: bool
    created_at: datetime
    
    class Config:
        from_attributes = True


class UserTaskResponse(BaseModel):
    id: int
    task_id: int
    name: str
    description: str
    points: int
    completed: bool
    completed_at: Optional[datetime] = None
    points_earned: int
    
    class Config:
        from_attributes = True


class TaskComplete(BaseModel):
    task_id: int