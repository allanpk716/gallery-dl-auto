"""配置加载和验证

实现配置加载和验证逻辑,使用 OmegaConf 进行类型转换和验证。
"""

from omegaconf import DictConfig, OmegaConf

from gallery_dl_auto.config.schema import AppConfig


def load_and_validate_config(cfg: DictConfig) -> AppConfig:
    """加载并验证配置

    Args:
        cfg: Hydra 加载的 DictConfig 对象

    Returns:
        AppConfig: 验证后的配置对象

    Raises:
        ValueError: 配置验证失败
    """
    # 转换为 dataclass 对象,触发类型验证
    config: AppConfig = OmegaConf.to_object(cfg)

    # 自定义验证逻辑
    if config.concurrent_downloads < 1:
        raise ValueError(
            "concurrent_downloads 必须大于 0\n" "建议值: 3-5(避免触发 pixiv 反爬虫)"
        )

    if config.request_interval < 0.5:
        raise ValueError(
            "request_interval 不能小于 0.5 秒\n"
            "建议值: 1.0-2.0 秒(避免触发 pixiv 反爬虫)"
        )

    if config.log_level.upper() not in [
        "DEBUG",
        "INFO",
        "WARNING",
        "ERROR",
        "CRITICAL",
    ]:
        raise ValueError(
            f"log_level 必须是以下值之一: DEBUG, INFO, WARNING, ERROR, CRITICAL\n"
            f"当前值: {config.log_level}"
        )

    return config
