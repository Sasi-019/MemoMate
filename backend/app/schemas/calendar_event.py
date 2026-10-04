from datetime import datetime
from pydantic import BaseModel


class CalendarEventCreate(BaseModel):

    title: str

    description: str | None = None

    start_time: datetime

    end_time: datetime | None = None

    # -------------------------------------------------
    # Reminder
    # -------------------------------------------------

    reminder_enabled: int = 0

    reminder_type: str | None = None

    reminder_value: int | None = None

    reminder_unit: str | None = None

    reminder_datetime: datetime | None = None

    reminder_time: str | None = None

    reminder_day: str | None = None

    reminder_month: int | None = None

    # -------------------------------------------------
    # Event recurrence
    # -------------------------------------------------

    recurrence_type: str = "none"

    recurrence_day: str | None = None


class CalendarEventResponse(CalendarEventCreate):

    id: int

    class Config:
        from_attributes = True