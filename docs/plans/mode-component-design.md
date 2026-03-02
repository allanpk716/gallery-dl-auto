# Mode 映射 - 组件设计和接口规范

## 1. 模块概览

### 1.1 模块职责划分

```
┌────────────────────────────────────────────────────────────┐
│                     组件层次结构                            │
├────────────────────────────────────────────────────────────┤
│ Layer 1: CLI Layer (用户交互)                              │
│   └─ validators.py: 参数验证和初步转换                     │
├────────────────────────────────────────────────────────────┤
│ Layer 2: Core Layer (核心逻辑)                             │
│   └─ mode_manager.py: 统一 mode 管理 (NEW)                 │
├────────────────────────────────────────────────────────────┤
│ Layer 3: Business Layer (业务逻辑)                         │
│   └─ download_cmd.py: 下载命令编排                         │
├────────────────────────────────────────────────────────────┤
│ Layer 4: Integration Layer (集成层)                        │
│   ├─ pixiv_client.py: Pixiv API 客户端                     │
│   └─ gallery_dl_wrapper.py: Gallery-dl 封装                │
└────────────────────────────────────────────────────────────┘
```

## 2. 核心组件设计

### 2.1 ModeManager (新增)

**位置**: `src/gallery_dl_auto/core/mode_manager.py`

**职责**:
- 作为 mode 定义的唯一权威来源 (Single Source of Truth)
- 提供 mode 验证功能
- 提供 mode 转换功能
- 生成文档和帮助信息

**接口规范**:

