/**
 * The BlindPaper API: one small fetch wrapper and a function for every endpoint.
 * Every call resolves to parsed JSON (or a Blob for downloads) and rejects with an ApiError
 * whose message is safe to show the user.
 */

export const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://127.0.0.1:8000";

const TOKEN_KEY = "blindpaper.token";

export const tokenStore = {
  get() {
    try {
      return localStorage.getItem(TOKEN_KEY);
    } catch {
      return null;
    }
  },
  set(token) {
    try {
      localStorage.setItem(TOKEN_KEY, token);
    } catch {
      /* storage unavailable: the session just won't survive a reload */
    }
  },
  clear() {
    try {
      localStorage.removeItem(TOKEN_KEY);
    } catch {
      /* nothing to clear */
    }
  },
};

export class ApiError extends Error {
  constructor(message, { status = 0, problems = [], retryAfter = null } = {}) {
    super(message);
    this.name = "ApiError";
    this.status = status;
    this.problems = problems; // a list of things to fix, for 422 configuration errors
    this.retryAfter = retryAfter; // seconds, for 429 rate limits
  }
}

let unauthorizedHandler = null;

/** Called when the server says our session is gone, so the app can send the user to the login page. */
export function onUnauthorized(handler) {
  unauthorizedHandler = handler;
}

function errorMessage(status, body) {
  const detail = body?.detail;
  if (typeof detail === "string") return detail;
  if (Array.isArray(detail)) {
    return detail
      .map((item) => {
        const field = Array.isArray(item.loc) ? item.loc.filter((p) => p !== "body").join(".") : "";
        return field ? `${field}: ${item.msg}` : item.msg;
      })
      .join("; ");
  }
  return `Server error (${status})`;
}

async function request(path, { method = "GET", json, form, query, blob = false, auth = true } = {}) {
  const url = new URL(`${API_BASE}${path}`);
  Object.entries(query || {}).forEach(([key, value]) => {
    if (value !== undefined && value !== null && value !== "") url.searchParams.set(key, value);
  });

  const headers = {};
  const token = tokenStore.get();
  if (auth && token) headers.Authorization = `Bearer ${token}`;
  if (json !== undefined) headers["Content-Type"] = "application/json";

  let response;
  try {
    response = await fetch(url, { method, headers, body: json !== undefined ? JSON.stringify(json) : form });
  } catch {
    throw new ApiError(`Cannot reach the BlindPaper server at ${API_BASE}. Check that the backend is running.`);
  }

  if (!response.ok) {
    let body = null;
    try {
      body = await response.json();
    } catch {
      /* not JSON */
    }
    if (response.status === 401 && auth && token) {
      tokenStore.clear();
      unauthorizedHandler?.();
    }
    const retryAfter = Number(response.headers.get("Retry-After")) || null;
    throw new ApiError(errorMessage(response.status, body), {
      status: response.status,
      problems: Array.isArray(body?.problems) ? body.problems : [],
      retryAfter,
    });
  }

  if (blob) {
    const disposition = response.headers.get("Content-Disposition") || "";
    const filename = /filename="?([^";]+)"?/.exec(disposition)?.[1] || "question-paper.pdf";
    return { blob: await response.blob(), filename };
  }
  return response.json();
}

/** Save a downloaded Blob through the browser. */
export function saveBlob({ blob, filename }) {
  const url = URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = url;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}

export const api = {
  auth: {
    register: (data) => request("/api/auth/register", { method: "POST", json: data, auth: false }),
    login: (email, password) => request("/api/auth/login", { method: "POST", json: { email, password }, auth: false }),
    me: () => request("/api/auth/me"),
    updateMe: (data) => request("/api/auth/me", { method: "PUT", json: data }),
    logout: () => request("/api/auth/logout", { method: "POST" }),
  },

  syllabus: {
    process: (file) => {
      const form = new FormData();
      form.append("file", file);
      return request("/api/syllabus/process", { method: "POST", form });
    },
    list: () => request("/api/syllabus"),
    get: (id) => request(`/api/syllabus/${id}`),
    remove: (id) => request(`/api/syllabus/${id}`, { method: "DELETE" }),
  },

  papers: {
    generate: (config) => request("/api/papers/generate", { method: "POST", json: config }),
    list: (status) => request("/api/papers", { query: { status } }),
    get: (id) => request(`/api/papers/${id}`),
    update: (id, questions) => request(`/api/papers/${id}`, { method: "PUT", json: { questions } }),
    regenerate: (id) => request(`/api/papers/${id}/regenerate`, { method: "POST" }),
    regenerateQuestion: (id, subQuestionId) =>
      request(`/api/papers/${id}/questions/${encodeURIComponent(subQuestionId)}/regenerate`, { method: "POST" }),
    submit: (id) => request(`/api/papers/${id}/submit`, { method: "POST" }),
    remove: (id) => request(`/api/papers/${id}`, { method: "DELETE" }),
    notifications: () => request("/api/papers/notifications"),
    pdf: (id) => request(`/api/papers/${id}/pdf`, { blob: true }),
  },

  admin: {
    stats: (department) => request("/api/admin/stats", { query: { department } }),
    papers: ({ status, department, q } = {}) => request("/api/admin/papers", { query: { status, department, q } }),
    paper: (id) => request(`/api/admin/papers/${id}`),
    approve: (id) => request(`/api/admin/papers/${id}/approve`, { method: "POST" }),
    reject: (id, reason) => request(`/api/admin/papers/${id}/reject`, { method: "POST", json: { reason } }),
    faculty: () => request("/api/admin/faculty"),
    departments: () => request("/api/admin/departments"),
    pdf: (id) => request(`/api/admin/papers/${id}/pdf`, { blob: true }),
  },
};
