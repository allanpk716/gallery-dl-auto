# Stack Research

**Domain:** Pixiv 排行榜下载器 (CLI 工具)
**Researched:** 2026-02-24
**Confidence:** HIGH

## Recommended Stack

### Core Technologies

| Technology | Version | Purpose | Why Recommended |
|------------|---------|---------|-----------------|
| **Python** | 3.10+ | 核心语言 | 与 gallery-dl 生态一致,成熟的异步支持和类型系统,丰富的第三方库 |
| **gallery-dl** | 1.27.0+ | 下载引擎 | 成熟的 pixiv 支持和 refresh token 认证,可直接作为 Python 模块调用,活跃维护 |
| **Playwright** | 1.51.0+ | 浏览器自动化 | 自动化获取 refresh token,支持 Chromium/Firefox/WebKit,可捕获网络请求和 cookies,比 Selenium 更现代可靠 |
| **Typer** | 0.21.1+ | CLI 框架 | 基于 Python 类型提示的现代化 CLI,自动生成帮助文档,支持子命令和复杂参数验证 |
| **Pydantic** | 2.x | 配置和数据验证 | 类型安全的数据验证,支持环境变量和 .env 文件加载,Settings 管理简化配置 |

### Supporting Libraries

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| **playwright-stealth** | 1.0.6+ | 反爬虫检测规避 | Playwright 启动时应用,让自动化脚本更像真实用户,避免被 pixiv 的反爬虫系统拦截 |
| **Rich** | 13.x+ | 终端美化输出 | 进度条、表格、语法高亮等美化 CLI 输出,提升用户体验 |
| **Loguru** | 0.7.3+ | 日志系统 | 比 logging 模块更简洁的 API,支持日志轮转和彩色输出,适合调试和问题排查 |
| **pathlib** | (标准库) | 跨平台路径处理 | 处理所有文件路径操作,避免 Windows/Linux 路径分隔符问题,比 os.path 更面向对象 |
| **python-dotenv** | 1.0.0+ | 环境变量加载 | 从 .env 文件加载配置,支持敏感信息(如 refresh token)与代码分离 |

### Development Tools

| Tool | Purpose | Notes |
|------|---------|-------|
| **uv** | 包管理器和构建工具 | 2025 年推荐的 Python 包管理器,比 pip 快 10-100 倍,支持 pyproject.toml 和虚拟环境管理 |
| **pyproject.toml** | 项目配置 | PEP 621 标准的项目元数据声明,替代 setup.py,统一管理依赖、构建和工具配置 |

## Installation

```bash
# 核心依赖
uv pip install gallery-dl playwright typer pydantic

# 支持库
uv pip install playwright-stealth rich loguru python-dotenv

# Playwright 浏览器(首次安装)
uv run playwright install chromium

# 开发工具
uv pip install -D pytest ruff mypy
```

## Alternatives Considered

| Category | Recommended | Alternative | Why Not |
|----------|-------------|-------------|---------|
| **浏览器自动化** | Playwright | Selenium | Selenium 是 2010 年代的技术,需要额外的 WebDriver 管理,API 不如 Playwright 现代,且 Playwright 由 Microsoft 维护,社区活跃度高 (Context7: Benchmark 92 vs 82) |
| **浏览器自动化** | Playwright | Requests + BeautifulSoup | pixiv 的登录流程需要 JavaScript 执行和 OAuth 重定向,无法通过纯 HTTP 请求完成,必须使用真实浏览器 |
| **CLI 框架** | Typer | Click | Click 需要手动管理参数装饰器和帮助文本,Typer 基于类型提示自动生成,代码更简洁,与 Pydantic 集成更好 (Context7: 两者都是 pallets/fastapi 团队维护) |
| **CLI 框架** | Typer | argparse | argparse 是标准库但 API 冗长,缺乏现代特性如子命令组织和类型验证,需要大量样板代码 |
| **配置管理** | Pydantic Settings | configparser | configparser 不支持类型验证和环境变量嵌套,Pydantic 提供强类型和自动验证,更适合复杂配置 (Context7 verified) |
| **HTTP 客户端** | (无需额外库) | httpx/requests | 本项目封装 gallery-dl,不需要独立的 HTTP 客户端,gallery-dl 内部已处理所有 HTTP 请求 |
| **日志库** | Loguru | logging | logging 是标准库但配置复杂,Loguru 提供开箱即用的彩色输出和轮转,对于 CLI 工具更友好 |

