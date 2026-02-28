"""
Exit code validation tests for authentication-related errors

Tests that CLI commands return correct exit codes for authentication scenarios.
"""
import pytest
from click.testing import CliRunner
from unittest.mock import Mock, patch
import json

from gallery_dl_auto.cli.main import cli
from gallery_dl_auto.models.error_response import StructuredError, BatchDownloadResult
from gallery_dl_auto.utils.error_codes import ErrorCode


class TestAuthExitCodes:
    """Test authentication-related exit codes"""

    @pytest.fixture
    def runner(self):
        """Create CLI runner with UTF-8 encoding for Windows"""
        runner = CliRunner()
        return runner

    def test_no_token_exit_code(self, runner, monkeypatch):
        """Verify exit code 1 when no token is found"""
        # Mock token storage to return None (no token)
        from gallery_dl_auto.auth import token_storage

        mock_storage = Mock()
        mock_storage.load_token.return_value = None

        monkeypatch.setattr(
            "gallery_dl_auto.cli.download_cmd.get_default_token_storage",
            lambda: mock_storage
        )

        # Run download command
        result = runner.invoke(cli, ["download", "--type", "daily"])

        # Verify exit code
        assert result.exit_code == 1, f"Expected exit code 1, got {result.exit_code}"

        # Verify error code in output
        assert "AUTH_TOKEN_NOT_FOUND" in result.output, \
            f"Expected AUTH_TOKEN_NOT_FOUND in output, got: {result.output}"

    def test_expired_token_exit_code(self, runner, monkeypatch):
        """Verify exit code 1 when token is expired"""
        # Mock token storage to return expired token
        from gallery_dl_auto.auth import token_storage
        from gallery_dl_auto.api.pixiv_client import PixivAPIError

        mock_storage = Mock()
        mock_storage.load_token.return_value = {"refresh_token": "expired_token"}

        monkeypatch.setattr(
            "gallery_dl_auto.cli.download_cmd.get_default_token_storage",
            lambda: mock_storage
        )

        # Mock PixivClient to raise expired token error
        def mock_client_init(*args, **kwargs):
            raise PixivAPIError("Token expired")

        monkeypatch.setattr(
            "gallery_dl_auto.cli.download_cmd.PixivClient",
            mock_client_init
        )

        # Run download command
        result = runner.invoke(cli, ["download", "--type", "daily"])

        # Verify exit code
        assert result.exit_code == 1, f"Expected exit code 1, got {result.exit_code}"

        # Verify error code in output
        assert "AUTH_TOKEN_INVALID" in result.output or "AUTH_TOKEN_EXPIRED" in result.output, \
            f"Expected AUTH_TOKEN_INVALID or AUTH_TOKEN_EXPIRED in output, got: {result.output}"

    def test_invalid_token_exit_code(self, runner, monkeypatch):
        """Verify exit code 1 when token is invalid"""
        from gallery_dl_auto.auth import token_storage
        from gallery_dl_auto.api.pixiv_client import PixivAPIError

        # Mock token storage to return invalid token
        mock_storage = Mock()
        mock_storage.load_token.return_value = {"refresh_token": "invalid_token"}

        monkeypatch.setattr(
            "gallery_dl_auto.cli.download_cmd.get_default_token_storage",
            lambda: mock_storage
        )

        # Mock PixivClient to raise invalid token error
        def mock_client_init(*args, **kwargs):
            raise PixivAPIError("Invalid token format")

        monkeypatch.setattr(
            "gallery_dl_auto.cli.download_cmd.PixivClient",
            mock_client_init
        )

        # Run download command
        result = runner.invoke(cli, ["download", "--type", "daily"])

        # Verify exit code
        assert result.exit_code == 1, f"Expected exit code 1, got {result.exit_code}"

        # Verify error code in output
        assert "AUTH_TOKEN_INVALID" in result.output, \
            f"Expected AUTH_TOKEN_INVALID in output, got: {result.output}"

    def test_refresh_failed_exit_code(self, runner, monkeypatch):
        """Verify exit code 1 when token refresh fails"""
        from gallery_dl_auto.auth import token_storage
        from gallery_dl_auto.auth.oauth import OAuthError

        # Mock token storage to return token
        mock_storage = Mock()
        mock_storage.load_token.return_value = {"refresh_token": "valid_token"}

        monkeypatch.setattr(
            "gallery_dl_auto.cli.download_cmd.get_default_token_storage",
            lambda: mock_storage
        )

        # Mock PixivClient to raise refresh failed error during initialization
        def mock_client_init(*args, **kwargs):
            raise OAuthError("Refresh failed")

        monkeypatch.setattr(
            "gallery_dl_auto.cli.download_cmd.PixivClient",
            mock_client_init
        )

        # Run download command
        result = runner.invoke(cli, ["download", "--type", "daily"])

        # Verify exit code
        assert result.exit_code == 1, f"Expected exit code 1, got {result.exit_code}"

        # Verify error code in output (could be AUTH_TOKEN_INVALID or AUTH_REFRESH_FAILED)
        error_found = (
            "AUTH_TOKEN_INVALID" in result.output or
            "AUTH_REFRESH_FAILED" in result.output
        )
        assert error_found, \
            f"Expected AUTH error code in output, got: {result.output}"


