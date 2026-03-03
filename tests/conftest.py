"""pytest 共享 fixture 和配置"""

from pathlib import Path
from unittest.mock import MagicMock

import pytest
from click.testing import CliRunner
from gallery_dl_auto.auth.token_storage import TokenStorage
from gallery_dl_auto.config.schema import AppConfig
from omegaconf import OmegaConf


@pytest.fixture
def runner() -> CliRunner:
    """提供 CliRunner fixture"""
    return CliRunner()


@pytest.fixture
def sample_config() -> OmegaConf:
    """提供示例配置"""
    return OmegaConf.structured(AppConfig())


@pytest.fixture
def temp_dir(tmp_path: Path) -> Path:
    """临时目录 fixture

    使用 pytest 内置的 tmp_path，提供隔离的临时目录。

    Returns:
        Path: 临时目录路径
    """
    return tmp_path


@pytest.fixture
def temp_token_file(temp_dir: Path) -> Path:
    """临时 Token 文件 fixture

    创建一个包含有效测试 token 的临时文件。
    使用 TokenStorage 加密存储。

    Args:
        temp_dir: 临时目录 fixture

    Returns:
        Path: 临时 token 文件路径
    """
    from tests.fixtures.test_data import TestData

    token_file = temp_dir / ".token"
    storage = TokenStorage(token_file)
    storage.save_token(
        refresh_token=TestData.VALID_REFRESH_TOKEN,
        access_token=TestData.ALT_REFRESH_TOKEN,
        user={"id": 12345678, "name": "TestUser", "account": "testuser"},
    )
    return token_file


@pytest.fixture
def mock_pixiv_client() -> MagicMock:
    """Mock PixivClient fixture

    创建一个 Mock 的 PixivClient 实例，预设了常见行为。
    可以在测试中根据需要覆盖返回值。

    Returns:
        MagicMock: Mock 的 PixivClient 实例
    """
    from tests.fixtures.mock_pixiv_responses import MockPixivResponses

    mock = MagicMock()

    # 设置默认行为
    mock.get_ranking.return_value = MockPixivResponses.create_sample_ranking_data(
        count=10
    )
    mock.get_ranking_range.return_value = (
        MockPixivResponses.create_sample_ranking_data(count=30)
    )

    # 设置 get_artwork_detail 的默认行为
    sample_illust = MockPixivResponses.create_mock_illust(
        illust_id=12345678, title="Test Artwork"
    )
    mock.get_artwork_detail.return_value = sample_illust

    return mock
