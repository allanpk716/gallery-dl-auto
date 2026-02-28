"""下载模块

提供文件下载、速率控制和文件名清理功能。
"""

from gallery_dl_auto.download.file_downloader import download_file
from gallery_dl_auto.download.rate_limiter import rate_limit_delay

__all__ = ["download_file", "rate_limit_delay"]
