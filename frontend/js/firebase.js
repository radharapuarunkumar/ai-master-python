/**
 * Firebase Authentication wrapper for AI Master Python.
 *
 * Uses the Firebase v10 compat CDN build so no bundler is required.
 * Must be loaded AFTER config.js and the Firebase CDN scripts.
 *
 * Exports (on window.FirebaseAuth):
 *   signInWithGoogle()   → opens Google popup, returns Firebase user
 *   signOutUser()        → signs out from Firebase + clears local state
 *   getCurrentUser()     → returns firebase.auth().currentUser (or null)
 *   getIdToken()         → returns fresh Firebase ID token string
 *   onAuthStateChanged() → subscribes to auth state changes
 */

(function () {
  "use strict";

  // Guard: Firebase compat SDK must be loaded before this script
  if (typeof firebase === "undefined") {
    console.error("[FirebaseAuth] Firebase SDK not loaded. Check script order in HTML.");
    return;
  }

  // Initialise Firebase app (idempotent — safe if called multiple times)
  if (!firebase.apps.length) {
    firebase.initializeApp(CONFIG.FIREBASE);
  }

  const auth = firebase.auth();
  const googleProvider = new firebase.auth.GoogleAuthProvider();
  googleProvider.addScope("email");
  googleProvider.addScope("profile");
  // Force account selection every time so switching accounts is easy
  googleProvider.setCustomParameters({ prompt: "select_account" });

  // ── Public API ───────────────────────────────────────────────────────────

  /**
   * Opens a Google sign-in popup.
   * Returns the Firebase UserCredential on success.
   * Throws on cancellation or error.
   */
  async function signInWithGoogle() {
    return auth.signInWithPopup(googleProvider);
  }

  /**
   * Signs the current user out of Firebase.
   */
  async function signOutUser() {
    return auth.signOut();
  }

  /**
   * Returns the currently signed-in Firebase user, or null.
   */
  function getCurrentUser() {
    return auth.currentUser;
  }

  /**
   * Returns a fresh Firebase ID token for the current user.
   * Automatically refreshes if it has expired.
   * Returns null if no user is signed in.
   */
  async function getIdToken() {
    const user = auth.currentUser;
    if (!user) return null;
    return user.getIdToken(/* forceRefresh = */ false);
  }

  /**
   * Subscribes to Firebase auth state changes.
   * callback(user) is called with the Firebase user object (or null on sign-out).
   * Returns the unsubscribe function.
   */
  function onAuthStateChanged(callback) {
    return auth.onAuthStateChanged(callback);
  }

  // Expose on window
  window.FirebaseAuth = {
    signInWithGoogle,
    signOutUser,
    getCurrentUser,
    getIdToken,
    onAuthStateChanged,
    auth, // raw auth instance for advanced use
  };

  console.log("[FirebaseAuth] Initialised for project:", CONFIG.FIREBASE.projectId);
})();
