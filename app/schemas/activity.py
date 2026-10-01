from datetime import date
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field, model_validator


class ActivityCreate(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)

    title: str = Field(..., min_length=1, max_length=200)
    category: str = Field(..., min_length=1, max_length=100)
    provider_name: Optional[str] = Field(None, max_length=180)
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    declared_hours: Decimal = Field(..., gt=0, le=99999.99, decimal_places=2)
    description: Optional[str] = None

    @model_validator(mode="after")
    def validate_period(self):
        if self.start_date and self.end_date and self.end_date < self.start_date:
            raise ValueError("A data final deve ser igual ou posterior à inicial.")
        return self


class ActivityRead(ActivityCreate):
    id: int
    student_id: int

    model_config = ConfigDict(from_attributes=True, str_strip_whitespace=True)
