# Phase 03: 排行榜基础下载 - Research

**Researched:** 2026-02-25
**Domain:** Pixiv API 排行榜下载、速率控制、文件下载
**Confidence:** HIGH

## Summary

Phase 3 需要实现从 Pixiv 下载每日排行榜图片的核心功能。经过研究,发现 **pixivpy3** 是 Python 生态中成熟的 Pixiv API 库,支持 refresh token 认证和排行榜访问。关键发现包括:

1. **pixivpy3 是标准选择**: 该库提供完整的 AppPixivAPI,支持 `illust_ranking()` 方法获取排行榜数据,配合 `download()` 方法下载图片
2. **速率控制至关重要**: Pixiv 有严格的速率限制,必须实现 2-3 秒间隔 + 随机抖动的保守策略,避免触发 429 错误
3. **文件下载最佳实践**: 使用 requests 的 `stream=True` 进行流式下载,配合 iter_content() 分块写入,避免内存溢出

**Primary recommendation:** 使用 pixivpy3 库的 AppPixivAPI 类进行排行榜访问,结合自定义的速率控制和稳健的文件下载逻辑,通过 Click 子命令模式集成到现有 CLI 架构中。

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **CLI 命令**: `pixiv-downloader download` (子命令模式,与 login/status/refresh 平级)
- **输出格式**: 默认 JSON 输出 (第三方友好,与 refresh 命令风格一致)
  - JSON 包含: 下载统计、成功列表、失败列表、文件路径
  - 不输出 Rich 进度条 (除非添加 --human 参数)
- **日期参数**: `--date 2026-02-23` (默认今天)
  - 格式: YYYY-MM-DD
  - 支持今天、昨天、指定日期
- **保存路径**: 可配置,默认固定目录
  - 默认: `./pixiv-downloads/` (可通过 --output 覆盖)
- **文件命名**: `作品ID_标题.扩展名`
  - 示例: `12345678_美丽的风景.jpg`
  - 标题中的特殊字符需清理 (Windows 兼容)
- **目录结构**: `排行榜名称-日期/作品ID_标题.扩展名`
  - 示例: `daily-2026-02-23/12345678_美丽的风景.jpg`
- **请求间隔**: 保守策略 (大间隔+随机抖动)
  - 固定基础间隔: 2-3 秒
  - 随机抖动: ±0.5-1.5 秒
- **并发下载**: 串行下载 (一次一张)
  - 不使用多线程/异步并发
- **单图失败**: 跳过并继续
  - 记录失败到 JSON 输出
  - 包含失败原因 (网络错误、404、权限等)

### Claude's Discretion
- 具体的请求间隔数值 (2-3 秒 + 抖动) — 研究时根据 pixiv API 特性调整
- 标题特殊字符清理规则 — 确保 Windows 兼容,不破坏文件名可读性
- JSON 输出的详细字段设计 — 包含足够信息供第三方使用

