# Domain Pitfalls

**Domain:** Pixiv 排行榜下载器
**Researched:** 2026-02-24
**Confidence:** MEDIUM

## Critical Pitfalls

### Pitfall 1: OAuth Token 获取流程复杂且易失败

**What goes wrong:**
用户无法正确获取 pixiv refresh token,在 OAuth 流程中遇到空白页、找不到 callback 请求、验证码阻塞等问题,导致项目一开始就无法使用。

**Why it happens:**
1. pixiv 的 OAuth 流程需要手动操作浏览器开发者工具,对非技术用户极其不友好
2. 浏览器开发者工具中的网络请求众多,用户难以找到正确的 callback 请求
3. pixiv 会弹出验证码页面,导致自动化流程中断
4. token 有时效性,过期后需要重新获取

**How to avoid:**
- 实现全自动化的 token 获取流程,使用 Playwright/Selenium 模拟浏览器登录
- 首次运行时打开浏览器窗口让用户手动登录,自动监听网络请求捕获 token
- 将 refresh token 持久化存储,避免重复获取
- 实现 token 自动刷新机制,在 access token 过期前主动刷新

**Warning signs:**
- 用户反馈"找不到 code 参数"
- 测试时 OAuth 流程经常卡在空白页
- token 获取成功率低于 90%

**Phase to address:**
Phase 1 (认证基础) - 这是项目的核心价值,必须在第一阶段就正确实现

---

### Pitfall 2: Rate Limit 触发导致 429 错误和账号封禁

**What goes wrong:**
批量下载排行榜时触发 pixiv 的频率限制,返回 429 Too Many Requests 错误,严重时导致账号被封禁。

**Why it happens:**
1. pixiv API 有严格的请求频率限制
2. 下载排行榜时短时间内发起大量请求
3. 没有实现请求间隔和速率控制
4. 下载已封禁账号的作品时会触发更严格的限制

**How to avoid:**
- 实现请求速率限制(建议每请求间隔 1-2 秒)
- 使用指数退避算法处理 429 错误,自动重试
- 检测已封禁账号并跳过,避免无效请求
- 实现断点续传,避免中断后重新开始导致重复请求

**Warning signs:**
- 测试时出现 429 错误
- 连续下载超过 50 张图片时失败
- 下载速度明显变慢或经常中断

**Phase to address:**
Phase 1 (认证基础) - 必须在核心下载功能实现时就加入速率限制

---

### Pitfall 3: 封装 gallery-dl 时未正确处理子进程输出

**What goes wrong:**
调用 gallery-dl 时无法正确捕获其输出,导致无法获取下载结果的元数据和状态,JSON 输出功能失效。

**Why it happens:**
1. gallery-dl 的输出混合了进度信息、错误信息和元数据
2. 不同版本的 gallery-dl 输出格式可能变化
3. 未正确配置 gallery-dl 的输出格式
4. 子进程的 stdout/stderr 处理不当

**How to avoid:**
- 使用 gallery-dl 的 `--write-metadata` 和 `--metadata` 选项获取结构化数据
- 使用 `--no-download` 选项先获取元数据
- 解析 gallery-dl 的 JSON 输出而不是尝试解析文本输出
- 正确处理子进程的返回码和错误输出
- 为 gallery-dl 调用添加超时控制

**Warning signs:**
- 无法获取下载文件的路径
- JSON 输出中缺少元数据字段
- gallery-dl 错误时程序崩溃

**Phase to address:**
Phase 2 (排行榜下载核心) - 在实现下载功能时必须正确处理输出

---

### Pitfall 4: API Offset 限制导致排行榜下载不完整

**What goes wrong:**
pixiv API 限制 offset 最大为 5000,导致无法获取完整的排行榜内容(日榜通常 500 张,但其他榜单可能更多)。

**Why it happens:**
1. pixiv API 明确限制 offset 不能超过 5000
2. 未检查 API 返回的错误信息
3. 分页逻辑实现不正确

**How to avoid:**
- 检查 API 响应中的错误信息 `{"offset":["offset must be no more than 5000"]}`
- 实现正确的分页逻辑,每页请求合理数量(如 50-100 张)
- 对于大型排行榜,分段下载而不是一次性请求
- 记录已下载的 offset,支持从中断处继续

**Warning signs:**
- 排行榜下载数量与实际不符
- 日志中出现 offset 相关错误
- 下载在某个点突然中断

**Phase to address:**
Phase 2 (排行榜下载核心) - 实现排行榜下载时必须处理分页限制

---

### Pitfall 5: 缺乏错误恢复和状态持久化

