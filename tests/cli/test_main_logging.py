"""日志系统测试模块"""

import logging
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from gallery_dl_auto.utils.logging import setup_logging, StructuredFileHandler


class TestLogging:
    """日志系统测试类"""

    def test_verbose_mode_outputs_to_console(self, capsys, tmp_path):
        """测试详细模式输出到控制台"""
        # Mock get_log_file_path 返回临时路径
        with patch("gallery_dl_auto.config.paths.get_log_file_path") as mock_path:
            mock_path.return_value = tmp_path / "test.log"

            console = setup_logging(log_level="DEBUG", verbose=True)
            logger = logging.getLogger("gallery_dl_auto")

            # 清除之前的日志
            logger.handlers.clear()

            # 重新调用 setup_logging
            setup_logging(log_level="DEBUG", verbose=True)

            # 输出一条日志
            logger.info("Test message")

            # 验证 stderr 输出包含消息
            captured = capsys.readouterr()
            assert "Test message" in captured.err

    def test_silent_mode_no_console_output(self, capsys, tmp_path):
        """测试静默模式无控制台输出"""
        # Mock get_log_file_path 返回临时路径
        with patch("gallery_dl_auto.config.paths.get_log_file_path") as mock_path:
            mock_path.return_value = tmp_path / "test.log"

            # 静默模式
            setup_logging(log_level="INFO", verbose=False)
            logger = logging.getLogger("gallery_dl_auto")

            # 清除之前的日志
            logger.handlers.clear()

            # 重新调用 setup_logging
            setup_logging(log_level="INFO", verbose=False)

            # 输出一条日志
            logger.info("Test message")

            # 验证无控制台输出
            captured = capsys.readouterr()
            assert "Test message" not in captured.err

    def test_file_logging_always_enabled(self, tmp_path):
        """测试文件日志始终启用"""
        # Mock get_log_file_path 返回临时路径
        with patch("gallery_dl_auto.config.paths.get_log_file_path") as mock_path:
            log_file = tmp_path / "test.log"
            mock_path.return_value = log_file

            # 静默模式
            setup_logging(log_level="DEBUG", verbose=False)
            logger = logging.getLogger("gallery_dl_auto")

            # 清除之前的日志
            logger.handlers.clear()

            # 重新调用 setup_logging
            setup_logging(log_level="DEBUG", verbose=False)

            # 输出一条日志
            logger.debug("Debug message")

            # 验证文件日志存在
            assert log_file.exists()

            # 验证文件内容包含消息
            content = log_file.read_text(encoding="utf-8")
            assert "Debug message" in content

    def test_handlers_cleared_on_reinit(self, tmp_path):
        """测试重新初始化时清除现有 handlers"""
        # Mock get_log_file_path 返回临时路径
        with patch("gallery_dl_auto.config.paths.get_log_file_path") as mock_path:
            mock_path.return_value = tmp_path / "test.log"

            logger = logging.getLogger("gallery_dl_auto")

            # 第一次初始化
            setup_logging(log_level="INFO", verbose=True)
            initial_handler_count = len(logger.handlers)

            # 第二次初始化
            setup_logging(log_level="INFO", verbose=True)
            final_handler_count = len(logger.handlers)

            # 验证 handler 数量未增加(重复调用不会添加多个 handlers)
            assert final_handler_count == initial_handler_count
            # 验证有 2 个 handlers: RichHandler + StructuredFileHandler
            assert final_handler_count == 2

    def test_log_levels_correct(self, tmp_path):
        """测试日志级别正确设置"""
        # Mock get_log_file_path 返回临时路径
        with patch("gallery_dl_auto.config.paths.get_log_file_path") as mock_path:
            mock_path.return_value = tmp_path / "test.log"

            # 详细模式
            setup_logging(log_level="DEBUG", verbose=True)
            logger = logging.getLogger("gallery_dl_auto")

            # 验证 logger 级别为 DEBUG
            assert logger.level == logging.DEBUG

            # 验证 handler 级别:控制台 INFO,文件 DEBUG
            console_handler = None
            file_handler = None
            for handler in logger.handlers:
                if isinstance(handler, StructuredFileHandler):
                    file_handler = handler
                else:
                    console_handler = handler

            assert console_handler is not None
            assert console_handler.level == logging.INFO

            assert file_handler is not None
            assert file_handler.level == logging.DEBUG


class TestStructuredFileHandler:
    """StructuredFileHandler 测试类"""

    def test_writes_json_lines(self, tmp_path):
        """测试写入 JSON Lines 格式"""
        log_file = tmp_path / "test.log"
        handler = StructuredFileHandler(log_file)

        # 创建日志记录
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg="Test message",
            args=(),
            exc_info=None,
        )

        # 写入日志
        handler.emit(record)

        # 验证文件存在
        assert log_file.exists()

        # 验证 JSON Lines 格式
        content = log_file.read_text(encoding="utf-8")
        import json
        log_entry = json.loads(content.strip())

        assert log_entry["message"] == "Test message"
        assert log_entry["level"] == "INFO"
        assert "timestamp" in log_entry

    def test_creates_log_directory(self, tmp_path):
        """测试自动创建日志目录"""
        log_file = tmp_path / "logs" / "test.log"
        handler = StructuredFileHandler(log_file)

        # 验证目录已创建
        assert log_file.parent.exists()
