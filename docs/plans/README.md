# Mode 映射和验证 - 设计总览

## 文档导航

本目录包含 gallery-dl-auto 项目 mode 映射和验证的完整设计文档。

### 设计文档

1. **[架构设计](./mode-mapping-architecture.md)**
   - 背景和问题分析
   - 整体架构设计
   - 核心组件概览
   - 实施计划和风险分析

2. **[组件设计](./mode-component-design.md)**
   - 各模块的职责和接口
   - ModeManager 类设计
   - validators.py 修改方案
   - gallery_dl_wrapper.py 修改方案

3. **[数据流设计](./mode-dataflow-design.md)**
   - 完整的数据流图
   - 关键节点分析
   - 异常流程处理
   - 性能和并发考虑

4. **[错误处理设计](./mode-error-handling-design.md)**
   - 错误场景分析
   - 自定义异常类
   - 错误处理策略
   - 错误消息设计

5. **[测试策略设计](./mode-testing-strategy.md)**
   - 单元测试设计
   - 集成测试设计
   - 端到端测试设计
   - 性能和边界条件测试

## 快速开始

### 问题背景

当前项目存在 mode 映射问题:

```
CLI (daily) → API (day) → Gallery-dl (daily)
         ↓              ↓
    validators.py   gallery_dl_wrapper.py
    (映射表1)        (映射表2)
```

**问题**:
- 双重映射容易出错
- 映射逻辑分散
- 难以维护和扩展

### 解决方案

创建统一的 ModeManager:

```
CLI (daily) → ModeManager → API (day) → ModeManager → Gallery-dl (daily)
              (单一来源)               (统一转换)
```

### 核心设计

**ModeManager 类**:
- 单一的 mode 映射权威来源
- 提供验证和转换功能
- 所有方法都是类方法,无需实例化

**数据流**:
```
用户输入 --type daily
  ↓
validate_type_param() 调用 ModeManager.validate_cli_mode("daily")
  ↓ 返回 "day"
业务逻辑层使用 mode = "day"
  ↓
GalleryDLWrapper 调用 ModeManager.api_to_gallery_dl("day")
  ↓ 返回 "daily"
构建 URL: mode=daily
```

## 实施计划

### 阶段 1: 核心实现 (1-2 天)

- [ ] 创建 `src/gallery_dl_auto/core/mode_manager.py`
- [ ] 实现 ModeManager 类
- [ ] 创建 `src/gallery_dl_auto/core/mode_errors.py`
- [ ] 编写单元测试

### 阶段 2: 重构现有代码 (1-2 天)

- [ ] 修改 `validators.py` 使用 ModeManager
- [ ] 修改 `gallery_dl_wrapper.py` 使用 ModeManager
- [ ] 运行所有测试确保向后兼容

### 阶段 3: 测试和验证 (1 天)

- [ ] 编写集成测试
- [ ] 编写端到端测试
- [ ] 性能测试
- [ ] 边界条件测试

### 阶段 4: 文档和部署 (1 天)

- [ ] 更新用户文档
- [ ] 更新开发者文档
- [ ] 代码审查
- [ ] 合并到主分支

## 验收标准

### 功能验收

- [ ] 所有现有的 CLI 命令正常工作
- [ ] 所有 mode 转换正确
- [ ] 错误消息清晰有用
- [ ] 添加新 mode 只需修改一处

### 质量验收

- [ ] 单元测试覆盖率 > 95%
- [ ] 集成测试覆盖所有 mode
- [ ] 代码符合项目规范
- [ ] 文档完整清晰

### 性能验收

- [ ] Mode 转换延迟 < 1ms
- [ ] 无内存泄漏
- [ ] 启动时间无明显增加

## 文件清单

### 新增文件

```
src/gallery_dl_auto/core/
├── __init__.py
├── mode_manager.py      # Mode 管理器
└── mode_errors.py       # Mode 错误类

tests/core/
├── test_mode_manager.py # ModeManager 单元测试
└── test_mode_errors.py  # 错误类单元测试

tests/integration/
└── test_mode_flow.py    # 集成测试

tests/e2e/
└── test_mode_e2e.py     # 端到端测试

tests/performance/
└── test_mode_performance.py  # 性能测试

tests/edge_cases/
└── test_mode_edge_cases.py   # 边界条件测试
```

### 修改文件

```
src/gallery_dl_auto/cli/validators.py
src/gallery_dl_auto/integration/gallery_dl_wrapper.py
```

## 关键设计决策

### 决策 1: 使用类方法而非实例方法

**理由**:
- Mode 数据是全局共享的配置
- 避免不必要的实例化开销
- 简化使用方式

### 决策 2: 按索引构建反向缓存

**理由**:
- 避免每次转换都遍历 MODES 字典
- 延迟初始化,首次访问时构建
- 线程安全 (只读数据)

### 决策 3: 区分用户错误和系统错误

**理由**:
- 用户错误: 提供友好的提示和建议
- 系统错误: 记录详细日志,返回通用错误

### 决策 4: 使用 TypedDict 定义 Mode 结构

**理由**:
- 类型安全,IDE 自动补全
- 清晰的文档作用
- 便于未来扩展

## 风险和缓解

| 风险 | 缓解措施 |
|------|---------|
| 向后兼容性破坏 | 保持所有 CLI 接口不变,运行完整测试套件 |
| 性能下降 | 使用缓存,避免重复计算,性能测试验证 |
| 维护成本增加 | 集中管理减少重复代码,完整测试覆盖 |
| 迁移困难 | 提供详细的迁移指南,分阶段实施 |

## 未来扩展

### 短期 (1-2 个月)

- [ ] 支持更多 Pixiv 排行榜类型
- [ ] 添加 mode 别名支持 (如 "today" -> "daily")
- [ ] 改进错误消息的本地化

### 长期 (3-6 个月)

- [ ] 支持自定义 mode 映射配置文件
- [ ] 添加 mode 推荐功能
- [ ] 集成到 Web UI
- [ ] 监控和分析 mode 使用情况

## 参考资源

### 内部文档

- [Pixiv API 文档](https://pixivpy.readthedocs.io/)
- [Gallery-dl 文档](https://github.com/mikf/gallery-dl)
- [Click 框架文档](https://click.palletsprojects.com/)

### 相关代码

- 现有映射表: `src/gallery_dl_auto/cli/validators.py` (RANKING_MODES)
- Gallery-dl 映射: `src/gallery_dl_auto/integration/gallery_dl_wrapper.py`
- 测试用例: `tests/cli/test_validators.py`

## 更新日志

- **2026-03-01**: v1.0 - 初始设计完成
  - 完成架构设计
  - 完成组件设计
  - 完成数据流设计
  - 完成错误处理设计
  - 完成测试策略设计

---

**维护者**: gallery-dl-auto 开发团队
**创建日期**: 2026-03-01
**最后更新**: 2026-03-01
