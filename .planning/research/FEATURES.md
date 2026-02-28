# Feature Research

**Domain:** Pixiv 排行榜下载器
**Researched:** 2026-02-24
**Confidence:** HIGH

## Feature Landscape

### Table Stakes (Users Expect These)

功能用户假设存在。缺失这些 = 产品感觉不完整。

| Feature | Why Expected | Complexity | Notes |
|---------|--------------|------------|-------|
| **排行榜下载** | 排行榜是 pixiv 最重要的内容发现渠道,用户需要保存高质量内容 | MEDIUM | 支持日榜、周榜、月榜,以及分类排行榜(原创、男性向、女性向等) |
| **refresh token 管理** | gallery-dl 必须使用 refresh token 认证,用户无法手动复制 | HIGH | 自动化获取、存储、更新 refresh token 的完整生命周期管理 |
| **图片文件下载** | 下载图片是核心需求,没有这个功能就不是下载器 | LOW | 支持不同分辨率原图下载,使用 gallery-dl 作为下载引擎 |
| **元数据获取** | 用户需要知道下载了什么,作品信息对后续管理很重要 | MEDIUM | 包括标题、作者、标签、收藏数、浏览量等作品元信息 |
| **JSON 输出** | 作为 CLI 工具被其他程序调用时需要结构化数据 | LOW | 返回下载结果、文件路径、错误信息等结构化 JSON |
| **CLI 使用** | 目标用户是技术人员,命令行是最自然的交互方式 | LOW | 提供清晰的命令行参数和帮助信息 |
| **错误处理** | 下载过程会遇到网络错误、权限错误等各种问题 | MEDIUM | 清晰的错误信息,支持重试,不崩溃 |

### Differentiators (Competitive Advantage)

差异化功能。非必需,但很有价值。

| Feature | Value Proposition | Complexity | Notes |
|---------|-------------------|------------|-------|
| **自动化 token 获取** | 用户首次登录后自动捕获 token,无需从浏览器开发者工具手动复制,真正实现自动化流程 | HIGH | 这是核心差异化价值,对标工具都需要用户手动操作浏览器获取 token |
| **多排行榜类型支持** | 支持下载多种排行榜(日/周/月 + 各分类),满足不同场景需求 | MEDIUM | gallery-dl 已支持多种模式,需要提供友好的选择接口 |
| **增量下载** | 避免重复下载已保存内容,节省带宽和时间 | MEDIUM | 需要记录下载历史,检查文件是否已存在 |
| **丰富的元数据** | 获取完整的作品和用户信息,支持更复杂的下游应用 | MEDIUM | 利用 gallery-dl 的 metadata 选项,扩展 JSON 输出内容 |
| **可编程调用** | 作为 Python 库被其他程序导入使用,支持自动化脚本集成 | LOW | 设计清晰的 API 接口,支持模块化调用 |
| **下载进度反馈** | 实时显示下载进度和状态,提升用户体验 | MEDIUM | 终端进度条或 JSON 事件流 |
| **并发控制** | 控制下载速率避免被封禁,同时保证下载效率 | MEDIUM | 合理的请求间隔,支持配置并发数 |
| **动图支持** | 下载并转换 ugoira 动图为 GIF/WebM/APNG 等格式 | HIGH | 需要集成 FFmpeg,增加依赖复杂度 |

### Anti-Features (Commonly Requested, Often Problematic)

反功能。看起来很好但会带来问题。

| Feature | Why Requested | Why Problematic | Alternative |
|---------|---------------|-----------------|-------------|
| **GUI 界面** | 非技术用户更容易上手 | 增加开发和维护成本,偏离 CLI 工具定位,限制自动化集成能力 | 专注于 CLI + JSON 输出,让用户构建自己的 UI |
| **批量账号管理** | 下载不同用户的内容 | 增加复杂度,违反 pixiv 使用条款风险,单账号已满足大部分场景 | 单账号设计,专注于个人使用 |
| **自动上传/分享** | 自动将下载内容发布到其他平台 | 版权问题,平台政策风险,功能蔓延 | 专注于下载,让用户自行处理后续使用 |
| **图片格式转换/编辑** | 统一格式或修改图片 | 偏离核心功能,依赖复杂,性能开销 | 保持原图质量,让用户使用专业工具 |
| **下载非排行榜内容** | 扩展到搜索结果、用户作品集等 | 功能蔓延,复杂度增加,维护负担重 | 专注排行榜场景,避免成为大而全的下载器 |
| **代理/VPN 集成** | 帮助用户访问 pixiv | 网络环境复杂多样,难以通用化,增加维护成本 | 让用户自行配置系统代理环境变量 |

