"""端到端集成测试：R18 排行榜下载功能

测试所有 R18 排行榜在实际环境中的下载功能,验证 day_male_r18 等不再报 Invalid mode 错误。
使用 --dry-run 模式避免实际下载图片。

标记说明:
- @pytest.mark.integration: 集成测试标记
- @pytest.mark.slow: 慢速测试标记
- @pytest.mark.skipif: 条件跳过(无 token 时)
"""

import json
import pytest
from pathlib import Path
from click.testing import CliRunner
from unittest.mock import Mock, patch, MagicMock

from gallery_dl_auto.cli.download_cmd import download
from gallery_dl_auto.auth.token_storage import TokenStorage


# 检查是否有可用的 token
def has_valid_token():
    """检查是否存在有效的登录 token"""
    try:
        from gallery_dl_auto.auth.token_storage import get_default_token_storage
        storage = get_default_token_storage()
        token_data = storage.load_token()
        return token_data is not None and "refresh_token" in token_data
    except Exception:
        return False


# Skip 条件:无有效 token 时跳过
requires_auth = pytest.mark.skipif(
    not has_valid_token(),
    reason="需要有效的登录 token 才能运行此测试。运行 'pixiv-downloader login' 进行登录。"
)


@pytest.fixture
def runner():
    """CLI 测试 runner"""
    return CliRunner()


@pytest.fixture
def mock_config():
    """模拟配置对象"""
    # 创建简单的配置字典,模拟 OmegaConf DictConfig
    from omegaconf import OmegaConf

    config = OmegaConf.create({
        "save_path": "./downloads",
        "concurrent_downloads": 3,
        "request_interval": 1.0,
        "log_level": "INFO",
        "api_timeout": 30,
        "max_retries": 3,
        "output_mode": "normal",
        "download": {
            "batch_size": 30,
            "image_delay": 0.1,  # 加速测试
            "batch_delay": 0.1,
            "max_retries": 1,
            "retry_delay": 0.1,
        }
    })
    return config


class TestR18RankingDownload:
    """测试 R18 排行榜下载功能"""

    @pytest.mark.integration
    @pytest.mark.slow
    @requires_auth
    def test_day_r18_dry_run(self, runner, mock_config):
        """测试 day_r18 排行榜 (--dry-run 模式)

        验证点:
        1. 命令成功执行,无 "Invalid mode" 错误 (最重要)
        2. 输出 JSON 格式正确
        3. success 字段为 true (dry-run 模式下不会真正失败)
        """
        result = runner.invoke(
            download,
            ["--type", "day_r18", "--dry-run", "--limit", "5"],
            obj=mock_config,
        )

        # 关键验证：命令执行成功，无 Invalid mode 错误
        assert result.exit_code == 0, f"命令执行失败: {result.output}"
        assert "Invalid mode" not in result.output, f"发现 Invalid mode 错误: {result.output}"
        assert "Invalid ranking type" not in result.output, f"发现 Invalid ranking type 错误: {result.output}"

        # 解析 JSON 输出
        try:
            output_data = json.loads(result.output)
        except json.JSONDecodeError as e:
            pytest.fail(f"输出不是有效的 JSON: {e}\n输出内容: {result.output}")

        # 验证输出结构（gallery-dl 引擎的 dry-run 输出）
        assert output_data.get("success") is True, "dry-run 模式应该成功"

    @pytest.mark.integration
    @pytest.mark.slow
    @requires_auth
    def test_day_male_r18_dry_run(self, runner, mock_config):
        """测试 day_male_r18 排行榜 (--dry-run 模式)

        验证点:
        1. day_male_r18 mode 不再报 "Invalid mode" 错误 (核心验证)
        2. 命令成功执行
        """
        result = runner.invoke(
            download,
            ["--type", "day_male_r18", "--dry-run", "--limit", "5"],
            obj=mock_config,
        )

        # 关键验证:无 Invalid mode 错误
        assert result.exit_code == 0, f"命令执行失败: {result.output}"
        assert "Invalid mode" not in result.output, f"发现 Invalid mode 错误: {result.output}"
        assert "Invalid ranking type" not in result.output, f"发现 Invalid ranking type 错误: {result.output}"

        # 验证输出是有效 JSON
        output_data = json.loads(result.output)
        assert output_data.get("success") is True

    @pytest.mark.integration
    @pytest.mark.slow
    @requires_auth
    def test_day_female_r18_dry_run(self, runner, mock_config):
        """测试 day_female_r18 排行榜 (--dry-run 模式)

        验证点:
        1. day_female_r18 mode 正常工作
        2. 没有 Invalid mode 错误
        """
        result = runner.invoke(
            download,
            ["--type", "day_female_r18", "--dry-run", "--limit", "5"],
            obj=mock_config,
        )

        assert result.exit_code == 0, f"命令执行失败: {result.output}"
        assert "Invalid mode" not in result.output
        assert "Invalid ranking type" not in result.output

        output_data = json.loads(result.output)
        assert output_data.get("success") is True

    @pytest.mark.integration
    @pytest.mark.slow
    @requires_auth
    def test_week_r18_dry_run(self, runner, mock_config):
        """测试 week_r18 排行榜 (--dry-run 模式)

        验证点:
        1. week_r18 mode 正常工作
        2. 没有 Invalid mode 错误
        """
        result = runner.invoke(
            download,
            ["--type", "week_r18", "--dry-run", "--limit", "5"],
            obj=mock_config,
        )

        assert result.exit_code == 0, f"命令执行失败: {result.output}"
        assert "Invalid mode" not in result.output
        assert "Invalid ranking type" not in result.output

        output_data = json.loads(result.output)
        assert output_data.get("success") is True

    @pytest.mark.integration
    @pytest.mark.slow
    @requires_auth
    def test_week_r18g_dry_run(self, runner, mock_config):
        """测试 week_r18g 排行榜 (--dry-run 模式)

        验证点:
        1. week_r18g mode 正常工作
        2. 没有 Invalid mode 错误
        """
        result = runner.invoke(
            download,
            ["--type", "week_r18g", "--dry-run", "--limit", "5"],
            obj=mock_config,
        )

        assert result.exit_code == 0, f"命令执行失败: {result.output}"
        assert "Invalid mode" not in result.output
        assert "Invalid ranking type" not in result.output

        output_data = json.loads(result.output)
        assert output_data.get("success") is True

    @pytest.mark.integration
    @pytest.mark.slow
    @requires_auth
    def test_all_r18_modes_with_date(self, runner, mock_config):
        """测试所有 R18 mode 带日期参数

        验证 R18 mode 可以正确处理日期参数,且没有 Invalid mode 错误。
        """
        r18_modes = [
            "day_r18",
            "day_male_r18",
            "day_female_r18",
            "week_r18",
            "week_r18g",
        ]

        for mode in r18_modes:
            result = runner.invoke(
                download,
                ["--type", mode, "--date", "2024-03-01", "--dry-run", "--limit", "3"],
                obj=mock_config,
            )

            # 验证每个 mode 都成功，且无 Invalid mode 错误
            assert result.exit_code == 0, f"Mode '{mode}' 执行失败: {result.output}"
            assert "Invalid mode" not in result.output, f"Mode '{mode}' 报 Invalid mode 错误"
            assert "Invalid ranking type" not in result.output, f"Mode '{mode}' 报 Invalid ranking type 错误"

            output_data = json.loads(result.output)
            assert output_data.get("success") is True, f"Mode '{mode}' 应该成功"


