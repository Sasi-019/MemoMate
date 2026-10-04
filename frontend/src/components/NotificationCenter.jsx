import { useEffect, useState } from "react";
import { apiFetch } from "../services/api";

export default function NotificationCenter() {
    const [notifications, setNotifications] =
        useState([]);
    const [open, setOpen] = useState(false);
    const [loading, setLoading] = useState(false);

    async function loadNotifications() {
        setLoading(true);

        try {
            const response = await apiFetch(
                "/notifications"
            );

            if (response.status === 401) {
                setNotifications([]);
                return;
            }

            if (!response.ok) {
                throw new Error(
                    "Failed to load notifications"
                );
            }

            const data = await response.json();

            setNotifications(
                Array.isArray(data) ? data : []
            );
        } catch (error) {
            console.error(
                "Notification loading error:",
                error
            );
        } finally {
            setLoading(false);
        }
    }

    async function markAsRead(id) {
        try {
            const response = await apiFetch(
                `/notifications/${id}/read`,
                {
                    method: "PUT",
                }
            );

            if (!response.ok) {
                throw new Error(
                    "Failed to mark notification as read"
                );
            }

            setNotifications((current) =>
                current.filter(
                    (notification) =>
                        notification.id !== id
                )
            );
        } catch (error) {
            console.error(
                "Notification read error:",
                error
            );
        }
    }

    async function markAllAsRead() {
        try {
            const response = await apiFetch(
                "/notifications/read-all",
                {
                    method: "PUT",
                }
            );

            if (!response.ok) {
                throw new Error(
                    "Failed to mark notifications as read"
                );
            }

            setNotifications([]);
        } catch (error) {
            console.error(
                "Notification read-all error:",
                error
            );
        }
    }

    useEffect(() => {
        loadNotifications();

        const interval = setInterval(
            loadNotifications,
            15000
        );

        return () => clearInterval(interval);
    }, []);

    const unreadCount = notifications.length;

    return (
        <div className="relative">
            <button
                type="button"
                onClick={() => setOpen((value) => !value)}
                className="relative flex h-10 w-10 items-center justify-center rounded-xl border border-slate-200 bg-white text-slate-600 shadow-sm transition hover:bg-slate-50"
                aria-label="Notifications"
            >
                <span className="text-lg">🔔</span>

                {unreadCount > 0 && (
                    <span className="absolute -right-1 -top-1 flex min-h-5 min-w-5 items-center justify-center rounded-full bg-red-500 px-1 text-[10px] font-bold text-white">
                        {unreadCount > 9
                            ? "9+"
                            : unreadCount}
                    </span>
                )}
            </button>

            {open && (
                <>
                    <div
                        className="fixed inset-0 z-30"
                        onClick={() => setOpen(false)}
                    />

                    <div className="absolute right-0 z-40 mt-3 w-[340px] overflow-hidden rounded-2xl border border-slate-200 bg-white shadow-2xl">
                        <div className="flex items-center justify-between border-b border-slate-100 px-4 py-3">
                            <div>
                                <h3 className="font-semibold text-slate-900">
                                    Notifications
                                </h3>

                                <p className="text-xs text-slate-500">
                                    {loading
                                        ? "Checking..."
                                        : unreadCount > 0
                                        ? `${unreadCount} unread`
                                        : "You're all caught up"}
                                </p>
                            </div>

                            {unreadCount > 0 && (
                                <button
                                    type="button"
                                    onClick={
                                        markAllAsRead
                                    }
                                    className="text-xs font-medium text-violet-600 hover:text-violet-700"
                                >
                                    Mark all read
                                </button>
                            )}
                        </div>

                        <div className="max-h-[360px] overflow-y-auto">
                            {notifications.length ===
                            0 ? (
                                <div className="px-5 py-10 text-center">
                                    <div className="mb-3 text-3xl">
                                        ✓
                                    </div>

                                    <p className="text-sm font-medium text-slate-700">
                                        No new
                                        notifications
                                    </p>

                                    <p className="mt-1 text-xs text-slate-400">
                                        Your reminders will
                                        appear here.
                                    </p>
                                </div>
                            ) : (
                                notifications.map(
                                    (notification) => (
                                        <div
                                            key={
                                                notification.id
                                            }
                                            className="border-b border-slate-100 px-4 py-4 last:border-b-0"
                                        >
                                            <div className="flex gap-3">
                                                <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-violet-50 text-sm">
                                                    🔔
                                                </div>

                                                <div className="min-w-0 flex-1">
                                                    <p className="text-sm font-semibold text-slate-900">
                                                        {
                                                            notification.title
                                                        }
                                                    </p>

                                                    {notification.message && (
                                                        <p className="mt-1 text-xs leading-5 text-slate-500">
                                                            {
                                                                notification.message
                                                            }
                                                        </p>
                                                    )}

                                                    <button
                                                        type="button"
                                                        onClick={() =>
                                                            markAsRead(
                                                                notification.id
                                                            )
                                                        }
                                                        className="mt-2 text-xs font-medium text-violet-600 hover:text-violet-700"
                                                    >
                                                        Mark as
                                                        read
                                                    </button>
                                                </div>
                                            </div>
                                        </div>
                                    )
                                )
                            )}
                        </div>
                    </div>
                </>
            )}
        </div>
    );
}
