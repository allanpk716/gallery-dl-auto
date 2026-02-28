"""进度报告器模块

详细模式下的实时进度显示,输出到 stderr 避免污染 stdout 的 JSON 输出。
"""

from datetime import datetime

from rich.console import Console


class ProgressReporter:
    """进度报告器:详细模式实时更新,静默模式无输出

    Args:
        verbose: 是否启用详细模式

    日志策略:
        - 详细模式:输出到 stderr,带时间戳和样式
        - 静默模式:无任何输出

    Example:
        >>> reporter = ProgressReporter(verbose=True)
        >>> reporter.update_progress(24, 30, 2)
        [2026-02-25 14:23:15] 下载中: 24/30 (失败: 2)
        >>> reporter.report_success("标题", 12345678)
          ✓ 标题 (ID: 12345678)
    """

    def __init__(self, verbose: bool = False) -> None:
        """初始化进度报告器

        Args:
            verbose: 是否启用详细模式
        """
        self.verbose = verbose
        self.console = Console(stderr=True)

    def update_progress(self, idx: int, total: int, failed: int) -> None:
        """更新进度状态

        Args:
            idx: 当前下载索引(1-based)
            total: 总作品数
            failed: 失败数量

        详细模式输出示例:
            [2026-02-25 14:23:15] 下载中: 24/30 (失败: 2)
        """
        if not self.verbose:
            return

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.console.print(f"[{timestamp}] 下载中: {idx}/{total} (失败: {failed})")

    def report_success(self, title: str, illust_id: int) -> None:
        """报告成功下载

        Args:
            title: 作品标题
            illust_id: 作品 ID

        详细模式输出示例:
          ✓ 标题 (ID: 12345678)
        """
        if not self.verbose:
            return

        self.console.print(f"  ✓ {title} (ID: {illust_id})", style="green")

    def report_rate_limit_wait(self, delay: float) -> None:
        """报告速率控制等待

        Args:
            delay: 等待秒数

        详细模式输出示例:
          等待 2.5s...
        """
        if not self.verbose:
            return

        self.console.print(f"  等待 {delay}s...", style="dim")

    def report_retry(self, attempt: int, max_retries: int, error: str) -> None:
        """报告重试

        Args:
            attempt: 当前重试次数
            max_retries: 最大重试次数
            error: 错误信息

        详细模式输出示例:
          重试 2/3: Connection timeout
        """
        if not self.verbose:
            return

        self.console.print(
            f"  重试 {attempt}/{max_retries}: {error}", style="yellow"
        )
