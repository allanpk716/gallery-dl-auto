# Architecture Research

**Domain:** pixiv 排行榜下载器 (封装型 CLI 工具)
**Researched:** 2026-02-24
**Confidence:** HIGH (基于 gallery-dl 源码、官方文档、社区最佳实践)

## Standard Architecture

### System Overview

```
┌─────────────────────────────────────────────────────────────┐
│                      CLI Interface Layer                     │
│  (argparse/click/typer)                                     │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐      │
│  │ Auth Manager │  │ Config Mgr   │  │  CLI Parser  │      │
│  └──────┬───────┘  └──────┬───────┘  └──────┬───────┘      │
│         │                  │                  │              │
├─────────┴──────────────────┴──────────────────┴─────────────┤
│                    Core Orchestration Layer                  │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────┐    │
│  │            Ranking Downloader Service                │    │
│  │  - Ranking Type Selection (daily/weekly/monthly)    │    │
│  │  - Download Coordination                             │    │
│  │  - Result Aggregation                                │    │
│  └──────────────────────┬──────────────────────────────┘    │
│                         │                                    │
├─────────────────────────┴────────────────────────────────────┤
│                    Wrapper Integration Layer                 │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────┐    │
│  │         gallery-dl Python API Wrapper               │    │
│  │  - Subprocess/Library Invocation                     │    │
│  │  - Result Capture (JSON parsing)                     │    │
│  │  - Error Translation                                 │    │
│  └──────────────────────┬──────────────────────────────┘    │
│                         │                                    │
├─────────────────────────┴────────────────────────────────────┤
│                    Token Management Layer                    │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────────────────────────────────────────────────┐    │
│  │         Browser Automation Token Capturer            │    │
│  │  - Selenium/Playwright Integration                   │    │
│  │  - Login Flow Automation                             │    │
│  │  - Token Extraction & Refresh                        │    │
│  └──────────────────────┬──────────────────────────────┘    │
│                         │                                    │
├─────────────────────────┴────────────────────────────────────┤
│                      Data Layer                              │
├─────────────────────────────────────────────────────────────┤
│  ┌──────────┐  ┌──────────┐  ┌──────────┐                   │
│  │Token Store│  │ Config   │  │  Result  │                   │
│  │(keyring) │  │ (JSON)   │  │  (JSON)  │                   │
│  └──────────┘  └──────────┘  └──────────┘                   │
└─────────────────────────────────────────────────────────────┘
```

### Component Responsibilities

| Component | Responsibility | Typical Implementation |
|-----------|----------------|------------------------|
| **CLI Interface** | 用户交互、参数解析、命令分发 | argparse/click/typer |
| **Auth Manager** | Token 生命周期管理、自动刷新、安全存储 | keyring + OAuth2 flow |
| **Config Manager** | 配置文件读写、默认值管理、路径解析 | JSON/YAML + dataclasses |
| **Ranking Downloader** | 排行榜选择、下载协调、结果聚合 | Service class + async/await |
| **gallery-dl Wrapper** | 封装外部工具、结果转换、错误处理 | subprocess.run / import |
| **Token Capturer** | 浏览器自动化、Token 捕获、自动登录 | Selenium/Playwright |
| **Token Store** | Token 持久化、加密存储 | keyring 库 |
| **Result Formatter** | JSON 输出格式化、数据结构化 | Python dataclasses/Pydantic |

## Recommended Project Structure

```
src/
├── gallery_dl_auo/
│   ├── __init__.py
│   ├── __main__.py              # CLI entry point
│   ├── cli/                     # CLI interface layer
│   │   ├── __init__.py
│   │   ├── main.py              # Main CLI command
│   │   ├── commands/            # Subcommand implementations
│   │   │   ├── download.py      # Download command
│   │   │   ├── auth.py          # Auth command
│   │   │   └── config.py        # Config command
│   │   └── parser.py            # Argument parser setup
│   ├── core/                    # Core orchestration layer
│   │   ├── __init__.py
│   │   ├── downloader.py        # Ranking downloader service
│   │   ├── result.py            # Result aggregation
│   │   └── exceptions.py        # Custom exceptions
│   ├── wrapper/                 # Wrapper integration layer
│   │   ├── __init__.py
│   │   ├── gallery_dl.py        # gallery-dl wrapper
│   │   ├── parser.py            # Output parser
│   │   └── error_handler.py     # Error translation
│   ├── auth/                    # Token management layer
│   │   ├── __init__.py
│   │   ├── manager.py           # Token lifecycle manager
│   │   ├── browser/             # Browser automation
│   │   │   ├── __init__.py
│   │   │   ├── login.py         # Login automation
│   │   │   └── token_capture.py # Token extraction
│   │   └── storage.py           # Token storage (keyring)
│   ├── config/                  # Configuration layer
│   │   ├── __init__.py
│   │   ├── manager.py           # Config manager
│   │   ├── defaults.py          # Default values
│   │   └── schema.py            # Config schema (dataclass)
│   └── models/                  # Data models
│       ├── __init__.py
│       ├── download_result.py   # Download result model
│       ├── metadata.py          # Work metadata model
│       └── error.py             # Error model
├── tests/                       # Test suite
│   ├── unit/
│   ├── integration/
│   └── fixtures/
├── docs/                        # Documentation
└── tmp/                         # Temporary test files
```

