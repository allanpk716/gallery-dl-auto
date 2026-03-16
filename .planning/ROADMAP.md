# Roadmap: gallery-dl-auto

## Milestones

- ✅ **v1.0 Pixiv 排行榜下载器初始版本** - Phases 1-6 (shipped 2026-02-25)
- ✅ **v1.1 Polish** - Phase 7 (shipped 2026-02-25)
- ✅ **v1.2 第三方 CLI 集成优化** - Phases 8-10 (shipped 2026-02-28)
- 🔄 **v1.3 Bug 修复与验证** - Phase 11 (in progress)

## Phases

**Phase Numbering:**
- Integer phases (1-7): v1.0 和 v1.1 已完成阶段
- Integer phases (8-10): v1.2 已完成阶段
- Integer phases (11+): v1.3 及后续里程碑

<details>
<summary>✅ v1.0 Pixiv 排行榜下载器初始版本 (Phases 1-6) - SHIPPED 2026-02-25</summary>

### Phase 1: 项目基础设施
**Goal**: 建立项目基础结构和开发环境
**Plans**: 3 plans

Plans:
- [x] 01-01: 项目初始化和依赖管理
- [x] 01-02: 代码质量工具配置
- [x] 01-03: 测试框架搭建

### Phase 2: 认证系统
**Goal**: 实现自动化 Pixiv OAuth 认证和 token 管理
**Plans**: 4 plans

Plans:
- [x] 02-01: OAuth PKCE 认证实现
- [x] 02-02: Token 加密存储
- [x] 02-03: Token 自动刷新
- [x] 02-04: 认证命令集成

### Phase 2.1: 认证修复 (INSERTED)
**Goal**: 修复认证系统的关键问题
**Plans**: 1 plan

Plans:
- [x] 02.1-01: 修复 token 加密和登录流程

### Phase 3: 排行榜下载核心
**Goal**: 实现排行榜数据获取和下载功能
**Plans**: 3 plans

Plans:
- [x] 03-01: Pixiv API 集成
- [x] 03-02: 文件下载器
- [x] 03-03: 下载命令集成

### Phase 4: 元数据系统
**Goal**: 实现作品元数据获取和管理
**Plans**: 2 plans

Plans:
- [x] 04-01: Pydantic 数据模型
- [x] 04-02: 元数据获取和存储

### Phase 5: 多排行榜支持
**Goal**: 支持多种排行榜类型和配置
**Plans**: 3 plans

Plans:
- [x] 05-01: 排行榜类型枚举
- [x] 05-02: 配置文件集成
- [x] 05-03: 批量下载支持

### Phase 6: 输出标准化
**Goal**: 实现标准化 JSON 输出和错误处理
**Plans**: 3 plans

Plans:
- [x] 06-01: JSON 输出模型
- [x] 06-02: 错误码系统
- [x] 06-03: 命令输出集成

</details>

<details>
<summary>✅ v1.1 Polish (Phase 7) - SHIPPED 2026-02-25</summary>

### Phase 7: 生产级别错误处理
**Goal**: 增强错误处理和用户体验,达到生产就绪状态
**Plans**: 4 plans

Plans:
- [x] 07-01: Tenacity 重试机制
- [x] 07-02: SQLite 下载历史追踪
- [x] 07-03: 结构化错误响应
- [x] 07-04: 断点续传和文件日志

</details>

<details>
<summary>✅ v1.2 第三方 CLI 集成优化 (Phases 8-10) - SHIPPED 2026-02-28</summary>

### Phase 8: 用户体验优化
**Goal**: 优化 CLI 用户体验,提供详细模式和速率控制配置
**Depends on**: Phase 7 (生产级别错误处理基础)
**Plans**: 2 plans

Plans:
- [x] 08-01: 详细模式和进度显示
- [x] 08-02: 日志模式配置和 429 错误处理

### Phase 8.1: CLI API 增强
**Goal**: 提供完整的第三方 CLI 集成 API 接口
**Depends on**: Phase 8 (用户体验优化基础)
**Plans**: 3 plans

