# Phase 7: 错误处理与健壮性 - Research

**Researched:** 2026-02-25
**Domain:** Python 错误处理、重试机制、SQLite 数据库管理、断点续传
**Confidence:** HIGH

## Summary

为 Pixiv 排行榜下载器增强错误处理和健壮性能力。核心实现包括:使用 Tenacity 库实现指数退避重试策略、使用 SQLite 维护下载历史记录(替代现有 JSON 进度文件)、使用临时文件+原子重命名机制确保文件完整性、实现结构化 JSON 错误输出。现有代码库已具备基础重试逻辑(retry_handler.py)和进度管理(progress_manager.py),Phase 7 将升级为生产级别的错误处理系统。

**Primary recommendation:** 使用 Tenacity 替换现有简单重试逻辑,使用 SQLite 替代 JSON 进度文件以支持更复杂的查询和更好的并发性,所有错误通过结构化 JSON 返回给第三方调用者。

<user_constraints>
## User Constraints (from CONTEXT.md)

### Implementation Decisions

#### 错误处理策略
- 网络请求失败时重试 3 次,使用指数退避策略(1秒、2秒、3秒)
- 错误消息友好且详细:显示错误类型 + 建议操作 + 原始错误信息
- 记录错误日志到文件,包含时间戳、错误类型、上下文信息

#### 增量下载检测
- Claude 决定最佳的文件检测方式
- 使用 SQLite 数据库维护下载记录(作品 ID、文件路径等)
- 使用临时文件 + 重命名机制处理部分下载的文件,避免不完整文件

#### 断点续传机制
- 使用 JSON 状态文件存储断点状态
- 状态包含:当前下载位置(作品 ID、索引位置、已下载数量)
- 程序重新运行时自动从断点继续,无需手动指定参数

#### 错误恢复行为
- 关键错误(如认证失败、配置错误)终止程序
- Claude 决定权限错误的处理方式
- Claude 决定跳过失败项目时的通知方式

#### JSON 错误输出
- **重要**:本项目面向第三方程序调用,所有错误通过 JSON 格式返回
- JSON 错误响应包含结构化错误对象:错误类型、错误消息、作品 ID、建议操作
- 批量下载部分成功时,返回成功和失败的项目列表,包含错误详情
- 更新 help 命令以反映新的错误处理功能

### Claude's Discretion
- 文件检测的最佳实现方式(文件名匹配 vs 内容验证)
- 权限错误的处理策略(终止 vs 跳过)
- 跳过失败项目时的通知方式(终端显示 vs 静默日志)
- 日志文件的位置和命名约定

### Deferred Ideas (OUT OF SCOPE)
None — discussion stayed within phase scope
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| UX-01 | 程序处理网络错误并提供清晰的错误提示 | Tenacity 重试库 + 指数退避策略 + 结构化 JSON 错误输出 |
| UX-02 | 程序处理权限错误并提供清晰的错误提示 | Python 异常处理最佳实践 + 错误分类 + JSON 错误响应格式 |
| UX-03 | 程序支持增量下载,跳过已下载的内容 | SQLite 数据库记录下载历史 + 文件存在性检查 + 原子操作保证 |
| UX-03 | 程序中断后重新运行能从中断处继续 | JSON 状态文件存储断点 + SQLite 查询已下载内容 + 自动恢复逻辑 |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| tenacity | 8.2+ | 重试机制与指数退避 | Python 最成熟的重试库,支持装饰器模式,与现有代码无缝集成,HIGH confidence (Context7 验证) |
| sqlite3 | stdlib | 下载历史记录数据库 | Python 标准库,无需额外依赖,ACID 事务保证,HIGH confidence (官方文档) |
| pathlib | stdlib | 文件路径操作 | 已在项目中使用,支持跨平台路径操作,HIGH confidence (现有代码) |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| pydantic | 2.0+ | 错误模型验证 | 定义 JSON 错误响应结构,已在项目中使用 |
| structlog | 23.0+ | 结构化日志 | 可选升级,如果需要更复杂的日志上下文管理 |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| tenacity | 自定义 retry 装饰器 | Tenacity 提供 wait_exponential、stop_after_attempt 等成熟策略,避免重复造轮子 |
| sqlite3 | 继续使用 JSON 进度文件 | SQLite 支持复杂查询(按日期、状态过滤)、更好的并发性、更小的文件大小 |
| structlog | 继续使用 logging 模块 | 项目已配置 Rich 日志,升级 structlog 增加复杂度,暂不推荐 |

