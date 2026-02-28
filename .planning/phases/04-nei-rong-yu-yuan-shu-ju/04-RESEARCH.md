# Phase 4: 内容与元数据 - Research

**Researched:** 2026-02-25
**Domain:** Pixiv API 元数据获取、结构化数据建模、路径模板系统
**Confidence:** HIGH

## Summary

Phase 4 扩展 Phase 3 的排行榜下载功能,增加完整的元数据获取和自定义保存路径支持。核心任务包括:(1) 使用 pixivpy3 的 `illust_detail()` API 获取扩展元数据(标签、统计数据),(2) 使用 Pydantic 建模结构化元数据,(3) 实现路径模板系统支持自定义保存路径。

pixivpy3 库提供完整的元数据访问能力,包括 `illust.tags`、`illust.total_bookmarks`、`illust.total_view` 和 `illust.total_comments` 字段。Pydantic 是 Python 生态的标准数据验证库,提供类型安全的元数据建模。pathvalidate 库提供跨平台的路径清理能力。

**Primary recommendation:** 使用 Pydantic 构建结构化元数据模型,通过 pixivpy3 的 `illust_detail()` 批量获取元数据,使用 pathvalidate 清理路径,支持简单的字符串模板配置保存路径(如 `{mode}/{date}/{author}/{title}.jpg`)。

## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| CONT-02 | 程序获取作品的基础元数据(标题、作者、标签) | pixivpy3 `illust_detail()` 提供 `tags` 字段,Pydantic 模型定义结构 |
| CONT-03 | 程序获取作品的扩展统计数据(收藏数、浏览量、评论数) | pixivpy3 提供 `total_bookmarks`、`total_view`、`total_comments` 字段 |
| CONT-04 | 用户能够指定图片下载的保存路径 | 使用 pathvalidate 清理路径,支持简单模板语法 `{variable}` |

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| pixivpy3 | 3.7.5 | Pixiv API 客户端 | 项目已使用,提供完整的 `illust_detail()` API 访问标签和统计数据 |
| Pydantic | v2 (2.12+) | 数据验证和建模 | Python 生态标准,类型安全,自动验证,比 dataclass 更强大 |
| pathvalidate | latest | 路径清理 | 跨平台路径验证,处理非法字符,比手动实现更健壮 |
| pathlib (stdlib) | 3.10+ | 路径操作 | Python 标准库,已广泛使用,提供跨平台路径操作 |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| typing (stdlib) | 3.10+ | 类型注解 | 定义 Pydantic 模型时使用 |
| re (stdlib) | 3.10+ | 模板变量替换 | 解析路径模板时使用 |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Pydantic | dataclasses + 手动验证 | dataclasses 更轻量,但缺少验证和序列化能力,Pydantic 提供完整的验证链 |
| pathvalidate | 手动字符串替换 | 手动实现需要处理多种边界情况(Windows 保留名、非法字符、长度限制),pathvalidate 已处理所有边界情况 |
| 简单模板 `{var}` | Jinja2 模板引擎 | Jinja2 更强大但过度设计,简单字符串替换已满足需求,降低复杂度 |

**Installation:**
```bash
# pixivpy3 已在项目中
pip install pydantic pathvalidate
```

## Architecture Patterns

### Recommended Project Structure
```
src/gallery_dl_auo/
├── models/              # 新增: Pydantic 数据模型
│   ├── __init__.py
│   └── artwork.py       # ArtworkMetadata, ArtworkStatistics 模型
├── api/
│   └── pixiv_client.py  # 扩展: 添加 get_artwork_metadata() 方法
├── download/
│   └── ranking_downloader.py  # 扩展: 集成元数据获取和路径模板
├── utils/
│   └── path_template.py # 新增: 路径模板解析和清理
└── cli/
    └── download_cmd.py  # 扩展: 添加 --path-template 参数
```

