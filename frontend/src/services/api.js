
const API_URL =
    import.meta.env.VITE_API_URL || "http://127.0.0.1:8000";

export { API_URL };


// ======================================================
// TOKEN FUNCTIONS
// ======================================================

export function getToken() {
    return localStorage.getItem("memomate_token");
}

export function token() {
    return getToken();
}

export function setToken(value) {
    if (value) {
        localStorage.setItem("memomate_token", value);
    } else {
        localStorage.removeItem("memomate_token");
    }
}

export function clearToken() {
    localStorage.removeItem("memomate_token");
    localStorage.removeItem("memomate_user");

    window.dispatchEvent(
        new Event("memomate:unauthorized")
    );
}


// ======================================================
// USER FUNCTIONS
// ======================================================

export function getStoredUser() {
    const stored = localStorage.getItem("memomate_user");

    if (!stored) {
        return null;
    }

    try {
        return JSON.parse(stored);
    } catch (error) {
        console.error("Invalid stored user:", error);
        localStorage.removeItem("memomate_user");
        return null;
    }
}

export function setStoredUser(user) {
    if (!user) {
        localStorage.removeItem("memomate_user");
        return;
    }

    localStorage.setItem(
        "memomate_user",
        JSON.stringify(user)
    );
}


// ======================================================
// API FUNCTION
// Returns parsed JSON
// ======================================================

export async function api(path, options = {}) {
    const headers = new Headers(
        options.headers || {}
    );

    const t = getToken();

    if (t) {
        headers.set(
            "Authorization",
            `Bearer ${t}`
        );
    }

    if (
        options.body &&
        !headers.has("Content-Type")
    ) {
        headers.set(
            "Content-Type",
            "application/json"
        );
    }

    const response = await fetch(
        `${API_URL}${path}`,
        {
            ...options,
            headers,
        }
    );

    const data = await response
        .json()
        .catch(() => ({}));

    if (response.status === 401) {
        clearToken();
    }

    if (!response.ok) {
        throw new Error(
            data.detail ||
            data.message ||
            "Request failed."
        );
    }

    return data;
}


// ======================================================
// apiFetch
// Returns the RAW Response object
// Used by App.jsx
// ======================================================

export async function apiFetch(
    path,
    options = {}
) {
    const headers = new Headers(
        options.headers || {}
    );

    const t = getToken();

    if (t) {
        headers.set(
            "Authorization",
            `Bearer ${t}`
        );
    }

    if (
        options.body &&
        !headers.has("Content-Type")
    ) {
        headers.set(
            "Content-Type",
            "application/json"
        );
    }

    return fetch(
        `${API_URL}${path}`,
        {
            ...options,
            headers,
        }
    );
}


