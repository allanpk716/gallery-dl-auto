# Project Research Summary

**Project:** gallery-dl-auto (Pixiv 排行榜下载器)
**Domain:** CLI 工具,封装型下载器,浏览器自动化
**Researched:** 2026-02-24
**Confidence:** HIGH

## Executive Summary

gallery-dl-auto 是一个专注于 Pixiv 排行榜下载的 CLI 工具,核心价值在于自动化 OAuth refresh token 管理,这是对标工具(如 gallery-dl、PowerfulPixivDownloader)都未能很好解决的痛点。该项目采用封装模式,将 gallery-dl 作为 Python 库调用,并使用 Playwright 实现浏览器自动化登录,首次运行时用户手动登录后自动捕获 token,后续自动刷新,彻底免去从浏览器开发者工具手动复制 token 的繁琐操作。

推荐的技术栈为:Python 3.10+ 作为核心语言,gallery-dl 1.27.0+ 作为下载引擎,Playwright 1.51.0+ 实现浏览器自动化,Typer 0.21.1+ 提供 CLI 框架,Pydantic 2.x 处理配置管理。架构采用分层设计:CLI Interface Layer → Core Orchestration Layer → Wrapper Integration Layer → Token Management Layer → Data Layer,各层职责清晰,便于测试和维护。

主要风险集中在三个方面:1) OAuth token 获取流程复杂,pixiv 的 OAuth 机制需要处理验证码、空白页等问题,必须使用 Playwright 提供流畅的用户体验;2) Pixiv API 有严格的速率限制(offset 不超过 5000,高频请求触发 429 错误),必须在 Phase 1 就实现速率控制和自适应退避算法;3) 封装 gallery-dl 时需要正确处理 JSON 输出和元数据解析,避免依赖文本输出格式。关键成功因素是让 token 管理完全透明化——用户首次登录后,后续所有 token 刷新和过期处理都自动完成,这是项目的核心差异化价值。

## Key Findings

### Recommended Stack

研究推荐使用 Python 3.10+ 作为核心语言,与 gallery-dl 生态一致,提供成熟的类型提示和异步支持。核心依赖包括 gallery-dl 1.27.0+(作为 Python 模块调用,提供成熟的 pixiv 支持和 refresh token 认证)、Playwright 1.51.0+(比 Selenium 更现代的浏览器自动化工具,支持网络请求监听和 cookies 捕获)、Typer 0.21.1+(基于类型提示的现代化 CLI 框架,自动生成帮助文档)、Pydantic 2.x(类型安全的配置管理和数据验证)。

**Core technologies:**
- **Python 3.10+:** 核心开发语言 — 与 gallery-dl 生态一致,提供完善的类型提示和 match 语句
- **gallery-dl 1.27.0+:** 下载引擎 — 成熟的 pixiv 支持和 refresh token 认证,可直接作为 Python 模块调用
- **Playwright 1.51.0+:** 浏览器自动化 — 自动化获取 refresh token,支持网络请求监听,比 Selenium 更现代可靠
- **Typer 0.21.1+:** CLI 框架 — 基于类型提示的现代化 CLI,自动生成帮助,支持复杂参数验证
- **Pydantic 2.x:** 配置管理 — 类型安全的数据验证,支持环境变量和 .env 文件加载

**Supporting libraries:**
- **playwright-stealth 1.0.6+:** 反爬虫检测规避 — 让自动化脚本更像真实用户
- **Rich 13.x+:** 终端美化 — 进度条、表格、语法高亮,提升用户体验
- **Loguru 0.7.3+:** 日志系统 — 比标准 logging 更简洁的 API,支持日志轮转和彩色输出
- **python-dotenv 1.0.0+:** 环境变量加载 — 敏感信息(如 refresh token)与代码分离

**开发工具:**
- **uv:** 包管理器 — 2025 年推荐的 Python 包管理器,比 pip 快 10-100 倍
- **pyproject.toml:** 项目配置 — PEP 621 标准,替代 setup.py,统一管理依赖

