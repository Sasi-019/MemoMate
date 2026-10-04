from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from app.database.database import Base


class CalendarEvent(Base):
    __tablename__ = "calendar_events"

    id = Column(Integer, primary_key=True, index=True)

    # -------------------------------------------------
    # User ownership
    # -------------------------------------------------

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        index=True
    )

    title = Column(String, nullable=False)
    description = Column(String, nullable=True)

    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=True)

    # -------------------------------------------------
    # Reminder settings
    # -------------------------------------------------

    reminder_enabled = Column(
        Integer,
        default=0,
        nullable=False
    )

    # before
    # after
    # specific
    # daily
    # weekly
    # monthly
    # yearly
    # custom
    reminder_type = Column(
        String,
        nullable=True
    )

    # Used for:
    # before / after
    # Example: 30 minutes
    reminder_value = Column(
        Integer,
        nullable=True
    )

    # minutes / hours / days
    reminder_unit = Column(
        String,
        nullable=True
    )

    # Used for:
    # specific / custom
    #
    # Example:
    # 2026-10-04 18:00
    reminder_datetime = Column(
        DateTime,
        nullable=True
    )

    # Used for:
    # daily / weekly / monthly / yearly
    #
    # Example:
    # "18:00"
    reminder_time = Column(
        String,
        nullable=True
    )

    # Used for weekly/monthly
    #
    # weekly:
    # monday
    # tuesday
    #
    # monthly:
    # 1
    # 15
    # 30
    reminder_day = Column(
        String,
        nullable=True
    )

    # Used for yearly reminders.
    #
    # Example:
    # 6 = June
    reminder_month = Column(
        Integer,
        nullable=True
    )

    # -------------------------------------------------
    # Event recurrence
    # -------------------------------------------------

    recurrence_type = Column(
        String,
        default="none",
        nullable=False
    )

    recurrence_day = Column(
        String,
        nullable=True
    )
