from sqlalchemy import Column, Integer, String, DateTime, Boolean, ForeignKey
from app.database.database import Base


class Reminder(Base):
    __tablename__ = "reminders"

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

    remind_at = Column(DateTime, nullable=False)

    recurrence_type = Column(
        String,
        default="none",
        nullable=False
    )

    recurrence_day = Column(String, nullable=True)

    is_active = Column(
        Boolean,
        default=True,
        nullable=False
    )
