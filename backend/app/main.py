from typing import List

from fastapi import FastAPI, Depends, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from app.database.database import Base, engine, get_db

# Models
from app.models.calendar_event import CalendarEvent
from app.models.reminder import Reminder
from app.models.notification import Notification
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


# ============================================================
# CORS
# ============================================================

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
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


# ============================================================
# NOTIFICATIONS
# ============================================================

@app.get("/notifications")
def get_notifications(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    notifications = (
        db.query(Notification)
        .filter(
            Notification.user_id == current_user.id,
            Notification.is_read == False,
        )
        .order_by(
            Notification.created_at.desc()
        )
        .all()
    )

    return notifications


@app.put(
    "/notifications/{notification_id}/read"
)
def mark_notification_read(
    notification_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    notification = (
        db.query(Notification)
        .filter(
            Notification.id == notification_id,
            Notification.user_id == current_user.id,
        )
        .first()
    )

    if notification is None:
        raise HTTPException(
            status_code=404,
            detail="Notification not found",
        )

    notification.is_read = True
    db.commit()

    return {
        "message": "Notification marked as read"
    }


# ============================================================
# SCHEDULER
# ============================================================

@app.on_event("startup")
def startup_event():
    start_scheduler()


@app.on_event("shutdown")
def shutdown_event():
    stop_scheduler()