### Deferred Ideas (OUT OF SCOPE)
- 增量下载和断点续传 — Phase 7 实现
- 多排行榜类型 (周榜、月榜) — Phase 6 实现
- 下载进度条、实时显示 — Phase 8 实现
- 并发下载优化 — 未来考虑,Phase 3 串行即可
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| RANK-01 | 用户能够下载 pixiv 每日排行榜 | pixivpy3 库的 `illust_ranking(mode='day', date='YYYY-MM-DD')` 方法 |
| RANK-04 | 用户能够通过参数指定要下载的排行榜类型 | Click 的 `--date` 参数支持日期指定,pixivpy3 的 mode 参数支持排行榜类型 |
| CONT-01 | 程序下载排行榜中的图片文件 | pixivpy3 的 `download()` 方法 + requests 流式下载最佳实践 |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| pixivpy3 | 3.7.5+ | Pixiv API 访问 | 官方社区维护,支持 OAuth + AppAPI,提供 `illust_ranking()` 和 `download()` 方法,广泛使用(1.8k stars) |
| requests | 2.31.0+ | HTTP 请求和文件下载 | Python HTTP 客户端标准库,支持流式下载、会话管理、超时控制,项目已依赖 |
| click | 8.1.0+ | CLI 命令行接口 | 项目已使用,子命令模式成熟,与现有架构一致 |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pathlib | stdlib | 跨平台路径处理 | 文件路径构建和目录创建,Windows 兼容性 |
| time | stdlib | 速率控制延迟 | 实现请求间隔和随机抖动 |
| json | stdlib | JSON 输出格式化 | 构建结构化输出结果 |
| re | stdlib | 文件名清理 | 移除标题中的非法字符 |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| pixivpy3 | 手动调用 Pixiv API | pixivpy3 已处理认证、请求签名、错误解析等复杂逻辑,重复造轮子增加维护负担 |
| pixivpy3 | pixiv-api (azuline) | pixiv-api 已停止维护(2021),pixivpy3 活跃维护且社区更大 |
| requests | httpx/aiohttp | requests 同步模型符合 Phase 3 串行下载需求,httpx 异步优势在 Phase 3 不需要 |
| 手动实现速率控制 | tenacity 库 | tenacity 提供声明式重试,但简单场景下 time.sleep() + random 更直观可控 |

**Installation:**
```bash
pip install pixivpy3>=3.7.5
```

Note: requests 和 click 已在项目依赖中。

## Architecture Patterns

### Recommended Project Structure
```
src/gallery_dl_auo/
├── download/
│   ├── __init__.py
│   ├── ranking_downloader.py    # 排行榜下载逻辑
│   ├── file_downloader.py       # 文件下载工具
│   └── rate_limiter.py          # 速率控制器
├── cli/
│   └── download_cmd.py          # download 子命令
└── utils/
    └── filename_sanitizer.py    # 文件名清理工具
```

### Pattern 1: PixivPy API Client 封装
**What:** 使用 pixivpy3 的 AppPixivAPI 类,通过 refresh token 认证,访问排行榜数据
**When to use:** 所有需要访问 Pixiv API 的场景
**Example:**
```python
from pixivpy3 import AppPixivAPI

# Source: https://github.com/upbit/pixivpy
api = AppPixivAPI()
api.auth(refresh_token=REFRESH_TOKEN)

# 获取每日排行榜
json_result = api.illust_ranking(mode='day', date='2026-02-23')
for illust in json_result.illusts:
    print(f"[{illust.title}] {illust.image_urls.medium}")

# 下载图片
api.download(illust.image_urls.large, path='./downloads')
```

### Pattern 2: 流式文件下载 (Streaming Download)
**What:** 使用 requests 的 `stream=True` 避免内存溢出,分块写入文件
**When to use:** 下载大文件(>10MB)或批量下载场景
**Example:**
```python
import requests

# Source: https://stackoverflow.com/questions/16694907
def download_file(url: str, filepath: str, chunk_size: int = 8192) -> None:
    """流式下载文件,避免内存溢出"""
    with requests.get(url, stream=True, timeout=30) as response:
        response.raise_for_status()
        with open(filepath, 'wb') as f:
            for chunk in response.iter_content(chunk_size=chunk_size):
                if chunk:  # 过滤保持连接的新块
                    f.write(chunk)
```

### Pattern 3: 速率控制 (Rate Limiting)
**What:** 在请求间添加延迟 + 随机抖动,避免触发 429 错误
**When to use:** 批量 API 调用或文件下载场景
**Example:**
```python
import time
import random

# Source: Phase 3 CONTEXT.md 决策
def rate_limit_delay(base_seconds: float = 2.5, jitter: float = 1.0) -> None:
    """保守速率控制: 固定间隔 + 随机抖动"""
    delay = base_seconds + random.uniform(-jitter, jitter)
    time.sleep(max(0, delay))

# 使用示例
for illust in ranking:
    download_illust(illust)
    rate_limit_delay(base_seconds=2.5, jitter=1.0)  # 1.5-3.5 秒
```

