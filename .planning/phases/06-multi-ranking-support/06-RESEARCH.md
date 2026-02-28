# Phase 6: 多排行榜支持 - Research

**Researched:** 2026-02-25
**Domain:** Pixiv API 排行榜扩展、大规模数据集处理、断点续传
**Confidence:** HIGH

## Summary

Phase 6 需要扩展现有的排行榜下载功能,从仅支持日榜(daily)扩展到支持全部 13 种排行榜类型(包括周榜、月榜、R18 榜单等),并处理月榜大规模数据集(1500+ 张作品)的完整下载,同时实现断点续传功能。

**Primary recommendation:** 使用 pixivpy3 的 `illust_ranking()` API 支持所有排行榜类型,通过 `next_url` 自动跟随机制处理大规模数据集,使用 JSON 进度文件实现断点续传,配置参数通过 Hydra 配置系统管理。

<user_constraints>
## User Constraints (from CONTEXT.md)

### 排行榜类型选择方式
- 使用单命令 + `--type` 参数方式,格式:`pixiv-download download --type weekly --date 2026-02-18`
- `--type` 参数值使用完整单词(非缩写)
- 不支持同时下载多种类型,每次运行仅下载单一排行榜
- 无默认值,必须显式指定 `--type` 参数
- 用户输入无效类型时立即报错并退出,格式:`Invalid ranking type 'xyz'. Valid types: daily, weekly, monthly, ...`
- 支持全部 13 种排行榜类型:
  - 常规: `daily`, `weekly`, `monthly`
  - 分类: `day_male`, `day_female`, `week_original`, `week_rookie`, `day_manga`
  - R18: `day_r18`, `day_male_r18`, `day_female_r18`, `week_r18`, `week_r18g`

### 大规模数据集处理策略
- 用户可通过配置文件自定义下载参数:
  - `batch_size`: 每批次下载的作品数量(默认 30)
  - `batch_delay`: 批次间隔秒数(默认 2.0)
  - `concurrency`: 并发下载数(默认 1)
  - `image_delay`: 单张图片间隔秒数(默认 2.5)
- 进度显示: 静默模式,仅在完成时显示总结
- 自动跟随 `next_url` 持续下载,直到无更多数据,确保月榜完整下载

### 时间范围指定
- 支持历史排行榜下载,使用 `--date` 参数
- 日期格式: `YYYY-MM-DD`(仅支持此格式)
- 用户输入无效日期时立即报错并退出,格式:`Invalid date '2026-13-45'. Format: YYYY-MM-DD`
- 拒绝未来日期,立即报错,格式:`Date '2026-03-01' is in the future`

### 错误恢复行为
- 支持断点续传,记录已下载作品 ID
- 进度记录方式: 在下载目录内创建 `.progress.json` 文件
  - 示例: `./pixiv-downloads/weekly-2026-02-18/.progress.json`
  - 使用路径模板时也遵循此规则
- 单张图片下载失败时重试 3 次,间隔 5 秒
- 检测到未完成下载时自动继续,不询问用户
- 下载完成后自动删除 `.progress.json` 文件

### Claude's Discretion
- `.progress.json` 文件的具体格式和数据结构
- 批次间隔和图片间隔的默认值优化
- 重试间隔的具体实现
- 错误信息的详细程度

### Deferred Ideas (OUT OF SCOPE)
None — discussion stayed within phase scope
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|------------------|
| RANK-02 | 用户能够下载 pixiv 每周排行榜 | pixivpy3 `illust_ranking(mode='week')` API 支持 |
| RANK-03 | 用户能够下载 pixiv 每月排行榜 | pixivpy3 `illust_ranking(mode='month')` + `next_url` 自动跟随机制 |