Plans:
- [x] 08.1-01: JSON 帮助系统 — 实现 --json-help 全局参数和结构化命令元数据
- [x] 08.1-02: 静默和 JSON 输出模式 — 实现 --quiet 和 --json-output 全局参数
- [x] 08.1-03: 集成验证 — 端到端测试验证所有命令的 CLI API 行为

### Phase 9: 集成文档
**Goal**: 为第三方开发者提供完整的集成指南和参考文档
**Depends on**: Phase 8.1 (CLI API 接口就绪)
**Plans**: 3 plans

Plans:
- [x] 09-01: INTEGRATION.md 文档编写
- [x] 09-02: 调用示例代码
- [x] 09-03: 退出码文档

### Phase 10: API 验证
**Goal**: 验证所有 CLI 输出的一致性和可靠性,确保第三方集成的稳定性
**Depends on**: Phase 9 (文档完成,验证标准明确)
**Plans**: 10 plans (包括 5 gap closure plans)

Plans:
- [x] 10-01: JSON 输出格式验证
- [x] 10-02: 退出码验证
- [x] 10-03: 集成测试
- [x] 10-01-GAP01: 修复测试框架导入路径
- [x] 10-01-GAP02: 实现 status/config JSON 输出
- [x] 10-02-GAP01: 修复 status username 字段
- [x] 10-02-GAP02: 实现 JSON 错误格式
- [x] 10-03-GAP01: 修复退出码回归

</details>

<details>
<summary>🔄 v1.3 Bug 修复与验证 (Phase 11) - IN PROGRESS</summary>

### Phase 11: Bug Fix & Verification
**Goal**: 程序能够正确记录下载历史并实现跨日去重
**Depends on**: Phase 10 (v1.2 CLI 集成优化已完成)
**Requirements**: BUG-01, VERI-01
**Success Criteria**:
1. 用户首次下载排行榜后，tracker DB 包含所有下载作品的记录
2. 用户第二次下载相同排行榜时，程序跳过已下载作品（从 DB 读取）
3. 用户下载不同日期的排行榜时，程序正确识别新作品（跨日去重）
4. GitHub issue #1 和 #2 被关闭（验证完成）

**Plans**: 2 plans

Plans:
- [ ] 11-01: 修复 tracker DB 记录逻辑 (BUG-01) — 修改 Phase 4 条件判断 + 添加边界测试用例
- [ ] 11-02: 验证跨日去重功能 (VERI-01) — 验证 cross-day-dedup.md 验收标准 + 关闭 GitHub issues

</details>

## Progress

| Phase | Milestone | Plans Complete | Status | Completed |
|-------|-----------|----------------|--------|-----------|
| 1. 项目基础设施 | v1.0 | 3/3 | Complete | 2026-02-25 |
| 2. 认证系统 | v1.0 | 4/4 | Complete | 2026-02-25 |
| 2.1. 认证修复 | v1.0 | 1/1 | Complete | 2026-02-25 |
| 3. 排行榜下载核心 | v1.0 | 3/3 | Complete | 2026-02-25 |
| 4. 元数据系统 | v1.0 | 2/2 | Complete | 2026-02-25 |
| 5. 多排行榜支持 | v1.0 | 3/3 | Complete | 2026-02-25 |
| 6. 输出标准化 | v1.0 | 3/3 | Complete | 2026-02-25 |
| 7. 生产级别错误处理 | v1.1 | 4/4 | Complete | 2026-02-25 |
| 8. 用户体验优化 | v1.2 | 2/2 | Complete | 2026-02-25 |
| 8.1. CLI API 增强 | v1.2 | 3/3 | Complete | 2026-02-26 |
| 9. 集成文档 | v1.2 | 3/3 | Complete | 2026-02-26 |
| 10. API 验证 | v1.2 | 10/10 | Complete | 2026-02-28 |
| 11. Bug Fix & Verification | 2/2 | Complete   | 2026-03-16 | - |

---

## Coverage Validation

**v1.3 Requirements Coverage:**

| Requirement | Phase | Status |
|-------------|-------|--------|
| BUG-01 | Phase 11 (Plan 11-01) | Pending |
| VERI-01 | Phase 11 (Plan 11-02) | Pending |

**Coverage:** 2/2 (100%) ✓

---

*Roadmap created: 2026-02-25*
*Last updated: 2026-03-16 for Phase 11 planning*
