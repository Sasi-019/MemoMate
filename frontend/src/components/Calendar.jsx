import { useEffect, useState } from "react";
import FullCalendar from "@fullcalendar/react";
import dayGridPlugin from "@fullcalendar/daygrid";
import interactionPlugin from "@fullcalendar/interaction";
import "./Calendar.css";

const API_URL = "https://memomate-af77.onrender.com";

const REMINDER_OPTIONS = [
    {
        value: "before",
        label: "Before event",
        description: "Remind me before this event",
    },
    {
        value: "after",
        label: "After event",
        description: "Remind me after this event",
    },
    {
        value: "specific",
        label: "At a specific time",
        description: "Remind me once at a chosen time",
    },
    {
        value: "daily",
        label: "Every day",
        description: "Remind me every day",
    },
    {
        value: "weekly",
        label: "Every week",
        description: "Remind me every week",
    },
    {
        value: "monthly",
        label: "Every month",
        description: "Remind me every month",
    },
    {
        value: "yearly",
        label: "Every year",
        description: "Remind me every year",
    },
    {
        value: "custom",
        label: "Custom",
        description: "Choose a custom date and time",
    },
];

const WEEKDAYS = [
    { value: "monday", label: "Monday" },
    { value: "tuesday", label: "Tuesday" },
    { value: "wednesday", label: "Wednesday" },
    { value: "thursday", label: "Thursday" },
    { value: "friday", label: "Friday" },
    { value: "saturday", label: "Saturday" },
    { value: "sunday", label: "Sunday" },
];