## Feature Dependencies

```
[refresh token 自动化获取]
    └──requires──> [浏览器自动化工具(Selenium/Playwright)]
                       └──requires──> [用户手动登录(首次)]

[排行榜下载]
    └──requires──> [refresh token 管理]
    └──requires──> [gallery-dl 集成]

[元数据获取]
    └──requires──> [gallery-dl 集成]
    └──enhances──> [JSON 输出]

[增量下载]
    └──requires──> [下载历史记录]
    └──requires──> [文件存在性检查]

[动图转换]
    └──requires──> [FFmpeg 安装]
    └──conflicts──> [无依赖设计理念]

[并发控制]
    └──enhances──> [排行榜下载]
    └──prevents──> [反爬虫封禁]

[可编程调用]
    └──enhances──> [JSON 输出]
    └──requires──> [清晰的 API 设计]
```

### Dependency Notes

- **refresh token 自动化获取 requires 浏览器自动化工具:** 需要使用 Selenium 或 Playwright 等工具模拟浏览器行为,首次需要用户手动登录,之后自动捕获 token
- **元数据获取 enhances JSON 输出:** 通过 gallery-dl 的 metadata 选项获取更丰富的作品信息,使 JSON 输出更有价值
- **动图转换 conflicts 无依赖设计理念:** FFmpeg 是重量级依赖,与轻量化设计理念冲突,作为可选功能提供
- **并发控制 prevents 反爬虫封禁:** 合理控制请求频率避免触发 pixiv 的反爬虫机制

## MVP Definition

### Launch With (v1)

MVP - 验证概念所需的最小功能集。

- [x] **refresh token 自动化管理** — 核心差异化价值,解决最大痛点,首次登录后自动捕获和更新
- [x] **日排行榜下载** — 最常用的排行榜类型,验证核心下载流程
- [x] **图片文件下载** — 核心功能,使用 gallery-dl 作为下载引擎
- [x] **基础元数据获取** — 作品标题、作者、标签等信息
- [x] **JSON 输出** — 返回下载结果、文件路径等结构化数据
- [x] **CLI 命令行接口** — 支持命令行直接调用
- [x] **基础错误处理** — 网络错误、权限错误的清晰提示

### Add After Validation (v1.x)

核心功能验证后添加的增强功能。

- [ ] **多排行榜类型支持** — 添加周榜、月榜、原创榜、男性向、女性向等分类排行榜下载
- [ ] **增量下载** — 记录下载历史,跳过已下载内容
- [ ] **扩展元数据** — 获取收藏数、浏览量、评论数等统计数据
- [ ] **可编程调用 API** — 支持作为 Python 库导入使用
- [ ] **下载进度反馈** — 终端进度条或 JSON 事件流
- [ ] **并发控制配置** — 允许用户自定义请求速率

### Future Consideration (v2+)

延后到产品市场契合度建立后。

- [ ] **动图转换** — ugoira 转 GIF/WebM/APNG,需要集成 FFmpeg,复杂度较高
- [ ] **高级过滤** — 按标签、收藏数、分辨率等条件筛选作品
- [ ] **自定义文件命名** — 支持模板化文件名和目录结构
- [ ] **下载历史查询** — 提供查询已下载内容的接口
- [ ] **批量排行榜下载** — 一次性下载多个日期的排行榜

## Feature Prioritization Matrix

