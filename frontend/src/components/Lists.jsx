import { useEffect, useState } from "react";

const API_URL =
    import.meta.env.VITE_API_URL ||
    "https://memomate-af77.onrender.com";

const getToken = () =>
    localStorage.getItem("access_token") ||
    localStorage.getItem("token") ||
    localStorage.getItem("auth_token") ||
    "";

const getErrorMessage = (data, fallback) => {
    if (!data) return fallback;

    if (typeof data === "string") {
        return data;
    }

    if (typeof data.detail === "string") {
        return data.detail;
    }

    if (Array.isArray(data.detail)) {
        return data.detail
            .map((item) =>
                typeof item === "string"
                    ? item
                    : item?.msg ||
                      JSON.stringify(item)
            )
            .join(", ");
    }

    if (
        data.detail &&
        typeof data.detail === "object"
    ) {
        if (data.detail.message) {
            return data.detail.message;
        }

        if (data.detail.msg) {
            return data.detail.msg;
        }

        return JSON.stringify(data.detail);
    }

    if (data.message) {
        return data.message;
    }

    return fallback;
};

const apiRequest = async (
    url,
    options = {}
) => {
    const token = getToken();

    const response = await fetch(url, {
        ...options,

        headers: {
            ...(token
                ? {
                      Authorization: `Bearer ${token}`,
                  }
                : {}),

            ...(options.headers || {}),
        },
    });

    let data = null;

    try {
        data = await response.json();
    } catch {
        data = null;
    }

    if (!response.ok) {
        throw new Error(
            getErrorMessage(
                data,
                `Request failed with status ${response.status}.`
            )
        );
    }

    return data;
};