### Pattern 4: Windows 文件名清理
**What:** 移除 Windows 非法字符,确保跨平台兼容
**When to use:** 构建文件名时,包含用户输入(标题、作者名)
**Example:**
```python
import re

def sanitize_filename(filename: str, max_length: int = 200) -> str:
    """清理文件名,Windows 兼容

    Windows 非法字符: < > : " / \ | ? *
    保留字符: 空格、下划线、连字符、中文
    """
    # 移除非法字符
    filename = re.sub(r'[<>:"/\\|?*]', '', filename)
    # 移除首尾空格和点
    filename = filename.strip('. ')
    # 限制长度(保留扩展名空间)
    return filename[:max_length]

# 使用示例
safe_name = sanitize_filename("美丽的风景<测试>.jpg")  # "美丽的风景测试.jpg"
```

### Anti-Patterns to Avoid
- **一次性加载全部排行榜数据**: Pixiv 排行榜可能包含 100+ 项,应使用 `parse_qs(next_url)` 分页获取 — 避免内存溢出
- **直接使用 illust.title 作为文件名**: 标题可能包含 Windows 非法字符 — 必须清理
- **忽略速率限制**: 触发 429 错误会导致 IP 被临时封禁 — 必须实现延迟
- **全局禁用 SSL 验证**: 绕过安全检查增加中间人攻击风险 — 使用合法证书

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| Pixiv API 认证和请求签名 | 手动构造 OAuth 头部、X-Client-Hash | pixivpy3 | Pixiv API 需要 X-Client-Time/X-Client-Hash 签名,逻辑复杂且易变 |
| 排行榜分页逻辑 | 手动解析 next_url 参数 | api.parse_qs(next_url) | pixivpy3 已实现标准化分页解析 |
| 文件下载重试逻辑 | 手动循环 + 异常捕获 | requests HTTPAdapter + Retry | urllib3 的 Retry 提供指数退避、状态码过滤等成熟机制 |
| Refresh token 存储 | 手动写入 JSON/INI | 现有 TokenStorage 类 | Phase 2 已实现加密存储,直接复用 |

**Key insight:** Pixiv API 认证和签名逻辑复杂(包括时间戳、设备指纹、Cloudflare 绕过),pixivpy3 已处理这些细节,重复实现增加维护成本和风险。

## Common Pitfalls

### Pitfall 1: 触发 Pixiv 速率限制 (429 Too Many Requests)
**What goes wrong:** 快速连续请求排行榜或下载图片,Pixiv 返回 429 错误,IP 可能被临时封禁
**Why it happens:** Pixiv 有严格的速率限制(具体阈值未公开),触发后会拒绝服务
**How to avoid:**
- 实现保守的请求间隔: 2-3 秒 + 随机抖动(±1秒)
- 串行下载,不使用并发
- 监控响应状态码,429 时延长等待时间

**Warning signs:**
- 连续快速下载 10-20 张图片后突然失败
- requests.exceptions.HTTPError: 429 Client Error
- 响应头包含 `Retry-After` 字段

