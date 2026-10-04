from datetime import datetime

from sqlalchemy.orm import Session
from fastapi import HTTPException

from app.models.reminder import Reminder
from app.models.list import SmartList, SmartListItem
from app.models.memory import PersonalMemory


def execute_action(
    action: str,
    data: dict,
    db: Session,
    user_id: int,
):
    """
    Execute a validated AI action for the currently authenticated user.

    The AI decides WHAT should happen.
    This action engine decides HOW to safely perform it.
    """

    data = data or {}

    # ---------------------------------------------------------
    # CREATE REMINDER
    # ---------------------------------------------------------
    if action == "CREATE_REMINDER":
        title = (data.get("title") or "").strip()
        remind_at = data.get("remind_at")

        if not title:
            raise ValueError("Reminder title is required.")

        if not remind_at:
            raise ValueError("Reminder time is required.")

        reminder = Reminder(
            user_id=user_id,
            title=title,
            description=data.get("description"),
            remind_at=remind_at,
            recurrence_type=data.get("recurrence_type", "none"),
            recurrence_day=data.get("recurrence_day"),
            is_active=data.get("is_active", True),
        )

        db.add(reminder)
        db.commit()
        db.refresh(reminder)

        return {
            "success": True,
            "message": f"Reminder '{reminder.title}' created successfully.",
            "id": reminder.id,
        }

    # ---------------------------------------------------------
    # CREATE LIST
    # ---------------------------------------------------------
    if action == "CREATE_LIST":
        # Accept multiple common field names from the LLM.
        name = (
            data.get("name")
            or data.get("list_name")
            or data.get("title")
            or ""
        ).strip()

        if not name:
            raise ValueError("List name is required.")

        existing = (
            db.query(SmartList)
            .filter(
                SmartList.user_id == user_id,
                SmartList.name.ilike(name),
            )
            .first()
        )

        if existing:
            return {
                "success": False,
                "message": f"You already have a list named '{existing.name}'.",
                "id": existing.id,
            }

        smart_list = SmartList(
            user_id=user_id,
            name=name,
            created_at=datetime.utcnow().isoformat(),
        )

        db.add(smart_list)
        db.commit()
        db.refresh(smart_list)

        return {
            "success": True,
            "message": f"List '{smart_list.name}' created successfully.",
            "id": smart_list.id,
        }

    # ---------------------------------------------------------
    # ADD LIST ITEM
    # ---------------------------------------------------------
    if action == "ADD_LIST_ITEM":
        list_id = data.get("list_id")

        list_name = (
            data.get("list_name")
            or data.get("name")
            or ""
        ).strip()

        text = (
            data.get("text")
            or data.get("item")
            or data.get("item_text")
            or ""
        ).strip()

        if not text:
            raise ValueError("List item text is required.")

        smart_list = None

        if list_id is not None:
            smart_list = (
                db.query(SmartList)
                .filter(
                    SmartList.id == list_id,
                    SmartList.user_id == user_id,
                )
                .first()
            )

        elif list_name:
            smart_list = (
                db.query(SmartList)
                .filter(
                    SmartList.user_id == user_id,
                    SmartList.name.ilike(list_name),
                )
                .first()
            )

        if not smart_list:
            raise HTTPException(
                status_code=404,
                detail="List not found.",
            )

        item = SmartListItem(
            list_id=smart_list.id,
            text=text,
            completed=False,
        )

        db.add(item)
        db.commit()
        db.refresh(item)

        return {
            "success": True,
            "message": f"Added '{text}' to '{smart_list.name}'.",
            "id": item.id,
            "list_id": smart_list.id,
        }

    # ---------------------------------------------------------
    # COMPLETE LIST ITEM
    # ---------------------------------------------------------
    if action == "COMPLETE_LIST_ITEM":
        item_id = data.get("item_id")

        if item_id is None:
            raise ValueError("List item ID is required.")

        item = (
            db.query(SmartListItem)
            .join(
                SmartList,
                SmartList.id == SmartListItem.list_id,
            )
            .filter(
                SmartListItem.id == item_id,
                SmartList.user_id == user_id,
            )
            .first()
        )

        if not item:
            raise HTTPException(
                status_code=404,
                detail="List item not found.",
            )

        item.completed = True
        db.commit()

        return {
            "success": True,
            "message": f"Marked '{item.text}' as completed.",
            "id": item.id,
        }

    # ---------------------------------------------------------
    # REMOVE LIST ITEM
    # ---------------------------------------------------------
    if action == "REMOVE_LIST_ITEM":
        item_id = data.get("item_id")

        if item_id is None:
            raise ValueError("List item ID is required.")

        item = (
            db.query(SmartListItem)
            .join(
                SmartList,
                SmartList.id == SmartListItem.list_id,
            )
            .filter(
                SmartListItem.id == item_id,
                SmartList.user_id == user_id,
            )
            .first()
        )

        if not item:
            raise HTTPException(
                status_code=404,
                detail="List item not found.",
            )

        item_text = item.text

        db.delete(item)
        db.commit()

        return {
            "success": True,
            "message": f"Removed '{item_text}' from the list.",
            "id": item_id,
        }

    # ---------------------------------------------------------
    # DELETE LIST
    # ---------------------------------------------------------
    if action == "DELETE_LIST":
        list_id = data.get("list_id")

        list_name = (
            data.get("name")
            or data.get("list_name")
            or ""
        ).strip()

        smart_list = None

        if list_id is not None:
            smart_list = (
                db.query(SmartList)
                .filter(
                    SmartList.id == list_id,
                    SmartList.user_id == user_id,
                )
                .first()
            )

        elif list_name:
            smart_list = (
                db.query(SmartList)
                .filter(
                    SmartList.user_id == user_id,
                    SmartList.name.ilike(list_name),
                )
                .first()
            )

        if not smart_list:
            raise HTTPException(
                status_code=404,
                detail="List not found.",
            )

        deleted_name = smart_list.name

        db.query(SmartListItem).filter(
            SmartListItem.list_id == smart_list.id
        ).delete(synchronize_session=False)

        db.delete(smart_list)
        db.commit()

        return {
            "success": True,
            "message": f"List '{deleted_name}' deleted successfully.",
            "id": smart_list.id,
        }

    # ---------------------------------------------------------
    # SAVE MEMORY
    # ---------------------------------------------------------
    if action == "SAVE_MEMORY":
        title = (data.get("title") or "").strip()
        content = (data.get("content") or "").strip()

        if not title:
            raise ValueError("Memory title is required.")

        if not content:
            raise ValueError("Memory content is required.")

        memory = PersonalMemory(
            user_id=user_id,
            title=title,
            content=content,
        )

        db.add(memory)
        db.commit()
        db.refresh(memory)

        return {
            "success": True,
            "message": f"Memory '{memory.title}' saved successfully.",
            "id": memory.id,
        }

    # ---------------------------------------------------------
    # UNSUPPORTED ACTION
    # ---------------------------------------------------------
    raise ValueError(f"Unsupported action: {action}")
