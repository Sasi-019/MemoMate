from pydantic import BaseModel, ConfigDict

from app.schemas.utc import UTCDateTime


class ReminderCreate(BaseModel):
    title: str
    description: str | None = None
    remind_at: UTCDateTime
    recurrence_type: str = "none"
    recurrence_day: str | None = None
    is_active: bool = True


class ReminderResponse(ReminderCreate):
    id: int

    model_config = ConfigDict(from_attributes=True)
