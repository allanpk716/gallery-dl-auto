# Mode 映射 - 数据流设计

## 1. 数据流概览

### 1.1 Mode 数据流图

```
┌─────────────────────────────────────────────────────────────────┐
│                        完整数据流                                │
└─────────────────────────────────────────────────────────────────┘

用户输入
  │
  │  pixiv-downloader download --type daily --date 2026-03-01
  │
  ▼
┌─────────────────────────────────────────────────────────────────┐
│  CLI Layer (download_cmd.py)                                    │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  @click.option("--type", callback=validate_type_param)   │  │
│  │                                                            │  │
│  │  Input:  type="daily" (CLI mode)                         │  │
│  │  Process: validate_type_param()                          │  │
│  │    └─> ModeManager.validate_cli_mode("daily")            │  │
│  │        - 验证 "daily" 是否有效                            │  │
│  │        - 返回 API mode: "day"                            │  │
│  │  Output: type="day" (API mode)                           │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
  │
  │  mode = "day"  (业务逻辑层统一使用 API mode)
  │
  ▼
┌─────────────────────────────────────────────────────────────────┐
│  Business Logic Layer (download_cmd.py)                         │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  def download(type: str, ...):                           │  │
│  │      mode = type  # mode = "day"                         │  │
│  │                                                            │  │
│  │      # 路由到不同的引擎                                    │  │
│  │      if engine == "gallery-dl":                          │  │
│  │          _download_with_gallery_dl(mode="day", ...)      │  │
│  │      else:                                                │  │
│  │          _download_with_internal(mode="day", ...)        │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘
  │
  ├─────────────────────┬───────────────────────────────────────┐
  │                     │                                        │
  │  mode = "day"       │  mode = "day"                         │
  │                     │                                        │
  ▼                     ▼                                        │
┌──────────────┐  ┌──────────────────────────────────┐         │
│ Pixiv API    │  │  Gallery-dl Wrapper              │         │
│ (internal)   │  │  (gallery-dl engine)             │         │
│              │  │                                  │         │
│ 使用: day    │  │  Input:  mode="day" (API mode)  │         │
│              │  │  Convert:                        │         │
│ client.get_   │  │    ModeManager.api_to_gallery_  │         │
│   ranking(    │  │      dl("day")                  │         │
│     mode=     │  │      - 查找 MODES["day"]        │         │
│     "day"     │  │      - 返回 "daily"             │         │
│   )           │  │  Output: mode="daily"           │         │
│              │  │                                  │         │
│              │  │  Build URL:                      │         │
│              │  │    mode=daily&content=illust     │         │
└──────────────┘  └──────────────────────────────────┘         │
                                                                │
└────────────────────────────────────────────────────────────────┘
```

## 2. 详细流程分析

### 2.1 CLI 参数解析流程

```python
# 步骤 1: Click 解析命令行参数
@click.command()
@click.option("--type", callback=validate_type_param)
def download(type: str):
    # 此时 type 还是原始的用户输入 "daily"
    pass

# 步骤 2: Click 调用验证器
def validate_type_param(ctx, param, value):
    # value = "daily"
    if value is None:
        return None

    # 步骤 3: 调用 ModeManager 验证
    return ModeManager.validate_cli_mode(value)
    # 内部流程:
    #   1. 检查 _cli_to_api_cache (第一次会构建)
    #   2. 查找 cache["daily"]
    #   3. 找到 -> 返回 "day"
    #   4. 未找到 -> 抛出 InvalidModeError

# 步骤 4: 验证器返回 API mode
# type = "day" (已转换)
```

**数据转换**:
```
输入:  "daily" (str, CLI mode)
处理:  ModeManager.validate_cli_mode("daily")
  1. 查找缓存: _cli_to_api_cache["daily"]
  2. 找到映射: "daily" -> "day"
输出:  "day" (str, API mode)
```

### 2.2 业务逻辑层流程

```python
def download(type: str, date: str, engine: str):
    # type = "day" (已经是 API mode)

    # 重命名为 mode (语义更清晰)
    mode = type

    # 根据 engine 路由
    if engine == "gallery-dl":
        return _download_with_gallery_dl(
            mode=mode,  # "day"
            date=date,
            # ...
        )
    else:
        return _download_with_internal(
            mode=mode,  # "day"
            date=date,
            # ...
        )
```

