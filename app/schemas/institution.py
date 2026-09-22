from datetime import datetime

from pydantic import BaseModel, ConfigDict


class InstitutionCreate(BaseModel):
    name: str
    code: str | None = None


class InstitutionRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    code: str | None
    active: bool
    created_at: datetime
    updated_at: datetime
