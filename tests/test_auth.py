"""
OAuth authentication module tests.

Tests for PKCE generation, OAuth login flow, and token exchange.
"""

import pytest
from unittest.mock import MagicMock, patch
import requests

from gallery_dl_auto.auth import (
    OAuthError,
    PixivOAuth,
    generate_pkce_challenge,
    generate_pkce_verifier,
)


class TestPKCEGeneration:
    """Test PKCE verifier and challenge generation."""

    def test_pkce_verifier_length(self) -> None:
        """Verify verifier length is within 43-128 characters."""
        verifier = generate_pkce_verifier()
        assert 43 <= len(verifier) <= 128

    def test_pkce_verifier_urlsafe(self) -> None:
        """Verify verifier only contains URL-safe characters."""
        import re

        verifier = generate_pkce_verifier()
        # URL-safe characters: A-Za-z0-9-._~
        assert re.match(r"^[A-Za-z0-9\-._~]+$", verifier)

    def test_pkce_challenge_format(self) -> None:
        """Verify challenge is base64url format without padding."""
        import re

        verifier = generate_pkce_verifier()
        challenge = generate_pkce_challenge(verifier)
        # Base64url: A-Za-z0-9-_
        # No padding (=)
        assert re.match(r"^[A-Za-z0-9\-_]+$", challenge)
        assert "=" not in challenge

    def test_pkce_deterministic(self) -> None:
        """Verify same verifier generates same challenge."""
        verifier = generate_pkce_verifier()
        challenge1 = generate_pkce_challenge(verifier)
        challenge2 = generate_pkce_challenge(verifier)
        assert challenge1 == challenge2

    def test_pkce_different_verifiers(self) -> None:
        """Verify different verifiers generate different challenges."""
        verifier1 = generate_pkce_verifier()
        verifier2 = generate_pkce_verifier()
        challenge1 = generate_pkce_challenge(verifier1)
        challenge2 = generate_pkce_challenge(verifier2)
        # Highly unlikely to be equal
        assert challenge1 != challenge2


class TestOAuthError:
    """Test OAuthError exception class."""

    def test_oauth_error_basic(self) -> None:
        """Test basic error message."""
        error = OAuthError("Test error")
        assert str(error) == "OAuth Error: Test error"
        assert error.message == "Test error"
        assert error.status_code is None

    def test_oauth_error_with_status_code(self) -> None:
        """Test error with HTTP status code."""
        error = OAuthError("Unauthorized", status_code=401)
        assert str(error) == "OAuth Error (401): Unauthorized"
        assert error.message == "Unauthorized"
        assert error.status_code == 401


