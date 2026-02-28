"""重试处理器单元测试

测试 Tenacity 装饰器和重试逻辑。
"""

import logging
import time
from unittest.mock import MagicMock, patch

import pytest
from requests.exceptions import ConnectionError, Timeout

from gallery_dl_auto.download.retry_handler import (
    retry_download_file,
    retry_on_file_error,
    retry_on_network_error,
)


class TestRetryOnNetworkError:
    """测试网络错误重试装饰器"""

    def test_success_first_attempt(self):
        """测试第一次成功"""
        call_count = 0

        @retry_on_network_error
        def operation():
            nonlocal call_count
            call_count += 1
            return "success"

        result = operation()
        assert result == "success"
        assert call_count == 1

    def test_retry_on_connection_error(self):
        """测试连接错误时自动重试"""
        call_count = 0

        @retry_on_network_error
        def operation():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ConnectionError("Network error")
            return "success"

        result = operation()
        assert result == "success"
        assert call_count == 3

    def test_retry_on_timeout(self):
        """测试超时错误时自动重试"""
        call_count = 0

        @retry_on_network_error
        def operation():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise Timeout("Request timeout")
            return "success"

        result = operation()
        assert result == "success"
        assert call_count == 2

    def test_all_attempts_fail(self):
        """测试所有重试都失败"""
        call_count = 0

        @retry_on_network_error
        def operation():
            nonlocal call_count
            call_count += 1
            raise ConnectionError("Persistent error")

        with pytest.raises(ConnectionError) as exc_info:
            operation()

        assert "Persistent error" in str(exc_info.value)
        assert call_count == 3  # Tenacity 默认重试 3 次

    def test_non_network_error_no_retry(self):
        """测试非网络错误不重试"""
        call_count = 0

        @retry_on_network_error
        def operation():
            nonlocal call_count
            call_count += 1
            raise ValueError("Logic error")

        with pytest.raises(ValueError):
            operation()

        assert call_count == 1  # 不重试


class TestRetryOnFileError:
    """测试文件错误重试装饰器"""

    def test_success_first_attempt(self):
        """测试第一次成功"""
        call_count = 0

        @retry_on_file_error
        def operation():
            nonlocal call_count
            call_count += 1
            return "success"

        result = operation()
        assert result == "success"
        assert call_count == 1

    def test_retry_on_ioerror(self):
        """测试 IO 错误时自动重试"""
        call_count = 0

        @retry_on_file_error
        def operation():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise IOError("Disk full")
            return "success"

        result = operation()
        assert result == "success"
        assert call_count == 3

    def test_retry_on_permission_error(self):
        """测试权限错误时自动重试"""
        call_count = 0

        @retry_on_file_error
        def operation():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise PermissionError("Access denied")
            return "success"

        result = operation()
        assert result == "success"
        assert call_count == 2

    def test_all_attempts_fail(self):
        """测试所有重试都失败"""
        call_count = 0

        @retry_on_file_error
        def operation():
            nonlocal call_count
            call_count += 1
            raise IOError("Disk error")

        with pytest.raises(IOError) as exc_info:
            operation()

        assert "Disk error" in str(exc_info.value)
        assert call_count == 3


class TestRetryDownloadFile:
    """测试文件下载重试"""

    def test_success_first_attempt(self):
        """测试第一次成功"""
        call_count = 0

        def download():
            nonlocal call_count
            call_count += 1
            return {"success": True, "filepath": "/path/to/file"}

        result = retry_download_file(download)
        assert result["success"] is True
        assert call_count == 1

    def test_success_after_ioerror(self):
        """测试 IO 错误后重试成功"""
        call_count = 0

        def download():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise IOError("Disk error")
            return {"success": True, "filepath": "/path/to/file"}

        result = retry_download_file(download)
        assert result["success"] is True
        assert call_count == 2

    def test_all_attempts_fail_with_exception(self):
        """测试所有重试都失败(异常)"""
        call_count = 0

        def download():
            nonlocal call_count
            call_count += 1
            raise IOError("Disk full")

        result = retry_download_file(download, max_retries=3)
        assert result["success"] is False
        assert result["retries_exhausted"] is True
        assert call_count == 3

    def test_all_attempts_fail_with_dict(self):
        """测试所有重试都失败(字典返回)"""
        call_count = 0

        def download():
            nonlocal call_count
            call_count += 1
            return {"success": False, "error": "Download failed"}

        result = retry_download_file(download, max_retries=2)
        assert result["success"] is False
        assert result["retries_exhausted"] is True
        assert call_count == 1  # 不抛出异常,只调用一次


class TestExponentialBackoff:
    """测试指数退避策略"""

    @patch("time.sleep")
    def test_exponential_wait_times(self, mock_sleep):
        """测试指数退避延迟(1s, 2s, 3s)"""
        call_count = 0

        @retry_on_network_error
        def operation():
            nonlocal call_count
            call_count += 1
            raise ConnectionError("Network error")

        with pytest.raises(ConnectionError):
            operation()

        # 验证调用了 3 次
        assert call_count == 3

        # 验证 sleep 被调用了 2 次(在失败后,成功前不 sleep)
        # Tenacity 在每次重试前调用 sleep
        # 第 1 次失败后 sleep(1),第 2 次失败后 sleep(2)
        assert mock_sleep.call_count == 2

        # 检查 sleep 的参数(指数退避: 1, 2)
        calls = [call[0][0] for call in mock_sleep.call_args_list]
        # Tenacity 的 wait_exponential(multiplier=1, min=1, max=3)
        # 会产生 1, 2 秒的延迟
        assert calls[0] == 1
        assert calls[1] == 2

    @patch("time.sleep")
    def test_logging_on_retry(self, mock_sleep, caplog):
        """测试重试时记录日志"""
        call_count = 0

        @retry_on_network_error
        def operation():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ConnectionError("Network error")
            return "success"

        with caplog.at_level(logging.WARNING):
            result = operation()

        assert result == "success"
        # 检查日志包含重试信息
        assert any("Retrying" in record.message for record in caplog.records)
