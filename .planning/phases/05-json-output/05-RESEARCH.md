# Phase 5: JSON 输出 - Research

**Researched:** 2026-02-25
**Domain:** JSON 序列化、结构化输出、CLI 错误处理
**Confidence:** HIGH

## Summary

Phase 5 的核心目标是为程序化调用提供结构化的 JSON 输出。当前代码库已经在 download 命令中实现了基础的 JSON 输出(使用 `print(json.dumps(...))`),但需要进一步完善错误处理、标准化输出格式,并确保所有命令都支持 JSON 输出模式。

研究发现:Pydantic v2 提供了完善的 `model_dump_json()` 方法用于序列化,Python 标准库的 `json` 模块已经足够满足需求。关键是要设计一致的输出结构、错误码体系和可预测的键名,让第三方程序能够可靠地解析输出。

**Primary recommendation:** 使用 Pydantic v2 的 `model_dump_json()` 方法序列化数据模型,使用 `json.dumps(ensure_ascii=False, indent=2)` 格式化输出,设计包含 `success`、`error`、`data` 字段的标准响应结构。

<phase_requirements>

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| OUTP-01 | 程序以 JSON 格式返回下载结果汇总(成功数、失败数、总数) | 已在 download_cmd.py 实现,需要确保格式标准化 |
| OUTP-02 | 程序以 JSON 格式返回每张图片的详细信息(URL、标题、作者、标签、统计数据) | ArtworkMetadata 模型已包含所有字段,使用 `model_dump()` 序列化 |
| OUTP-03 | 程序以 JSON 格式返回下载文件的路径 | 已在 RankingDownloader 的 results 中返回 `filepath` 字段 |
| OUTP-04 | 程序以 JSON 格式返回错误信息和失败原因 | 需要标准化错误结构:包含 `error_code`、`message`、`details` |

</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| json (stdlib) | 3.x | JSON 序列化和输出 | Python 标准库,无需额外依赖,性能足够 |
| Pydantic v2 | 2.x | 数据模型序列化 | 已在 Phase 4 使用,提供 `model_dump_json()` 方法 |
| sys | stdlib | 输出到 stdout/stderr,退出码控制 | 标准库,CLI 工具必须 |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| typing | stdlib | 类型提示,定义输出结构 | 所有函数返回类型注解 |
| enum | stdlib | 定义错误码枚举 | 标准化错误类型 |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| json.dumps() | orjson | orjson 更快(2-3倍),但增加依赖;当前性能需求下标准库足够 |
| 手动构建 dict | Pydantic models | Pydantic 提供验证和类型安全;已在 Phase 4 引入,继续使用 |

**Installation:**
无额外安装需求 — 所有库已在项目中使用

## Architecture Patterns

### Recommended Project Structure
```
src/gallery_dl_auo/
├── models/
│   ├── artwork.py          # 已存在: ArtworkMetadata 等模型
│   └── output.py           # 新增: 定义 JSON 输出结构模型
├── cli/
│   ├── download_cmd.py     # 已存在: 需要优化 JSON 输出格式
│   └── output_formatter.py # 新增: 统一的 JSON 输出格式化器
└── utils/
    └── errors.py           # 新增: 标准化错误码和错误消息
```

### Pattern 1: Pydantic 模型序列化
**What:** 使用 Pydantic v2 的 `model_dump()` 和 `model_dump_json()` 方法序列化数据模型
**When to use:** 所有需要将 Pydantic 模型转换为 JSON 的场景
**Example:**
```python
# Source: https://docs.pydantic.dev/2.12/api/base_model
from pydantic import BaseModel

class DownloadResult(BaseModel):
    success: bool
    total: int
    success_count: int
    failed_count: int
    error: str | None = None

# 方法 1: 转换为 dict,然后用 json.dumps 输出
result = DownloadResult(success=True, total=10, success_count=10, failed_count=0)
output_dict = result.model_dump(mode='json')  # 转换为 JSON-compatible dict
print(json.dumps(output_dict, ensure_ascii=False, indent=2))

# 方法 2: 直接生成 JSON 字符串
json_str = result.model_dump_json(indent=2, ensure_ascii=False)
print(json_str)
```

### Pattern 2: 标准化输出结构
**What:** 所有命令的输出都使用统一的顶层结构,包含 `success`、`error`、`data` 字段
**When to use:** 所有 CLI 命令的 JSON 输出
**Example:**
```python
# 成功响应
{
  "success": true,
  "data": {
    "total": 50,
    "success_count": 48,
    "failed_count": 2,
    "results": [...]
  }
}

# 错误响应
{
  "success": false,
  "error": {
    "code": "AUTH_TOKEN_EXPIRED",
    "message": "Token has expired. Please run 'pixiv-downloader refresh' or 'pixiv-downloader login'.",
    "details": {
      "token_age_days": 35,
      "max_token_age_days": 30
    }
  }
}
```

