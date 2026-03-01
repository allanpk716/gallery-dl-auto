# Mode 映射修复设计方案

**日期**: 2026-03-01
**问题**: gallery-dl 报错 "Invalid mode 'day_male_r18'"
**解决方案**: 完整的 API mode → gallery-dl mode 映射表

---

## 1. 问题分析

### 1.1 错误现象

```bash
$ pixiv-downloader download --type day_male_r18 --limit 1

错误：
{
  "success": false,
  "failed_errors": [{
    "message": "gallery-dl 执行失败: [pixiv][error] Invalid mode 'day_male_r18'\n"
  }]
}
```

### 1.2 根本原因

通过分析 gallery-dl 源码（`pixiv.py:705-724`），发现：

1. **gallery-dl 使用简写格式的 mode 参数**
   - URL 中应为: `male_r18`（而非 `day_male_r18`）
   - gallery-dl 内部会转换为: `day_male_r18` 传给 Pixiv API

2. **当前代码直接传递 API 格式**
   - `gallery_dl_wrapper.py` 第 218 行: `gallery_dl_mode = api_to_gallery_dl.get(mode, mode)`
   - 导致 `day_male_r18` 直接传给 gallery-dl URL，触发 "Invalid mode" 错误

3. **映射表不完整**
   - 当前只映射了基础 mode（day→daily, week→weekly）
   - R18 排行榜的 mode 没有处理

### 1.3 gallery-dl 的映射规则

从 gallery-dl 源码提取的完整映射表：

| URL mode | API mode | 说明 |
|----------|----------|------|
| `daily` | `day` | 每日排行榜 |
| `daily_r18` | `day_r18` | 每日 R18 |
| `daily_ai` | `day_ai` | 每日 AI |
| `daily_r18_ai` | `day_r18_ai` | 每日 R18 AI |
| `weekly` | `week` | 每周排行榜 |
| `weekly_r18` | `week_r18` | 每周 R18 |
| `monthly` | `month` | 每月排行榜 |
| `male` | `day_male` | 男性热门 |
| `male_r18` | `day_male_r18` | 男性热门 R18 |
| `female` | `day_female` | 女性热门 |
| `female_r18` | `day_female_r18` | 女性热门 R18 |
| `original` | `week_original` | 原创作品 |
| `rookie` | `week_rookie` | 新人作品 |
| `r18g` | `week_r18g` | R18G |

---

## 2. 设计目标

1. ✅ **统一管理**: 创建 `ModeManager` 作为唯一权威来源
2. ✅ **清晰流程**: CLI → API mode → gallery-dl mode，单向转换
3. ✅ **严格验证**: 不支持的模式立即报错
4. ✅ **易于维护**: 添加新 mode 只需修改一处
5. ✅ **向后兼容**: 所有现有 CLI 接口保持不变

---

## 3. 架构设计

### 3.1 整体架构

```
┌─────────────────────────────────────────────┐
│           CLI Layer (用户输入)               │
│  Input: --type daily                       │
│  Validator: validate_type_param()          │
│  Output: API mode (day)                    │
└─────────────┬───────────────────────────────┘
              │ mode = "day"
              ▼
┌─────────────────────────────────────────────┐
│         Business Logic Layer                │
│  ModeManager (NEW)                          │
│  - Central mode registry                    │
│  - Validation functions                     │
│  - Conversion functions                     │
└─────────────┬───────────────────────────────┘
              │ mode = "day"
              ▼
┌─────────────────────────────────────────────┐
│         Integration Layer                   │
│  Gallery-dl Wrapper                         │
│  Convert: day -> daily                      │
│  Build URL: mode=daily                      │
└─────────────────────────────────────────────┘
```

### 3.2 核心组件

#### ModeManager 类

**位置**: `src/gallery_dl_auto/core/mode_manager.py`

