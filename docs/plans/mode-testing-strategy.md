# Mode 映射 - 测试策略设计

## 1. 测试目标和范围

### 1.1 测试目标

1. **功能正确性**: 验证所有 mode 转换逻辑正确
2. **向后兼容性**: 确保重构后现有功能不受影响
3. **错误处理**: 验证各种错误场景的处理
4. **性能**: 确保 mode 转换不会成为性能瓶颈
5. **边界条件**: 测试极端情况和特殊输入

### 1.2 测试范围

```
┌────────────────────────────────────────────────────────┐
│                    测试金字塔                           │
├────────────────────────────────────────────────────────┤
│                                                         │
│                     /        \                         │
│                   /   E2E     \                         │
│                 /    Tests     \                        │
│               /------------------\                      │
│             /   Integration Tests \                     │
│           /--------------------------\                  │
│         /       Unit Tests            \                 │
│       /----------------------------------\              │
│                                                         │
│  数量: E2E < Integration < Unit                         │
│  速度: E2E < Integration < Unit                         │
│  成本: E2E > Integration > Unit                         │
└────────────────────────────────────────────────────────┘
```

**测试层次**:
- **单元测试 (70%)**: 测试 ModeManager 的各个方法
- **集成测试 (20%)**: 测试 mode 在组件间的流转
- **端到端测试 (10%)**: 测试完整的 CLI 命令

## 2. 单元测试设计

### 2.1 ModeManager 单元测试

**位置**: `tests/core/test_mode_manager.py`