class TestPixivOAuth:
    """Test PixivOAuth login flow."""

    def test_oauth_initialization(self) -> None:
        """Test OAuth handler initialization."""
        oauth = PixivOAuth()
        assert hasattr(oauth, "code_verifier")
        assert hasattr(oauth, "code_challenge")
        assert 43 <= len(oauth.code_verifier) <= 128
        assert len(oauth.code_challenge) > 0

    @patch("gallery_dl_auto.auth.pixiv_auth.webbrowser.open")
    @patch("gallery_dl_auto.auth.pixiv_auth.Prompt.ask")
    @patch("gallery_dl_auto.auth.pixiv_auth.requests.post")
    def test_oauth_login_success(
        self,
        mock_post: MagicMock,
        mock_prompt: MagicMock,
        mock_browser: MagicMock,
    ) -> None:
        """Test successful OAuth login flow."""
        # Mock authorization code input
        mock_prompt.return_value = "test_auth_code_12345"

        # Mock token exchange response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "access_token": "test_access_token",
            "refresh_token": "test_refresh_token",
            "expires_in": 3600,
            "token_type": "Bearer",
        }
        mock_post.return_value = mock_response

        # Execute login
        oauth = PixivOAuth()
        tokens = oauth.login()

        # Verify
        assert tokens["access_token"] == "test_access_token"
        assert tokens["refresh_token"] == "test_refresh_token"
        assert tokens["expires_in"] == 3600

        # Verify browser was opened
        mock_browser.assert_called_once()

        # Verify token exchange request
        mock_post.assert_called_once()
        call_data = mock_post.call_args[1]["data"]
        assert call_data["code"] == "test_auth_code_12345"
        assert call_data["grant_type"] == "authorization_code"

    @patch("gallery_dl_auto.auth.pixiv_auth.webbrowser.open")
    @patch("gallery_dl_auto.auth.pixiv_auth.Prompt.ask")
    @patch("gallery_dl_auto.auth.pixiv_auth.requests.post")
    def test_oauth_login_with_url_input(
        self,
        mock_post: MagicMock,
        mock_prompt: MagicMock,
        mock_browser: MagicMock,
    ) -> None:
        """Test OAuth login with URL input (extract code from URL)."""
        # Mock URL input with code parameter
        mock_prompt.return_value = (
            "https://example.com/callback?code=extracted_code_67890&state=xyz"
        )

        # Mock token exchange
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "access_token": "access_token_from_url",
            "refresh_token": "refresh_token_from_url",
            "expires_in": 3600,
        }
        mock_post.return_value = mock_response

        # Execute login
        oauth = PixivOAuth()
        tokens = oauth.login()

        # Verify code was extracted from URL
        assert tokens["access_token"] == "access_token_from_url"
        call_data = mock_post.call_args[1]["data"]
        assert call_data["code"] == "extracted_code_67890"

    @patch("gallery_dl_auto.auth.pixiv_auth.webbrowser.open")
    @patch("gallery_dl_auto.auth.pixiv_auth.Prompt.ask")
    @patch("gallery_dl_auto.auth.pixiv_auth.requests.post")
    def test_oauth_login_auth_error(
        self,
        mock_post: MagicMock,
        mock_prompt: MagicMock,
        mock_browser: MagicMock,
    ) -> None:
        """Test OAuth login with authentication error (401)."""
        # Mock authorization code input
        mock_prompt.return_value = "invalid_code"

        # Mock 401 response
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(
            response=mock_response
        )
        mock_post.return_value = mock_response

        # Execute login and expect error
        oauth = PixivOAuth()
        with pytest.raises(OAuthError) as exc_info:
            oauth.login()

        # Verify error contains status code
        assert exc_info.value.status_code == 401

    @patch("gallery_dl_auto.auth.pixiv_auth.webbrowser.open")
    @patch("gallery_dl_auto.auth.pixiv_auth.Prompt.ask")
    @patch("gallery_dl_auto.auth.pixiv_auth.requests.post")
    def test_oauth_login_network_error(
        self,
        mock_post: MagicMock,
        mock_prompt: MagicMock,
        mock_browser: MagicMock,
    ) -> None:
        """Test OAuth login with network error."""
        # Mock authorization code input
        mock_prompt.return_value = "test_code"

        # Mock network error
        mock_post.side_effect = requests.exceptions.ConnectionError("Network error")

        # Execute login and expect error
        oauth = PixivOAuth()
        with pytest.raises(OAuthError) as exc_info:
            oauth.login()

        # Verify error message mentions network
        assert "网络" in str(exc_info.value)

    @patch("gallery_dl_auto.auth.pixiv_auth.webbrowser.open")
    @patch("gallery_dl_auto.auth.pixiv_auth.Prompt.ask")
    @patch("gallery_dl_auto.auth.pixiv_auth.requests.post")
    def test_oauth_login_browser_open_failure(
        self,
        mock_post: MagicMock,
        mock_prompt: MagicMock,
        mock_browser: MagicMock,
    ) -> None:
        """Test OAuth login when browser fails to open."""
        # Mock browser open failure
        mock_browser.side_effect = Exception("Browser not found")

        # Mock authorization code input
        mock_prompt.return_value = "test_code"

        # Mock token exchange
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "access_token": "token",
            "refresh_token": "refresh",
            "expires_in": 3600,
        }
        mock_post.return_value = mock_response

        # Execute login - should still work with manual URL
        oauth = PixivOAuth()
        tokens = oauth.login()

        # Verify tokens were obtained
        assert tokens["access_token"] == "token"

    @patch("gallery_dl_auto.auth.pixiv_auth.Prompt.ask")
    def test_wait_for_callback_no_code_in_url(
        self, mock_prompt: MagicMock
    ) -> None:
        """Test callback waiting with URL missing code parameter."""
        # Mock URL without code parameter
        # When URL doesn't contain code, the entire URL is used as code
        # This test verifies that behavior
        mock_prompt.return_value = "https://example.com/callback?state=xyz"

        # Execute - should use URL as code directly
        oauth = PixivOAuth()
        code = oauth._wait_for_callback()

        # Verify URL was used as code
        assert code == "https://example.com/callback?state=xyz"

    @patch("gallery_dl_auto.auth.pixiv_auth.Prompt.ask")
    def test_wait_for_callback_empty_input(
        self, mock_prompt: MagicMock
    ) -> None:
        """Test callback waiting with empty input."""
        # Mock empty input
        mock_prompt.return_value = "   "

        # Execute and expect error
        oauth = PixivOAuth()
        with pytest.raises(OAuthError) as exc_info:
            oauth._wait_for_callback()

        assert "未提供授权码" in str(exc_info.value)

    @patch("gallery_dl_auto.auth.pixiv_auth.webbrowser.open")
    @patch("gallery_dl_auto.auth.pixiv_auth.Prompt.ask")
    @patch("gallery_dl_auto.auth.pixiv_auth.requests.post")
    def test_oauth_login_timeout_error(
        self,
        mock_post: MagicMock,
        mock_prompt: MagicMock,
        mock_browser: MagicMock,
    ) -> None:
        """Test OAuth login with request timeout."""
        mock_prompt.return_value = "code"
        mock_post.side_effect = requests.exceptions.Timeout("Timeout")

        oauth = PixivOAuth()
        with pytest.raises(OAuthError) as exc_info:
            oauth.login()

        assert "超时" in str(exc_info.value)

    @patch("gallery_dl_auto.auth.pixiv_auth.webbrowser.open")
    @patch("gallery_dl_auto.auth.pixiv_auth.Prompt.ask")
    @patch("gallery_dl_auto.auth.pixiv_auth.requests.post")
    def test_oauth_login_invalid_json_response(
        self,
        mock_post: MagicMock,
        mock_prompt: MagicMock,
        mock_browser: MagicMock,
    ) -> None:
        """Test OAuth login with invalid JSON response."""
        mock_prompt.return_value = "code"

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_post.return_value = mock_response

        oauth = PixivOAuth()
        with pytest.raises(OAuthError) as exc_info:
            oauth.login()

        assert "格式错误" in str(exc_info.value)

    @patch("gallery_dl_auto.auth.pixiv_auth.webbrowser.open")
    @patch("gallery_dl_auto.auth.pixiv_auth.Prompt.ask")
    @patch("gallery_dl_auto.auth.pixiv_auth.requests.post")
    def test_oauth_login_missing_token_field(
        self,
        mock_post: MagicMock,
        mock_prompt: MagicMock,
        mock_browser: MagicMock,
    ) -> None:
        """Test OAuth login with response missing required field."""
        mock_prompt.return_value = "code"

        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "access_token": "token"
            # Missing refresh_token
        }
        mock_post.return_value = mock_response

        oauth = PixivOAuth()
        with pytest.raises(OAuthError) as exc_info:
            oauth.login()

        assert "缺少必需字段" in str(exc_info.value)

    @patch("gallery_dl_auto.auth.pixiv_auth.requests.post")
    def test_refresh_tokens_invalid_json(self, mock_post: MagicMock) -> None:
        """Test token refresh with invalid JSON response."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_post.return_value = mock_response

        oauth = PixivOAuth()
        with pytest.raises(OAuthError) as exc_info:
            oauth.refresh_tokens("refresh_token")

        assert "格式错误" in str(exc_info.value)

    @patch("gallery_dl_auto.auth.pixiv_auth.requests.post")
    def test_refresh_tokens_success(self, mock_post: MagicMock) -> None:
        """Test successful token refresh."""
        # Mock refresh response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "access_token": "new_access_token",
            "refresh_token": "new_refresh_token",
            "expires_in": 3600,
        }
        mock_post.return_value = mock_response

        # Execute refresh
        oauth = PixivOAuth()
        tokens = oauth.refresh_tokens("old_refresh_token")

        # Verify
        assert tokens["access_token"] == "new_access_token"
        assert tokens["refresh_token"] == "new_refresh_token"

        # Verify request used refresh_token
        call_data = mock_post.call_args[1]["data"]
        assert call_data["refresh_token"] == "old_refresh_token"
        assert call_data["grant_type"] == "refresh_token"

    @patch("gallery_dl_auto.auth.pixiv_auth.requests.post")
    def test_refresh_tokens_failure(self, mock_post: MagicMock) -> None:
        """Test token refresh failure (expired token)."""
        # Mock 400 response
        mock_response = MagicMock()
        mock_response.status_code = 400
        mock_response.raise_for_status.side_effect = requests.exceptions.HTTPError(
            response=mock_response
        )
        mock_post.return_value = mock_response

        # Execute refresh and expect error
        oauth = PixivOAuth()
        with pytest.raises(OAuthError) as exc_info:
            oauth.refresh_tokens("expired_token")

        # Verify error message suggests re-login
        assert "重新登录" in str(exc_info.value)


@pytest.mark.integration
class TestPixivOAuthIntegration:
    """Integration tests for PixivOAuth (requires real network)."""

    @pytest.mark.skip(reason="Integration test - requires manual testing")
    def test_real_login_flow(self) -> None:
        """
        Test real OAuth login flow.

        This test requires manual interaction and is skipped by default.
        To run: pytest -m integration --run-integration
        """
        oauth = PixivOAuth()
        tokens = oauth.login()
        assert "access_token" in tokens
        assert "refresh_token" in tokens