### Expected Features

用户期望的核心功能包括排行榜下载(日榜/周榜/月榜,以及分类排行榜)、图片文件下载、元数据获取(标题、作者、标签)、JSON 输出(用于程序化调用)、CLI 命令行接口、基础错误处理。这些是 table stakes,缺失任何一项都会让产品感觉不完整。

**Must have (table stakes):**
- **排行榜下载** — 用户假设存在,支持日榜、周榜、月榜,以及分类排行榜(原创、男性向、女性向等)
- **refresh token 管理** — gallery-dl 必须使用 refresh token 认证,用户无法手动复制
- **图片文件下载** — 核心需求,支持不同分辨率原图下载,使用 gallery-dl 作为下载引擎
- **元数据获取** — 用户需要知道下载了什么,作品信息对后续管理很重要
- **JSON 输出** — 作为 CLI 工具被其他程序调用时需要结构化数据
- **CLI 使用** — 目标用户是技术人员,命令行是最自然的交互方式
- **错误处理** — 下载过程会遇到网络错误、权限错误等各种问题

**Should have (competitive):**
- **自动化 token 获取** — 核心差异化价值,首次登录后自动捕获 token,无需手动操作浏览器
- **多排行榜类型支持** — 支持下载多种排行榜,满足不同场景需求
- **增量下载** — 避免重复下载已保存内容,节省带宽和时间
- **丰富的元数据** — 获取完整的作品和用户信息,支持更复杂的下游应用
- **可编程调用** — 作为 Python 库被其他程序导入使用,支持自动化脚本集成
- **下载进度反馈** — 实时显示下载进度和状态,提升用户体验
- **并发控制** — 控制下载速率避免被封禁,同时保证下载效率

**Defer (v2+):**
- **动图转换** — ugoira 转 GIF/WebM/APNG,需要集成 FFmpeg,复杂度较高
- **高级过滤** — 按标签、收藏数、分辨率等条件筛选作品
- **自定义文件命名** — 支持模板化文件名和目录结构

### Architecture Approach

推荐采用分层架构,从上到下依次为:CLI Interface Layer(用户交互和命令解析)、Core Orchestration Layer(下载协调和结果聚合)、Wrapper Integration Layer(封装 gallery-dl,隔离外部依赖)、Token Management Layer(Token 生命周期管理和浏览器自动化)、Data Layer(配置和状态持久化)。这种设计的核心思想是通过封装模式隔离 gallery-dl 的复杂性,使用 Token Manager 自动处理 OAuth 流程,让用户无感知 token 过期和刷新。

**Major components:**
1. **CLI Interface Layer (cli/)** — 用户交互入口,使用 Typer 实现命令行接口,支持 download/auth/config 子命令
2. **Core Orchestration Layer (core/)** — Ranking Downloader Service 负责下载协调,Result Aggregator 聚合多次下载结果,提供统一的 JSON 输出格式
3. **Wrapper Integration Layer (wrapper/)** — gallery-dl Wrapper 封装外部工具调用,提供统一接口,处理 JSON 解析和错误转换
4. **Token Management Layer (auth/)** — Token Manager 管理 token 生命周期(获取、存储、自动刷新),Browser Automation 使用 Playwright 实现登录自动化,Token Storage 使用 keyring 安全存储
5. **Data Layer (config/, models/)** — Config Manager 管理配置文件和环境变量,Result Models 定义数据结构,使用 Pydantic 确保类型安全

**关键架构模式:**
- **Wrapper/Facade Pattern:** 封装 gallery-dl,隔离外部依赖,提供稳定接口,便于版本升级和测试
- **Token Manager with Auto-Refresh:** 集中管理 token 生命周期,自动处理过期,使用 keyring 安全存储
- **Result Aggregator Pattern:** 聚合多次下载结果,提供统一的 JSON 输出,支持增量下载和错误恢复

