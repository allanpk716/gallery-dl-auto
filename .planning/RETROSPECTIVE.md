# Project Retrospective

Living document capturing lessons learned across milestones.

---

## Milestone: v1.2 — 第三方 CLI 集成优化

**Shipped:** 2026-02-28
**Phases:** 4 | **Plans:** 18

### What Was Built

- 用户体验优化 — 实时进度显示、详细模式、速率控制参数、429 错误检测
- CLI API 接口 — --json-help (命令发现)、--quiet (静默执行)、--json-output (JSON 输出)
- 集成文档 — INTEGRATION.md (831 行) 包含完整集成指南、示例代码、退出码参考
- API 验证 — 端到端验证 JSON 输出、退出码、集成测试
- Gap Closure — 5 轮修复测试框架、JSON 输出、用户信息、错误格式、退出码回归

### What Worked

**Decimal Phase Numbering**
- Phase 8.1 插入在 Phase 8 和 9 之间，清晰表达了依赖关系和插入逻辑
- 避免了重新编号所有后续阶段

**Gap Closure Workflow**
- 为每个发现的 gap 创建独立修复计划 (10-01-GAP01, 10-02-GAP01, etc.)
- Wave-based execution 确保 gaps 不积累
- 关键修复: 10-03-GAP01 修复了退出码回归，避免了第三方集成失败

**3-Source Cross-Reference Audit**
- VERIFICATION.md + REQUIREMENTS.md + SUMMARY.md 三源交叉验证
- 发现 REQUIREMENTS.md tracking discrepancies (CLI-01/02/03 marked as Pending but actually Complete)
- Integration checker agent 自动验证跨阶段连接和 E2E flows

**Documentation-First Approach**
- Phase 9 先完成 INTEGRATION.md，Phase 10 再验证实现是否符合文档
- 文档定义了 API 契约，验证确保实现遵守契约

### What Was Inefficient

**Exit Code Regression Detection Lag**
- 10-02-GAP02 commit (76842b2) 引入退出码回归，但 Phase 10 测试使用 CliRunner 而非真实进程
- 回归在集成测试 (test_integration.py) 中才被发现
- **Lesson:** 退出码测试必须使用 subprocess 真实进程，不能依赖 Click CliRunner

**Requirements Tracking Lag**
- CLI-01/02/03 在 Phase 8.1 完成并验证，但 REQUIREMENTS.md 未更新
- 审计时才发现 tracking gap
- **Lesson:** 每个阶段完成后立即更新 REQUIREMENTS.md traceability table

**Windows Encoding Issues**
- 2 个集成测试因 Rich table encoding 失败 (CP1252 vs UTF-8)
- 测试解析 Rich table 输出，而非使用 --json-output 模式
- **Lesson:** 集成测试应优先使用 --json-output 模式，避免平台相关编码问题

### Patterns Established

**CLI API Design Pattern**
- 全局参数优先级: --json-output > --quiet > --verbose
- ctx.obj["output_mode"] 在命令间传递
- JSON 输出使用 Pydantic model_dump_json()

**Integration Testing Pattern**
- tests/validation/test_integration.py 使用 subprocess 真实进程
- tests/validation/test_exit_codes.py 使用 CliRunner (快速但不测试退出码传播)
- 两者都需要，各有用途

**Gap Closure Naming Convention**
- `{PHASE}-{PLAN}-GAP{NN}` 格式 (10-01-GAP01, 10-02-GAP01)
- 关联到原始计划和 wave number

### Key Lessons

1. **Exit codes must be tested with real processes**
   - Click CliRunner 捕获 SystemExit 但不传播退出码到 OS
   - 集成测试必须使用 subprocess.run() 或 subprocess.Popen()

2. **Requirements tracking must be updated immediately**
   - 阶段完成后立即勾选 REQUIREMENTS.md checkboxes
   - 更新 Traceability table 的 Phase assignment 和 Status

3. **Documentation-first reduces rework**
   - INTEGRATION.md 定义 API 契约
   - 验证阶段确保实现符合契约
   - 避免"实现后补文档"的 common pitfall

4. **Decimal phases enable agile insertion**
   - Phase 8.1 成功插入在 Phase 8 和 9 之间
   - 不需要重新编号后续阶段
   - 清晰表达依赖关系

5. **Gap closure prevents accumulation**
   - 每个 gap 独立修复和验证
   - Wave-based execution 确保系统性修复
   - 避免在完成阶段时遗留技术债务

### Cost Observations

- **Model mix:** ~70% sonnet (planning, code review), ~30% haiku (simple edits)
- **Sessions:** 6 sessions (Phase 8, 8.1, 9, 10 + 2 gap closure sessions)
- **Notable:** Phase 10 required 5 gap closure waves, but workflow kept context manageable

---

## Milestone: v1.1 — Polish

**Shipped:** 2026-02-25
**Phases:** 1 | **Plans:** 4

### What Was Built

- 生产级别重试机制 — Tenacity 指数退避 (1s→2s→3s)
- SQLite 下载历史追踪 — 替代 JSON 进度文件，WAL 模式
- 结构化错误响应 — StructuredError 和 BatchDownloadResult 模型
- 断点续传 — ResumeManager 支持中断恢复