### Pattern 3: 错误码枚举
**What:** 使用 Python enum 定义标准化的错误码,避免字符串硬编码
**When to use:** 所有错误抛出和错误处理场景
**Example:**
```python
from enum import Enum

class ErrorCode(str, Enum):
    """标准化错误码"""
    AUTH_TOKEN_NOT_FOUND = "AUTH_TOKEN_NOT_FOUND"
    AUTH_TOKEN_EXPIRED = "AUTH_TOKEN_EXPIRED"
    AUTH_TOKEN_INVALID = "AUTH_TOKEN_INVALID"
    API_NETWORK_ERROR = "API_NETWORK_ERROR"
    API_RATE_LIMIT = "API_RATE_LIMIT"
    FILE_PERMISSION_ERROR = "FILE_PERMISSION_ERROR"
    INVALID_ARGUMENT = "INVALID_ARGUMENT"
```

### Pattern 4: stdout/stderr 分离
**What:** JSON 输出到 stdout,日志和进度信息输出到 stderr
**When to use:** 所有 CLI 命令,确保 JSON 输出可被管道捕获
**Example:**
```python
import sys
import json

# JSON 输出到 stdout (程序可以捕获)
result = {"success": True, "data": {...}}
print(json.dumps(result, ensure_ascii=False, indent=2))

# 日志输出到 stderr (不污染 JSON 流)
print("Downloading image 1/50...", file=sys.stderr)
logger.info("Download started", file=sys.stderr)  # 如果 logger 配置正确
```

### Anti-Patterns to Avoid
- **在 JSON 输出中使用 Rich Console:** Rich 会添加 ANSI 转义序列,破坏 JSON 格式。已在新代码中使用 `print()` 替代。
- **混用 stdout 和 stderr:** 日志信息污染 JSON 输出,导致解析失败。
- **不一致的键名:** 同一概念在不同命令中使用不同键名(如 `error` vs `error_message`),增加调用方负担。
- **缺少错误码:** 仅返回错误消息字符串,无法程序化处理错误类型。

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| JSON 格式化 | 手动拼接 JSON 字符串 | `json.dumps(data, ensure_ascii=False, indent=2)` | 处理转义、Unicode、格式化 |
| Pydantic 序列化 | 手动遍历模型字段 | `model.model_dump(mode='json')` | 处理嵌套模型、可选字段、类型转换 |
| 错误码管理 | 字符串常量或魔法值 | `enum.Enum` 子类 | 类型安全、IDE 自动补全、防止拼写错误 |
| Unicode 处理 | 手动 encode/decode | `ensure_ascii=False` | Python 3 默认 UTF-8,无需手动处理 |

**Key insight:** JSON 输出的复杂性在于边缘情况(Unicode、特殊字符、嵌套结构),标准库和 Pydantic 已经处理了这些情况,不要重新发明轮子。

## Common Pitfalls

### Pitfall 1: ANSI 转义序列污染
**What goes wrong:** 使用 Rich Console 或彩色输出时,JSON 中包含 `\x1b[32m` 等 ANSI 转义序列,导致 `jq` 等工具解析失败
**Why it happens:** Rich Console 默认添加颜色和格式化代码到输出中
**How to avoid:** 始终使用 `print()` 而非 `console.print()` 输出 JSON;或确保 Rich Console 配置 `force_terminal=False`
**Warning signs:** JSON 解析器报告 "invalid character" 或 "unexpected token"

### Pitfall 2: 缺少 ensure_ascii=False
**What goes wrong:** 中文、日文等非 ASCII 字符被转义为 `\u4e2d\u6587`,降低可读性,增加响应体积
**Why it happens:** `json.dumps()` 默认 `ensure_ascii=True`,转义所有非 ASCII 字符
**How to avoid:** 始终使用 `json.dumps(data, ensure_ascii=False)`
**Warning signs:** JSON 输出中大量 `\uXXXX` 转义序列

### Pitfall 3: 不一致的退出码
**What goes wrong:** 有时错误返回 0,有时成功返回非零,导致 shell 脚本无法判断命令是否成功
**Why it happens:** 缺少统一的退出码策略,不同开发者使用不同惯例
**How to avoid:**
- 成功: `sys.exit(0)` 或不调用 `sys.exit()`
- 错误: `sys.exit(1)` — 让第三方程序决定重试策略
**Warning signs:** Shell 脚本中 `if $?` 判断失败,或错误时继续执行