### Critical Pitfalls

研究发现了 5 个关键陷阱,其中 2 个必须在 Phase 1 就解决,3 个在 Phase 2 解决:

1. **OAuth Token 获取流程复杂且易失败** — pixiv 的 OAuth 流程需要手动操作浏览器开发者工具,对非技术用户极不友好,容易遇到空白页、找不到 callback 请求、验证码阻塞等问题。**避免方法:** 使用 Playwright 实现全自动化流程,首次运行时打开浏览器窗口让用户手动登录,自动监听网络请求捕获 token,持久化存储并实现自动刷新机制。

2. **Rate Limit 触发导致 429 错误和账号封禁** — 批量下载排行榜时触发 pixiv 的频率限制,返回 429 Too Many Requests,严重时导致账号被封禁。**避免方法:** 实现请求速率限制(建议每请求间隔 1-2 秒),使用指数退避算法处理 429 错误并自动重试,检测已封禁账号并跳过,实现断点续传避免重复请求。

3. **封装 gallery-dl 时未正确处理子进程输出** — 调用 gallery-dl 时无法正确捕获其输出,导致无法获取下载结果的元数据和状态,JSON 输出功能失效。**避免方法:** 使用 gallery-dl 的 `--write-metadata` 和 `--metadata` 选项获取结构化数据,解析 JSON 输出而不是文本输出,正确处理子进程返回码和错误输出。

4. **API Offset 限制导致排行榜下载不完整** — pixiv API 限制 offset 最大为 5000,导致无法获取完整的排行榜内容(日榜通常 500 张,但月榜可能 1500+ 张)。**避免方法:** 检查 API 响应中的错误信息,实现正确的分页逻辑,对于大型排行榜分段下载,记录已下载的 offset 支持从中断处继续。

5. **缺乏错误恢复和状态持久化** — 下载过程中断(网络问题、程序崩溃)后,必须从头开始,已下载的文件被重复下载,浪费时间且增加触发 rate limit 的风险。**避免方法:** 实现下载状态的持久化存储(JSON 文件或 SQLite),每次启动时检查已下载的内容并跳过,保存失败的下载项支持单独重试。

## Implications for Roadmap

基于研究发现,建议将项目分为 3 个阶段,每个阶段都有明确的价值交付和风险控制:

### Phase 1: 认证基础与核心下载

**Rationale:** OAuth token 管理是项目的核心差异化价值,也是最大的技术难点。根据 PITFALLS.md,OAuth 流程复杂且易失败,必须在第一阶段就正确实现。同时,Phase 1 必须实现速率限制,避免用户触发 429 错误导致账号封禁。这两个问题是致命的——如果 token 获取失败或触发封禁,用户根本无法使用产品。

**Delivers:** 完整的 token 自动化管理(首次登录后自动捕获、存储、刷新),基础排行榜下载功能(日榜),JSON 输出,速率限制保护

**Addresses (features):** refresh token 自动化管理(核心差异化)、日排行榜下载、图片文件下载、基础元数据获取、JSON 输出、CLI 接口、基础错误处理

**Avoids (pitfalls):** OAuth Token 获取流程复杂且易失败、Rate Limit 触发导致 429 错误和账号封禁

**Stack elements:** Python 3.10+, Playwright 1.51.0+(浏览器自动化), Typer 0.21.1+(CLI), Pydantic 2.x(配置), python-dotenv(环境变量), playwright-stealth(反检测), Rich(进度条), Loguru(日志)

**Architecture components:** CLI Interface Layer, Token Management Layer (Token Manager + Browser Automation + Token Storage), Wrapper Integration Layer (gallery-dl Wrapper), Data Layer (Config Manager + Result Models)

**Success criteria:**
- 连续测试 10 次 token 获取流程,成功率 > 95%
- 下载 500 张图片不触发 429 错误
- Token 过期后自动刷新,用户无感知

