import re
from datetime import datetime, timedelta, timezone

from fastapi import HTTPException
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.calendar_event import CalendarEvent
from app.models.list import SmartList, SmartListItem
from app.models.memory import PersonalMemory
from app.models.reminder import Reminder


VALID_RECURRENCE = {"none", "daily", "weekly", "monthly", "yearly"}


# ---------------------------------------------------------
# Date / time helpers
#
# Everything is stored as naive UTC. The AI works in the user's
# LOCAL time, so tz_offset_minutes (minutes ahead of UTC, India = 330)
# is used to convert between the two.
# ---------------------------------------------------------

def _local_to_utc(local_value: datetime, tz_offset_minutes: int):
    return local_value - timedelta(minutes=tz_offset_minutes)


def _utc_to_local(utc_value: datetime, tz_offset_minutes: int):
    return utc_value + timedelta(minutes=tz_offset_minutes)


def _format_local(utc_value: datetime, tz_offset_minutes: int) -> str:
    local_value = _utc_to_local(utc_value, tz_offset_minutes)
    return local_value.strftime("%a %d %b, %I:%M %p")


def _parse_iso(value, tz_offset_minutes: int):
    """
    Parse an ISO string into naive UTC.
    Values with a timezone ("Z" / "+05:30") are converted to UTC;
    values without one are treated as the user's local time.
    """

    if not value or not isinstance(value, str):
        return None

    text = value.strip().replace("Z", "+00:00")

    try:
        parsed = datetime.fromisoformat(text)
    except ValueError:
        return None

    if parsed.tzinfo is not None:
        return parsed.astimezone(timezone.utc).replace(tzinfo=None)

    return _local_to_utc(parsed, tz_offset_minutes)


def _parse_time_text(value):
    """'18:00', '6 pm', '6:30pm' -> (hour, minute) or None."""

    if not value:
        return None

    match = re.match(
        r"^\s*(\d{1,2})(?::(\d{2}))?\s*(am|pm)?\s*$",
        str(value),
        flags=re.IGNORECASE,
    )

    if not match:
        return None

    hour = int(match.group(1))
    minute = int(match.group(2) or 0)
    meridiem = (match.group(3) or "").lower()

    if meridiem == "pm" and hour < 12:
        hour += 12
    elif meridiem == "am" and hour == 12:
        hour = 0

    if hour > 23 or minute > 59:
        return None

    return hour, minute


def _resolve_local_date(value, local_now: datetime):
    """'today' / 'tomorrow' / 'YYYY-MM-DD' -> date or None."""

    if not value:
        return None

    text = str(value).strip().lower()

    if text == "today":
        return local_now.date()

    if text == "tomorrow":
        return (local_now + timedelta(days=1)).date()

    try:
        return datetime.fromisoformat(text[:10]).date()
    except ValueError:
        return None


def _resolve_datetime(
    data: dict,
    iso_key: str,
    tz_offset_minutes: int,
):
    """
    Return a naive UTC datetime from data[iso_key], falling back to
    data["date"] + data["time"] if the model used those instead.
    """

    parsed = _parse_iso(data.get(iso_key), tz_offset_minutes)

    if parsed:
        return parsed

    local_now = _utc_to_local(
        datetime.utcnow(),
        tz_offset_minutes,
    )

    day = _resolve_local_date(data.get("date"), local_now)
    clock = _parse_time_text(data.get("time"))

    if day and clock:
        local_value = datetime(
            day.year,
            day.month,
            day.day,
            clock[0],
            clock[1],
        )

        return _local_to_utc(local_value, tz_offset_minutes)

    return None


# ---------------------------------------------------------
# Lookup helpers
# ---------------------------------------------------------

def _find_list(db: Session, user_id: int, data: dict):
    list_id = data.get("list_id")

    list_name = (
        data.get("list_name")
        or data.get("name")
        or data.get("list")
        or ""
    ).strip()

    query = db.query(SmartList).filter(
        SmartList.user_id == user_id
    )

    if list_id is not None:
        return query.filter(SmartList.id == list_id).first()

    if list_name:
        return query.filter(
            SmartList.name.ilike(list_name)
        ).first()

    return None


