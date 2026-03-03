"""config 命令测试

测试 config 命令的配置查看功能。
"""

import json
import os
from pathlib import Path

import pytest
import yaml
from click.testing import CliRunner

from gallery_dl_auto.cli.main import cli
from tests.utils.test_helpers import assert_json_output, run_cli_command


class TestConfigCommand:
    """config 命令测试套件"""

    def test_config_with_valid_file_default_output(
        self, runner: CliRunner, temp_dir: Path
    ) -> None:
        """测试：有配置文件的默认输出（Rich 表格格式）"""
        # 创建配置文件
        config_data = {
            "save_path": "./downloads",
            "log_level": "INFO",
            "max_retries": 3
        }
        config_file = temp_dir / "config.yaml"
        with open(config_file, "w", encoding="utf-8") as f:
            yaml.dump(config_data, f)

        # 切换到临时目录
        old_cwd = os.getcwd()
        try:
            os.chdir(temp_dir)
            result = run_cli_command(runner, ["config"])

            # 验证命令执行成功
            assert result.exit_code == 0

            # 验证输出包含配置项
            assert "当前配置" in result.output or "save_path" in result.output
            assert "downloads" in result.output
        finally:
            os.chdir(old_cwd)

    def test_config_with_valid_file_json_output(
        self, runner: CliRunner, temp_dir: Path
    ) -> None:
        """测试：有配置文件的 JSON 输出"""
        # 创建配置文件
        config_data = {
            "save_path": "./downloads",
            "log_level": "INFO",
            "max_retries": 3
        }
        config_file = temp_dir / "config.yaml"
        with open(config_file, "w", encoding="utf-8") as f:
            yaml.dump(config_data, f)

        # 切换到临时目录
        old_cwd = os.getcwd()
        try:
            os.chdir(temp_dir)
            result = run_cli_command(runner, ["--json-output", "config"])

            # 验证命令执行成功
            assert result.exit_code == 0

            # 验证 JSON 输出
            data = assert_json_output(result.output, ["config"])

            # 验证配置内容
            assert "config" in data
            assert data["config"]["save_path"] == "./downloads"
            assert data["config"]["log_level"] == "INFO"
            assert data["config"]["max_retries"] == 3
        finally:
            os.chdir(old_cwd)

    def test_config_without_file_default_output(
        self, runner: CliRunner, temp_dir: Path
    ) -> None:
        """测试：无配置文件的默认输出（错误提示）"""
        old_cwd = os.getcwd()
        try:
            os.chdir(temp_dir)
            result = run_cli_command(runner, ["config"])

            # 验证命令失败
            assert result.exit_code != 0

            # 验证错误消息
            assert "错误" in result.output or "error" in result.output.lower()
            assert "config.yaml" in result.output
        finally:
            os.chdir(old_cwd)

    def test_config_without_file_json_output(
        self, runner: CliRunner, temp_dir: Path
    ) -> None:
        """测试：无配置文件的 JSON 输出"""
        old_cwd = os.getcwd()
        try:
            os.chdir(temp_dir)
            result = run_cli_command(runner, ["--json-output", "config"])

            # 验证命令失败（退出码 1）
            assert result.exit_code == 1

            # 验证 JSON 输出
            data = assert_json_output(result.output, ["error", "message"])

            # 验证错误信息
            assert data["error"] == "FileNotFoundError"
            assert "config.yaml" in data["message"]
        finally:
            os.chdir(old_cwd)

    def test_config_with_invalid_yaml(
        self, runner: CliRunner, temp_dir: Path
    ) -> None:
        """测试：无效 YAML 格式的配置文件"""
        # 创建无效的 YAML 文件
        config_file = temp_dir / "config.yaml"
        config_file.write_text("invalid: yaml: content:\n  - [unclosed", encoding="utf-8")

        old_cwd = os.getcwd()
        try:
            os.chdir(temp_dir)
            result = run_cli_command(runner, ["--json-output", "config"])

            # 验证命令失败
            assert result.exit_code == 1

            # 验证 JSON 输出
            data = assert_json_output(result.output, ["error", "message"])

            # 验证错误信息
            assert data["error"] == "YAMLError"
            assert "格式错误" in data["message"]
        finally:
            os.chdir(old_cwd)

    def test_config_with_chinese_characters(
        self, runner: CliRunner, temp_dir: Path
    ) -> None:
        """测试：包含中文字符的配置文件"""
        # 创建包含中文的配置文件
        config_data = {
            "save_path": "./下载目录",
            "description": "这是一个测试配置",
            "tags": ["插画", "漫画", "小说"]
        }
        config_file = temp_dir / "config.yaml"
        with open(config_file, "w", encoding="utf-8") as f:
            yaml.dump(config_data, f, allow_unicode=True)

        old_cwd = os.getcwd()
        try:
            os.chdir(temp_dir)
            result = run_cli_command(runner, ["--json-output", "config"])

            # 验证命令执行成功
            assert result.exit_code == 0

            # 验证 JSON 输出
            data = assert_json_output(result.output, ["config"])

            # 验证中文内容正确解析
            assert "下载目录" in data["config"]["save_path"]
            assert "测试配置" in data["config"]["description"]
            assert "插画" in data["config"]["tags"]
        finally:
            os.chdir(old_cwd)
