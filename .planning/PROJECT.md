# Pixiv 排行榜下载器 (gallery-dl-auto)

## What This Is

一个 Python CLI 工具,用于自动化管理 Pixiv 认证并下载排行榜内容。实现了完全自动化的 refresh token 管理(首次登录后无需手动干预)和多排行榜支持(日榜、周榜、月榜等 13 种类型)。提供完整的 CLI API 接口(`--json-help`, `--quiet`, `--json-output`)便于第三方工具集成,支持结构化 JSON 输出和标准化退出码。

该工具支持作为终端工具直接使用,也可以被第三方程序通过 subprocess 调用,适用于自动化采集 Pixiv 排行榜内容的场景。

## Core Value

**自动化获取 Pixiv refresh token 并下载排行榜内容** — 用户首次手动登录后,程序自动捕获、存储和更新 refresh token,无需手动从浏览器开发者工具中复制,实现真正的自动化下载流程。

## Current Milestone: v1.3 Bug 修复与验证

**Goal:** 修复 GitHub issue #2（去重功能失效 bug），验证 issue #1（跨日去重功能）是否完整实现

**Target features:**
- 修复 tracker DB 记录逻辑，确保下载结果正确写入数据库
- 验证跨日去重功能完整可用
- 确保增量下载功能正常工作

## Requirements

### Validated

**v1.0 Core Features:**
- ✓ 用户能够通过自动化流程获取 Pixiv 的 refresh token (首次需手动登录) — v1.0
- ✓ 程序自动保存和管理 refresh token,支持自动更新 — v1.0
- ✓ 用户能够下载 Pixiv 排行榜 (每日/每周/每月及 10 种其他类型) — v1.0
- ✓ 程序下载排行榜中的图片文件 — v1.0
- ✓ 程序获取作品的元数据(标题、作者、标签等)和统计数据(收藏数、浏览量等) — v1.0
- ✓ 程序以 JSON 格式返回下载结果、详细信息、路径和错误信息 — v1.0
- ✓ 工具支持在终端直接使用和被其他程序调用 — v1.0

**v1.1 Production Polish:**
- ✓ 程序处理网络错误和权限错误并提供清晰的错误提示 — v1.1
- ✓ 程序支持增量下载,跳过已下载的内容 (SQLite DownloadTracker) — v1.1
- ✓ 程序中断后重新运行能从中断处继续 (ResumeManager) — v1.1

**v1.2 CLI Integration:**
- ✓ 用户可以通过 --json-help 获取结构化命令元数据 (8 个命令,包含参数和描述) — v1.2
- ✓ 用户可以通过 --quiet 获得静默执行 (仅输出最终结果,无进度/日志) — v1.2
- ✓ 用户可以通过 --json-output 确保所有输出可被 JSON 解析器解析 (包括错误信息) — v1.2
- ✓ 开发者可以查阅 INTEGRATION.md 了解如何集成 (调用方式、参数说明、最佳实践) — v1.2
- ✓ 开发者可以参考 Python 和命令行调用示例代码 — v1.2
- ✓ 开发者可以根据完整退出码文档 (22 个错误码) 判断执行状态 — v1.2
- ✓ CLI API 稳定性经过验证 (JSON 输出、退出码、集成测试) — v1.2

### Active

(Ready for v1.3+)

- [ ] 程序实时显示下载进度 (Phase 8 已实现,可增强)
- [ ] 程序控制下载速率以避免触发 Pixiv 反爬虫机制 (Phase 8 已实现基础版本)
- [ ] 用户能够配置请求间隔和并发数 (Phase 8 已实现 CLI 参数覆盖)

### Out of Scope

- **GUI 界面** — 专注于 CLI + JSON 输出,让用户构建自己的 UI — ✓ 理由依然有效
- **批量账号管理** — 单账号设计 — ✓ 理由依然有效
- **自动上传/分享** — 专注于下载 — ✓ 理由依然有效
- **图片格式转换/编辑** — 保持原图质量 — ✓ 理由依然有效
- **下载非排行榜内容** — 专注排行榜场景 — ✓ 理由依然有效 (搜索结果、用户作品集等)
- **代理/VPN 集成** — 用户自行配置 — ✓ 理由依然有效 (让用户自行配置系统代理环境变量)
- **gallery-dl 封装** — v1.0 改为直接使用 PixivPy3 — ⚠️ 策略已改变,不再封装 gallery-dl

## Context

**Shipped v1.0** (2026-02-25) with:
- **2925 lines of Python code** in src/
- **Tech stack:** Python 3.8+, Click (CLI), Hydra (配置), Pydantic v2 (数据模型), PixivPy3 (Pixiv API), Rich (日志/输出)
- **189/211 tests passing** (89.6%) — 核心功能通过测试验证
- **100% requirements coverage** — 18/18 v1 requirements satisfied
- **完整实现:** 自动化 Token 管理、排行榜下载、元数据获取、JSON 输出、多排行榜支持

