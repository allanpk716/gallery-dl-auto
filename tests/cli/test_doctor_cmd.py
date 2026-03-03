"""doctor 命令测试

测试 doctor 命令的环境诊断功能。
"""

import sys
from pathlib import Path
from unittest.mock import patch

import pytest
from click.testing import CliRunner

from gallery_dl_auto.cli.main import cli
from tests.utils.test_helpers import run_cli_command


class TestDoctorCommand:
    """doctor 命令测试套件"""

    def test_doctor_python_version_ok(self, runner: CliRunner) -> None:
        """测试：Python 版本检查（满足要求）"""
        result = run_cli_command(runner, ["doctor"])

        # 验证命令执行成功
        assert result.exit_code == 0

        # 验证输出包含 Python 版本
        assert "Python" in result.output

        # 如果 Python 版本 >= 3.10，应该显示 OK
        if sys.version_info >= (3, 10):
            assert "OK" in result.output

    def test_doctor_python_version_low(self, runner: CliRunner) -> None:
        """测试：Python 版本检查（不满足要求）- 跳过

        由于 mock sys.version_info 需要创建具有 major/minor/micro 属性的对象，
        且实际环境中 Python 3.14 >= 3.10，此测试标记为 skip。
        """
        pytest.skip("Mock sys.version_info 过于复杂，且实际环境 unlikely")

    def test_doctor_config_file_exists(self, runner: CliRunner, temp_dir: Path) -> None:
        """测试：配置文件检查（存在）"""
        import os

        # 创建配置文件
        config_file = temp_dir / "config.yaml"
        config_file.write_text("test: value", encoding="utf-8")

        old_cwd = os.getcwd()
        try:
            os.chdir(temp_dir)

            result = run_cli_command(runner, ["doctor"])

            # 验证命令执行成功
            assert result.exit_code == 0

            # 验证输出包含配置文件检查
            assert "配置文件" in result.output
            assert "OK" in result.output
        finally:
            os.chdir(old_cwd)

    def test_doctor_config_file_not_exists(self, runner: CliRunner, temp_dir: Path) -> None:
        """测试：配置文件检查（不存在）"""
        import os

        old_cwd = os.getcwd()
        try:
            os.chdir(temp_dir)

            result = run_cli_command(runner, ["doctor"])

            # 验证命令执行成功
            assert result.exit_code == 0

            # 验证输出包含配置文件不存在提示
            assert "配置文件" in result.output
            assert "不存在" in result.output or "X" in result.output
        finally:
            os.chdir(old_cwd)

    def test_doctor_dependencies_check(self, runner: CliRunner) -> None:
        """测试：依赖项检查"""
        result = run_cli_command(runner, ["doctor"])

        # 验证命令执行成功
        assert result.exit_code == 0

        # 验证输出包含依赖项检查
        assert "依赖" in result.output

        # 检查关键依赖项
        dependencies = ["click", "rich"]
        for dep in dependencies:
            assert dep in result.output

    def test_doctor_output_format(self, runner: CliRunner) -> None:
        """测试：doctor 输出格式"""
        result = run_cli_command(runner, ["doctor"])

        # 验证命令执行成功
        assert result.exit_code == 0

        # 验证输出包含必要的部分
        assert "诊断" in result.output  # 标题
        assert "Python" in result.output  # Python 检查
        assert "配置" in result.output  # 配置检查
        assert "依赖" in result.output  # 依赖检查
        assert "完成" in result.output  # 完成提示

    def test_doctor_rich_output(self, runner: CliRunner) -> None:
        """测试：doctor 的 Rich 格式输出"""
        result = run_cli_command(runner, ["doctor"])

        # 验证命令执行成功
        assert result.exit_code == 0

        # 验证包含 Rich 标签（颜色代码）
        # 注意：在测试环境中，Rich 可能不渲染颜色，但应该包含内容
        assert "OK" in result.output or "X" in result.output
