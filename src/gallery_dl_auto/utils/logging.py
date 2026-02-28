"""日志配置模块

使用 Rich 提供彩色、格式化的日志输出,同时支持结构化文件日志。
"""

import json
import logging
from datetime import datetime
from pathlib import Path

from rich.console import Console
from rich.logging import RichHandler


class StructuredFileHandler(logging.Handler):
    """结构化日志处理器:写入 JSON Lines 文件

    每行一个 JSON 对象,包含时间戳、日志级别、消息、模块信息等。
    """

    def __init__(self, log_file: Path):
        """初始化结构化文件处理器

        Args:
            log_file: 日志文件路径
        """
        super().__init__()
        self.log_file = log_file
        # 确保日志目录存在
        log_file.parent.mkdir(parents=True, exist_ok=True)

    def emit(self, record: logging.LogRecord):
        """写入日志记录

        Args:
            record: 日志记录对象
        """
        try:
            log_entry = {
                "timestamp": datetime.fromtimestamp(record.created).isoformat(),
                "level": record.levelname,
                "logger": record.name,
                "message": record.getMessage(),
                "module": record.module,
                "function": record.funcName,
                "line": record.lineno,
            }

            # 添加异常信息
            if record.exc_info:
                log_entry["exception"] = self.format(record)

            # 追加写入(每行一个 JSON)
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + "\n")

        except Exception:
            self.handleError(record)


def setup_logging(log_level: str = "INFO", verbose: bool = False, quiet: bool = False) -> Console:
    """配置日志系统

    Args:
        log_level: 日志级别 (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        verbose: 是否启用详细模式(控制台输出)
        quiet: 是否启用静默模式(禁用所有控制台输出)

    Returns:
        Console: Rich Console 实例

    日志策略:
        - 详细模式(verbose=True, quiet=False): 控制台 INFO+, 文件 DEBUG+
        - 静默模式(quiet=True): 控制台无输出, 文件 DEBUG+
        - JSON 模式(外部传入 quiet=True): 控制台无输出, 文件 DEBUG+

    Example:
        >>> console = setup_logging("DEBUG", verbose=True)
        >>> logger = logging.getLogger("gallery_dl_auto")
        >>> logger.info("[bold blue]Starting application[/bold blue]")
    """
    # 使用 stderr 输出日志,避免污染 stdout 的 JSON 输出
    console = Console(stderr=True)

    # 配置 logger
    logger = logging.getLogger("gallery_dl_auto")
    logger.setLevel(logging.DEBUG)  # 始终捕获所有级别

    # 清除现有 handlers,避免重复日志
    logger.handlers.clear()

    # 详细模式:控制台输出(仅在非静默模式下)
    if verbose and not quiet:
        handler = RichHandler(
            console=console,
            show_time=True,  # 显示时间戳
            show_level=True,  # 显示日志级别
            show_path=False,  # 不显示文件路径(避免输出过长)
            markup=True,  # 支持 Rich markup
            rich_tracebacks=True,  # 美化 traceback
            tracebacks_show_locals=True,  # 显示局部变量
        )
        handler.setLevel(logging.INFO)  # 控制台仅输出 INFO+
        logger.addHandler(handler)

    # 文件日志始终启用
    from gallery_dl_auto.config.paths import get_log_file_path

    file_handler = StructuredFileHandler(get_log_file_path())
    file_handler.setLevel(logging.DEBUG)  # 文件记录 DEBUG+
    logger.addHandler(file_handler)

    # 避免重复日志
    logger.propagate = False

    return console


def get_logger(name: str | None = None) -> logging.Logger:
    """获取 logger 实例

    Args:
        name: 模块名称 (可选)

    Returns:
        logging.Logger: logger 实例

    Example:
        >>> logger = get_logger(__name__)
        >>> logger.info("Module initialized")
    """
    if name:
        return logging.getLogger(f"gallery_dl_auto.{name}")
    return logging.getLogger("gallery_dl_auto")
