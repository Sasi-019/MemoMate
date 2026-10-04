import os
from typing import List

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import inspect, text
from sqlalchemy.orm import Session

from app.database.database import Base, engine, get_db

# Models
from app.models.calendar_event import CalendarEvent
from app.models.reminder import Reminder
from app.models.notification import Notification  # noqa: F401  (registers table)
from app.models.session import UserSession  # noqa: F401  (registers table)
from app.models.list import SmartList  # noqa: F401  (registers table)
from app.models.memory import PersonalMemory  # noqa: F401  (registers table)
from app.models.user import User

# Schemas
from app.schemas.calendar_event import (
    CalendarEventCreate,
    CalendarEventResponse,
)
from app.schemas.reminder import (
    ReminderCreate,
    ReminderResponse,
)

# Authentication
from app.dependencies.auth import get_current_user

# Routers
from app.api.assistant import router as assistant_router
from app.api.voice import router as voice_router
from app.api.lists import router as lists_router
from app.api.memory import router as memory_router
from app.api.notifications import router as notifications_router
from app.api.auth import router as auth_router

# Scheduler
from app.services.reminder_scheduler import (
    start_scheduler,
    stop_scheduler,
)


app = FastAPI(
    title="MemoMate API",
    version="1.0.0",
)


# ============================================================
# DATABASE
# ============================================================

Base.metadata.create_all(bind=engine)


def ensure_new_columns():
    """
    create_all() only creates MISSING TABLES; it never adds columns to an
    existing table. If you already have a database from before
    calendar_events.tz_offset_minutes existed, every /events query (and the
    reminder scheduler) would fail with "no such column". Add it if needed.
    """
    inspector = inspect(engine)

    if "calendar_events" not in inspector.get_table_names():
        return

    columns = {
        column["name"]
        for column in inspector.get_columns("calendar_events")
    }

    if "tz_offset_minutes" not in columns:
        with engine.begin() as connection:
            connection.execute(
                text(
                    "ALTER TABLE calendar_events "
                    "ADD COLUMN tz_offset_minutes "
                    "INTEGER NOT NULL DEFAULT 0"
                )
            )


ensure_new_columns()


# ============================================================
# CORS
# ============================================================
# FRONTEND_URL        -> main frontend origin
# EXTRA_CORS_ORIGINS  -> optional, comma-separated extra origins

FRONTEND_URL = os.getenv(
    "FRONTEND_URL",
    "http://localhost:5173",
)

allowed_origins = {
    FRONTEND_URL.rstrip("/"),
    "http://localhost:5173",
    "https://memomate-frontend-vjt2.onrender.com",
}

for origin in os.getenv("EXTRA_CORS_ORIGINS", "").split(","):
    origin = origin.strip().rstrip("/")

    if origin:
        allowed_origins.add(origin)

