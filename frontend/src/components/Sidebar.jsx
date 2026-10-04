import { useState } from "react";

const navigation = [
    {
        id: "dashboard",
        label: "Dashboard",
        icon: "⌂",
    },
    {
        id: "calendar",
        label: "Calendar",
        icon: "▣",
    },
    {
        id: "reminders",
        label: "Reminders",
        icon: "◷",
    },
    {
        id: "lists",
        label: "Lists",
        icon: "☷",
    },
    {
        id: "memory",
        label: "Memory",
        icon: "✦",
    },
    {
        id: "assistant",
        label: "AI Assistant",
        icon: "✧",
    },
];

function Sidebar({
    activePage,
    setActivePage,
    mobileOpen,
    setMobileOpen,
}) {
    const handleNavigation = (page) => {
        setActivePage(page);
        setMobileOpen(false);
    };

    return (
        <>
            {/* Mobile backdrop */}
            {mobileOpen && (
                <div
                    className="fixed inset-0 z-40 bg-slate-950/40 backdrop-blur-sm lg:hidden"
                    onClick={() => setMobileOpen(false)}
                />
            )}

            {/* Sidebar */}
            <aside
                className={`
                    fixed inset-y-0 left-0 z-50
                    flex w-[280px] flex-col
                    border-r border-slate-200
                    bg-white
                    shadow-xl shadow-slate-200/40
                    transition-transform duration-300 ease-in-out
                    lg:static lg:z-auto lg:translate-x-0
                    lg:shadow-none
                    ${
                        mobileOpen
                            ? "translate-x-0"
                            : "-translate-x-full"
                    }
                `}
            >
                {/* Brand */}
                <div className="flex h-[88px] items-center justify-between border-b border-slate-100 px-6">
                    <button
                        onClick={() => handleNavigation("dashboard")}
                        className="flex items-center gap-3"
                    >
                        <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-slate-950 text-xl text-white shadow-lg shadow-slate-300">
                            🧠
                        </div>

                        <div className="text-left">
                            <h1 className="text-lg font-bold tracking-tight text-slate-950">
                                MemoMate
                            </h1>

                            <p className="text-xs text-slate-400">
                                Remember. Organize. Do.
                            </p>
                        </div>
                    </button>

                    {/* Mobile close */}
                    <button
                        onClick={() => setMobileOpen(false)}
                        className="flex h-9 w-9 items-center justify-center rounded-xl text-xl text-slate-500 transition hover:bg-slate-100 hover:text-slate-900 lg:hidden"
                        aria-label="Close menu"
                    >
                        ×
                    </button>
                </div>

                {/* Navigation */}
                <div className="flex-1 overflow-y-auto px-4 py-6">
                    <p className="mb-3 px-3 text-[11px] font-bold uppercase tracking-[0.16em] text-slate-400">
                        Workspace
                    </p>

                    <nav className="space-y-1.5">
                        {navigation.map((item) => {
                            const active = activePage === item.id;

                            return (
                                <button
                                    key={item.id}
                                    onClick={() =>
                                        handleNavigation(item.id)
                                    }
                                    className={`
                                        group flex w-full items-center gap-3
                                        rounded-2xl px-3.5 py-3
                                        text-left
                                        transition-all duration-200
                                        ${
                                            active
                                                ? "bg-slate-950 text-white shadow-md shadow-slate-300/50"
                                                : "text-slate-600 hover:bg-slate-100 hover:text-slate-950"
                                        }
                                    `}
                                >
                                    <span
                                        className={`
                                            flex h-9 w-9 shrink-0
                                            items-center justify-center
                                            rounded-xl
                                            text-lg
                                            ${
                                                active
                                                    ? "bg-white/10 text-white"
                                                    : "bg-slate-100 text-slate-500 group-hover:bg-white group-hover:text-slate-900"
                                            }
                                        `}
                                    >
                                        {item.icon}
                                    </span>

                                    <span className="flex-1 text-sm font-semibold">
                                        {item.label}
                                    </span>

                                    {active && (
                                        <span className="h-1.5 w-1.5 rounded-full bg-white" />
                                    )}
                                </button>
                            );
                        })}
                    </nav>

                    {/* Assistant callout */}
                    <div className="mt-8 rounded-2xl border border-slate-200 bg-slate-50 p-4">
                        <div className="mb-3 flex h-9 w-9 items-center justify-center rounded-xl bg-white text-lg shadow-sm">
                            ✨
                        </div>

                        <p className="text-sm font-semibold text-slate-900">
                            Meet your memory assistant
                        </p>

                        <p className="mt-1 text-xs leading-5 text-slate-500">
                            Soon you can tell MemoMate what you need in
                            natural language.
                        </p>

                        <button
                            onClick={() =>
                                handleNavigation("assistant")
                            }
                            className="mt-3 text-xs font-bold text-slate-900 hover:underline"
                        >
                            Open Assistant →
                        </button>
                    </div>
                </div>

                {/* Bottom section */}
                <div className="border-t border-slate-100 p-4">
                    <button
                        onClick={() => handleNavigation("settings")}
                        className={`
                            flex w-full items-center gap-3 rounded-2xl
                            px-3.5 py-3 text-left
                            transition
                            ${
                                activePage === "settings"
                                    ? "bg-slate-950 text-white"
                                    : "text-slate-600 hover:bg-slate-100 hover:text-slate-950"
                            }
                        `}
                    >
                        <span className="flex h-9 w-9 items-center justify-center rounded-xl bg-slate-100 text-lg">
                            ⚙
                        </span>

                        <span className="text-sm font-semibold">
                            Settings
                        </span>
                    </button>

                    <p className="mt-4 px-3 text-[10px] text-slate-400">
                        MemoMate · Your everyday memory assistant
                    </p>
                </div>
            </aside>
        </>
    );
}

export default Sidebar;