```python
from typing import Literal, TypedDict, Optional
from enum import Enum

class ModeType(Enum):
    """Mode 类型枚举"""
    CLI = "cli"           # 用户输入
    API = "api"           # Pixiv API
    GALLERY_DL = "gallery_dl"  # Gallery-dl

class ModeDefinition(TypedDict):
    """Mode 完整定义"""
    cli_name: str          # CLI 用户输入名称
    api_name: str          # Pixiv API 名称
    gallery_dl_name: str   # Gallery-dl 名称
    description: str       # 中文描述
    category: str          # 分类: normal, category, r18

class ModeManager:
    """统一 Mode 管理器

    作为 mode 映射的唯一权威来源，提供验证和转换功能。
    所有方法都是类方法，无需实例化。

    使用示例:
        >>> ModeManager.validate_cli_mode("daily")
        'day'
        >>> ModeManager.api_to_gallery_dl("day")
        'daily'
        >>> ModeManager.get_all_cli_modes()
        ['daily', 'weekly', 'monthly', ...]
    """

    # Mode 定义注册表 (按 API name 索引)
    MODES: dict[str, ModeDefinition] = {
        # 常规排行榜
        "day": {
            "cli_name": "daily",
            "api_name": "day",
            "gallery_dl_name": "daily",
            "description": "每日排行榜",
            "category": "normal"
        },
        "week": {
            "cli_name": "weekly",
            "api_name": "week",
            "gallery_dl_name": "weekly",
            "description": "每周排行榜",
            "category": "normal"
        },
        "month": {
            "cli_name": "monthly",
            "api_name": "month",
            "gallery_dl_name": "monthly",
            "description": "每月排行榜",
            "category": "normal"
        },

        # 分类排行榜
        "day_male": {
            "cli_name": "day_male",
            "api_name": "day_male",
            "gallery_dl_name": "day_male",
            "description": "男性喜爱排行榜",
            "category": "category"
        },
        "day_female": {
            "cli_name": "day_female",
            "api_name": "day_female",
            "gallery_dl_name": "day_female",
            "description": "女性喜爱排行榜",
            "category": "category"
        },
        "week_original": {
            "cli_name": "week_original",
            "api_name": "week_original",
            "gallery_dl_name": "week_original",
            "description": "原创排行榜",
            "category": "category"
        },
        "week_rookie": {
            "cli_name": "week_rookie",
            "api_name": "week_rookie",
            "gallery_dl_name": "week_rookie",
            "description": "新人排行榜",
            "category": "category"
        },
        "day_manga": {
            "cli_name": "day_manga",
            "api_name": "day_manga",
            "gallery_dl_name": "day_manga",
            "description": "漫画排行榜",
            "category": "category"
        },

        # R18 排行榜
        "day_r18": {
            "cli_name": "day_r18",
            "api_name": "day_r18",
            "gallery_dl_name": "day_r18",
            "description": "R18 每日排行榜",
            "category": "r18"
        },
        "day_male_r18": {
            "cli_name": "day_male_r18",
            "api_name": "day_male_r18",
            "gallery_dl_name": "day_male_r18",
            "description": "R18 男性喜爱排行榜",
            "category": "r18"
        },
        "day_female_r18": {
            "cli_name": "day_female_r18",
            "api_name": "day_female_r18",
            "gallery_dl_name": "day_female_r18",
            "description": "R18 女性喜爱排行榜",
            "category": "r18"
        },
        "week_r18": {
            "cli_name": "week_r18",
            "api_name": "week_r18",
            "gallery_dl_name": "week_r18",
            "description": "R18 每周排行榜",
            "category": "r18"
        },
        "week_r18g": {
            "cli_name": "week_r18g",
            "api_name": "week_r18g",
            "gallery_dl_name": "week_r18g",
            "description": "R18G 每周排行榜",
            "category": "r18"
        },
    }

    # 反向索引缓存 (延迟初始化)
    _cli_to_api_cache: Optional[dict[str, str]] = None
    _api_to_gallery_dl_cache: Optional[dict[str, str]] = None

    @classmethod
    def _build_cli_to_api_cache(cls) -> dict[str, str]:
        """构建 CLI -> API 反向索引"""
        if cls._cli_to_api_cache is None:
            cls._cli_to_api_cache = {
                defn["cli_name"]: api_name
                for api_name, defn in cls.MODES.items()
            }
        return cls._cli_to_api_cache

    @classmethod
    def _build_api_to_gallery_dl_cache(cls) -> dict[str, str]:
        """构建 API -> Gallery-dl 索引"""
        if cls._api_to_gallery_dl_cache is None:
            cls._api_to_gallery_dl_cache = {
                api_name: defn["gallery_dl_name"]
                for api_name, defn in cls.MODES.items()
            }
        return cls._api_to_gallery_dl_cache

    @classmethod
    def validate_cli_mode(cls, cli_mode: str) -> str:
        """验证 CLI mode 并返回 API mode

        Args:
            cli_mode: CLI 用户输入的 mode 名称

        Returns:
            str: 对应的 API mode 名称

        Raises:
            InvalidModeError: 当 mode 无效时

        Example:
            >>> ModeManager.validate_cli_mode("daily")
            'day'
            >>> ModeManager.validate_cli_mode("invalid")
            InvalidModeError: Invalid mode 'invalid'. Valid modes: daily, weekly, ...
        """
        cache = cls._build_cli_to_api_cache()
        if cli_mode not in cache:
            valid_modes = sorted(cache.keys())
            raise InvalidModeError(cli_mode, valid_modes)
        return cache[cli_mode]

    @classmethod
    def validate_api_mode(cls, api_mode: str) -> str:
        """验证 API mode 的有效性

        Args:
            api_mode: Pixiv API mode 名称

        Returns:
            str: 验证通过的 API mode (原样返回)

        Raises:
            InvalidModeError: 当 mode 无效时

        Example:
            >>> ModeManager.validate_api_mode("day")
            'day'
        """
        if api_mode not in cls.MODES:
            valid_modes = sorted(cls.MODES.keys())
            raise InvalidModeError(api_mode, valid_modes)
        return api_mode

    @classmethod
    def cli_to_api(cls, cli_mode: str) -> str:
        """转换: CLI mode -> API mode

        validate_cli_mode 的别名，语义更清晰
        """
        return cls.validate_cli_mode(cli_mode)

    @classmethod
    def api_to_gallery_dl(cls, api_mode: str) -> str:
        """转换: API mode -> Gallery-dl mode

        Args:
            api_mode: Pixiv API mode 名称

        Returns:
            str: 对应的 Gallery-dl mode 名称

        Raises:
            InvalidModeError: 当 mode 无效时

        Example:
            >>> ModeManager.api_to_gallery_dl("day")
            'daily'
            >>> ModeManager.api_to_gallery_dl("day_male")
            'day_male'
        """
        cls.validate_api_mode(api_mode)  # 先验证
        cache = cls._build_api_to_gallery_dl_cache()
        return cache[api_mode]

    @classmethod
    def get_all_cli_modes(cls) -> list[str]:
        """获取所有有效的 CLI mode 名称

        Returns:
            list[str]: 排序后的 CLI mode 列表

        Example:
            >>> ModeManager.get_all_cli_modes()
            ['daily', 'day_female', 'day_female_r18', ...]
        """
        cache = cls._build_cli_to_api_cache()
        return sorted(cache.keys())

    @classmethod
    def get_all_api_modes(cls) -> list[str]:
        """获取所有有效的 API mode 名称

        Returns:
            list[str]: 排序后的 API mode 列表
        """
        return sorted(cls.MODES.keys())

    @classmethod
    def get_mode_definition(cls, api_mode: str) -> ModeDefinition:
        """获取 mode 的完整定义

        Args:
            api_mode: API mode 名称

        Returns:
            ModeDefinition: mode 的完整定义

        Raises:
            InvalidModeError: 当 mode 无效时
        """
        cls.validate_api_mode(api_mode)
        return cls.MODES[api_mode]

    @classmethod
    def get_modes_by_category(cls, category: str) -> list[str]:
        """按分类获取 CLI mode 列表

        Args:
            category: 分类名称 (normal, category, r18)

        Returns:
            list[str]: 该分类的 CLI mode 列表

        Example:
            >>> ModeManager.get_modes_by_category("r18")
            ['day_female_r18', 'day_male_r18', 'day_r18', ...]
        """
        return sorted([
            defn["cli_name"]
            for defn in cls.MODES.values()
            if defn["category"] == category
        ])

    @classmethod
    def get_help_text(cls) -> str:
        """生成 CLI 帮助文本

        Returns:
            str: 格式化的帮助文本

        Example:
            >>> print(ModeManager.get_help_text())
            Ranking Types:
              Normal:
                - daily: 每日排行榜
                - weekly: 每周排行榜
                ...
              Category:
                - day_male: 男性喜爱排行榜
                ...
              R18:
                - day_r18: R18 每日排行榜
                ...
        """
        lines = ["Ranking Types:"]

        for category, category_name in [
            ("normal", "Normal"),
            ("category", "Category"),
            ("r18", "R18")
        ]:
            lines.append(f"  {category_name}:")
            modes = cls.get_modes_by_category(category)
            for cli_mode in modes:
                api_mode = cls._build_cli_to_api_cache()[cli_mode]
                defn = cls.MODES[api_mode]
                lines.append(f"    - {cli_mode}: {defn['description']}")

        return "\n".join(lines)


class InvalidModeError(Exception):
    """无效的 Mode 错误"""

    def __init__(self, mode: str, valid_modes: list[str]):
        self.mode = mode
        self.valid_modes = valid_modes
        super().__init__(
            f"Invalid mode '{mode}'. Valid modes: {', '.join(valid_modes)}"
        )
```