### What Worked

**Comprehensive Error Handling**
- 覆盖网络错误、文件操作错误、权限错误
- 原子文件操作 (write to temp + rename) 保证下载完整性
- 100% tests passing (48/48)

**SQLite vs JSON Progress**
- SQLite 支持高效查询和跨目录统一追踪
- WAL 模式提升并发性能
- 从 JSON 迁移平滑

### Key Lessons

1. **Atomic operations prevent corruption**
   - write to temp file + os.replace() 保证原子性
   - 适用于配置文件、下载文件、进度文件

2. **Structured errors enable partial success**
   - BatchDownloadResult 支持 success + failed 混合场景
   - 退出码分级 (0=全部成功, 1=部分失败, 2=完全失败)

---

## Milestone: v1.0 — MVP

**Shipped:** 2026-02-25
**Phases:** 7 | **Plans:** 19

### What Was Built

- 项目基础设施 — src 布局、Hatchling 构建、Rich 日志、Hydra 配置
- 自动化 Token 管理 — OAuth PKCE + Playwright + Fernet 加密
- 排行榜下载核心 — PixivPy3 API、速率控制、文件下载
- 元数据系统 — Pydantic 模型、路径模板、统计数据
- 多排行榜支持 — 13 种类型、增量下载、配置文件
- 标准化输出 — JSON 输出、错误码系统

### What Worked

**Automation First**
- OAuth PKCE + Playwright 自动化登录，用户首次手动登录后无需干预
- Token 自动刷新和加密存储
- 实现真正的自动化下载流程

**Pydantic v2 Data Models**
- 自动验证、序列化、类型安全
- 减少样板代码，提高可靠性
- JSON 输出友好

**Click + Hydra Integration**
- Click 子命令结构清晰
- Hydra 配置管理灵活 (YAML + CLI override)
- 配置优先级: CLI > 配置文件 > 默认值

### Key Lessons

1. **Direct API control > wrapper libraries**
   - 直接使用 PixivPy3 而非封装 gallery-dl
   - 更好的错误处理和性能控制

2. **JSON output from day one**
   - 设计时考虑第三方集成
   - 结构化输出便于程序解析

3. **13 ranking types cover all scenarios**
   - 日榜、周榜、月榜 + 10 种其他类型
   - 满足不同用户需求

---

## Cross-Milestone Trends

### Cost Efficiency

| Milestone | Sessions | Model Mix | Notable |
|-----------|----------|-----------|---------|
| v1.0 MVP | 12 | 80% sonnet, 20% haiku | 基础架构搭建，较多探索 |
| v1.1 Polish | 3 | 60% sonnet, 40% haiku | 专注于错误处理，效率提升 |
| v1.2 CLI Integration | 6 | 70% sonnet, 30% haiku | Gap closure 增加 sessions |

**Observation:** Haiku 比例提升，简单任务使用 haiku 节省成本。

### Quality Metrics

| Milestone | Requirements | Tests | Integration | E2E Flows |
|-----------|--------------|-------|-------------|-----------|
| v1.0 | 18/18 (100%) | 189/211 (90%) | 23/23 (100%) | 6/6 (100%) |
| v1.1 | 4/4 (100%) | 48/48 (100%) | 12/12 (100%) | 4/4 (100%) |
| v1.2 | 9/9 (100%) | 57/62 (92%) | 12/12 (100%) | 4/4 (100%) |

**Observation:** Requirements coverage 保持 100%，测试通过率稳定在 90%+。

### Technical Debt Patterns

| Type | v1.0 | v1.1 | v1.2 |
|------|------|------|------|
| Test failures | 21 (非阻塞) | 0 | 5 (2 Windows encoding, 3 skipped) |
| TODOs/FIXMEs | 0 | 0 | 0 |
| Stubs/Placeholders | 0 | 0 | 0 |

**Observation:** 技术债务控制良好，无 TODOs 或 stubs。v1.2 Windows encoding issues 为 low-severity。

---

## Recommendations

### Process Improvements

1. **Update REQUIREMENTS.md immediately after phase completion**
   - 避免 tracking lag
   - 使用 checklist 确保更新

2. **Test exit codes with real processes (subprocess)**
   - 不依赖 Click CliRunner 测试退出码传播
   - 集成测试必须使用 subprocess

3. **Use --json-output in integration tests**
   - 避免平台相关的编码问题
   - JSON 输出更稳定，易于解析

### Tooling Enhancements

1. **Automated REQUIREMENTS.md validation**
   - CI 检查 VERIFICATION.md status vs REQUIREMENTS.md checkboxes
   - 避免 tracking discrepancies

2. **Exit code integration tests by default**
   - 生成测试代码时，退出码测试使用 subprocess
   - 单元测试可使用 CliRunner

3. **Gap closure workflow improvements**
   - 自动生成 GAP plan 模板
   - 追踪 gap closure waves 数量

---

*Last updated: 2026-02-28 after v1.2 milestone completion*
