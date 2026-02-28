"""
OAuth authentication module for gallery-dl-auto.

Provides PKCE-based OAuth authentication for Pixiv API access.
"""

from .oauth import OAuthError, generate_pkce_challenge, generate_pkce_verifier
from .pixiv_auth import PixivOAuth

__all__ = [
    "OAuthError",
    "generate_pkce_verifier",
    "generate_pkce_challenge",
    "PixivOAuth",
]
