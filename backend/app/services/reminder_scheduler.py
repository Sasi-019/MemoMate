import calendar
import threading
from datetime import date, datetime, time, timedelta

from app.database.database import SessionLocal
from app.models.reminder import Reminder
from app.models.notification import Notification
from app.models.calendar_event import CalendarEvent


_scheduler_thread = None
_stop_event = threading.Event()

# Notifications older than this are skipped instead of being "caught up"
# (prevents a flood of old alerts after the server has been asleep).
CATCH_UP_WINDOW = timedelta(days=1)

WEEKDAYS = [
    "monday",
    "tuesday",
    "wednesday",
    "thursday",
    "friday",
    "saturday",
    "sunday",
]


def _make_occurrence_key(
    reminder_id=None,
    event_id=None,
    scheduled_for=None,
):
    source = (
        f"reminder:{reminder_id}"
        if reminder_id
        else f"event:{event_id}"
    )
    timestamp = (
        scheduled_for.isoformat()
        if scheduled_for
        else datetime.utcnow().isoformat()
    )
    return f"{source}:{timestamp}"


def _create_notification(
    db,
    user_id,
    title,
    message,
    scheduled_for,
    reminder_id=None,
    event_id=None,
):
    occurrence_key = _make_occurrence_key(
        reminder_id=reminder_id,
        event_id=event_id,
        scheduled_for=scheduled_for,
    )

    existing = (
        db.query(Notification)
        .filter(Notification.occurrence_key == occurrence_key)
        .first()
    )

    if existing:
        return False

    notification = Notification(
        user_id=user_id,
        reminder_id=reminder_id,
        event_id=event_id,
        title=title,
        message=message,
        scheduled_for=scheduled_for,
        created_at=datetime.utcnow(),
        is_read=False,
        occurrence_key=occurrence_key,
    )

    db.add(notification)
    # Flush so a second occurrence in the same loop sees it.
    db.flush()
    return True


# ---------------------------------------------------------
# Plain reminders (Reminders page + AI assistant)
# ---------------------------------------------------------

def _next_occurrence(current, recurrence_type):
    """Return the next remind_at after `current`, or None if one-time/unknown."""

    if recurrence_type == "daily":
        return current + timedelta(days=1)

    if recurrence_type == "weekly":
        return current + timedelta(weeks=1)

    if recurrence_type == "monthly":
        month = current.month + 1
        year = current.year

        if month > 12:
            month = 1
            year += 1

        day = min(
            current.day,
            calendar.monthrange(year, month)[1],
        )

        return current.replace(year=year, month=month, day=day)

    if recurrence_type == "yearly":
        year = current.year + 1
        day = min(
            current.day,
            calendar.monthrange(year, current.month)[1],
        )

        return current.replace(year=year, day=day)

    return None


def _process_reminders(db, now):
    reminders = (
        db.query(Reminder)
        .filter(
            Reminder.is_active == True,  # noqa: E712
            Reminder.remind_at <= now,
        )
        .all()
    )

    changed = False

    for reminder in reminders:
        due = reminder.remind_at

        # Only notify if this occurrence is recent enough.
        if now - due <= CATCH_UP_WINDOW:
            if _create_notification(
                db=db,
                user_id=reminder.user_id,
                title=reminder.title,
                message=reminder.description or "You have a reminder.",
                scheduled_for=due,
                reminder_id=reminder.id,
            ):
                changed = True

        if reminder.recurrence_type == "none":
            reminder.is_active = False
            changed = True
            continue

        following = _next_occurrence(due, reminder.recurrence_type)

        if following is None:
            # Unknown recurrence: stop it so it can't loop forever.
            reminder.is_active = False
            changed = True
            continue

        # Skip every occurrence that is already in the past so a
        # long-sleeping server doesn't send a burst of notifications.
        guard = 0

        while following <= now and guard < 1000:
            following = _next_occurrence(
                following,
                reminder.recurrence_type,
            )
            guard += 1

        reminder.remind_at = following
        changed = True

    return changed


# ---------------------------------------------------------
# Calendar event reminders
# ---------------------------------------------------------

def _to_minutes(value, unit):
    minutes = value

    if unit == "hours":
        minutes *= 60
    elif unit == "days":
        minutes *= 60 * 24

    return minutes


def _parse_hhmm(value):
    try:
        hours, minutes = str(value).split(":")[:2]
        return time(int(hours), int(minutes))
    except (ValueError, TypeError):
        return None


