"""ProgressReporter 测试模块"""

import io
import sys
from datetime import datetime

import pytest
from rich.console import Console

from gallery_dl_auto.download.progress_reporter import ProgressReporter


class TestProgressReporter:
    """ProgressReporter 测试类"""

    def test_verbose_mode_outputs_progress(self, capsys):
        """测试详细模式输出进度信息"""
        reporter = ProgressReporter(verbose=True)

        # 捕获 stderr 输出
        reporter.update_progress(24, 30, 2)

        # 验证 stderr 输出包含进度信息
        captured = capsys.readouterr()
        assert "下载中: 24/30" in captured.err
        assert "失败: 2" in captured.err

    def test_silent_mode_no_output(self, capsys):
        """测试静默模式无输出"""
        reporter = ProgressReporter(verbose=False)

        reporter.update_progress(24, 30, 2)
        reporter.report_success("测试标题", 12345678)
        reporter.report_rate_limit_wait(2.5)
        reporter.report_retry(1, 3, "Connection timeout")

        # 验证无输出
        captured = capsys.readouterr()
        assert captured.out == ""
        assert captured.err == ""

    def test_success_report_styled(self, capsys):
        """测试成功报告包含样式"""
        reporter = ProgressReporter(verbose=True)

        reporter.report_success("测试标题", 12345678)

        # 验证输出包含标题和 ID
        captured = capsys.readouterr()
        assert "✓ 测试标题 (ID: 12345678)" in captured.err

    def test_rate_limit_wait_styled(self, capsys):
        """测试速率限制等待报告"""
        reporter = ProgressReporter(verbose=True)

        reporter.report_rate_limit_wait(2.5)

        # 验证输出包含等待时间
        captured = capsys.readouterr()
        assert "等待 2.5s" in captured.err

    def test_retry_report_styled(self, capsys):
        """测试重试报告包含样式"""
        reporter = ProgressReporter(verbose=True)

        reporter.report_retry(2, 3, "Connection timeout")

        # 验证输出包含重试信息和错误
        captured = capsys.readouterr()
        assert "重试 2/3" in captured.err
        assert "Connection timeout" in captured.err

    def test_timestamp_format(self, capsys):
        """测试时间戳格式正确"""
        reporter = ProgressReporter(verbose=True)

        reporter.update_progress(1, 10, 0)

        # 验证时间戳格式存在且格式正确(YYYY-MM-DD HH:MM:SS)
        captured = capsys.readouterr()
        import re
        # 查找时间戳模式
        timestamp_pattern = r'\[(\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2})\]'
        match = re.search(timestamp_pattern, captured.err)
        assert match is not None, "时间戳格式未找到"

        # 验证时间戳可以正确解析
        timestamp_str = match.group(1)
        parsed_time = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S")
        assert parsed_time is not None

    def test_verbose_false_all_methods_return_early(self):
        """测试 verbose=False 时所有方法立即返回"""
        reporter = ProgressReporter(verbose=False)

        # 验证所有方法在 verbose=False 时立即返回
        # 通过检查 console.print 未被调用来验证
        original_print = reporter.console.print
        call_count = [0]

        def mock_print(*args, **kwargs):
            call_count[0] += 1
            return original_print(*args, **kwargs)

        reporter.console.print = mock_print

        reporter.update_progress(1, 10, 0)
        reporter.report_success("标题", 123)
        reporter.report_rate_limit_wait(1.0)
        reporter.report_retry(1, 3, "错误")

        # 验证 console.print 未被调用
        assert call_count[0] == 0

    def test_console_uses_stderr(self):
        """测试 Console 输出到 stderr"""
        reporter = ProgressReporter(verbose=True)

        # 验证 Console 初始化为 stderr=True
        assert reporter.console.file == sys.stderr