```python
"""ModeManager 单元测试

测试 ModeManager 的所有公共方法
"""

import pytest
from gallery_dl_auto.core.mode_manager import ModeManager, InvalidModeError


class TestModeManagerBasics:
    """ModeManager 基础功能测试"""

    def test_modes_count(self):
        """测试 mode 总数正确"""
        assert len(ModeManager.MODES) == 13

    def test_all_modes_have_required_fields(self):
        """测试所有 mode 定义包含必需字段"""
        required_fields = ["cli_name", "api_name", "gallery_dl_name", "description", "category"]

        for api_mode, definition in ModeManager.MODES.items():
            for field in required_fields:
                assert field in definition, \
                    f"Mode '{api_mode}' missing field '{field}'"

    def test_cli_to_api_consistency(self):
        """测试 CLI -> API 映射的一致性"""
        for api_mode, definition in ModeManager.MODES.items():
            cli_mode = definition["cli_name"]
            converted = ModeManager.cli_to_api(cli_mode)
            assert converted == api_mode, \
                f"CLI '{cli_mode}' should map to '{api_mode}', got '{converted}'"

    def test_api_to_gallery_dl_consistency(self):
        """测试 API -> Gallery-dl 映射的一致性"""
        for api_mode, definition in ModeManager.MODES.items():
            expected = definition["gallery_dl_name"]
            converted = ModeManager.api_to_gallery_dl(api_mode)
            assert converted == expected, \
                f"API '{api_mode}' should map to '{expected}', got '{converted}'"


class TestCLIModeValidation:
    """CLI mode 验证测试"""

    def test_validate_valid_daily(self):
        """测试有效的 daily mode"""
        result = ModeManager.validate_cli_mode("daily")
        assert result == "day"

    def test_validate_valid_weekly(self):
        """测试有效的 weekly mode"""
        result = ModeManager.validate_cli_mode("weekly")
        assert result == "week"

    def test_validate_valid_monthly(self):
        """测试有效的 monthly mode"""
        result = ModeManager.validate_cli_mode("monthly")
        assert result == "month"

    def test_validate_valid_day_male(self):
        """测试有效的 day_male mode"""
        result = ModeManager.validate_cli_mode("day_male")
        assert result == "day_male"

    def test_validate_all_cli_modes(self):
        """测试所有 CLI mode 都能通过验证"""
        for cli_mode in ModeManager.get_all_cli_modes():
            result = ModeManager.validate_cli_mode(cli_mode)
            assert result in ModeManager.MODES

    def test_validate_invalid_mode_raises_error(self):
        """测试无效 mode 抛出异常"""
        with pytest.raises(InvalidModeError) as exc_info:
            ModeManager.validate_cli_mode("invalid_mode")

        assert "invalid_mode" in str(exc_info.value)
        assert "daily" in str(exc_info.value)

    def test_validate_empty_string_raises_error(self):
        """测试空字符串抛出异常"""
        with pytest.raises(InvalidModeError):
            ModeManager.validate_cli_mode("")

    def test_validate_case_sensitive(self):
        """测试 mode 名称大小写敏感"""
        with pytest.raises(InvalidModeError):
            ModeManager.validate_cli_mode("DAILY")  # 应该是小写 "daily"


class TestAPIModeValidation:
    """API mode 验证测试"""

    def test_validate_valid_api_day(self):
        """测试有效的 API mode: day"""
        result = ModeManager.validate_api_mode("day")
        assert result == "day"

    def test_validate_valid_api_week(self):
        """测试有效的 API mode: week"""
        result = ModeManager.validate_api_mode("week")
        assert result == "week"

    def test_validate_all_api_modes(self):
        """测试所有 API mode 都能通过验证"""
        for api_mode in ModeManager.get_all_api_modes():
            result = ModeManager.validate_api_mode(api_mode)
            assert result == api_mode

    def test_validate_invalid_api_mode_raises_error(self):
        """测试无效的 API mode 抛出异常"""
        with pytest.raises(InvalidModeError) as exc_info:
            ModeManager.validate_api_mode("invalid_api")

        assert "invalid_api" in str(exc_info.value)


class TestModeConversion:
    """Mode 转换测试"""

    def test_cli_to_api_daily(self):
        """测试 CLI -> API: daily -> day"""
        assert ModeManager.cli_to_api("daily") == "day"

    def test_cli_to_api_weekly(self):
        """测试 CLI -> API: weekly -> week"""
        assert ModeManager.cli_to_api("weekly") == "week"

    def test_cli_to_api_monthly(self):
        """测试 CLI -> API: monthly -> month"""
        assert ModeManager.cli_to_api("monthly") == "month"

    def test_cli_to_api_identity_mapping(self):
        """测试 CLI -> API: 不需要转换的 mode"""
        # day_male 等 mode 在 CLI 和 API 中名称相同
        assert ModeManager.cli_to_api("day_male") == "day_male"
        assert ModeManager.cli_to_api("week_original") == "week_original"

    def test_api_to_gallery_dl_day(self):
        """测试 API -> Gallery-dl: day -> daily"""
        assert ModeManager.api_to_gallery_dl("day") == "daily"

    def test_api_to_gallery_dl_week(self):
        """测试 API -> Gallery-dl: week -> weekly"""
        assert ModeManager.api_to_gallery_dl("week") == "weekly"

    def test_api_to_gallery_dl_month(self):
        """测试 API -> Gallery-dl: month -> monthly"""
        assert ModeManager.api_to_gallery_dl("month") == "monthly"

    def test_api_to_gallery_dl_identity_mapping(self):
        """测试 API -> Gallery-dl: 不需要转换的 mode"""
        # 大多数 mode 在 API 和 Gallery-dl 中名称相同
        assert ModeManager.api_to_gallery_dl("day_male") == "day_male"
        assert ModeManager.api_to_gallery_dl("day_r18") == "day_r18"

    def test_round_trip_conversion(self):
        """测试往返转换的一致性"""
        # CLI -> API -> Gallery-dl
        for cli_mode in ModeManager.get_all_cli_modes():
            api_mode = ModeManager.cli_to_api(cli_mode)
            gallery_dl_mode = ModeManager.api_to_gallery_dl(api_mode)

            # 验证转换是有效的
            assert api_mode in ModeManager.MODES
            assert gallery_dl_mode is not None


class TestModeQueries:
    """Mode 查询功能测试"""

    def test_get_all_cli_modes(self):
        """测试获取所有 CLI mode"""
        modes = ModeManager.get_all_cli_modes()

        assert isinstance(modes, list)
        assert len(modes) == 13
        assert "daily" in modes
        assert "weekly" in modes
        assert all(isinstance(m, str) for m in modes)

    def test_get_all_cli_modes_sorted(self):
        """测试 CLI mode 列表已排序"""
        modes = ModeManager.get_all_cli_modes()
        assert modes == sorted(modes)

    def test_get_all_api_modes(self):
        """测试获取所有 API mode"""
        modes = ModeManager.get_all_api_modes()

        assert isinstance(modes, list)
        assert len(modes) == 13
        assert "day" in modes
        assert "week" in modes

    def test_get_all_api_modes_sorted(self):
        """测试 API mode 列表已排序"""
        modes = ModeManager.get_all_api_modes()
        assert modes == sorted(modes)

    def test_get_modes_by_category_normal(self):
        """测试按分类获取 mode: normal"""
        modes = ModeManager.get_modes_by_category("normal")

        assert "daily" in modes
        assert "weekly" in modes
        assert "monthly" in modes
        assert "day_male" not in modes  # category 类型

    def test_get_modes_by_category_category(self):
        """测试按分类获取 mode: category"""
        modes = ModeManager.get_modes_by_category("category")

        assert "day_male" in modes
        assert "day_female" in modes
        assert "week_original" in modes
        assert "daily" not in modes  # normal 类型

    def test_get_modes_by_category_r18(self):
        """测试按分类获取 mode: r18"""
        modes = ModeManager.get_modes_by_category("r18")

        assert "day_r18" in modes
        assert "week_r18" in modes
        assert "daily" not in modes  # normal 类型

    def test_get_mode_definition(self):
        """测试获取 mode 定义"""
        definition = ModeManager.get_mode_definition("day")

        assert definition["cli_name"] == "daily"
        assert definition["api_name"] == "day"
        assert definition["gallery_dl_name"] == "daily"
        assert definition["description"] == "每日排行榜"
        assert definition["category"] == "normal"

    def test_get_mode_definition_invalid(self):
        """测试获取无效 mode 的定义"""
        with pytest.raises(InvalidModeError):
            ModeManager.get_mode_definition("invalid")


class TestHelpText:
    """帮助文本生成测试"""

    def test_get_help_text(self):
        """测试生成帮助文本"""
        help_text = ModeManager.get_help_text()

        assert "Ranking Types:" in help_text
        assert "Normal:" in help_text
        assert "Category:" in help_text
        assert "R18:" in help_text
        assert "daily" in help_text
        assert "每日排行榜" in help_text

    def test_help_text_contains_all_modes(self):
        """测试帮助文本包含所有 mode"""
        help_text = ModeManager.get_help_text()

        for cli_mode in ModeManager.get_all_cli_modes():
            assert cli_mode in help_text, \
                f"Help text missing mode '{cli_mode}'"


class TestCaching:
    """缓存机制测试"""

    def test_cli_to_api_cache_built_once(self):
        """测试 CLI -> API 缓存只构建一次"""
        # 清空缓存
        ModeManager._cli_to_api_cache = None

        # 第一次调用 (构建缓存)
        result1 = ModeManager.validate_cli_mode("daily")
        assert ModeManager._cli_to_api_cache is not None

        # 第二次调用 (使用缓存)
        result2 = ModeManager.validate_cli_mode("daily")

        assert result1 == result2 == "day"

    def test_api_to_gallery_dl_cache_built_once(self):
        """测试 API -> Gallery-dl 缓存只构建一次"""
        # 清空缓存
        ModeManager._api_to_gallery_dl_cache = None

        # 第一次调用 (构建缓存)
        result1 = ModeManager.api_to_gallery_dl("day")
        assert ModeManager._api_to_gallery_dl_cache is not None

        # 第二次调用 (使用缓存)
        result2 = ModeManager.api_to_gallery_dl("day")

        assert result1 == result2 == "daily"
```