function Lists() {
    const [lists, setLists] = useState([]);
    const [loading, setLoading] = useState(true);
    const [error, setError] = useState("");

    const [showCreate, setShowCreate] =
        useState(false);

    const [newListName, setNewListName] =
        useState("");

    const [newItem, setNewItem] = useState({});
    const [addingItem, setAddingItem] =
        useState(null);

    const loadLists = async () => {
        try {
            setLoading(true);
            setError("");

            const data = await apiRequest(
                `${API_URL}/lists`
            );

            setLists(
                Array.isArray(data)
                    ? data
                    : Array.isArray(data?.lists)
                      ? data.lists
                      : []
            );
        } catch (err) {
            console.error(
                "Lists error:",
                err
            );

            setError(
                err.message ||
                    "Could not connect to MemoMate lists."
            );
        } finally {
            setLoading(false);
        }
    };

    useEffect(() => {
        loadLists();
    }, []);

    const createList = async () => {
        const name = newListName.trim();

        if (!name) {
            return;
        }

        try {
            setError("");

            await apiRequest(
                `${API_URL}/lists`,
                {
                    method: "POST",

                    headers: {
                        "Content-Type":
                            "application/json",
                    },

                    body: JSON.stringify({
                        name,
                    }),
                }
            );

            setNewListName("");
            setShowCreate(false);

            await loadLists();
        } catch (err) {
            console.error(
                "Create list error:",
                err
            );

            setError(
                err.message ||
                    "Could not create list."
            );
        }
    };

    const addItem = async (listId) => {
        const text = (
            newItem[listId] || ""
        ).trim();

        if (!text) {
            return;
        }

        try {
            setError("");
            setAddingItem(listId);

            await apiRequest(
                `${API_URL}/lists/${listId}/items?text=${encodeURIComponent(
                    text
                )}`,
                {
                    method: "POST",
                }
            );

            setNewItem((previous) => ({
                ...previous,
                [listId]: "",
            }));

            await loadLists();
        } catch (err) {
            console.error(
                "Add item error:",
                err
            );

            setError(
                err.message ||
                    "Could not add item."
            );
        } finally {
            setAddingItem(null);
        }
    };

    const completeItem = async (itemId) => {
        try {
            setError("");

            await apiRequest(
                `${API_URL}/lists/items/${itemId}/complete`,
                {
                    method: "PUT",
                }
            );

            await loadLists();
        } catch (err) {
            console.error(
                "Complete item error:",
                err
            );

            setError(
                err.message ||
                    "Could not complete item."
            );
        }
    };

    const deleteItem = async (itemId) => {
        try {
            setError("");

            await apiRequest(
                `${API_URL}/lists/items/${itemId}`,
                {
                    method: "DELETE",
                }
            );

            await loadLists();
        } catch (err) {
            console.error(
                "Delete item error:",
                err
            );

            setError(
                err.message ||
                    "Could not delete item."
            );
        }
    };

    const totalItems = lists.reduce(
        (total, list) =>
            total +
            (list.items?.length || 0),
        0
    );

    const completedItems = lists.reduce(
        (total, list) =>
            total +
            (list.items || []).filter(
                (item) => item.completed
            ).length,
        0
    );

    if (loading) {
        return (
            <div className="space-y-6">
                <div>
                    <div className="h-8 w-48 animate-pulse rounded-lg bg-slate-200" />

                    <div className="mt-3 h-4 w-80 animate-pulse rounded bg-slate-200" />
                </div>

                <div className="grid gap-5 md:grid-cols-2">
                    {[1, 2].map((item) => (
                        <div
                            key={item}
                            className="h-64 animate-pulse rounded-3xl bg-white shadow-sm"
                        />
                    ))}
                </div>
            </div>
        );
    }

    return (
        <div className="space-y-6">
            <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">
                <div>
                    <p className="text-sm font-semibold text-emerald-600">
                        Stay organized
                    </p>

                    <h1 className="mt-1 text-3xl font-bold tracking-tight text-slate-900">
                        Smart Lists
                    </h1>

                    <p className="mt-2 max-w-2xl text-slate-500">
                        Organize shopping, tasks,
                        packing and anything else
                        you want MemoMate to remember.
                    </p>
                </div>

                <button
                    type="button"
                    onClick={() =>
                        setShowCreate(true)
                    }
                    className="inline-flex items-center justify-center gap-2 rounded-xl bg-slate-900 px-5 py-3 text-sm font-semibold text-white shadow-lg transition hover:bg-slate-800"
                >
                    <span className="text-lg">
                        +
                    </span>
                    New list
                </button>
            </div>

            {error && (
                <div className="flex items-start justify-between gap-4 rounded-2xl border border-red-200 bg-red-50 px-4 py-3 text-sm text-red-700">
                    <span>
                        ⚠️ {error}
                    </span>

                    <button
                        type="button"
                        onClick={() =>
                            setError("")
                        }
                        className="font-bold"
                    >
                        ×
                    </button>
                </div>
            )}

            <div className="grid gap-4 sm:grid-cols-3">
                <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
                    <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">
                        Lists
                    </p>

                    <p className="mt-2 text-3xl font-bold text-slate-900">
                        {lists.length}
                    </p>
                </div>

                <div className="rounded-2xl border border-slate-200 bg-white p-5 shadow-sm">
                    <p className="text-xs font-semibold uppercase tracking-wide text-slate-400">
                        Items
                    </p>

                    <p className="mt-2 text-3xl font-bold text-slate-900">
                        {totalItems}
                    </p>
                </div>

                <div className="rounded-2xl border border-emerald-100 bg-emerald-50 p-5 shadow-sm">
                    <p className="text-xs font-semibold uppercase tracking-wide text-emerald-600">
                        Completed
                    </p>

                    <p className="mt-2 text-3xl font-bold text-emerald-700">
                        {completedItems}
                    </p>
                </div>
            </div>

            {lists.length === 0 && (
                <div className="rounded-3xl border border-dashed border-slate-300 bg-white px-6 py-16 text-center shadow-sm">
                    <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-2xl bg-emerald-50 text-3xl">
                        📝
                    </div>

                    <h2 className="mt-5 text-xl font-bold text-slate-900">
                        No lists yet
                    </h2>

                    <p className="mx-auto mt-2 max-w-md text-sm leading-6 text-slate-500">
                        Create your first list or
                        simply tell MemoMate:
                        “Add milk and bread to my
                        shopping list.”
                    </p>

                    <div className="mt-6 flex flex-col justify-center gap-3 sm:flex-row">
                        <button
                            type="button"
                            onClick={() =>
                                setShowCreate(true)
                            }
                            className="rounded-xl bg-slate-900 px-5 py-3 text-sm font-semibold text-white hover:bg-slate-800"
                        >
                            Create a list
                        </button>
                    </div>
                </div>
            )}

            {lists.length > 0 && (
                <div className="grid gap-5 lg:grid-cols-2">
                    {lists.map((list) => {
                        const items =
                            list.items || [];

                        const completed =
                            items.filter(
                                (item) =>
                                    item.completed
                            ).length;

                        return (
                            <div
                                key={list.id}
                                className="overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-sm transition hover:shadow-md"
                            >
                                <div className="border-b border-slate-100 p-5">
                                    <div className="flex items-start justify-between gap-4">
                                        <div className="flex items-center gap-3">
                                            <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-emerald-50 text-xl">
                                                📝
                                            </div>

                                            <div>
                                                <h2 className="font-bold text-slate-900">
                                                    {list.name}
                                                </h2>

                                                <p className="mt-0.5 text-xs text-slate-400">
                                                    {completed}{" "}
                                                    of{" "}
                                                    {
                                                        items.length
                                                    }{" "}
                                                    completed
                                                </p>
                                            </div>
                                        </div>

                                        <span className="rounded-full bg-slate-100 px-3 py-1 text-xs font-semibold text-slate-500">
                                            {
                                                items.length
                                            }{" "}
                                            {items.length ===
                                            1
                                                ? "item"
                                                : "items"}
                                        </span>
                                    </div>
                                </div>

                                <div className="p-4">
                                    {items.length ===
                                    0 ? (
                                        <div className="rounded-2xl bg-slate-50 px-4 py-6 text-center">
                                            <p className="text-sm text-slate-400">
                                                No items yet.
                                            </p>
                                        </div>
                                    ) : (
                                        <div className="space-y-2">
                                            {items.map(
                                                (
                                                    item
                                                ) => (
                                                    <div
                                                        key={
                                                            item.id
                                                        }
                                                        className={`group flex items-center gap-3 rounded-xl px-3 py-3 transition ${
                                                            item.completed
                                                                ? "bg-emerald-50"
                                                                : "bg-slate-50 hover:bg-slate-100"
                                                        }`}
                                                    >
                                                        <button
                                                            type="button"
                                                            onClick={() =>
                                                                !item.completed &&
                                                                completeItem(
                                                                    item.id
                                                                )
                                                            }
                                                            className={`flex h-6 w-6 shrink-0 items-center justify-center rounded-full border-2 text-xs font-bold transition ${
                                                                item.completed
                                                                    ? "border-emerald-500 bg-emerald-500 text-white"
                                                                    : "border-slate-300 bg-white text-transparent hover:border-emerald-400"
                                                            }`}
                                                            aria-label={
                                                                item.completed
                                                                    ? "Completed"
                                                                    : "Mark complete"
                                                            }
                                                        >
                                                            ✓
                                                        </button>

                                                        <span
                                                            className={`min-w-0 flex-1 text-sm ${
                                                                item.completed
                                                                    ? "text-slate-400 line-through"
                                                                    : "text-slate-700"
                                                            }`}
                                                        >
                                                            {
                                                                item.text
                                                            }
                                                        </span>

                                                        <button
                                                            type="button"
                                                            onClick={() =>
                                                                deleteItem(
                                                                    item.id
                                                                )
                                                            }
                                                            className="rounded-lg px-2 py-1 text-slate-300 opacity-0 transition hover:bg-red-50 hover:text-red-500 group-hover:opacity-100"
                                                            aria-label="Delete item"
                                                        >
                                                            ×
                                                        </button>
                                                    </div>
                                                )
                                            )}
                                        </div>
                                    )}

                                    <div className="mt-4 flex gap-2">
                                        <input
                                            value={
                                                newItem[
                                                    list.id
                                                ] || ""
                                            }
                                            onChange={(
                                                event
                                            ) =>
                                                setNewItem(
                                                    (
                                                        previous
                                                    ) => ({
                                                        ...previous,
                                                        [list.id]:
                                                            event
                                                                .target
                                                                .value,
                                                    })
                                                )
                                            }
                                            onKeyDown={(
                                                event
                                            ) => {
                                                if (
                                                    event.key ===
                                                    "Enter"
                                                ) {
                                                    addItem(
                                                        list.id
                                                    );
                                                }
                                            }}
                                            placeholder="Add an item..."
                                            className="min-w-0 flex-1 rounded-xl border border-slate-200 bg-white px-3 py-2.5 text-sm outline-none transition focus:border-emerald-400 focus:ring-2 focus:ring-emerald-100"
                                        />

                                        <button
                                            type="button"
                                            onClick={() =>
                                                addItem(
                                                    list.id
                                                )
                                            }
                                            disabled={
                                                addingItem ===
                                                list.id
                                            }
                                            className="rounded-xl bg-emerald-600 px-4 py-2 text-sm font-semibold text-white transition hover:bg-emerald-700 disabled:opacity-50"
                                        >
                                            {addingItem ===
                                            list.id
                                                ? "..."
                                                : "Add"}
                                        </button>
                                    </div>
                                </div>
                            </div>
                        );
                    })}
                </div>
            )}

            {showCreate && (
                <div
                    className="fixed inset-0 z-50 flex items-center justify-center bg-slate-900/50 p-4 backdrop-blur-sm"
                    onMouseDown={(event) => {
                        if (
                            event.target ===
                            event.currentTarget
                        ) {
                            setShowCreate(false);
                        }
                    }}
                >
                    <div className="w-full max-w-md rounded-3xl bg-white p-6 shadow-2xl">
                        <div className="flex items-start justify-between">
                            <div>
                                <div className="flex h-11 w-11 items-center justify-center rounded-xl bg-emerald-50 text-xl">
                                    📝
                                </div>

                                <h2 className="mt-4 text-xl font-bold text-slate-900">
                                    Create a new list
                                </h2>

                                <p className="mt-1 text-sm text-slate-500">
                                    Give your list a simple
                                    name.
                                </p>
                            </div>

                            <button
                                type="button"
                                onClick={() =>
                                    setShowCreate(false)
                                }
                                className="flex h-9 w-9 items-center justify-center rounded-lg text-xl text-slate-400 hover:bg-slate-100"
                            >
                                ×
                            </button>
                        </div>

                        <div className="mt-6">
                            <label className="mb-2 block text-sm font-semibold text-slate-700">
                                List name
                            </label>

                            <input
                                autoFocus
                                value={newListName}
                                onChange={(event) =>
                                    setNewListName(
                                        event.target.value
                                    )
                                }
                                onKeyDown={(event) => {
                                    if (
                                        event.key ===
                                        "Enter"
                                    ) {
                                        createList();
                                    }
                                }}
                                placeholder="e.g. Shopping"
                                className="w-full rounded-xl border border-slate-200 px-4 py-3 text-sm outline-none transition focus:border-emerald-400 focus:ring-2 focus:ring-emerald-100"
                            />
                        </div>

                        <div className="mt-6 flex gap-3">
                            <button
                                type="button"
                                onClick={() =>
                                    setShowCreate(false)
                                }
                                className="flex-1 rounded-xl border border-slate-200 px-4 py-3 text-sm font-semibold text-slate-600 hover:bg-slate-50"
                            >
                                Cancel
                            </button>

                            <button
                                type="button"
                                onClick={createList}
                                disabled={
                                    !newListName.trim()
                                }
                                className="flex-1 rounded-xl bg-emerald-600 px-4 py-3 text-sm font-semibold text-white hover:bg-emerald-700 disabled:cursor-not-allowed disabled:opacity-50"
                            >
                                Create list
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}

export default Lists;