---

### Phase 2: 排行榜下载完善与错误恢复

**Rationale:** Phase 1 验证了核心流程后,Phase 2 扩展排行榜类型支持,并解决 PITFALLS.md 中提到的 3 个陷阱:gallery-dl 输出处理、API offset 限制、错误恢复和状态持久化。这些是让产品真正可用的关键——没有状态持久化,中断后必须从头开始,用户体验极差。

**Delivers:** 多排行榜类型支持(周榜、月榜、原创榜、男性向、女性向),增量下载(跳过已下载内容),扩展元数据(收藏数、浏览量等统计数据),完善的错误恢复机制

**Uses (stack):** 继续使用 Phase 1 的所有技术,重点优化 gallery-dl 集成(正确处理 JSON 输出和元数据)

**Implements (architecture):** Core Orchestration Layer (Ranking Downloader Service + Result Aggregator), Data Layer 扩展(下载状态持久化,支持 SQLite 或 JSON)

**Addresses (features):** 多排行榜类型支持、增量下载、扩展元数据、下载进度反馈、并发控制配置

**Avoids (pitfalls):** 封装 gallery-dl 时未正确处理子进程输出、API Offset 限制导致排行榜下载不完整、缺乏错误恢复和状态持久化

**Success criteria:**
- 月榜(1500+ 张)能完整下载,不因 offset 限制中断
- 验证能正确获取所有元数据字段(标题、作者、标签、收藏数、浏览量)
- kill 程序后重新运行能从中断处继续
- 所有错误都有对应的重试或恢复机制

---

### Phase 3: 可编程性与高级功能

**Rationale:** Phase 1 和 Phase 2 完成了核心功能,Phase 3 专注于提升可编程性和用户体验,让工具更容易集成到自动化流程中。根据 FEATURES.md,可编程调用是差异化功能,JSON 输出是 table stakes,Phase 3 将两者结合,提供清晰的 Python API 接口。

**Delivers:** 可编程调用 API(作为 Python 库导入使用),优化下载进度反馈(Rich 进度条或 JSON 事件流),可配置的并发控制

**Uses (stack):** Rich 13.x+(增强进度条和表格显示), 优化 Pydantic 配置(支持更复杂的嵌套配置)

**Implements (architecture):** Core Orchestration Layer 优化(提供公共 API 接口), CLI Interface Layer 优化(支持 `--format json` 输出事件流)

**Addresses (features):** 可编程调用 API、下载进度反馈、并发控制配置

**Success criteria:**
- 提供清晰的 Python API 文档和示例代码
- 支持作为库导入并调用 `download_ranking()` 等函数
- 进度条显示当前下载项、已完成数量、预计剩余时间
- 支持配置并发数和请求速率

---

### Phase Ordering Rationale

**为什么这个顺序?**

1. **依赖关系:** ARCHITECTURE.md 的构建顺序明确指出,Config Manager 和 CLI Parser 是基础,必须最先实现。Token Management 依赖 Config Manager 和 Token Storage,gallery-dl Wrapper 依赖 Config Manager。因此 Phase 1 必须包含这些基础设施。

2. **风险前置:** PITFALLS.md 的前两个陷阱(OAuth token 获取和 Rate Limit)是致命的,必须在 Phase 1 解决。如果 token 获取失败,用户根本无法使用产品;如果触发 Rate Limit,用户账号会被封禁。这两个问题不能留到后续阶段。

3. **价值驱动:** FEATURES.md 明确标注了 P1(必须)、P2(应该)、P3(未来)优先级。Phase 1 覆盖所有 P1 功能,Phase 2 覆盖 P2 功能的核心部分,Phase 3 覆盖剩余的 P2 功能。这种划分确保每个阶段都交付独立价值。