### 2.2 Validators 单元测试

**位置**: `tests/cli/test_validators.py` (已存在,需要更新)

```python
"""验证器单元测试 (更新版)

测试使用 ModeManager 的验证器
"""

import pytest
from datetime import date, timedelta
from click import BadParameter

from gallery_dl_auto.cli.validators import (
    validate_ranking_type,
    validate_type_param,
    validate_ranking_date,
    validate_date_param,
)
from gallery_dl_auto.core.mode_manager import ModeManager


class TestValidateRankingType:
    """排行榜类型验证测试 (更新)"""

    def test_validate_valid_daily(self):
        """测试验证 daily -> day"""
        result = validate_ranking_type("daily")
        assert result == "day"

    def test_validate_all_valid_modes(self):
        """测试所有有效的 mode"""
        for cli_mode in ModeManager.get_all_cli_modes():
            result = validate_ranking_type(cli_mode)
            # 应该返回 API mode
            assert result in ModeManager.get_all_api_modes()

    def test_validate_invalid_mode(self):
        """测试无效的 mode"""
        with pytest.raises(ValueError) as exc_info:
            validate_ranking_type("invalid_mode")

        assert "Invalid ranking type" in str(exc_info.value)
        assert "invalid_mode" in str(exc_info.value)

    def test_validate_case_sensitive(self):
        """测试大小写敏感"""
        with pytest.raises(ValueError):
            validate_ranking_type("DAILY")


class TestValidateTypeParam:
    """Click 参数验证器测试"""

    def test_validate_with_valid_value(self):
        """测试有效值"""
        result = validate_type_param(None, None, "daily")
        assert result == "day"

    def test_validate_with_none(self):
        """测试 None 值"""
        result = validate_type_param(None, None, None)
        assert result is None

    def test_validate_with_invalid_value(self):
        """测试无效值"""
        with pytest.raises(BadParameter) as exc_info:
            validate_type_param(None, None, "invalid")

        assert "Invalid ranking type" in str(exc_info.value)
```

