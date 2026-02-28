# Phase 9: 集成文档 - Context

**Gathered:** 2026-02-26
**Status:** Ready for planning

<domain>
## Phase Boundary

为第三方开发者提供完整的集成指南和参考文档,包括 INTEGRATION.md 文档、调用示例代码和退出码文档。文档阶段不涉及代码实现,专注于文档编写和示例代码的组织。INTEGRATION.md、示例代码和退出码文档是此阶段的全部交付物。

</domain>

<decisions>
## Implementation Decisions

### 文档结构
- 采用单一 INTEGRATION.md 文件,所有内容整合在一起
- 包含调用方式、参数说明、最佳实践、示例代码和退出码文档
- 便于查阅和维护,避免文档分散

### 示例代码覆盖
- 以命令行调用示例为主,Python 调用示例为辅
- 重点展示 CLI 的 --json-help、--quiet、--json-output 等参数的使用
- 包含如何解析 JSON 输出的示例
- Python 示例使用 subprocess 调用方式

### 文档深度和语气
- 简洁专业的风格,面向有经验的开发者
- 假设开发者熟悉 CLI 工具集成
- 重点说明 API 规范、参数说明和注意事项
- 减少基础说明和手把手教程

### 退出码文档格式
- 在 INTEGRATION.md 中用表格形式呈现
- 列出所有退出码及其含义
- 便于开发者快速查阅和理解

### Claude's Discretion
- INTEGRATION.md 的具体章节组织结构
- 示例代码的详细场景选择(哪些常见场景需要示例)
- 文档的具体措辞和排版格式
- Python 示例的详细程度

</decisions>

<specifics>
## Specific Ideas

- 文档目标受众是需要集成 gallery-dl-auto 的第三方开发者
- CLI 是主要集成方式,应该重点展示
- 退出码文档应该便于自动化流程判断执行状态
- 文档应该让开发者能够快速上手,不需要阅读大量内容

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 09-集成文档*
*Context gathered: 2026-02-26*