## What NOT to Use

| Avoid | Why | Use Instead |
|-------|-----|-------------|
| **Selenium** | 旧技术栈,需要手动管理 WebDriver,性能和稳定性不如 Playwright | Playwright |
| **直接调用 pixiv API** | pixiv 已移除用户名/密码认证,只支持 OAuth refresh token,手动实现复杂且易失效 | 封装 gallery-dl,它已处理认证和 API 调用 |
| **os.path** | 函数式 API 不够直观,容易在 Windows 上出现路径分隔符问题 | pathlib (标准库,面向对象,跨平台) |
| **手写 refresh token 提取逻辑** | pixiv OAuth 流程复杂,需要处理 PKCE 挑战和回调,容易出错 | 使用 Playwright 自动化浏览器登录并捕获网络请求 |
| **setup.py + setup.cfg** | 2025 年已被 pyproject.toml (PEP 621) 取代,导致工具链碎片化 | pyproject.toml 作为唯一配置源 |
| **Poetry (< 2.0)** | 2025 年 1 月 Poetry 2.0 才支持 pyproject.toml [project] 表,旧版使用专有 [tool.poetry] 表,不兼容标准 | uv + pyproject.toml (PEP 621) |
| **硬编码配置路径** | Windows/Linux/macOS 配置文件位置不同,硬编码会破坏跨平台兼容性 | 使用 pathlib.Path.home() 和标准配置目录 |

## Stack Patterns by Variant

**如果是纯下载工具(无需浏览器自动化):**
- 移除 Playwright 和 playwright-stealth
- 要求用户手动提供 refresh token(从浏览器开发者工具复制)
- 简化架构,但牺牲自动化的核心价值

**如果需要 GUI 界面:**
- 添加 Textual (终端 TUI) 或 PyQt (桌面 GUI)
- 但项目明确 Out of Scope,应专注于 CLI

**如果需要高性能并发下载:**
- 添加 asyncio + aiohttp
- 但 gallery-dl 已内置并发控制,无需额外引入复杂度

## Version Compatibility

| Package A | Compatible With | Notes |
|-----------|-----------------|-------|
| Python 3.10+ | gallery-dl 1.27+ | gallery-dl 支持 Python 3.8+,但 3.10+ 提供更好的类型提示和 match 语句 |
| Playwright 1.51+ | playwright-stealth 1.0.6+ | 两者 API 稳定,兼容性良好 (Context7 verified) |
| Typer 0.21+ | Pydantic 2.x | Typer 基于 type hints,与 Pydantic 的类型系统无缝集成 |
| Pydantic 2.x | Python 3.10+ | Pydantic v2 使用 Rust 加速,需要 Python 3.7+,推荐 3.10+ 以获得完整特性 |

## Critical Implementation Notes

### 1. gallery-dl 集成方式
- **作为 Python 模块调用**,不通过 subprocess
- 使用 `gallery_dl.config.set()` 配置选项
- 使用 `gallery_dl.job.DownloadJob(url).run()` 执行下载
- 通过 `metadata` 选项获取 JSON 格式的作品信息

```python
from gallery_dl import config, job

# 配置 refresh token
config.set(("extractor", "pixiv"), "refresh-token", token)

# 配置输出格式
config.set(("extractor", "pixiv"), "filename", "{id}{num}.{extension}")
config.set(("extractor", "pixiv"), "metadata", True)

# 执行下载
job.DownloadJob("https://www.pixiv.net/ranking.php?mode=daily").run()
```