function Calendar() {
    const [events, setEvents] = useState([]);
    const [selectedDate, setSelectedDate] = useState(null);

    const [title, setTitle] = useState("");
    const [description, setDescription] = useState("");

    const [startTime, setStartTime] = useState("10:00");
    const [endTime, setEndTime] = useState("11:00");

    // -------------------------------------------------
    // Reminder state
    // -------------------------------------------------

    const [reminderEnabled, setReminderEnabled] = useState(false);

    const [reminderType, setReminderType] = useState("before");

    const [reminderValue, setReminderValue] = useState(30);

    const [reminderUnit, setReminderUnit] = useState("minutes");

    const [reminderDate, setReminderDate] = useState("");

    const [reminderTime, setReminderTime] = useState("18:00");

    const [reminderDay, setReminderDay] = useState("monday");

    const [reminderMonth, setReminderMonth] = useState(1);

    const [editingEventId, setEditingEventId] = useState(null);

    // -------------------------------------------------
    // Fetch events
    // -------------------------------------------------

    useEffect(() => {
        fetch(`${API_URL}/events`)
            .then((response) => {
                if (!response.ok) {
                    throw new Error("Failed to fetch events");
                }

                return response.json();
            })
            .then((data) => {
                const formattedEvents = data.map((event) => ({
                    id: event.id,
                    title: event.title,
                    start: event.start_time,
                    end: event.end_time,

                    extendedProps: {
                        description: event.description,

                        reminder_enabled:
                            event.reminder_enabled,

                        reminder_type:
                            event.reminder_type,

                        reminder_value:
                            event.reminder_value,

                        reminder_unit:
                            event.reminder_unit,

                        reminder_datetime:
                            event.reminder_datetime,

                        reminder_time:
                            event.reminder_time,

                        reminder_day:
                            event.reminder_day,

                        reminder_month:
                            event.reminder_month,
                    },
                }));

                setEvents(formattedEvents);
            })
            .catch((error) => {
                console.error(
                    "Error fetching events:",
                    error
                );
            });
    }, []);

    // -------------------------------------------------
    // Reset form
    // -------------------------------------------------

    const resetForm = () => {
        setTitle("");
        setDescription("");

        setStartTime("10:00");
        setEndTime("11:00");

        setReminderEnabled(false);
        setReminderType("before");
        setReminderValue(30);
        setReminderUnit("minutes");

        setReminderDate("");
        setReminderTime("18:00");
        setReminderDay("monday");
        setReminderMonth(1);

        setSelectedDate(null);
        setEditingEventId(null);
    };

    // -------------------------------------------------
    // Open create modal
    // -------------------------------------------------

    const handleDateClick = (info) => {
        setEditingEventId(null);

        setSelectedDate(info.dateStr);

        setTitle("");
        setDescription("");

        setStartTime("10:00");
        setEndTime("11:00");

        setReminderEnabled(false);
        setReminderType("before");
        setReminderValue(30);
        setReminderUnit("minutes");

        setReminderDate(`${info.dateStr}`);
        setReminderTime("18:00");
        setReminderDay("monday");
        setReminderMonth(
            Number(info.dateStr.slice(5, 7))
        );
    };

    // -------------------------------------------------
    // Open edit modal
    // -------------------------------------------------

    const handleEventClick = (info) => {
        const event = info.event;
        const props = event.extendedProps;

        setEditingEventId(event.id);

        setSelectedDate(
            event.startStr.slice(0, 10)
        );

        setTitle(event.title);

        setDescription(
            props.description || ""
        );

        if (event.start) {
            setStartTime(
                event.start
                    .toTimeString()
                    .slice(0, 5)
            );
        }

        if (event.end) {
            setEndTime(
                event.end
                    .toTimeString()
                    .slice(0, 5)
            );
        }

        setReminderEnabled(
            Boolean(props.reminder_enabled)
        );

        setReminderType(
            props.reminder_type || "before"
        );

        setReminderValue(
            props.reminder_value || 30
        );

        setReminderUnit(
            props.reminder_unit || "minutes"
        );

        if (props.reminder_datetime) {
            const dateTime =
                new Date(
                    props.reminder_datetime
                );

            if (!Number.isNaN(dateTime.getTime())) {
                const year =
                    dateTime.getFullYear();

                const month = String(
                    dateTime.getMonth() + 1
                ).padStart(2, "0");

                const day = String(
                    dateTime.getDate()
                ).padStart(2, "0");

                setReminderDate(
                    `${year}-${month}-${day}`
                );
            }
        } else {
            setReminderDate(
                event.startStr.slice(0, 10)
            );
        }

        setReminderTime(
            props.reminder_time || "18:00"
        );

        setReminderDay(
            props.reminder_day || "monday"
        );

        setReminderMonth(
            props.reminder_month ||
                Number(
                    event.startStr.slice(5, 7)
                )
        );
    };

    // -------------------------------------------------
    // Create reminder datetime
    // -------------------------------------------------

    const buildReminderDateTime = () => {
        if (
            !reminderDate ||
            !reminderTime
        ) {
            return null;
        }

        return `${reminderDate}T${reminderTime}:00`;
    };

    // -------------------------------------------------
    // Reminder validation
    // -------------------------------------------------

    const validateReminder = () => {
        if (!reminderEnabled) {
            return true;
        }

        if (
            reminderType === "before" ||
            reminderType === "after"
        ) {
            if (
                !reminderValue ||
                Number(reminderValue) <= 0
            ) {
                alert(
                    "Please enter a valid reminder time."
                );

                return false;
            }
        }

        if (
            reminderType === "specific" ||
            reminderType === "custom"
        ) {
            if (
                !reminderDate ||
                !reminderTime
            ) {
                alert(
                    "Please choose a reminder date and time."
                );

                return false;
            }
        }

        if (reminderType === "daily") {
            if (!reminderTime) {
                alert(
                    "Please choose a reminder time."
                );

                return false;
            }
        }

        if (reminderType === "weekly") {
            if (
                !reminderDay ||
                !reminderTime
            ) {
                alert(
                    "Please choose a weekday and time."
                );

                return false;
            }
        }

        if (reminderType === "monthly") {
            const day = Number(reminderDay);

            if (
                !day ||
                day < 1 ||
                day > 31 ||
                !reminderTime
            ) {
                alert(
                    "Please choose a valid day and time."
                );

                return false;
            }
        }

        if (reminderType === "yearly") {
            const day = Number(reminderDay);

            if (
                !day ||
                day < 1 ||
                day > 31 ||
                !reminderMonth ||
                !reminderTime
            ) {
                alert(
                    "Please choose a valid month, day and time."
                );

                return false;
            }
        }

        return true;
    };

    // -------------------------------------------------
    // Save event
    // -------------------------------------------------

    const handleSaveEvent = () => {
        if (!title.trim()) {
            alert(
                "Please enter an event title."
            );

            return;
        }

        if (!selectedDate) {
            alert(
                "Please select a date."
            );

            return;
        }

        if (!validateReminder()) {
            return;
        }

        // ---------------------------------------------
        // Build reminder fields
        // ---------------------------------------------

        let reminder_datetime = null;
        let reminder_time = null;
        let reminder_day = null;
        let reminder_month = null;

        let finalReminderValue = null;
        let finalReminderUnit = null;

        if (reminderEnabled) {
            if (
                reminderType === "before" ||
                reminderType === "after"
            ) {
                finalReminderValue =
                    Number(reminderValue);

                finalReminderUnit =
                    reminderUnit;
            }

            if (
                reminderType === "specific" ||
                reminderType === "custom"
            ) {
                reminder_datetime =
                    buildReminderDateTime();
            }

            if (
                reminderType === "daily"
            ) {
                reminder_time =
                    reminderTime;
            }

            if (
                reminderType === "weekly"
            ) {
                reminder_day =
                    reminderDay;

                reminder_time =
                    reminderTime;
            }

            if (
                reminderType === "monthly"
            ) {
                reminder_day =
                    String(reminderDay);

                reminder_time =
                    reminderTime;
            }

            if (
                reminderType === "yearly"
            ) {
                reminder_month =
                    Number(reminderMonth);

                reminder_day =
                    String(reminderDay);

                reminder_time =
                    reminderTime;
            }
        }

        const eventData = {
            title: title.trim(),

            description:
                description.trim() || null,

            start_time:
                `${selectedDate}T${startTime}:00`,

            end_time:
                `${selectedDate}T${endTime}:00`,

            // -----------------------------------------
            // Reminder
            // -----------------------------------------

            reminder_enabled:
                reminderEnabled ? 1 : 0,

            reminder_type:
                reminderEnabled
                    ? reminderType
                    : null,

            reminder_value:
                finalReminderValue,

            reminder_unit:
                finalReminderUnit,

            reminder_datetime:
                reminder_datetime,

            reminder_time:
                reminder_time,

            reminder_day:
                reminder_day,

            reminder_month:
                reminder_month,

            // -----------------------------------------
            // Event recurrence
            // -----------------------------------------

            recurrence_type: "none",

            recurrence_day: null,
        };

        const url = editingEventId
            ? `${API_URL}/events/${editingEventId}`
            : `${API_URL}/events`;

        const method = editingEventId
            ? "PUT"
            : "POST";

        fetch(url, {
            method,

            headers: {
                "Content-Type":
                    "application/json",
            },

            body: JSON.stringify(
                eventData
            ),
        })
            .then((response) => {
                if (!response.ok) {
                    throw new Error(
                        "Failed to save event"
                    );
                }

                return response.json();
            })
            .then((savedEvent) => {
                const formattedEvent = {
                    id: savedEvent.id,

                    title:
                        savedEvent.title,

                    start:
                        savedEvent.start_time,

                    end:
                        savedEvent.end_time,

                    extendedProps: {
                        description:
                            savedEvent.description,

                        reminder_enabled:
                            savedEvent.reminder_enabled,

                        reminder_type:
                            savedEvent.reminder_type,

                        reminder_value:
                            savedEvent.reminder_value,

                        reminder_unit:
                            savedEvent.reminder_unit,

                        reminder_datetime:
                            savedEvent.reminder_datetime,

                        reminder_time:
                            savedEvent.reminder_time,

                        reminder_day:
                            savedEvent.reminder_day,

                        reminder_month:
                            savedEvent.reminder_month,
                    },
                };

                if (editingEventId) {
                    setEvents(
                        (currentEvents) =>
                            currentEvents.map(
                                (event) =>
                                    String(
                                        event.id
                                    ) ===
                                    String(
                                        editingEventId
                                    )
                                        ? formattedEvent
                                        : event
                            )
                    );
                } else {
                    setEvents(
                        (currentEvents) => [
                            ...currentEvents,
                            formattedEvent,
                        ]
                    );
                }

                resetForm();
            })
            .catch((error) => {
                console.error(
                    "Error saving event:",
                    error
                );

                alert(
                    "Could not save the event."
                );
            });
    };

    // -------------------------------------------------
    // Delete event
    // -------------------------------------------------

    const handleDeleteEvent = () => {
        if (!editingEventId) {
            return;
        }

        const confirmed =
            window.confirm(
                "Are you sure you want to delete this event?"
            );

        if (!confirmed) {
            return;
        }

        fetch(
            `${API_URL}/events/${editingEventId}`,
            {
                method: "DELETE",
            }
        )
            .then((response) => {
                if (!response.ok) {
                    throw new Error(
                        "Failed to delete event"
                    );
                }

                return response.json();
            })
            .then(() => {
                setEvents(
                    (currentEvents) =>
                        currentEvents.filter(
                            (event) =>
                                String(
                                    event.id
                                ) !==
                                String(
                                    editingEventId
                                )
                        )
                );

                resetForm();
            })
            .catch((error) => {
                console.error(
                    "Error deleting event:",
                    error
                );

                alert(
                    "Could not delete the event."
                );
            });
    };

    // -------------------------------------------------
    // Reminder preview
    // -------------------------------------------------

    const getReminderPreview = () => {
        if (!reminderEnabled) {
            return "No reminder set.";
        }

        if (reminderType === "before") {
            return `You'll be reminded ${reminderValue} ${reminderUnit} before the event.`;
        }

        if (reminderType === "after") {
            return `You'll be reminded ${reminderValue} ${reminderUnit} after the event.`;
        }

        if (
            reminderType === "specific"
        ) {
            if (
                !reminderDate ||
                !reminderTime
            ) {
                return "Choose a date and time.";
            }

            return `You'll be reminded on ${reminderDate} at ${reminderTime}.`;
        }

        if (reminderType === "daily") {
            return `Every day at ${reminderTime}.`;
        }

        if (reminderType === "weekly") {
            return `Every ${reminderDay} at ${reminderTime}.`;
        }

        if (reminderType === "monthly") {
            return `On the ${reminderDay}${getOrdinal(
                Number(reminderDay)
            )} of every month at ${reminderTime}.`;
        }

        if (reminderType === "yearly") {
            const monthName =
                new Date(
                    2000,
                    Number(reminderMonth) - 1,
                    1
                ).toLocaleString(
                    "en-US",
                    {
                        month: "long",
                    }
                );

            return `Every ${monthName} ${reminderDay} at ${reminderTime}.`;
        }

        if (reminderType === "custom") {
            if (
                !reminderDate ||
                !reminderTime
            ) {
                return "Choose a custom date and time.";
            }

            return `Custom reminder: ${reminderDate} at ${reminderTime}.`;
        }

        return "";
    };

    // -------------------------------------------------
    // JSX
    // -------------------------------------------------

    return (
        <div className="calendar-page">

            {/* Header */}

            <div className="calendar-header">

                <div>
                    <h2>Calendar</h2>

                    <p>
                        Keep track of everything
                        you need to remember.
                    </p>
                </div>

                <button
                    className="add-event-button"
                    onClick={() => {
                        const today =
                            new Date()
                                .toISOString()
                                .split("T")[0];

                        handleDateClick({
                            dateStr: today,
                        });
                    }}
                >
                    + Add Event
                </button>

            </div>

            {/* Calendar */}

            <div className="calendar-card">

                <FullCalendar
                    plugins={[
                        dayGridPlugin,
                        interactionPlugin,
                    ]}
                    initialView="dayGridMonth"
                    events={events}
                    dateClick={
                        handleDateClick
                    }
                    eventClick={
                        handleEventClick
                    }
                    height="auto"
                />

            </div>

            {/* Modal */}

            {selectedDate && (
                <div
                    className="modal-overlay"
                    onClick={(event) => {
                        if (
                            event.target ===
                            event.currentTarget
                        ) {
                            resetForm();
                        }
                    }}
                >

                    <div className="event-modal">

                        {/* Modal Header */}

                        <div className="modal-header">

                            <div>

                                <h3>
                                    {editingEventId
                                        ? "Edit Event"
                                        : "Add Event"}
                                </h3>

                                <p>
                                    {editingEventId
                                        ? "Update your event details."
                                        : "Add something you want to remember."}
                                </p>

                            </div>

                            <button
                                className="close-button"
                                onClick={
                                    resetForm
                                }
                            >
                                ×
                            </button>

                        </div>

                        {/* Title */}

                        <div className="form-group">

                            <label>
                                Event title
                            </label>

                            <input
                                type="text"
                                placeholder="e.g. DBMS Class"
                                value={title}
                                onChange={(event) =>
                                    setTitle(
                                        event.target
                                            .value
                                    )
                                }
                            />

                        </div>

                        {/* Description */}

                        <div className="form-group">

                            <label>
                                Description
                            </label>

                            <textarea
                                placeholder="Add some details..."
                                value={
                                    description
                                }
                                onChange={(event) =>
                                    setDescription(
                                        event.target
                                            .value
                                    )
                                }
                            />

                        </div>

                        {/* Date */}

                        <div className="form-group">

                            <label>
                                Date
                            </label>

                            <input
                                type="date"
                                value={
                                    selectedDate
                                }
                                onChange={(event) =>
                                    setSelectedDate(
                                        event.target
                                            .value
                                    )
                                }
                            />

                        </div>

                        {/* Time */}

                        <div className="time-row">

                            <div className="form-group">

                                <label>
                                    Start time
                                </label>

                                <input
                                    type="time"
                                    value={
                                        startTime
                                    }
                                    onChange={(
                                        event
                                    ) =>
                                        setStartTime(
                                            event
                                                .target
                                                .value
                                        )
                                    }
                                />

                            </div>

                            <div className="form-group">

                                <label>
                                    End time
                                </label>

                                <input
                                    type="time"
                                    value={
                                        endTime
                                    }
                                    onChange={(
                                        event
                                    ) =>
                                        setEndTime(
                                            event
                                                .target
                                                .value
                                        )
                                    }
                                />

                            </div>

                        </div>

                        {/* Reminder */}

                        <div className="reminder-section">

                            <div className="reminder-header">

                                <div>

                                    <label>
                                        Reminder
                                    </label>

                                    <p>
                                        Choose when MemoMate
                                        should remind you.
                                    </p>

                                </div>

                                <label className="reminder-toggle">

                                    <input
                                        type="checkbox"
                                        checked={
                                            reminderEnabled
                                        }
                                        onChange={(
                                            event
                                        ) =>
                                            setReminderEnabled(
                                                event
                                                    .target
                                                    .checked
                                            )
                                        }
                                    />

                                    <span>
                                        Remind me
                                    </span>

                                </label>

                            </div>

                            {reminderEnabled && (
                                <>

                                    {/* Reminder type */}

                                    <div className="form-group">

                                        <label>
                                            When should I remind you?
                                        </label>

                                        <select
                                            value={
                                                reminderType
                                            }
                                            onChange={(
                                                event
                                            ) => {
                                                const type =
                                                    event
                                                        .target
                                                        .value;

                                                setReminderType(
                                                    type
                                                );

                                                if (
                                                    type ===
                                                    "specific"
                                                ) {
                                                    setReminderDate(
                                                        selectedDate
                                                    );
                                                }

                                                if (
                                                    type ===
                                                    "custom"
                                                ) {
                                                    setReminderDate(
                                                        selectedDate
                                                    );
                                                }
                                            }}
                                        >

                                            {REMINDER_OPTIONS.map(
                                                (option) => (
                                                    <option
                                                        key={
                                                            option.value
                                                        }
                                                        value={
                                                            option.value
                                                        }
                                                    >
                                                        {
                                                            option.label
                                                        }
                                                    </option>
                                                )
                                            )}

                                        </select>

                                    </div>

                                    {/* Before / After */}

                                    {(
                                        reminderType ===
                                            "before" ||
                                        reminderType ===
                                            "after"
                                    ) && (

                                        <div className="reminder-value-row">

                                            <div className="form-group">

                                                <label>
                                                    How much?
                                                </label>

                                                <input
                                                    type="number"
                                                    min="1"
                                                    value={
                                                        reminderValue
                                                    }
                                                    onChange={(
                                                        event
                                                    ) =>
                                                        setReminderValue(
                                                            event
                                                                .target
                                                                .value
                                                        )
                                                    }
                                                />

                                            </div>

                                            <div className="form-group">

                                                <label>
                                                    Unit
                                                </label>

                                                <select
                                                    value={
                                                        reminderUnit
                                                    }
                                                    onChange={(
                                                        event
                                                    ) =>
                                                        setReminderUnit(
                                                            event
                                                                .target
                                                                .value
                                                        )
                                                    }
                                                >

                                                    <option value="minutes">
                                                        Minutes
                                                    </option>

                                                    <option value="hours">
                                                        Hours
                                                    </option>

                                                    <option value="days">
                                                        Days
                                                    </option>

                                                </select>

                                            </div>

                                        </div>
                                    )}

                                    {/* Specific */}

                                    {reminderType ===
                                        "specific" && (

                                        <div className="reminder-custom-grid">

                                            <div className="form-group">

                                                <label>
                                                    Date
                                                </label>

                                                <input
                                                    type="date"
                                                    value={
                                                        reminderDate
                                                    }
                                                    onChange={(
                                                        event
                                                    ) =>
                                                        setReminderDate(
                                                            event
                                                                .target
                                                                .value
                                                        )
                                                    }
                                                />

                                            </div>

                                            <div className="form-group">

                                                <label>
                                                    Time
                                                </label>

                                                <input
                                                    type="time"
                                                    value={
                                                        reminderTime
                                                    }
                                                    onChange={(
                                                        event
                                                    ) =>
                                                        setReminderTime(
                                                            event
                                                                .target
                                                                .value
                                                        )
                                                    }
                                                />

                                            </div>

                                        </div>
                                    )}

                                    {/* Daily */}

                                    {reminderType ===
                                        "daily" && (

                                        <div className="form-group">

                                            <label>
                                                Every day at
                                            </label>

                                            <input
                                                type="time"
                                                value={
                                                    reminderTime
                                                }
                                                onChange={(
                                                    event
                                                ) =>
                                                    setReminderTime(
                                                        event
                                                            .target
                                                            .value
                                                    )
                                                }
                                            />

                                        </div>
                                    )}

                                    {/* Weekly */}

                                    {reminderType ===
                                        "weekly" && (

                                        <div className="reminder-value-row">

                                            <div className="form-group">

                                                <label>
                                                    Day
                                                </label>

                                                <select
                                                    value={
                                                        reminderDay
                                                    }
                                                    onChange={(
                                                        event
                                                    ) =>
                                                        setReminderDay(
                                                            event
                                                                .target
                                                                .value
                                                        )
                                                    }
                                                >

                                                    {WEEKDAYS.map(
                                                        (
                                                            day
                                                        ) => (
                                                            <option
                                                                key={
                                                                    day.value
                                                                }
                                                                value={
                                                                    day.value
                                                                }
                                                            >
                                                                {
                                                                    day.label
                                                                }
                                                            </option>
                                                        )
                                                    )}

                                                </select>

                                            </div>

                                            <div className="form-group">

                                                <label>
                                                    Time
                                                </label>

                                                <input
                                                    type="time"
                                                    value={
                                                        reminderTime
                                                    }
                                                    onChange={(
                                                        event
                                                    ) =>
                                                        setReminderTime(
                                                            event
                                                                .target
                                                                .value
                                                        )
                                                    }
                                                />

                                            </div>

                                        </div>
                                    )}

                                    {/* Monthly */}

                                    {reminderType ===
                                        "monthly" && (

                                        <div className="reminder-value-row">

                                            <div className="form-group">

                                                <label>
                                                    Day of month
                                                </label>

                                                <select
                                                    value={
                                                        reminderDay
                                                    }
                                                    onChange={(
                                                        event
                                                    ) =>
                                                        setReminderDay(
                                                            event
                                                                .target
                                                                .value
                                                        )
                                                    }
                                                >

                                                    {Array.from(
                                                        {
                                                            length: 31,
                                                        },
                                                        (
                                                            _,
                                                            index
                                                        ) => (
                                                            <option
                                                                key={
                                                                    index +
                                                                    1
                                                                }
                                                                value={
                                                                    index +
                                                                    1
                                                                }
                                                            >
                                                                {index +
                                                                    1}
                                                                {getOrdinal(
                                                                    index +
                                                                        1
                                                                )}
                                                            </option>
                                                        )
                                                    )}

                                                </select>

                                            </div>

                                            <div className="form-group">

                                                <label>
                                                    Time
                                                </label>

                                                <input
                                                    type="time"
                                                    value={
                                                        reminderTime
                                                    }
                                                    onChange={(
                                                        event
                                                    ) =>
                                                        setReminderTime(
                                                            event
                                                                .target
                                                                .value
                                                        )
                                                    }
                                                />

                                            </div>

                                        </div>
                                    )}

                                    {/* Yearly */}

                                    {reminderType ===
                                        "yearly" && (

                                        <div className="reminder-custom-grid">

                                            <div className="form-group">

                                                <label>
                                                    Month
                                                </label>

                                                <select
                                                    value={
                                                        reminderMonth
                                                    }
                                                    onChange={(
                                                        event
                                                    ) =>
                                                        setReminderMonth(
                                                            Number(
                                                                event
                                                                    .target
                                                                    .value
                                                            )
                                                        )
                                                    }
                                                >

                                                    {[
                                                        "January",
                                                        "February",
                                                        "March",
                                                        "April",
                                                        "May",
                                                        "June",
                                                        "July",
                                                        "August",
                                                        "September",
                                                        "October",
                                                        "November",
                                                        "December",
                                                    ].map(
                                                        (
                                                            month,
                                                            index
                                                        ) => (
                                                            <option
                                                                key={
                                                                    index +
                                                                    1
                                                                }
                                                                value={
                                                                    index +
                                                                    1
                                                                }
                                                            >
                                                                {
                                                                    month
                                                                }
                                                            </option>
                                                        )
                                                    )}

                                                </select>

                                            </div>

                                            <div className="form-group">

                                                <label>
                                                    Day
                                                </label>

                                                <select
                                                    value={
                                                        reminderDay
                                                    }
                                                    onChange={(
                                                        event
                                                    ) =>
                                                        setReminderDay(
                                                            event
                                                                .target
                                                                .value
                                                        )
                                                    }
                                                >

                                                    {Array.from(
                                                        {
                                                            length: 31,
                                                        },
                                                        (
                                                            _,
                                                            index
                                                        ) => (
                                                            <option
                                                                key={
                                                                    index +
                                                                    1
                                                                }
                                                                value={
                                                                    index +
                                                                    1
                                                                }
                                                            >
                                                                {index +
                                                                    1}
                                                            </option>
                                                        )
                                                    )}

                                                </select>

                                            </div>

                                            <div className="form-group">

                                                <label>
                                                    Time
                                                </label>

                                                <input
                                                    type="time"
                                                    value={
                                                        reminderTime
                                                    }
                                                    onChange={(
                                                        event
                                                    ) =>
                                                        setReminderTime(
                                                            event
                                                                .target
                                                                .value
                                                        )
                                                    }
                                                />

                                            </div>

                                        </div>
                                    )}

                                    {/* Custom */}

                                    {reminderType ===
                                        "custom" && (

                                        <div className="reminder-custom-grid">

                                            <div className="form-group">

                                                <label>
                                                    Date
                                                </label>

                                                <input
                                                    type="date"
                                                    value={
                                                        reminderDate
                                                    }
                                                    onChange={(
                                                        event
                                                    ) =>
                                                        setReminderDate(
                                                            event
                                                                .target
                                                                .value
                                                        )
                                                    }
                                                />

                                            </div>

                                            <div className="form-group">

                                                <label>
                                                    Time
                                                </label>

                                                <input
                                                    type="time"
                                                    value={
                                                        reminderTime
                                                    }
                                                    onChange={(
                                                        event
                                                    ) =>
                                                        setReminderTime(
                                                            event
                                                                .target
                                                                .value
                                                        )
                                                    }
                                                />

                                            </div>

                                        </div>
                                    )}

                                    {/* Preview */}

                                    <div className="reminder-preview">

                                        <strong>
                                            Reminder preview
                                        </strong>

                                        <p>
                                            {getReminderPreview()}
                                        </p>

                                    </div>

                                </>
                            )}

                        </div>

                        {/* Actions */}

                        <div className="modal-actions">

                            {editingEventId && (
                                <button
                                    className="delete-button"
                                    onClick={
                                        handleDeleteEvent
                                    }
                                >
                                    Delete
                                </button>
                            )}

                            <div className="right-actions">

                                <button
                                    className="cancel-button"
                                    onClick={
                                        resetForm
                                    }
                                >
                                    Cancel
                                </button>

                                <button
                                    className="save-button"
                                    onClick={
                                        handleSaveEvent
                                    }
                                >
                                    {editingEventId
                                        ? "Save Changes"
                                        : "Add Event"}
                                </button>

                            </div>

                        </div>

                    </div>

                </div>
            )}

        </div>
    );
}


// -----------------------------------------------------
// Helper: ordinal numbers
// -----------------------------------------------------

function getOrdinal(number) {
    if (
        number >= 11 &&
        number <= 13
    ) {
        return "th";
    }

    switch (number % 10) {
        case 1:
            return "st";

        case 2:
            return "nd";

        case 3:
            return "rd";

        default:
            return "th";
    }
}

export default Calendar;