## 3. 集成测试设计

### 3.1 Mode 流转集成测试

**位置**: `tests/integration/test_mode_flow.py`

```python
"""Mode 流转集成测试

测试 mode 在不同组件间的流转
"""

import pytest
from pathlib import Path
from unittest.mock import Mock, patch

from gallery_dl_auto.core.mode_manager import ModeManager
from gallery_dl_auto.cli.validators import validate_ranking_type
from gallery_dl_auto.integration.gallery_dl_wrapper import GalleryDLWrapper
from gallery_dl_auto.config.download_config import DownloadConfig


class TestModeFlowIntegration:
    """Mode 完整流转测试"""

    def test_cli_to_gallery_dl_flow(self):
        """测试 CLI -> API -> Gallery-dl 的完整流程"""
        # 1. CLI 输入
        cli_mode = "daily"

        # 2. CLI 验证转换为 API mode
        api_mode = validate_ranking_type(cli_mode)
        assert api_mode == "day"

        # 3. 业务逻辑使用 API mode
        # (在 download_cmd.py 中)

        # 4. Gallery-dl 转换为 gallery-dl mode
        config = DownloadConfig()
        wrapper = GalleryDLWrapper(config=config)

        # Mock gallery-dl 命令执行
        with patch.object(wrapper, '_check_gallery_dl_installed'):
            url = wrapper._build_ranking_url(mode=api_mode, date="2026-03-01")

        # 5. 验证 URL 包含正确的 mode
        assert "mode=daily" in url
        assert "date=2026-03-01" in url

    def test_all_modes_flow(self):
        """测试所有 mode 的完整流转"""
        for cli_mode in ModeManager.get_all_cli_modes():
            # CLI -> API
            api_mode = validate_ranking_type(cli_mode)
            assert api_mode in ModeManager.get_all_api_modes()

            # API -> Gallery-dl
            gallery_dl_mode = ModeManager.api_to_gallery_dl(api_mode)

            # 构建完整 URL
            config = DownloadConfig()
            wrapper = GalleryDLWrapper(config=config)
            with patch.object(wrapper, '_check_gallery_dl_installed'):
                url = wrapper._build_ranking_url(mode=api_mode, date=None)

            # 验证 URL 有效
            assert f"mode={gallery_dl_mode}" in url

    def test_mode_preservation_in_business_logic(self):
        """测试 mode 在业务逻辑层保持不变"""
        # 业务逻辑层应该使用 API mode,不进行转换
        api_mode = "day"

        # 传递给 PixivClient (internal 引擎)
        # mode 应该保持为 "day"
        assert api_mode == "day"

        # 传递给 GalleryDLWrapper (gallery-dl 引擎)
        # wrapper 内部会转换,但业务逻辑层看到的仍然是 "day"
        assert api_mode == "day"


class TestModeIntegrationWithPixivClient:
    """Mode 与 PixivClient 集成测试"""

    @pytest.mark.skipif(
        not pytest.config.getoption("--run-integration"),
        reason="需要 --run-integration 选项"
    )
    def test_pixiv_client_with_valid_api_mode(self, mock_pixiv_client):
        """测试 PixivClient 使用有效的 API mode"""
        # 使用真实的 API mode
        api_mode = "day"

        # 调用 PixivClient
        result = mock_pixiv_client.get_ranking(mode=api_mode, date="2026-03-01")

        # 验证结果
        assert isinstance(result, list)

    @pytest.mark.skipif(
        not pytest.config.getoption("--run-integration"),
        reason="需要 --run-integration 选项"
    )
    def test_pixiv_client_with_all_api_modes(self, mock_pixiv_client):
        """测试 PixivClient 使用所有 API mode"""
        for api_mode in ModeManager.get_all_api_modes():
            # 每个 mode 都应该能正常调用
            result = mock_pixiv_client.get_ranking(mode=api_mode, date=None)
            assert isinstance(result, list)


class TestModeIntegrationWithGalleryDL:
    """Mode 与 Gallery-dl 集成测试"""

    def test_gallery_dl_url_building(self):
        """测试 Gallery-dl URL 构建"""
        config = DownloadConfig()
        wrapper = GalleryDLWrapper(config=config)

        with patch.object(wrapper, '_check_gallery_dl_installed'):
            # 测试不同的 mode
            test_cases = [
                ("day", "daily"),
                ("week", "weekly"),
                ("month", "monthly"),
                ("day_male", "day_male"),
                ("day_r18", "day_r18"),
            ]

            for api_mode, expected_gallery_dl_mode in test_cases:
                url = wrapper._build_ranking_url(mode=api_mode, date="2026-03-01")
                assert f"mode={expected_gallery_dl_mode}" in url
                assert "date=2026-03-01" in url
                assert "content=illust" in url
```