4. **架构分层:** ARCHITECTURE.md 推荐的分层架构自然地映射到 3 个阶段:
   - Phase 1: CLI Interface + Token Management + Wrapper + 基础 Data Layer
   - Phase 2: Core Orchestration + Data Layer 扩展(状态持久化)
   - Phase 3: API 优化 + 用户体验增强

### Research Flags

**需要 deeper research 的阶段:**

- **Phase 1 - Token 自动刷新逻辑:** pitfall #1 提到 pixiv OAuth 流程复杂,虽然研究找到了 Playwright 自动化方案,但 token 刷新的具体实现(如何使用旧 token 自动登录并获取新 token)需要更深入的技术调研。建议在 Phase 1 规划时使用 `/gsd:research-phase` 研究 pixiv OAuth token 刷新机制。

- **Phase 2 - gallery-dl JSON 输出格式:** pitfall #3 提到不同版本的 gallery-dl 输出格式可能变化,需要验证 gallery-dl 1.27.0+ 的 `--metadata` 选项返回的 JSON 字段是否完整。建议在 Phase 2 开始前使用 `/gsd:research-phase` 研究 gallery-dl 的 metadata 输出格式和版本兼容性。

**标准模式,可跳过 research-phase 的阶段:**

- **Phase 1 - CLI 和配置管理:** Typer 和 Pydantic 是成熟的库,官方文档完善,ARCHITECTURE.md 已提供清晰的代码示例,无需额外研究。

- **Phase 3 - 可编程 API 设计:** Python API 设计有成熟的最佳实践,ARCHITECTURE.md 已提供 Result Aggregator Pattern 示例,可直接实现。

## Confidence Assessment

| Area | Confidence | Notes |
|------|------------|-------|
| Stack | HIGH | 基于 Context7 官方文档和多个 HIGH confidence 源,所有推荐技术都有成熟的官方支持和活跃的社区。gallery-dl、Playwright、Typer、Pydantic 都是 2025-2026 年的推荐选择,有多个成功案例验证。 |
| Features | HIGH | FEATURES.md 基于竞争对手分析(gallery-dl、PowerfulPixivDownloader、PixivToolkit)和用户痛点分析(GitHub issues、Reddit 讨论),优先级划分清晰,P1/P2/P3 有明确的依据。MVP 定义合理,核心价值聚焦在自动化 token 管理。 |
| Architecture | HIGH | ARCHITECTURE.md 基于画廊-dl 源码分析和官方文档,Wrapper/Facade Pattern 和 Token Manager Pattern 都是成熟的设计模式,有详细的代码示例。分层架构清晰,依赖关系明确,构建顺序合理。 |
| Pitfalls | MEDIUM | PITFALLS.md 基于 GitHub issues、社区讨论和最佳实践文章,识别了 5 个关键陷阱,但部分陷阱(如 token 自动刷新逻辑、API offset 限制的具体表现)需要在实现时进一步验证。MEDIUM confidence 是因为部分来源是社区经验,不是官方文档。 |

**Overall confidence:** HIGH

### Gaps to Address

虽然整体信心度是 HIGH,但在实际开发中需要注意以下 gaps:

1. **Token 自动刷新的具体实现:** 研究发现 pixiv 的 refresh token 有效期约 90 天,但如何使用旧 refresh token 自动登录并获取新 token 的具体流程不明确。**处理方法:** 在 Phase 1 开始前,使用 `/gsd:research-phase` 深入研究 pixiv OAuth token 刷新机制,或参考 gallery-dl 源码中的实现。

2. **gallery-dl metadata 输出字段的完整性:** 研究推荐使用 gallery-dl 的 `--metadata` 选项获取作品信息,但未验证返回的 JSON 是否包含所有需要的字段(标题、作者、标签、收藏数、浏览量等)。**处理方法:** 在 Phase 2 开始前,实际运行 `gallery-dl --metadata` 并检查输出格式,确保包含所有 P1/P2 需要的元数据字段。

