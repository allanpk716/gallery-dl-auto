"""Logout command tests

Tests the 'pixiv-downloader logout' command functionality.
"""

from pathlib import Path
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from gallery_dl_auto.auth.token_storage import TokenStorage
from gallery_dl_auto.cli.main import cli
from tests.fixtures.test_data import TestData
from tests.utils.test_helpers import assert_cli_success, run_cli_command


class TestLogoutCommand:
    """logout 命令测试套件"""

    def test_logout_success_with_confirmation(self, runner: CliRunner, temp_token_file: Path):
        """测试：登出成功（用户确认删除）"""
        with patch('gallery_dl_auto.cli.logout_cmd.get_default_token_storage') as mock_storage_factory:
            storage = TokenStorage(temp_token_file)
            mock_storage_factory.return_value = storage

            # 执行命令并自动确认
            result = run_cli_command(runner, ['logout'], input='y\n')

            # 验证命令执行成功
            assert result.exit_code == 0

            # 验证 token 文件已删除
            assert not temp_token_file.exists()

            # 验证成功消息
            assert "Logged out successfully" in result.output

    def test_logout_cancelled_by_user(self, runner: CliRunner, temp_token_file: Path):
        """测试：用户取消登出"""
        with patch('gallery_dl_auto.cli.logout_cmd.get_default_token_storage') as mock_storage_factory:
            storage = TokenStorage(temp_token_file)
            mock_storage_factory.return_value = storage

            # 执行命令并取消
            result = run_cli_command(runner, ['logout'], input='n\n')

            # 验证命令执行成功（退出码 0）
            assert result.exit_code == 0

            # 验证 token 文件仍然存在
            assert temp_token_file.exists()

            # 验证取消消息
            assert "Logout cancelled" in result.output

    def test_logout_no_token_exists(self, runner: CliRunner):
        """测试：无 token 时登出"""
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            non_existent_token = Path(tmpdir) / ".token"

            with patch('gallery_dl_auto.cli.logout_cmd.get_default_token_storage') as mock_storage_factory:
                storage = TokenStorage(non_existent_token)
                mock_storage_factory.return_value = storage

                # 执行命令
                result = run_cli_command(runner, ['logout'])

                # 验证命令执行成功（退出码 0）
                assert result.exit_code == 0

                # 验证提示消息
                assert "No token found" in result.output
                assert "Already logged out" in result.output

    def test_logout_delete_failure(self, runner: CliRunner, temp_token_file: Path):
        """测试：删除 token 文件失败"""
        with patch('gallery_dl_auto.cli.logout_cmd.get_default_token_storage') as mock_storage_factory:
            storage = TokenStorage(temp_token_file)
            mock_storage_factory.return_value = storage

            # Mock delete_token 方法抛出异常
            with patch.object(storage, 'delete_token', side_effect=PermissionError("Permission denied")):
                # 执行命令并确认
                result = run_cli_command(runner, ['logout'], input='y\n')

                # 验证命令失败（退出码非 0）
                assert result.exit_code != 0

                # 验证错误消息
                assert "Logout failed" in result.output

    def test_logout_rich_output_format(self, runner: CliRunner, temp_token_file: Path):
        """测试：登出输出的 Rich 格式（默认模式）"""
        with patch('gallery_dl_auto.cli.logout_cmd.get_default_token_storage') as mock_storage_factory:
            storage = TokenStorage(temp_token_file)
            mock_storage_factory.return_value = storage

            # 执行命令并确认
            result = run_cli_command(runner, ['logout'], input='y\n')

            # 验证命令执行成功
            assert result.exit_code == 0

            # 验证 Rich 格式输出（包含颜色标签）
            # 注意：在测试环境中，Rich 可能不渲染颜色，但应该包含文本内容
            assert "Logged out successfully" in result.output
            assert "Token file has been removed" in result.output