### 2.2 validators.py (修改)

**位置**: `src/gallery_dl_auto/cli/validators.py`

**修改要点**:
- 移除 `RANKING_MODES` 映射表
- 使用 `ModeManager` 进行验证和转换

**新接口**:

```python
from gallery_dl_auto.core.mode_manager import ModeManager, InvalidModeError

def validate_ranking_type(type_str: str) -> str:
    """验证排行榜类型并返回 API mode 参数

    Args:
        type_str: 用户输入的排行榜类型 (CLI mode)

    Returns:
        API mode 参数 (day, week, month 等)

    Raises:
        ValueError: 无效的排行榜类型
    """
    try:
        return ModeManager.validate_cli_mode(type_str)
    except InvalidModeError as e:
        valid_types = ", ".join(e.valid_modes)
        raise ValueError(
            f"Invalid ranking type '{type_str}'. Valid types: {valid_types}"
        ) from e

def validate_type_param(ctx, param, value: str | None) -> str | None:
    """Click 参数验证器: 排行榜类型

    Args:
        ctx: Click 上下文
        param: 参数对象
        value: 用户输入值

    Returns:
        验证后的 API mode 参数,或 None

    Raises:
        click.BadParameter: 无效的排行榜类型
    """
    if value is None:
        return None
    try:
        return validate_ranking_type(value)
    except ValueError as e:
        raise click.BadParameter(str(e))

# 移除 RANKING_MODES 和 RankingType (由 ModeManager 管理)
```

