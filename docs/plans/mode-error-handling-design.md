# Mode 映射 - 错误处理设计

## 1. 错误场景分析

### 1.1 错误分类

| 错误类型 | 发生位置 | 触发条件 | 严重程度 | 处理策略 |
|---------|---------|---------|---------|---------|
| 无效的 CLI mode | validators.py | 用户输入不存在的 mode | 用户错误 | 返回友好提示 |
| 无效的 API mode | 业务逻辑层 | 代码 bug 导致传入无效 mode | 内部错误 | 记录日志 + 返回错误 |
| Mode 转换失败 | ModeManager | 映射表不完整 | 内部错误 | 记录日志 + 返回错误 |
| Gallery-dl mode 无效 | gallery_dl_wrapper.py | Gallery-dl 不支持该 mode | 兼容性错误 | 记录日志 + 降级处理 |

### 1.2 用户错误 vs 系统错误

**用户错误** (User Error):
- 用户输入了无效的 mode
- 应该提供清晰的错误提示和正确的用法
- 不需要记录 ERROR 日志 (INFO 级别即可)

**系统错误** (System Error):
- 代码 bug 导致 mode 值错误
- 应该记录 ERROR 日志
- 返回通用错误提示,建议联系开发者

## 2. 错误类型定义

### 2.1 自定义异常类

```python
# src/gallery_dl_auto/core/mode_errors.py

class ModeError(Exception):
    """Mode 相关错误的基类

    所有 mode 相关的自定义异常都继承此类
    """
    def __init__(self, message: str, mode: str | None = None):
        self.message = message
        self.mode = mode
        super().__init__(self.message)

    def __str__(self) -> str:
        if self.mode:
            return f"{self.message} (mode: {self.mode})"
        return self.message


class InvalidModeError(ModeError):
    """无效的 mode 值

    当 mode 不在允许的列表中时抛出
    """
    def __init__(
        self,
        mode: str,
        valid_modes: list[str],
        mode_type: str = "CLI"
    ):
        self.mode = mode
        self.valid_modes = valid_modes
        self.mode_type = mode_type

        message = (
            f"Invalid {mode_type} mode '{mode}'. "
            f"Valid modes: {', '.join(sorted(valid_modes))}"
        )
        super().__init__(message, mode)

    def to_user_friendly_message(self) -> str:
        """生成用户友好的错误消息

        Returns:
            str: 格式化的错误消息,包含建议
        """
        lines = [
            f"错误: 无效的排行榜类型 '{self.mode}'",
            "",
            "有效的排行榜类型:",
        ]

        # 按分类显示
        categories = {
            "常规": ["daily", "weekly", "monthly"],
            "分类": [
                "day_male", "day_female",
                "week_original", "week_rookie", "day_manga"
            ],
            "R18": [
                "day_r18", "day_male_r18", "day_female_r18",
                "week_r18", "week_r18g"
            ]
        }

        for category, modes in categories.items():
            valid_in_category = [m for m in modes if m in self.valid_modes]
            if valid_in_category:
                lines.append(f"  {category}:")
                for m in valid_in_category:
                    lines.append(f"    - {m}")

        lines.extend([
            "",
            f"示例: pixiv-downloader download --type daily --date 2026-03-01"
        ])

        return "\n".join(lines)


class ModeConversionError(ModeError):
    """Mode 转换失败

    当无法将 mode 从一种格式转换为另一种格式时抛出
    """
    def __init__(
        self,
        source_mode: str,
        source_type: str,
        target_type: str,
        reason: str = "unknown"
    ):
        self.source_mode = source_mode
        self.source_type = source_type
        self.target_type = target_type
        self.reason = reason

        message = (
            f"Cannot convert mode '{source_mode}' "
            f"from {source_type} to {target_type}: {reason}"
        )
        super().__init__(message, source_mode)

    def to_error_response(self) -> dict:
        """转换为错误响应格式

        Returns:
            dict: 结构化错误响应
        """
        return {
            "error_code": "MODE_CONVERSION_ERROR",
            "error_type": "InternalError",
            "message": f"Mode 转换失败: {self.source_mode}",
            "suggestion": "这是一个内部错误,请联系开发者",
            "severity": "error",
            "details": {
                "source_mode": self.source_mode,
                "source_type": self.source_type,
                "target_type": self.target_type,
                "reason": self.reason
            }
        }


class UnsupportedModeError(ModeError):
    """不支持的 mode

    当 mode 在理论上有效,但在当前上下文中不支持时抛出
    例如: 某个 mode 在 Pixiv API 有效,但 gallery-dl 不支持
    """
    def __init__(
        self,
        mode: str,
        context: str,
        supported_modes: list[str] | None = None
    ):
        self.mode = mode
        self.context = context
        self.supported_modes = supported_modes or []

        message = f"Mode '{mode}' is not supported in {context}"
        if self.supported_modes:
            message += f". Supported modes: {', '.join(self.supported_modes)}"

        super().__init__(message, mode)

    def to_user_friendly_message(self) -> str:
        """生成用户友好的错误消息"""
        lines = [
            f"错误: 排行榜类型 '{self.mode}' 在 {self.context} 中不受支持",
            ""
        ]

        if self.supported_modes:
            lines.append("支持的排行榜类型:")
            for mode in self.supported_modes:
                lines.append(f"  - {mode}")
            lines.append("")

        lines.append("建议: 使用 --engine 参数切换下载引擎")

        return "\n".join(lines)
```

