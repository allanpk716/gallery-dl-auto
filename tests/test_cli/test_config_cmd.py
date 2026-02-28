"""config 命令测试"""

import os

import pytest
from click.testing import CliRunner
from gallery_dl_auto.cli.main import cli


def test_config_command_with_file(
    runner: CliRunner, tmp_path: pytest.TempPathFactory
) -> None:
    """测试 config 命令(有配置文件)"""
    # 创建临时配置文件
    config_file = tmp_path / "config.yaml"
    config_file.write_text("save_path: ./downloads\nlog_level: INFO\n")

    # 切换到临时目录
    old_cwd = os.getcwd()
    try:
        os.chdir(tmp_path)
        result = runner.invoke(cli, ["config"])
        assert result.exit_code == 0
        assert "配置" in result.output or "save_path" in result.output
    finally:
        os.chdir(old_cwd)


def test_config_command_without_file(
    runner: CliRunner, tmp_path: pytest.TempPathFactory
) -> None:
    """测试 config 命令(无配置文件)"""
    # 切换到没有配置文件的临时目录
    old_cwd = os.getcwd()
    try:
        os.chdir(tmp_path)
        result = runner.invoke(cli, ["config"])
        # 应该失败或提示文件不存在
        assert (
            result.exit_code != 0
            or "错误" in result.output
            or "error" in result.output.lower()
        )
    finally:
        os.chdir(old_cwd)