| Feature | User Value | Implementation Cost | Priority |
|---------|------------|---------------------|----------|
| refresh token 自动化管理 | HIGH | HIGH | P1 |
| 日排行榜下载 | HIGH | LOW | P1 |
| 图片文件下载 | HIGH | LOW | P1 |
| 基础元数据获取 | HIGH | MEDIUM | P1 |
| JSON 输出 | HIGH | LOW | P1 |
| CLI 接口 | HIGH | LOW | P1 |
| 基础错误处理 | HIGH | MEDIUM | P1 |
| 多排行榜类型 | MEDIUM | MEDIUM | P2 |
| 增量下载 | MEDIUM | MEDIUM | P2 |
| 扩展元数据 | MEDIUM | LOW | P2 |
| 可编程调用 API | MEDIUM | MEDIUM | P2 |
| 下载进度反馈 | MEDIUM | MEDIUM | P2 |
| 并发控制配置 | MEDIUM | LOW | P2 |
| 动图转换 | LOW | HIGH | P3 |
| 高级过滤 | LOW | MEDIUM | P3 |
| 自定义命名 | LOW | MEDIUM | P3 |
| 下载历史查询 | LOW | MEDIUM | P3 |
| 批量排行榜 | LOW | MEDIUM | P3 |

**Priority key:**
- P1: Must have for launch (MVP)
- P2: Should have, add when possible (v1.x)
- P3: Nice to have, future consideration (v2+)

## Competitor Feature Analysis

| Feature | gallery-dl | PowerfulPixivDownloader | PixivToolkit | 我们的设计 |
|---------|-----------|------------------------|-------------|----------|
| **排行榜下载** | ✅ 支持多种排行榜 | ✅ 支持 7 种排行榜 | ✅ 支持 | ✅ 支持多种排行榜 |
| **认证方式** | 手动复制 refresh token | 浏览器扩展自动获取 | 浏览器扩展 | 自动化获取 refresh token |
| **元数据获取** | ✅ 丰富 | ✅ 丰富 | ✅ 丰富 | ✅ 基于画廊-画廊-dl |
| **JSON 输出** | ✅ 支持 | ❌ 浏览器下载 | ⚠️ 有限 | ✅ 结构化 JSON |
| **CLI 使用** | ✅ 原生 CLI | ❌ 浏览器扩展 | ❌ 浏览器扩展 | ✅ 专注 CLI |
| **批量下载** | ✅ 强大 | ✅ 强大 | ✅ 强大 | ✅ 通过 gallery-dl |
| **GUI 界面** | ❌ 无 | ✅ 浏览器面板 | ✅ 浏览器面板 | ❌ 专注 CLI |
| **动图转换** | ✅ 支持 | ✅ 支持 | ✅ 支持 | ⚠️ 可选(v2+) |
| **增量下载** | ✅ 通过 archive | ✅ 下载记录 | ✅ 下载记录 | ⚠️ v1.x 添加 |
| **过滤器** | ✅ 强大 | ✅ 丰富 | ⚠️ 基础 | ⚠️ v2+ 添加 |
| **可编程调用** | ✅ Python 库 | ❌ 浏览器扩展 | ❌ 浏览器扩展 | ✅ 设计目标 |

**我们的定位:**
- **vs gallery-dl:** 提供 refresh token 自动化,降低使用门槛,专注于排行榜场景
- **vs 浏览器扩展:** CLI 优先,支持自动化集成,JSON 输出便于程序化调用
- **核心优势:** 自动化 token 管理 + CLI + 可编程 + JSON 输出的组合

## Sources

- [gallery-dl GitHub Repository](https://github.com/mikf/gallery-dl) - MEDIUM confidence
- [gallery-dl Configuration Documentation](https://github.com/mikf/gallery-dl/blob/master/docs/configuration.rst) - HIGH confidence
- [PowerfulPixivDownloader Chrome Extension](https://chromewebstore.google.com/detail/powerful-pixiv-downloader/dkndmhgdcmjdmkdonmbgjpijejdcilfh) - HIGH confidence
- [PowerfulPixivDownloader Official Site](https://pixiv.download/) - HIGH confidence
- [Pixiv MCP Server GitHub](https://github.com/DiLiuNEUexpresscompany/pixiv-mcp) - MEDIUM confidence
- [Pixiv API Documentation](https://pixiv-api.readthedocs.io/en/latest) - MEDIUM confidence (可能过时)
- [Pixiv Ajax API Docs](https://github.com/daydreamer-json/pixiv-ajax-api-docs) - LOW confidence (已停止维护)
- [Pixiv.ts GitHub Repository](https://github.com/Moestash/pixiv.ts) - MEDIUM confidence
- 腾讯云开发者社区 - PowerfulPixivDownloader 介绍 - MEDIUM confidence
- 项目 README 和需求文档 - HIGH confidence

---
*Feature research for: Pixiv 排行榜下载器*
*Researched: 2026-02-24*