**关键点**:
- 业务逻辑层统一使用 API mode
- mode 值在不同引擎间传递时保持不变

### 2.3 Pixiv API 调用流程 (internal 引擎)

```python
def _download_with_internal(mode: str, date: str):
    # mode = "day"

    client = PixivClient(refresh_token=token)

    # 直接使用 API mode (无需转换)
    ranking_data = client.get_ranking(
        mode=mode,  # "day"
        date=date
    )

    # Pixiv API 期望的格式:
    # {
    #   "mode": "day",
    #   "date": "2026-03-01"
    # }
```

**API 请求示例**:
```http
GET /v1/illust/ranking?mode=day&date=2026-03-01 HTTP/1.1
Host: app-api.pixiv.net
```

### 2.4 Gallery-dl 调用流程 (gallery-dl 引擎)

```python
def _download_with_gallery_dl(mode: str, date: str):
    # mode = "day" (API mode)

    wrapper = GalleryDLWrapper(config=config)

    # Wrapper 内部会转换 mode
    result = wrapper.download_ranking(
        mode=mode,  # "day"
        date=date,
        # ...
    )

    # download_ranking 内部:
    #   url = _build_ranking_url(mode="day", date="2026-03-01")
```

```python
# GalleryDLWrapper._build_ranking_url
def _build_ranking_url(self, mode: str, date: str) -> str:
    # mode = "day" (API mode)

    # 步骤 1: 转换为 gallery-dl mode
    gallery_dl_mode = ModeManager.api_to_gallery_dl(mode)
    # 内部流程:
    #   1. 验证 mode 有效性: validate_api_mode("day")
    #   2. 查找缓存: _api_to_gallery_dl_cache["day"]
    #   3. 找到映射: "day" -> "daily"
    # gallery_dl_mode = "daily"

    # 步骤 2: 构建 URL
    base_url = "https://www.pixiv.net/ranking.php"
    params = f"?mode={gallery_dl_mode}&content=illust"
    if date:
        params += f"&date={date}"

    # 最终 URL:
    # https://www.pixiv.net/ranking.php?mode=daily&content=illust&date=2026-03-01
    return base_url + params
```

**Gallery-dl 命令示例**:
```bash
gallery-dl \
  --config /tmp/config.json \
  --range 1-100 \
  "https://www.pixiv.net/ranking.php?mode=daily&content=illust&date=2026-03-01"
```

## 3. 数据流关键节点

### 3.1 节点清单

| 节点 | 位置 | 输入类型 | 输出类型 | 转换逻辑 |
|------|------|----------|----------|----------|
| 1. CLI 参数 | `download_cmd.py` | CLI mode | CLI mode | 无 (原始输入) |
| 2. 参数验证 | `validators.py` | CLI mode | API mode | `ModeManager.validate_cli_mode()` |
| 3. 业务逻辑 | `download_cmd.py` | API mode | API mode | 无 (直接传递) |
| 4. Pixiv API | `pixiv_client.py` | API mode | API mode | 无 (直接使用) |
| 5. Gallery-dl 转换 | `gallery_dl_wrapper.py` | API mode | Gallery-dl mode | `ModeManager.api_to_gallery_dl()` |
| 6. URL 构建 | `gallery_dl_wrapper.py` | Gallery-dl mode | URL string | 字符串拼接 |

### 3.2 数据流状态跟踪

```python
# 示例: 跟踪 "daily" mode 的完整流程

# 节点 1: 用户输入
user_input = "daily"  # CLI mode

# 节点 2: 参数验证
api_mode = ModeManager.validate_cli_mode(user_input)
# api_mode = "day"

# 节点 3: 业务逻辑
mode = api_mode  # mode = "day"

# 节点 4: Pixiv API (internal 引擎)
client.get_ranking(mode=mode)
# API 调用: mode=day

# 节点 5: Gallery-dl 转换 (gallery-dl 引擎)
gallery_dl_mode = ModeManager.api_to_gallery_dl(mode)
# gallery_dl_mode = "daily"

# 节点 6: URL 构建
url = f"https://www.pixiv.net/ranking.php?mode={gallery_dl_mode}"
# url = "https://www.pixiv.net/ranking.php?mode=daily"
```