</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| pixivpy3 | 3.7.5 | Pixiv API 客户端 | 官方 Python API 库,支持所有排行榜类型和分页机制 |
| click | 8.1.0+ | CLI 参数解析 | 项目已使用,支持 `--type` 参数扩展 |
| hydra-core | 1.3.0+ | 配置管理 | 项目已使用,支持配置文件管理下载参数 |
| Pydantic | 2.12.0+ | 数据验证 | 项目已使用,用于配置模型和进度文件结构 |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| json | stdlib | 进度文件序列化 | 断点续传状态保存 |
| datetime | stdlib | 日期验证和处理 | 历史排行榜和日期校验 |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| pixivpy3 | 直接 HTTP API 调用 | pixivpy3 已封装认证、分页、错误处理,无需重复造轮子 |
| JSON 进度文件 | SQLite 数据库 | JSON 更轻量,易于调试,适合单次下载场景 |

**Installation:**
无需安装新依赖,所有库已在项目中。

## Architecture Patterns

### Recommended Project Structure
```
src/gallery_dl_auo/
├── cli/
│   ├── download_cmd.py      # 添加 --type 参数验证
│   └── validators.py         # 新增:类型和日期验证函数
├── download/
│   ├── ranking_downloader.py  # 扩展:支持多类型和断点续传
│   ├── progress_manager.py    # 新增:进度文件管理
│   └── retry_handler.py       # 新增:重试逻辑
├── config/
│   └── download_config.py     # 新增:下载配置模型
└── api/
    └── pixiv_client.py        # 已支持 mode 参数
```

### Pattern 1: 排行榜类型映射
**What:** 将用户友好的类型名称映射到 pixivpy3 API 的 mode 参数
**When to use:** CLI 参数验证和 API 调用
**Example:**
```python
# Source: pixivpy3 文档 + CONTEXT.md 用户决策
RANKING_TYPES = {
    # 常规
    "daily": "day",
    "weekly": "week",
    "monthly": "month",
    # 分类
    "day_male": "day_male",
    "day_female": "day_female",
    "week_original": "week_original",
    "week_rookie": "week_rookie",
    "day_manga": "day_manga",
    # R18
    "day_r18": "day_r18",
    "day_male_r18": "day_male_r18",
    "day_female_r18": "day_female_r18",
    "week_r18": "week_r18",
    "week_r18g": "week_r18g",
}

def validate_ranking_type(type_str: str) -> str:
    """验证并返回 API mode 参数"""
    if type_str not in RANKING_TYPES:
        valid_types = ", ".join(RANKING_TYPES.keys())
        raise ValueError(
            f"Invalid ranking type '{type_str}'. Valid types: {valid_types}"
        )
    return RANKING_TYPES[type_str]
```

### Pattern 2: next_url 自动跟随
**What:** 自动处理 pixiv API 的分页,直到无更多数据
**When to use:** 月榜等大规模数据集下载
**Example:**
```python
# Source: pixivpy3 文档 + 现有 get_ranking() 实现
def get_ranking_with_pagination(
    self, mode: str, date: str | None = None
) -> list[dict]:
    """获取排行榜所有数据(自动跟随 next_url)"""
    all_works = []

    # 首次请求
    params = {"mode": mode}
    if date:
        params["date"] = date

    json_result = self.api.illust_ranking(**params)

    # 累积作品
    if hasattr(json_result, "illusts"):
        all_works.extend(extract_works(json_result.illusts))

    # 自动跟随 next_url
    next_url = getattr(json_result, "next_url", None)
    while next_url:
        next_qs = self.api.parse_qs(next_url)
        json_result = self.api.illust_ranking(**next_qs)

        if not hasattr(json_result, "illusts"):
            break

        all_works.extend(extract_works(json_result.illusts))
        next_url = getattr(json_result, "next_url", None)

    return all_works
```