**Installation:**
```bash
pip install tenacity
# sqlite3 和 pathlib 是 Python 标准库,无需安装
```

## Architecture Patterns

### Recommended Project Structure
```
src/gallery_dl_auo/
├── download/
│   ├── retry_handler.py         # 升级:使用 Tenacity 替换现有逻辑
│   ├── download_tracker.py      # 新增:SQLite 下载历史管理
│   ├── resume_manager.py        # 新增:断点续传状态管理
│   └── atomic_file.py           # 新增:原子文件操作(临时文件+重命名)
├── models/
│   └── error_response.py        # 新增:JSON 错误响应模型
├── utils/
│   ├── error_codes.py           # 已存在:扩展错误码定义
│   └── logging.py               # 升级:添加文件日志处理器
└── cli/
    └── download_cmd.py          # 升级:集成新错误处理系统
```

### Pattern 1: Tenacity 指数退避重试
**What:** 使用装饰器模式包装网络请求,自动重试失败操作
**When to use:** 所有 Pixiv API 调用、文件下载操作
**Example:**
```python
from tenacity import retry, stop_after_attempt, wait_exponential, retry_if_exception_type
from requests.exceptions import RequestException

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=3),
    retry=retry_if_exception_type(RequestException),
    before_sleep=log_retry_attempt
)
def download_with_retry(url: str, output_path: Path) -> dict:
    """带重试的文件下载

    指数退避策略: 1秒 → 2秒 → 3秒
    """
    try:
        response = requests.get(url, timeout=30)
        response.raise_for_status()

        # 原子写入:临时文件+重命名
        temp_path = output_path.with_suffix('.tmp')
        temp_path.write_bytes(response.content)
        temp_path.rename(output_path)

        return {"success": True, "path": str(output_path)}
    except RequestException as e:
        logger.error(f"Download failed: {e}")
        raise  # Tenacity 会捕获并重试
```

### Pattern 2: SQLite 下载历史追踪
**What:** 使用 SQLite 数据库记录每个作品的下载状态,支持复杂查询
**When to use:** 增量下载检查、断点续传、下载历史查询
**Example:**
```python
import sqlite3
from pathlib import Path
from datetime import datetime
from typing import Optional

class DownloadTracker:
    """下载历史追踪器"""

    def __init__(self, db_path: Path):
        self.db_path = db_path
        self._init_database()

    def _init_database(self):
        """初始化数据库表结构"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE TABLE IF NOT EXISTS downloads (
                    illust_id INTEGER PRIMARY KEY,
                    file_path TEXT NOT NULL,
                    mode TEXT NOT NULL,
                    date TEXT NOT NULL,
                    downloaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    file_size INTEGER,
                    checksum TEXT
                )
            """)
            conn.execute("""
                CREATE INDEX IF NOT EXISTS idx_mode_date
                ON downloads(mode, date)
            """)

    def is_downloaded(self, illust_id: int) -> bool:
        """检查作品是否已下载"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "SELECT 1 FROM downloads WHERE illust_id = ?",
                (illust_id,)
            )
            return cursor.fetchone() is not None

    def record_download(
        self,
        illust_id: int,
        file_path: Path,
        mode: str,
        date: str,
        file_size: Optional[int] = None
    ):
        """记录下载完成"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO downloads
                (illust_id, file_path, mode, date, file_size)
                VALUES (?, ?, ?, ?, ?)
            """, (illust_id, str(file_path), mode, date, file_size))

    def get_pending_illusts(self, mode: str, date: str, all_illusts: list[int]) -> list[int]:
        """获取待下载的作品 ID(排除已下载)"""
        with sqlite3.connect(self.db_path) as conn:
            placeholders = ','.join('?' * len(all_illusts))
            cursor = conn.execute(f"""
                SELECT illust_id FROM downloads
                WHERE mode = ? AND date = ? AND illust_id IN ({placeholders})
            """, [mode, date] + all_illusts)

            downloaded = {row[0] for row in cursor.fetchall()}
            return [iid for iid in all_illusts if iid not in downloaded]
```

