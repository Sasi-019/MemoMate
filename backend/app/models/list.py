from datetime import datetime

from sqlalchemy import Boolean, Column, DateTime, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.database.database import Base


class SmartList(Base):
    __tablename__ = "smart_lists"

    id = Column(Integer, primary_key=True, index=True)

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

    # Relationship with list items
    items = relationship(
        "SmartListItem",
        back_populates="smart_list",
        cascade="all, delete-orphan",
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

    # Relationship back to the parent list
    smart_list = relationship(
        "SmartList",
        back_populates="items",
    )