class TestDownloadExitCodes:
    """Test download-related exit codes"""

    @pytest.fixture
    def runner(self):
        """Create CLI runner with UTF-8 encoding for Windows"""
        runner = CliRunner()
        return runner

    def test_success_exit_code(self, runner, monkeypatch):
        """Verify exit code 0 when all downloads succeed"""
        from gallery_dl_auto.auth import token_storage
        from gallery_dl_auto.api.pixiv_client import PixivClient
        from gallery_dl_auto.download.ranking_downloader import RankingDownloader

        # Mock token storage
        mock_storage = Mock()
        mock_storage.load_token.return_value = {"refresh_token": "valid_token"}
        monkeypatch.setattr(
            "gallery_dl_auto.cli.download_cmd.get_default_token_storage",
            lambda: mock_storage
        )

        # Mock PixivClient
        mock_client = Mock(spec=PixivClient)
        monkeypatch.setattr(
            "gallery_dl_auto.cli.download_cmd.PixivClient",
            lambda refresh_token: mock_client
        )

        # Mock download result: all success
        result = BatchDownloadResult(
            success=True,
            total=10,
            downloaded=10,
            failed=0,
            skipped=0,
            success_list=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
            failed_errors=[],
            output_dir="/tmp/downloads"
        )
        monkeypatch.setattr(
            RankingDownloader,
            "download_ranking",
            lambda self, mode, date, path_template, tracker: result
        )

        # Run download command
        result = runner.invoke(cli, ["download", "--type", "daily"])

        # Verify exit code
        assert result.exit_code == 0, f"Expected exit code 0, got {result.exit_code}"

    def test_partial_success_exit_code(self, runner, monkeypatch):
        """Verify exit code 1 when partial downloads succeed"""
        from gallery_dl_auto.auth import token_storage
        from gallery_dl_auto.api.pixiv_client import PixivClient
        from gallery_dl_auto.download.ranking_downloader import RankingDownloader

        # Mock token storage
        mock_storage = Mock()
        mock_storage.load_token.return_value = {"refresh_token": "valid_token"}
        monkeypatch.setattr(
            "gallery_dl_auto.cli.download_cmd.get_default_token_storage",
            lambda: mock_storage
        )

        # Mock PixivClient
        mock_client = Mock(spec=PixivClient)
        monkeypatch.setattr(
            "gallery_dl_auto.cli.download_cmd.PixivClient",
            lambda refresh_token: mock_client
        )

        # Mock download result: partial success
        result = BatchDownloadResult(
            success=False,
            total=10,
            downloaded=7,
            failed=3,
            skipped=0,
            success_list=[1, 2, 3, 4, 5, 6, 7],
            failed_errors=[
                StructuredError(
                    error_code=ErrorCode.DOWNLOAD_FAILED,
                    error_type="DownloadError",
                    message="Failed to download",
                    suggestion="Check network connection",
                    severity="error",
                    illust_id=8
                )
            ],
            output_dir="/tmp/downloads"
        )
        monkeypatch.setattr(
            RankingDownloader,
            "download_ranking",
            lambda self, mode, date, path_template, tracker: result
        )

        # Run download command
        result = runner.invoke(cli, ["download", "--type", "daily"])

        # Verify exit code
        assert result.exit_code == 1, f"Expected exit code 1, got {result.exit_code}"

    def test_complete_failure_exit_code(self, runner, monkeypatch):
        """Verify exit code 2 when all downloads fail"""
        from gallery_dl_auto.auth import token_storage
        from gallery_dl_auto.api.pixiv_client import PixivClient
        from gallery_dl_auto.download.ranking_downloader import RankingDownloader

        # Mock token storage
        mock_storage = Mock()
        mock_storage.load_token.return_value = {"refresh_token": "valid_token"}
        monkeypatch.setattr(
            "gallery_dl_auto.cli.download_cmd.get_default_token_storage",
            lambda: mock_storage
        )

        # Mock PixivClient
        mock_client = Mock(spec=PixivClient)
        monkeypatch.setattr(
            "gallery_dl_auto.cli.download_cmd.PixivClient",
            lambda refresh_token: mock_client
        )

        # Mock download result: complete failure
        result = BatchDownloadResult(
            success=False,
            total=10,
            downloaded=0,
            failed=10,
            skipped=0,
            success_list=[],
            failed_errors=[
                StructuredError(
                    error_code=ErrorCode.DOWNLOAD_NETWORK_ERROR,
                    error_type="NetworkError",
                    message="Network error",
                    suggestion="Check network connection",
                    severity="error",
                    illust_id=1
                )
            ],
            output_dir="/tmp/downloads"
        )
        monkeypatch.setattr(
            RankingDownloader,
            "download_ranking",
            lambda self, mode, date, path_template, tracker: result
        )

        # Run download command
        result = runner.invoke(cli, ["download", "--type", "daily"])

        # Verify exit code
        assert result.exit_code == 2, f"Expected exit code 2, got {result.exit_code}"


