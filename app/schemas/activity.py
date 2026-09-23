from datetime import date
from decimal import Decimal
from typing import Optional
from pydantic import BaseModel, Field

class ActivityCreate(BaseModel):
    title: str = Field(..., max_length=200)
    category: str = Field(..., max_length=100)
    provider_name: Optional[str] = Field(None, max_length=180)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    declared_hours: Decimal = Field(..., gt=0, decimal_places=2)
    description: Optional[str] = None

class ActivityRead(ActivityCreate):
    id: int
    student_id: int

    class Config:
        from_attributes = True