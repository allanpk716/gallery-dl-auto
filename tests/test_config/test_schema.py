"""配置 schema 测试"""

from gallery_dl_auto.config.schema import AppConfig


def test_app_config_defaults() -> None:
    """测试配置默认值"""
    config = AppConfig()
    assert config.save_path == "./downloads"
    assert config.concurrent_downloads == 3
    assert config.request_interval == 1.0
    assert config.log_level == "INFO"
    assert config.api_timeout == 30
    assert config.max_retries == 3


def test_app_config_custom_values() -> None:
    """测试自定义配置值"""
    config = AppConfig(
        save_path="/custom/path", concurrent_downloads=5, log_level="DEBUG"
    )
    assert config.save_path == "/custom/path"
    assert config.concurrent_downloads == 5
    assert config.log_level == "DEBUG"
