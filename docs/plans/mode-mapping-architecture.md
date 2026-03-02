# Mode 映射和验证架构设计

## 1. 背景和问题分析

### 1.1 当前状态

gallery-dl-auto 项目在三个不同的层次使用不同的 mode 命名规范:

1. **CLI 层 (用户输入)**: 使用用户友好的名称
   - `daily`, `weekly`, `monthly`
   - `day_male`, `day_female`, `week_original`, etc.

2. **API 层 (Pixiv API)**: 使用 API 规范的名称
   - `day`, `week`, `month`
   - `day_male`, `day_female`, `week_original`, etc.

3. **Gallery-dl 层**: 使用 gallery-dl 规范的名称
   - `daily`, `weekly`, `monthly`
   - `day_male`, `day_female`, `week_original`, etc.

### 1.2 发现的问题

1. **双重映射问题**:
   - CLI → API: `daily` → `day` (在 validators.py)
   - API → Gallery-dl: `day` → `daily` (在 gallery_dl_wrapper.py)
   - 这种双重转换容易出错且难以维护

2. **映射逻辑分散**:
   - `validators.py`: 定义 RANKING_MODES 映射表
   - `gallery_dl_wrapper.py`: 定义 api_to_gallery_dl 反向映射
   - 映射逻辑在两处,容易不同步

3. **缺乏统一验证**:
   - CLI 层验证用户输入
   - API 层和 Gallery-dl 层没有验证 mode 的有效性
   - 可能传入无效的 mode 值

4. **文档不一致**:
   - 帮助文档中同时出现两种命名
   - 用户可能混淆 API mode 和 CLI type

### 1.3 设计目标

1. **统一 mode 管理**: 建立单一的 mode 映射权威来源
2. **清晰的转换路径**: 明确定义 mode 在各层之间的转换
3. **强类型验证**: 在边界处验证 mode 的有效性
4. **易于维护**: 添加新 mode 时只需修改一处
5. **向后兼容**: 不破坏现有的 CLI 接口

## 2. 架构设计

### 2.1 整体架构

```
┌─────────────────────────────────────────────────────────────┐
│                        CLI Layer                             │
│  Input: --type daily (user-friendly name)                   │
│  Validator: validate_type_param()                           │
│  Output: API mode (day)                                     │
└─────────────────────┬───────────────────────────────────────┘
                      │ mode = "day"
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                     Business Logic Layer                     │
│  Unified Mode Manager (NEW)                                 │
│  - Central mode registry                                    │
│  - Validation functions                                     │
│  - Conversion functions                                     │
└─────────────────────┬───────────────────────────────────────┘
                      │ mode = "day"
                      ▼
┌─────────────────────────────────────────────────────────────┐
│                   Integration Layer                          │
│  ┌──────────────────┐      ┌──────────────────────────┐   │
│  │   Pixiv API      │      │    Gallery-dl Wrapper    │   │
│  │  (uses: day)     │      │  (needs: daily)          │   │
│  │                  │      │  Convert: day -> daily   │   │
│  └──────────────────┘      └──────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

### 2.2 核心组件设计

#### 2.2.1 统一 Mode 管理器 (新增)

创建新模块 `src/gallery_dl_auto/core/mode_manager.py`:

```python
from typing import Literal, TypedDict

class ModeDefinition(TypedDict):
    """Mode 定义"""
    cli_name: str          # CLI 用户输入名称
    api_name: str          # Pixiv API 名称
    gallery_dl_name: str   # Gallery-dl 名称
    description: str       # 描述信息

class ModeManager:
    """统一 Mode 管理器

    作为 mode 映射的唯一权威来源 (Single Source of Truth)
    """

    # Mode 定义注册表 (按 API name 索引)
    MODES: dict[str, ModeDefinition] = {
        # 常规排行榜
        "day": {
            "cli_name": "daily",
            "api_name": "day",
            "gallery_dl_name": "daily",
            "description": "每日排行榜"
        },
        "week": {
            "cli_name": "weekly",
            "api_name": "week",
            "gallery_dl_name": "weekly",
            "description": "每周排行榜"
        },
        "month": {
            "cli_name": "monthly",
            "api_name": "month",
            "gallery_dl_name": "monthly",
            "description": "每月排行榜"
        },
        # ... 其他 mode
    }

    @classmethod
    def validate_cli_mode(cls, cli_mode: str) -> str:
        """验证 CLI mode 并返回 API mode"""
        pass

    @classmethod
    def validate_api_mode(cls, api_mode: str) -> str:
        """验证 API mode 的有效性"""
        pass

    @classmethod
    def cli_to_api(cls, cli_mode: str) -> str:
        """转换: CLI mode -> API mode"""
        pass

    @classmethod
    def api_to_gallery_dl(cls, api_mode: str) -> str:
        """转换: API mode -> Gallery-dl mode"""
        pass

    @classmethod
    def get_all_cli_modes(cls) -> list[str]:
        """获取所有有效的 CLI mode 名称"""
        pass