**What goes wrong:**
下载过程中断(网络问题、程序崩溃)后,必须从头开始,已下载的文件被重复下载,浪费时间且增加触发 rate limit 的风险。

**Why it happens:**
1. 未记录下载进度和状态
2. 未检查文件是否已存在
3. 没有实现断点续传机制

**How to avoid:**
- 实现下载状态的持久化存储(如 JSON 文件或 SQLite)
- 每次启动时检查已下载的内容,跳过已完成的
- 提供清理和重新开始选项
- 保存失败的下载项,支持单独重试

**Warning signs:**
- 中断后重新运行时重复下载已完成的文件
- 无法从中断处继续
- 大型排行榜下载失败率高

**Phase to address:**
Phase 2 (排行榜下载核心) - 核心功能实现时就必须加入

---

## Technical Debt Patterns

Shortcuts that seem reasonable but create long-term problems.

| Shortcut | Immediate Benefit | Long-term Cost | When Acceptable |
|----------|-------------------|----------------|-----------------|
| 手动输入 refresh token | 快速实现原型 | 用户每次都要手动操作,失去自动化价值 | 仅在 PoC 阶段,1 周内必须替换 |
| 不处理 429 错误 | 减少代码复杂度 | 用户账号被封禁,程序不可用 | 永远不可接受 |
| 同步调用 gallery-dl | 实现简单 | 大量下载时程序无响应 | MVP 阶段可接受,正式版必须异步 |
| 不保存下载状态 | 减少文件操作 | 中断后必须重新开始 | 仅 PoC,正式版必须有状态持久化 |
| 直接解析文本输出 | 避免 JSON 解析 | gallery-dl 更新后输出格式变化导致崩溃 | 永远不可接受,必须使用结构化输出 |
| 固定请求间隔 | 快速实现速率限制 | 下载速度可能过慢或仍然触发限制 | MVP 可接受,正式版需要自适应速率 |

## Integration Gotchas

Common mistakes when connecting to external services.

| Integration | Common Mistake | Correct Approach |
|-------------|----------------|------------------|
| gallery-dl OAuth | 依赖 gallery-dl 的 `oauth:pixiv` 命令 | 自己实现 OAuth 流程,使用 Playwright 自动化 |
| gallery-dl 输出 | 尝试解析 stdout 文本 | 使用 `--metadata` 获取 JSON,或解析 sidecar 文件 |
| pixiv API | 在请求头中硬编码 User-Agent | 使用正确的移动端 User-Agent: `PixivAndroidApp/5.0.234` |
| pixiv API | 忽略 API 响应中的错误信息 | 检查每个响应的 `error`, `message` 字段 |
| refresh token | 假设 token 永久有效 | 实现 token 自动刷新,处理 token 失效的情况 |
| gallery-dl 版本 | 假设所有版本行为一致 | 在文档中指定最低版本要求,测试多个版本 |

## Performance Traps

Patterns that work at small scale but fail as usage grows.

| Trap | Symptoms | Prevention | When It Breaks |
|------|----------|------------|----------------|
| 同步下载排行榜 | 500 张图片需要 10+ 分钟 | 使用异步下载,并行处理多个作品 | 下载超过 100 张图片时 |
| 不检查文件存在 | 重复下载浪费带宽和时间 | 下载前检查文件是否存在 | 任何规模,但在中断后重启时最明显 |
| 固定请求速率 | 下载速度过慢或仍触发限制 | 实现自适应速率,根据响应动态调整 | 下载超过 200 张图片时 |
| 内存中保存所有元数据 | 内存占用过高,程序崩溃 | 流式处理,保存到磁盘后释放内存 | 处理超过 1000 张图片时 |
| 无下载队列 | 无法暂停或取消下载 | 实现任务队列,支持暂停/恢复/取消 | 任何需要用户交互的场景 |

## Security Mistakes

Domain-specific security issues beyond general web security.

| Mistake | Risk | Prevention |
|---------|------|------------|
| 明文存储 refresh token | token 泄露导致账号被盗 | 使用系统密钥库或加密存储 token |
| 在日志中打印 token | token 泄露到日志文件 | 日志输出时脱敏敏感信息 |
| 使用不安全的 HTTP 请求 | 中间人攻击 | 确保所有请求使用 HTTPS |
| 硬编码 client_id/client_secret | 密钥泄露,被滥用 | 从环境变量或配置文件读取 |
| 不验证 SSL 证书 | 中间人攻击 | 正确配置 SSL 证书验证 |

## UX Pitfalls

Common user experience mistakes in this domain.

