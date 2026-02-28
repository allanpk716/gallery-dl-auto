"""测试 JSON 帮助功能

测试 --json-help 全局参数,验证 JSON 帮助的结构和完整性。
"""

import json

import pytest

from gallery_dl_auto.cli.main import cli


class TestJsonHelpStructure:
    """验证 JSON 帮助的结构"""

    def test_json_help_structure(self, runner):
        """验证 JSON 帮助的结构包含必需字段"""
        result = runner.invoke(cli, ["--json-help"])

        # 验证命令成功执行
        assert result.exit_code == 0

        # 验证输出是有效 JSON
        help_data = json.loads(result.output)

        # 验证返回值是字典类型
        assert isinstance(help_data, dict)

        # 验证包含预期命令
        expected_commands = ["download", "version", "config", "doctor", "login", "logout", "refresh", "status"]
        for cmd in expected_commands:
            assert cmd in help_data, f"命令 {cmd} 未出现在 JSON 帮助中"

            # 验证每个命令对象包含必需字段
            assert "name" in help_data[cmd]
            assert "description" in help_data[cmd]
            assert "parameters" in help_data[cmd]

    def test_json_help_completeness(self, runner):
        """验证参数完整性"""
        result = runner.invoke(cli, ["--json-help"])
        assert result.exit_code == 0

        help_data = json.loads(result.output)

        # 遍历每个命令的参数列表
        for cmd_name, cmd_info in help_data.items():
            parameters = cmd_info["parameters"]

            # 断言每个参数包含必需字段
            for param in parameters:
                assert "name" in param, f"命令 {cmd_name} 的参数缺少 name 字段"
                assert "type" in param, f"命令 {cmd_name} 的参数 {param.get('name')} 缺少 type 字段"
                assert "required" in param, f"命令 {cmd_name} 的参数 {param.get('name')} 缺少 required 字段"
                assert "description" in param, f"命令 {cmd_name} 的参数 {param.get('name')} 缺少 description 字段"
                assert "default_value" in param, f"命令 {cmd_name} 的参数 {param.get('name')} 缺少 default_value 字段"

    def test_json_help_flag_works(self, runner):
        """验证 --json-help 参数工作正常"""
        result = runner.invoke(cli, ["--json-help"])

        # 验证退出码
        assert result.exit_code == 0

        # 验证输出是有效 JSON
        try:
            help_data = json.loads(result.output)
        except json.JSONDecodeError:
            pytest.fail("--json-help 输出不是有效 JSON")

        # 验证 JSON 包含 download 命令
        assert "download" in help_data

    def test_json_help_contains_global_options(self, runner):
        """验证每个命令的参数列表包含全局选项"""
        result = runner.invoke(cli, ["--json-help"])
        assert result.exit_code == 0

        help_data = json.loads(result.output)

        # 遍历所有命令
        for cmd_name, cmd_info in help_data.items():
            param_names = [p["name"] for p in cmd_info["parameters"]]

            # 验证全局选项存在
            assert "verbose" in param_names, f"命令 {cmd_name} 缺少全局选项 verbose"
            assert "quiet" in param_names, f"命令 {cmd_name} 缺少全局选项 quiet"
            assert "json_output" in param_names, f"命令 {cmd_name} 缺少全局选项 json_output"
            assert "json_help" in param_names, f"命令 {cmd_name} 缺少全局选项 json_help"