## 3. 错误处理策略

### 3.1 CLI 层错误处理

**位置**: `src/gallery_dl_auto/cli/validators.py`

```python
import click
from gallery_dl_auto.core.mode_manager import ModeManager
from gallery_dl_auto.core.mode_errors import InvalidModeError

def validate_type_param(ctx, param, value: str | None) -> str | None:
    """Click 参数验证器: 排行榜类型

    错误处理策略:
    1. 捕获 InvalidModeError (用户错误)
    2. 生成用户友好的错误消息
    3. 转换为 click.BadParameter (Click 标准)
    """
    if value is None:
        return None

    try:
        # 调用 ModeManager 验证
        return ModeManager.validate_cli_mode(value)

    except InvalidModeError as e:
        # 用户错误: 输入了无效的 mode
        # 生成友好的错误消息
        user_message = e.to_user_friendly_message()

        # 转换为 Click 标准错误
        raise click.BadParameter(user_message) from e

    except Exception as e:
        # 系统错误: 不应该发生的异常
        # 记录日志并返回通用错误
        logger = logging.getLogger("gallery_dl_auto")
        logger.error(
            f"Unexpected error in validate_type_param: {e}",
            exc_info=True
        )

        raise click.BadParameter(
            "参数验证时发生内部错误,请联系开发者"
        ) from e
```

### 3.2 业务逻辑层错误处理

**位置**: `src/gallery_dl_auto/cli/download_cmd.py`

```python
from gallery_dl_auto.core.mode_errors import ModeConversionError
from gallery_dl_auto.models.error_response import StructuredError
from gallery_dl_auto.utils.error_codes import ErrorCode

def _download_with_gallery_dl(
    mode: str,
    date: str | None,
    # ...
) -> None:
    """使用 gallery-dl 引擎下载

    错误处理策略:
    1. 捕获 mode 相关异常
    2. 转换为 StructuredError
    3. 输出 JSON 格式错误并退出
    """
    try:
        wrapper = GalleryDLWrapper(config=download_config)
        result = wrapper.download_ranking(
            mode=mode,
            date=date,
            # ...
        )
        print(result.model_dump_json(indent=2, ensure_ascii=False))

    except ModeConversionError as e:
        # Mode 转换失败 (系统错误)
        logger.error(f"Mode conversion failed: {e}", exc_info=True)

        error_response = e.to_error_response()
        print(json.dumps(error_response, ensure_ascii=False, indent=2))
        sys.exit(2)

    except Exception as e:
        # 其他未预期的错误
        logger.error(f"Unexpected error: {e}", exc_info=True)

        error = StructuredError(
            error_code=ErrorCode.INTERNAL_ERROR,
            error_type="DownloadError",
            message=f"下载失败: {e}",
            suggestion="查看日志了解详细错误",
            severity="error",
            original_error=str(e)
        )
        print(error.model_dump_json(indent=2, ensure_ascii=False))
        sys.exit(2)
```

### 3.3 Gallery-dl 层错误处理

**位置**: `src/gallery_dl_auto/integration/gallery_dl_wrapper.py`

