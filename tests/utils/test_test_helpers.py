"""测试 test_helpers 辅助函数

验证所有辅助函数可以正常导入和基本使用。
"""

import json

import pytest
from click.testing import CliRunner

from tests.utils.test_helpers import (
    assert_cli_failure,
    assert_cli_success,
    assert_json_output,
    assert_jsonl_output,
    run_cli_command,
)


class TestAssertJsonOutput:
    """测试 assert_json_output 函数"""

    def test_valid_json(self) -> None:
        """测试有效的 JSON 输出"""
        output = '{"status": "success", "count": 10}'
        data = assert_json_output(output)
        assert data["status"] == "success"
        assert data["count"] == 10

    def test_valid_json_with_expected_keys(self) -> None:
        """测试带期望键的有效 JSON"""
        output = '{"command": "download", "status": "success"}'
        data = assert_json_output(output, expected_keys=["command", "status"])
        assert data["command"] == "download"

    def test_invalid_json(self) -> None:
        """测试无效的 JSON 输出"""
        output = "not a json"
        with pytest.raises(AssertionError, match="输出不是有效的 JSON"):
            assert_json_output(output)

    def test_missing_expected_key(self) -> None:
        """测试缺少期望键的 JSON"""
        output = '{"status": "success"}'
        with pytest.raises(AssertionError, match="JSON 输出缺少期望的键"):
            assert_json_output(output, expected_keys=["missing_key"])

    def test_json_with_chinese(self) -> None:
        """测试包含中文的 JSON"""
        output = '{"状态": "成功", "消息": "下载完成"}'
        data = assert_json_output(output)
        assert data["状态"] == "成功"


class TestAssertJsonlOutput:
    """测试 assert_jsonl_output 函数"""

    def test_valid_jsonl(self) -> None:
        """测试有效的 JSONL 输出"""
        output = '{"status":"success","count":10}'
        data = assert_jsonl_output(output)
        assert data["status"] == "success"
        assert data["count"] == 10

    def test_jsonl_single_line_only(self) -> None:
        """测试 JSONL 必须是单行"""
        output = '{"status":"success"}\n{"status":"failed"}'
        with pytest.raises(AssertionError, match="JSONL 输出应该只有一行"):
            assert_jsonl_output(output)

    def test_jsonl_no_indentation(self) -> None:
        """测试 JSONL 不应该有缩进"""
        # 带格式的 JSON（不是紧凑格式）
        output = '{"status": "success", "count": 10}'
        with pytest.raises(AssertionError, match="JSONL 输出应该是紧凑格式"):
            assert_jsonl_output(output)

    def test_jsonl_with_expected_keys(self) -> None:
        """测试带期望键的 JSONL"""
        output = '{"command":"download","status":"success"}'
        data = assert_jsonl_output(output, expected_keys=["command", "status"])
        assert data["command"] == "download"


class TestRunCliCommand:
    """测试 run_cli_command 函数"""

    def test_help_command(self) -> None:
        """测试帮助命令"""
        runner = CliRunner()
        result = run_cli_command(runner, ["--help"])
        assert result.exit_code == 0
        assert "Usage" in result.output or "用法" in result.output

    def test_version_command(self) -> None:
        """测试版本命令"""
        runner = CliRunner()
        result = run_cli_command(runner, ["--version"])
        # 版本命令可能不存在，这里只是测试函数可以正常调用
        # 如果不存在，exit_code 可能为 2
        assert result.exit_code in [0, 2]

    def test_command_with_kwargs(self) -> None:
        """测试带额外参数的命令"""
        runner = CliRunner()
        result = run_cli_command(runner, ["--help"], catch_exceptions=False)
        assert result.exit_code == 0


class TestAssertCliSuccess:
    """测试 assert_cli_success 函数"""

    def test_successful_command(self) -> None:
        """测试成功的命令"""
        runner = CliRunner()
        # 使用实际的 CLI 命令而不是 lambda
        result = run_cli_command(runner, ["--help"])
        assert_cli_success(result)  # 不应该抛出异常

    def test_failed_command(self) -> None:
        """测试失败的命令"""
        runner = CliRunner()
        # 使用一个会失败的命令
        result = run_cli_command(runner, ["invalid-command"])
        with pytest.raises(AssertionError, match="命令执行失败"):
            assert_cli_success(result)

    def test_custom_message(self) -> None:
        """测试自定义错误消息"""
        runner = CliRunner()
        result = run_cli_command(runner, ["invalid-command"])
        with pytest.raises(AssertionError, match="自定义错误"):
            assert_cli_success(result, message="自定义错误")


class TestAssertCliFailure:
    """测试 assert_cli_failure 函数"""

    def test_failed_command(self) -> None:
        """测试失败的命令"""
        runner = CliRunner()
        result = run_cli_command(runner, ["invalid-command"])
        assert_cli_failure(result)  # 不应该抛出异常

    def test_failed_command_with_expected_code(self) -> None:
        """测试带期望退出码的失败命令"""
        runner = CliRunner()
        result = run_cli_command(runner, ["invalid-command"])
        # Click 对于无效命令通常返回 exit_code 2
        assert_cli_failure(result, expected_exit_code=2)

    def test_successful_command(self) -> None:
        """测试成功的命令应该抛出异常"""
        runner = CliRunner()
        result = run_cli_command(runner, ["--help"])
        with pytest.raises(AssertionError, match="命令应该执行失败但成功了"):
            assert_cli_failure(result)

    def test_wrong_exit_code(self) -> None:
        """测试错误的退出码"""
        runner = CliRunner()
        result = run_cli_command(runner, ["invalid-command"])
        # 期望退出码 1，但实际是 2
        with pytest.raises(AssertionError, match="期望退出码 1"):
            assert_cli_failure(result, expected_exit_code=1)


class TestHelperFunctionsIntegration:
    """集成测试：测试辅助函数的组合使用"""

    def test_json_output_with_cli(self) -> None:
        """测试 JSON 输出与 CLI 的组合"""
        runner = CliRunner()

        # 使用 --json-help 应该输出 JSON
        result = run_cli_command(runner, ["--json-help"])
        assert_cli_success(result)

        # 验证输出是有效的 JSON
        # --json-help 输出的结构是 {command_name: {info}, ...}
        data = assert_json_output(result.output)

        # 验证包含一些已知的命令
        assert "version" in data or "download" in data or "login" in data

    def test_jsonl_validation_workflow(self) -> None:
        """测试 JSONL 验证工作流"""
        # 模拟一个 JSONL 输出
        jsonl_output = json.dumps(
            {"status": "success", "downloaded": 5}, separators=(",", ":")
        )

        # 验证 JSONL 格式
        data = assert_jsonl_output(jsonl_output, expected_keys=["status", "downloaded"])
        assert data["status"] == "success"
        assert data["downloaded"] == 5
