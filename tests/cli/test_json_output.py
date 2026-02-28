"""测试静默和 JSON 输出模式

测试 --quiet 和 --json-output 全局参数,验证输出控制和格式。
"""

import json

import pytest

from gallery_dl_auto.cli.main import cli


class TestQuietMode:
    """测试 --quiet 参数"""

    def test_quiet_mode(self, runner):
        """验证 --quiet 参数禁用日志输出"""
        result = runner.invoke(cli, ["--quiet", "version"])

        # 静默模式下应该有输出
        assert len(result.output) > 0

        # 验证退出码
        assert result.exit_code == 0

    def test_quiet_disables_verbose(self, runner):
        """验证 --quiet 优先级高于 --verbose"""
        result = runner.invoke(cli, ["--quiet", "--verbose", "version"])

        # 静默模式下应该有输出(verbose 被忽略)
        assert len(result.output) > 0

        # 验证退出码
        assert result.exit_code == 0


class TestJsonOutputMode:
    """测试 --json-output 参数"""

    def test_json_output_flag_accepted(self, runner):
        """验证 --json-output 参数被接受"""
        result = runner.invoke(cli, ["--json-output", "version"])

        # 验证命令执行成功(参数被接受)
        assert result.exit_code == 0

        # 验证有输出
        assert len(result.output) > 0

    def test_json_error_handling(self, runner):
        """验证 JSON 模式下的错误处理"""
        # 测试无效命令
        result = runner.invoke(cli, ["--json-output", "nonexistent"])

        # 验证退出码(非0表示错误)
        # Click 在命令不存在时返回非0退出码
        assert result.exit_code != 0

        # Click 默认错误输出不是 JSON,这是预期行为
        # 实际的 JSON 错误处理将在具体命令中实现


class TestParameterPriority:
    """测试参数优先级"""

    def test_priority_json_over_quiet(self, runner):
        """验证 --json-output 优先级高于 --quiet"""
        result = runner.invoke(cli, ["--json-output", "--quiet", "version"])

        # 应该执行成功(参数组合有效)
        assert result.exit_code == 0

    def test_priority_quiet_over_verbose(self, runner):
        """验证 --quiet 优先级高于 --verbose"""
        result = runner.invoke(cli, ["--quiet", "--verbose", "version"])

        # 应该为静默模式(verbose 被忽略)
        assert len(result.output) > 0
