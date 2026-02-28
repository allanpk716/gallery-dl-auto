"""文件下载器

使用 requests 实现流式文件下载,避免内存溢出。
使用原子文件操作保证下载完整性。
"""

import logging
from pathlib import Path
from typing import Any

import requests

from gallery_dl_auto.download.retry_handler import retry_on_file_error, retry_on_network_error
from gallery_dl_auto.models.error_response import ErrorSeverity, StructuredError
from gallery_dl_auto.utils.error_codes import ErrorCode

logger = logging.getLogger("gallery_dl_auto")


def download_file(
    url: str,
    filepath: Path,
    illust_id: int,
    timeout: int = 30,
    chunk_size: int = 8192,
) -> dict[str, Any] | StructuredError:
    """流式下载文件,避免内存溢出,使用原子文件操作。

    Args:
        url: 图片 URL
        filepath: 保存路径 (Path 对象)
        illust_id: 作品 ID (用于错误报告)
        timeout: 超时秒数 (默认 30)
        chunk_size: 分块大小 (默认 8192 字节)

    Returns:
        成功时返回 dict: {'success': True, 'filepath': str, 'size': int}
        失败时返回 StructuredError 对象

    Note:
        - 使用临时文件 + 重命名保证原子性
        - 网络错误和文件错误都会自动重试 3 次
        - Windows 兼容:重命名前先删除目标文件(如果存在)
        - 重试失败后返回 StructuredError 而非抛出异常

    Examples:
        >>> result = download_file(
        ...     "https://example.com/image.jpg",
        ...     Path("./downloads/image.jpg"),
        ...     illust_id=12345
        ... )
        >>> if isinstance(result, dict) and result['success']:
        ...     print(f"Downloaded to {result['filepath']}")
    """
    try:
        # 调用带重试的内部下载函数
        file_size = _download_file_with_retry(url, filepath, timeout, chunk_size)
        return {
            "success": True,
            "filepath": str(filepath),
            "size": file_size,
        }

    except requests.exceptions.Timeout as e:
        return StructuredError(
            error_code=ErrorCode.DOWNLOAD_TIMEOUT,
            error_type="TimeoutError",
            message=f"下载超时:作品 {illust_id}",
            suggestion="检查网络连接或稍后重试",
            severity=ErrorSeverity.WARNING,
            illust_id=illust_id,
            original_error=str(e),
        )

    except requests.exceptions.HTTPError as e:
        # 检测 429 速率限制错误
        if e.response.status_code == 429:
            logger.error(f"Rate limit exceeded (HTTP 429) for illust {illust_id}")
            return StructuredError(
                error_code=ErrorCode.RATE_LIMIT_EXCEEDED,
                error_type="RateLimitError",
                message="Pixiv API 速率限制触发 (HTTP 429)",
                suggestion=(
                    "建议增加延迟参数以避免触发反爬虫机制:\n"
                    "  --image-delay 5.0  (当前: 2.5s)\n"
                    "  --batch-delay 4.0  (当前: 2.0s)"
                ),
                severity=ErrorSeverity.ERROR,
                illust_id=illust_id,
            )

        # 其他 HTTP 错误
        return StructuredError(
            error_code=ErrorCode.API_SERVER_ERROR,
            error_type="HTTPError",
            message=f"HTTP 错误 {e.response.status_code}:作品 {illust_id}",
            suggestion="服务器返回错误,请稍后重试",
            severity=ErrorSeverity.WARNING,
            illust_id=illust_id,
            original_error=str(e),
        )

    except requests.exceptions.ConnectionError as e:
        return StructuredError(
            error_code=ErrorCode.DOWNLOAD_FAILED,
            error_type="NetworkError",
            message=f"网络连接失败:作品 {illust_id}",
            suggestion="检查网络连接,错误将持续重试 3 次",
            severity=ErrorSeverity.WARNING,
            illust_id=illust_id,
            original_error=str(e),
        )

    except PermissionError as e:
        return StructuredError(
            error_code=ErrorCode.DOWNLOAD_PERMISSION_DENIED,
            error_type="PermissionError",
            message=f"无法写入文件:{filepath.name}",
            suggestion="检查目录权限或以管理员身份运行",
            severity=ErrorSeverity.ERROR,
            illust_id=illust_id,
            original_error=str(e),
        )

    except OSError as e:
        return StructuredError(
            error_code=ErrorCode.FILE_DISK_FULL,
            error_type="OSError",
            message=f"文件操作失败:{filepath.name}",
            suggestion="检查磁盘空间或文件路径",
            severity=ErrorSeverity.ERROR,
            illust_id=illust_id,
            original_error=str(e),
        )

    except Exception as e:
        return StructuredError(
            error_code=ErrorCode.INTERNAL_ERROR,
            error_type="InternalError",
            message=f"下载失败:作品 {illust_id}",
            suggestion="未知错误,请联系开发者",
            severity=ErrorSeverity.ERROR,
            illust_id=illust_id,
            original_error=str(e),
        )


@retry_on_network_error
@retry_on_file_error
def _download_file_with_retry(
    url: str,
    filepath: Path,
    timeout: int,
    chunk_size: int,
) -> int:
    """内部下载函数(带重试装饰器)

    Args:
        url: 图片 URL
        filepath: 保存路径
        timeout: 超时秒数
        chunk_size: 分块大小

    Returns:
        文件大小(字节)

    Raises:
        网络错误或文件错误,由装饰器自动重试
    """
    # 使用临时文件路径
    temp_filepath = filepath.with_suffix(filepath.suffix + ".tmp")

    try:
        # 确保父目录存在
        filepath.parent.mkdir(parents=True, exist_ok=True)

        # 流式下载到临时文件
        with requests.get(url, stream=True, timeout=timeout) as response:
            response.raise_for_status()

            file_size = 0
            with open(temp_filepath, "wb") as f:
                for chunk in response.iter_content(chunk_size=chunk_size):
                    if chunk:  # 过滤保持连接的新块
                        f.write(chunk)
                        file_size += len(chunk)

        # 原子重命名:临时文件 → 目标文件
        # Windows 兼容:如果目标文件存在,先删除
        if filepath.exists():
            filepath.unlink()

        temp_filepath.rename(filepath)
        logger.info(f"Successfully downloaded: {filepath}")
        return file_size

    except Exception:
        # 清理临时文件
        _cleanup_temp_file(temp_filepath)
        raise  # 触发重试


def _cleanup_temp_file(temp_filepath: Path) -> None:
    """清理临时文件

    Args:
        temp_filepath: 临时文件路径
    """
    try:
        if temp_filepath.exists():
            temp_filepath.unlink()
    except Exception as e:
        logger.warning(f"Failed to cleanup temp file {temp_filepath}: {e}")