**Shipped v1.1** (2026-02-25) with:
- **3732 lines of Python code** in src/ (+807 lines from v1.0)
- **Tech stack additions:** Tenacity (重试机制), SQLite3 (下载历史追踪)
- **48/48 tests passing** (100% - Phase 7 专用测试)
- **100% requirements coverage** — 4/4 v1.1 requirements satisfied
- **完整实现:** 生产级别错误处理、增量下载、断点续传、结构化日志
- **生产就绪:** 完整的错误处理覆盖、原子文件操作、优雅退出机制

**Shipped v1.2** (2026-02-28) with:
- **4305 lines of Python code** in src/ (+573 lines from v1.1)
- **Tech stack:** Same as v1.1, enhanced with CLI API features
- **57/62 tests passing** (92%) — 2 Windows encoding issues, 3 skipped
- **100% requirements coverage** — 9/9 v1.2 requirements satisfied
- **完整实现:** CLI API 接口 (--json-help, --quiet, --json-output)、INTEGRATION.md 文档 (831 行)、API 验证
- **第三方集成:** 完整的 CLI API 接口,支持命令发现、静默执行、JSON 输出、退出码判断

**Key Technical Decisions:**
- 直接使用 PixivPy3 而非封装 gallery-dl (更直接的 API 控制)
- OAuth PKCE 认证流程 + Playwright 自动化
- Fernet 加密存储 token
- Pydantic v2 用于数据模型和验证
- Click 子命令模式 + Hydra 配置系统
- JSON 标准化输出模型 (第三方友好)

## Constraints

- **技术栈:** Python 3.8+ — 与 PixivPy3 兼容性要求
- **依赖:** PixivPy3 — 核心 API 调用功能
- **认证方式:** Pixiv refresh token — 受 Pixiv 平台限制
- **平台限制:** Pixiv 反爬虫和频率限制 — 已实现速率控制和自动重试
- **跨平台:** 支持 Windows/Linux/macOS — v1.0 在 Windows 环境开发和测试
- **开发规范:** BAT 脚本不包含中文字符,临时测试文件放在 `tmp` 目录

## Key Decisions

| Decision | Rationale | Outcome |
|----------|-----------|---------|
| 直接使用 PixivPy3 而非封装 gallery-dl | 更直接的 API 控制,避免额外依赖层,性能更好 | ✓ Good — 完全控制认证和下载流程 |
| Python 3.8+ 作为实现语言 | 与 PixivPy3 兼容,生态成熟,类型安全 | ✓ Good — Pydantic v2 + Click 完美集成 |
| JSON 标准化输出模型 | 结构化数据,易于程序解析,支持复杂嵌套信息 | ✓ Good — 第三方集成友好 |
| 支持 13 种排行榜类型 | 满足不同场景需求,提供灵活性 | ✓ Good — 覆盖所有 Pixiv 官方排行榜 |
| OAuth PKCE + Playwright 自动化 | 提供浏览器自动化登录体验,降低用户门槛 | ✓ Good — 首次登录后完全自动 |
| Fernet 加密存储 token | 保护敏感信息,基于机器特征派生密钥 | ✓ Good — 无需用户管理密钥 |
| Click 子命令 + Hydra 配置 | 清晰的 CLI 结构 + 灵活的配置管理 | ✓ Good — 易于扩展和维护 |
| Pydantic v2 数据模型 | 自动验证、序列化、类型安全 | ✓ Good — 减少样板代码,提高可靠性 |
| 增量下载 + 进度文件 | 支持断点续传,避免重复下载 | ✓ Good — 大型排行榜(月榜)友好 |
| YAML 配置文件 | 易于阅读和编辑,与 Hydra 集成 | ✓ Good — 用户可自定义下载参数 |
| Tenacity 重试机制 | 生产级别的指数退避策略,自动重试网络和文件操作 | ✓ Good — 网络错误自动恢复,用户体验提升 |
| SQLite 下载历史追踪 | 替代 JSON 进度文件,支持高效查询和增量下载 | ✓ Good — WAL 模式提升并发性能,跨目录统一追踪 |
| 结构化错误响应模型 | 统一的错误格式,支持部分成功场景,退出码分级 | ✓ Good — 第三方程序友好,错误信息清晰 |
| ResumeManager 断点续传 | 基于索引的恢复机制,程序中断后从中断处继续 | ✓ Good — 减少重复下载,优雅退出 |
| JSON Lines 文件日志 | 结构化日志格式,便于解析和分析 | ✓ Good — 控制台简洁,文件详细 |
| CLI API 全局参数 | --json-help, --quiet, --json-output 支持第三方工具集成 | ✓ Good — 命令发现、静默执行、JSON 输出 |
| INTEGRATION.md 文档 | 831 行完整集成指南,包含示例和退出码参考 | ✓ Good — 降低第三方集成门槛 |
| API 验证和 Gap Closure | 5 轮 gap closure 修复关键问题,确保 API 稳定性 | ✓ Good — 修复退出码回归,验证 JSON 输出 |

---
*Last updated: 2026-03-16 after starting v1.3 milestone*
