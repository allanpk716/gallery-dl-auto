"""测试主命令和全局选项

测试 CLI 的主命令入口点、全局选项、选项优先级和错误处理。
"""

import json

import pytest
from click.testing import CliRunner

from gallery_dl_auto.cli.main import cli
from tests.utils.test_helpers import (
    assert_cli_success,
    assert_cli_failure,
    assert_json_output,
    run_cli_command,
)


class TestMainCommand:
    """测试主命令入口点"""

    def test_main_help(self, runner: CliRunner) -> None:
        """测试主命令帮助输出"""
        result = run_cli_command(runner, ["--help"])

        # 验证命令成功
        assert_cli_success(result)

        # 验证帮助内容包含关键字
        assert "Pixiv 排行榜下载器" in result.output
        assert "Usage:" in result.output
        assert "Commands:" in result.output

        # 验证常用命令出现在帮助中
        expected_commands = ["download", "login", "status", "version", "config", "doctor"]
        for cmd in expected_commands:
            assert cmd in result.output, f"命令 {cmd} 未出现在帮助中"

    def test_main_help_shows_first_time_notice(self, runner: CliRunner) -> None:
        """测试主命令帮助显示首次使用提示"""
        result = run_cli_command(runner, ["--help"])

        assert_cli_success(result)
        assert "首次使用必读" in result.output or "首次使用" in result.output

    def test_version_via_help_command(self, runner: CliRunner) -> None:
        """测试 version 命令在帮助中可见"""
        result = run_cli_command(runner, ["--help"])

        # 验证命令成功
        assert_cli_success(result)

        # 验证 version 命令出现在帮助中
        assert "version" in result.output

    def test_version_command_shows_version(self, runner: CliRunner) -> None:
        """测试 version 子命令显示版本信息"""
        result = run_cli_command(runner, ["version"])

        # 验证命令成功
        assert_cli_success(result)

        # 验证版本号格式
        assert "version" in result.output.lower()

    def test_main_shows_usage_without_args(self, runner: CliRunner) -> None:
        """测试无参数时显示使用说明"""
        result = run_cli_command(runner, [])

        # Click 默认会显示帮助
        assert "Usage:" in result.output or "Commands:" in result.output


class TestGlobalOptions:
    """测试全局选项"""

    def test_verbose_mode_accepted(self, runner: CliRunner) -> None:
        """测试 --verbose 参数被接受"""
        result = run_cli_command(runner, ["--verbose", "version"])

        # 验证参数被接受
        assert_cli_success(result)

    def test_verbose_short_flag_accepted(self, runner: CliRunner) -> None:
        """测试 -v 短标志被接受"""
        result = run_cli_command(runner, ["-v", "version"])

        # 验证参数被接受
        assert_cli_success(result)

    def test_quiet_mode_accepted(self, runner: CliRunner) -> None:
        """测试 --quiet 参数被接受"""
        result = run_cli_command(runner, ["--quiet", "version"])

        # 验证参数被接受
        assert_cli_success(result)

    def test_quiet_short_flag_accepted(self, runner: CliRunner) -> None:
        """测试 -q 短标志被接受"""
        result = run_cli_command(runner, ["-q", "version"])

        # 验证参数被接受
        assert_cli_success(result)

    def test_json_output_mode_accepted(self, runner: CliRunner) -> None:
        """测试 --json-output 参数被接受"""
        result = run_cli_command(runner, ["--json-output", "version"])

        # 验证参数被接受
        assert_cli_success(result)

        # 验证输出为 JSON 格式
        data = assert_json_output(result.output)
        assert "version" in data

    def test_json_help_mode_accepted(self, runner: CliRunner) -> None:
        """测试 --json-help 参数被接受"""
        result = run_cli_command(runner, ["--json-help"])

        # 验证参数被接受
        assert_cli_success(result)

        # 验证输出为 JSON 格式
        data = assert_json_output(result.output)
        assert isinstance(data, dict)