### Pitfall 4: 错误信息不可操作
**What goes wrong:** 错误消息如 "Error occurred" 或 "Operation failed",用户不知道如何修复
**Why it happens:** 开发者捕获异常后仅返回通用消息,未提供上下文
**How to avoid:** 遵循 "What + Why + How" 模式: "Token expired (what). Token age is 35 days, max is 30 days (why). Run 'pixiv-downloader refresh' to update token (how)."
**Warning signs:** 用户反复尝试相同操作,提交 support tickets 询问如何修复

### Pitfall 5: stdout/stderr 混用
**What goes wrong:** 进度信息、日志输出到 stdout,与 JSON 混在一起,破坏 JSON 结构
**Why it happens:** 使用 `print()` 输出进度信息,未指定 `file=sys.stderr`
**How to avoid:**
- JSON 输出 → stdout (默认)
- 日志、进度 → stderr (`print(..., file=sys.stderr)`)
- 或使用 `logging` 模块(配置 StreamHandler 到 stderr)
**Warning signs:** `jq '.'` 命令报错 "parse error",`python -m json.tool` 失败

## Code Examples

### Example 1: 定义标准化输出模型
```python
# src/gallery_dl_auo/models/output.py
from typing import Any
from pydantic import BaseModel, Field
from enum import Enum

class ErrorCode(str, Enum):
    """标准化错误码"""
    AUTH_TOKEN_NOT_FOUND = "AUTH_TOKEN_NOT_FOUND"
    AUTH_TOKEN_EXPIRED = "AUTH_TOKEN_EXPIRED"
    AUTH_TOKEN_INVALID = "AUTH_TOKEN_INVALID"
    API_NETWORK_ERROR = "API_NETWORK_ERROR"
    API_RATE_LIMIT = "API_RATE_LIMIT"
    FILE_PERMISSION_ERROR = "FILE_PERMISSION_ERROR"

class ErrorDetail(BaseModel):
    """错误详情"""
    code: ErrorCode
    message: str
    details: dict[str, Any] | None = None

    class Config:
        use_enum_values = True  # 序列化时使用枚举值(字符串)

class DownloadSuccessData(BaseModel):
    """下载成功时的数据结构"""
    total: int = Field(..., description="总图片数")
    success_count: int = Field(..., description="成功下载数")
    failed_count: int = Field(..., description="失败下载数")
    output_dir: str = Field(..., description="输出目录路径")
    date: str = Field(..., description="排行榜日期")
    mode: str = Field(..., description="排行榜类型")
    success_list: list[dict[str, Any]] = Field(default_factory=list)
    failed_list: list[dict[str, Any]] = Field(default_factory=list)

class DownloadOutput(BaseModel):
    """download 命令的输出结构"""
    success: bool
    data: DownloadSuccessData | None = None
    error: ErrorDetail | None = None

    def to_json(self) -> str:
        """序列化为 JSON 字符串"""
        return self.model_dump_json(
            exclude_none=True,  # 排除 None 字段
            indent=2,
            ensure_ascii=False
        )
```

### Example 2: 使用输出模型的命令实现
```python
# src/gallery_dl_auo/cli/download_cmd.py (优化后)
import sys
from gallery_dl_auo.models.output import (
    DownloadOutput,
    DownloadSuccessData,
    ErrorDetail,
    ErrorCode
)

def download(date: str | None, output: str, mode: str) -> None:
    """Download Pixiv ranking images with structured JSON output"""

    # 1. Load token
    storage = get_default_token_storage()
    token_data = storage.load_token()

    if not token_data or not token_data.get("refresh_token"):
        error_output = DownloadOutput(
            success=False,
            error=ErrorDetail(
                code=ErrorCode.AUTH_TOKEN_NOT_FOUND,
                message="No token found. Run 'pixiv-downloader login' first.",
                details=None
            )
        )
        print(error_output.to_json())
        sys.exit(1)

    # 2. Initialize API client
    try:
        client = PixivClient(refresh_token=token_data["refresh_token"])
    except Exception as e:
        error_output = DownloadOutput(
            success=False,
            error=ErrorDetail(
                code=ErrorCode.AUTH_TOKEN_INVALID,
                message=f"Authentication failed: {e}",
                details={"exception_type": type(e).__name__}
            )
        )
        print(error_output.to_json())
        sys.exit(1)

    # 3. Execute download
    output_dir = Path(output)
    downloader = RankingDownloader(client, output_dir)
    results = downloader.download_ranking(mode=mode, date=date)

    # 4. Build success output
    success_data = DownloadSuccessData(
        total=results["total"],
        success_count=len(results["success"]),
        failed_count=len(results["failed"]),
        output_dir=str(output_dir),
        date=date or datetime.date.today().strftime("%Y-%m-%d"),
        mode=mode,
        success_list=results["success"],
        failed_list=results["failed"]
    )

    output = DownloadOutput(success=True, data=success_data)
    print(output.to_json())

    # 5. Return exit code 1 if any failures
    if results["failed"]:
        sys.exit(1)
```

