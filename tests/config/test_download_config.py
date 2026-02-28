"""测试下载配置模型

测试 DownloadConfig 的验证和序列化功能。
"""

import pytest
from gallery_dl_auto.config.download_config import DownloadConfig


def test_default_config():
    """测试默认配置"""
    config = DownloadConfig()
    assert config.batch_size == 30
    assert config.batch_delay == 2.0
    assert config.concurrency == 1
    assert config.image_delay == 2.5
    assert config.max_retries == 3
    assert config.retry_delay == 5.0


def test_custom_config():
    """测试自定义配置"""
    config = DownloadConfig(
        batch_size=50,
        batch_delay=1.5,
        image_delay=3.0
    )
    assert config.batch_size == 50
    assert config.batch_delay == 1.5
    assert config.image_delay == 3.0


def test_invalid_batch_size():
    """测试无效的批次大小"""
    with pytest.raises(ValueError):
        DownloadConfig(batch_size=0)

    with pytest.raises(ValueError):
        DownloadConfig(batch_size=101)


def test_invalid_concurrency():
    """测试无效的并发数"""
    with pytest.raises(ValueError):
        DownloadConfig(concurrency=0)

    with pytest.raises(ValueError):
        DownloadConfig(concurrency=11)


def test_negative_delay():
    """测试负延迟"""
    with pytest.raises(ValueError):
        DownloadConfig(image_delay=-1.0)

    with pytest.raises(ValueError):
        DownloadConfig(batch_delay=-0.5)


def test_invalid_retry_params():
    """测试无效的重试参数"""
    with pytest.raises(ValueError):
        DownloadConfig(max_retries=0)

    with pytest.raises(ValueError):
        DownloadConfig(max_retries=11)

    with pytest.raises(ValueError):
        DownloadConfig(retry_delay=-1.0)


def test_extra_fields_forbidden():
    """测试禁止额外字段"""
    with pytest.raises(ValueError):
        DownloadConfig(unknown_field="value")
