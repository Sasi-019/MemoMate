// Backend base URL. Vite bakes VITE_API_URL in at BUILD time, so it must be
// set in your host's environment variables before the frontend is built.
const API_URL = (
    import.meta.env.VITE_API_URL ||
    "https://memomate-af77.onrender.com"
).replace(/\/+$/, "");

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
// TIME HELPERS
// The backend stores UTC. These keep the browser's local
// time and the server's UTC time in sync.
// ======================================================

// Minutes the user's timezone is AHEAD of UTC (India = 330).
export function getTimezoneOffsetMinutes() {
    return -new Date().getTimezoneOffset();
}

// "2026-10-04T18:00" (local, from an input) -> "2026-10-04T12:30:00.000Z"
export function localToUtcIso(localValue) {
    if (!localValue) {
        return null;
    }

    const date = new Date(localValue);

    if (Number.isNaN(date.getTime())) {
        return null;
    }

    return date.toISOString();
}

// Today's date in the user's LOCAL timezone as "YYYY-MM-DD".
// (toISOString() would give the UTC date, which is "yesterday"
// for India before 5:30 AM.)
export function todayLocalDate() {
    const now = new Date();

    const year = now.getFullYear();
    const month = String(now.getMonth() + 1).padStart(2, "0");
    const day = String(now.getDate()).padStart(2, "0");

    return `${year}-${month}-${day}`;
}


// ======================================================
// Shared header builder
// ======================================================

function buildHeaders(options) {
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

    // Only default to JSON for plain bodies. For FormData the browser
    // must set "multipart/form-data; boundary=..." itself, otherwise the
    // upload (e.g. voice recording) is rejected by the server.
    const isFormData =
        typeof FormData !== "undefined" &&
        options.body instanceof FormData;

    if (
        options.body &&
        !isFormData &&
        !headers.has("Content-Type")
    ) {
        headers.set(
            "Content-Type",
            "application/json"
        );
    }

    return headers;
}


// ======================================================
// API FUNCTION
// Returns parsed JSON (throws on errors)
// ======================================================

export async function api(path, options = {}) {
    const headers = buildHeaders(options);

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

    if (response.status === 401 && getToken()) {
        clearToken();
    }

    if (!response.ok) {
        throw new Error(
            (typeof data.detail === "string" && data.detail) ||
            data.message ||
            "Request failed."
        );
    }

    return data;
}


// ======================================================
// apiFetch
// Returns the RAW Response object
// ======================================================

export async function apiFetch(
    path,
    options = {}
) {
    const headers = buildHeaders(options);

    const response = await fetch(
        `${API_URL}${path}`,
        {
            ...options,
            headers,
        }
    );

    // An expired / invalid session sends the user back to login.
    // (Network errors and 5xx are NOT treated as logged out.)
    if (response.status === 401 && getToken()) {
        clearToken();
    }

    return response;
}
