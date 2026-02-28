"""文件名清理工具测试

测试 sanitize_filename 函数的 Windows 非法字符清理、长度限制和中文支持。
"""

import pytest
from gallery_dl_auto.utils.filename_sanitizer import sanitize_filename


class TestSanitizeFilename:
    """测试文件名清理功能"""

    def test_sanitize_basic(self) -> None:
        """测试基本文件名 (无变化)"""
        filename = "test_file.jpg"
        assert sanitize_filename(filename) == "test_file.jpg"

    def test_sanitize_windows_chars(self) -> None:
        """测试移除 Windows 非法字符"""
        # 测试所有非法字符
        assert sanitize_filename("test<file>.jpg") == "testfile.jpg"
        assert sanitize_filename('test"file".jpg') == "testfile.jpg"
        assert sanitize_filename("test|file|.jpg") == "testfile.jpg"
        assert sanitize_filename("test?file?.jpg") == "testfile.jpg"
        assert sanitize_filename("test*file*.jpg") == "testfile.jpg"
        assert sanitize_filename("test:file:.jpg") == "testfile.jpg"

        # 测试混合非法字符
        assert sanitize_filename("test<>:\"/\\|?*.jpg") == "test.jpg"

    def test_sanitize_leading_trailing(self) -> None:
        """测试移除首尾空格和点"""
        assert sanitize_filename("  test.jpg  ") == "test.jpg"
        assert sanitize_filename("..test.jpg..") == "test.jpg"
        assert sanitize_filename(" . test.jpg . ") == "test.jpg"

    def test_sanitize_length_limit(self) -> None:
        """测试长度限制"""
        # 创建超长文件名
        long_name = "a" * 300 + ".jpg"
        result = sanitize_filename(long_name, max_length=200)

        # 验证长度被限制
        assert len(result) == 200

        # 测试默认长度限制
        result_default = sanitize_filename(long_name)
        assert len(result_default) == 200

    def test_sanitize_chinese(self) -> None:
        """测试中文字符保留"""
        # 测试中文标题
        assert sanitize_filename("美丽的风景.jpg") == "美丽的风景.jpg"
        assert sanitize_filename("测试<文件>.txt") == "测试文件.txt"

        # 测试混合中英文
        assert (
            sanitize_filename("Beautiful风景<pic>.jpg") == "Beautiful风景pic.jpg"
        )

    def test_sanitize_path_traversal(self) -> None:
        """测试路径遍历攻击防护 (移除 ..)"""
        # 注意: / 和 \\ 已被移除,但 .. 会被清理为空字符串后的点
        assert sanitize_filename("../../../etc/passwd") == "etcpasswd"
        assert sanitize_filename("..\\..\\test.jpg") == "test.jpg"


class TestSanitizeFilenameEdgeCases:
    """测试文件名清理边界情况"""

    def test_empty_string(self) -> None:
        """测试空字符串"""
        assert sanitize_filename("") == ""

    def test_only_invalid_chars(self) -> None:
        """测试仅包含非法字符"""
        assert sanitize_filename('<>:"/\\|?*') == ""

    def test_preserve_extension(self) -> None:
        """测试保留文件扩展名"""
        # 正常情况应保留扩展名
        assert sanitize_filename("test.jpg") == "test.jpg"
        assert sanitize_filename("test_file.png") == "test_file.png"
