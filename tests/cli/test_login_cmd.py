"""Login command tests

Tests the 'pixiv-downloader login' command functionality.
"""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from gallery_dl_auto.cli.main import cli
from tests.fixtures.test_data import TestData
from tests.utils.test_helpers import assert_cli_success, run_cli_command


class TestLoginCommand:
    """login 命令测试套件"""

    def test_login_with_existing_token_without_force(self, runner: CliRunner, temp_token_file: Path):
        """测试：已有 token 时，不使用 --force 应该提示并退出"""
        # 模拟 storage 使用 temp_token_file
        with patch('gallery_dl_auto.cli.login_cmd.get_default_token_storage') as mock_storage_factory:
            from gallery_dl_auto.auth.token_storage import TokenStorage
            storage = TokenStorage(temp_token_file)
            mock_storage_factory.return_value = storage

            result = run_cli_command(runner, ['login'])

            # 验证命令执行成功（退出码 0）
            assert result.exit_code == 0

            # 验证提示信息
            assert "Token already exists" in result.output
            assert "--force" in result.output

    def test_login_force_relogin_success(self, runner: CliRunner, temp_token_file: Path):
        """测试：使用 --force 强制重新登录（需要 Mock PixivOAuth.login）"""
        # Mock PixivOAuth.login 返回成功
        mock_tokens = {
            "refresh_token": TestData.VALID_REFRESH_TOKEN,
            "access_token": TestData.ALT_REFRESH_TOKEN,
            "user": {
                "id": 12345678,
                "name": "TestUser",
                "account": "testuser"
            }
        }

        with patch('gallery_dl_auto.cli.login_cmd.PixivOAuth') as mock_oauth_class, \
             patch('gallery_dl_auto.cli.login_cmd.get_default_token_storage') as mock_storage_factory:

            # 配置 Mock
            mock_oauth_instance = MagicMock()
            mock_oauth_instance.login.return_value = mock_tokens
            mock_oauth_class.return_value = mock_oauth_instance

            from gallery_dl_auto.auth.token_storage import TokenStorage
            storage = TokenStorage(temp_token_file)
            mock_storage_factory.return_value = storage

            # 执行命令
            result = run_cli_command(runner, ['login', '--force'])

            # 验证命令执行成功
            assert result.exit_code == 0

            # 验证调用 login 方法
            mock_oauth_instance.login.assert_called_once()

            # 验证成功消息
            assert "Login successful" in result.output

    def test_login_force_relogin_cancelled(self, runner: CliRunner):
        """测试：用户取消登录流程"""
        with patch('gallery_dl_auto.cli.login_cmd.PixivOAuth') as mock_oauth_class, \
             patch('gallery_dl_auto.cli.login_cmd.get_default_token_storage') as mock_storage_factory:

            # 配置 Mock - 用户取消登录
            mock_oauth_instance = MagicMock()
            mock_oauth_instance.login.side_effect = KeyboardInterrupt("User cancelled")
            mock_oauth_class.return_value = mock_oauth_instance

            from gallery_dl_auto.auth.token_storage import TokenStorage
            import tempfile
            with tempfile.TemporaryDirectory() as tmpdir:
                storage = TokenStorage(Path(tmpdir) / ".token")
                mock_storage_factory.return_value = storage

                # 执行命令
                result = run_cli_command(runner, ['login', '--force'])

                # 验证命令被中断（退出码非 0）
                assert result.exit_code != 0

    def test_login_force_relogin_network_error(self, runner: CliRunner):
        """测试：网络错误导致登录失败"""
        with patch('gallery_dl_auto.cli.login_cmd.PixivOAuth') as mock_oauth_class, \
             patch('gallery_dl_auto.cli.login_cmd.get_default_token_storage') as mock_storage_factory:

            # 配置 Mock - 网络错误
            mock_oauth_instance = MagicMock()
            mock_oauth_instance.login.side_effect = ConnectionError("Network error")
            mock_oauth_class.return_value = mock_oauth_instance

            from gallery_dl_auto.auth.token_storage import TokenStorage
            import tempfile
            with tempfile.TemporaryDirectory() as tmpdir:
                storage = TokenStorage(Path(tmpdir) / ".token")
                mock_storage_factory.return_value = storage

                # 执行命令
                result = run_cli_command(runner, ['login', '--force'])

                # 验证命令失败（退出码非 0）
                assert result.exit_code != 0

                # 验证错误消息
                assert "Login failed" in result.output

    @pytest.mark.skip(reason="首次登录需要真实浏览器环境，无法在自动化测试中完成")
    def test_login_first_time_real_browser(self, runner: CliRunner):
        """测试：首次登录（需要真实浏览器环境，跳过）

        此测试标记为 skip，因为：
        - 需要打开浏览器进行用户交互
        - 无法在自动化测试环境中模拟
        - 应该由手动测试或集成测试覆盖
        """
        pass