## 4. 异常流程

### 4.1 无效 Mode 错误流

```
用户输入: --type invalid_mode
  │
  ▼
validate_type_param()
  │
  ├─> ModeManager.validate_cli_mode("invalid_mode")
  │     │
  │     └─> 查找 _cli_to_api_cache["invalid_mode"]
  │           │
  │           └─> 未找到 -> 抛出 InvalidModeError
  │                   │
  │                   └─> 错误信息:
  │                         "Invalid mode 'invalid_mode'.
  │                          Valid modes: daily, day_female, ..."
  │
  └─> 捕获 InvalidModeError
        │
        └─> 转换为 click.BadParameter
              │
              └─> Click 输出错误信息并退出 (exit code 2)
```

### 4.2 API Mode 验证失败 (内部错误)

```
假设代码 bug 导致传入无效的 API mode
  │
  ▼
ModeManager.api_to_gallery_dl("invalid_api_mode")
  │
  ├─> validate_api_mode("invalid_api_mode")
  │     │
  │     └─> 检查 MODES 字典
  │           │
  │           └─> 未找到 -> 抛出 InvalidModeError
  │
  └─> 错误处理:
        │
        ├─> 记录日志 (ERROR 级别)
        │
        └─> 返回 StructuredError 给用户
              {
                "error_code": "INTERNAL_ERROR",
                "message": "Invalid API mode: invalid_api_mode",
                "suggestion": "This is a bug, please report"
              }
```

## 5. 并发和性能

### 5.1 缓存初始化时机

```python
# 首次访问时延迟初始化缓存

# 第一次调用
api_mode = ModeManager.validate_cli_mode("daily")
# 1. 检查 _cli_to_api_cache -> None
# 2. 调用 _build_cli_to_api_cache()
# 3. 构建缓存: {"daily": "day", "weekly": "week", ...}
# 4. 保存到 _cli_to_api_cache
# 5. 查找并返回 "day"

# 第二次调用
api_mode = ModeManager.validate_cli_mode("weekly")
# 1. 检查 _cli_to_api_cache -> 已存在
# 2. 直接查找并返回 "week"
```

### 5.2 线程安全性

- **只读数据**: MODES 字典在类定义时创建,不会被修改
- **延迟初始化**: 缓存在首次访问时创建,之后只读
- **无状态**: 所有方法都是类方法,无实例状态
- **结论**: 天然线程安全,无需加锁

### 5.3 性能基准

```python
# 单次验证性能
import time

start = time.perf_counter()
for _ in range(10000):
    ModeManager.validate_cli_mode("daily")
end = time.perf_counter()

# 平均耗时: < 0.01ms per call
# 总耗时 (10000次): < 100ms
```

## 6. 数据流验证

### 6.1 端到端测试用例

```python
def test_mode_flow_cli_to_gallery_dl():
    """测试完整的 mode 数据流"""

    # 1. 用户输入 CLI mode
    cli_mode = "daily"

    # 2. CLI 验证转换为 API mode
    api_mode = ModeManager.validate_cli_mode(cli_mode)
    assert api_mode == "day"

    # 3. 业务逻辑使用 API mode
    mode = api_mode

    # 4. Gallery-dl 转换为 gallery-dl mode
    gallery_dl_mode = ModeManager.api_to_gallery_dl(mode)
    assert gallery_dl_mode == "daily"

    # 5. 构建 URL
    url = f"https://www.pixiv.net/ranking.php?mode={gallery_dl_mode}"
    assert "mode=daily" in url

def test_all_modes_flow():
    """测试所有 mode 的完整流程"""

    for cli_mode in ModeManager.get_all_cli_modes():
        # 验证 -> 转换 -> 构建URL 的完整流程
        api_mode = ModeManager.validate_cli_mode(cli_mode)
        gallery_dl_mode = ModeManager.api_to_gallery_dl(api_mode)

        # 构建完整 URL
        url = f"https://www.pixiv.net/ranking.php?mode={gallery_dl_mode}"

        # 验证 URL 格式正确
        assert "mode=" in url
        assert gallery_dl_mode.isalnum() or "_" in gallery_dl_mode
```

