"""CLI refresh command test suite

Tests for refresh command.
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from gallery_dl_auto.auth.pixiv_auth import PixivOAuth
from gallery_dl_auto.auth.token_storage import TokenStorage
from gallery_dl_auto.cli.refresh_cmd import refresh


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
        "gallery_dl_auto.cli.refresh_cmd.get_default_token_storage"
    ) as mock_get_storage:
        storage = TokenStorage(temp_storage_path)
        mock_get_storage.return_value = storage
        yield storage


@pytest.fixture
def runner():
    """Create CLI test runner"""
    return CliRunner()


# Refresh Command Tests
class TestRefreshCommand:
    """Test cases for refresh command"""

    def test_refresh_success(self, runner, mock_storage):
        """Test successful token refresh"""
        # Setup: save existing token
        mock_storage.save_token("test_refresh_token_12345678901234567890")

        with patch(
            "gallery_dl_auto.cli.refresh_cmd.get_default_token_storage"
        ) as mock_get_storage, patch.object(
            PixivOAuth, "validate_refresh_token"
        ) as mock_validate:
            mock_get_storage.return_value = mock_storage
            mock_validate.return_value = {
                "valid": True,
                "refresh_token": "new_refresh_token_abcdefghij1234567890",
                "access_token": "new_access_token",
                "expires_in": 3600,
            }

            # Run command
            result = runner.invoke(refresh)

            # Verify exit code
            assert result.exit_code == 0

            # Parse JSON output
            output = json.loads(result.output)

            # Verify JSON structure
            assert output["status"] == "success"
            assert "expires_at" in output
            assert "token" in output

            # Verify token is masked
            assert "..." in output["token"]
            assert output["token"] != "new_refresh_token_abcdefghij1234567890"

            # Verify token was saved
            token_data = mock_storage.load_token()
            assert token_data is not None
            assert token_data["refresh_token"] == "new_refresh_token_abcdefghij1234567890"

            # Verify validate_refresh_token was called
            mock_validate.assert_called_once_with("test_refresh_token_12345678901234567890")

    def test_refresh_no_token(self, runner, mock_storage):
        """Test refresh when no token exists"""
        with patch(
            "gallery_dl_auto.cli.refresh_cmd.get_default_token_storage"
        ) as mock_get_storage:
            mock_get_storage.return_value = mock_storage

            # Run command (no token saved)
            result = runner.invoke(refresh)

            # Verify exit code
            assert result.exit_code == 1

            # Parse JSON output
            output = json.loads(result.output)

            # Verify JSON structure
            assert output["status"] == "failed"
            assert "error" in output
            assert "login" in output["error"].lower()

    def test_refresh_failure(self, runner, mock_storage):
        """Test refresh when token validation fails"""
        # Setup: save existing token
        mock_storage.save_token("invalid_refresh_token_1234567890123456")

        with patch(
            "gallery_dl_auto.cli.refresh_cmd.get_default_token_storage"
        ) as mock_get_storage, patch.object(
            PixivOAuth, "validate_refresh_token"
        ) as mock_validate:
            mock_get_storage.return_value = mock_storage
            mock_validate.return_value = {
                "valid": False,
                "error": "Token expired or invalid",
            }

            # Run command
            result = runner.invoke(refresh)

            # Verify exit code
            assert result.exit_code == 1

            # Parse JSON output
            output = json.loads(result.output)

            # Verify JSON structure
            assert output["status"] == "failed"
            assert "error" in output
            assert "Token expired or invalid" in output["error"]
            assert "login" in output["error"].lower()

            # Verify token was NOT updated
            token_data = mock_storage.load_token()
            assert token_data is not None
            assert token_data["refresh_token"] == "invalid_refresh_token_1234567890123456"