```python
from typing import TypedDict

class ModeDefinition(TypedDict):
    """Mode 定义"""
    api_name: str          # Pixiv API 名称
    gallery_dl_name: str   # Gallery-dl URL 参数名称
    description: str       # 描述信息

class ModeManager:
    """统一 Mode 管理器

    作为 mode 映射的唯一权威来源 (Single Source of Truth)
    """

    # Mode 定义注册表 (按 API name 索引)
    MODES: dict[str, ModeDefinition] = {
        # 基础排行榜
        "day": {
            "api_name": "day",
            "gallery_dl_name": "daily",
            "description": "每日排行榜"
        },
        "week": {
            "api_name": "week",
            "gallery_dl_name": "weekly",
            "description": "每周排行榜"
        },
        "month": {
            "api_name": "month",
            "gallery_dl_name": "monthly",
            "description": "每月排行榜"
        },
        # 分类排行榜
        "day_male": {
            "api_name": "day_male",
            "gallery_dl_name": "male",
            "description": "男性热门"
        },
        "day_female": {
            "api_name": "day_female",
            "gallery_dl_name": "female",
            "description": "女性热门"
        },
        "week_original": {
            "api_name": "week_original",
            "gallery_dl_name": "original",
            "description": "原创作品"
        },
        "week_rookie": {
            "api_name": "week_rookie",
            "gallery_dl_name": "rookie",
            "description": "新人作品"
        },
        # R18 排行榜
        "day_r18": {
            "api_name": "day_r18",
            "gallery_dl_name": "daily_r18",
            "description": "每日 R18"
        },
        "day_male_r18": {
            "api_name": "day_male_r18",
            "gallery_dl_name": "male_r18",  # ← 关键修复
            "description": "男性热门 R18"
        },
        "day_female_r18": {
            "api_name": "day_female_r18",
            "gallery_dl_name": "female_r18",
            "description": "女性热门 R18"
        },
        "week_r18": {
            "api_name": "week_r18",
            "gallery_dl_name": "weekly_r18",
            "description": "每周 R18"
        },
        "week_r18g": {
            "api_name": "week_r18g",
            "gallery_dl_name": "r18g",
            "description": "R18G"
        },
    }

    @classmethod
    def api_to_gallery_dl(cls, api_mode: str) -> str:
        """转换 API mode 为 gallery-dl URL mode

        Args:
            api_mode: Pixiv API 格式 (如 "day_male_r18")

        Returns:
            gallery-dl URL 格式 (如 "male_r18")

        Raises:
            InvalidModeError: mode 不在支持列表中
        """
        if api_mode not in cls.MODES:
            valid_modes = list(cls.MODES.keys())
            raise InvalidModeError(api_mode, valid_modes)

        return cls.MODES[api_mode]["gallery_dl_name"]
```

#### 错误类型定义

**位置**: `src/gallery_dl_auto/core/mode_errors.py`

```python
class ModeError(Exception):
    """Mode 相关错误的基类"""
    pass

class InvalidModeError(ModeError):
    """无效的 mode 值"""
    def __init__(self, mode: str, valid_modes: list[str]):
        self.mode = mode
        self.valid_modes = valid_modes
        super().__init__(
            f"Invalid mode '{mode}'. "
            f"Valid modes: {', '.join(sorted(valid_modes))}"
        )
```

---

## 4. 代码修改

### 4.1 修改 gallery_dl_wrapper.py

**位置**: `_build_ranking_url()` 方法

**当前代码** (第 196-227 行):
```python
def _build_ranking_url(self, mode: str, date: Optional[str]) -> str:
    # gallery-dl 期望的 mode 格式与 Pixiv API 不同
    api_to_gallery_dl = {
        "day": "daily",
        "week": "weekly",
        "month": "monthly",
    }
    gallery_dl_mode = api_to_gallery_dl.get(mode, mode)  # ← 问题所在

    base_url = f"https://www.pixiv.net/ranking.php?mode={gallery_dl_mode}&content=illust"
    if date:
        base_url += f"&date={date}"
    return base_url
```

