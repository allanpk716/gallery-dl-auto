"""
OAuth PKCE core implementation module.

This module provides PKCE (Proof Key for Code Exchange) utilities
for secure OAuth authentication flows.
"""

import base64
import hashlib
import secrets
from typing import Any


class OAuthError(Exception):
    """
    OAuth authentication error.

    Raised when OAuth operations fail due to network errors,
    invalid responses, or authentication failures.
    """

    def __init__(self, message: str, status_code: int | None = None) -> None:
        """
        Initialize OAuth error.

        Args:
            message: Error description
            status_code: Optional HTTP status code
        """
        self.message = message
        self.status_code = status_code
        super().__init__(self.message)

    def __str__(self) -> str:
        """Return string representation of error."""
        if self.status_code:
            return f"OAuth Error ({self.status_code}): {self.message}"
        return f"OAuth Error: {self.message}"


def generate_pkce_verifier() -> str:
    """
    Generate a PKCE code verifier.

    Creates a cryptographically random URL-safe string between 43-128 characters.

    Returns:
        URL-safe random string (length 43-128)
    """
    # Generate 96 bytes = 128 characters in base64url encoding
    # Truncate to ensure maximum length of 128
    verifier = secrets.token_urlsafe(96)
    return verifier[:128]


def generate_pkce_challenge(verifier: str) -> str:
    """
    Generate a PKCE code challenge from a verifier.

    Creates a SHA-256 hash of the verifier, encoded in base64url format
    without padding.

    Args:
        verifier: PKCE code verifier string

    Returns:
        Base64url-encoded SHA-256 hash (without padding)
    """
    # Hash the verifier with SHA-256
    hash_bytes = hashlib.sha256(verifier.encode("utf-8")).digest()

    # Encode in base64url and remove padding
    challenge = base64.urlsafe_b64encode(hash_bytes).decode("utf-8")
    return challenge.rstrip("=")


# OAuth constants (Pixiv official client credentials)
# Source: Pixiv official Android app
CLIENT_ID = "MOBrBDS8blbauoSck0ZfDbtuzpyT"
CLIENT_SECRET = "lsACyCD94FhDUtGTXi3QzcFE2uU1hqtDaKeqrdwj"
AUTH_URL = "https://app-api.pixiv.net/web/v1/login"
TOKEN_URL = "https://oauth.secure.pixiv.net/auth/token"
REDIRECT_URI = "https://app-api.pixiv.net/web/v1/users/auth/pixiv/callback"