app.add_middleware(
    CORSMiddleware,
    allow_origins=sorted(allowed_origins),
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ============================================================
# ROUTERS
# ============================================================

app.include_router(auth_router)
app.include_router(assistant_router)
app.include_router(voice_router)
app.include_router(lists_router)
app.include_router(memory_router)
app.include_router(notifications_router)


# ============================================================
# HOME
# ============================================================

@app.get("/")
def home():
    return {
        "message": "MemoMate backend is running"
    }


# ============================================================
# CALENDAR EVENTS
# ============================================================

@app.post(
    "/events",
    response_model=CalendarEventResponse,
)
def create_event(
    event: CalendarEventCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    new_event = CalendarEvent(
        user_id=current_user.id,
        title=event.title,
        description=event.description,
        start_time=event.start_time,
        end_time=event.end_time,
        reminder_enabled=event.reminder_enabled,
        reminder_type=event.reminder_type,
        reminder_value=event.reminder_value,
        reminder_unit=event.reminder_unit,
        reminder_datetime=event.reminder_datetime,
        reminder_time=event.reminder_time,
        reminder_day=event.reminder_day,
        reminder_month=event.reminder_month,
        tz_offset_minutes=event.tz_offset_minutes,
        recurrence_type=event.recurrence_type,
        recurrence_day=event.recurrence_day,
    )

    db.add(new_event)
    db.commit()
    db.refresh(new_event)

    return new_event


@app.get(
    "/events",
    response_model=List[CalendarEventResponse],
)
def get_events(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    events = (
        db.query(CalendarEvent)
        .filter(
            CalendarEvent.user_id == current_user.id
        )
        .all()
    )

    return events


@app.put(
    "/events/{event_id}",
    response_model=CalendarEventResponse,
)
def update_event(
    event_id: int,
    event: CalendarEventCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    existing_event = (
        db.query(CalendarEvent)
        .filter(
            CalendarEvent.id == event_id,
            CalendarEvent.user_id == current_user.id,
        )
        .first()
    )

    if existing_event is None:
        raise HTTPException(
            status_code=404,
            detail="Event not found",
        )

    existing_event.title = event.title
    existing_event.description = event.description
    existing_event.start_time = event.start_time
    existing_event.end_time = event.end_time
    existing_event.reminder_enabled = event.reminder_enabled
    existing_event.reminder_type = event.reminder_type
    existing_event.reminder_value = event.reminder_value
    existing_event.reminder_unit = event.reminder_unit
    existing_event.reminder_datetime = event.reminder_datetime
    existing_event.reminder_time = event.reminder_time
    existing_event.reminder_day = event.reminder_day
    existing_event.reminder_month = event.reminder_month
    existing_event.tz_offset_minutes = event.tz_offset_minutes
    existing_event.recurrence_type = event.recurrence_type
    existing_event.recurrence_day = event.recurrence_day

    db.commit()
    db.refresh(existing_event)

    return existing_event


@app.delete("/events/{event_id}")
def delete_event(
    event_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    existing_event = (
        db.query(CalendarEvent)
        .filter(
            CalendarEvent.id == event_id,
            CalendarEvent.user_id == current_user.id,
        )
        .first()
    )

    if existing_event is None:
        raise HTTPException(
            status_code=404,
            detail="Event not found",
        )

    db.delete(existing_event)
    db.commit()

    return {
        "message": "Event deleted successfully"
    }


# ============================================================
# REMINDERS
# ============================================================

@app.post(
    "/reminders",
    response_model=ReminderResponse,
)
def create_reminder(
    reminder: ReminderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    new_reminder = Reminder(
        user_id=current_user.id,
        title=reminder.title,
        description=reminder.description,
        remind_at=reminder.remind_at,
        recurrence_type=reminder.recurrence_type,
        recurrence_day=reminder.recurrence_day,
        is_active=reminder.is_active,
    )

    db.add(new_reminder)
    db.commit()
    db.refresh(new_reminder)

    return new_reminder


@app.get(
    "/reminders",
    response_model=List[ReminderResponse],
)
def get_reminders(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    reminders = (
        db.query(Reminder)
        .filter(
            Reminder.user_id == current_user.id
        )
        .all()
    )

    return reminders


@app.put(
    "/reminders/{reminder_id}",
    response_model=ReminderResponse,
)
def update_reminder(
    reminder_id: int,
    reminder: ReminderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    existing_reminder = (
        db.query(Reminder)
        .filter(
            Reminder.id == reminder_id,
            Reminder.user_id == current_user.id,
        )
        .first()
    )

    if existing_reminder is None:
        raise HTTPException(
            status_code=404,
            detail="Reminder not found",
        )

    existing_reminder.title = reminder.title
    existing_reminder.description = reminder.description
    existing_reminder.remind_at = reminder.remind_at
    existing_reminder.recurrence_type = reminder.recurrence_type
    existing_reminder.recurrence_day = reminder.recurrence_day
    existing_reminder.is_active = reminder.is_active

    db.commit()
    db.refresh(existing_reminder)

    return existing_reminder


@app.delete("/reminders/{reminder_id}")
def delete_reminder(
    reminder_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    existing_reminder = (
        db.query(Reminder)
        .filter(
            Reminder.id == reminder_id,
            Reminder.user_id == current_user.id,
        )
        .first()
    )

    if existing_reminder is None:
        raise HTTPException(
            status_code=404,
            detail="Reminder not found",
        )

    db.delete(existing_reminder)
    db.commit()

    return {
        "message": "Reminder deleted successfully"
    }


# NOTE: notification endpoints live in app/api/notifications.py
# (they were duplicated here before and have been removed).


# ============================================================
# SCHEDULER
# ============================================================

@app.on_event("startup")
def startup_event():
    start_scheduler()


@app.on_event("shutdown")
def shutdown_event():
    stop_scheduler()