| Pitfall | User Impact | Better Approach |
|---------|-------------|-----------------|
| 首次使用需要读文档 | 用户流失率高 | 提供交互式引导,首次运行自动打开浏览器 |
| 错误信息是原始 API 错误 | 用户不知道如何修复 | 将错误转换为可操作的提示,如"请求过快,等待 X 秒后重试" |
| 没有下载进度显示 | 用户不知道程序是否在运行 | 显示进度条、当前下载项、预计剩余时间 |
| JSON 输出格式不明确 | 调用者难以解析 | 提供明确的 JSON schema 文档和示例 |
| 配置选项过多 | 用户不知如何配置 | 提供合理的默认值,只在必要时暴露配置 |

## "Looks Done But Isn't" Checklist

Things that appear complete but are missing critical pieces.

- [x] **OAuth 登录:** 往往只测试了一次成功,未考虑 token 过期、验证码、网络错误等场景 — 验证连续运行 24 小时无需重新登录
- [x] **排行榜下载:** 可能只测试了日榜,未考虑周榜、月榜内容更多时的分页和速率限制 — 验证月榜(约 1500 张)能完整下载
- [x] **JSON 输出:** 可能只返回部分字段,缺少错误信息或文件路径 — 验证输出包含所有要求的字段(标题、作者、标签、统计、路径、错误)
- [x] **错误处理:** 可能只处理了常见错误,未考虑 429、403、网络超时等 — 验证所有错误都有对应的重试或恢复机制
- [x] **速率限制:** 可能加了固定延迟,但未处理 429 响应的自适应退避 — 验证触发 429 后能自动降低请求速率
- [x] **状态持久化:** 可能保存了状态,但未测试程序崩溃后的恢复 — 验证 kill 程序后重新运行能从中断处继续

## Recovery Strategies

When pitfalls occur despite prevention, how to recover.

| Pitfall | Recovery Cost | Recovery Steps |
|---------|---------------|----------------|
| OAuth token 失效 | LOW | 检测 token 失效,提示用户重新登录,自动重新获取 |
| 触发 Rate Limit | MEDIUM | 暂停下载,等待 5-10 分钟,以更低的速率继续 |
| gallery-dl 版本不兼容 | LOW | 检测版本,提示用户升级或降级到支持的版本 |
| 下载状态损坏 | MEDIUM | 扫描已下载文件,重建状态数据库 |
| API 响应格式变化 | HIGH | 解析失败时降级到兼容模式,通知用户需要更新程序 |
| 账号被封禁 | HIGH | 检测封禁状态,提示用户联系 pixiv 客服,提供切换账号选项 |

## Pitfall-to-Phase Mapping

How roadmap phases should address these pitfalls.

| Pitfall | Prevention Phase | Verification |
|---------|------------------|--------------|
| OAuth Token 获取流程复杂且易失败 | Phase 1: 认证基础 | 连续测试 10 次 token 获取流程,成功率 > 95% |
| Rate Limit 触发导致 429 错误 | Phase 1: 认证基础 | 下载 500 张图片不触发 429 错误 |
| 封装 gallery-dl 时未正确处理子进程输出 | Phase 2: 排行榜下载核心 | 验证能正确获取所有元数据字段 |
| API Offset 限制导致下载不完整 | Phase 2: 排行榜下载核心 | 验证月榜(1500+ 张)能完整下载 |
| 缺乏错误恢复和状态持久化 | Phase 2: 排行榜下载核心 | kill 程序后重新运行能从中断处继续 |

## Sources

- [gallery-dl GitHub Issues](https://github.com/mikf/gallery-dl/issues) - 大量用户报告的 OAuth、Rate Limit、API 错误
- [Pixiv OAuth Flow Gist](https://gist.github.com/ZipFile/c9ebedb224406f4f11845ab700124362) - OAuth 实现细节和常见问题
- [Pixiv API Rate Limit Issue #535](https://github.com/mikf/gallery-dl/issues/535) - Rate Limit 处理策略
- [Pixiv API Offset Limit Issue #7082](https://github.com/mikf/gallery-dl/issues/7082) - API offset 限制问题
- [Pixiv 429 Error on Suspended Accounts Issue #7990](https://github.com/mikf/gallery-dl/issues/7990) - 已封禁账号导致 429 错误
- [Reddit: Help Getting Gallery-dl Working With Pixiv](https://www.reddit.com/r/DataHoarder/comments/1hyx7hq/help_getting_gallerydl_working_with_pixiv/) - 用户体验问题
- [Web Scraping Rate Limit Best Practices 2026](https://scrape.do/blog/web-scraping-rate-limit/) - 通用的 rate limit 处理策略

---
*Pitfalls research for: Pixiv 排行榜下载器*
*Researched: 2026-02-24*