### 2. Playwright 自动化流程
- 启动浏览器并导航到 pixiv 登录页
- 用户手动登录(首次),监听网络请求
- 捕获 OAuth 回调中的 `code` 参数
- 交换 code 为 refresh token
- 保存到配置文件,后续自动使用

```python
from playwright.sync_api import sync_playwright
from playwright_stealth import stealth_sync

with sync_playwright() as p:
    browser = p.chromium.launch(headless=False)
    page = browser.new_page()
    stealth_sync(page)  # 应用反检测

    # 监听网络请求
    def handle_response(response):
        if "callback" in response.url and "code=" in response.url:
            code = extract_code_from_url(response.url)
            # 交换 code 为 refresh token

    page.on("response", handle_response)
    page.goto("https://app-api.pixiv.net/web/v1/login")
```

### 3. Pydantic Settings 配置管理
- 使用 `BaseSettings` 自动从环境变量和 .env 加载
- 支持嵌套配置和验证
- 类型安全的配置访问

```python
from pydantic_settings import BaseSettings, SettingsConfigDict

class PixivConfig(BaseSettings):
    model_config = SettingsConfigDict(
        env_prefix="PIXIV_",
        env_file=".env",
        env_nested_delimiter="__"
    )

    refresh_token: str | None = None
    download_dir: str = "~/Pictures/pixiv"
    rate_limit: int = 1  # 每秒请求数,避免被封禁

config = PixivConfig()
```

### 4. Windows 路径处理最佳实践
- 始终使用 `pathlib.Path`,避免字符串拼接
- 使用 `/` 运算符连接路径(跨平台)
- 使用 `Path.home()` 获取用户目录

```python
from pathlib import Path

# 错误方式(Windows 特定)
config_path = "C:\\Users\\user\\.config\\gallery-dl\\config.json"

# 正确方式(跨平台)
config_path = Path.home() / ".config" / "gallery-dl" / "config.json"
```

## Sources

- **Context7 library ID**: `/mikf/gallery-dl` — gallery-dl 作为 Python 模块的 API 使用和 pixiv 认证配置 (HIGH confidence)
- **Context7 library ID**: `/websites/playwright_dev_python` — Playwright Python API,浏览器自动化,网络请求监听,cookies 管理 (HIGH confidence)
- **Context7 library ID**: `/fastapi/typer` — Typer CLI 框架,子命令,参数验证 (HIGH confidence)
- **Context7 library ID**: `/websites/pydantic_dev` — Pydantic Settings,环境变量加载,嵌套配置 (HIGH confidence)
- **Context7 library ID**: `/textualize/rich` — Rich 终端美化,进度条,表格 (HIGH confidence)
- **Context7 library ID**: `/delgan/loguru` — Loguru 日志系统 (HIGH confidence)
- **WebSearch**: "Python CLI tool best practices 2025 project structure configuration management" — 2025 年 Python 项目结构和 pyproject.toml 标准 (MEDIUM confidence, verified by packaging.python.org)
- **WebSearch**: "pixiv API authentication refresh token automation 2025" — pixiv OAuth 流程和 refresh token 获取方法 (HIGH confidence, 多个开源项目验证)
- **WebSearch**: "playwright stealth mode avoid bot detection Python 2025" — playwright-stealth 反爬虫检测 (MEDIUM confidence, 社区最佳实践)
- **WebSearch**: "Python pathlib vs os path 2025 best practices cross-platform Windows" — pathlib 跨平台优势 (HIGH confidence, Real Python 和官方文档验证)
- **WebSearch**: "gallery-dl pixiv configuration best practices refresh token management 2025" — gallery-dl pixiv 配置示例 (HIGH confidence, GitHub issues 和官方文档)

---
*Stack research for: Pixiv 排行榜下载器*
*Researched: 2026-02-24*