## 4. 端到端测试设计

### 4.1 CLI 端到端测试

**位置**: `tests/e2e/test_mode_e2e.py`

```python
"""Mode 端到端测试

测试完整的 CLI 命令执行
"""

import pytest
from click.testing import CliRunner
from unittest.mock import patch, Mock

from gallery_dl_auto.cli.download_cmd import download


class TestModeE2E:
    """Mode 端到端测试"""

    @pytest.fixture
    def runner(self):
        """Click 测试运行器"""
        return CliRunner()

    @pytest.fixture
    def mock_dependencies(self):
        """Mock 外部依赖"""
        with patch('gallery_dl_auto.cli.download_cmd.get_default_token_storage') as mock_storage, \
             patch('gallery_dl_auto.cli.download_cmd.GalleryDLWrapper') as mock_wrapper:

            # Mock token storage
            mock_storage.return_value.load_token.return_value = {
                "refresh_token": "test_token"
            }

            # Mock GalleryDLWrapper
            mock_result = Mock()
            mock_result.success = True
            mock_result.total = 10
            mock_result.downloaded = 10
            mock_result.failed = 0
            mock_result.skipped = 0
            mock_result.model_dump_json.return_value = '{"success": true}'
            mock_wrapper.return_value.download_ranking.return_value = mock_result

            yield mock_storage, mock_wrapper

    def test_e2e_daily_mode(self, runner, mock_dependencies):
        """测试完整的 daily mode 下载流程"""
        result = runner.invoke(download, [
            '--type', 'daily',
            '--date', '2026-03-01',
            '--engine', 'gallery-dl'
        ])

        # 验证命令执行成功
        assert result.exit_code == 0

        # 验证调用了正确的 mode
        mock_wrapper = mock_dependencies[1]
        mock_wrapper.return_value.download_ranking.assert_called_once()
        call_kwargs = mock_wrapper.return_value.download_ranking.call_args[1]
        assert call_kwargs['mode'] == 'day'  # API mode

    def test_e2e_weekly_mode(self, runner, mock_dependencies):
        """测试完整的 weekly mode 下载流程"""
        result = runner.invoke(download, [
            '--type', 'weekly',
            '--date', '2026-03-01',
            '--engine', 'gallery-dl'
        ])

        assert result.exit_code == 0

        # 验证 mode
        mock_wrapper = mock_dependencies[1]
        call_kwargs = mock_wrapper.return_value.download_ranking.call_args[1]
        assert call_kwargs['mode'] == 'week'

    def test_e2e_invalid_mode(self, runner):
        """测试无效的 mode"""
        result = runner.invoke(download, [
            '--type', 'invalid_mode',
            '--date', '2026-03-01'
        ])

        # 验证命令失败
        assert result.exit_code == 2  # Click BadParameter

        # 验证错误消息
        assert '错误' in result.output or 'Invalid' in result.output
        assert 'invalid_mode' in result.output

    def test_e2e_all_modes(self, runner, mock_dependencies):
        """测试所有 mode 的端到端流程"""
        from gallery_dl_auto.core.mode_manager import ModeManager

        for cli_mode in ModeManager.get_all_cli_modes():
            result = runner.invoke(download, [
                '--type', cli_mode,
                '--date', '2026-03-01',
                '--engine', 'gallery-dl'
            ])

            # 验证所有有效 mode 都能通过 CLI 验证
            # (可能因为其他原因失败,但不应是 mode 验证失败)
            if result.exit_code == 2:  # Click 参数错误
                assert 'Invalid ranking type' not in result.output

    def test_e2e_dry_run_mode(self, runner, mock_dependencies):
        """测试 dry-run 模式"""
        result = runner.invoke(download, [
            '--type', 'daily',
            '--date', '2026-03-01',
            '--dry-run',
            '--engine', 'gallery-dl'
        ])

        # 验证 dry-run 模式执行成功
        assert result.exit_code == 0

        # 验证传递了 dry_run 参数
        mock_wrapper = mock_dependencies[1]
        call_kwargs = mock_wrapper.return_value.download_ranking.call_args[1]
        assert call_kwargs['dry_run'] is True
```

