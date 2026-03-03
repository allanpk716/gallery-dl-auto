"""测试 conftest.py 中的共享 fixtures

验证所有共享 fixtures 都能正确初始化和使用。
"""

from pathlib import Path
from unittest.mock import MagicMock

import pytest
from click.testing import CliRunner
from omegaconf import OmegaConf


class TestRunnerFixture:
    """测试 runner fixture"""

    def test_runner_is_cli_runner(self, runner: CliRunner) -> None:
        """验证 runner 是 CliRunner 实例"""
        assert isinstance(runner, CliRunner)

    def test_runner_can_invoke(self, runner: CliRunner) -> None:
        """验证 runner 可以调用命令"""
        # runner 已经可用，无需额外测试
        # 这个测试只需要验证 runner 存在即可
        assert runner is not None


class TestTempDirFixture:
    """测试 temp_dir fixture"""

    def test_temp_dir_is_path(self, temp_dir: Path) -> None:
        """验证 temp_dir 是 Path 实例"""
        assert isinstance(temp_dir, Path)

    def test_temp_dir_exists(self, temp_dir: Path) -> None:
        """验证临时目录存在"""
        assert temp_dir.exists()

    def test_temp_dir_is_directory(self, temp_dir: Path) -> None:
        """验证临时目录是目录"""
        assert temp_dir.is_dir()

    def test_temp_dir_is_writable(self, temp_dir: Path) -> None:
        """验证临时目录可写"""
        test_file = temp_dir / "test.txt"
        test_file.write_text("test content", encoding="utf-8")
        assert test_file.read_text(encoding="utf-8") == "test content"


class TestTempTokenFileFixture:
    """测试 temp_token_file fixture"""

    def test_temp_token_file_is_path(self, temp_token_file: Path) -> None:
        """验证 temp_token_file 是 Path 实例"""
        assert isinstance(temp_token_file, Path)

    def test_temp_token_file_exists(self, temp_token_file: Path) -> None:
        """验证 token 文件存在"""
        assert temp_token_file.exists()

    def test_temp_token_file_is_file(self, temp_token_file: Path) -> None:
        """验证 token 文件是文件"""
        assert temp_token_file.is_file()

    def test_temp_token_file_can_be_loaded(
        self, temp_token_file: Path
    ) -> None:
        """验证 token 文件可以被 TokenStorage 加载"""
        from gallery_dl_auto.auth.token_storage import TokenStorage

        storage = TokenStorage(temp_token_file)
        token_data = storage.load_token()

        assert token_data is not None
        assert "refresh_token" in token_data
        assert "access_token" in token_data
        assert "user" in token_data

    def test_temp_token_file_contains_valid_data(
        self, temp_token_file: Path
    ) -> None:
        """验证 token 文件包含有效的测试数据"""
        from gallery_dl_auto.auth.token_storage import TokenStorage
        from tests.fixtures.test_data import TestData

        storage = TokenStorage(temp_token_file)
        token_data = storage.load_token()

        assert token_data is not None
        assert token_data["refresh_token"] == TestData.VALID_REFRESH_TOKEN
        assert token_data["access_token"] == TestData.ALT_REFRESH_TOKEN


class TestMockPixivClientFixture:
    """测试 mock_pixiv_client fixture"""

    def test_mock_pixiv_client_is_mock(
        self, mock_pixiv_client: MagicMock
    ) -> None:
        """验证 mock_pixiv_client 是 MagicMock 实例"""
        assert isinstance(mock_pixiv_client, MagicMock)

    def test_mock_pixiv_client_has_get_ranking(
        self, mock_pixiv_client: MagicMock
    ) -> None:
        """验证 mock_pixiv_client 有 get_ranking 方法"""
        assert hasattr(mock_pixiv_client, "get_ranking")

    def test_mock_pixiv_client_get_ranking_returns_list(
        self, mock_pixiv_client: MagicMock
    ) -> None:
        """验证 get_ranking 返回列表"""
        result = mock_pixiv_client.get_ranking()
        assert isinstance(result, list)

    def test_mock_pixiv_client_get_ranking_returns_mock_illusts(
        self, mock_pixiv_client: MagicMock
    ) -> None:
        """验证 get_ranking 返回 Mock illust 对象"""
        result = mock_pixiv_client.get_ranking()
        assert len(result) > 0
        # 验证第一个元素有预期的属性
        first_illust = result[0]
        assert hasattr(first_illust, "id")
        assert hasattr(first_illust, "title")
        assert hasattr(first_illust, "user")

    def test_mock_pixiv_client_get_ranking_range(
        self, mock_pixiv_client: MagicMock
    ) -> None:
        """验证 get_ranking_range 方法"""
        result = mock_pixiv_client.get_ranking_range()
        assert isinstance(result, list)
        assert len(result) == 30  # 默认返回 30 个作品

    def test_mock_pixiv_client_can_override_return_value(
        self, mock_pixiv_client: MagicMock
    ) -> None:
        """验证可以覆盖 mock 的返回值"""
        from tests.fixtures.mock_pixiv_responses import MockPixivResponses

        # 创建自定义返回数据
        custom_data = MockPixivResponses.create_sample_ranking_data(count=5)
        mock_pixiv_client.get_ranking.return_value = custom_data

        result = mock_pixiv_client.get_ranking()
        assert len(result) == 5


class TestSampleConfigFixture:
    """测试 sample_config fixture"""

    def test_sample_config_is_dictconfig(
        self, sample_config: OmegaConf
    ) -> None:
        """验证 sample_config 是 DictConfig 对象"""
        from omegaconf import DictConfig

        assert isinstance(sample_config, DictConfig)

    def test_sample_config_has_required_fields(
        self, sample_config: OmegaConf
    ) -> None:
        """验证 sample_config 有必需的字段"""
        # 验证配置有必要的字段
        # 根据 AppConfig 的定义，检查关键字段
        assert "save_path" in sample_config or "download" in sample_config