**Reference:** GitHub issues (mikf/gallery-dl#535) 显示大量 Pixiv 下载场景遇到速率限制问题

### Pitfall 2: 文件名包含 Windows 非法字符
**What goes wrong:** 在 Windows 上保存文件时报错 `OSError: [Errno 22] Invalid argument`
**Why it happens:** Windows 文件系统禁止 `<>:"/\|?*` 字符,而 Pixiv 作品标题经常包含这些字符
**How to avoid:**
- 使用正则表达式清理文件名: `re.sub(r'[<>:"/\\|?*]', '', title)`
- 限制文件名长度(<200字符)
- 测试跨平台兼容性(Windows/Linux)

**Warning signs:**
- 标题包含特殊符号(如 `<>?:` 等)
- 仅在 Windows 上失败,Linux 正常

### Pitfall 3: 内存溢出 (下载大文件)
**What goes wrong:** 下载高质量原图(>10MB)时 Python 进程内存暴涨,甚至 OOM 崩溃
**Why it happens:** 默认的 `requests.get()` 会将整个文件加载到内存
**How to avoid:**
- 使用 `stream=True` 参数
- 使用 `iter_content(chunk_size=8192)` 分块写入
- 避免一次性读取 `response.content`

**Warning signs:**
- 下载大文件时系统内存占用激增
- Python 进程被 OOM Killer 终止

### Pitfall 4: 路径遍历攻击 (Path Traversal)
**What goes wrong:** 恶意标题(如 `../../etc/passwd`)导致文件写入到非预期目录
**Why it happens:** 未清理用户输入(标题、作者名)直接拼接路径
**How to avoid:**
- 使用 `pathlib.Path` 构建路径
- 使用 `resolve()` 获取绝对路径并验证是否在预期目录内
- 清理文件名中的 `..` 和路径分隔符

**Warning signs:**
- 标题或作者名包含 `..` 或路径分隔符
- 文件保存到项目目录外

**Reference:** https://osintteam.blog/path-traversal-and-remediation-in-python-0b6e126b4746

## Code Examples

Verified patterns from official sources:

### 获取 Pixiv 每日排行榜
```python
from pixivpy3 import AppPixivAPI

# Source: https://github.com/upbit/pixivpy
api = AppPixivAPI()
api.auth(refresh_token=REFRESH_TOKEN)

# 获取 2026-02-23 的每日排行榜
json_result = api.illust_ranking(mode='day', date='2026-02-23')

# 遍历排行榜作品
for illust in json_result.illusts:
    print(f"#{illust.rank} {illust.title} by {illust.user.name}")
    print(f"  URL: {illust.image_urls.large}")

# 分页获取下一页
if json_result.next_url:
    next_qs = api.parse_qs(json_result.next_url)
    json_result = api.illust_ranking(**next_qs)
```

### 下载排行榜图片到指定目录
```python
from pathlib import Path
from pixivpy3 import AppPixivAPI

# Source: https://github.com/upbit/pixivpy
def download_ranking(api: AppPixivAPI, date: str, output_dir: Path):
    """下载指定日期的每日排行榜"""
    json_result = api.illust_ranking(mode='day', date=date)

    # 创建日期目录: daily-2026-02-23/
    ranking_dir = output_dir / f"daily-{date}"
    ranking_dir.mkdir(parents=True, exist_ok=True)

    for illust in json_result.illusts:
        # 文件名: 12345678_美丽的风景.jpg
        filename = f"{illust.id}_{illust.title}.jpg"
        filepath = ranking_dir / filename

        # 下载图片
        api.download(
            url=illust.image_urls.large,
            path=str(ranking_dir),
            name=filename
        )
```

### 稳健的文件下载 (带错误处理)
```python
import requests
from pathlib import Path

# Source: https://stackoverflow.com/questions/16694907
def robust_download(
    url: str,
    filepath: Path,
    timeout: int = 30,
    chunk_size: int = 8192
) -> dict:
    """稳健的文件下载,返回结果字典"""
    result = {
        'success': False,
        'filepath': str(filepath),
        'error': None
    }

    try:
        with requests.get(url, stream=True, timeout=timeout) as response:
            response.raise_for_status()

            # 确保父目录存在
            filepath.parent.mkdir(parents=True, exist_ok=True)

            # 流式写入文件
            with open(filepath, 'wb') as f:
                for chunk in response.iter_content(chunk_size=chunk_size):
                    if chunk:
                        f.write(chunk)

        result['success'] = True

    except requests.exceptions.Timeout:
        result['error'] = f"下载超时 ({timeout}秒)"
    except requests.exceptions.HTTPError as e:
        result['error'] = f"HTTP 错误: {e.response.status_code}"
    except requests.exceptions.ConnectionError:
        result['error'] = "网络连接失败"
    except OSError as e:
        result['error'] = f"文件写入失败: {e}"

    return result
```

### 带速率控制的批量下载
```python
import time
import random
from pathlib import Path

def download_with_rate_limit(
    api,
    illusts: list,
    output_dir: Path,
    base_delay: float = 2.5,
    jitter: float = 1.0
) -> dict:
    """带速率控制的批量下载"""
    results = {
        'total': len(illusts),
        'success': [],
        'failed': []
    }

    for illust in illusts:
        # 下载单张图片
        result = download_illust(api, illust, output_dir)

        if result['success']:
            results['success'].append(result)
        else:
            results['failed'].append(result)

        # 速率控制: 基础延迟 + 随机抖动
        delay = base_delay + random.uniform(-jitter, jitter)
        time.sleep(max(0, delay))

    return results
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| 密码登录 Pixiv API | OAuth + Refresh Token | 2019 (#158 issue) | Pixiv 废弃密码登录,必须使用 refresh token |
| 手动构造 API 请求 | pixivpy3 库封装 | 2015+ | 简化认证、签名、错误处理,降低维护成本 |
| 一次性加载全部排行榜 | 分页获取 (next_url) | 持续优化 | 避免内存溢出,支持大型排行榜 |
| 同步无延迟下载 | 速率控制 + 抖动 | 经验积累 | 避免 429 错误,提高稳定性 |

**Deprecated/outdated:**
- **密码登录**: Pixiv 在 2019 年废弃密码登录,必须使用 refresh token — pixivpy3 的 `login()` 方法已不可用
- **Public-API**: Pixiv 在 2022 年废弃 Public-API,必须使用 App-API — pixivpy3 3.7+ 已移除 Public-API 支持
- **手动 X-Client-Hash 计算**: pixivpy3 已内置签名逻辑 — 不需要手动实现

## Open Questions

1. **Pixiv 速率限制的具体阈值是多少?**
   - What we know: 社区经验表明连续快速请求会触发 429,但官方未公开具体数值
   - What's unclear: 每分钟/每小时允许的请求数上限
   - Recommendation: 采用保守策略(2-3秒间隔),监控 429 响应并动态调整

2. **pixivpy3 的 download() 方法是否内置速率控制?**
   - What we know: pixivpy3 源码显示 `download()` 方法直接调用 requests,无内置延迟
   - What's unclear: 是否在更高级别有全局速率控制
   - Recommendation: 假设无内置控制,在外层实现自定义速率控制

3. **排行榜作品的完整元数据结构是什么?**
   - What we know: `illust` 对象包含 id、title、user、image_urls 等基础字段
   - What's unclear: 完整的字段列表(如收藏数、浏览量、标签等)
   - Recommendation: Phase 3 只关注下载,元数据获取延后到 Phase 4,当前只使用必需字段

## Validation Architecture

nyquist_validation 配置未启用,跳过此部分。

## Sources

### Primary (HIGH confidence)
- https://github.com/upbit/pixivpy - PixivPy3 官方仓库,包含 API 使用示例、认证流程、下载方法
- https://pypi.org/project/pixivpy3/ - PyPI 官方包索引,版本信息和依赖声明
- 项目现有代码库 - Phase 2 的 TokenStorage、PixivOAuth、CLI 架构

### Secondary (MEDIUM confidence)
- https://stackoverflow.com/questions/16694907 - 大文件流式下载最佳实践,社区验证的代码模式
- https://github.com/mikf/gallery-dl/issues/535 - gallery-dl 项目遇到的 Pixiv 速率限制问题和解决方案
- https://osintteam.blog/path-traversal-and-remediation-in-python - Python 路径遍历防护实践

### Tertiary (LOW confidence)
- Web 搜索结果中的速率限制博客文章 - 通用 API 速率控制建议,未针对 Pixiv 验证

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - pixivpy3 是社区标准库,活跃维护,文档完善
- Architecture: HIGH - 基于官方示例和成熟设计模式,已在多个项目中验证
- Pitfalls: HIGH - 来自真实项目 issue 和社区经验,有具体案例支持

**Research date:** 2026-02-25
**Valid until:** 2027-02-25 (Pixiv API 相对稳定,pixivpy3 持续维护)
