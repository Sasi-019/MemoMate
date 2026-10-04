from datetime import datetime
from pydantic import BaseModel


class ReminderCreate(BaseModel):
    title: str
    description: str | None = None
    remind_at: datetime
    recurrence_type: str = "none"
    recurrence_day: str | None = None
    is_active: bool = True


class ReminderResponse(ReminderCreate):
    id: int

    class Config:
        from_attributes = True