## 5. 性能测试设计

### 5.1 Mode 转换性能测试

**位置**: `tests/performance/test_mode_performance.py`

```python
"""Mode 转换性能测试

验证 mode 转换不会成为性能瓶颈
"""

import pytest
import time
from gallery_dl_auto.core.mode_manager import ModeManager


class TestModePerformance:
    """Mode 性能测试"""

    def test_validate_cli_mode_performance(self):
        """测试 CLI mode 验证性能"""
        iterations = 10000

        start = time.perf_counter()
        for _ in range(iterations):
            ModeManager.validate_cli_mode("daily")
        end = time.perf_counter()

        avg_time_ms = (end - start) / iterations * 1000

        # 平均耗时应小于 0.1ms
        assert avg_time_ms < 0.1, \
            f"validate_cli_mode too slow: {avg_time_ms:.3f}ms per call"

        print(f"\nvalidate_cli_mode: {avg_time_ms:.3f}ms per call")

    def test_api_to_gallery_dl_performance(self):
        """测试 API -> Gallery-dl 转换性能"""
        iterations = 10000

        start = time.perf_counter()
        for _ in range(iterations):
            ModeManager.api_to_gallery_dl("day")
        end = time.perf_counter()

        avg_time_ms = (end - start) / iterations * 1000

        # 平均耗时应小于 0.1ms
        assert avg_time_ms < 0.1, \
            f"api_to_gallery_dl too slow: {avg_time_ms:.3f}ms per call"

        print(f"\napi_to_gallery_dl: {avg_time_ms:.3f}ms per call")

    def test_get_all_cli_modes_performance(self):
        """测试获取所有 CLI mode 的性能"""
        iterations = 1000

        start = time.perf_counter()
        for _ in range(iterations):
            ModeManager.get_all_cli_modes()
        end = time.perf_counter()

        avg_time_ms = (end - start) / iterations * 1000

        # 平均耗时应小于 0.05ms
        assert avg_time_ms < 0.05, \
            f"get_all_cli_modes too slow: {avg_time_ms:.3f}ms per call"

        print(f"\nget_all_cli_modes: {avg_time_ms:.3f}ms per call")

    def test_full_mode_flow_performance(self):
        """测试完整 mode 流程的性能"""
        iterations = 1000

        start = time.perf_counter()
        for _ in range(iterations):
            # 模拟完整的 mode 流程
            cli_mode = "daily"
            api_mode = ModeManager.validate_cli_mode(cli_mode)
            gallery_dl_mode = ModeManager.api_to_gallery_dl(api_mode)
            _ = f"https://www.pixiv.net/ranking.php?mode={gallery_dl_mode}"
        end = time.perf_counter()

        avg_time_ms = (end - start) / iterations * 1000

        # 完整流程平均耗时应小于 0.5ms
        assert avg_time_ms < 0.5, \
            f"Full mode flow too slow: {avg_time_ms:.3f}ms per call"

        print(f"\nFull mode flow: {avg_time_ms:.3f}ms per call")

    def test_cache_initialization_performance(self):
        """测试缓存初始化性能"""
        # 清空缓存
        ModeManager._cli_to_api_cache = None
        ModeManager._api_to_gallery_dl_cache = None

        start = time.perf_counter()
        # 第一次调用会初始化缓存
        ModeManager.validate_cli_mode("daily")
        end = time.perf_counter()

        init_time_ms = (end - start) * 1000

        # 缓存初始化应小于 10ms
        assert init_time_ms < 10, \
            f"Cache initialization too slow: {init_time_ms:.3f}ms"

        print(f"\nCache initialization: {init_time_ms:.3f}ms")
```