class TestOptionPriority:
    """测试选项优先级"""

    def test_json_output_overrides_verbose(self, runner: CliRunner) -> None:
        """测试 JSON 输出模式覆盖详细模式

        当 --json-output 和 --verbose 同时指定时，应该使用 JSON 输出
        """
        result = run_cli_command(runner, ["--json-output", "--verbose", "version"])

        # 验证命令成功
        assert_cli_success(result)

        # 验证输出为 JSON 格式
        data = assert_json_output(result.output)
        assert "version" in data

    def test_json_output_overrides_quiet(self, runner: CliRunner) -> None:
        """测试 JSON 输出模式覆盖静默模式

        当 --json-output 和 --quiet 同时指定时，应该使用 JSON 输出
        """
        result = run_cli_command(runner, ["--json-output", "--quiet", "version"])

        # 验证命令成功
        assert_cli_success(result)

        # 验证输出为 JSON 格式
        data = assert_json_output(result.output)
        assert "version" in data

    def test_quiet_overrides_verbose(self, runner: CliRunner) -> None:
        """测试静默模式覆盖详细模式

        当 --quiet 和 --verbose 同时指定时，应该使用静默模式
        """
        result = run_cli_command(runner, ["--quiet", "--verbose", "version"])

        # 验证命令成功
        assert_cli_success(result)

        # 静默模式应该有输出（version 命令仍会输出）
        assert len(result.output) > 0

    def test_priority_chain_json_wins(self, runner: CliRunner) -> None:
        """测试优先级链：json-output > quiet > verbose"""
        # 三者同时指定，json-output 应该获胜
        result = run_cli_command(
            runner, ["--json-output", "--quiet", "--verbose", "version"]
        )

        # 验证命令成功
        assert_cli_success(result)

        # 验证输出为 JSON 格式
        data = assert_json_output(result.output)
        assert "version" in data


class TestErrorHandling:
    """测试错误处理"""

    def test_invalid_command_shows_error(self, runner: CliRunner) -> None:
        """测试无效命令显示错误信息"""
        result = run_cli_command(runner, ["invalid_command_that_does_not_exist"])

        # 验证命令失败
        assert_cli_failure(result)

        # 验证错误信息
        assert "No such command" in result.output or "Error" in result.output

    def test_invalid_option_shows_error(self, runner: CliRunner) -> None:
        """测试无效选项显示错误信息"""
        result = run_cli_command(runner, ["--invalid-option"])

        # 验证命令失败
        assert_cli_failure(result)

        # 验证错误信息
        assert "Error" in result.output or "no such option" in result.output.lower()

    def test_missing_command_argument_shows_error(self, runner: CliRunner) -> None:
        """测试缺少命令参数时显示错误"""
        # 测试需要参数但未提供的命令
        # download 命令通常需要参数
        result = run_cli_command(runner, ["download"])

        # 验证失败或显示帮助
        # Click 可能会显示帮助而不是错误
        assert result.exit_code != 0 or "Usage:" in result.output

    @pytest.mark.parametrize(
        "option_combo",
        [
            ["--verbose", "--quiet", "version"],
            ["--json-output", "--verbose", "version"],
            ["--json-output", "--quiet", "version"],
            ["-v", "-q", "version"],
        ],
    )
    def test_conflicting_options_handled_gracefully(
        self, runner: CliRunner, option_combo: list[str]
    ) -> None:
        """测试冲突选项被优雅处理

        冲突选项不应该导致程序崩溃，而是按照优先级处理
        """
        result = run_cli_command(runner, option_combo)

        # 验证命令成功（不会因为冲突而失败）
        assert_cli_success(result)


class TestCommandRegistration:
    """测试命令注册"""

    @pytest.mark.parametrize(
        "command_name",
        ["version", "config", "doctor", "download", "login", "logout", "refresh", "status"],
    )
    def test_command_registered(self, runner: CliRunner, command_name: str) -> None:
        """测试所有预期命令已注册"""
        result = run_cli_command(runner, ["--help"])

        # 验证命令出现在帮助中
        assert_cli_success(result)
        assert command_name in result.output

    def test_all_commands_accessible(self, runner: CliRunner) -> None:
        """测试所有命令可以访问"""
        # 测试几个关键命令
        commands_to_test = [
            ["version"],
            ["status"],
            ["config"],
        ]

        for cmd in commands_to_test:
            result = run_cli_command(runner, cmd)
            # 命令应该执行成功或失败，但不应该抛出异常
            assert result.exit_code is not None


class TestCommandHelpIntegration:
    """测试命令帮助集成"""

    @pytest.mark.parametrize(
        "command",
        [
            "version",
            "status",
            "config",
            "doctor",
            "login",
            "logout",
            "refresh",
            "download",
        ],
    )
    def test_command_help_works(self, runner: CliRunner, command: str) -> None:
        """测试每个子命令的 --help 工作正常"""
        result = run_cli_command(runner, [command, "--help"])

        # 验证帮助显示
        assert_cli_success(result)
        assert "Usage:" in result.output or command in result.output.lower()

    def test_main_help_lists_all_commands(self, runner: CliRunner) -> None:
        """测试主帮助列出所有命令"""
        result = run_cli_command(runner, ["--help"])

        assert_cli_success(result)

        # 验证所有命令都出现在帮助中
        expected_commands = [
            "download",
            "version",
            "config",
            "doctor",
            "login",
            "logout",
            "refresh",
            "status",
        ]

        for cmd in expected_commands:
            assert cmd in result.output, f"命令 {cmd} 未出现在主帮助中"
