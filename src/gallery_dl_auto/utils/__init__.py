"""工具函数模块

提供文件名清理、错误码等通用工具函数。
"""

from gallery_dl_auto.utils.error_codes import ErrorCode
from gallery_dl_auto.utils.filename_sanitizer import sanitize_filename

__all__ = ["ErrorCode", "sanitize_filename"]
