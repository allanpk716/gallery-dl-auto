"""pytest 共享 fixture 和配置"""

import pytest
from click.testing import CliRunner
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