### 2.3 gallery_dl_wrapper.py (修改)

**位置**: `src/gallery_dl_auto/integration/gallery_dl_wrapper.py`

**修改要点**:
- 移除 `api_to_gallery_dl` 局部映射表
- 使用 `ModeManager.api_to_gallery_dl()` 进行转换

**修改的方法**:

```python
from gallery_dl_auto.core.mode_manager import ModeManager

def _build_ranking_url(self, mode: str, date: Optional[str]) -> str:
    """构建排行榜 URL

    Args:
        mode: 排行榜类型 (Pixiv API format: day, week, day_male_r18 等)
        date: 日期 (YYYY-MM-DD), None 表示今天

    Returns:
        str: 排行榜 URL
    """
    # 使用 ModeManager 转换: API mode -> Gallery-dl mode
    gallery_dl_mode = ModeManager.api_to_gallery_dl(mode)

    # gallery-dl 支持的排行榜 URL 格式
    base_url = f"https://www.pixiv.net/ranking.php?mode={gallery_dl_mode}&content=illust"

    if date:
        base_url += f"&date={date}"

    return base_url

# 移除 api_to_gallery_dl 局部变量
```

### 2.4 download_cmd.py (保持)

**位置**: `src/gallery_dl_auto/cli/download_cmd.py`

**无需修改**: 继续使用 API mode (由 validators 返回)

## 3. 接口依赖关系

```
┌─────────────────────────────────────────────────────────┐
│                   依赖关系图                             │
├─────────────────────────────────────────────────────────┤
│                                                          │
│  download_cmd.py                                         │
│       │                                                  │
│       ├─ imports ──> validators.py                       │
│       │                  │                               │
│       │                  └─ imports ──> ModeManager     │
│       │                                                  │
│       ├─ calls ───> PixivClient.get_ranking(mode)      │
│       │              (uses API mode)                     │
│       │                                                  │
│       └─ calls ───> GalleryDLWrapper.download_ranking  │
│                      (uses API mode)                     │
│                          │                               │
│                          └─ imports ──> ModeManager     │
│                                                          │
└─────────────────────────────────────────────────────────┘
```

## 4. 类型定义

### 4.1 类型别名

```python
# 在 mode_manager.py 中定义
from typing import Literal

# API Mode 类型 (用于类型检查)
APIMode = Literal[
    "day", "week", "month",
    "day_male", "day_female", "week_original", "week_rookie", "day_manga",
    "day_r18", "day_male_r18", "day_female_r18", "week_r18", "week_r18g"
]

# CLI Mode 类型
CLIMode = Literal[
    "daily", "weekly", "monthly",
    "day_male", "day_female", "week_original", "week_rookie", "day_manga",
    "day_r18", "day_male_r18", "day_female_r18", "week_r18", "week_r18g"
]

# Gallery-dl Mode 类型
GalleryDLMode = Literal[
    "daily", "weekly", "monthly",
    "day_male", "day_female", "week_original", "week_rookie", "day_manga",
    "day_r18", "day_male_r18", "day_female_r18", "week_r18", "week_r18g"
]
```