class TestBasicRankingBackwardCompatibility:
    """测试基础排行榜的向后兼容性"""

    @pytest.mark.integration
    @pytest.mark.slow
    @requires_auth
    def test_day_mode_still_works(self, runner, mock_config):
        """测试 day mode 向后兼容性

        验证基础 mode (day) 仍然正常工作。
        """
        result = runner.invoke(
            download,
            ["--type", "day", "--dry-run", "--limit", "3"],
            obj=mock_config,
        )

        assert result.exit_code == 0, f"day mode 执行失败: {result.output}"
        assert "Invalid mode" not in result.output
        assert "Invalid ranking type" not in result.output

        output_data = json.loads(result.output)
        assert output_data.get("success") is True

    @pytest.mark.integration
    @pytest.mark.slow
    @requires_auth
    def test_cli_friendly_names(self, runner, mock_config):
        """测试 CLI 友好名称

        验证 CLI 友好名称 (如 daily, weekly) 仍然工作,且没有 Invalid mode 错误。
        """
        test_cases = [
            ("daily", "day"),
            ("weekly", "week"),
            ("monthly", "month"),
        ]

        for cli_name, api_name in test_cases:
            result = runner.invoke(
                download,
                ["--type", cli_name, "--dry-run", "--limit", "3"],
                obj=mock_config,
            )

            assert result.exit_code == 0, f"CLI name '{cli_name}' 执行失败: {result.output}"
            assert "Invalid mode" not in result.output
            assert "Invalid ranking type" not in result.output

            output_data = json.loads(result.output)
            assert output_data.get("success") is True


class TestErrorHandling:
    """测试错误处理"""

    @pytest.mark.integration
    def test_invalid_mode_error(self, runner, mock_config):
        """测试无效 mode 的错误处理

        验证传入无效 mode 时返回清晰的错误信息。
        """
        result = runner.invoke(
            download,
            ["--type", "invalid_mode", "--dry-run"],
            obj=mock_config,
        )

        # 应该返回非零退出码
        assert result.exit_code != 0, "无效 mode 应该返回错误"

        # 错误信息应包含有效 mode 列表
        assert "Invalid ranking type" in result.output or "Invalid mode" in result.output

    @pytest.mark.integration
    def test_future_date_error(self, runner, mock_config):
        """测试未来日期错误

        验证未来日期被正确拒绝。
        """
        result = runner.invoke(
            download,
            ["--type", "day", "--date", "2099-12-31", "--dry-run"],
            obj=mock_config,
        )

        # 应该返回非零退出码
        assert result.exit_code != 0, "未来日期应该返回错误"
        assert "future" in result.output.lower() or "未来" in result.output

    @pytest.mark.integration
    def test_invalid_date_format_error(self, runner, mock_config):
        """测试无效日期格式错误

        验证无效日期格式被正确拒绝。
        """
        result = runner.invoke(
            download,
            ["--type", "day", "--date", "2024/03/01", "--dry-run"],
            obj=mock_config,
        )

        # 应该返回非零退出码
        assert result.exit_code != 0, "无效日期格式应该返回错误"
        assert "Invalid date" in result.output or "格式" in result.output


