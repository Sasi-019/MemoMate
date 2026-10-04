from sqlalchemy import Column, Integer, String, Boolean, ForeignKey
from app.database.database import Base


class SmartList(Base):
    __tablename__ = "smart_lists"

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

    # A list name only needs to be unique for the same user.
    # The API layer will enforce this when creating lists.
    name = Column(String, nullable=False)

    created_at = Column(String, nullable=False)


class SmartListItem(Base):
    __tablename__ = "smart_list_items"

    id = Column(Integer, primary_key=True, index=True)

    list_id = Column(
        Integer,
        ForeignKey("smart_lists.id"),
        nullable=False,
        index=True
    )

    text = Column(String, nullable=False)

    completed = Column(
        Boolean,
        default=False,
        nullable=False
    )