### Pattern 3: 断点续传进度文件
**What:** 使用 JSON 文件记录已下载作品 ID,支持中断后继续
**When to use:** 所有排行榜下载,特别是月榜大规模数据集
**Example:**
```python
# Source: Python 下载最佳实践 + CONTEXT.md 用户决策
from pydantic import BaseModel
from typing import Set
import json
from pathlib import Path

class DownloadProgress(BaseModel):
    """下载进度模型"""
    mode: str
    date: str
    downloaded_ids: Set[int]  # 使用集合去重
    failed_ids: Set[int]

    def save(self, progress_file: Path) -> None:
        """保存进度到文件"""
        with open(progress_file, 'w', encoding='utf-8') as f:
            json.dump(self.model_dump(), f, ensure_ascii=False, indent=2)

    @classmethod
    def load(cls, progress_file: Path) -> 'DownloadProgress | None':
        """从文件加载进度"""
        if not progress_file.exists():
            return None
        with open(progress_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            # 转换 list 为 set
            data['downloaded_ids'] = set(data.get('downloaded_ids', []))
            data['failed_ids'] = set(data.get('failed_ids', []))
            return cls(**data)

# 使用示例
progress_file = output_dir / ".progress.json"
progress = DownloadProgress.load(progress_file)

# 跳过已下载的作品
for illust in ranking_data:
    if illust['id'] in progress.downloaded_ids:
        logger.info(f"Skipping already downloaded: {illust['id']}")
        continue

    # 下载作品...
    progress.downloaded_ids.add(illust['id'])
    progress.save(progress_file)  # 每次下载后保存
```

### Pattern 4: 重试机制
**What:** 单张图片下载失败时自动重试
**When to use:** 文件下载操作
**Example:**
```python
# Source: Python 重试最佳实践
import time
from typing import Callable

def retry_on_failure(
    func: Callable,
    max_retries: int = 3,
    retry_delay: float = 5.0,
) -> dict:
    """重试包装器"""
    last_error = None

    for attempt in range(max_retries):
        try:
            result = func()
            if result["success"]:
                return result
            last_error = result.get("error")
        except Exception as e:
            last_error = str(e)

        if attempt < max_retries - 1:
            logger.warning(
                f"Download failed (attempt {attempt + 1}/{max_retries}): {last_error}"
            )
            time.sleep(retry_delay)

    return {"success": False, "error": f"Failed after {max_retries} attempts: {last_error}"}

# 使用示例
result = retry_on_failure(
    lambda: download_file(image_url, filepath),
    max_retries=3,
    retry_delay=5.0
)
```

### Pattern 5: 配置文件管理
**What:** 使用 Hydra 配置系统管理下载参数
**When to use:** 用户自定义下载行为
**Example:**
```python
# Source: Hydra 配置模式
# config.yaml
download:
  batch_size: 30      # 每批次作品数
  batch_delay: 2.0    # 批次间隔秒数
  concurrency: 1      # 并发数(暂不支持)
  image_delay: 2.5    # 单张图片间隔

# download_config.py
from pydantic import BaseModel, Field

class DownloadConfig(BaseModel):
    """下载配置模型"""
    batch_size: int = Field(default=30, ge=1, le=100)
    batch_delay: float = Field(default=2.0, ge=0.0)
    concurrency: int = Field(default=1, ge=1)  # Phase 6 仅支持 1
    image_delay: float = Field(default=2.5, ge=0.0)

# 使用
from hydra import compose, initialize_config_dir
from omegaconf import OmegaConf

with initialize_config_dir(config_dir=config_path):
    cfg = compose(config_name="config")
    download_cfg = DownloadConfig(**cfg.download)

# 应用延迟
time.sleep(download_cfg.image_delay)
```

### Anti-Patterns to Avoid
- **手动拼接 next_url 参数:** 使用 `api.parse_qs(next_url)` 而非手动解析
- **全局进度文件:** 每个排行榜使用独立的 `.progress.json` 文件,避免冲突
- **硬编码重试次数:** 从配置读取,便于调优
- **忽略 API 响应中的 next_url:** 导致月榜无法完整下载

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| 排行榜类型验证 | 自定义正则或 if-else | Pydantic 模型 + 预定义映射 | 类型安全,易于扩展,错误信息友好 |
| 分页处理 | 手动构造 offset 参数 | pixivpy3 的 `next_url` + `parse_qs` | 官方推荐方式,处理边界情况 |
| 进度持久化 | pickle 或自定义格式 | JSON + Pydantic | 可读性,调试友好,类型验证 |
| 重试逻辑 | 自定义循环 + 异常捕获 | 封装的重试函数 | 统一行为,可配置,易于测试 |
| 配置管理 | 硬编码或环境变量 | Hydra + YAML 文件 | 层级配置,环境隔离,类型验证 |

