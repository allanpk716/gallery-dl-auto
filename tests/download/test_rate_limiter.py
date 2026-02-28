"""速率控制器测试

测试 rate_limit_delay 函数的基础延迟、随机抖动和负数保护功能。
"""

import pytest
from unittest.mock import patch
from gallery_dl_auto.download.rate_limiter import rate_limit_delay


class TestRateLimitDelay:
    """测试速率控制延迟"""

    @patch("gallery_dl_auto.download.rate_limiter.time.sleep")
    def test_rate_limit_delay_basic(self, mock_sleep: pytest.Mock) -> None:
        """测试基础延迟"""
        # 使用固定种子确保可重复
        import random
        random.seed(42)

        rate_limit_delay(base_seconds=2.5, jitter=1.0)

        # 验证 time.sleep 被调用
        mock_sleep.assert_called_once()

        # 验证延迟在合理范围内 (1.5-3.5 秒)
        call_args = mock_sleep.call_args[0][0]
        assert 1.5 <= call_args <= 3.5

    @patch("gallery_dl_auto.download.rate_limiter.time.sleep")
    def test_rate_limit_delay_with_jitter(self, mock_sleep: pytest.Mock) -> None:
        """测试随机抖动"""
        # 调用多次,验证抖动生效
        delays = []
        for _ in range(10):
            rate_limit_delay(base_seconds=2.5, jitter=1.0)
            delays.append(mock_sleep.call_args[0][0])
            mock_sleep.reset_mock()

        # 验证延迟有变化 (抖动生效)
        assert len(set(delays)) > 1  # 至少有不同的延迟值

        # 验证所有延迟都在范围内
        for delay in delays:
            assert 1.5 <= delay <= 3.5

    @patch("gallery_dl_auto.download.rate_limiter.time.sleep")
    def test_rate_limit_delay_negative(self, mock_sleep: pytest.Mock) -> None:
        """测试负数延迟保护"""
        import random

        # 设置随机返回极小值
        with patch.object(random, "uniform", return_value=-3.0):
            rate_limit_delay(base_seconds=2.5, jitter=10.0)

            # 验证负数延迟被修正为 0
            mock_sleep.assert_called_once_with(0.0)