```python
from gallery_dl_auto.core.mode_manager import ModeManager
from gallery_dl_auto.core.mode_errors import (
    InvalidModeError,
    UnsupportedModeError,
    ModeConversionError
)

def _build_ranking_url(self, mode: str, date: str | None) -> str:
    """构建排行榜 URL

    错误处理策略:
    1. 验证 mode 有效性
    2. 转换为 gallery-dl mode
    3. 处理转换失败
    """
    try:
        # 转换: API mode -> Gallery-dl mode
        gallery_dl_mode = ModeManager.api_to_gallery_dl(mode)

    except InvalidModeError as e:
        # API mode 无效 (不应该发生,这是 bug)
        logger.error(
            f"Invalid API mode passed to gallery_dl_wrapper: {mode}",
            exc_info=True
        )
        raise ModeConversionError(
            source_mode=mode,
            source_type="API",
            target_type="Gallery-dl",
            reason=f"Invalid API mode: {mode}"
        ) from e

    # 检查 gallery-dl 是否支持该 mode
    # (未来扩展: 可以维护 gallery-dl 支持的 mode 列表)
    supported_by_gallery_dl = [
        "daily", "weekly", "monthly",
        "day_male", "day_female", "week_original", "week_rookie",
        "day_r18", "day_male_r18", "day_female_r18", "week_r18", "week_r18g"
    ]

    if gallery_dl_mode not in supported_by_gallery_dl:
        logger.warning(
            f"Mode '{gallery_dl_mode}' may not be supported by gallery-dl"
        )
        # 不抛出异常,让 gallery-dl 自己处理
        # 如果 gallery-dl 不支持,会返回错误

    # 构建 URL
    base_url = f"https://www.pixiv.net/ranking.php?mode={gallery_dl_mode}&content=illust"
    if date:
        base_url += f"&date={date}"

    return base_url
```

## 4. 错误消息设计

### 4.1 用户错误消息

**格式**:
```
错误: <简短描述>

<详细说明>

建议:
  - <建议 1>
  - <建议 2>

示例: <正确的使用示例>
```

**示例 1: 无效的 CLI mode**

```
错误: 无效的排行榜类型 'invalid_mode'

有效的排行榜类型:
  常规:
    - daily: 每日排行榜
    - weekly: 每周排行榜
    - monthly: 每月排行榜
  分类:
    - day_male: 男性喜爱排行榜
    - day_female: 女性喜爱排行榜
    - week_original: 原创排行榜
    - week_rookie: 新人排行榜
    - day_manga: 漫画排行榜
  R18:
    - day_r18: R18 每日排行榜
    - day_male_r18: R18 男性喜爱排行榜
    - day_female_r18: R18 女性喜爱排行榜
    - week_r18: R18 每周排行榜
    - week_r18g: R18G 每周排行榜

示例: pixiv-downloader download --type daily --date 2026-03-01
```

**示例 2: 未来日期错误**

```
错误: 日期 '2026-03-10' 是未来日期

排行榜数据只提供过去的日期,无法获取未来的排行榜。

建议:
  - 使用今天或过去的日期
  - 格式: YYYY-MM-DD

示例: pixiv-downloader download --type daily --date 2026-02-28
```

### 4.2 系统错误消息

**格式** (JSON):
```json
{
  "error_code": "MODE_CONVERSION_ERROR",
  "error_type": "InternalError",
  "message": "Mode 转换失败: invalid_api_mode",
  "suggestion": "这是一个内部错误,请联系开发者",
  "severity": "error",
  "details": {
    "source_mode": "invalid_api_mode",
    "source_type": "API",
    "target_type": "Gallery-dl",
    "reason": "Invalid API mode"
  }
}
```

## 5. 错误恢复策略

### 5.1 降级策略

**场景**: Gallery-dl 不支持某个 mode

**策略**:
```python
def _build_ranking_url(self, mode: str, date: str | None) -> str:
    """构建排行榜 URL (带降级策略)"""
    try:
        gallery_dl_mode = ModeManager.api_to_gallery_dl(mode)
    except InvalidModeError:
        # 降级策略 1: 尝试使用类似的 mode
        fallback_map = {
            "month": "weekly",  # monthly 不支持,降级为 weekly
        }
        if mode in fallback_map:
            logger.warning(
                f"Mode '{mode}' not supported, "
                f"falling back to '{fallback_map[mode]}'"
            )
            gallery_dl_mode = fallback_map[mode]
        else:
            # 降级策略 2: 直接使用 API mode (让 gallery-dl 尝试)
            logger.warning(
                f"Using API mode '{mode}' directly as fallback"
            )
            gallery_dl_mode = mode

    # 构建 URL
    # ...
```

