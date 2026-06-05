/**
 * AI Master Python — API Client
 * Centralised fetch wrapper that connects to the FastAPI backend.
 * Base URL is read from CONFIG (set in frontend/js/config.js).
 */

// CONFIG is loaded by config.js which must be included before this script
const API_BASE = (typeof CONFIG !== 'undefined' ? CONFIG.API_BASE_URL : null)
  || 'http://localhost:8000/api/v1';

class ApiError extends Error {
  constructor(message, status, code) {
    super(message);
    this.status = status;
    this.code = code;
    this.name = 'ApiError';
  }
}

async function request(path, options = {}) {
  const url = `${API_BASE}${path}`;
  const config = {
    credentials: 'include',            // send httpOnly cookies
    headers: { 'Content-Type': 'application/json', ...options.headers },
    ...options,
  };
  if (config.body && typeof config.body === 'object') {
    config.body = JSON.stringify(config.body);
  }

  let res;
  try {
    res = await fetch(url, config);
  } catch (err) {
    throw new ApiError('Network error — is the backend running?', 0, 'NETWORK_ERROR');
  }

  // 204 No Content
  if (res.status === 204) return null;

  const data = await res.json().catch(() => ({}));

  if (!res.ok) {
    const msg = data?.error?.message || data?.detail || `HTTP ${res.status}`;
    throw new ApiError(msg, res.status, data?.error?.code);
  }

  return data?.data ?? data;
}

/* ── Token refresh interceptor ───────────────────────────── */
let refreshPromise = null;
async function requestWithRefresh(path, options = {}) {
  try {
    return await request(path, options);
  } catch (err) {
    if (err.status === 401 && path !== '/auth/refresh' && path !== '/auth/google/callback') {
      // Attempt one token refresh (deduplicated)
      if (!refreshPromise) {
        refreshPromise = request('/auth/refresh', { method: 'POST' }).finally(() => {
          refreshPromise = null;
        });
      }
      try {
        await refreshPromise;
        return await request(path, options); // Retry
      } catch {
        if (typeof CONFIG !== 'undefined' && CONFIG.DEV_MODE) {
          console.warn(`[DEV MODE] Bypassing 401 on ${path} — returning empty data.`);
          return path.includes('progress/all') ? [] : {};
        }
        // Refresh failed → boot to login
        Auth.clear();
        window.location.href = '/frontend/pages/login.html';
        throw err;
      }
    }
    throw err;
  }
}

/* ── Auth endpoints ──────────────────────────────────────── */
const AuthApi = {
  googleCallback: (code) =>
    request('/auth/google/callback', { method: 'POST', body: { code } }),

  refresh: () =>
    request('/auth/refresh', { method: 'POST' }),

  logout: () =>
    requestWithRefresh('/auth/logout', { method: 'POST' }),

  me: () =>
    requestWithRefresh('/auth/me'),
};

/* ── User endpoints ──────────────────────────────────────── */
const UsersApi = {
  me: () => requestWithRefresh('/users/me'),
  stats: () => requestWithRefresh('/users/me/stats'),
  updateMe: (data) => requestWithRefresh('/users/me', { method: 'PATCH', body: data }),
  list: (params = {}) => {
    const q = new URLSearchParams(params).toString();
    return requestWithRefresh(`/users?${q}`);
  },
  updateRole: (id, role) =>
    requestWithRefresh(`/users/${id}/role`, { method: 'PATCH', body: { role } }),
  deactivate: (id) =>
    requestWithRefresh(`/users/${id}`, { method: 'DELETE' }),
};

/* ── Course endpoints ────────────────────────────────────── */
const CoursesApi = {
  list: (params = {}) => {
    const q = new URLSearchParams(params).toString();
    return requestWithRefresh(`/courses?${q}`);
  },
  get: (slug) => requestWithRefresh(`/courses/${slug}`),
  create: (data) => requestWithRefresh('/courses', { method: 'POST', body: data }),
  update: (id, data) => requestWithRefresh(`/courses/${id}`, { method: 'PUT', body: data }),
  delete: (id) => requestWithRefresh(`/courses/${id}`, { method: 'DELETE' }),
  listModules: (courseId) => requestWithRefresh(`/courses/${courseId}/modules`),
  listLessons: (moduleId) => requestWithRefresh(`/courses/modules/${moduleId}/lessons`),
  getLesson: (lessonId) => requestWithRefresh(`/courses/lessons/${lessonId}`),
};

/* ── Progress endpoints ──────────────────────────────────── */
const ProgressApi = {
  all: () => requestWithRefresh('/progress'),
  course: (courseId) => requestWithRefresh(`/progress/course/${courseId}`),
  start: (lessonId) =>
    requestWithRefresh(`/progress/lesson/${lessonId}/start`, { method: 'POST' }),
  complete: (lessonId, body = {}) =>
    requestWithRefresh(`/progress/lesson/${lessonId}/complete`, { method: 'POST', body }),
  streak: () => requestWithRefresh('/progress/streak'),
};

/* ── Expose globally ─────────────────────────────────────── */
window.API = { AuthApi, UsersApi, CoursesApi, ProgressApi, ApiError };
