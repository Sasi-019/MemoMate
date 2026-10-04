
import { useEffect, useState } from "react";

import Sidebar from "./components/Sidebar";
import Calendar from "./components/Calendar";
import Reminders from "./components/Reminders";
import Lists from "./components/Lists";
import Assistant from "./components/Assistant";
import NotificationCenter from "./components/NotificationCenter";
import Login from "./pages/Login";

import {
    apiFetch,
    clearToken,
    getStoredUser,
    getToken,
    setStoredUser,
} from "./services/api";

function Dashboard({ setActivePage, user }) {
    const cards = [
        {
            title: "Calendar",
            description: "See your schedule and events.",
            icon: "📅",
            page: "calendar",
            className: "bg-indigo-50 text-indigo-700",
        },
        {
            title: "Reminders",
            description: "Never forget an important task.",
            icon: "⏰",
            page: "reminders",
            className: "bg-amber-50 text-amber-700",
        },
        {
            title: "Smart Lists",
            description: "Organize shopping and everyday lists.",
            icon: "📝",
            page: "lists",
            className: "bg-emerald-50 text-emerald-700",
        },
        {
            title: "AI Assistant",
            description: "Tell MemoMate what you need naturally.",
            icon: "✨",
            page: "assistant",
            className: "bg-violet-50 text-violet-700",
        },
    ];

    return (
        <div className="space-y-5">

            {/* Welcome section */}
            <div className="rounded-3xl bg-gradient-to-r from-indigo-600 via-violet-600 to-purple-600 p-5 text-white shadow-xl shadow-indigo-100 sm:p-6 lg:p-7">

                <p className="text-sm font-medium text-indigo-100">
                    Your everyday memory assistant
                </p>

                <h2 className="mt-1.5 text-2xl font-bold sm:text-3xl">
                    Welcome, {user?.name || "there"} 👋
                </h2>

                <p className="mt-2 max-w-2xl text-sm leading-5 text-indigo-100 sm:text-base">
                    Tell MemoMate what you need to remember, schedule, or organize.
                    It turns your request into a real action.
                </p>

                <button
                    type="button"
                    onClick={() => setActivePage("assistant")}
                    className="mt-4 rounded-xl bg-white px-5 py-2.5 font-semibold text-indigo-700 shadow-lg transition hover:bg-indigo-50"
                >
                    Ask MemoMate →
                </button>
            </div>

            {/* Quick access */}
            <div>

                <div className="mb-3">
                    <h2 className="text-xl font-bold text-slate-900">
                        Quick access
                    </h2>

                    <p className="mt-1 text-sm text-slate-500">
                        Jump straight to the things you use most.
                    </p>
                </div>

                <div className="grid gap-4 sm:grid-cols-2 xl:grid-cols-4">

                    {cards.map((card) => (
                        <button
                            key={card.title}
                            type="button"
                            onClick={() => setActivePage(card.page)}
                            className="rounded-2xl border border-slate-200 bg-white p-4 text-left shadow-sm transition hover:-translate-y-0.5 hover:shadow-md"
                        >
                            <div
                                className={`flex h-11 w-11 items-center justify-center rounded-xl text-2xl ${card.className}`}
                            >
                                {card.icon}
                            </div>

                            <h3 className="mt-3 font-bold text-slate-900">
                                {card.title}
                            </h3>

                            <p className="mt-1 text-sm leading-5 text-slate-500">
                                {card.description}
                            </p>
                        </button>
                    ))}

                </div>
            </div>
        </div>
    );
}