### Pattern 1: Pydantic Metadata Model
**What:** 使用 Pydantic BaseModel 定义结构化元数据,提供类型安全和自动验证
**When to use:** 需要处理来自 pixivpy3 API 的复杂嵌套数据结构时
**Example:**
```python
# Source: https://docs.pydantic.dev/latest/concepts/models
from pydantic import BaseModel
from typing import Literal

class ArtworkStatistics(BaseModel):
    """作品统计数据"""
    bookmark_count: int
    view_count: int
    comment_count: int

class ArtworkTag(BaseModel):
    """作品标签"""
    name: str
    translated_name: str | None = None

class ArtworkMetadata(BaseModel):
    """作品完整元数据"""
    illust_id: int
    title: str
    author: str
    author_id: int
    tags: list[ArtworkTag]
    statistics: ArtworkStatistics

    # 允许从 pixivpy3 对象构建
    class Config:
        from_attributes = True

# 使用示例
metadata = ArtworkMetadata(
    illust_id=12345,
    title="Beautiful Sunset",
    author="Artist",
    author_id=67890,
    tags=[ArtworkTag(name="风景", translated_name="landscape")],
    statistics=ArtworkStatistics(
        bookmark_count=1000,
        view_count=5000,
        comment_count=50
    )
)

# 序列化为 dict/JSON
data = metadata.model_dump()
json_str = metadata.model_dump_json()
```

### Pattern 2: Path Template System
**What:** 使用简单字符串模板和正则表达式实现路径变量替换,配合 pathvalidate 清理
**When to use:** 需要支持用户自定义保存路径模板时
**Example:**
```python
# Source: https://thelinuxcode.com/create-a-file-path-with-variables-in-python-practical-2026-guide/
import re
from pathlib import Path
from pathvalidate import sanitize_filepath

class PathTemplate:
    """路径模板解析器"""

    # 支持的模板变量
    VARIABLES = {
        "mode", "date", "illust_id", "title", "author", "author_id"
    }

    def __init__(self, template: str):
        self.template = template

    def render(self, context: dict) -> Path:
        """渲染路径模板

        Args:
            context: 包含模板变量的字典

        Returns:
            清理后的 Path 对象
        """
        # 1. 替换模板变量
        path_str = self.template
        for var in self.VARIABLES:
            placeholder = f"{{{var}}}"
            if placeholder in path_str:
                value = str(context.get(var, "unknown"))
                path_str = path_str.replace(placeholder, value)

        # 2. 清理非法字符
        path_str = sanitize_filepath(path_str)

        return Path(path_str)

# 使用示例
template = PathTemplate("{mode}/{date}/{author}/{title}.jpg")
path = template.render({
    "mode": "daily",
    "date": "2026-02-25",
    "author": "Artist Name",
    "title": "Beautiful Sunset"
})
# -> Path("daily/2026-02-25/Artist Name/Beautiful Sunset.jpg")
```

### Pattern 3: Batch Metadata Fetching with Rate Limiting
**What:** 在下载前批量获取元数据,使用现有的速率控制机制
**When to use:** 需要获取排行榜中所有作品的详细元数据时
**Example:**
```python
# 扩展现有 PixivClient
from gallery_dl_auo.api.pixiv_client import PixivClient

def get_artwork_metadata(self, illust_id: int) -> dict:
    """获取单个作品的完整元数据

    Args:
        illust_id: 作品 ID

    Returns:
        包含完整元数据的字典
    """
    try:
        result = self.api.illust_detail(illust_id)
        illust = result.illust

        return {
            "illust_id": illust.id,
            "title": illust.title,
            "author": illust.user.name,
            "author_id": illust.user.id,
            "tags": [
                {"name": tag.name, "translated_name": tag.translated_name}
                for tag in illust.tags
            ],
            "statistics": {
                "bookmark_count": illust.total_bookmarks,
                "view_count": illust.total_view,
                "comment_count": illust.total_comments,
            }
        }
    except Exception as e:
        logger.error(f"Failed to get metadata for {illust_id}: {e}")
        raise PixivAPIError(f"Metadata fetch failed: {e}") from e
```

