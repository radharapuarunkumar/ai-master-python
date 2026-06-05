"""
Google OAuth 2.0 client integration.

Handles the server-side OAuth flow:
  1. Exchange authorization code for tokens
  2. Fetch user profile from Google
  3. Verify ID tokens
"""
from __future__ import annotations

import logging

import httpx

logger = logging.getLogger(__name__)

GOOGLE_TOKEN_URL = "https://oauth2.googleapis.com/token"
GOOGLE_USERINFO_URL = "https://www.googleapis.com/oauth2/v2/userinfo"
GOOGLE_TOKENINFO_URL = "https://oauth2.googleapis.com/tokeninfo"


class GoogleOAuthClient:
    """Handles all Google OAuth 2.0 server-side operations."""

    def __init__(self, client_id: str, client_secret: str, redirect_uri: str) -> None:
        self.client_id = client_id
        self.client_secret = client_secret
        self.redirect_uri = redirect_uri
        self._http = httpx.AsyncClient(timeout=15.0)

    async def exchange_code(self, code: str, redirect_uri: str | None = None) -> dict:
        """Exchange an authorization code for access + id tokens.

        Args:
            code: The authorization code from Google's redirect.
            redirect_uri: Override redirect URI (must match original).

        Returns:
            Token response dict with access_token, id_token, refresh_token.

        Raises:
            ValueError: If Google returns an error response.
        """
        payload = {
            "code": code,
            "client_id": self.client_id,
            "client_secret": self.client_secret,
            "redirect_uri": redirect_uri or self.redirect_uri,
            "grant_type": "authorization_code",
        }
        response = await self._http.post(GOOGLE_TOKEN_URL, data=payload)
        data = response.json()

        if "error" in data:
            logger.error("Google token exchange failed: %s", data)
            raise ValueError(f"Google OAuth error: {data.get('error_description', data['error'])}")

        return data

    async def get_user_info(self, access_token: str) -> dict:
        """Fetch the authenticated user's profile from Google.

        Args:
            access_token: A valid Google access token.

        Returns:
            User profile dict with id, email, name, picture.

        Raises:
            ValueError: On HTTP or API errors.
        """
        response = await self._http.get(
            GOOGLE_USERINFO_URL,
            headers={"Authorization": f"Bearer {access_token}"},
        )
        if response.status_code != 200:
            raise ValueError(f"Failed to fetch Google user info: {response.status_code}")

        return response.json()

    async def verify_id_token(self, id_token: str) -> dict:
        """Verify a Google ID token and return its claims.

        Args:
            id_token: The JWT id_token from Google's token endpoint.

        Returns:
            Decoded token claims dict.

        Raises:
            ValueError: If token is invalid or expired.
        """
        response = await self._http.get(
            GOOGLE_TOKENINFO_URL,
            params={"id_token": id_token},
        )
        data = response.json()

        if "error_description" in data:
            raise ValueError(f"Invalid Google ID token: {data['error_description']}")

        # Verify audience matches our client ID
        if data.get("aud") != self.client_id:
            raise ValueError("Google ID token audience mismatch")

        return data

    async def aclose(self) -> None:
        """Close the underlying HTTP client."""
        await self._http.aclose()