### Pattern 3: 结构化 JSON 错误响应
**What:** 统一的 JSON 错误格式,包含错误类型、消息、建议操作
**When to use:** 所有 CLI 命令的错误输出(面向第三方程序调用)
**Example:**
```python
from pydantic import BaseModel, Field
from typing import Optional
from enum import Enum

class ErrorSeverity(str, Enum):
    WARNING = "warning"   # 跳过单个项目
    ERROR = "error"       # 操作失败
    CRITICAL = "critical" # 程序终止

class StructuredError(BaseModel):
    """结构化错误模型"""
    error_code: str = Field(..., description="错误码,如 DOWNLOAD_FAILED")
    error_type: str = Field(..., description="错误类型,如 NetworkError")
    message: str = Field(..., description="用户友好的错误消息")
    suggestion: str = Field(..., description="建议的操作步骤")
    severity: ErrorSeverity = Field(..., description="错误严重性")
    illust_id: Optional[int] = Field(None, description="相关作品 ID")
    original_error: Optional[str] = Field(None, description="原始异常信息")
    timestamp: str = Field(default_factory=lambda: datetime.now().isoformat())

    class Config:
        json_encoders = {
            ErrorSeverity: lambda v: v.value
        }

# 使用示例
def download_artwork(illust_id: int) -> dict:
    """下载单个作品"""
    try:
        # 下载逻辑...
        pass
    except PermissionError as e:
        error = StructuredError(
            error_code="FILE_PERMISSION_ERROR",
            error_type="PermissionError",
            message=f"无法写入文件:权限不足",
            suggestion="检查目录权限或以管理员身份运行",
            severity=ErrorSeverity.ERROR,
            illust_id=illust_id,
            original_error=str(e)
        )
        return error.model_dump()
    except requests.Timeout as e:
        error = StructuredError(
            error_code="DOWNLOAD_TIMEOUT",
            error_type="TimeoutError",
            message=f"下载超时:作品 {illust_id}",
            suggestion="检查网络连接或稍后重试",
            severity=ErrorSeverity.WARNING,
            illust_id=illust_id,
            original_error=str(e)
        )
        return error.model_dump()
```

### Pattern 4: 断点续传状态文件
**What:** JSON 文件存储当前下载位置,支持中断后恢复
**When to use:** 大型排行榜下载(月榜 500+ 作品)
**Example:**
```python
from pydantic import BaseModel
from pathlib import Path
import json

class ResumeState(BaseModel):
    """断点续传状态"""
    mode: str
    date: str
    current_index: int = 0
    total_count: int = 0
    downloaded_count: int = 0
    failed_count: int = 0
    last_illust_id: Optional[int] = None

    def save(self, state_file: Path):
        """保存状态到文件"""
        state_file.parent.mkdir(parents=True, exist_ok=True)
        temp_file = state_file.with_suffix('.tmp')

        with open(temp_file, 'w', encoding='utf-8') as f:
            json.dump(self.model_dump(), f, ensure_ascii=False, indent=2)

        # Windows 兼容:先删除再重命名
        if state_file.exists():
            state_file.unlink()
        temp_file.rename(state_file)

    @classmethod
    def load(cls, state_file: Path) -> Optional["ResumeState"]:
        """加载状态"""
        if not state_file.exists():
            return None
        try:
            with open(state_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            return cls(**data)
        except (json.JSONDecodeError, KeyError):
            return None

# 使用示例
def download_ranking_with_resume(mode: str, date: str, output_dir: Path):
    """支持断点续传的排行榜下载"""
    state_file = output_dir / f"{mode}-{date}" / ".resume.json"

    # 尝试加载断点
    state = ResumeState.load(state_file)
    if state:
        logger.info(f"从断点恢复:已下载 {state.downloaded_count}/{state.total_count}")
        start_index = state.current_index
    else:
        # 新下载
        ranking = get_ranking(mode, date)
        state = ResumeState(
            mode=mode,
            date=date,
            total_count=len(ranking.illusts)
        )
        start_index = 0

    # 从断点位置继续下载
    for idx, illust in enumerate(ranking.illusts[start_index:], start=start_index):
        state.current_index = idx
        try:
            download_artwork(illust)
            state.downloaded_count += 1
        except Exception:
            state.failed_count += 1

        # 每下载 10 个作品保存一次状态
        if idx % 10 == 0:
            state.save(state_file)

    # 下载完成,删除状态文件
    if state_file.exists():
        state_file.unlink()
```

