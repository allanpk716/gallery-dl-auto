"""速率控制器

实现保守的速率控制策略,避免触发 Pixiv 的 429 错误。
"""

import random
import time


def rate_limit_delay(base_seconds: float = 2.5, jitter: float = 1.0) -> None:
    """添加请求间延迟 + 随机抖动,避免速率限制。

    Args:
        base_seconds: 基础延迟秒数 (默认 2.5 秒)
        jitter: 抖动范围 ±秒数 (默认 ±1.0 秒)

    Examples:
        >>> rate_limit_delay()  # 延迟 1.5-3.5 秒
        >>> rate_limit_delay(3.0, 0.5)  # 延迟 2.5-3.5 秒
    """
    delay = base_seconds + random.uniform(-jitter, jitter)
    time.sleep(max(0, delay))
