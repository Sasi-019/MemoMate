
import { getToken } from "./api";

const originalFetch = window.fetch;

window.fetch = async function (input, options = {}) {
    const headers = new Headers(options.headers || {});

    const token = getToken();

    if (token) {
        headers.set("Authorization", `Bearer ${token}`);
    }

    return originalFetch(input, {
        ...options,
        headers,
    });
};

