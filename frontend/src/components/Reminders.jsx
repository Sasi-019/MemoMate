import { useEffect, useState } from "react";
import { apiFetch, localToUtcIso } from "../services/api";

function Reminders() {
    const [reminders, setReminders] = useState([]);
    const [loadError, setLoadError] = useState("");

    const [showForm, setShowForm] = useState(false);
    const [editingId, setEditingId] = useState(null);

    const [title, setTitle] = useState("");
    const [description, setDescription] = useState("");
    const [remindAt, setRemindAt] = useState("");
    const [recurrenceType, setRecurrenceType] = useState("none");
    const [recurrenceDay, setRecurrenceDay] = useState("");

    const fetchReminders = async () => {
        try {
            setLoadError("");

            const response = await apiFetch("/reminders");
            const data = await response.json().catch(() => null);

            if (!response.ok) {
                throw new Error(
                    (data && typeof data.detail === "string"
                        && data.detail) ||
                        "Could not load reminders."
                );
            }

            // Never store a non-array: reminders.map() would crash
            // the whole page (blank white screen).
            setReminders(Array.isArray(data) ? data : []);
        } catch (error) {
            console.error("Error fetching reminders:", error);
            setLoadError(
                error.message || "Could not load reminders."
            );
        }
    };

    useEffect(() => {
        fetchReminders();
    }, []);

    const resetForm = () => {
        setTitle("");
        setDescription("");
        setRemindAt("");
        setRecurrenceType("none");
        setRecurrenceDay("");
        setEditingId(null);
        setShowForm(false);
    };

    const handleSubmit = async (e) => {
        e.preventDefault();

        if (!title || !remindAt) {
            alert("Please enter a title and date/time.");
            return;
        }

        // Send UTC so the server's scheduler fires at the right moment
        // (the datetime-local input gives the user's LOCAL time).
        const remindAtUtc = localToUtcIso(remindAt);

        if (!remindAtUtc) {
            alert("Please enter a valid date and time.");
            return;
        }

        const reminderData = {
            title,
            description: description || null,
            remind_at: remindAtUtc,
            recurrence_type: recurrenceType,
            recurrence_day:
                recurrenceType === "weekly"
                    ? recurrenceDay
                    : null,
            is_active: true,
        };

        try {
            const path = editingId
                ? `/reminders/${editingId}`
                : "/reminders";

            const response = await apiFetch(path, {
                method: editingId ? "PUT" : "POST",
                body: JSON.stringify(reminderData),
            });

            if (!response.ok) {
                throw new Error("Failed to save reminder");
            }

            await fetchReminders();
            resetForm();
        } catch (error) {
            console.error("Error saving reminder:", error);
            alert(error.message || "Could not save the reminder.");
        }
    };

    const handleEdit = (reminder) => {
        setEditingId(reminder.id);
        setTitle(reminder.title);
        setDescription(reminder.description || "");

        const date = new Date(reminder.remind_at);

        const localDateTime = new Date(
            date.getTime() - date.getTimezoneOffset() * 60000
        )
            .toISOString()
            .slice(0, 16);

        setRemindAt(localDateTime);
        setRecurrenceType(reminder.recurrence_type);
        setRecurrenceDay(reminder.recurrence_day || "");

        setShowForm(true);
    };

    const handleDelete = async (id) => {
        const confirmed = window.confirm(
            "Are you sure you want to delete this reminder?"
        );

        if (!confirmed) return;

        try {
            const response = await apiFetch(
                `/reminders/${id}`,
                {
                    method: "DELETE",
                }
            );

            if (!response.ok) {
                throw new Error("Failed to delete reminder");
            }

            await fetchReminders();
        } catch (error) {
            console.error("Error deleting reminder:", error);
            alert(error.message || "Could not delete the reminder.");
        }
    };

    const formatDate = (dateString) => {
        return new Date(dateString).toLocaleString([], {
            dateStyle: "medium",
            timeStyle: "short",
        });
    };

    const getRecurrenceText = (reminder) => {
        if (reminder.recurrence_type === "daily") {
            return "Every day";
        }

        if (reminder.recurrence_type === "weekly") {
            return `Every week`;
        }

        if (reminder.recurrence_type === "monthly") {
            return "Every month";
        }

        if (reminder.recurrence_type === "yearly") {
            return "Every year";
        }

        return "One time";
    };

    return (
        <section className="mt-10 rounded-3xl bg-white p-6 shadow-sm ring-1 ring-slate-200 sm:p-8">

            {/* Header */}
            <div className="mb-6 flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">

                <div>
                    <div className="flex items-center gap-3">
                        <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-slate-900 text-xl text-white">
                            🔔
                        </div>

                        <div>
                            <h2 className="text-2xl font-bold tracking-tight text-slate-900">
                                Reminders
                            </h2>

                            <p className="text-sm text-slate-500">
                                Never forget something important.
                            </p>
                        </div>
                    </div>
                </div>

                <button
                    onClick={() => setShowForm(true)}
                    className="rounded-xl bg-slate-900 px-5 py-3 text-sm font-semibold text-white shadow-sm transition hover:bg-slate-800 active:scale-[0.98]"
                >
                    + Add Reminder
                </button>
            </div>

            {loadError && (
                <div className="mb-4 rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
                    ⚠️ {loadError}
                </div>
            )}

            {/* Reminder list */}
            {reminders.length === 0 ? (
                <div className="rounded-2xl border border-dashed border-slate-300 bg-slate-50 px-6 py-12 text-center">
                    <div className="mb-3 text-4xl">🔔</div>

                    <h3 className="font-semibold text-slate-800">
                        No reminders yet
                    </h3>

                    <p className="mt-1 text-sm text-slate-500">
                        Add your first reminder so MemoMate can help you remember.
                    </p>
                </div>
            ) : (
                <div className="grid gap-4 md:grid-cols-2">

                    {reminders.map((reminder) => (
                        <div
                            key={reminder.id}
                            className="group rounded-2xl border border-slate-200 bg-slate-50 p-5 transition hover:-translate-y-0.5 hover:border-slate-300 hover:shadow-md"
                        >

                            <div className="flex items-start justify-between gap-4">

                                <div className="min-w-0">

                                    <h3 className="truncate text-lg font-bold text-slate-900">
                                        {reminder.title}
                                    </h3>

                                    {reminder.description && (
                                        <p className="mt-1 text-sm text-slate-500">
                                            {reminder.description}
                                        </p>
                                    )}

                                </div>

                                <span className="shrink-0 rounded-full bg-white px-3 py-1 text-xs font-semibold text-slate-600 ring-1 ring-slate-200">
                                    {getRecurrenceText(reminder)}
                                </span>

                            </div>

                            <div className="mt-5 flex items-center gap-2 text-sm text-slate-600">
                                <span>🕐</span>
                                <span>
                                    {formatDate(reminder.remind_at)}
                                </span>
                            </div>

                            <div className="mt-4 flex gap-2 border-t border-slate-200 pt-4">

                                <button
                                    onClick={() => handleEdit(reminder)}
                                    className="rounded-lg bg-white px-4 py-2 text-sm font-semibold text-slate-700 ring-1 ring-slate-200 transition hover:bg-slate-100"
                                >
                                    Edit
                                </button>

                                <button
                                    onClick={() => handleDelete(reminder.id)}
                                    className="rounded-lg px-4 py-2 text-sm font-semibold text-red-600 transition hover:bg-red-50"
                                >
                                    Delete
                                </button>

                            </div>
                        </div>
                    ))}

                </div>
            )}

            {/* Modal */}
            {showForm && (
                <div
                    className="fixed inset-0 z-50 flex items-center justify-center bg-slate-950/50 p-4 backdrop-blur-sm"
                    onMouseDown={(e) => {
                        if (e.target === e.currentTarget) {
                            resetForm();
                        }
                    }}
                >

                    <div className="w-full max-w-lg rounded-3xl bg-white p-6 shadow-2xl sm:p-8">

                        {/* Modal header */}
                        <div className="mb-6 flex items-start justify-between">

                            <div>
                                <h2 className="text-2xl font-bold text-slate-900">
                                    {editingId
                                        ? "Edit Reminder"
                                        : "Add Reminder"}
                                </h2>

                                <p className="mt-1 text-sm text-slate-500">
                                    Tell MemoMate what you don't want to forget.
                                </p>
                            </div>

                            <button
                                onClick={resetForm}
                                className="text-2xl font-semibold text-slate-400 transition hover:text-slate-700"
                            >
                                ×
                            </button>

                        </div>

                        <form
                            onSubmit={handleSubmit}
                            className="space-y-5"
                        >

                            {/* Title */}
                            <div>
                                <label className="mb-2 block text-sm font-semibold text-slate-700">
                                    Reminder title
                                </label>

                                <input
                                    type="text"
                                    placeholder="e.g. Review assignments"
                                    value={title}
                                    onChange={(e) =>
                                        setTitle(e.target.value)
                                    }
                                    className="w-full rounded-xl border border-slate-300 px-4 py-3 text-slate-900 outline-none transition placeholder:text-slate-400 focus:border-slate-900 focus:ring-2 focus:ring-slate-900/10"
                                />
                            </div>

                            {/* Description */}
                            <div>
                                <label className="mb-2 block text-sm font-semibold text-slate-700">
                                    Description
                                </label>

                                <textarea
                                    rows="3"
                                    placeholder="Add some details..."
                                    value={description}
                                    onChange={(e) =>
                                        setDescription(e.target.value)
                                    }
                                    className="w-full resize-none rounded-xl border border-slate-300 px-4 py-3 text-slate-900 outline-none transition placeholder:text-slate-400 focus:border-slate-900 focus:ring-2 focus:ring-slate-900/10"
                                />
                            </div>

                            {/* Date/time */}
                            <div>
                                <label className="mb-2 block text-sm font-semibold text-slate-700">
                                    Date & time
                                </label>

                                <input
                                    type="datetime-local"
                                    value={remindAt}
                                    onChange={(e) =>
                                        setRemindAt(e.target.value)
                                    }
                                    className="w-full rounded-xl border border-slate-300 px-4 py-3 text-slate-900 outline-none transition focus:border-slate-900 focus:ring-2 focus:ring-slate-900/10"
                                />
                            </div>

                            {/* Recurrence */}
                            <div>
                                <label className="mb-2 block text-sm font-semibold text-slate-700">
                                    Repeat
                                </label>

                                <select
                                    value={recurrenceType}
                                    onChange={(e) => {
                                        setRecurrenceType(e.target.value);

                                        if (
                                            e.target.value !==
                                            "weekly"
                                        ) {
                                            setRecurrenceDay("");
                                        }
                                    }}
                                    className="w-full rounded-xl border border-slate-300 bg-white px-4 py-3 text-slate-900 outline-none transition focus:border-slate-900 focus:ring-2 focus:ring-slate-900/10"
                                >
                                    <option value="none">
                                        One time
                                    </option>

                                    <option value="daily">
                                        Every day
                                    </option>

                                    <option value="weekly">
                                        Every week
                                    </option>
                                </select>
                            </div>

                            {/* Weekly day */}
                            {recurrenceType === "weekly" && (
                                <div>
                                    <label className="mb-2 block text-sm font-semibold text-slate-700">
                                        Day of the week
                                    </label>

                                    <select
                                        value={recurrenceDay}
                                        onChange={(e) =>
                                            setRecurrenceDay(
                                                e.target.value
                                            )
                                        }
                                        className="w-full rounded-xl border border-slate-300 bg-white px-4 py-3 text-slate-900 outline-none transition focus:border-slate-900 focus:ring-2 focus:ring-slate-900/10"
                                    >
                                        <option value="">
                                            Select day
                                        </option>

                                        <option value="Monday">
                                            Monday
                                        </option>

                                        <option value="Tuesday">
                                            Tuesday
                                        </option>

                                        <option value="Wednesday">
                                            Wednesday
                                        </option>

                                        <option value="Thursday">
                                            Thursday
                                        </option>

                                        <option value="Friday">
                                            Friday
                                        </option>

                                        <option value="Saturday">
                                            Saturday
                                        </option>

                                        <option value="Sunday">
                                            Sunday
                                        </option>
                                    </select>
                                </div>
                            )}

                            {/* Buttons */}
                            <div className="flex justify-end gap-3 pt-3">

                                <button
                                    type="button"
                                    onClick={resetForm}
                                    className="rounded-xl bg-slate-100 px-5 py-3 text-sm font-semibold text-slate-700 transition hover:bg-slate-200"
                                >
                                    Cancel
                                </button>

                                <button
                                    type="submit"
                                    className="rounded-xl bg-slate-900 px-5 py-3 text-sm font-semibold text-white shadow-sm transition hover:bg-slate-800 active:scale-[0.98]"
                                >
                                    {editingId
                                        ? "Save Changes"
                                        : "Add Reminder"}
                                </button>

                            </div>

                        </form>
                    </div>
                </div>
            )}
        </section>
    );
}

export default Reminders;