def _latest_recurring_occurrence(event, now):
    """
    Latest scheduled reminder time (naive UTC) that is <= now for
    daily / weekly / monthly / yearly event reminders, or None.

    reminder_time is the user's local wall-clock time, so it is
    shifted using the event's tz_offset_minutes.
    """

    at = _parse_hhmm(event.reminder_time)

    if at is None:
        return None

    offset = timedelta(minutes=event.tz_offset_minutes or 0)
    local_now = now + offset
    rtype = event.reminder_type

    candidate = None

    if rtype == "daily":
        candidate = datetime.combine(local_now.date(), at)

        if candidate > local_now:
            candidate -= timedelta(days=1)

    elif rtype == "weekly":
        name = (event.reminder_day or "").strip().lower()

        if name not in WEEKDAYS:
            return None

        target = WEEKDAYS.index(name)
        days_back = (local_now.weekday() - target) % 7

        candidate = datetime.combine(
            local_now.date() - timedelta(days=days_back),
            at,
        )

        if candidate > local_now:
            candidate -= timedelta(days=7)

    elif rtype == "monthly":
        try:
            wanted_day = int(event.reminder_day)
        except (TypeError, ValueError):
            return None

        year, month = local_now.year, local_now.month

        for _ in range(14):
            day = min(wanted_day, calendar.monthrange(year, month)[1])
            attempt = datetime.combine(date(year, month, day), at)

            if attempt <= local_now:
                candidate = attempt
                break

            month -= 1

            if month == 0:
                month = 12
                year -= 1

    elif rtype == "yearly":
        try:
            wanted_day = int(event.reminder_day)
            wanted_month = int(event.reminder_month)
        except (TypeError, ValueError):
            return None

        if not 1 <= wanted_month <= 12:
            return None

        for year in range(local_now.year, local_now.year - 6, -1):
            day = min(
                wanted_day,
                calendar.monthrange(year, wanted_month)[1],
            )
            attempt = datetime.combine(
                date(year, wanted_month, day),
                at,
            )

            if attempt <= local_now:
                candidate = attempt
                break

    if candidate is None:
        return None

    # Recurring reminders start from the event's own date.
    local_start = event.start_time + offset

    if candidate.date() < local_start.date():
        return None

    return candidate - offset


def _process_event_reminders(db, now):
    events = (
        db.query(CalendarEvent)
        .filter(CalendarEvent.reminder_enabled == 1)
        .all()
    )

    changed = False

    for event in events:
        scheduled_for = None
        rtype = event.reminder_type

        if rtype in ("before", "after"):
            if not event.reminder_value:
                continue

            minutes = _to_minutes(
                event.reminder_value,
                event.reminder_unit,
            )

            if rtype == "before":
                scheduled_for = event.start_time - timedelta(
                    minutes=minutes
                )
            else:
                scheduled_for = (
                    event.end_time or event.start_time
                ) + timedelta(minutes=minutes)

        elif rtype in ("specific", "custom"):
            scheduled_for = event.reminder_datetime

        elif rtype in ("daily", "weekly", "monthly", "yearly"):
            scheduled_for = _latest_recurring_occurrence(event, now)

        if scheduled_for is None:
            continue

        if scheduled_for > now:
            continue

        if now - scheduled_for > CATCH_UP_WINDOW:
            continue

        created = _create_notification(
            db=db,
            user_id=event.user_id,
            title=event.title,
            message=event.description or "You have a scheduled event.",
            scheduled_for=scheduled_for,
            event_id=event.id,
        )

        if created:
            changed = True

    return changed


def _scheduler_loop():
    while not _stop_event.is_set():
        db = SessionLocal()

        try:
            now = datetime.utcnow()

            changed = _process_reminders(
                db,
                now,
            )

            event_changed = _process_event_reminders(
                db,
                now,
            )

            if changed or event_changed:
                db.commit()

        except Exception as exc:
            db.rollback()
            print(
                "[MemoMate Scheduler Error]",
                type(exc).__name__,
                str(exc),
            )

        finally:
            db.close()

        _stop_event.wait(30)


def start_scheduler():
    global _scheduler_thread

    if _scheduler_thread and _scheduler_thread.is_alive():
        return

    _stop_event.clear()

    _scheduler_thread = threading.Thread(
        target=_scheduler_loop,
        name="memomate-reminder-scheduler",
        daemon=True,
    )

    _scheduler_thread.start()

    print("MemoMate reminder scheduler started.")


def stop_scheduler():
    global _scheduler_thread

    _stop_event.set()

    if _scheduler_thread and _scheduler_thread.is_alive():
        _scheduler_thread.join(timeout=2)

    _scheduler_thread = None

    print("MemoMate reminder scheduler stopped.")