class TestArgumentExitCodes:
    """Test argument-related exit codes"""

    @pytest.fixture
    def runner(self):
        """Create CLI runner with UTF-8 encoding for Windows"""
        runner = CliRunner()
        return runner

    def test_invalid_ranking_type(self, runner):
        """Verify exit code 2 for invalid ranking type"""
        result = runner.invoke(cli, ["download", "--type", "invalid_type"])

        # Verify exit code (Click returns 2 for BadParameter)
        assert result.exit_code == 2, f"Expected exit code 2, got {result.exit_code}"

        # Verify error message contains "Invalid" or "Error"
        assert "Invalid" in result.output or "Error" in result.output, \
            f"Expected error message in output, got: {result.output}"

    def test_invalid_date_format(self, runner):
        """Verify exit code 2 for invalid date format"""
        result = runner.invoke(cli, ["download", "--type", "daily", "--date", "invalid-date"])

        # Verify exit code (Click returns 2 for BadParameter)
        assert result.exit_code == 2, f"Expected exit code 2, got {result.exit_code}"

        # Verify error message contains "Invalid" or "Error"
        assert "Invalid" in result.output or "Error" in result.output, \
            f"Expected error message in output, got: {result.output}"

    def test_missing_required_argument(self, runner):
        """Verify exit code 2 when required argument is missing"""
        # Missing --type argument
        result = runner.invoke(cli, ["download"])

        # Verify exit code (Click returns 2 for missing required option)
        assert result.exit_code == 2, f"Expected exit code 2, got {result.exit_code}"

        # Verify error message mentions missing option
        assert "Missing option" in result.output or "--type" in result.output, \
            f"Expected missing option message in output, got: {result.output}"
