"""配置加载器测试"""

import pytest
from gallery_dl_auto.config.loader import load_and_validate_config
from gallery_dl_auto.config.schema import AppConfig
from omegaconf import DictConfig


def test_load_valid_config(sample_config: DictConfig) -> None:
    """测试加载有效配置"""
    config = load_and_validate_config(sample_config)
    assert isinstance(config, AppConfig)
    assert config.concurrent_downloads == 3


def test_validate_concurrent_downloads_too_low(sample_config: DictConfig) -> None:
    """测试并发数过低验证"""
    sample_config.concurrent_downloads = 0
    with pytest.raises(ValueError) as exc_info:
        load_and_validate_config(sample_config)
    assert "concurrent_downloads" in str(exc_info.value)


def test_validate_request_interval_too_low(sample_config: DictConfig) -> None:
    """测试请求间隔过低验证"""
    sample_config.request_interval = 0.1
    with pytest.raises(ValueError) as exc_info:
        load_and_validate_config(sample_config)
    assert "request_interval" in str(exc_info.value)


def test_validate_invalid_log_level(sample_config: DictConfig) -> None:
    """测试无效日志级别验证"""
    sample_config.log_level = "INVALID"
    with pytest.raises(ValueError) as exc_info:
        load_and_validate_config(sample_config)
    assert "log_level" in str(exc_info.value)