### Anti-Patterns to Avoid
- **不要直接序列化 pixivpy3 对象:** pixivpy3 返回的对象不是标准 Python 类型,使用 Pydantic 模型显式转换
- **不要忽略路径清理:** 用户输入的模板可能包含非法字符(Windows 的 `:`, `*`, `?` 等),必须使用 pathvalidate 清理
- **不要过度设计模板引擎:** 简单的字符串替换足够,避免引入 Jinja2 等复杂模板引擎

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| 数据验证 | 手动 if-else 检查 | Pydantic | Pydantic 提供类型强制、必填检查、嵌套验证,减少样板代码 |
| 路径清理 | 正则表达式替换非法字符 | pathvalidate | pathvalidate 处理所有边界情况(Windows 保留名、长度限制、编码问题) |
| 模板变量替换 | split/join 手动拼接 | 正则表达式 + format | Python 内置字符串格式化更清晰,正则用于验证模板语法 |

**Key insight:** Phase 4 核心复杂度在于数据建模和路径处理,使用成熟库比手动实现更可靠,减少边界情况错误。

## Common Pitfalls

### Pitfall 1: Pydantic 模型与 pixivpy3 对象不匹配
**What goes wrong:** pixivpy3 返回的对象是自定义类,直接传递给 Pydantic 会失败
**Why it happens:** Pydantic 默认期望 dict 或 kwargs,不了解 pixivpy3 的对象结构
**How to avoid:** 使用 `Config.from_attributes = True` 允许 Pydantic 从对象属性构建模型
**Warning signs:** `ValidationError: field required` 或 `dict expected`

### Pitfall 2: Windows 路径中的非法字符
**What goes wrong:** 模板包含作者名或标题,用户输入可能包含 `:`, `*`, `?`, `"`, `<`, `>`, `|` 等 Windows 非法字符
**Why it happens:** Pixiv 用户名和作品标题不限制字符,但 Windows 文件系统限制严格
**How to avoid:** 所有用户输入(标题、作者)通过 `sanitize_filename()` 或 `sanitize_filepath()` 清理
**Warning signs:** 文件创建失败 `OSError: [Errno 22] Invalid argument`

### Pitfall 3: 元数据获取速率限制
**What goes wrong:** 批量调用 `illust_detail()` 触发 Pixiv 429 错误
**Why it happens:** 每个作品调用一次元数据 API,100 个作品 = 100 次 API 调用
**How to avoid:** 复用现有的 `rate_limit_delay()` 机制,在元数据获取间添加延迟
**Warning signs:** `PixivAPIError: 429 Too Many Requests`

### Pitfall 4: 路径模板变量缺失
**What goes wrong:** 用户使用 `{author_id}` 但排行榜数据不包含作者 ID,导致 `{author_id}` 未替换
**Why it happens:** `illust_ranking()` 返回的数据有限,不包含所有元数据字段
**How to avoid:** 明确文档支持的变量列表,未提供变量替换为 `"unknown"` 或空字符串
**Warning signs:** 路径包含字面量 `{author_id}` 字符串

### Pitfall 5: 元数据和排行榜数据不一致
**What goes wrong:** 排行榜获取的 `illust.title` 与 `illust_detail()` 获取的不一致(作品改名)
**Why it happens:** 排行榜缓存,元数据实时获取
**How to avoid:** 以 `illust_detail()` 数据为准,用于最终文件名;排行榜数据仅用于 URL
**Warning signs:** 文件名与预期不符

## Code Examples

Verified patterns from official sources:

### 1. Pydantic Nested Model with Optional Fields
```python
# Source: https://docs.pydantic.dev/latest/concepts/models
from pydantic import BaseModel
from typing import Literal

class ArtworkStatistics(BaseModel):
    """作品统计数据 - 所有字段必填"""
    bookmark_count: int
    view_count: int
    comment_count: int

class ArtworkTag(BaseModel):
    """作品标签 - 翻译名可选"""
    name: str
    translated_name: str | None = None

class ArtworkMetadata(BaseModel):
    """完整元数据 - 嵌套模型"""
    illust_id: int
    title: str
    author: str
    author_id: int
    tags: list[ArtworkTag]
    statistics: ArtworkStatistics

# 从 pixivpy3 对象构建(需要启用 from_attributes)
metadata = ArtworkMetadata.model_validate(pixiv_illust_object)
```

