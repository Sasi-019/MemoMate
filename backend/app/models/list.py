from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime
from datetime import datetime

from app.database.database import Base


class SmartList(Base):
    __tablename__ = "smart_lists"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    user_id = Column(
        Integer,
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    name = Column(
        String,
        nullable=False,
    )

    created_at = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )


class SmartListItem(Base):
    __tablename__ = "smart_list_items"

    id = Column(
        Integer,
        primary_key=True,
        index=True,
    )

    list_id = Column(
        Integer,
        ForeignKey("smart_lists.id"),
        nullable=False,
        index=True,
    )

    text = Column(
        String,
        nullable=False,
    )

    completed = Column(
        Boolean,
        default=False,
        nullable=False,
    )