**修改后代码**:
```python
from gallery_dl_auto.core.mode_manager import ModeManager
from gallery_dl_auto.core.mode_errors import InvalidModeError

def _build_ranking_url(self, mode: str, date: Optional[str]) -> str:
    """构建排行榜 URL

    Args:
        mode: 排行榜类型 (Pixiv API format: day, day_male_r18 等)
        date: 日期 (YYYY-MM-DD), None 表示今天

    Returns:
        排行榜 URL
    """
    # 使用 ModeManager 进行转换
    try:
        gallery_dl_mode = ModeManager.api_to_gallery_dl(mode)
    except InvalidModeError as e:
        logger.error(f"gallery-dl 不支持 mode: {mode}")
        logger.info(f"有效的 mode: {', '.join(e.valid_modes)}")
        raise

    # 构建 URL
    base_url = f"https://www.pixiv.net/ranking.php?mode={gallery_dl_mode}&content=illust"
    if date:
        base_url += f"&date={date}"

    logger.debug(f"构建排行榜 URL: mode={gallery_dl_mode}, date={date}")
    return base_url
```

### 4.2 修改 validators.py

**位置**: `validate_type_param()` 函数

**当前代码** (第 49-66 行):
```python
def validate_ranking_type(type_str: str) -> str:
    """验证排行榜类型并返回 API mode 参数"""
    if type_str not in RANKING_MODES:
        valid_types = ", ".join(sorted(RANKING_MODES.keys()))
        raise ValueError(
            f"Invalid ranking type '{type_str}'. Valid types: {valid_types}"
        )
    return RANKING_MODES[type_str]
```

**修改后代码**:
```python
from gallery_dl_auto.core.mode_manager import ModeManager
from gallery_dl_auto.core.mode_errors import InvalidModeError

def validate_ranking_type(type_str: str) -> str:
    """验证排行榜类型并返回 API mode 参数

    Args:
        type_str: 用户输入的排行榜类型

    Returns:
        API mode 参数

    Raises:
        ValueError: 无效的排行榜类型
    """
    try:
        return ModeManager.cli_to_api(type_str)
    except InvalidModeError as e:
        valid_types = ", ".join(sorted(e.valid_modes))
        raise ValueError(
            f"Invalid ranking type '{type_str}'. Valid types: {valid_types}"
        )
```

**移除旧的映射表**:
```python
# 删除第 12-29 行的 RANKING_MODES 字典
# 所有映射逻辑迁移到 ModeManager
```

---

## 5. 错误处理设计

### 5.1 错误场景

| 场景 | 位置 | 处理方式 | 用户体验 |
|------|------|----------|----------|
| CLI 无效 mode | validators.py | 抛出 click.BadParameter | 显示友好的错误提示和有效 mode 列表 |
| API mode 无效 | ModeManager | 抛出 InvalidModeError | 记录日志，返回内部错误 |
| 转换失败 | gallery_dl_wrapper.py | 捕获并记录日志 | 返回详细错误信息 |

### 5.2 示例错误输出

**用户输入无效 mode**:
```bash
$ pixiv-downloader download --type invalid --limit 1

Error: Invalid value for '--type': Invalid ranking type 'invalid'.
Valid types: daily, day_female, day_female_r18, day_male, day_male_r18,
day_r18, month, week_original, week_rookie, week_r18, week_r18g, weekly
```

**成功使用修复后的 mode**:
```bash
$ pixiv-downloader download --type day_male_r18 --limit 1

{
  "success": true,
  "total": 1,
  "downloaded": 1,
  "failed": 0,
  "output_dir": "pixiv-downloads"
}
```

---

## 6. 测试策略

### 6.1 单元测试

**位置**: `tests/core/test_mode_manager.py`

```python
import pytest
from gallery_dl_auto.core.mode_manager import ModeManager
from gallery_dl_auto.core.mode_errors import InvalidModeError

class TestModeManager:

    def test_api_to_gallery_dl_basic_modes(self):
        """测试基础 mode 转换"""
        assert ModeManager.api_to_gallery_dl("day") == "daily"
        assert ModeManager.api_to_gallery_dl("week") == "weekly"
        assert ModeManager.api_to_gallery_dl("month") == "monthly"

    def test_api_to_gallery_dl_r18_modes(self):
        """测试 R18 mode 转换 - 修复的核心"""
        assert ModeManager.api_to_gallery_dl("day_male_r18") == "male_r18"
        assert ModeManager.api_to_gallery_dl("day_female_r18") == "female_r18"
        assert ModeManager.api_to_gallery_dl("day_r18") == "daily_r18"
        assert ModeManager.api_to_gallery_dl("week_r18") == "weekly_r18"
        assert ModeManager.api_to_gallery_dl("week_r18g") == "r18g"

    def test_api_to_gallery_dl_invalid_mode(self):
        """测试无效 mode 抛出异常"""
        with pytest.raises(InvalidModeError) as exc_info:
            ModeManager.api_to_gallery_dl("invalid_mode")

        assert "invalid_mode" in str(exc_info.value)
        assert "day" in exc_info.value.valid_modes
```

