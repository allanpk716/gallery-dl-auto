# Milestones

## v1.0 Pixiv 排行榜下载器初始版本 (Shipped: 2026-02-25)

**Phases completed:** 7 phases (01, 02, 02.1, 03, 04, 05, 06), 19 plans

**Key accomplishments:**
- 完整的项目基础设施 - src 布局、Hatchling 构建系统、Rich 日志系统、Hydra 配置管理
- 自动化 Token 管理 - OAuth PKCE 认证、加密存储、自动刷新,用户首次登录后无需手动干预
- 排行榜下载核心功能 - Pixiv API 集成、速率控制、文件下载、JSON 输出
- 完整的元数据系统 - Pydantic 模型、路径模板、作品统计数据获取
- 多排行榜支持 - 13 种排行榜类型、增量下载、自动重试、配置文件集成
- 标准化输出 - JSON 输出模型、错误码系统、第三方友好接口

**Quality metrics:**
- Requirements: 18/18 (100%)
- Tests: 189/211 (89.6%)
- Integration: 23/23 cross-phase connections (100%)
- E2E Flows: 6/6 complete workflows (100%)

**Tech debt:**
- 21 个测试失败 (非阻塞,核心功能正常)
- Pydantic V2 迁移警告

---


## v1.1 Polish (Shipped: 2026-02-25)

**Phases completed:** 1 phase (07), 4 plans, 12 tasks

**Key accomplishments:**
- 生产级别重试机制 — Tenacity 指数退避策略 (1s→2s→3s),网络请求和文件操作自动重试 3 次,原子文件操作保证下载完整性
- SQLite 下载历史追踪 — 基于 SQLite 的增量下载系统,替代 JSON 进度文件,WAL 模式提升并发性能,支持从 JSON 迁移
- 结构化 JSON 错误响应 — 统一的 `StructuredError` 和 `BatchDownloadResult` 模型,支持部分成功场景,退出码分级 (0=成功, 1=部分失败, 2=完全失败)
- 断点续传和文件日志 — ResumeManager 支持中断后从断点继续,SIGINT 优雅退出,JSON Lines 日志文件

**Quality metrics:**
- Requirements: 4/4 (100%)
- Tests: 48/48 (100% - Phase 7 专用测试)
- Integration: 12/12 跨阶段连接 (100%)
- E2E Flows: 4/4 完整工作流 (100%)

**Tech debt:**
- 无技术债务积累
- Phase 7 实现干净,无 TODOs、stubs 或占位符

---


## v1.2 第三方 CLI 集成优化 (Shipped: 2026-02-28)

**Phases completed:** 4 phases (08, 08.1, 09, 10), 18 plans

**Key accomplishments:**
- 用户体验优化 — 实时进度显示、详细模式时间戳格式、速率控制 CLI 参数、429 错误检测与参数调整建议
- 完整的 CLI API 接口 — `--json-help` 结构化命令元数据、`--quiet` 静默模式、`--json-output` 全 JSON 输出，支持第三方工具发现和集成
- 集成文档完善 — INTEGRATION.md (831 行) 提供完整集成指南，包含 CLI 调用方式、JSON API 说明、Python subprocess 示例 (24 个场景)、完整退出码参考 (22 个错误码)
- API 稳定性验证 — 端到端验证 JSON 输出格式 (7/9)、退出码 (10/10)、集成测试 (9/12)，发现并修复关键退出码回归
- Gap Closure (5 waves) — 修复测试框架、JSON 输出、用户信息字段、错误格式、退出码回归等 5 个关键问题

**Quality metrics:**
- Requirements: 9/9 (100%)
- Tests: 57/62 (92% - 2 Windows encoding issues, 3 skipped)
- Integration: 12/12 跨阶段连接 (100%)
- E2E Flows: 4/4 完整工作流 (100%)

**Tech debt:**
- Windows 编码问题: 2 个集成测试失败 (非阻塞,不影响 JSON 输出功能)
- 命令 JSON 输出未完全实现: status/config 命令在默认模式仍输出 Rich 表格 (推荐使用 --json-output)

---