### 4.2 类型使用示例

```python
from gallery_dl_auto.core.mode_manager import ModeManager, APIMode

def get_ranking(mode: APIMode) -> list[dict]:
    """获取排行榜 (类型安全)

    Args:
        mode: API mode (类型检查器会验证)

    Returns:
        作品列表
    """
    # ModeManager 验证确保 mode 有效
    validated_mode = ModeManager.validate_api_mode(mode)
    # ...
```

## 5. 配置和扩展

### 5.1 环境变量

```bash
# 启用 mode 转换调试日志
export GALLERY_DL_AUTO_DEBUG_MODE=true
```

### 5.2 配置文件 (未来扩展)

```yaml
# config/mode_mappings.yaml (未来功能)
version: 1
overrides:
  # 自定义 mode 映射
  day:
    cli_name: "today"  # 允许用户自定义 CLI 名称
```

## 6. 性能考虑

### 6.1 缓存策略

- **反向索引缓存**: 延迟初始化,只计算一次
- **验证缓存**: 不缓存验证结果 (避免状态问题)
- **内存占用**: 三个缓存字典,每个约 13 个键值对 (< 1KB)

### 6.2 性能基准

```
操作                    目标延迟
────────────────────────────────
validate_cli_mode      < 0.1ms
api_to_gallery_dl      < 0.1ms
get_all_cli_modes      < 0.05ms
get_help_text          < 1ms (首次)
                       < 0.1ms (后续可缓存)
```

## 7. 测试接口

### 7.1 单元测试示例

```python
# tests/core/test_mode_manager.py

def test_validate_cli_mode_valid():
    """测试有效的 CLI mode"""
    assert ModeManager.validate_cli_mode("daily") == "day"
    assert ModeManager.validate_cli_mode("weekly") == "week"

def test_validate_cli_mode_invalid():
    """测试无效的 CLI mode"""
    with pytest.raises(InvalidModeError) as exc_info:
        ModeManager.validate_cli_mode("invalid")

    assert "invalid" in str(exc_info.value)
    assert "daily" in str(exc_info.value)

def test_api_to_gallery_dl():
    """测试 API -> Gallery-dl 转换"""
    assert ModeManager.api_to_gallery_dl("day") == "daily"
    assert ModeManager.api_to_gallery_dl("day_male") == "day_male"

def test_all_modes_count():
    """测试 mode 总数"""
    assert len(ModeManager.get_all_cli_modes()) == 13
    assert len(ModeManager.get_all_api_modes()) == 13
```

## 8. 迁移指南

### 8.1 从旧代码迁移

**旧代码 (validators.py)**:
```python
# 旧方式
RANKING_MODES = {
    "daily": "day",
    "weekly": "week",
    # ...
}
result = RANKING_MODES.get(type_str)
```

**新代码**:
```python
# 新方式
from gallery_dl_auto.core.mode_manager import ModeManager

result = ModeManager.validate_cli_mode(type_str)
```

**旧代码 (gallery_dl_wrapper.py)**:
```python
# 旧方式
api_to_gallery_dl = {
    "day": "daily",
    "week": "weekly",
}
gallery_dl_mode = api_to_gallery_dl.get(mode, mode)
```

**新代码**:
```python
# 新方式
from gallery_dl_auto.core.mode_manager import ModeManager

gallery_dl_mode = ModeManager.api_to_gallery_dl(mode)
```

### 8.2 兼容性保证

- ✅ CLI 接口保持不变 (所有现有命令继续工作)
- ✅ API mode 格式保持不变
- ✅ 错误消息格式保持不变
- ✅ 测试用例保持不变

---

**版本历史**:
- 2026-03-01: v1.0 初始设计
