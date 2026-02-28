"""重试处理器

使用 Tenacity 库实现生产级别的指数退避重试策略。
"""

import logging
from typing import TypeVar

import tenacity
from requests.exceptions import RequestException
from tenacity import (
    before_sleep_log,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

logger = logging.getLogger("gallery_dl_auto")

T = TypeVar("T")


def retry_on_network_error(func: T) -> T:
    """网络错误重试装饰器

    自动重试网络请求失败的操作,使用指数退避策略(1秒、2秒、3秒)。

    Args:
        func: 要装饰的函数

    Returns:
        装饰后的函数

    Retry Strategy:
        - 最大重试次数: 3
        - 退避策略: 指数退避 (1s → 2s → 3s)
        - 重试条件: requests.RequestException

    Example:
        >>> @retry_on_network_error
        ... def fetch_data():
        ...     return requests.get("https://api.example.com")
    """
    return retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=3),
        retry=retry_if_exception_type(RequestException),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True,
    )(func)


def retry_on_file_error(func: T) -> T:
    """文件操作错误重试装饰器

    自动重试文件操作失败的操作,使用指数退避策略(1秒、2秒、3秒)。

    Args:
        func: 要装饰的函数

    Returns:
        装饰后的函数

    Retry Strategy:
        - 最大重试次数: 3
        - 退避策略: 指数退避 (1s → 2s → 3s)
        - 重试条件: IOError, PermissionError, OSError

    Example:
        >>> @retry_on_file_error
        ... def write_file(path, content):
        ...     with open(path, 'w') as f:
        ...         f.write(content)
    """
    return retry(
        stop=stop_after_attempt(3),
        wait=wait_exponential(multiplier=1, min=1, max=3),
        retry=retry_if_exception_type((IOError, PermissionError, OSError)),
        before_sleep=before_sleep_log(logger, logging.WARNING),
        reraise=True,
    )(func)


def retry_download_file(
    download_func: tenacity.Callable[[], dict],
    max_retries: int = 3,
    retry_delay: float = 5.0,
) -> dict:
    """重试文件下载

    专门用于文件下载的重试包装器,处理返回 dict 的下载函数。
    使用 Tenacity 装饰器实现自动重试。

    Args:
        download_func: 下载函数,返回 {'success': bool, 'error': str, ...}
        max_retries: 最大重试次数 (默认 3)
        retry_delay: 重试间隔秒数 (已弃用,使用指数退避)

    Returns:
        下载结果字典 {'success': bool, 'error': str, ...}

    Note:
        如果所有重试都失败,返回最后一次的错误结果,不抛出异常

    Example:
        >>> result = retry_download_file(
        ...     lambda: download_image(url, path),
        ...     max_retries=3
        ... )
    """
    # 使用装饰器包装函数
    @retry_on_file_error
    def wrapped_download() -> dict:
        return download_func()

    try:
        result = wrapped_download()
        if result.get("success"):
            return result
        else:
            # 下载函数返回失败但不抛出异常
            logger.error(f"Download failed: {result.get('error', 'Unknown error')}")
            result["retries_exhausted"] = True
            return result
    except (IOError, PermissionError, OSError) as e:
        # 文件操作异常
        error_msg = f"File operation failed after {max_retries} retries: {e}"
        logger.error(error_msg)
        return {
            "success": False,
            "error": error_msg,
            "retries_exhausted": True,
        }
    except Exception as e:
        # 其他异常
        error_msg = f"Download failed: {e}"
        logger.error(error_msg)
        return {
            "success": False,
            "error": error_msg,
            "retries_exhausted": True,
        }
