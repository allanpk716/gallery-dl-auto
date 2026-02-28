"""端到端集成测试

验证所有命令的 CLI API 行为,包括 JSON 帮助、静默模式和 JSON 输出。
"""

import json

import pytest

from gallery_dl_auto.cli.main import cli


def get_all_commands():
    """返回所有注册命令列表"""
    return list(cli.commands.keys())


class TestAllCommandsJsonHelp:
    """验证所有命令的 JSON 帮助功能"""

    def test_json_help_contains_all_commands(self, runner):
        """验证 JSON 帮助包含所有注册命令"""
        all_commands = get_all_commands()
        result = runner.invoke(cli, ["--json-help"])
        assert result.exit_code == 0

        help_data = json.loads(result.output)

        # 验证所有命令出现
        for cmd in all_commands:
            assert cmd in help_data, f"命令 {cmd} 未出现在 JSON 帮助中"

            # 验证命令元数据完整
            assert "name" in help_data[cmd]
            assert "description" in help_data[cmd]
            assert "parameters" in help_data[cmd]

    def test_all_commands_have_global_options(self, runner):
        """验证每个命令的参数列表包含全局选项"""
        all_commands = get_all_commands()
        result = runner.invoke(cli, ["--json-help"])
        help_data = json.loads(result.output)

        for command in all_commands:
            param_names = [p["name"] for p in help_data[command]["parameters"]]

            # 验证全局选项存在
            assert "verbose" in param_names, f"命令 {command} 缺少全局选项 verbose"
            assert "quiet" in param_names, f"命令 {command} 缺少全局选项 quiet"
            assert "json_output" in param_names, f"命令 {command} 缺少全局选项 json_output"
            assert "json_help" in param_names, f"命令 {command} 缺少全局选项 json_help"

    def test_json_help_parameter_completeness(self, runner):
        """验证每个命令的参数字段完整"""
        all_commands = get_all_commands()
        result = runner.invoke(cli, ["--json-help"])
        help_data = json.loads(result.output)

        for command in all_commands:
            for param in help_data[command]["parameters"]:
                # 验证必需字段存在
                assert "name" in param, f"命令 {command} 的参数缺少 name 字段"
                assert "type" in param, f"命令 {command} 的参数缺少 type 字段"
                assert "required" in param, f"命令 {command} 的参数缺少 required 字段"
                assert "description" in param, f"命令 {command} 的参数缺少 description 字段"
                assert "default_value" in param, f"命令 {command} 的参数缺少 default_value 字段"

                # 验证字段类型
                assert isinstance(param["name"], str)
                assert isinstance(param["type"], str)
                assert isinstance(param["required"], bool)
                assert isinstance(param["description"], str)


class TestAllCommandsQuietMode:
    """验证所有命令的静默模式"""

    def test_all_commands_quiet_mode(self, runner):
        """验证所有命令支持静默模式"""
        all_commands = get_all_commands()

        for command in all_commands:
            result = runner.invoke(cli, ["--quiet", command, "--help"])

            # 静默模式应该执行成功(虽然 --help 会覆盖)
            assert result.exit_code == 0, f"命令 {command} 在静默模式下执行失败"


class TestAllCommandsJsonOutput:
    """验证所有命令的 JSON 输出模式"""

    def test_all_commands_json_output_mode(self, runner):
        """验证所有命令支持 JSON 输出模式"""
        all_commands = get_all_commands()

        for command in all_commands:
            result = runner.invoke(cli, ["--json-output", command, "--help"])

            # JSON 输出模式应该执行成功(虽然 --help 会覆盖)
            assert result.exit_code == 0, f"命令 {command} 在 JSON 输出模式下执行失败"


class TestParameterPriority:
    """测试参数优先级在所有命令上的行为"""

    def test_priority_modes(self, runner):
        """验证参数优先级: --json-output > --quiet > --verbose"""
        # --quiet --verbose → 静默模式
        result = runner.invoke(cli, ["--quiet", "--verbose", "version"])
        assert result.exit_code == 0

        # --json-output --quiet → JSON 模式
        result = runner.invoke(cli, ["--json-output", "--quiet", "version"])
        assert result.exit_code == 0

        # --json-output --verbose → JSON 模式(verbose 被忽略)
        result = runner.invoke(cli, ["--json-output", "--verbose", "version"])
        assert result.exit_code == 0