### Anti-Patterns to Avoid
- **手动实现重试逻辑:** 项目现有 retry_handler.py 使用简单的 for 循环,应替换为 Tenacity 的成熟策略
- **JSON 进度文件存储大量历史:** progress_manager.py 使用 JSON 存储已下载 ID 列表,大量数据时性能下降,应迁移到 SQLite
- **直接写入目标文件:** 未使用临时文件+重命名,中断后可能留下不完整文件
- **错误信息仅打印到终端:** 第三方程序无法解析,必须使用结构化 JSON 输出

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| 重试逻辑 | 自定义 for 循环 + sleep | tenacity.retry 装饰器 | 成熟的指数退避、停止条件、日志集成,避免边界情况 bug |
| 下载历史存储 | JSON 文件存储 ID 列表 | SQLite 数据库 | 支持索引、复杂查询、事务保证、更好的并发性 |
| 文件原子操作 | 手动 try/except + cleanup | 临时文件 + os.rename() | 操作系统保证原子性,避免竞态条件 |
| 错误分类 | 手动 if/elif 判断异常类型 | Pydantic 模型 + ErrorCode 枚举 | 类型安全、自动验证、JSON 序列化 |

**Key insight:** 错误处理是基础设施代码,应使用成熟库而非自定义实现。Tenacity、SQLite、Pydantic 都是生产验证的解决方案。

## Common Pitfalls

### Pitfall 1: Tenacity 与 Pydantic 冲突
**What goes wrong:** Tenacity 装饰器与 Pydantic 模型方法结合时,可能遇到类型检查错误
**Why it happens:** Tenacity 返回包装函数,可能丢失原始方法的类型提示
**How to avoid:** 使用 `@functools.wraps` 保留元数据,或单独定义重试函数而非装饰方法
**Warning signs:** mypy/pyright 报告类型不匹配

### Pitfall 2: SQLite 并发写入锁
**What goes wrong:** 多线程同时写入 SQLite 时遇到 "database is locked" 错误
**Why it happens:** SQLite 默认序列化写入,长时间事务会阻塞其他操作
**How to avoid:**
1. 使用 WAL 模式:`PRAGMA journal_mode=WAL;`
2. 保持事务短小:立即 commit,不要长时间持有连接
3. 使用超时:`sqlite3.connect(db_path, timeout=30.0)`
**Warning signs:** 间歇性 "database is locked" 错误,特别是批量下载时

### Pitfall 3: Windows 文件重命名失败
**What goes wrong:** `temp_file.rename(target_file)` 在 Windows 上失败,提示文件已存在
**Why it happens:** Windows 不允许 rename() 覆盖已存在文件,Linux/macOS 可以
**How to avoid:**
```python
if target_file.exists():
    target_file.unlink()  # Windows 需要先删除
temp_file.rename(target_file)
```
**Warning signs:** 仅在 Windows 环境出现文件操作错误

### Pitfall 4: JSON 状态文件损坏
**What goes wrong:** 程序崩溃时 JSON 文件可能写入一半,导致下次加载失败
**Why it happens:** JSON 文件不是原子操作,崩溃时可能处于不一致状态
**How to avoid:**
1. 使用临时文件+重命名(与文件下载相同的模式)
2. 加载时使用 try/except 捕获 JSONDecodeError
3. 损坏时重新开始,不要尝试修复
**Warning signs:** `json.JSONDecodeError` 异常,特别是程序异常退出后

### Pitfall 5: 错误消息泄露敏感信息
**What goes wrong:** 错误消息包含 token、API 密钥或文件路径
**Why it happens:** 直接将异常信息传递给用户,未过滤敏感内容
**How to avoid:**
1. 定义用户友好的错误消息模板
2. 仅在 `original_error` 字段包含技术细节(可选)
3. 记录完整错误到日志文件,用户看到的是简化版本
**Warning signs:** 错误消息中出现 `/home/user/...` 路径或 `token=xxx` 参数