**Key insight:** pixivpy3 已经提供了完整的分页机制,直接使用 `next_url` 自动跟随即可处理月榜 1500+ 张作品,无需手动计算 offset。

## Common Pitfalls

### Pitfall 1: API mode 参数不匹配
**What goes wrong:** 用户输入 `weekly` 但 API 需要 `week`,导致 400 错误
**Why it happens:** 用户友好的命名与 API 参数不一致
**How to avoid:** 使用映射表 `RANKING_TYPES` 转换用户输入到 API 参数
**Warning signs:** API 返回 400 错误,或排行榜数据为空

### Pitfall 2: 月榜数据不完整
**What goes wrong:** 只下载了前 50 张,缺少后续数据
**Why it happens:** 忘记跟随 `next_url`,或提前退出循环
**How to avoid:** 始终在循环中检查 `next_url`,直到为 `None` 时才退出
**Warning signs:** 月榜作品数少于 500,或远低于预期

### Pitfall 3: 进度文件丢失或损坏
**What goes wrong:** 程序崩溃后无法继续下载,需要从头开始
**Why it happens:** 进度文件未及时保存,或写入过程中断
**How to avoid:**
1. 每下载一张图片后立即保存进度
2. 使用原子写入(先写临时文件,再重命名)
3. 捕获 JSON 解析错误,优雅降级
**Warning signs:** 重复下载已存在的文件,进度文件为空

### Pitfall 4: 未来日期验证失败
**What goes wrong:** 用户请求未来日期的排行榜,API 返回错误
**Why it happens:** 未在前端验证日期有效性
**How to avoid:** 在 CLI 层验证 `date <= today`,立即报错
**Warning signs:** 用户输入的日期大于当前日期

### Pitfall 5: R18 排行榜认证失败
**What goes wrong:** 未登录或 token 无效时访问 R18 排行榜,返回 403
**Why it happens:** R18 内容需要认证和年龄验证
**How to avoid:** 确保 refresh token 有效,捕获 403 错误并提示用户检查账号设置
**Warning signs:** 仅 R18 类型失败,其他类型正常

## Code Examples

### 排行榜类型验证
```python
# Source: CLI 参数验证最佳实践
import click
from typing import Literal

# 类型别名(用于类型提示)
RankingType = Literal[
    "daily", "weekly", "monthly",
    "day_male", "day_female", "week_original", "week_rookie", "day_manga",
    "day_r18", "day_male_r18", "day_female_r18", "week_r18", "week_r18g"
]

def validate_ranking_type(ctx, param, value: str) -> str:
    """Click 参数验证器:排行榜类型"""
    valid_types = {
        "daily", "weekly", "monthly",
        "day_male", "day_female", "week_original", "week_rookie", "day_manga",
        "day_r18", "day_male_r18", "day_female_r18", "week_r18", "week_r18g"
    }

    if value not in valid_types:
        raise click.BadParameter(
            f"Invalid ranking type '{value}'. Valid types: {', '.join(sorted(valid_types))}"
        )
    return value

# 使用
@click.command()
@click.option('--type', callback=validate_ranking_type, required=True)
def download(type: str):
    mode = RANKING_TYPES[type]
    # ...
```

### 日期验证
```python
# Source: Python 日期处理最佳实践
from datetime import datetime, date

def validate_ranking_date(date_str: str) -> str:
    """验证日期格式和有效性"""
    try:
        parsed = datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        raise ValueError(
            f"Invalid date '{date_str}'. Format: YYYY-MM-DD"
        )

    today = date.today()
    if parsed > today:
        raise ValueError(
            f"Date '{date_str}' is in the future"
        )

    return date_str
```