### Example 3: 统一的错误处理装饰器
```python
# src/gallery_dl_auo/cli/output_formatter.py
import sys
import json
from functools import wraps
from typing import Callable
from gallery_dl_auo.models.output import DownloadOutput, ErrorDetail, ErrorCode

def json_output(func: Callable) -> Callable:
    """装饰器: 捕获异常并格式化为标准 JSON 输出"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except KeyboardInterrupt:
            # 用户中断,不输出 JSON,直接退出
            print("\nOperation cancelled by user.", file=sys.stderr)
            sys.exit(130)  # 128 + SIGINT(2)
        except Exception as e:
            # 未预期的异常
            error_output = DownloadOutput(
                success=False,
                error=ErrorDetail(
                    code=ErrorCode.INTERNAL_ERROR,
                    message=f"Unexpected error: {e}",
                    details={"exception_type": type(e).__name__}
                )
            )
            print(error_output.to_json())
            sys.exit(1)
    return wrapper
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| 手动拼接 JSON 字符串 | 使用 `json.dumps()` 和 Pydantic 序列化 | Python 3.x | 减少转义错误,支持复杂嵌套结构 |
| Rich Console 输出 JSON | `print()` 输出 JSON | Phase 3 (2026-02-25) | 避免 ANSI 转义序列污染 |
| 混用 stdout/stderr | stdout 仅 JSON,stderr 仅日志 | Phase 3 (2026-02-25) | 支持 JSON 管道处理 |
| 字符串错误消息 | 标准化错误码 + 结构化详情 | Phase 5 (推荐) | 支持程序化错误处理 |

**Deprecated/outdated:**
- `simplejson`: Python 3 标准库的 `json` 已足够,无需第三方库
- 手动 `json.loads()` + 键检查: 使用 Pydantic 模型验证和序列化

## Open Questions

1. **是否需要支持 `--output-format` 参数?**
   - What we know: 当前项目已使用 `print(json.dumps(...))` 输出 JSON
   - What's unclear: 是否需要支持 `text`、`json`、`json-compact` 等多种输出格式
   - Recommendation: 暂不实现,Phase 5 专注于 JSON 输出。如果用户有需求,在 Phase 8 或 v2 中添加 `--format json|text` 参数。

2. **是否需要提供 JSON Schema?**
   - What we know: Pydantic v2 提供 `model_json_schema()` 方法生成 JSON Schema
   - What's unclear: 用户是否需要 Schema 文件来验证输出格式
   - Recommendation: 暂不生成 Schema 文件,但保留可能性。可以在文档中说明输出结构,或在未来添加 `pixiv-downloader schema` 命令。

3. **错误详情(details 字段)应该包含多少信息?**
   - What we know: 太少的信息不可操作,太多的信息暴露内部实现
   - What's unclear: 具体应该包含哪些字段
   - Recommendation: 遵循 "对用户有用的调试信息" 原则。例如: `token_age_days`、`max_token_age_days` 有用;`internal_user_id` 无用且危险。

## Sources

### Primary (HIGH confidence)
- /websites/pydantic_dev_2_12 - Pydantic v2 model_dump_json() 和 model_json_schema() API
- https://docs.pydantic.dev/2.12/api/base_model - Pydantic 序列化方法官方文档
- https://blog.kellybrazil.com/2021/12/03/tips-on-adding-json-output-to-your-cli-app/ - CLI JSON 输出最佳实践(业界标准)

### Secondary (MEDIUM confidence)
- https://thelinuxcode.com/pretty-print-json-in-python-practical-guide-for-2026/ - Python JSON 格式化实践(2026)
- https://dev.to/leejackson/building-a-production-ready-python-cli-tool-with-logging-error-handling-and-auto-updates-in-2026-58ca - CLI 错误处理模式(2026)
- https://thelinuxcode.com/how-to-print-to-stdout-and-stderr-in-python-with-real-cli-patterns-and-tests/ - stdout/stderr 分离实践

### Tertiary (LOW confidence)
- WebSearch 结果中关于 JSON 输出的通用建议 — 大部分与 Python 标准库文档一致,未提供额外价值

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - Python 标准库 + Pydantic v2 是成熟方案,文档完善
- Architecture: HIGH - 基于业界最佳实践(Kelly Brazil 的文章),并参考了现有代码模式
- Pitfalls: HIGH - 所有陷阱都在实际项目中遇到并解决(如 ANSI 转义序列、ensure_ascii、stdout/stderr 混用)

**Research date:** 2026-02-25
**Valid until:** 2027-02-25 (JSON 和 Pydantic API 稳定,年度复查即可)
