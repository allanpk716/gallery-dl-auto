"""version 命令测试

测试 version 命令的版本信息显示功能。
"""

import json
import platform
import sys

import pytest
from click.testing import CliRunner

from gallery_dl_auto import __version__
from gallery_dl_auto.cli.main import cli
from tests.utils.test_helpers import assert_json_output, run_cli_command


class TestVersionCommand:
    """version 命令测试套件"""

    def test_version_default_output(self, runner: CliRunner) -> None:
        """测试：version 命令默认输出"""
        result = run_cli_command(runner, ["version"])

        # 验证命令执行成功
        assert result.exit_code == 0

        # 验证输出包含版本号
        assert "version" in result.output.lower()
        assert __version__ in result.output

    def test_version_json_output(self, runner: CliRunner) -> None:
        """测试：version 命令 JSON 输出"""
        result = run_cli_command(runner, ["--json-output", "version"])

        # 验证命令执行成功
        assert result.exit_code == 0

        # 验证 JSON 输出
        data = assert_json_output(result.output, ["version", "python_version", "platform"])

        # 验证版本号
        assert data["version"] == __version__

        # 验证 Python 版本
        python_version = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        assert data["python_version"] == python_version

        # 验证平台信息
        assert data["platform"] == platform.system().lower()

    def test_version_format(self, runner: CliRunner) -> None:
        """测试：version 输出格式验证"""
        result = run_cli_command(runner, ["version"])

        # 验证命令执行成功
        assert result.exit_code == 0

        # 验证输出格式（应该是 "pixiv-downloader version X.X.X"）
        assert "pixiv-downloader" in result.output
        assert __version__ in result.output

    def test_version_json_structure(self, runner: CliRunner) -> None:
        """测试：version JSON 输出结构"""
        result = run_cli_command(runner, ["--json-output", "version"])

        # 验证命令执行成功
        assert result.exit_code == 0

        # 验证 JSON 结构
        data = json.loads(result.output)

        # 验证必需字段存在
        assert "version" in data
        assert "python_version" in data
        assert "platform" in data

        # 验证字段类型
        assert isinstance(data["version"], str)
        assert isinstance(data["python_version"], str)
        assert isinstance(data["platform"], str)

    def test_version_consistency(self, runner: CliRunner) -> None:
        """测试：version 在不同输出模式下版本号一致"""
        # 获取默认输出的版本号
        default_result = run_cli_command(runner, ["version"])
        assert __version__ in default_result.output

        # 获取 JSON 输出的版本号
        json_result = run_cli_command(runner, ["--json-output", "version"])
        data = json.loads(json_result.output)

        # 验证版本号一致
        assert data["version"] == __version__

    def test_version_python_version_format(self, runner: CliRunner) -> None:
        """测试：Python 版本格式（X.Y.Z）"""
        result = run_cli_command(runner, ["--json-output", "version"])

        # 验证命令执行成功
        assert result.exit_code == 0

        # 解析 JSON
        data = json.loads(result.output)

        # 验证 Python 版本格式（应该是 "major.minor.micro"）
        python_version = data["python_version"]
        parts = python_version.split(".")

        assert len(parts) == 3
        assert all(part.isdigit() for part in parts)

    def test_version_platform_value(self, runner: CliRunner) -> None:
        """测试：平台信息验证"""
        result = run_cli_command(runner, ["--json-output", "version"])

        # 验证命令执行成功
        assert result.exit_code == 0

        # 解析 JSON
        data = json.loads(result.output)

        # 验证平台信息（应该是小写的系统名称）
        expected_platform = platform.system().lower()
        assert data["platform"] == expected_platform
