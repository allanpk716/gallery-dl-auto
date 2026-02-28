"""CLI 主命令测试"""

from click.testing import CliRunner
from gallery_dl_auto.cli.main import cli


def test_cli_help(runner: CliRunner) -> None:
    """测试 --help 选项"""
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "Pixiv 排行榜下载器" in result.output


def test_cli_verbose_option(runner: CliRunner) -> None:
    """测试 --verbose 选项"""
    result = runner.invoke(cli, ["--verbose", "version"])
    assert result.exit_code == 0


def test_cli_quiet_option(runner: CliRunner) -> None:
    """测试 --quiet 选项"""
    result = runner.invoke(cli, ["--quiet", "version"])
    assert result.exit_code == 0


def test_version_command(runner: CliRunner) -> None:
    """测试 version 命令"""
    result = runner.invoke(cli, ["version"])
    assert result.exit_code == 0
    assert "version" in result.output.lower()