### 6.2 集成测试

**位置**: `tests/integration/test_ranking_download.py`

```python
@pytest.mark.integration
def test_download_day_male_r18_with_gallery_dl(tmp_path):
    """测试 day_male_r18 排行榜下载 - 修复验证"""
    result = subprocess.run(
        [
            "pixiv-downloader", "download",
            "--type", "day_male_r18",
            "--limit", "1",
            "--output", str(tmp_path),
            "--dry-run"
        ],
        capture_output=True,
        text=True,
        timeout=60
    )

    # 验证命令成功执行（不再报 Invalid mode 错误）
    assert result.returncode == 0
    assert "Invalid mode" not in result.stderr

    # 验证输出是有效的 JSON
    import json
    output = json.loads(result.stdout)
    assert output["dry_run"] is True
```

### 6.3 手动测试清单

```markdown
## R18 排行榜测试（修复重点）

- [ ] `pixiv-downloader download --type day_male_r18 --limit 1 --dry-run`
- [ ] `pixiv-downloader download --type day_female_r18 --limit 1 --dry-run`
- [ ] `pixiv-downloader download --type day_r18 --limit 1 --dry-run`
- [ ] `pixiv-downloader download --type week_r18 --limit 1 --dry-run`
- [ ] `pixiv-downloader download --type week_r18g --limit 1 --dry-run`

## 错误处理测试

- [ ] 输入无效 mode: `--type invalid` 应显示友好的错误提示
- [ ] 验证所有 mode 都能正常工作
```

---

## 7. 实施计划

### 阶段 1: 核心实现（1-2 小时）

1. 创建 `src/gallery_dl_auto/core/` 目录
2. 创建 `mode_errors.py` - 错误类型定义
3. 创建 `mode_manager.py` - ModeManager 类
4. 实现 MODES 映射表
5. 实现转换方法

### 阶段 2: 重构现有代码（1 小时）

1. 修改 `gallery_dl_wrapper.py` 使用 ModeManager
2. 修改 `validators.py` 使用 ModeManager
3. 删除旧的映射表（RANKING_MODES）
4. 添加错误处理和日志

### 阶段 3: 测试验证（1-2 小时）

1. 编写单元测试
2. 运行集成测试
3. 执行手动测试清单
4. 验证所有 R18 mode 都能工作

### 阶段 4: 文档和提交（30 分钟）

1. 更新 CLI 帮助文档
2. 提交代码
3. 编写 commit message

**总预估时间: 4-5 小时**

---

## 8. 验收标准

### 8.1 功能验收

- [ ] `pixiv-downloader download --type day_male_r18 --limit 1` 成功执行
- [ ] 所有 R18 排行榜都能正常下载
- [ ] 无效的 mode 显示友好的错误提示
- [ ] 所有现有的 CLI 命令保持向后兼容

### 8.2 质量验收

- [ ] 单元测试覆盖率 > 95%
- [ ] 集成测试通过
- [ ] 代码符合项目规范
- [ ] 文档完整清晰

### 8.3 性能验收

- [ ] Mode 转换延迟 < 1ms
- [ ] 无内存泄漏
- [ ] 启动时间无明显增加

---

## 9. 参考资料

- Gallery-dl Pixiv Extractor 源码: `gallery_dl/extractor/pixiv.py:705-724`
- Pixiv API 文档: https://pixivpy.readthedocs.io/
- Gallery-dl 文档: https://github.com/mikf/gallery-dl

---

**版本历史**:
- 2026-03-01: v1.0 初始设计
