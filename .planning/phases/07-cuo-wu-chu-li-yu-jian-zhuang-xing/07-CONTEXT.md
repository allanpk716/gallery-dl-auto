# Phase 7: 错误处理与健壮性 - Context

**Gathered:** 2026-02-25
**Status:** Ready for planning

<domain>
## Phase Boundary

为 Pixiv 排行榜下载器添加健壮的错误处理和增量下载能力。包括:处理网络错误和权限错误、跳过已下载内容、支持从中断点恢复下载。不改变现有功能,只增强健壮性和可靠性。

</domain>

<decisions>
## Implementation Decisions

### 错误处理策略
- 网络请求失败时重试 3 次,使用指数退避策略(1秒、2秒、3秒)
- 错误消息友好且详细:显示错误类型 + 建议操作 + 原始错误信息
- 记录错误日志到文件,包含时间戳、错误类型、上下文信息

### 增量下载检测
- Claude 决定最佳的文件检测方式
- 使用 SQLite 数据库维护下载记录(作品 ID、文件路径等)
- 使用临时文件 + 重命名机制处理部分下载的文件,避免不完整文件

### 断点续传机制
- 使用 JSON 状态文件存储断点状态
- 状态包含:当前下载位置(作品 ID、索引位置、已下载数量)
- 程序重新运行时自动从断点继续,无需手动指定参数

### 错误恢复行为
- 关键错误(如认证失败、配置错误)终止程序
- Claude 决定权限错误的处理方式
- Claude 决定跳过失败项目时的通知方式

### JSON 错误输出
- **重要**:本项目面向第三方程序调用,所有错误通过 JSON 格式返回
- JSON 错误响应包含结构化错误对象:错误类型、错误消息、作品 ID、建议操作
- 批量下载部分成功时,返回成功和失败的项目列表,包含错误详情
- 更新 help 命令以反映新的错误处理功能

### Claude's Discretion
- 文件检测的最佳实现方式(文件名匹配 vs 内容验证)
- 权限错误的处理策略(终止 vs 跳过)
- 跳过失败项目时的通知方式(终端显示 vs 静默日志)
- 日志文件的位置和命名约定

</decisions>

<specifics>
## Specific Ideas

- "因为本项目是打算给第三方程序调用的,CLI 方式,如果有错误希望能够跟之前的命令一样,返回 JSON 便于第三方解析"
- "记得更新 help 命令"
- 与 Phase 6 保持一致的 JSON 输出风格

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 07-cuo-wu-chu-li-yu-jian-zhuang-xing*
*Context gathered: 2026-02-25*