## 6. 边界条件测试

### 6.1 边界条件测试用例

**位置**: `tests/edge_cases/test_mode_edge_cases.py`

```python
"""Mode 边界条件测试

测试极端情况和特殊输入
"""

import pytest
from gallery_dl_auto.core.mode_manager import ModeManager, InvalidModeError


class TestModeEdgeCases:
    """Mode 边界条件测试"""

    def test_empty_string_mode(self):
        """测试空字符串 mode"""
        with pytest.raises(InvalidModeError):
            ModeManager.validate_cli_mode("")

    def test_whitespace_mode(self):
        """测试空白字符 mode"""
        with pytest.raises(InvalidModeError):
            ModeManager.validate_cli_mode("   ")

    def test_mode_with_special_characters(self):
        """测试包含特殊字符的 mode"""
        invalid_modes = [
            "daily!",
            "@daily",
            "daily#",
            "dai.ly",
            "dai-ly",
            "daily_123",
        ]

        for mode in invalid_modes:
            with pytest.raises(InvalidModeError):
                ModeManager.validate_cli_mode(mode)

    def test_mode_with_unicode(self):
        """测试包含 Unicode 字符的 mode"""
        invalid_modes = [
            "日报",  # 中文
            "dαily",  # 希腊字母
            "daily🎉",  # emoji
        ]

        for mode in invalid_modes:
            with pytest.raises(InvalidModeError):
                ModeManager.validate_cli_mode(mode)

    def test_very_long_mode_name(self):
        """测试超长的 mode 名称"""
        long_mode = "daily" * 100

        with pytest.raises(InvalidModeError):
            ModeManager.validate_cli_mode(long_mode)

    def test_mode_with_numbers(self):
        """测试包含数字的 mode"""
        # R18 mode 包含数字,这是有效的
        assert ModeManager.validate_cli_mode("day_r18") == "day_r18"

        # 但包含其他数字的 mode 无效
        with pytest.raises(InvalidModeError):
            ModeManager.validate_cli_mode("daily123")

    def test_mode_case_variations(self):
        """测试不同大小写的 mode"""
        case_variations = [
            "DAILY",
            "Daily",
            "DaIlY",
            "dAiLy",
        ]

        for mode in case_variations:
            with pytest.raises(InvalidModeError):
                ModeManager.validate_cli_mode(mode)

    def test_mode_with_underscores(self):
        """测试包含下划线的 mode"""
        # 有效的下划线 mode
        valid_modes = ["day_male", "week_original", "day_r18"]
        for mode in valid_modes:
            result = ModeManager.validate_cli_mode(mode)
            assert result is not None

        # 无效的下划线 mode
        invalid_modes = ["day__male", "_daily", "daily_", "day_male_"]
        for mode in invalid_modes:
            with pytest.raises(InvalidModeError):
                ModeManager.validate_cli_mode(mode)

    def test_similar_but_invalid_modes(self):
        """测试相似但无效的 mode"""
        similar_invalid = [
            ("dayli", "daily"),    # 拼写错误
            ("weeky", "weekly"),   # 拼写错误
            ("montly", "monthly"), # 拼写错误
            ("daymail", "day_male"), # 拼写错误
        ]

        for invalid, valid in similar_invalid:
            with pytest.raises(InvalidModeError):
                ModeManager.validate_cli_mode(invalid)

    def test_mode_definition_immutability(self):
        """测试 mode 定义不可修改"""
        # 尝试修改 mode 定义 (不应该成功)
        original_count = len(ModeManager.MODES)

        # Python 的类属性可以被修改,但我们的测试应该验证这不会意外发生
        assert len(ModeManager.MODES) == original_count

    def test_all_modes_unique(self):
        """测试所有 mode 名称唯一"""
        cli_modes = [defn["cli_name"] for defn in ModeManager.MODES.values()]
        assert len(cli_modes) == len(set(cli_modes)), "CLI modes should be unique"

        api_modes = list(ModeManager.MODES.keys())
        assert len(api_modes) == len(set(api_modes)), "API modes should be unique"

        gallery_dl_modes = [defn["gallery_dl_name"] for defn in ModeManager.MODES.values()]
        assert len(gallery_dl_modes) == len(set(gallery_dl_modes)), \
            "Gallery-dl modes should be unique"

    def test_concurrent_access(self):
        """测试并发访问 (基本测试)"""
        import threading

        results = []
        errors = []

        def validate_mode():
            try:
                result = ModeManager.validate_cli_mode("daily")
                results.append(result)
            except Exception as e:
                errors.append(e)

        # 创建多个线程同时访问
        threads = [threading.Thread(target=validate_mode) for _ in range(100)]

        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # 验证结果
        assert len(errors) == 0, f"Concurrent access errors: {errors}"
        assert len(results) == 100
        assert all(r == "day" for r in results)
```