### Structure Rationale

- **cli/**: CLI 独立分层,便于支持多种调用方式(终端/库),符合单一职责原则
- **core/**: 核心业务逻辑,不依赖具体实现,方便测试和替换组件
- **wrapper/**: 封装第三方工具(gallery-dl),隔离外部依赖,便于版本升级和维护
- **auth/**: 认证逻辑独立模块,Token 管理是关键功能,需要清晰的边界
- **config/**: 配置管理集中,支持多种配置源(文件/环境变量/命令行)
- **models/**: 数据模型定义,使用 dataclass/Pydantic 确保类型安全和 JSON 序列化

## Architectural Patterns

### Pattern 1: Wrapper/Facade Pattern

**What:** 通过封装层隔离外部依赖,提供统一接口,隐藏实现细节

**When to use:** 封装 gallery-dl 这种外部工具时,隔离复杂性,提供稳定接口

**Trade-offs:**
- ✅ 解耦外部依赖,升级时不影响业务代码
- ✅ 统一错误处理和结果格式
- ✅ 便于测试(可 mock wrapper)
- ❌ 增加一层抽象,略微增加复杂度
- ❌ 需要维护封装层与上游的同步

**Example:**
```python
# wrapper/gallery_dl.py
from typing import List, Dict
import subprocess
import json

class GalleryDlWrapper:
    """封装 gallery-dl,提供统一接口"""

    def __init__(self, config_path: str = None):
        self.config_path = config_path

    def download_ranking(
        self,
        ranking_type: str,
        refresh_token: str,
        output_format: str = "json"
    ) -> Dict:
        """
        下载排行榜并返回结构化结果

        Args:
            ranking_type: daily/weekly/monthly
            refresh_token: pixiv refresh token
            output_format: 输出格式

        Returns:
            {
                "success": bool,
                "files": List[str],
                "metadata": List[Dict],
                "errors": List[str]
            }
        """
        cmd = [
            "gallery-dl",
            "--config", self.config_path,
            "--output", output_format,
            f"https://www.pixiv.net/ranking.php?mode={ranking_type}"
        ]

        # 执行并捕获输出
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            env={"PIXIV_REFRESH_TOKEN": refresh_token}
        )

        # 统一错误处理
        if result.returncode != 0:
            return {
                "success": False,
                "files": [],
                "metadata": [],
                "errors": [result.stderr]
            }

        # 解析 JSON 输出
        try:
            data = json.loads(result.stdout)
            return {
                "success": True,
                "files": data.get("files", []),
                "metadata": data.get("metadata", []),
                "errors": []
            }
        except json.JSONDecodeError as e:
            return {
                "success": False,
                "files": [],
                "metadata": [],
                "errors": [f"JSON parse error: {e}"]
            }
```

### Pattern 2: Token Manager with Auto-Refresh

**What:** 集中管理 Token 生命周期,包括获取、存储、自动刷新和失效处理

**When to use:** 处理 OAuth refresh token,避免 token 过期导致下载失败

**Trade-offs:**
- ✅ 自动处理 token 过期,用户无感知
- ✅ 安全存储 token(使用 keyring)
- ✅ 支持多账号(未来扩展)
- ❌ 首次登录需要浏览器自动化,增加依赖
- ❌ token 刷新逻辑需要与 pixiv API 同步

**Example:**
```python
# auth/manager.py
import keyring
from datetime import datetime, timedelta

class TokenManager:
    """Token 生命周期管理器"""

    SERVICE_NAME = "gallery-dl-auto"
    TOKEN_KEY = "pixiv_refresh_token"
    EXPIRY_KEY = "token_expiry"

    def __init__(self):
        self.storage = keyring.get_keyring()

    def get_valid_token(self) -> str:
        """
        获取有效的 refresh token,自动刷新过期 token
        """
        # 从 keyring 读取
        token = self.storage.get_password(self.SERVICE_NAME, self.TOKEN_KEY)

        if not token:
            raise AuthError("No token found. Please login first.")

        # 检查是否过期(如果有过期时间)
        expiry_str = self.storage.get_password(self.SERVICE_NAME, self.EXPIRY_KEY)

        if expiry_str:
            expiry = datetime.fromisoformat(expiry_str)
            if datetime.now() >= expiry:
                # Token 过期,需要刷新
                token = self._refresh_token(token)

        return token

    def save_token(self, token: str, expires_in_days: int = 90):
        """保存 token 和过期时间"""
        self.storage.set_password(self.SERVICE_NAME, self.TOKEN_KEY, token)

        expiry = datetime.now() + timedelta(days=expires_in_days)
        self.storage.set_password(
            self.SERVICE_NAME,
            self.EXPIRY_KEY,
            expiry.isoformat()
        )

    def _refresh_token(self, old_token: str) -> str:
        """
        使用浏览器自动化刷新 token

        实际实现:
        1. 使用 Selenium/Playwright 打开 pixiv 登录页
        2. 使用 old_token 自动登录
        3. 捕获新的 refresh token
        4. 保存并返回
        """
        from .browser import TokenCapturer

        capturer = TokenCapturer()
        new_token = capturer.refresh_token(old_token)
        self.save_token(new_token)
        return new_token

    def clear_token(self):
        """清除存储的 token"""
        try:
            self.storage.delete_password(self.SERVICE_NAME, self.TOKEN_KEY)
            self.storage.delete_password(self.SERVICE_NAME, self.EXPIRY_KEY)
        except keyring.errors.PasswordDeleteError:
            pass  # Token 不存在,忽略
```

### Pattern 3: Result Aggregator Pattern

**What:** 聚合多次下载结果,提供统一的 JSON 输出格式,支持结构化返回给调用者

**When to use:** 批量下载时需要汇总所有结果,同时支持 CLI 输出和程序化调用

**Trade-offs:**
- ✅ 统一的结果格式,便于解析和集成
- ✅ 支持增量下载(只下载失败的项目)
- ✅ 详细的错误信息,便于调试
- ❌ 需要维护完整的元数据,内存占用稍高
- ❌ JSON 序列化增加 CPU 开销

**Example:**
```python
# core/result.py
from dataclasses import dataclass, field, asdict
from typing import List, Dict
import json

@dataclass
class WorkMetadata:
    """单个作品的元数据"""
    work_id: str
    title: str
    author: str
    tags: List[str]
    bookmarks: int
    views: int
    image_urls: List[str]

@dataclass
class DownloadResult:
    """下载结果聚合"""
    success: bool
    ranking_type: str
    total_works: int
    downloaded_files: List[str] = field(default_factory=list)
    metadata: List[WorkMetadata] = field(default_factory=list)
    errors: List[Dict[str, str]] = field(default_factory=list)

    def add_success(self, file_path: str, metadata: WorkMetadata):
        """添加成功的下载"""
        self.downloaded_files.append(file_path)
        self.metadata.append(metadata)

    def add_error(self, work_id: str, error: str):
        """添加失败的下载"""
        self.errors.append({
            "work_id": work_id,
            "error": error
        })

    def to_json(self, indent: int = 2) -> str:
        """转换为 JSON 字符串"""
        return json.dumps(asdict(self), indent=indent, ensure_ascii=False)

    def print_summary(self):
        """打印摘要信息(用于 CLI)"""
        print(f"Ranking: {self.ranking_type}")
        print(f"Total: {self.total_works}")
        print(f"Downloaded: {len(self.downloaded_files)}")
        if self.errors:
            print(f"Failed: {len(self.errors)}")
            for err in self.errors[:5]:  # 只显示前5个错误
                print(f"  - {err['work_id']}: {err['error']}")
```

## Data Flow

### Request Flow

```
[User CLI Command]
    ↓
[CLI Parser] → [Auth Manager] → [Token Store]
    ↓               ↓                  ↓
[Download Command] ← [Valid Token]
    ↓
[Ranking Downloader Service]
    ↓
[gallery-dl Wrapper] → [Execute gallery-dl] → [Parse JSON]
    ↓                         ↓                      ↓
[Result Aggregator] ← [Metadata & Files] ← [Downloaded Items]
    ↓
[JSON Output / Print Summary]
```

### Token Management Flow

```
[First Time Login]
    ↓
[Browser Automation] → [Open Login Page] → [Capture Token]
    ↓                              ↓                ↓
[Token Manager] → [Save to Keyring] ← [Extract Token]
    ↓
[Ready for Download]

[Subsequent Runs]
    ↓
[Token Manager] → [Get from Keyring] → [Check Expiry]
    ↓                                        ↓
[If Expired] → [Auto-Refresh] → [Update Keyring]
    ↓
[Return Valid Token]
```

### Key Data Flows

1. **认证流程:** 用户登录 → 浏览器自动化捕获 token → Token Manager 存储 → Keyring 加密存储 → 后续自动读取
2. **下载流程:** CLI 命令 → 获取 token → 调用 gallery-dl → 解析 JSON 输出 → 聚合结果 → 返回给用户
3. **配置流程:** 读取配置文件 → 合并命令行参数 → 应用默认值 → 传递给 gallery-dl
4. **错误处理:** 捕获异常 → 转换为统一格式 → 记录到 Result → 返回 JSON 输出

## Scaling Considerations

| Scale | Architecture Adjustments |
|-------|--------------------------|
| 单用户单次下载 | 当前架构完全适用,单线程同步执行即可 |
| 批量下载多个排行榜 | 引入 asyncio 并发下载,限制并发数避免被限流 |
| 长期自动化运行 | 添加定时任务(scheduler),自动刷新 token,持久化下载历史 |
| 多账号支持 | Token Manager 支持多账号存储,配置文件添加账号管理 |
| 高频次调用 | 实现本地缓存机制,避免重复下载,添加速率限制器 |

### Scaling Priorities

1. **First bottleneck:** pixiv 反爬虫限流
   - 解决方案: 添加请求间隔(sleep)、重试机制、IP 轮换(如果需要)

2. **Second bottleneck:** 大量图片下载占用带宽和存储
   - 解决方案: 支持增量下载(跳过已下载)、并发控制、断点续传

## Anti-Patterns

### Anti-Pattern 1: 硬编码 Token 或配置

**What people do:** 直接在代码中写死 refresh token 或配置路径

**Why it's wrong:**
- Token 泄露到 Git 仓库,安全风险
- 无法灵活配置,每次修改需要改代码
- 难以支持多环境(开发/生产)

**Do this instead:**
- 使用 keyring 安全存储敏感信息
- 配置文件使用标准路径(`~/.config/gallery-dl-auto/config.json`)
- 支持环境变量覆盖配置

### Anti-Pattern 2: 直接调用 gallery-dl CLI 而不处理输出

**What people do:** 简单封装 `subprocess.run("gallery-dl ...")`,不解析输出

**Why it's wrong:**
- 无法获取结构化结果,只能知道成功/失败
- 错误信息丢失,难以调试
- 无法提取元数据(标题、作者等)

**Do this instead:**
- 使用 gallery-dl 的 `--output json` 选项
- 解析 JSON 输出为结构化数据
- 提供详细的 Result 对象给调用者

### Anti-Pattern 3: 同步阻塞式浏览器自动化登录

**What people do:** 使用 Selenium 同步等待用户登录,阻塞整个程序

**Why it's wrong:**
- 用户必须等待浏览器打开,无法后台运行
- 超时处理困难,容易卡死
- 难以集成到自动化流程

**Do this instead:**
- 首次登录引导用户完成,后续自动刷新 token
- Token 刷新失败时提示用户重新登录,不强制阻塞
- 提供 `--headless` 选项用于自动化场景

### Anti-Pattern 4: 忽略 gallery-dl 的版本兼容性

**What people do:** 假设 gallery-dl API/输出格式永远不变

**Why it's wrong:**
- gallery-dl 升级可能改变 JSON 输出格式
- 配置选项可能弃用或重命名
- 导致封装层突然失效

**Do this instead:**
- 在 `setup.py` 中明确 gallery-dl 版本依赖
- 编写集成测试验证 gallery-dl 输出格式
- 提供版本检查和兼容性提示

## Integration Points

### External Services

| Service | Integration Pattern | Notes |
|---------|---------------------|-------|
| **gallery-dl** | Subprocess invocation + JSON parsing | 核心下载功能,必须确保版本兼容 |
| **pixiv API** | 通过 gallery-dl 间接调用 | 不直接调用 pixiv API,避免 API 变更 |
| **系统 Keyring** | keyring 库 | 跨平台安全存储,Windows 使用 Credential Manager |
| **浏览器自动化** | Selenium/Playwright | 仅用于首次登录和 token 刷新,可选依赖 |

### Internal Boundaries

| Boundary | Communication | Notes |
|----------|---------------|-------|
| CLI ↔ Core | 直接函数调用 | 紧耦合,CLI 是入口点 |
| Core ↔ Wrapper | 通过接口(Abstract Base Class) | 松耦合,便于替换 wrapper 实现 |
| Wrapper ↔ gallery-dl | subprocess 或 import | 隔离外部依赖 |
| Auth ↔ Storage | keyring API | 标准接口,跨平台兼容 |
| Core ↔ Result | Python 对象 | 数据传递,JSON 序列化可选 |

## Build Order (Component Dependencies)

基于架构分析,建议的构建顺序:

### Phase 1: Foundation (Week 1)
1. **Config Manager** - 配置管理基础设施
   - 原因: 所有组件都需要配置
   - 依赖: 无

2. **CLI Parser** - 基础命令行界面
   - 原因: 提供用户入口
   - 依赖: Config Manager

### Phase 2: Core Wrapper (Week 2)
3. **gallery-dl Wrapper** - 封装下载功能
   - 原因: 核心功能,其他功能依赖它
   - 依赖: Config Manager

4. **Result Models** - 数据模型定义
   - 原因: Wrapper 需要返回结构化结果
   - 依赖: 无(Pure data)

### Phase 3: Authentication (Week 3)
5. **Token Storage** - Token 安全存储
   - 原因: Auth Manager 依赖存储层
   - 依赖: Config Manager

6. **Browser Automation** - 登录自动化
   - 原因: Token 获取需要浏览器
   - 依赖: Token Storage

7. **Token Manager** - Token 生命周期管理
   - 原因: 整合存储和浏览器自动化
   - 依赖: Token Storage, Browser Automation

### Phase 4: Orchestration (Week 4)
8. **Ranking Downloader Service** - 下载协调服务
   - 原因: 核心业务逻辑
   - 依赖: gallery-dl Wrapper, Token Manager, Result Models

9. **Result Aggregator** - 结果聚合
   - 原因: 批量下载需要汇总结果
   - 依赖: Result Models

### Phase 5: Polish (Week 5)
10. **Error Handling** - 统一错误处理
    - 原因: 提升用户体验
    - 依赖: 所有组件

11. **Integration Tests** - 集成测试
    - 原因: 验证端到端流程
    - 依赖: 所有组件

**依赖关系图:**
```
Config Manager ──┬──> CLI Parser
                 ├──> Token Storage
                 └──> gallery-dl Wrapper

Token Storage ──────> Token Manager
                          ↑
Browser Automation ──────┘

gallery-dl Wrapper ───> Ranking Downloader Service
                              ↑
Token Manager ────────────────┤
                              |
Result Models ────────────────┘
```

## Sources

- **gallery-dl 源码分析**: https://github.com/mikf/gallery-dl (HIGH confidence - 官方仓库)
- **gallery-dl 文档**: https://gdl-docs.mikf.eu/ (HIGH confidence - 官方文档)
- **gallery-dl 配置参考**: https://github.com/mikf/gallery-dl/blob/master/docs/configuration.rst (HIGH confidence)
- **Python CLI 最佳实践**: https://realpython.com/python-click/ (MEDIUM confidence - Real Python)
- **Token 管理模式**: https://workos.com/guide/best-practices-for-cli-authentication (MEDIUM confidence)
- **Python Wrapper 模式**: https://medium.com/the-pythonworld/you-dont-need-that-python-library-you-need-this-pattern (MEDIUM confidence)
- **Selenium 自动化**: https://selenium-python.readthedocs.io/ (HIGH confidence - 官方文档)

---
*Architecture research for: pixiv 排行榜下载器 (gallery-dl-auto)*
*Researched: 2026-02-24*
