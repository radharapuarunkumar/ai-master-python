/**
 * AI Master Python — Frontend Configuration
 * ==========================================
 * Firebase replaces the previous Google OAuth / GOOGLE_CLIENT_ID flow.
 * All auth is handled by Firebase on the frontend; the backend receives
 * a Firebase ID token and issues its own JWT session cookies.
 */

const CONFIG = {
  // ── Firebase ──────────────────────────────────────────────
  FIREBASE: {
    apiKey:            "AIzaSyAkAUsLXT9LHjBNHoHfjKYtbVoTZ7DQUkc",
    authDomain:        "ai-master-python.firebaseapp.com",
    projectId:         "ai-master-python",
    storageBucket:     "ai-master-python.firebasestorage.app",
    messagingSenderId: "582774203686",
    appId:             "1:582774203686:web:09aa75d9135b5e875c8de7",
    measurementId:     "G-5QC6XP08CX",
  },

  // ── Development ───────────────────────────────────────────
  // Set DEV_MODE to true to bypass real authentication
  DEV_MODE: true,

  // ── Backend API ───────────────────────────────────────────
  API_BASE_URL: window.location.hostname === "localhost" || window.location.hostname === "127.0.0.1" 
    ? "http://localhost:8000/api/v1" 
    : window.location.origin + "/api/v1",

  // ── App ───────────────────────────────────────────────────
  APP_NAME: "AI Master Python",
};

Object.freeze(CONFIG);
Object.freeze(CONFIG.FIREBASE);
window.CONFIG = CONFIG;