## Code Examples

### 网络错误重试(指数退避)
```python
from tenacity import retry, stop_after_attempt, wait_exponential, before_sleep_log
import logging

logger = logging.getLogger("gallery_dl_auo")

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=3),
    before_sleep=before_sleep_log(logger, logging.WARNING)
)
def fetch_ranking_page(api: PixivAPI, mode: str, date: str, offset: int = 0):
    """获取排行榜页面(带重试)

    指数退避: 1秒 → 2秒 → 3秒
    最多重试 3 次
    """
    return api.get_ranking(mode=mode, date=date, offset=offset)
```

### SQLite 数据库初始化与查询
```python
import sqlite3
from pathlib import Path

def init_download_database(db_path: Path):
    """初始化下载数据库

    表结构:
    - downloads: 下载记录主表
    - failures: 失败记录(可选,用于分析)
    """
    db_path.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(db_path) as conn:
        # 下载记录表
        conn.execute("""
            CREATE TABLE IF NOT EXISTS downloads (
                illust_id INTEGER PRIMARY KEY,
                file_path TEXT NOT NULL,
                mode TEXT NOT NULL,
                date TEXT NOT NULL,
                downloaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                file_size INTEGER,
                checksum TEXT
            )
        """)

        # 索引:按排行榜查询
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_mode_date
            ON downloads(mode, date)
        """)

        # 索引:按文件路径查询(检测重复)
        conn.execute("""
            CREATE INDEX IF NOT EXISTS idx_file_path
            ON downloads(file_path)
        """)

        # 失败记录表(可选)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS failures (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                illust_id INTEGER NOT NULL,
                error_code TEXT NOT NULL,
                error_message TEXT,
                failed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                retry_count INTEGER DEFAULT 0
            )
        """)

        # 启用 WAL 模式(提升并发性能)
        conn.execute("PRAGMA journal_mode=WAL")
```

### 权限错误处理(Claude's Discretion:终止 vs 跳过)
```python
from pathlib import Path
from .models.error_response import StructuredError, ErrorSeverity

def ensure_output_directory(output_dir: Path) -> StructuredError | None:
    """确保输出目录可写

    Returns:
        None: 成功
        StructuredError: 权限错误
    """
    try:
        output_dir.mkdir(parents=True, exist_ok=True)

        # 测试写入权限
        test_file = output_dir / ".write_test"
        test_file.write_text("test")
        test_file.unlink()

        return None

    except PermissionError as e:
        return StructuredError(
            error_code="FILE_PERMISSION_ERROR",
            error_type="PermissionError",
            message=f"无法写入目录: {output_dir}",
            suggestion="检查目录权限或选择其他输出位置",
            severity=ErrorSeverity.CRITICAL,  # 关键错误,终止程序
            original_error=str(e)
        )

# 在下载命令中使用
def download_cmd(output_dir: Path, ...):
    # 1. 检查权限(关键错误,立即终止)
    error = ensure_output_directory(output_dir)
    if error:
        print(json.dumps(error.model_dump(), ensure_ascii=False))
        sys.exit(1)

    # 2. 批量下载(单个失败时跳过)
    for illust in ranking.illusts:
        try:
            download_artwork(illust, output_dir)
        except PermissionError as e:
            # 单个文件权限错误:记录并跳过
            error = StructuredError(
                error_code="FILE_PERMISSION_ERROR",
                error_type="PermissionError",
                message=f"无法写入文件: {illust.title}",
                suggestion="检查文件是否被其他程序占用",
                severity=ErrorSeverity.WARNING,  # 警告,跳过继续
                illust_id=illust.id,
                original_error=str(e)
            )
            errors.append(error)
            continue  # 继续下载下一个
```