### 完整下载流程(含断点续传)
```python
# Source: 综合模式实现
from pathlib import Path
import logging
from gallery_dl_auo.download.progress_manager import DownloadProgress
from gallery_dl_auo.download.retry_handler import retry_on_failure

logger = logging.getLogger("gallery_dl_auo")

def download_ranking_with_resume(
    client, mode: str, date: str, output_dir: Path, config: DownloadConfig
) -> dict:
    """带断点续传的排行榜下载"""
    # 1. 获取排行榜数据
    ranking_data = client.get_ranking_with_pagination(mode, date)

    # 2. 加载进度
    progress_file = output_dir / ".progress.json"
    progress = DownloadProgress.load(progress_file)
    if not progress:
        progress = DownloadProgress(
            mode=mode, date=date,
            downloaded_ids=set(), failed_ids=set()
        )

    # 3. 检查是否有未完成下载
    if progress.downloaded_ids:
        logger.info(
            f"Resuming download: {len(progress.downloaded_ids)} already downloaded"
        )

    # 4. 遍历排行榜,跳过已下载
    results = {"total": len(ranking_data), "success": [], "failed": []}

    for illust in ranking_data:
        if illust['id'] in progress.downloaded_ids:
            continue  # 跳过已下载

        # 下载作品(含重试)
        result = retry_on_failure(
            lambda: download_file(illust['image_url'], build_filepath(illust)),
            max_retries=3,
            retry_delay=5.0
        )

        # 记录结果
        if result["success"]:
            progress.downloaded_ids.add(illust['id'])
            results["success"].append(result)
        else:
            progress.failed_ids.add(illust['id'])
            results["failed"].append(result)

        # 保存进度
        progress.save(progress_file)

        # 速率控制
        time.sleep(config.image_delay)

    # 5. 下载完成,删除进度文件
    progress_file.unlink()
    logger.info("Download complete, progress file removed")

    return results
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| 手动拼接 API URL | pixivpy3 封装 | Phase 3 | 简化认证和错误处理 |
| 仅支持日榜 | 支持全部 13 种类型 | Phase 6 | 功能扩展,用户选择更灵活 |
| 无断点续传 | JSON 进度文件 | Phase 6 | 大规模数据集更可靠 |
| 硬编码延迟 | 配置文件管理 | Phase 6 | 用户可自定义下载行为 |

**Deprecated/outdated:**
- 手动计算 offset: pixivpy3 的 `next_url` 机制已足够,无需手动处理

## Open Questions

1. **月榜作品数上限**
   - What we know: 月榜通常 1500+ 张作品
   - What's unclear: pixivpy3 是否有 offset 限制(如 5000)
   - Recommendation: 测试获取完整月榜数据,如果遇到限制,添加警告和分批下载策略

2. **R18 排行榜年龄验证**
   - What we know: 需要账号开启 R18 显示设置
   - What's unclear: API 如何返回年龄验证失败
   - Recommendation: 捕获 403 错误,提示用户检查账号设置

3. **并发下载实现**
   - What we know: 配置中预留 `concurrency` 参数
   - What's unclear: Phase 6 是否实现多线程/异步下载
   - Recommendation: Phase 6 保持 `concurrency=1`,未来版本扩展异步下载

## Sources

### Primary (HIGH confidence)
- pixivpy3 GitHub 仓库 - illust_ranking API 文档和示例
- Pixiv AJAX API 文档 - 排行榜 API 参数和 mode 选项
- 项目现有代码: `pixiv_client.py` 中的 `get_ranking()` 实现

### Secondary (MEDIUM confidence)
- Python 下载最佳实践 - JSON 进度文件和重试机制
- Hydra 配置管理文档 - 层级配置和类型验证
- Pydantic v2 文档 - 数据模型和验证

### Tertiary (LOW confidence)
- Web 搜索结果 - Pixiv 排行榜类型描述(部分为用户经验,非官方文档)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - pixivpy3 官方文档,已在项目中使用
- Architecture: HIGH - 基于现有代码模式扩展,符合项目风格
- Pitfalls: HIGH - 来自 API 文档和常见错误模式

**Research date:** 2026-02-25
**Valid until:** 30 days (pixiv API 稳定,pixivpy3 版本近期无重大更新)