function App() {
    const [activePage, setActivePage] = useState("dashboard");
    const [mobileOpen, setMobileOpen] = useState(false);
    const [user, setUser] = useState(() => getStoredUser());
    const [authChecking, setAuthChecking] = useState(true);
    const [loginKey, setLoginKey] = useState(0);

    useEffect(() => {
        let mounted = true;

        async function validateSession() {
            const token = getToken();

            if (!token) {
                if (mounted) {
                    setUser(null);
                    setAuthChecking(false);
                }
                return;
            }

            try {
                const response = await apiFetch("/auth/me");

                if (response.status === 401) {
                    // Session really is invalid or expired.
                    // (apiFetch already cleared the token.)
                    clearToken();

                    if (mounted) {
                        setUser(null);
                    }

                    return;
                }

                if (!response.ok) {
                    // Server trouble (e.g. 5xx while Render is waking up):
                    // keep the saved session instead of logging out.
                    console.warn(
                        "Session check failed with status",
                        response.status
                    );

                    return;
                }

                const currentUser = await response.json();

                if (mounted) {
                    setStoredUser(currentUser);
                    setUser(currentUser);
                }
            } catch (error) {
                // Network error / cold start: do NOT log the user out.
                console.error(
                    "Session validation failed:",
                    error
                );
            } finally {
                if (mounted) {
                    setAuthChecking(false);
                }
            }
        }

        validateSession();

        return () => {
            mounted = false;
        };
    }, [loginKey]);

    useEffect(() => {
        function handleUnauthorized() {
            clearToken();
            setUser(null);
            setActivePage("dashboard");
            setMobileOpen(false);
        }

        window.addEventListener(
            "memomate:unauthorized",
            handleUnauthorized
        );

        return () => {
            window.removeEventListener(
                "memomate:unauthorized",
                handleUnauthorized
            );
        };
    }, []);

    const handleAuthenticated = (authenticatedUser) => {
        setStoredUser(authenticatedUser);
        setUser(authenticatedUser);
        setActivePage("dashboard");
        setMobileOpen(false);
        setAuthChecking(false);
    };

    const handleLogout = async () => {
        try {
            if (getToken()) {
                await apiFetch("/auth/logout", {
                    method: "POST",
                });
            }
        } catch (error) {
            console.error(
                "Logout request failed:",
                error
            );
        } finally {
            clearToken();
            setUser(null);
            setActivePage("dashboard");
            setMobileOpen(false);
            setLoginKey((value) => value + 1);
        }
    };

    const getPageTitle = () => {
        const titles = {
            dashboard: "Dashboard",
            calendar: "Calendar",
            reminders: "Reminders",
            lists: "Smart Lists",
            assistant: "AI Assistant",
            memory: "Memory",
            settings: "Settings",
        };

        return titles[activePage] || "MemoMate";
    };

    const handleNavigation = (page) => {
        setActivePage(page);
        setMobileOpen(false);
    };

    const renderPage = () => {
        switch (activePage) {
            case "dashboard":
                return (
                    <Dashboard
                        setActivePage={handleNavigation}
                        user={user}
                    />
                );

            case "calendar":
                return <Calendar />;

            case "reminders":
                return <Reminders />;

            case "lists":
                return <Lists />;

            case "assistant":
                return <Assistant />;

            case "memory":
                return (
                    <div className="rounded-3xl border border-slate-200 bg-white p-6 text-center shadow-sm sm:p-8">

                        <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-2xl bg-violet-50 text-3xl">
                            🧠
                        </div>

                        <h2 className="mt-5 text-2xl font-bold text-slate-900">
                            Personal Memory
                        </h2>

                        <p className="mx-auto mt-2 max-w-lg text-slate-500">
                            Ask MemoMate to remember something important.
                            Memory management is connected through the AI assistant.
                        </p>

                        <button
                            type="button"
                            onClick={() =>
                                handleNavigation("assistant")
                            }
                            className="mt-5 rounded-xl bg-indigo-600 px-5 py-3 font-semibold text-white shadow-lg shadow-indigo-200 transition hover:bg-indigo-700"
                        >
                            Ask MemoMate →
                        </button>

                    </div>
                );

            case "settings":
                return (
                    <div className="space-y-4 rounded-3xl border border-slate-200 bg-white p-6 shadow-sm sm:p-7">

                        <div>
                            <h2 className="text-2xl font-bold text-slate-900">
                                Settings
                            </h2>

                            <p className="mt-2 text-slate-500">
                                Your MemoMate account and application settings.
                            </p>
                        </div>

                        <div className="rounded-2xl bg-slate-50 p-5">

                            <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">
                                Signed in as
                            </p>

                            <p className="mt-1 text-lg font-bold text-slate-900">
                                {user?.name}
                            </p>

                            <p className="mt-1 text-sm text-slate-500">
                                MemoMate ID: {user?.name_id}
                            </p>

                        </div>

                        <div className="grid gap-3 sm:grid-cols-2">

                            <div className="rounded-2xl bg-slate-50 p-5">
                                <p className="text-sm font-semibold text-slate-700">
                                    AI provider
                                </p>

                                <p className="mt-1 text-sm text-slate-500">
                                    Qwen3 through the secure MemoMate backend
                                </p>
                            </div>

                            <div className="rounded-2xl bg-slate-50 p-5">
                                <p className="text-sm font-semibold text-slate-700">
                                    Voice
                                </p>

                                <p className="mt-1 text-sm text-slate-500">
                                    Groq Whisper speech-to-text
                                </p>
                            </div>

                        </div>

                        <div className="border-t border-slate-100 pt-5">

                            <button
                                type="button"
                                onClick={handleLogout}
                                className="rounded-xl border border-red-200 bg-red-50 px-5 py-3 font-semibold text-red-600 transition hover:bg-red-100"
                            >
                                Log out
                            </button>

                        </div>

                    </div>
                );

            default:
                return (
                    <Dashboard
                        setActivePage={handleNavigation}
                        user={user}
                    />
                );
        }
    };

    if (authChecking) {
        return (
            <div className="flex min-h-screen items-center justify-center bg-slate-50 px-4">

                <div className="rounded-3xl border border-slate-200 bg-white p-8 text-center shadow-xl">

                    <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-violet-50 text-2xl">
                        🧠
                    </div>

                    <h1 className="mt-4 text-xl font-bold text-slate-900">
                        MemoMate
                    </h1>

                    <p className="mt-2 text-sm text-slate-500">
                        Checking your secure session...
                    </p>

                </div>

            </div>
        );
    }

    if (!user || !getToken()) {
        return (
            <Login
                key={loginKey}
                onAuthenticated={handleAuthenticated}
            />
        );
    }

    return (
        /*
         * IMPORTANT:
         * Use the full laptop viewport.
         * The outer page itself does not scroll.
         */
        <div className="h-screen overflow-hidden bg-slate-50">

            <div className="flex h-full">

                {/* Sidebar */}
                <Sidebar
                    activePage={activePage}
                    setActivePage={handleNavigation}
                    mobileOpen={mobileOpen}
                    setMobileOpen={setMobileOpen}
                />

                {/* Main application area */}
                <div className="flex min-w-0 flex-1 flex-col lg:pl-[280px]">

                    {/* Header */}
                    <header className="sticky top-0 z-30 shrink-0 border-b border-slate-200 bg-white/90 backdrop-blur">

                        <div className="flex h-[64px] items-center justify-between px-4 sm:px-6 lg:px-7">

                            <div className="flex items-center gap-3">

                                <button
                                    type="button"
                                    onClick={() =>
                                        setMobileOpen(true)
                                    }
                                    className="flex h-10 w-10 items-center justify-center rounded-xl border border-slate-200 bg-white text-lg text-slate-700 lg:hidden"
                                    aria-label="Open menu"
                                >
                                    ☰
                                </button>

                                <div className="lg:hidden">
                                    <p className="font-bold text-slate-900">
                                        MemoMate
                                    </p>

                                    <p className="text-xs text-slate-400">
                                        Memory assistant
                                    </p>
                                </div>

                                <div className="hidden lg:block">
                                    <h1 className="text-lg font-bold text-slate-900">
                                        {getPageTitle()}
                                    </h1>

                                    <p className="text-xs text-slate-400">
                                        Your everyday memory assistant
                                    </p>
                                </div>

                            </div>

                            <div className="flex items-center gap-3">

                                <div className="hidden text-right sm:block">
                                    <p className="text-sm font-semibold text-slate-800">
                                        {user.name}
                                    </p>

                                    <p className="text-[11px] text-slate-400">
                                        {user.name_id}
                                    </p>
                                </div>

                                <NotificationCenter />

                            </div>

                        </div>

                    </header>

                    {/* Scrollable content only */}
                    <main className="min-h-0 flex-1 overflow-y-auto">

                        <div className="mx-auto w-full max-w-7xl px-4 py-4 sm:px-5 lg:px-6 lg:py-5">

                            {renderPage()}

                        </div>

                    </main>

                </div>

            </div>

        </div>
    );
}

export default App;


