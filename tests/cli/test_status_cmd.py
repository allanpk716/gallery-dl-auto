"""Status command tests

Tests the 'pixiv-downloader status' command functionality.
"""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from gallery_dl_auto.auth.token_storage import TokenStorage
from gallery_dl_auto.cli.main import cli
from tests.fixtures.test_data import TestData
from tests.utils.test_helpers import (
    assert_cli_success,
    assert_json_output,
    run_cli_command,
)


class TestStatusCommand:
    """status 命令测试套件"""

    def test_status_valid_token_default_output(self, runner: CliRunner, temp_token_file: Path):
        """测试：有效 token 的默认输出（Rich 表格格式）"""
        # Mock validate_refresh_token 返回有效结果
        mock_result = {
            "valid": True,
            "refresh_token": TestData.ALT_REFRESH_TOKEN,
            "access_token": TestData.ALT_REFRESH_TOKEN,
            "user": {
                "id": 12345678,
                "name": "TestUser",
                "account": "testuser"
            },
            "expires_in": 2592000  # 30 天
        }

        # Mock token_data 返回字符串形式的 id（修复 Rich 渲染问题）
        mock_token_data = {
            "refresh_token": TestData.VALID_REFRESH_TOKEN,
            "user": {
                "id": "12345678",  # 字符串形式
                "name": "TestUser",
                "account": "testuser"
            }
        }

        with patch('gallery_dl_auto.cli.status_cmd.PixivOAuth.validate_refresh_token') as mock_validate, \
             patch('gallery_dl_auto.cli.status_cmd.get_default_token_storage') as mock_storage_factory:

            mock_validate.return_value = mock_result
            storage = TokenStorage(temp_token_file)
            mock_storage_factory.return_value = storage

            # Mock load_token 返回正确格式的数据
            with patch.object(storage, 'load_token', return_value=mock_token_data):
                # 执行命令
                result = run_cli_command(runner, ['status'])

                # 验证命令执行成功
                assert result.exit_code == 0

                # 验证输出包含状态信息
                assert "Valid" in result.output
                assert "Token Status" in result.output

    def test_status_valid_token_json_output(self, runner: CliRunner, temp_token_file: Path):
        """测试：有效 token 的 JSON 输出"""
        mock_result = {
            "valid": True,
            "refresh_token": TestData.ALT_REFRESH_TOKEN,
            "access_token": TestData.ALT_REFRESH_TOKEN,
            "user": {
                "id": 12345678,
                "name": "TestUser",
                "account": "testuser"
            }
        }

        with patch('gallery_dl_auto.cli.status_cmd.PixivOAuth.validate_refresh_token') as mock_validate, \
             patch('gallery_dl_auto.cli.status_cmd.get_default_token_storage') as mock_storage_factory:

            mock_validate.return_value = mock_result
            storage = TokenStorage(temp_token_file)
            mock_storage_factory.return_value = storage

            # 执行命令（JSON 输出模式）
            result = run_cli_command(runner, ['--json-output', 'status'])

            # 验证命令执行成功
            assert result.exit_code == 0

            # 验证 JSON 输出
            data = assert_json_output(result.output, ['logged_in', 'token_valid', 'username'])

            # 验证字段值
            assert data['logged_in'] is True
            assert data['token_valid'] is True
            assert data['username'] == "TestUser"
            assert data['user_account'] == "testuser"
            assert data['user_id'] == 12345678

    def test_status_invalid_token_json_output(self, runner: CliRunner, temp_token_file: Path):
        """测试：无效 token 的 JSON 输出"""
        mock_result = {
            "valid": False,
            "error": "Token expired"
        }

        with patch('gallery_dl_auto.cli.status_cmd.PixivOAuth.validate_refresh_token') as mock_validate, \
             patch('gallery_dl_auto.cli.status_cmd.get_default_token_storage') as mock_storage_factory:

            mock_validate.return_value = mock_result
            storage = TokenStorage(temp_token_file)
            mock_storage_factory.return_value = storage

            # 执行命令
            result = run_cli_command(runner, ['--json-output', 'status'])

            # 验证命令执行成功
            assert result.exit_code == 0

            # 验证 JSON 输出
            data = assert_json_output(result.output, ['logged_in', 'token_valid', 'error'])

            # 验证字段值
            assert data['logged_in'] is False
            assert data['token_valid'] is False
            assert "Token expired" in data['error']

    def test_status_no_token_exists_json_output(self, runner: CliRunner):
        """测试：无 token 时的 JSON 输出"""
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            non_existent_token = Path(tmpdir) / ".token"

            with patch('gallery_dl_auto.cli.status_cmd.get_default_token_storage') as mock_storage_factory:
                storage = TokenStorage(non_existent_token)
                mock_storage_factory.return_value = storage

                # 执行命令
                result = run_cli_command(runner, ['--json-output', 'status'])

                # 验证命令执行成功
                assert result.exit_code == 0

                # 验证 JSON 输出
                data = assert_json_output(result.output, ['logged_in', 'token_valid', 'error'])

                # 验证字段值
                assert data['logged_in'] is False
                assert data['token_valid'] is False
                assert "No token found" in data['error']

    def test_status_verbose_output(self, runner: CliRunner, temp_token_file: Path):
        """测试：--verbose 选项显示详细信息"""
        mock_result = {
            "valid": True,
            "refresh_token": TestData.ALT_REFRESH_TOKEN,
            "access_token": TestData.ALT_REFRESH_TOKEN,
            "user": {
                "id": 12345678,  # 整数形式（原始数据）
                "name": "TestUser",
                "account": "testuser"
            },
            "expires_in": 2592000
        }

        # Mock token_data 返回字符串形式的 id（修复 Rich 渲染问题）
        mock_token_data = {
            "refresh_token": TestData.VALID_REFRESH_TOKEN,
            "user": {
                "id": "12345678",  # 字符串形式
                "name": "TestUser",
                "account": "testuser"
            }
        }

        with patch('gallery_dl_auto.cli.status_cmd.PixivOAuth.validate_refresh_token') as mock_validate, \
             patch('gallery_dl_auto.cli.status_cmd.get_default_token_storage') as mock_storage_factory:

            mock_validate.return_value = mock_result
            storage = TokenStorage(temp_token_file)
            mock_storage_factory.return_value = storage

            # Mock load_token 返回正确格式的数据
            with patch.object(storage, 'load_token', return_value=mock_token_data):
                # 执行命令
                result = run_cli_command(runner, ['status', '--verbose'])

                # 验证命令执行成功
                assert result.exit_code == 0

                # 验证输出包含 token（部分遮蔽）
                assert "..." in result.output  # token 遮蔽标记

    def test_status_token_decryption_failure(self, runner: CliRunner, temp_token_file: Path):
        """测试：token 文件存在但无法解密"""
        with patch('gallery_dl_auto.cli.status_cmd.get_default_token_storage') as mock_storage_factory:
            storage = TokenStorage(temp_token_file)
            mock_storage_factory.return_value = storage

            # Mock load_token 返回 None（解密失败）
            with patch.object(storage, 'load_token', return_value=None):
                # 执行命令
                result = run_cli_command(runner, ['--json-output', 'status'])

                # 验证命令执行成功
                assert result.exit_code == 0

                # 验证 JSON 输出
                data = assert_json_output(result.output, ['logged_in', 'token_valid', 'error'])

                # 验证字段值
                assert data['logged_in'] is False
                assert data['token_valid'] is False
                assert "cannot be decrypted" in data['error']

    def test_status_missing_refresh_token_field(self, runner: CliRunner, temp_token_file: Path):
        """测试：token 数据缺少 refresh_token 字段"""
        with patch('gallery_dl_auto.cli.status_cmd.get_default_token_storage') as mock_storage_factory:
            storage = TokenStorage(temp_token_file)
            mock_storage_factory.return_value = storage

            # Mock load_token 返回不完整的数据
            with patch.object(storage, 'load_token', return_value={"access_token": "test"}):
                # 执行命令
                result = run_cli_command(runner, ['--json-output', 'status'])

                # 验证命令执行成功
                assert result.exit_code == 0

                # 验证 JSON 输出
                data = assert_json_output(result.output, ['logged_in', 'token_valid', 'error'])

                # 验证字段值
                assert data['logged_in'] is False
                assert data['token_valid'] is False
                assert "missing refresh_token" in data['error']

    def test_status_auto_refresh_valid_token(self, runner: CliRunner, temp_token_file: Path):
        """测试：有效 token 自动刷新并保存"""
        mock_result = {
            "valid": True,
            "refresh_token": TestData.ALT_REFRESH_TOKEN,
            "access_token": TestData.ALT_REFRESH_TOKEN,
            "user": {
                "id": 12345678,
                "name": "TestUser",
                "account": "testuser"
            }
        }

        with patch('gallery_dl_auto.cli.status_cmd.PixivOAuth.validate_refresh_token') as mock_validate, \
             patch('gallery_dl_auto.cli.status_cmd.get_default_token_storage') as mock_storage_factory:

            mock_validate.return_value = mock_result
            storage = TokenStorage(temp_token_file)
            mock_storage_factory.return_value = storage

            # Mock save_token 方法以验证调用
            with patch.object(storage, 'save_token') as mock_save:
                # 执行命令
                result = run_cli_command(runner, ['--json-output', 'status'])

                # 验证命令执行成功
                assert result.exit_code == 0

                # 验证 save_token 被调用（自动刷新）
                mock_save.assert_called_once()
