from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class ChoreLogRequest(BaseModel):
    """Request model for logging a new chore"""
    appliance_type: str = Field(..., description="Type of appliance (e.g., washing_machine, microwave)")
    start_time: datetime = Field(..., description="When the chore starts")
    duration_minutes: int = Field(..., gt=0, description="Duration in minutes")


class ChoreLogResponse(BaseModel):
    """Response model after logging a chore"""
    id: int
    user_id: int
    appliance_type: str
    start_time: datetime
    end_time: datetime
    duration_minutes: int
    created_at: datetime

    class Config:
        from_attributes = True


class ChoreHistoryItem(BaseModel):
    """Item in chore history list"""
    id: int
    appliance_type: str
    start_time: datetime
    duration_minutes: int
    created_at: datetime

    class Config:
        from_attributes = True


class ChoreHistoryResponse(BaseModel):
    """Response for chore history"""
    chores: list[ChoreHistoryItem]
    total_count: int