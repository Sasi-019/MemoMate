import threading
import time
from datetime import datetime, timedelta

from app.database.database import SessionLocal
from app.models.reminder import Reminder
from app.models.notification import Notification
from app.models.calendar_event import CalendarEvent


_scheduler_thread = None
_stop_event = threading.Event()


def _make_occurrence_key(
    reminder_id=None,
    event_id=None,
    scheduled_for=None,
):
    source = f"reminder:{reminder_id}" if reminder_id else f"event:{event_id}"
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
    return True


def _process_reminders(db, now):
    reminders = (
        db.query(Reminder)
        .filter(
            Reminder.is_active == True,
            Reminder.remind_at <= now,
        )
        .all()
    )

    changed = False

    for reminder in reminders:
        created = _create_notification(
            db=db,
            user_id=reminder.user_id,
            title=reminder.title,
            message=reminder.description or "You have a reminder.",
            scheduled_for=reminder.remind_at,
            reminder_id=reminder.id,
        )

        if created:
            changed = True

        if reminder.recurrence_type == "none":
            reminder.is_active = False
            changed = True

        elif reminder.recurrence_type == "daily":
            reminder.remind_at = reminder.remind_at + timedelta(days=1)
            changed = True

        elif reminder.recurrence_type == "weekly":
            reminder.remind_at = reminder.remind_at + timedelta(weeks=1)
            changed = True

        elif reminder.recurrence_type == "monthly":
            # Keep the same day when possible. For dates such as the
            # 31st, move forward safely to the next valid month date.
            next_month = reminder.remind_at.month + 1
            year = reminder.remind_at.year

            if next_month > 12:
                next_month = 1
                year += 1

            import calendar

            day = min(
                reminder.remind_at.day,
                calendar.monthrange(year, next_month)[1],
            )

            reminder.remind_at = reminder.remind_at.replace(
                year=year,
                month=next_month,
                day=day,
            )
            changed = True

        elif reminder.recurrence_type == "yearly":
            try:
                reminder.remind_at = reminder.remind_at.replace(
                    year=reminder.remind_at.year + 1
                )
            except ValueError:
                # February 29 -> February 28 in a non-leap year.
                reminder.remind_at = reminder.remind_at.replace(
                    year=reminder.remind_at.year + 1,
                    day=28,
                )
            changed = True

        else:
            # Unknown recurrence: prevent an endless notification loop.
            reminder.is_active = False
            changed = True

    return changed


def _process_event_reminders(db, now):
    events = (
        db.query(CalendarEvent)
        .filter(CalendarEvent.reminder_enabled == 1)
        .all()
    )

    changed = False

    for event in events:
        scheduled_for = None

        if event.reminder_type == "before":
            if event.reminder_value is None:
                continue

            minutes = event.reminder_value

            if event.reminder_unit == "hours":
                minutes *= 60
            elif event.reminder_unit == "days":
                minutes *= 60 * 24

            scheduled_for = event.start_time - timedelta(
                minutes=minutes
            )

        elif event.reminder_type == "after":
            if event.reminder_value is None:
                continue

            minutes = event.reminder_value

            if event.reminder_unit == "hours":
                minutes *= 60
            elif event.reminder_unit == "days":
                minutes *= 60 * 24

            scheduled_for = event.end_time or event.start_time
            scheduled_for = scheduled_for + timedelta(
                minutes=minutes
            )

        elif event.reminder_type in ("specific", "custom"):
            scheduled_for = event.reminder_datetime

        if scheduled_for is None:
            continue

        if scheduled_for > now:
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
