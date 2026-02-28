"""文件下载器测试

测试 download_file 函数的流式下载、错误处理和目录创建功能。
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch, mock_open
from gallery_dl_auto.download.file_downloader import download_file
from gallery_dl_auto.models.error_response import StructuredError


class TestDownloadFile:
    """测试文件下载功能"""

    @patch("gallery_dl_auto.download.file_downloader.requests.get")
    def test_download_success(self, mock_get: Mock, tmp_path: Path) -> None:
        """测试成功下载"""
        # 模拟 HTTP 响应
        mock_response = Mock()
        mock_response.__enter__ = Mock(return_value=mock_response)
        mock_response.__exit__ = Mock(return_value=False)
        mock_response.status_code = 200
        mock_response.iter_content = Mock(return_value=[b"fake_image_data"])
        mock_response.raise_for_status = Mock()

        mock_get.return_value = mock_response

        # 下载文件
        filepath = tmp_path / "test.jpg"
        result = download_file("https://example.com/test.jpg", filepath, illust_id=12345)

        # 验证结果
        assert isinstance(result, dict)
        assert result["success"] is True
        assert result["filepath"] == str(filepath)
        assert "size" in result

        # 验证文件被写入
        assert filepath.exists()

    @patch("gallery_dl_auto.download.file_downloader.requests.get")
    def test_download_timeout(self, mock_get: Mock, tmp_path: Path) -> None:
        """测试超时处理"""
        import requests

        # 模拟超时异常
        mock_get.side_effect = requests.exceptions.Timeout()

        filepath = tmp_path / "test.jpg"
        result = download_file("https://example.com/test.jpg", filepath, illust_id=12345)

        # 验证错误处理
        assert isinstance(result, StructuredError)
        assert result.error_code == "DOWNLOAD_TIMEOUT"
        assert "下载超时" in result.message

    @patch("gallery_dl_auto.download.file_downloader.requests.get")
    def test_download_http_error_404(self, mock_get: Mock, tmp_path: Path) -> None:
        """测试 HTTP 404 错误处理"""
        import requests

        # 模拟 HTTP 404 错误
        mock_response = Mock()
        mock_response.status_code = 404
        mock_get.side_effect = requests.exceptions.HTTPError(
            response=mock_response
        )

        filepath = tmp_path / "test.jpg"
        result = download_file("https://example.com/test.jpg", filepath, illust_id=12345)

        # 验证错误处理
        assert isinstance(result, StructuredError)
        assert result.error_code == "API_SERVER_ERROR"
        assert "HTTP 错误 404" in result.message

    @patch("gallery_dl_auto.download.file_downloader.requests.get")
    def test_download_http_error_403(self, mock_get: Mock, tmp_path: Path) -> None:
        """测试 HTTP 403 错误处理"""
        import requests

        # 模拟 HTTP 403 错误
        mock_response = Mock()
        mock_response.status_code = 403
        mock_get.side_effect = requests.exceptions.HTTPError(
            response=mock_response
        )

        filepath = tmp_path / "test.jpg"
        result = download_file("https://example.com/test.jpg", filepath, illust_id=12345)

        # 验证错误处理
        assert isinstance(result, StructuredError)
        assert result.error_code == "API_SERVER_ERROR"
        assert "HTTP 错误 403" in result.message

    @patch("gallery_dl_auto.download.file_downloader.requests.get")
    def test_download_http_error_429(self, mock_get: Mock, tmp_path: Path) -> None:
        """测试 HTTP 429 错误处理 (速率限制)"""
        import requests

        # 模拟 HTTP 429 错误
        mock_response = Mock()
        mock_response.status_code = 429
        mock_get.side_effect = requests.exceptions.HTTPError(
            response=mock_response
        )

        filepath = tmp_path / "test.jpg"
        result = download_file("https://example.com/test.jpg", filepath, illust_id=12345)

        # 验证错误处理
        assert isinstance(result, StructuredError)
        assert result.error_code == "RATE_LIMIT_EXCEEDED"
        assert "HTTP 429" in result.message
        assert "--image-delay" in result.suggestion
        assert "--batch-delay" in result.suggestion

    @patch("gallery_dl_auto.download.file_downloader.requests.get")
    def test_download_connection_error(
        self, mock_get: Mock, tmp_path: Path
    ) -> None:
        """测试网络连接错误处理"""
        import requests

        # 模拟连接错误
        mock_get.side_effect = requests.exceptions.ConnectionError()

        filepath = tmp_path / "test.jpg"
        result = download_file("https://example.com/test.jpg", filepath, illust_id=12345)

        # 验证错误处理
        assert isinstance(result, StructuredError)
        assert result.error_code == "DOWNLOAD_FAILED"
        assert "网络连接失败" in result.message

    @patch("gallery_dl_auto.download.file_downloader.requests.get")
    def test_download_file_write_error(
        self, mock_get: Mock, tmp_path: Path
    ) -> None:
        """测试文件写入错误处理 (权限、磁盘满)"""
        # 模拟 HTTP 响应
        mock_response = Mock()
        mock_response.__enter__ = Mock(return_value=mock_response)
        mock_response.__exit__ = Mock(return_value=False)
        mock_response.status_code = 200
        mock_response.iter_content = Mock(return_value=[b"fake_image_data"])
        mock_response.raise_for_status = Mock()

        mock_get.return_value = mock_response

        # 模拟文件写入错误
        filepath = tmp_path / "test.jpg"
        with patch("builtins.open", side_effect=OSError("Disk full")):
            result = download_file("https://example.com/test.jpg", filepath, illust_id=12345)

        # 验证错误处理
        assert isinstance(result, StructuredError)
        assert result.error_code == "FILE_DISK_FULL"
        assert "文件操作失败" in result.message

    @patch("gallery_dl_auto.download.file_downloader.requests.get")
    def test_download_creates_parent_dir(
        self, mock_get: Mock, tmp_path: Path
    ) -> None:
        """测试自动创建父目录"""
        # 模拟 HTTP 响应
        mock_response = Mock()
        mock_response.__enter__ = Mock(return_value=mock_response)
        mock_response.__exit__ = Mock(return_value=False)
        mock_response.status_code = 200
        mock_response.iter_content = Mock(return_value=[b"fake_image_data"])
        mock_response.raise_for_status = Mock()

        mock_get.return_value = mock_response

        # 使用不存在的子目录
        filepath = tmp_path / "subdir" / "test.jpg"
        result = download_file("https://example.com/test.jpg", filepath, illust_id=12345)

        # 验证目录被创建
        assert filepath.parent.exists()
        assert isinstance(result, dict)
        assert result["success"] is True