### 5.2 重试策略

**场景**: 暂时性错误 (如网络问题)

**策略**: 在更高层次处理 (如 `retry_handler.py`),mode 层不重试

## 6. 错误日志记录

### 6.1 日志级别

| 错误类型 | 日志级别 | 记录内容 |
|---------|---------|---------|
| 用户输入无效 mode | INFO | 用户输入的 mode 和有效 mode 列表 |
| API mode 无效 (内部错误) | ERROR | 完整的异常堆栈 |
| Mode 转换失败 | ERROR | 转换详情和异常堆栈 |
| Gallery-dl 不支持 mode | WARNING | mode 名称和建议 |

### 6.2 日志格式

```python
import logging
import json

logger = logging.getLogger("gallery_dl_auto")

def log_mode_error(error: ModeError, level: str = "ERROR"):
    """记录 mode 错误日志

    Args:
        error: Mode 错误对象
        level: 日志级别
    """
    log_data = {
        "error_type": type(error).__name__,
        "mode": error.mode,
        "message": error.message,
    }

    if isinstance(error, InvalidModeError):
        log_data["valid_modes"] = error.valid_modes
        log_data["mode_type"] = error.mode_type
    elif isinstance(error, ModeConversionError):
        log_data["source_type"] = error.source_type
        log_data["target_type"] = error.target_type
        log_data["reason"] = error.reason

    # 记录日志
    log_func = getattr(logger, level.lower())
    log_func(f"Mode error: {json.dumps(log_data, ensure_ascii=False)}")

    # 如果是 ERROR 级别,记录堆栈
    if level == "ERROR":
        logger.error("Stack trace:", exc_info=True)
```

### 6.3 日志示例

**INFO 级别 (用户错误)**:
```
[INFO] Mode error: {
  "error_type": "InvalidModeError",
  "mode": "invalid_mode",
  "message": "Invalid CLI mode 'invalid_mode'. Valid modes: daily, weekly, ...",
  "valid_modes": ["daily", "weekly", "monthly", ...],
  "mode_type": "CLI"
}
```

**ERROR 级别 (系统错误)**:
```
[ERROR] Mode error: {
  "error_type": "ModeConversionError",
  "mode": "invalid_api_mode",
  "message": "Cannot convert mode 'invalid_api_mode' from API to Gallery-dl",
  "source_type": "API",
  "target_type": "Gallery-dl",
  "reason": "Invalid API mode"
}
[ERROR] Stack trace:
Traceback (most recent call last):
  File "src/gallery_dl_auto/integration/gallery_dl_wrapper.py", line 200, in _build_ranking_url
    gallery_dl_mode = ModeManager.api_to_gallery_dl(mode)
  ...
```

## 7. 错误监控和告警

### 7.1 关键指标

```python
# 未来扩展: 错误监控

class ModeErrorMetrics:
    """Mode 错误监控指标"""

    # 错误计数 (按错误类型)
    error_counts = {
        "InvalidModeError": 0,
        "ModeConversionError": 0,
        "UnsupportedModeError": 0,
    }

    # 错误率 (错误次数 / 总请求数)
    total_requests = 0
    error_rate = 0.0

    # 最常见的无效 mode
    invalid_mode_frequency: dict[str, int] = {}

    @classmethod
    def record_error(cls, error: ModeError):
        """记录错误"""
        error_type = type(error).__name__
        cls.error_counts[error_type] = cls.error_counts.get(error_type, 0) + 1

        if isinstance(error, InvalidModeError):
            mode = error.mode
            cls.invalid_mode_frequency[mode] = \
                cls.invalid_mode_frequency.get(mode, 0) + 1

        cls.total_requests += 1
        cls.error_rate = sum(cls.error_counts.values()) / cls.total_requests

    @classmethod
    def get_report(cls) -> dict:
        """生成错误报告"""
        return {
            "error_counts": cls.error_counts,
            "total_requests": cls.total_requests,
            "error_rate": cls.error_rate,
            "top_invalid_modes": sorted(
                cls.invalid_mode_frequency.items(),
                key=lambda x: x[1],
                reverse=True
            )[:10]
        }
```

### 7.2 告警规则

