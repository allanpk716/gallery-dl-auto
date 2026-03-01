"""进度报告器模块

详细模式下的实时进度显示,输出到 stderr 避免污染 stdout 的 JSON 输出。
"""

from datetime import datetime

from rich.console import Console


class ProgressReporter:
    """进度报告器:根据 output_mode 控制输出

    Args:
        verbose: 是否启用详细模式(显示每个作品的详细信息)
        output_mode: 输出模式 ('normal', 'json', 'quiet')

    输出策略:
        - normal 模式: 显示基本进度(下载进度、成功数量)
        - verbose 模式: 显示详细进度(包括每个作品、速率控制等待)
        - json/quiet 模式: 完全静默

    Example:
        >>> reporter = ProgressReporter(verbose=False, output_mode='normal')
        >>> reporter.update_progress(24, 30, 2)
        [2026-02-25 14:23:15] 下载中: 24/30 (失败: 2)

        >>> reporter = ProgressReporter(verbose=True, output_mode='normal')
        >>> reporter.report_success("标题", 12345678)
          ✓ 标题 (ID: 12345678)

        >>> reporter = ProgressReporter(verbose=False, output_mode='json')
        >>> reporter.update_progress(24, 30, 2)  # 无输出
    """

    def __init__(self, verbose: bool = False, output_mode: str = "normal") -> None:
        """初始化进度报告器

        Args:
            verbose: 是否启用详细模式
            output_mode: 输出模式 ('normal', 'json', 'quiet')
        """
        self.verbose = verbose
        self.output_mode = output_mode
        self.console = Console(stderr=True)

    def update_progress(self, idx: int, total: int, failed: int) -> None:
        """更新进度状态

        Args:
            idx: 当前下载索引(1-based)
            total: 总作品数
            failed: 失败数量

        输出规则:
            - json/quiet 模式: 不输出
            - normal/verbose 模式: 输出进度信息

        详细模式输出示例:
            [2026-02-25 14:23:15] 下载中: 24/30 (失败: 2)
        """
        # json/quiet 模式下不输出
        if self.output_mode in ["json", "quiet"]:
            return

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.console.print(f"[{timestamp}] 下载中: {idx}/{total} (失败: {failed})")

    def report_success(self, title: str, illust_id: int) -> None:
        """报告成功下载

        Args:
            title: 作品标题
            illust_id: 作品 ID

        输出规则:
            - json/quiet 模式: 不输出
            - normal 模式: 不输出
            - verbose 模式: 输出详细信息

        详细模式输出示例:
          ✓ 标题 (ID: 12345678)
        """
        # json/quiet 模式下不输出
        if self.output_mode in ["json", "quiet"]:
            return

        # 只在 verbose 模式下显示
        if not self.verbose:
            return

        self.console.print(f"  ✓ {title} (ID: {illust_id})", style="green")

    def report_rate_limit_wait(self, delay: float) -> None:
        """报告速率控制等待

        Args:
            delay: 等待秒数

        输出规则:
            - json/quiet 模式: 不输出
            - normal 模式: 不输出
            - verbose 模式: 输出等待信息

        详细模式输出示例:
          等待 2.5s...
        """
        # json/quiet 模式下不输出
        if self.output_mode in ["json", "quiet"]:
            return

        # 只在 verbose 模式下显示
        if not self.verbose:
            return

        self.console.print(f"  等待 {delay}s...", style="dim")

    def report_retry(self, attempt: int, max_retries: int, error: str) -> None:
        """报告重试

        Args:
            attempt: 当前重试次数
            max_retries: 最大重试次数
            error: 错误信息

        输出规则:
            - json/quiet 模式: 不输出
            - normal 模式: 不输出
            - verbose 模式: 输出重试信息

        详细模式输出示例:
          重试 2/3: Connection timeout
        """
        # json/quiet 模式下不输出
        if self.output_mode in ["json", "quiet"]:
            return

        # 只在 verbose 模式下显示
        if not self.verbose:
            return

        self.console.print(
            f"  重试 {attempt}/{max_retries}: {error}", style="yellow"
        )
