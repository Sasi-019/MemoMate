from pydantic import BaseModel, ConfigDict

from app.schemas.utc import UTCDateTime


class CalendarEventCreate(BaseModel):

    title: str

    description: str | None = None

    start_time: UTCDateTime

    end_time: UTCDateTime | None = None

    # -------------------------------------------------
    # Reminder
    # -------------------------------------------------

    reminder_enabled: int = 0

    reminder_type: str | None = None

    reminder_value: int | None = None

    reminder_unit: str | None = None

    reminder_datetime: UTCDateTime | None = None

    # Local wall-clock time such as "18:00". It is interpreted using
    # tz_offset_minutes below (needed for daily/weekly/monthly/yearly).
    reminder_time: str | None = None

    reminder_day: str | None = None

    reminder_month: int | None = None

    # Minutes the user's timezone is AHEAD of UTC (India = 330).
    tz_offset_minutes: int = 0

    # -------------------------------------------------
    # Event recurrence
    # -------------------------------------------------

    recurrence_type: str = "none"

    recurrence_day: str | None = None


class CalendarEventResponse(CalendarEventCreate):

    id: int

    model_config = ConfigDict(from_attributes=True)
