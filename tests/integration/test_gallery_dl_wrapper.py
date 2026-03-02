"""集成测试：GalleryDLWrapper 与 ModeManager 集成

测试 gallery_dl_wrapper 使用 ModeManager 的集成情况。
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch
import tempfile

from gallery_dl_auto.config.download_config import DownloadConfig
from gallery_dl_auto.integration.gallery_dl_wrapper import GalleryDLWrapper
from gallery_dl_auto.core.mode_errors import InvalidModeError


class TestGalleryDLWrapperModeIntegration:
    """测试 GalleryDLWrapper 的 Mode 集成"""

    @pytest.fixture
    def mock_config(self, tmp_path):
        """创建模拟配置"""
        config = Mock(spec=DownloadConfig)
        config.output_dir = tmp_path / "downloads"
        config.output_dir.mkdir(parents=True, exist_ok=True)
        return config

    @pytest.fixture
    def wrapper(self, mock_config):
        """创建 GalleryDLWrapper 实例"""
        # Mock token storage
        with patch(
            "gallery_dl_auto.integration.gallery_dl_wrapper.get_default_token_storage"
        ) as mock_storage:
            mock_storage.return_value = Mock()
            wrapper = GalleryDLWrapper(mock_config)
            return wrapper

    def test_build_ranking_url_day_male_r18(self, wrapper):
        """测试 day_male_r18 的 URL 构建

        验证点：
        1. API mode 'day_male_r18' 转换为 gallery-dl mode 'male_r18'
        2. URL 中包含正确的 mode 参数
        """
        url = wrapper._build_ranking_url("day_male_r18", "2024-03-01")

        # 关键验证：URL 应该是 mode=male_r18 而不是 mode=day_male_r18
        assert "mode=male_r18" in url, f"URL 应包含 mode=male_r18，实际为: {url}"
        assert "mode=day_male_r18" not in url
        assert "date=2024-03-01" in url
        assert "content=illust" in url

    def test_build_ranking_url_basic_modes(self, wrapper):
        """测试基础 mode 的 URL 构建

        验证基础 mode 的转换是否正确。
        """
        test_cases = [
            ("day", "daily", "每日排行榜"),
            ("week", "weekly", "每周排行榜"),
            ("month", "monthly", "每月排行榜"),
        ]

        for api_mode, expected_gdl_mode, description in test_cases:
            url = wrapper._build_ranking_url(api_mode, None)
            assert (
                f"mode={expected_gdl_mode}" in url
            ), f"{description}: 期望 mode={expected_gdl_mode}，实际 URL: {url}"
            assert "date=" not in url  # 无日期参数

    def test_build_ranking_url_all_r18_modes(self, wrapper):
        """测试所有 R18 mode 的 URL 构建

        验证所有 R18 mode 的转换。
        """
        test_cases = [
            ("day_r18", "daily_r18"),
            ("day_male_r18", "male_r18"),
            ("day_female_r18", "female_r18"),
            ("week_r18", "weekly_r18"),
            ("week_r18g", "r18g"),
        ]

        for api_mode, expected_gdl_mode in test_cases:
            url = wrapper._build_ranking_url(api_mode, "2024-03-01")
            assert (
                f"mode={expected_gdl_mode}" in url
            ), f"API mode '{api_mode}' 应转换为 '{expected_gdl_mode}'，实际 URL: {url}"

    def test_build_ranking_url_other_modes(self, wrapper):
        """测试其他分类 mode 的 URL 构建"""
        test_cases = [
            ("day_male", "male"),
            ("day_female", "female"),
            ("week_original", "original"),
            ("week_rookie", "rookie"),
        ]

        for api_mode, expected_gdl_mode in test_cases:
            url = wrapper._build_ranking_url(api_mode, None)
            assert (
                f"mode={expected_gdl_mode}" in url
            ), f"API mode '{api_mode}' 应转换为 '{expected_gdl_mode}'，实际 URL: {url}"

    def test_build_ranking_url_invalid_mode(self, wrapper):
        """测试无效 mode 的错误处理

        验证传入无效 mode 时是否抛出 InvalidModeError。
        """
        invalid_modes = ["invalid", "day_r19", "unknown", ""]

        for invalid_mode in invalid_modes:
            with pytest.raises(InvalidModeError) as exc_info:
                wrapper._build_ranking_url(invalid_mode, None)

            # 验证错误信息包含有效 mode 列表
            error_msg = str(exc_info.value)
            assert "Invalid mode" in error_msg or "无效的排行榜 mode" in error_msg
            assert invalid_mode in error_msg

    def test_build_ranking_url_with_date(self, wrapper):
        """测试带日期的 URL 构建"""
        url = wrapper._build_ranking_url("day", "2024-03-01")

        assert "mode=daily" in url
        assert "date=2024-03-01" in url
        assert "content=illust" in url

    def test_build_ranking_url_without_date(self, wrapper):
        """测试不带日期的 URL 构建"""
        url = wrapper._build_ranking_url("day", None)

        assert "mode=daily" in url
        assert "date=" not in url
        assert "content=illust" in url

    def test_mode_manager_integration_in_download_ranking(self, wrapper):
        """测试 ModeManager 在 download_ranking 方法中的集成

        验证完整下载流程中 ModeManager 的使用。
        """
        # Mock token
        wrapper.token_bridge.get_refresh_token = Mock(return_value="mock_token")

        # Mock gallery-dl 命令执行
        with patch("subprocess.run") as mock_run:
            mock_run.return_value = Mock(
                returncode=0,
                stdout="",
                stderr="",
            )

            # 调用 download_ranking 会触发 _build_ranking_url
            result = wrapper.download_ranking(
                mode="day_male_r18",
                date="2024-03-01",
                output_dir=Path(tempfile.mkdtemp()),
                dry_run=True,
            )

            # 验证命令被调用
            assert mock_run.called

            # 提取实际调用的 URL
            call_args = mock_run.call_args
            cmd = call_args[0][0]  # 第一个位置参数是命令列表

            # 验证 URL 包含正确的 mode
            url = cmd[-1]  # 最后一个参数是 URL
            assert "mode=male_r18" in url, f"URL 应包含 mode=male_r18，实际为: {url}"