def _find_item(db: Session, user_id: int, data: dict):
    """Find a list item by item_id, or by its text (and list name)."""

    item_id = data.get("item_id")

    query = (
        db.query(SmartListItem)
        .join(SmartList, SmartList.id == SmartListItem.list_id)
        .filter(SmartList.user_id == user_id)
    )

    if item_id is not None:
        return query.filter(SmartListItem.id == item_id).first()

    item_text = (
        data.get("item_text")
        or data.get("text")
        or data.get("item")
        or ""
    ).strip()

    if not item_text:
        return None

    list_name = (data.get("list_name") or "").strip()

    if list_name:
        query = query.filter(SmartList.name.ilike(list_name))

    exact = query.filter(
        SmartListItem.text.ilike(item_text)
    ).first()

    if exact:
        return exact

    return query.filter(
        SmartListItem.text.ilike(f"%{item_text}%")
    ).first()


# ---------------------------------------------------------
# Main entry point
# ---------------------------------------------------------

def execute_action(
    action: str,
    data: dict,
    db: Session,
    user_id: int,
    tz_offset_minutes: int = 0,
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

        if not title:
            raise ValueError("Reminder title is required.")

        remind_at = _resolve_datetime(
            data,
            "remind_at",
            tz_offset_minutes,
        )

        if remind_at is None:
            raise ValueError(
                "I couldn't work out the reminder time. "
                "Try something like 'remind me to call mom "
                "tomorrow at 6 PM'."
            )

        recurrence_type = (
            data.get("recurrence_type") or "none"
        ).strip().lower()

        if recurrence_type not in VALID_RECURRENCE:
            recurrence_type = "none"

        reminder = Reminder(
            user_id=user_id,
            title=title,
            description=data.get("description"),
            remind_at=remind_at,
            recurrence_type=recurrence_type,
            recurrence_day=data.get("recurrence_day"),
            is_active=True,
        )

        db.add(reminder)
        db.commit()
        db.refresh(reminder)

        when = _format_local(remind_at, tz_offset_minutes)

        return {
            "success": True,
            "message": (
                f"Reminder '{reminder.title}' set for {when}."
            ),
            "id": reminder.id,
        }

    # ---------------------------------------------------------
    # CREATE EVENT
    # ---------------------------------------------------------
    if action == "CREATE_EVENT":
        title = (data.get("title") or "").strip()

        if not title:
            raise ValueError("Event title is required.")

        start_time = _resolve_datetime(
            data,
            "start_time",
            tz_offset_minutes,
        )

        if start_time is None:
            raise ValueError(
                "I couldn't work out the event time. "
                "Try 'add dentist on Friday at 4 PM'."
            )

        end_time = _parse_iso(
            data.get("end_time"),
            tz_offset_minutes,
        ) or (start_time + timedelta(hours=1))

        event = CalendarEvent(
            user_id=user_id,
            title=title,
            description=data.get("description"),
            start_time=start_time,
            end_time=end_time,
            reminder_enabled=0,
            tz_offset_minutes=tz_offset_minutes,
            recurrence_type="none",
        )

        db.add(event)
        db.commit()
        db.refresh(event)

        when = _format_local(start_time, tz_offset_minutes)

        return {
            "success": True,
            "message": f"Event '{event.title}' added for {when}.",
            "id": event.id,
        }

    # ---------------------------------------------------------
    # GET NEXT EVENT / SCHEDULE
    # ---------------------------------------------------------
    if action == "GET_NEXT_EVENT":
        now_utc = datetime.utcnow()
        local_now = _utc_to_local(now_utc, tz_offset_minutes)

        day = _resolve_local_date(
            data.get("date"),
            local_now,
        )

        if day:
            local_start = datetime(day.year, day.month, day.day)
            window_start = _local_to_utc(
                local_start,
                tz_offset_minutes,
            )
            window_end = window_start + timedelta(days=1)
            label = day.strftime("%A, %d %b")
        else:
            window_start = now_utc
            window_end = now_utc + timedelta(days=7)
            label = "the next 7 days"

        events = (
            db.query(CalendarEvent)
            .filter(
                CalendarEvent.user_id == user_id,
                CalendarEvent.start_time >= window_start,
                CalendarEvent.start_time < window_end,
            )
            .order_by(CalendarEvent.start_time.asc())
            .all()
        )

        reminders = (
            db.query(Reminder)
            .filter(
                Reminder.user_id == user_id,
                Reminder.is_active == True,  # noqa: E712
                Reminder.remind_at >= window_start,
                Reminder.remind_at < window_end,
            )
            .order_by(Reminder.remind_at.asc())
            .all()
        )

        entries = [
            (event.start_time, f"Event: {event.title}")
            for event in events
        ] + [
            (reminder.remind_at, f"Reminder: {reminder.title}")
            for reminder in reminders
        ]

        entries.sort(key=lambda entry: entry[0])

        if not entries:
            message = f"You have nothing scheduled for {label}."
        else:
            lines = [
                f"{_format_local(when, tz_offset_minutes)} - {text}"
                for when, text in entries
            ]

            message = (
                f"Here's what you have for {label}:\n"
                + "\n".join(lines)
            )

        return {
            "success": True,
            "message": message,
            "count": len(entries),
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

        # created_at is a DateTime column with a default, so it must
        # NOT be given an ISO string (SQLite rejects that).
        smart_list = SmartList(
            user_id=user_id,
            name=name,
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
        text = (
            data.get("text")
            or data.get("item")
            or data.get("item_text")
            or ""
        ).strip()

        if not text:
            raise ValueError("List item text is required.")

        smart_list = _find_list(db, user_id, data)

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
    # VIEW LIST
    # ---------------------------------------------------------
    if action == "VIEW_LIST":
        smart_list = _find_list(db, user_id, data)

        if not smart_list:
            raise HTTPException(
                status_code=404,
                detail="List not found.",
            )

        items = (
            db.query(SmartListItem)
            .filter(SmartListItem.list_id == smart_list.id)
            .order_by(SmartListItem.id.asc())
            .all()
        )

        if not items:
            message = f"Your '{smart_list.name}' list is empty."
        else:
            lines = [
                f"{'[x]' if item.completed else '[ ]'} {item.text}"
                for item in items
            ]

            message = (
                f"Your '{smart_list.name}' list:\n"
                + "\n".join(lines)
            )

        return {
            "success": True,
            "message": message,
            "id": smart_list.id,
        }

    # ---------------------------------------------------------
    # COMPLETE LIST ITEM
    # ---------------------------------------------------------
    if action == "COMPLETE_LIST_ITEM":
        item = _find_item(db, user_id, data)

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
        item = _find_item(db, user_id, data)

        if not item:
            raise HTTPException(
                status_code=404,
                detail="List item not found.",
            )

        item_id = item.id
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
        smart_list = _find_list(db, user_id, data)

        if not smart_list:
            raise HTTPException(
                status_code=404,
                detail="List not found.",
            )

        # Read these BEFORE deleting; the object is unusable afterwards.
        deleted_id = smart_list.id
        deleted_name = smart_list.name

        db.query(SmartListItem).filter(
            SmartListItem.list_id == deleted_id
        ).delete(synchronize_session=False)

        db.delete(smart_list)
        db.commit()

        return {
            "success": True,
            "message": f"List '{deleted_name}' deleted successfully.",
            "id": deleted_id,
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
    # SEARCH MEMORY
    # ---------------------------------------------------------
    if action == "SEARCH_MEMORY":
        query_text = (
            data.get("query")
            or data.get("text")
            or ""
        ).strip()

        query = db.query(PersonalMemory).filter(
            PersonalMemory.user_id == user_id
        )

        if query_text:
            like = f"%{query_text}%"

            query = query.filter(
                or_(
                    PersonalMemory.title.ilike(like),
                    PersonalMemory.content.ilike(like),
                )
            )

        memories = (
            query.order_by(PersonalMemory.created_at.desc())
            .limit(5)
            .all()
        )

        if not memories:
            message = "I couldn't find anything saved about that."
        else:
            lines = [
                f"- {memory.title}: {memory.content}"
                for memory in memories
            ]

            message = "Here's what I found:\n" + "\n".join(lines)

        return {
            "success": True,
            "message": message,
            "count": len(memories),
        }

    # ---------------------------------------------------------
    # UNSUPPORTED ACTION
    # ---------------------------------------------------------
    raise ValueError(f"Unsupported action: {action}")