class TestAPIModeDirectInput:
    """测试 API mode 名称的直接输入"""

    @pytest.mark.integration
    @pytest.mark.slow
    @requires_auth
    def test_api_mode_day_male_r18(self, runner, mock_config):
        """测试直接使用 API mode 'day_male_r18'

        验证用户可以直接输入 API mode 名称,且没有 Invalid mode 错误。
        """
        result = runner.invoke(
            download,
            ["--type", "day_male_r18", "--dry-run", "--limit", "3"],
            obj=mock_config,
        )

        assert result.exit_code == 0, f"命令执行失败: {result.output}"
        assert "Invalid mode" not in result.output
        assert "Invalid ranking type" not in result.output

        output_data = json.loads(result.output)
        assert output_data.get("success") is True

    @pytest.mark.integration
    @pytest.mark.slow
    @requires_auth
    def test_api_mode_day_female_r18(self, runner, mock_config):
        """测试直接使用 API mode 'day_female_r18'"""
        result = runner.invoke(
            download,
            ["--type", "day_female_r18", "--dry-run", "--limit", "3"],
            obj=mock_config,
        )

        assert result.exit_code == 0, f"命令执行失败: {result.output}"
        assert "Invalid mode" not in result.output
        assert "Invalid ranking type" not in result.output

        output_data = json.loads(result.output)
        assert output_data.get("success") is True


class TestDryRunOutput:
    """测试 --dry-run 输出格式"""

    @pytest.mark.integration
    @pytest.mark.slow
    @requires_auth
    def test_dry_run_json_structure(self, runner, mock_config):
        """测试 --dry-run JSON 输出结构

        验证 --dry-run 输出包含基本的 success 字段。
        """
        result = runner.invoke(
            download,
            ["--type", "day_r18", "--dry-run", "--limit", "3"],
            obj=mock_config,
        )

        assert result.exit_code == 0
        output_data = json.loads(result.output)

        # 验证基本字段
        assert "success" in output_data, "缺少 success 字段"
        assert output_data["success"] is True

    @pytest.mark.integration
    @pytest.mark.slow
    @requires_auth
    def test_dry_run_with_limit_and_offset(self, runner, mock_config):
        """测试 --dry-run 与 --limit 和 --offset 的组合

        验证 --limit 和 --offset 参数不会导致 Invalid mode 错误。
        """
        result = runner.invoke(
            download,
            ["--type", "day_r18", "--dry-run", "--limit", "10", "--offset", "5"],
            obj=mock_config,
        )

        assert result.exit_code == 0
        assert "Invalid mode" not in result.output
        assert "Invalid ranking type" not in result.output

        output_data = json.loads(result.output)
        assert output_data.get("success") is True


class TestGalleryDLEngine:
    """测试 gallery-dl 引擎的 R18 支持"""

    @pytest.mark.integration
    @pytest.mark.slow
    @requires_auth
    def test_gallery_dl_engine_day_r18(self, runner, mock_config):
        """测试 gallery-dl 引擎处理 day_r18

        验证 gallery-dl 引擎可以处理 R18 mode。
        """
        result = runner.invoke(
            download,
            ["--type", "day_r18", "--engine", "gallery-dl", "--dry-run", "--limit", "3"],
            obj=mock_config,
        )

        assert result.exit_code == 0, f"gallery-dl 引擎执行失败: {result.output}"
        assert "Invalid mode" not in result.output

        output_data = json.loads(result.output)
        assert output_data.get("success") is True or output_data.get("dry_run") is True

    @pytest.mark.integration
    @pytest.mark.slow
    @requires_auth
    def test_gallery_dl_engine_all_r18_modes(self, runner, mock_config):
        """测试 gallery-dl 引擎处理所有 R18 mode"""
        r18_modes = [
            "day_r18",
            "day_male_r18",
            "day_female_r18",
            "week_r18",
            "week_r18g",
        ]

        for mode in r18_modes:
            result = runner.invoke(
                download,
                ["--type", mode, "--engine", "gallery-dl", "--dry-run", "--limit", "3"],
                obj=mock_config,
            )

            assert result.exit_code == 0, f"gallery-dl 引擎处理 {mode} 失败"
            assert "Invalid mode" not in result.output, f"{mode} 不应报 Invalid mode 错误"