```

#### 2.2.2 重构现有组件

**validators.py (修改)**
- 移除 RANKING_MODES 映射表
- 调用 ModeManager 进行验证和转换

**gallery_dl_wrapper.py (修改)**
- 移除 api_to_gallery_dl 映射表
- 调用 ModeManager.api_to_gallery_dl()

**pixiv_client.py (保持)**
- 继续使用 API mode 名称
- 无需修改

### 2.3 数据流设计

#### 2.3.1 标准流程

```
用户输入 (CLI)
  --type daily
      │
      ▼
  validate_type_param()
      │ 调用 ModeManager.validate_cli_mode("daily")
      │ 返回 API mode: "day"
      ▼
  mode = "day" (传递到业务逻辑层)
      │
      ├─────> Pixiv API (使用 "day")
      │         client.get_ranking(mode="day")
      │
      └─────> Gallery-dl Wrapper
                │ 调用 ModeManager.api_to_gallery_dl("day")
                │ 返回 gallery-dl mode: "daily"
                ▼
              构建 URL: mode=daily
```

#### 2.3.2 验证检查点

1. **CLI 入口**: 验证用户输入是有效的 CLI mode
2. **业务逻辑层**: 确保使用 API mode
3. **Gallery-dl 层**: 转换为 gallery-dl mode

### 2.4 错误处理设计

#### 2.4.1 错误类型

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
            f"Invalid mode '{mode}'. Valid modes: {', '.join(valid_modes)}"
        )

class ModeConversionError(ModeError):
    """Mode 转换失败"""
    def __init__(self, source_mode: str, target_type: str):
        self.source_mode = source_mode
        self.target_type = target_type
        super().__init__(
            f"Cannot convert mode '{source_mode}' to {target_type}"
        )
```

#### 2.4.2 错误处理策略

| 错误场景 | 处理策略 | 用户提示 |
|---------|---------|---------|
| CLI 无效 mode | 抛出 click.BadParameter | "Invalid ranking type 'xxx'. Valid types: daily, weekly, ..." |
| API mode 无效 | 抛出 InvalidModeError | 记录日志,返回内部错误 |
| 转换失败 | 抛出 ModeConversionError | 记录日志,返回内部错误 |

### 2.5 扩展性设计

#### 2.5.1 添加新 Mode

只需在 `ModeManager.MODES` 中添加新条目:

```python
"new_mode": {
    "cli_name": "new_mode_cli",
    "api_name": "new_mode",
    "gallery_dl_name": "new_mode_gdl",
    "description": "新的排行榜类型"
}
```

所有转换和验证逻辑自动生效。

#### 2.5.2 支持自定义 Mode 映射

可通过配置文件覆盖默认映射 (未来扩展):

```yaml
# config/mode_overrides.yaml
mode_mappings:
  day:
    cli_name: "today"  # 自定义 CLI 名称
```

## 3. 实施计划

### 3.1 阶段 1: 核心实现 (优先级: 高)

1. 创建 `src/gallery_dl_auto/core/mode_manager.py`
2. 实现 ModeManager 类和所有 mode 定义
3. 编写单元测试

### 3.2 阶段 2: 重构现有代码 (优先级: 高)

1. 修改 `validators.py` 使用 ModeManager
2. 修改 `gallery_dl_wrapper.py` 使用 ModeManager
3. 运行所有测试确保向后兼容

### 3.3 阶段 3: 增强和优化 (优先级: 中)

1. 添加更详细的错误消息
2. 添加 mode 相关的文档生成
3. 性能优化 (缓存常用转换)

### 3.4 阶段 4: 测试和验证 (优先级: 高)

1. 单元测试覆盖所有 mode 转换
2. 集成测试验证端到端流程
3. 手动测试 CLI 命令

## 4. 风险和缓解措施

### 4.1 向后兼容性风险

**风险**: 重构可能破坏现有行为

**缓解措施**:
- 保持所有现有的 CLI 接口不变
- 运行完整的测试套件
- 使用特性开关逐步迁移

### 4.2 性能风险

**风险**: 增加一层抽象可能影响性能

**缓解措施**:
- Mode 转换是轻量级操作
- 使用类方法避免实例化开销
- 缓存常用转换结果

### 4.3 维护风险

**风险**: 新增代码增加维护成本

**缓解措施**:
- 集中管理减少重复代码
- 清晰的文档和注释
- 完整的测试覆盖

## 5. 验收标准

### 5.1 功能验收

- [ ] 所有现有的 CLI 命令正常工作
- [ ] 所有 mode 转换正确
- [ ] 错误消息清晰有用
- [ ] 添加新 mode 只需修改一处

### 5.2 质量验收

- [ ] 单元测试覆盖率 > 95%
- [ ] 集成测试覆盖所有 mode
- [ ] 代码符合项目规范
- [ ] 文档完整清晰

### 5.3 性能验收

- [ ] Mode 转换延迟 < 1ms
- [ ] 无内存泄漏
- [ ] 启动时间无明显增加

## 6. 未来扩展

### 6.1 短期 (1-2 个月)

- 支持更多 Pixiv 排行榜类型
- 添加 mode 别名支持
- 改进错误消息的本地化

### 6.2 长期 (3-6 个月)

- 支持自定义 mode 映射配置
- 添加 mode 推荐功能
- 集成到 Web UI

## 7. 参考文档

- [Pixiv API 文档](https://pixivpy.readthedocs.io/)
- [Gallery-dl 文档](https://github.com/mikf/gallery-dl)
- [Click 框架文档](https://click.palletsprojects.com/)

---

**版本历史**:
- 2026-03-01: v1.0 初始设计