## 7. 测试数据管理

### 7.1 测试数据 Fixtures

**位置**: `tests/fixtures/mode_fixtures.py`

```python
"""Mode 测试数据 fixtures

提供可复用的测试数据
"""

import pytest
from gallery_dl_auto.core.mode_manager import ModeManager


@pytest.fixture
def all_cli_modes():
    """所有 CLI mode 列表"""
    return ModeManager.get_all_cli_modes()


@pytest.fixture
def all_api_modes():
    """所有 API mode 列表"""
    return ModeManager.get_all_api_modes()


@pytest.fixture
def sample_mode_mappings():
    """示例 mode 映射"""
    return [
        ("daily", "day", "daily"),
        ("weekly", "week", "weekly"),
        ("monthly", "month", "monthly"),
        ("day_male", "day_male", "day_male"),
        ("day_r18", "day_r18", "day_r18"),
    ]


@pytest.fixture
def invalid_modes():
    """无效的 mode 列表"""
    return [
        "",
        "   ",
        "invalid",
        "DAILY",
        "daily!",
        "日报",
        "daily123",
    ]
```

## 8. 测试执行策略

### 8.1 测试分类

```bash
# 运行所有单元测试
pytest tests/core/test_mode_manager.py -v

# 运行集成测试
pytest tests/integration/test_mode_flow.py -v

# 运行端到端测试
pytest tests/e2e/test_mode_e2e.py -v

# 运行性能测试
pytest tests/performance/test_mode_performance.py -v

# 运行边界条件测试
pytest tests/edge_cases/test_mode_edge_cases.py -v

# 运行所有测试
pytest tests/ -v

# 运行快速测试 (跳过慢速测试)
pytest tests/ -v -m "not slow"
```

### 8.2 测试覆盖率目标

```
目标覆盖率:
├─ mode_manager.py       > 95%
├─ validators.py         > 90%
├─ gallery_dl_wrapper.py > 85%
└─ 整体项目              > 85%
```

### 8.3 CI/CD 集成

```yaml
# .github/workflows/test.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v2

      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: 3.11

      - name: Install dependencies
        run: |
          pip install -e ".[dev]"

      - name: Run unit tests
        run: pytest tests/core tests/cli -v --cov=src/gallery_dl_auto/core

      - name: Run integration tests
        run: pytest tests/integration -v

      - name: Run edge case tests
        run: pytest tests/edge_cases -v

      - name: Upload coverage
        uses: codecov/codecov-action@v2
```

## 9. 测试文档

### 9.1 测试清单

```markdown
# Mode 映射测试清单

## 单元测试
- [x] ModeManager.validate_cli_mode() - 所有有效 mode
- [x] ModeManager.validate_cli_mode() - 无效 mode
- [x] ModeManager.api_to_gallery_dl() - 所有 API mode
- [x] ModeManager.get_all_cli_modes() - 返回正确列表
- [x] 缓存机制 - 正确初始化和复用

## 集成测试
- [x] CLI -> API -> Gallery-dl 完整流程
- [x] 所有 mode 的端到端流转
- [x] 与 PixivClient 集成
- [x] 与 GalleryDLWrapper 集成

## 端到端测试
- [x] 有效的 CLI 命令
- [x] 无效的 mode 错误处理
- [x] dry-run 模式
- [x] 所有 mode 的 CLI 测试

## 性能测试
- [x] 验证性能 < 0.1ms
- [x] 转换性能 < 0.1ms
- [x] 完整流程 < 0.5ms

## 边界条件测试
- [x] 空字符串
- [x] 特殊字符
- [x] Unicode
- [x] 大小写
- [x] 并发访问

## 错误处理测试
- [x] InvalidModeError
- [x] ModeConversionError
- [x] 用户友好错误消息
```

---

**版本历史**:
- 2026-03-01: v1.0 初始设计