| 条件 | 严重程度 | 告警方式 |
|-----|---------|---------|
| ModeConversionError > 5 次/小时 | CRITICAL | 立即通知开发者 |
| InvalidModeError > 50 次/小时 | WARNING | 记录日志,可能需要改进文档 |
| 某个 mode 错误率 > 10% | WARNING | 检查该 mode 是否有问题 |

## 8. 测试错误处理

### 8.1 单元测试

```python
# tests/core/test_mode_errors.py

import pytest
from gallery_dl_auto.core.mode_errors import (
    InvalidModeError,
    ModeConversionError,
    UnsupportedModeError
)

def test_invalid_mode_error_message():
    """测试 InvalidModeError 的错误消息"""
    error = InvalidModeError(
        mode="invalid",
        valid_modes=["daily", "weekly"],
        mode_type="CLI"
    )

    assert "invalid" in str(error)
    assert "daily" in str(error)
    assert "weekly" in str(error)

def test_invalid_mode_error_user_friendly():
    """测试用户友好的错误消息"""
    error = InvalidModeError(
        mode="invalid",
        valid_modes=["daily", "weekly", "day_r18"],
        mode_type="CLI"
    )

    message = error.to_user_friendly_message()

    assert "错误:" in message
    assert "invalid" in message
    assert "daily" in message
    assert "示例:" in message

def test_mode_conversion_error_response():
    """测试 ModeConversionError 的错误响应"""
    error = ModeConversionError(
        source_mode="invalid_api",
        source_type="API",
        target_type="Gallery-dl",
        reason="Invalid API mode"
    )

    response = error.to_error_response()

    assert response["error_code"] == "MODE_CONVERSION_ERROR"
    assert response["severity"] == "error"
    assert "source_mode" in response["details"]

def test_unsupported_mode_error():
    """测试 UnsupportedModeError"""
    error = UnsupportedModeError(
        mode="month",
        context="gallery-dl",
        supported_modes=["daily", "weekly"]
    )

    message = error.to_user_friendly_message()

    assert "month" in message
    assert "gallery-dl" in message
    assert "daily" in message
```

### 8.2 集成测试

```python
# tests/cli/test_mode_error_handling.py

from click.testing import CliRunner
from gallery_dl_auto.cli.download_cmd import download

def test_cli_invalid_mode_error():
    """测试 CLI 层的无效 mode 错误处理"""
    runner = CliRunner()

    result = runner.invoke(download, [
        "--type", "invalid_mode",
        "--date", "2026-03-01"
    ])

    # 验证退出码
    assert result.exit_code == 2  # Click BadParameter

    # 验证错误消息
    assert "错误:" in result.output
    assert "invalid_mode" in result.output
    assert "daily" in result.output
    assert "示例:" in result.output

def test_api_mode_conversion_error():
    """测试 API mode 转换错误的处理"""
    # 模拟代码 bug 导致传入无效 API mode
    # (这需要 mock 内部调用)
    pass
```

## 9. 文档和用户指引

### 9.1 错误码文档

```markdown
# 错误码参考

## MODE_INVALID (用户错误)

**描述**: 无效的排行榜类型

**触发条件**: 用户输入了不存在的 mode

**解决方法**:
1. 检查 mode 拼写是否正确
2. 使用 --help 查看所有有效的 mode
3. 参考文档中的 mode 列表

**示例**:
```
错误命令: pixiv-downloader download --type invalid
正确命令: pixiv-downloader download --type daily
```

## MODE_CONVERSION_ERROR (系统错误)

**描述**: Mode 转换失败

**触发条件**: 内部代码 bug

**解决方法**: 联系开发者并提供错误日志
```

### 9.2 常见问题 FAQ

```markdown
## 常见问题

### Q: 提示 "Invalid ranking type" 怎么办?

A: 这表示你输入的排行榜类型不存在。请使用以下命令查看所有有效的类型:
```bash
pixiv-downloader download --help
```

常用的排行榜类型:
- `daily`: 每日排行榜
- `weekly`: 每周排行榜
- `day_male`: 男性喜爱排行榜

### Q: 为什么有些 mode 在某些引擎下不可用?

A: 不同的下载引擎支持的 mode 可能不同。
- `internal` 引擎: 支持所有 Pixiv API mode
- `gallery-dl` 引擎: 支持大多数常用 mode

如果遇到不支持的情况,可以尝试切换引擎:
```bash
pixiv-downloader download --type monthly --engine internal
```
```

---

**版本历史**:
- 2026-03-01: v1.0 初始设计