## 7. 日志和调试

### 7.1 关键节点日志

```python
# 在 ModeManager 中添加调试日志

import logging
logger = logging.getLogger("gallery_dl_auto")

@classmethod
def validate_cli_mode(cls, cli_mode: str) -> str:
    """验证 CLI mode 并返回 API mode"""
    cache = cls._build_cli_to_api_cache()
    if cli_mode not in cache:
        valid_modes = sorted(cache.keys())
        logger.error(f"Invalid CLI mode: {cli_mode}")
        raise InvalidModeError(cli_mode, valid_modes)

    api_mode = cache[cli_mode]
    logger.debug(f"Mode conversion: CLI '{cli_mode}' -> API '{api_mode}'")
    return api_mode

@classmethod
def api_to_gallery_dl(cls, api_mode: str) -> str:
    """转换: API mode -> Gallery-dl mode"""
    cls.validate_api_mode(api_mode)
    cache = cls._build_api_to_gallery_dl_cache()
    gallery_dl_mode = cache[api_mode]

    logger.debug(
        f"Mode conversion: API '{api_mode}' -> Gallery-dl '{gallery_dl_mode}'"
    )
    return gallery_dl_mode
```

### 7.2 调试模式输出

```bash
# 启用详细日志
pixiv-downloader download --type daily --verbose

# 预期输出:
# [DEBUG] Mode conversion: CLI 'daily' -> API 'day'
# [DEBUG] Mode conversion: API 'day' -> Gallery-dl 'daily'
# [INFO] Executing gallery-dl command: ...
```

## 8. 监控指标

### 8.1 关键指标

```python
# 潜在的监控指标 (未来实现)

class ModeMetrics:
    """Mode 转换监控指标"""

    # 计数器
    cli_mode_usage: dict[str, int] = {}  # 各 mode 使用频率
    conversion_errors: int = 0  # 转换错误次数

    # 性能
    avg_conversion_time_ms: float = 0.0  # 平均转换耗时

    @classmethod
    def record_mode_usage(cls, cli_mode: str):
        """记录 mode 使用情况"""
        cls.cli_mode_usage[cli_mode] = \
            cls.cli_mode_usage.get(cli_mode, 0) + 1

    @classmethod
    def record_conversion_error(cls):
        """记录转换错误"""
        cls.conversion_errors += 1
```

### 8.2 指标示例

```json
{
  "mode_usage": {
    "daily": 1250,
    "weekly": 340,
    "day_male": 89,
    "day_r18": 45
  },
  "conversion_errors": 3,
  "avg_conversion_time_ms": 0.02
}
```

## 9. 未来扩展

### 9.1 Mode 别名支持

```python
# 未来功能: 支持 mode 别名

class ModeManager:
    # 别名映射
    ALIASES = {
        "today": "daily",
        "week": "weekly",
        "d": "daily",
        "w": "weekly",
    }

    @classmethod
    def validate_cli_mode(cls, cli_mode: str) -> str:
        """验证 CLI mode 并返回 API mode (支持别名)"""
        # 先检查别名
        resolved_mode = cls.ALIASES.get(cli_mode, cli_mode)

        # 然后验证
        cache = cls._build_cli_to_api_cache()
        if resolved_mode not in cache:
            raise InvalidModeError(cli_mode, sorted(cache.keys()))

        return cache[resolved_mode]
```

### 9.2 Mode 推荐系统

```python
# 未来功能: 推荐 mode

@classmethod
def recommend_modes(cls, description: str) -> list[str]:
    """根据描述推荐合适的 mode

    Args:
        description: 用户描述 (如 "popular", "new artists")

    Returns:
        推荐的 CLI mode 列表
    """
    keywords = {
        "popular": ["daily", "weekly"],
        "new": ["week_rookie"],
        "original": ["week_original"],
        "manga": ["day_manga"],
    }

    # 简单关键词匹配
    for keyword, modes in keywords.items():
        if keyword in description.lower():
            return modes

    return ["daily"]  # 默认推荐
```

---

**版本历史**:
- 2026-03-01: v1.0 初始设计
