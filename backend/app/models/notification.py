from sqlalchemy import (
    Column,
    Integer,
    String,
    DateTime,
    Boolean,
    ForeignKey,
)

from app.database.database import Base


class Notification(Base):

    __tablename__ = "notifications"

    id = Column(
        Integer,
        primary_key=True,
        index=True
    )

    # -------------------------------------------------
    # User ownership
    # -------------------------------------------------

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        index=True
    )

    reminder_id = Column(
        Integer,
        nullable=True,
        index=True
    )

    event_id = Column(
        Integer,
        nullable=True,
        index=True
    )

    title = Column(
        String,
        nullable=False
    )

    message = Column(
        String,
        nullable=True
    )

    scheduled_for = Column(
        DateTime,
        nullable=True,
        index=True
    )

    created_at = Column(
        DateTime,
        nullable=False
    )

    is_read = Column(
        Boolean,
        default=False,
        nullable=False
    )

    occurrence_key = Column(
        String,
        nullable=False,
        unique=True,
        index=True
    )
