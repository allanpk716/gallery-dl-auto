"""CLI authentication commands test suite

Tests for login, logout, and status commands.
"""

import tempfile
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest
from click.testing import CliRunner

from gallery_dl_auto.auth.pixiv_auth import PixivOAuth
from gallery_dl_auto.auth.token_storage import TokenStorage
from gallery_dl_auto.cli.login_cmd import login
from gallery_dl_auto.cli.logout_cmd import logout
from gallery_dl_auto.cli.status_cmd import status


# Fixtures
@pytest.fixture
def temp_storage_path():
    """Create a temporary storage path for testing"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir) / "credentials.enc"


@pytest.fixture
def mock_storage(temp_storage_path):
    """Mock TokenStorage instance"""
    with patch(
        "gallery_dl_auto.cli.login_cmd.get_default_token_storage"
    ) as mock_get_storage:
        storage = TokenStorage(temp_storage_path)
        mock_get_storage.return_value = storage
        yield storage


@pytest.fixture
def runner():
    """Create CLI test runner"""
    return CliRunner()


# Login Command Tests
class TestLoginCommand:
    """Test cases for login command"""

    def test_login_no_existing_token(self, runner, mock_storage):
        """Test login when no token exists"""
        with patch(
            "gallery_dl_auto.cli.login_cmd.get_default_token_storage"
        ) as mock_get_storage, patch.object(PixivOAuth, "login") as mock_login:
            # Setup mocks
            mock_get_storage.return_value = mock_storage
            mock_login.return_value = {
                "refresh_token": "test_refresh_token",
                "access_token": "test_access_token",
            }

            # Run command
            result = runner.invoke(login)

            # Verify
            assert result.exit_code == 0
            assert "Login successful" in result.output
            mock_login.assert_called_once()

            # Verify token was saved
            token_data = mock_storage.load_token()
            assert token_data is not None
            assert token_data["refresh_token"] == "test_refresh_token"

    def test_login_existing_token_no_force(self, runner, mock_storage):
        """Test login with existing token and no --force flag"""
        with patch(
            "gallery_dl_auto.cli.login_cmd.get_default_token_storage"
        ) as mock_get_storage:
            # Setup: save existing token
            mock_storage.save_token("existing_refresh_token")
            mock_get_storage.return_value = mock_storage

            # Run command
            result = runner.invoke(login)

            # Verify
            assert result.exit_code == 0
            assert "Token already exists" in result.output

    def test_login_existing_token_with_force(self, runner, mock_storage):
        """Test login with existing token and --force flag"""
        with patch(
            "gallery_dl_auto.cli.login_cmd.get_default_token_storage"
        ) as mock_get_storage, patch.object(PixivOAuth, "login") as mock_login:
            # Setup: save existing token
            mock_storage.save_token("old_refresh_token")
            mock_get_storage.return_value = mock_storage
            mock_login.return_value = {
                "refresh_token": "new_refresh_token",
                "access_token": "new_access_token",
            }

            # Run command
            result = runner.invoke(login, ["--force"])

            # Verify
            assert result.exit_code == 0
            assert "Login successful" in result.output
            mock_login.assert_called_once()

            # Verify new token was saved
            token_data = mock_storage.load_token()
            assert token_data["refresh_token"] == "new_refresh_token"

    def test_login_oauth_failure(self, runner, mock_storage):
        """Test login when OAuth fails"""
        with patch(
            "gallery_dl_auto.cli.login_cmd.get_default_token_storage"
        ) as mock_get_storage, patch.object(PixivOAuth, "login") as mock_login:
            # Setup mock to raise exception
            mock_get_storage.return_value = mock_storage
            mock_login.side_effect = Exception("OAuth failed")

            # Run command
            result = runner.invoke(login, ["--force"])

            # Verify
            assert result.exit_code != 0
            assert "Login failed" in result.output


# Logout Command Tests
class TestLogoutCommand:
    """Test cases for logout command"""

    def test_logout_with_token(self, runner, mock_storage):
        """Test logout when token exists"""
        with patch(
            "gallery_dl_auto.cli.logout_cmd.get_default_token_storage"
        ) as mock_get_storage:
            # Setup: save token
            mock_storage.save_token("test_refresh_token")
            mock_get_storage.return_value = mock_storage

            # Run command with confirmation
            result = runner.invoke(logout, input="y\n")

            # Verify
            assert result.exit_code == 0
            assert "Logged out successfully" in result.output

            # Verify token was deleted
            assert not mock_storage.storage_path.exists()

    def test_logout_no_token(self, runner, mock_storage):
        """Test logout when no token exists"""
        with patch(
            "gallery_dl_auto.cli.logout_cmd.get_default_token_storage"
        ) as mock_get_storage:
            mock_get_storage.return_value = mock_storage

            # Run command
            result = runner.invoke(logout)

            # Verify
            assert result.exit_code == 0
            assert "No token found" in result.output

    def test_logout_cancelled(self, runner, mock_storage):
        """Test logout when user cancels"""
        with patch(
            "gallery_dl_auto.cli.logout_cmd.get_default_token_storage"
        ) as mock_get_storage:
            # Setup: save token
            mock_storage.save_token("test_refresh_token")
            mock_get_storage.return_value = mock_storage

            # Run command with cancellation
            result = runner.invoke(logout, input="n\n")

            # Verify
            assert result.exit_code == 0
            assert "Logout cancelled" in result.output

            # Verify token still exists
            assert mock_storage.storage_path.exists()


# Status Command Tests
class TestStatusCommand:
    """Test cases for status command"""

    def test_status_no_token(self, runner, mock_storage):
        """Test status when no token exists"""
        with patch(
            "gallery_dl_auto.cli.status_cmd.get_default_token_storage"
        ) as mock_get_storage:
            mock_get_storage.return_value = mock_storage

            # Run command
            result = runner.invoke(status)

            # Verify
            assert result.exit_code == 0
            assert "No token found" in result.output

    def test_status_valid_token(self, runner, mock_storage):
        """Test status with valid token"""
        with patch(
            "gallery_dl_auto.cli.status_cmd.get_default_token_storage"
        ) as mock_get_storage, patch.object(
            PixivOAuth, "validate_refresh_token"
        ) as mock_validate:
            # Setup
            mock_storage.save_token("test_refresh_token")
            mock_get_storage.return_value = mock_storage
            mock_validate.return_value = {
                "valid": True,
                "access_token": "test_access_token",
                "refresh_token": "new_refresh_token",
                "expires_in": 3600,
                "error": None,
            }

            # Run command
            result = runner.invoke(status)

            # Verify
            assert result.exit_code == 0
            assert "Valid" in result.output
            assert "Token refreshed and saved" in result.output
            mock_validate.assert_called_once_with("test_refresh_token")

    def test_status_invalid_token(self, runner, mock_storage):
        """Test status with invalid token"""
        with patch(
            "gallery_dl_auto.cli.status_cmd.get_default_token_storage"
        ) as mock_get_storage, patch.object(
            PixivOAuth, "validate_refresh_token"
        ) as mock_validate:
            # Setup
            mock_storage.save_token("invalid_refresh_token")
            mock_get_storage.return_value = mock_storage
            mock_validate.return_value = {
                "valid": False,
                "access_token": None,
                "refresh_token": None,
                "expires_in": None,
                "error": "Invalid token",
            }

            # Run command
            result = runner.invoke(status)

            # Verify
            assert result.exit_code == 0
            assert "Invalid" in result.output
            assert "Invalid token" in result.output

    def test_status_verbose(self, runner, mock_storage):
        """Test status with --verbose flag"""
        with patch(
            "gallery_dl_auto.cli.status_cmd.get_default_token_storage"
        ) as mock_get_storage, patch.object(
            PixivOAuth, "validate_refresh_token"
        ) as mock_validate:
            # Setup
            mock_storage.save_token("test_refresh_token_1234567890")
            mock_get_storage.return_value = mock_storage
            mock_validate.return_value = {
                "valid": True,
                "access_token": "test_access_token",
                "refresh_token": "new_refresh_token",
                "expires_in": 3600,
                "error": None,
            }

            # Run command
            result = runner.invoke(status, ["--verbose"])

            # Verify
            assert result.exit_code == 0
            assert "Valid" in result.output
            assert "Refresh Token" in result.output
            assert "Expires" in result.output

    def test_status_decryption_failure(self, runner, mock_storage):
        """Test status when token cannot be decrypted"""
        with patch(
            "gallery_dl_auto.cli.status_cmd.get_default_token_storage"
        ) as mock_get_storage:
            # Setup: create corrupted token file
            mock_storage.storage_path.parent.mkdir(
                parents=True, exist_ok=True
            )
            mock_storage.storage_path.write_bytes(b"invalid_encrypted_data")
            mock_get_storage.return_value = mock_storage

            # Run command
            result = runner.invoke(status)

            # Verify
            assert result.exit_code == 0
            assert "cannot be decrypted" in result.output


# Token Validation Tests
class TestTokenValidation:
    """Test cases for token validation"""

    def test_validate_valid_token(self):
        """Test validate_refresh_token with valid token"""
        with patch("requests.post") as mock_post:
            # Setup mock response
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "access_token": "test_access_token",
                "refresh_token": "test_refresh_token",
                "expires_in": 3600,
            }
            mock_post.return_value = mock_response

            # Execute
            result = PixivOAuth.validate_refresh_token("valid_token")

            # Verify
            assert result["valid"] is True
            assert result["access_token"] == "test_access_token"
            assert result["refresh_token"] == "test_refresh_token"
            assert result["expires_in"] == 3600
            assert result["error"] is None

    def test_validate_invalid_token(self):
        """Test validate_refresh_token with invalid token"""
        with patch("requests.post") as mock_post:
            # Setup mock response
            mock_response = Mock()
            mock_response.status_code = 400
            mock_response.json.return_value = {
                "error": "invalid_grant",
                "error_description": "Invalid token",
            }
            mock_post.return_value = mock_response

            # Execute
            result = PixivOAuth.validate_refresh_token("invalid_token")

            # Verify
            assert result["valid"] is False
            assert result["access_token"] is None
            assert result["error"] == "invalid_grant"

    def test_validate_network_error(self):
        """Test validate_refresh_token with network error"""
        with patch("requests.post") as mock_post:
            # Setup mock to raise exception
            mock_post.side_effect = Exception("Network error")

            # Execute
            result = PixivOAuth.validate_refresh_token("test_token")

            # Verify
            assert result["valid"] is False
            assert result["error"] == "Network error"