### 结构化日志记录
```python
import logging
import json
from datetime import datetime
from pathlib import Path

class StructuredFileHandler(logging.Handler):
    """结构化日志处理器:写入 JSON 文件"""

    def __init__(self, log_file: Path):
        super().__init__()
        self.log_file = log_file
        log_file.parent.mkdir(parents=True, exist_ok=True)

    def emit(self, record: logging.LogRecord):
        """写入日志记录"""
        try:
            log_entry = {
                "timestamp": datetime.fromtimestamp(record.created).isoformat(),
                "level": record.levelname,
                "logger": record.name,
                "message": record.getMessage(),
                "module": record.module,
                "function": record.funcName,
                "line": record.lineno,
            }

            # 添加异常信息
            if record.exc_info:
                log_entry["exception"] = self.format(record)

            # 追加写入
            with open(self.log_file, 'a', encoding='utf-8') as f:
                f.write(json.dumps(log_entry, ensure_ascii=False) + '\n')

        except Exception:
            self.handleError(record)

# 配置日志
def setup_logging(log_dir: Path):
    """配置日志系统"""
    logger = logging.getLogger("gallery_dl_auo")
    logger.setLevel(logging.DEBUG)

    # 控制台输出(用户友好)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter("%(levelname)s: %(message)s")
    console_handler.setFormatter(console_formatter)

    # 文件输出(结构化 JSON)
    file_handler = StructuredFileHandler(log_dir / "gallery-dl-auto.log")
    file_handler.setLevel(logging.DEBUG)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| 简单 for 循环重试 | Tenacity 装饰器 + 指数退避 | Phase 7 | 更可靠的重试策略,避免雪崩效应 |
| JSON 进度文件 | SQLite 数据库 | Phase 7 | 支持复杂查询、更好的并发性、更小的存储 |
| 直接写入目标文件 | 临时文件 + 原子重命名 | Phase 7 | 避免中断后留下不完整文件 |
| 文本错误消息 | 结构化 JSON 错误 | Phase 7 | 第三方程序可解析,支持错误聚合 |

**Deprecated/outdated:**
- retry_handler.py 的简单 for 循环:应替换为 Tenacity
- progress_manager.py 的 JSON 文件:应迁移到 SQLite(保留 JSON 作为备份/导入选项)

## Open Questions

1. **日志文件位置**
   - What we know: 用户决策要求记录错误日志到文件
   - What's unclear: 日志文件应存储在哪个目录?(`~/.gallery-dl-auto/logs/` vs `./logs/` vs 输出目录内)
   - Recommendation: 使用 `~/.gallery-dl-auto/logs/` 作为全局日志位置,避免污染下载目录

2. **SQLite 数据库文件位置**
   - What we know: SQLite 数据库应持久化存储
   - What's unclear: 数据库文件应存储在哪里?(`~/.gallery-dl-auto/downloads.db` vs 每个下载目录单独的 `.tracking.db`)
   - Recommendation: 使用 `~/.gallery-dl-auto/downloads.db` 作为全局数据库,支持跨目录查询历史

3. **失败项目通知方式**
   - What we know: 批量下载时部分项目可能失败
   - What's unclear: 是实时打印到终端,还是最后汇总显示?
   - Recommendation: 实时记录到日志文件,终端仅显示进度条,最后汇总成功/失败数量

## Sources

### Primary (HIGH confidence)
- Tenacity 官方文档 (https://tenacity.readthedocs.io/en/latest/) - 重试策略、指数退避配置
- Python sqlite3 文档 (https://docs.python.org/3/library/sqlite3.html) - 数据库操作、事务管理
- Context7 /websites/tenacity_readthedocs_io_en - 指数退避实现模式

### Secondary (MEDIUM confidence)
- WebSearch: "Python SQLite best practices for download tracking database schema 2026" - 数据库设计模式、性能优化
- WebSearch: "Python structured logging with context JSON error handling best practices" - 日志最佳实践

### Tertiary (LOW confidence)
- None - 所有核心发现均通过 HIGH/MEDIUM confidence 源验证

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - Tenacity、SQLite、Pydantic 都是成熟库,官方文档完善
- Architecture: HIGH - 模式参考现有项目结构和最佳实践
- Pitfalls: HIGH - 常见陷阱来自实际开发经验和社区反馈

**Research date:** 2026-02-25
**Valid until:** 2026-03-25 (30 天 - SQLite 和 Tenacity API 稳定)