3. **Playwright 反检测效果验证:** 虽然推荐使用 playwright-stealth,但未验证其是否能有效绕过 pixiv 的反爬虫检测。**处理方法:** 在 Phase 1 开发时,先实现不带 playwright-stealth 的版本进行测试,如果触发反爬虫再添加 stealth 模式,记录效果。

4. **Rate Limit 的具体阈值:** 研究建议每请求间隔 1-2 秒,但未找到 pixiv 官方的具体限制数值。**处理方法:** 在 Phase 1 实现时采用保守策略(每请求间隔 2 秒),在测试中逐步优化,记录触发 429 的阈值。

5. **月榜下载的性能和内存占用:** ARCHITECTURE.md 提到月榜可能有 1500+ 张图片,但未评估内存占用和下载时间。**处理方法:** 在 Phase 2 实现增量下载和断点续传时,进行实际测试,如果内存占用过高则实现流式处理。

## Sources

### Primary (HIGH confidence)

- **Context7 library ID `/mikf/gallery-dl`:** gallery-dl 作为 Python 模块的 API 使用、pixiv 认证配置、配置选项 — HIGH confidence,官方源码和文档
- **Context7 library ID `/websites/playwright_dev_python`:** Playwright Python API、浏览器自动化、网络请求监听、cookies 管理 — HIGH confidence,官方文档
- **Context7 library ID `/fastapi/typer`:** Typer CLI 框架、子命令组织、参数验证 — HIGH confidence,官方文档
- **Context7 library ID `/websites/pydantic_dev`:** Pydantic Settings、环境变量加载、嵌套配置 — HIGH confidence,官方文档
- **gallery-dl 官方文档:** https://gdl-docs.mikf.eu/ — HIGH confidence,配置和 API 参考
- **gallery-dl GitHub Repository:** https://github.com/mikf/gallery-dl — HIGH confidence,源码分析和 issues 调研
- **gallery-dl Configuration Documentation:** https://github.com/mikf/gallery-dl/blob/master/docs/configuration.rst — HIGH confidence,配置示例
- **Pixiv OAuth Flow Gist:** https://gist.github.com/ZipFile/c9ebedb224406f4f11845ab700124362 — HIGH confidence,OAuth 实现细节

### Secondary (MEDIUM confidence)

- **PowerfulPixivDownloader Chrome Extension:** https://chromewebstore.google.com/detail/powerful-pixiv-downloader/dkndmhgdcmjdmkdonmbgjpijejdcilfh — 竞品分析,功能对比
- **PowerfulPixivDownloader Official Site:** https://pixiv.download/ — 竞品分析,用户需求调研
- **gallery-dl GitHub Issues:** OAuth、Rate Limit、API 错误等用户问题 — 真实用户痛点,但非官方文档
- **Reddit Discussion:** https://www.reddit.com/r/DataHoarder/comments/1hyx7hq/help_getting_gallerydl_working_with_pixiv/ — 用户体验问题,社区反馈
- **Real Python CLI Best Practices:** https://realpython.com/python-click/ — Python CLI 最佳实践,通用建议
- **Web Scraping Rate Limit Best Practices 2026:** https://scrape.do/blog/web-scraping-rate-limit/ — 通用 rate limit 处理策略,非 pixiv 特定

### Tertiary (LOW confidence)

- **Pixiv API Documentation:** https://pixiv-api.readthedocs.io/en/latest — 可能过时,pixiv 官方已移除用户名/密码认证
- **Pixiv Ajax API Docs:** https://github.com/daydreamer-json/pixiv-ajax-api-docs — 已停止维护,仅作参考
- **Pixiv.ts GitHub Repository:** https://github.com/Moestash/pixiv.ts — TypeScript 实现,思路可参考但细节不同
- **playwright-stealth 文档:** 反检测效果未在 pixiv 上验证,需要在实现时测试

---
*Research completed: 2026-02-24*
*Ready for roadmap: yes*
