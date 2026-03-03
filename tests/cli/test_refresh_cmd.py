"""Refresh command tests

Tests the 'pixiv-downloader refresh' command functionality.
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
    assert_cli_failure,
    assert_cli_success,
    assert_json_output,
    run_cli_command,
)


class TestRefreshCommand:
    """refresh 命令测试套件"""

    def test_refresh_success(self, runner: CliRunner, temp_token_file: Path):
        """测试：刷新 token 成功"""
        # Mock validate_refresh_token 返回成功
        mock_result = {
            "valid": True,
            "refresh_token": TestData.ALT_REFRESH_TOKEN,  # 新 token
            "access_token": TestData.ALT_REFRESH_TOKEN,
            "user": {
                "id": 12345678,
                "name": "TestUser",
                "account": "testuser"
            }
        }

        with patch('gallery_dl_auto.cli.refresh_cmd.PixivOAuth.validate_refresh_token') as mock_validate, \
             patch('gallery_dl_auto.cli.refresh_cmd.get_default_token_storage') as mock_storage_factory:

            mock_validate.return_value = mock_result
            storage = TokenStorage(temp_token_file)
            mock_storage_factory.return_value = storage

            # Mock save_token 方法以验证调用
            with patch.object(storage, 'save_token') as mock_save:
                # 执行命令
                result = run_cli_command(runner, ['refresh'])

                # 验证命令执行成功（退出码 0）
                assert result.exit_code == 0

                # 验证 JSON 输出
                data = assert_json_output(result.output, ['success', 'data'])

                # 验证字段值
                assert data['success'] is True
                assert 'old_token_masked' in data['data']
                assert 'new_token_masked' in data['data']
                assert 'expires_in_days' in data['data']

                # 验证 save_token 被调用
                mock_save.assert_called_once()

    def test_refresh_no_token_found(self, runner: CliRunner):
        """测试：无 token 时刷新"""
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            non_existent_token = Path(tmpdir) / ".token"

            with patch('gallery_dl_auto.cli.refresh_cmd.get_default_token_storage') as mock_storage_factory:
                storage = TokenStorage(non_existent_token)
                mock_storage_factory.return_value = storage

                # 执行命令
                result = run_cli_command(runner, ['refresh'])

                # 验证命令失败（退出码 1）
                assert result.exit_code == 1

                # 验证 JSON 输出
                data = assert_json_output(result.output, ['success', 'error'])

                # 验证字段值
                assert data['success'] is False
                assert 'error' in data
                assert 'code' in data['error']
                assert 'No token found' in data['error']['message']

    def test_refresh_invalid_token(self, runner: CliRunner, temp_token_file: Path):
        """测试：刷新无效 token 失败"""
        # Mock validate_refresh_token 返回失败
        mock_result = {
            "valid": False,
            "error": "Token expired or invalid"
        }

        with patch('gallery_dl_auto.cli.refresh_cmd.PixivOAuth.validate_refresh_token') as mock_validate, \
             patch('gallery_dl_auto.cli.refresh_cmd.get_default_token_storage') as mock_storage_factory:

            mock_validate.return_value = mock_result
            storage = TokenStorage(temp_token_file)
            mock_storage_factory.return_value = storage

            # 执行命令
            result = run_cli_command(runner, ['refresh'])

            # 验证命令失败（退出码 1）
            assert result.exit_code == 1

            # 验证 JSON 输出
            data = assert_json_output(result.output, ['success', 'error'])

            # 验证字段值
            assert data['success'] is False
            assert 'error' in data
            assert 'code' in data['error']
            assert 'Token expired' in data['error']['message']

    def test_refresh_network_error(self, runner: CliRunner, temp_token_file: Path):
        """测试：网络错误导致刷新失败"""
        with patch('gallery_dl_auto.cli.refresh_cmd.PixivOAuth.validate_refresh_token') as mock_validate, \
             patch('gallery_dl_auto.cli.refresh_cmd.get_default_token_storage') as mock_storage_factory:

            # Mock 抛出网络异常
            mock_validate.side_effect = ConnectionError("Network error")
            storage = TokenStorage(temp_token_file)
            mock_storage_factory.return_value = storage

            # 执行命令
            result = run_cli_command(runner, ['refresh'])

            # 验证命令失败（退出码 1）
            assert result.exit_code == 1

            # 验证 JSON 输出
            data = assert_json_output(result.output, ['success', 'error'])

            # 验证字段值
            assert data['success'] is False
            assert 'error' in data
            assert 'code' in data['error']
            assert 'Unexpected error' in data['error']['message']

    def test_refresh_output_format(self, runner: CliRunner, temp_token_file: Path):
        """测试：refresh 输出格式（JSON 格式化）"""
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

        with patch('gallery_dl_auto.cli.refresh_cmd.PixivOAuth.validate_refresh_token') as mock_validate, \
             patch('gallery_dl_auto.cli.refresh_cmd.get_default_token_storage') as mock_storage_factory:

            mock_validate.return_value = mock_result
            storage = TokenStorage(temp_token_file)
            mock_storage_factory.return_value = storage

            with patch.object(storage, 'save_token'):
                # 执行命令
                result = run_cli_command(runner, ['refresh'])

                # 验证命令执行成功
                assert result.exit_code == 0

                # 验证 JSON 格式（应该是格式化的 JSON，带缩进）
                data = json.loads(result.output)
                assert 'success' in data
                assert data['success'] is True
                assert 'data' in data
                assert 'old_token_masked' in data['data']
                assert 'new_token_masked' in data['data']
                assert 'expires_in_days' in data['data']
