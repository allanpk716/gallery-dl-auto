"""配置 schema 定义

使用 dataclass 定义结构化配置,支持类型检查和默认值。
"""

from dataclasses import dataclass


@dataclass
class AppConfig:
    """应用配置 schema

    所有配置项都在这里定义,支持类型检查和默认值。
    用户可以通过 config.yaml 文件或 CLI 参数覆盖。
    """

    # 下载配置
    save_path: str = "./downloads"
    """图片保存路径"""

    concurrent_downloads: int = 3
    """并发下载数量"""

    request_interval: float = 1.0
    """请求间隔(秒),避免触发反爬虫"""

    # 日志配置
    log_level: str = "INFO"
    """日志级别: DEBUG, INFO, WARNING, ERROR, CRITICAL"""

    # 网络配置(未来使用)
    api_timeout: int = 30
    """API 请求超时时间(秒)"""

    max_retries: int = 3
    """失败重试次数"""
