"""路径配置模块

定义项目中使用的路径常量,包括用户配置目录和凭证文件路径。
"""

from pathlib import Path

# 用户配置目录 (~/.gallery-dl-auto/)
USER_CONFIG_DIR = Path.home() / ".gallery-dl-auto"

# Token 加密存储路径
CREDENTIALS_FILE = USER_CONFIG_DIR / "credentials.enc"


def get_user_config_dir() -> Path:
    """获取用户配置目录路径

    如果目录不存在,则自动创建。

    Returns:
        Path: 用户配置目录的 Path 对象
    """
    USER_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    return USER_CONFIG_DIR


def get_download_db_path() -> Path:
    """获取下载历史数据库路径

    Returns:
        Path: 下载历史数据库的 Path 对象
    """
    return USER_CONFIG_DIR / "downloads.db"


def get_config_dir() -> Path:
    """获取配置目录路径(别名)

    Returns:
        Path: 配置目录的 Path 对象
    """
    return get_user_config_dir()


def get_log_file_path() -> Path:
    """获取日志文件路径

    Returns:
        Path: ~/.gallery-dl-auto/logs/gallery-dl-auto.log
    """
    log_dir = get_config_dir() / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)
    return log_dir / "gallery-dl-auto.log"
