"""StructuredFileHandler 单元测试"""

import json
import logging
import pytest
from pathlib import Path
from gallery_dl_auto.utils.logging import StructuredFileHandler


def test_structured_file_handler_init(tmp_path):
    """测试 StructuredFileHandler 初始化"""
    log_file = tmp_path / "logs" / "test.log"
    handler = StructuredFileHandler(log_file)

    # 验证日志目录被创建
    assert log_file.parent.exists()
    assert handler.log_file == log_file


def test_structured_file_handler_emit(tmp_path):
    """测试写入日志记录"""
    log_file = tmp_path / "test.log"
    handler = StructuredFileHandler(log_file)

    # 创建日志记录
    record = logging.LogRecord(
        name="test_logger",
        level=logging.INFO,
        pathname="test.py",
        lineno=42,
        msg="Test message",
        args=(),
        exc_info=None,
    )

    # 写入日志
    handler.emit(record)

    # 验证文件存在
    assert log_file.exists()

    # 验证日志内容
    with open(log_file, "r", encoding="utf-8") as f:
        line = f.readline()
        entry = json.loads(line)

        assert "timestamp" in entry
        assert entry["level"] == "INFO"
        assert entry["logger"] == "test_logger"
        assert entry["message"] == "Test message"
        assert entry["module"] == "test"
        # funcName 在手动创建的 LogRecord 中可能为 None
        assert "function" in entry
        assert entry["line"] == 42


def test_structured_file_handler_multiple_entries(tmp_path):
    """测试写入多条日志"""
    log_file = tmp_path / "test.log"
    handler = StructuredFileHandler(log_file)

    # 写入多条日志
    messages = ["First message", "Second message", "Third message"]
    for msg in messages:
        record = logging.LogRecord(
            name="test",
            level=logging.INFO,
            pathname="test.py",
            lineno=1,
            msg=msg,
            args=(),
            exc_info=None,
        )
        handler.emit(record)

    # 验证每行一个 JSON 对象
    with open(log_file, "r", encoding="utf-8") as f:
        lines = f.readlines()
        assert len(lines) == 3

        for i, line in enumerate(lines):
            entry = json.loads(line)
            assert entry["message"] == messages[i]


def test_structured_file_handler_with_exception(tmp_path):
    """测试异常信息记录"""
    log_file = tmp_path / "test.log"
    handler = StructuredFileHandler(log_file)

    try:
        # 触发异常
        raise ValueError("Test exception")
    except ValueError:
        import sys

        exc_info = sys.exc_info()

        # 创建包含异常信息的日志记录
        record = logging.LogRecord(
            name="test",
            level=logging.ERROR,
            pathname="test.py",
            lineno=1,
            msg="Error occurred",
            args=(),
            exc_info=exc_info,
        )
        handler.emit(record)

    # 验证异常信息被记录
    with open(log_file, "r", encoding="utf-8") as f:
        line = f.readline()
        entry = json.loads(line)

        assert "exception" in entry
        assert "ValueError: Test exception" in entry["exception"]


def test_structured_file_handler_json_lines_format(tmp_path):
    """测试 JSON Lines 格式(每行一个有效 JSON)"""
    log_file = tmp_path / "test.log"
    handler = StructuredFileHandler(log_file)

    # 写入多条日志
    for i in range(5):
        record = logging.LogRecord(
            name="test",
            level=logging.DEBUG,
            pathname="test.py",
            lineno=i,
            msg=f"Message {i}",
            args=(),
            exc_info=None,
        )
        handler.emit(record)

    # 验证每行都是有效的 JSON
    with open(log_file, "r", encoding="utf-8") as f:
        for i, line in enumerate(f):
            entry = json.loads(line)  # 如果不是有效 JSON 会抛出异常
            assert entry["message"] == f"Message {i}"


def test_structured_file_handler_chinese_text(tmp_path):
    """测试中文文本支持"""
    log_file = tmp_path / "test.log"
    handler = StructuredFileHandler(log_file)

    # 写入中文消息
    chinese_msg = "测试中文日志消息"
    record = logging.LogRecord(
        name="test",
        level=logging.INFO,
        pathname="test.py",
        lineno=1,
        msg=chinese_msg,
        args=(),
        exc_info=None,
    )
    handler.emit(record)

    # 验证中文正确保存
    with open(log_file, "r", encoding="utf-8") as f:
        line = f.readline()
        entry = json.loads(line)
        assert entry["message"] == chinese_msg
