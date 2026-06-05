"""
Firebase Admin SDK integration for AI Master Python.

Reads credentials from the service account JSON specified by
GOOGLE_APPLICATION_CREDENTIALS in .env.  Exposes:

  • init_firebase()          – call once at app startup
  • verify_firebase_token()  – verify an ID token from the frontend
  • startup_check()          – raises clearly if misconfigured

Required .env variables:
  FIREBASE_PROJECT_ID             = ai-master-python
  GOOGLE_APPLICATION_CREDENTIALS  = secrets/firebase-service-account.json
"""
from __future__ import annotations

import json
import logging
import os
from pathlib import Path

logger = logging.getLogger(__name__)

_firebase_app = None  # module-level singleton — initialised once


# ── Initialisation ────────────────────────────────────────────────────────────

def init_firebase() -> None:
    """Initialise Firebase Admin SDK.  Safe to call multiple times (idempotent).

    Credential resolution order:
      1. GOOGLE_APPLICATION_CREDENTIALS env var → path to service-account JSON
      2. Application Default Credentials (ADC) — works on GCP / Cloud Run

    Raises:
        RuntimeError: If the service account file is the placeholder or invalid.
        FileNotFoundError: If GOOGLE_APPLICATION_CREDENTIALS path doesn't exist.
    """
    global _firebase_app

    import firebase_admin
    from firebase_admin import credentials

    # Already initialised — nothing to do
    if _firebase_app is not None or firebase_admin._apps:
        _firebase_app = firebase_admin.get_app() if firebase_admin._apps else _firebase_app
        return

    cred_path = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", "")
    project_id = os.environ.get("FIREBASE_PROJECT_ID", "ai-master-python")

    if cred_path:
        p = Path(cred_path)
        if not p.exists():
            raise FileNotFoundError(
                f"Firebase service account file not found: {p.resolve()}\n"
                "  → Download it from Firebase Console → Project Settings → Service Accounts\n"
                "  → Save as: secrets/firebase-service-account.json"
            )

        # Detect placeholder file
        try:
            data = json.loads(p.read_text(encoding="utf-8"))
            if "_INSTRUCTIONS" in data or "type" not in data:
                raise RuntimeError(
                    f"Found placeholder at {p.resolve()} — not a real service account.\n"
                    "  → Go to: https://console.firebase.google.com/project/ai-master-python"
                    "/settings/serviceaccounts/adminsdk\n"
                    "  → Click 'Generate new private key' and save as "
                    "secrets/firebase-service-account.json"
                )
        except json.JSONDecodeError as exc:
            raise RuntimeError(f"Invalid JSON in {p}: {exc}") from exc

        cred = credentials.Certificate(str(p))
        logger.info("Firebase Admin: loaded service account from '%s'", p)
    else:
        # Fall back to Application Default Credentials
        cred = credentials.ApplicationDefault()
        logger.info("Firebase Admin: using Application Default Credentials (no GOOGLE_APPLICATION_CREDENTIALS set)")

    _firebase_app = firebase_admin.initialize_app(
        cred,
        {"projectId": project_id},
    )
    logger.info("Firebase Admin SDK ready — project: '%s'", project_id)


def startup_check() -> None:
    """Call during app startup to surface misconfig early with a clear message."""
    try:
        init_firebase()
        logger.info("Firebase Admin SDK startup check passed")
    except (FileNotFoundError, RuntimeError) as exc:
        # Log clearly but don't crash the whole app — auth will fail at request time
        logger.error(
            "\n"
            "╔══════════════════════════════════════════════════════════════╗\n"
            "║  Firebase Admin SDK NOT configured — Google login disabled   ║\n"
            "╠══════════════════════════════════════════════════════════════╣\n"
            "║  %s\n"
            "╚══════════════════════════════════════════════════════════════╝",
            str(exc).replace("\n", "\n║  "),
        )
    except Exception as exc:
        logger.error("Firebase Admin SDK unexpected error during startup: %s", exc)


# ── Token verification ────────────────────────────────────────────────────────

async def verify_firebase_token(id_token: str) -> dict:
    """Verify a Firebase ID token and return decoded user claims.

    Args:
        id_token: The Firebase ID token string sent by the frontend after
                  a successful Google sign-in popup.

    Returns:
        Dict containing:
            uid, email, name, picture, email_verified, firebase_uid, _claims

    Raises:
        ValueError: Token is invalid, expired, revoked, or project mismatch.
        RuntimeError: Firebase Admin SDK is not initialised.
    """
    from firebase_admin import auth as firebase_auth

    # Ensure SDK is ready
    init_firebase()

    try:
        decoded: dict = firebase_auth.verify_id_token(
            id_token,
            check_revoked=True,   # detects forcibly-revoked tokens
        )
    except firebase_auth.RevokedIdTokenError as exc:
        raise ValueError("Firebase token has been revoked. Please sign in again.") from exc
    except firebase_auth.ExpiredIdTokenError as exc:
        raise ValueError("Firebase token has expired. Please sign in again.") from exc
    except firebase_auth.InvalidIdTokenError as exc:
        raise ValueError(f"Invalid Firebase token: {exc}") from exc
    except Exception as exc:
        logger.warning("Firebase token verification failed: %s", exc)
        raise ValueError(f"Firebase token verification failed: {exc}") from exc

    # Normalise the name field — Firebase may store it under different keys
    name = (
        decoded.get("name")
        or decoded.get("display_name")
        or decoded.get("email", "").split("@")[0]
    )

    return {
        "uid":            decoded["uid"],
        "email":          decoded.get("email", ""),
        "name":           name,
        "picture":        decoded.get("picture", ""),
        "email_verified": decoded.get("email_verified", False),
        "firebase_uid":   decoded["uid"],
        "_claims":        decoded,
    }
