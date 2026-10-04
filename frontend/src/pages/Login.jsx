
import { useState } from "react";
import {
    API_URL,
    setToken,
    setStoredUser,
} from "../services/api";

export default function Login({ onAuthenticated }) {
    const [mode, setMode] = useState("login");
    const [name, setName] = useState("");
    const [nameId, setNameId] = useState("");
    const [pendingUser, setPendingUser] = useState(null);
    const [loading, setLoading] = useState(false);
    const [error, setError] = useState("");

    const reset = (nextMode) => {
        setMode(nextMode);
        setError("");
        setPendingUser(null);
    };

    async function startAuth(event) {
        event.preventDefault();
        setError("");

        if (mode === "register" && !name.trim()) {
            setError("Enter your name.");
            return;
        }

        if (!nameId.trim()) {
            setError("Enter your MemoMate ID.");
            return;
        }

        setLoading(true);

        try {
            const endpoint =
                mode === "register"
                    ? "/auth/register"
                    : "/auth/login";

            const body =
                mode === "register"
                    ? {
                          name: name.trim(),
                          name_id: nameId.trim(),
                      }
                    : {
                          name_id: nameId.trim(),
                      };

            const response = await fetch(
                `${API_URL}${endpoint}`,
                {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                    },
                    body: JSON.stringify(body),
                }
            );

            const data = await response.json();

            if (!response.ok) {
                throw new Error(
                    data.detail || "Unable to continue."
                );
            }

            setPendingUser(data.user);
        } catch (err) {
            setError(
                err.message || "Unable to continue."
            );
        } finally {
            setLoading(false);
        }
    }

    async function authorize() {
        if (!pendingUser?.id) {
            setError("User information is missing.");
            return;
        }

        setError("");
        setLoading(true);

        try {
            const response = await fetch(
                `${API_URL}/auth/authorize`,
                {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                    },
                    body: JSON.stringify({
                        user_id: pendingUser.id,
                    }),
                }
            );

            const data = await response.json();

            if (!response.ok) {
                throw new Error(
                    data.detail || "Authorization failed."
                );
            }

            /*
             * IMPORTANT:
             * App.jsx and api.js use "memomate_token".
             * Do NOT use "memomate_session" here.
             */
            setToken(data.access_token);
            setStoredUser(data.user);

            /*
             * Tell App.jsx that authentication succeeded.
             * App.jsx will then open the dashboard.
             */
            onAuthenticated(data.user);
        } catch (err) {
            setError(
                err.message || "Authorization failed."
            );
        } finally {
            setLoading(false);
        }
    }

    if (pendingUser) {
        return (
            <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-indigo-950 flex items-center justify-center p-5">
                <div className="w-full max-w-md rounded-3xl border border-white/10 bg-white/10 p-8 text-white shadow-2xl backdrop-blur-xl">

                    <div className="mb-8 text-center">
                        <div className="text-4xl">🔐</div>

                        <h1 className="mt-4 text-3xl font-black">
                            Authorize MemoMate
                        </h1>

                        <p className="mt-2 text-slate-300">
                            One final step before we open your private workspace.
                        </p>
                    </div>

                    <div className="rounded-2xl border border-white/10 bg-white/5 p-5">
                        <p className="text-sm text-slate-300">
                            Signed in as
                        </p>

                        <p className="mt-1 text-xl font-bold">
                            {pendingUser.name}
                        </p>

                        <p className="mt-1 text-sm text-indigo-300">
                            @{pendingUser.name_id}
                        </p>
                    </div>

                    <div className="mt-5 space-y-3 text-sm text-slate-200">
                        {[
                            "Calendar & reminders",
                            "Smart lists & personal memory",
                            "Uploaded files & timetable",
                            "Private data for this account",
                        ].map((item) => (
                            <div
                                key={item}
                                className="flex gap-3"
                            >
                                <span className="text-emerald-400">
                                    ✓
                                </span>

                                <span>{item}</span>
                            </div>
                        ))}
                    </div>

                    {error && (
                        <div className="mt-5 rounded-xl border border-red-400/20 bg-red-500/10 p-3 text-sm text-red-200">
                            {error}
                        </div>
                    )}

                    <button
                        onClick={authorize}
                        disabled={loading}
                        className="mt-7 w-full rounded-2xl bg-indigo-500 py-3.5 font-bold transition hover:bg-indigo-400 disabled:opacity-60"
                    >
                        {loading
                            ? "Creating secure session…"
                            : "Authorize MemoMate →"}
                    </button>

                    <button
                        onClick={() => reset("login")}
                        className="mt-3 w-full rounded-2xl py-3 text-sm font-semibold text-slate-400 hover:text-white"
                    >
                        Cancel
                    </button>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-gradient-to-br from-slate-950 via-slate-900 to-indigo-950 flex items-center justify-center p-5">

            <div className="w-full max-w-md rounded-3xl border border-white/10 bg-white/10 p-8 shadow-2xl backdrop-blur-xl">

                <div className="mb-8">
                    <div className="text-3xl font-black text-white">
                        ✨ MemoMate
                    </div>

                    <p className="mt-2 text-slate-300">
                        Your everyday AI memory assistant
                    </p>
                </div>

                <div className="mb-6 grid grid-cols-2 rounded-2xl bg-black/20 p-1">

                    <button
                        onClick={() => reset("login")}
                        className={`rounded-xl py-2.5 text-sm font-bold ${
                            mode === "login"
                                ? "bg-white text-slate-900"
                                : "text-slate-400"
                        }`}
                    >
                        Login
                    </button>

                    <button
                        onClick={() => reset("register")}
                        className={`rounded-xl py-2.5 text-sm font-bold ${
                            mode === "register"
                                ? "bg-white text-slate-900"
                                : "text-slate-400"
                        }`}
                    >
                        Create account
                    </button>

                </div>

                <form
                    onSubmit={startAuth}
                    className="space-y-5"
                >

                    {mode === "register" && (
                        <div>
                            <label className="text-sm text-slate-200">
                                Your name
                            </label>

                            <input
                                value={name}
                                onChange={(e) =>
                                    setName(e.target.value)
                                }
                                placeholder="Sasi"
                                className="mt-2 w-full rounded-2xl border border-white/10 bg-white/10 px-4 py-3 text-white outline-none placeholder:text-slate-500 focus:border-indigo-400"
                            />
                        </div>
                    )}

                    <div>
                        <label className="text-sm text-slate-200">
                            MemoMate ID
                        </label>

                        <input
                            value={nameId}
                            onChange={(e) =>
                                setNameId(
                                    e.target.value
                                        .toLowerCase()
                                        .replace(/\s/g, "")
                                )
                            }
                            placeholder="sasi_24"
                            className="mt-2 w-full rounded-2xl border border-white/10 bg-white/10 px-4 py-3 text-white outline-none placeholder:text-slate-500 focus:border-indigo-400"
                        />

                        <p className="mt-2 text-xs text-slate-400">
                            Letters, numbers, dot, dash and underscore.
                        </p>
                    </div>

                    {error && (
                        <div className="rounded-xl border border-red-400/20 bg-red-500/10 p-3 text-sm text-red-200">
                            {error}
                        </div>
                    )}

                    <button
                        disabled={loading}
                        className="w-full rounded-2xl bg-indigo-500 py-3.5 font-bold text-white transition hover:bg-indigo-400 disabled:opacity-60"
                    >
                        {loading
                            ? "Checking account…"
                            : "Continue →"}
                    </button>

                </form>

                <div className="mt-6 rounded-2xl border border-white/10 bg-white/5 p-4 text-xs leading-5 text-slate-400">
                    <strong className="text-slate-200">
                        Privacy:
                    </strong>{" "}
                    after authorization, MemoMate creates a separate
                    session for this account. Your calendar, reminders,
                    lists, memory and files are scoped to your user.
                </div>

            </div>
        </div>
    );
}