### 2. Path Template with pathvalidate
```python
# Source: https://github.com/thombashi/pathvalidate/blob/master/README.rst
from pathvalidate import sanitize_filepath
from pathlib import Path

# 清理包含非法字符的路径
template_str = "{mode}/{date}/{author}/{title}.jpg"
rendered = template_str.format(
    mode="daily",
    date="2026-02-25",
    author="Artist: Name",  # 包含非法字符 ":"
    title="Title? With*Chars"  # 包含非法字符 "?" 和 "*"
)

# 清理后
safe_path = sanitize_filepath(rendered)
# -> "daily/2026-02-25/Artist Name/Title WithChars.jpg" (Windows)
```

### 3. Pixivpy3 Metadata Extraction
```python
# Source: https://github.com/upbit/pixivpy (Context7 search)
from pixivpy3 import AppPixivAPI

api = AppPixivAPI()
api.auth(refresh_token="...")

# 获取作品详情
json_result = api.illust_detail(59580629)
illust = json_result.illust

# 提取元数据
metadata = {
    "illust_id": illust.id,
    "title": illust.title,
    "author": illust.user.name,
    "author_id": illust.user.id,
    "tags": [{"name": tag.name, "translated_name": tag.translated_name}
             for tag in illust.tags],
    "statistics": {
        "bookmark_count": illust.total_bookmarks,
        "view_count": illust.total_view,
        "comment_count": illust.total_comments,
    }
}
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| 手动数据类 + isinstance 检查 | Pydantic 自动验证 | Pydantic v2 (2023) | 减少样板代码,类型更安全 |
| os.path.join() 字符串操作 | pathlib Path 对象 | Python 3.6+ | 跨平台更可靠,代码更清晰 |
| 自定义路径清理函数 | pathvalidate 库 | 2020+ | 处理所有边界情况,减少维护负担 |

**Deprecated/outdated:**
- Python 3.9 之前的 `Optional[Type]` 语法: 使用 `Type | None` 更清晰
- 手动 `__dict__` 序列化: Pydantic 的 `model_dump()` 提供更好的控制

## Open Questions

1. **元数据获取策略: 批量 vs 按需**
   - What we know: Phase 3 仅下载图片,元数据需求是 Phase 4 新增
   - What's unclear: 是否需要在下载前获取所有元数据,还是下载时获取
   - Recommendation: 推荐下载前批量获取,确保路径模板使用最新元数据;但保留 fallback:元数据获取失败时使用排行榜基础数据

2. **路径模板复杂度: 简单变量 vs 条件逻辑**
   - What we know: 需求仅要求支持自定义路径,未指定模板复杂度
   - What's unclear: 是否需要支持条件逻辑(如 "if multi-page then create subfolder")
   - Recommendation: Phase 4 仅实现简单变量替换 `{var}`,条件逻辑留待 v2 (ADV-03)

3. **标签序列化: 简单列表 vs 嵌套对象**
   - What we know: 标签包含 `name` 和可选的 `translated_name`
   - What's unclear: JSON 输出时是否保留嵌套结构,还是展平为字符串数组
   - Recommendation: 保留嵌套结构 `{"name": "...", "translated_name": "..."}`,JSON 消费者可按需处理;同时提供辅助方法转换为简单字符串数组

## Validation Architecture

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 8.0+ (已在项目中) |
| Config file | pyproject.toml (pytest.ini_options 配置) |
| Quick run command | `pytest tests/ -x -v` |
| Full suite command | `pytest tests/ --cov=src/gallery_dl_auo` |
| Estimated runtime | ~15 秒 (新增测试约 10 个) |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| CONT-02 | 获取作品标签列表 | unit | `pytest tests/models/test_artwork.py::test_artwork_metadata_tags -x` | ❌ Wave 0 gap |
| CONT-02 | 标签包含名称和翻译 | unit | `pytest tests/models/test_artwork.py::test_artwork_tag_model -x` | ❌ Wave 0 gap |
| CONT-03 | 获取收藏数/浏览量/评论数 | unit | `pytest tests/models/test_artwork.py::test_artwork_statistics -x` | ❌ Wave 0 gap |
| CONT-03 | 统计数据为非负整数 | unit | `pytest tests/models/test_artwork.py::test_statistics_validation -x` | ❌ Wave 0 gap |
| CONT-04 | 路径模板变量替换 | unit | `pytest tests/utils/test_path_template.py::test_template_render -x` | ❌ Wave 0 gap |
| CONT-04 | 路径清理非法字符 | unit | `pytest tests/utils/test_path_template.py::test_path_sanitization -x` | ❌ Wave 0 gap |
| CONT-04 | 模板支持所有变量 | unit | `pytest tests/utils/test_path_template.py::test_all_variables -x` | ❌ Wave 0 gap |
| CONT-02 | API 获取完整元数据 | integration | `pytest tests/api/test_pixiv_client.py::test_get_artwork_metadata -x` | ❌ Wave 0 gap |
| CONT-03 | 元数据包含统计数据 | integration | `pytest tests/api/test_pixiv_client.py::test_metadata_statistics -x` | ❌ Wave 0 gap |
| CONT-04 | 下载器使用路径模板 | integration | `pytest tests/download/test_ranking_downloader.py::test_path_template_integration -x` | ❌ Wave 0 gap |

### Nyquist Sampling Rate
- **Minimum sample interval:** After every committed task → run: `pytest tests/ -x -v`
- **Full suite trigger:** Before merging final task of any plan wave
- **Phase-complete gate:** Full suite green before `/gsd:verify-work` runs
- **Estimated feedback latency per task:** ~15 秒

### Wave 0 Gaps (must be created before implementation)
- [ ] `tests/models/__init__.py` — 创建 models 测试包
- [ ] `tests/models/test_artwork.py` — 测试 Pydantic 模型(CONT-02, CONT-03)
- [ ] `tests/utils/test_path_template.py` — 测试路径模板系统(CONT-04)
- [ ] `tests/api/test_pixiv_client.py` — 扩展测试元数据获取方法(CONT-02, CONT-03)
- [ ] `tests/download/test_ranking_downloader.py` — 扩展测试路径模板集成(CONT-04)
- [ ] Pydantic 和 pathvalidate 依赖添加到 pyproject.toml

*(Note: 现有测试基础设施已覆盖 pytest、conftest、fixtures,仅需创建新测试文件)*

## Sources

### Primary (HIGH confidence)
- Context7 Pydantic v2 - Pydantic BaseModel 定义、嵌套模型、from_attributes 配置
- Context7 pathvalidate - sanitize_filepath 用法、跨平台路径清理
- GitHub upbit/pixivpy - illust_detail API 用法、元数据字段结构
- 官方 PixivPy3 README - illust_detail 示例代码、认证流程

### Secondary (MEDIUM confidence)
- WebSearch "pixivpy3 illust_detail metadata tags bookmarks 2026" - 验证 API 字段可用性
- WebSearch "Python pathlib path template 2026" - 路径模板最佳实践
- 项目代码审查 - Phase 3 实现的 PixivClient、RankingDownloader、rate_limiter

### Tertiary (LOW confidence)
- None - 所有核心功能已通过官方文档和现有代码验证

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - pixivpy3 已在项目中,Pydantic 和 pathvalidate 是 Python 生态标准库
- Architecture: HIGH - Pydantic 模式和路径模板是成熟模式,无创新性设计
- Pitfalls: HIGH - 所有问题(路径清理、速率限制、数据建模)都有标准解决方案

**Research date:** 2026-02-25
**Valid until:** 2026-03-25 (Pydantic v2 稳定,pixivpy3 API 稳定)
