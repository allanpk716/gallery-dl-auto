# Phase 8: CLI API 增强 - Context

**Gathered:** 2026-02-26
**Status:** Ready for planning

<domain>
## Phase Boundary

提供完整的第三方 CLI 集成 API 接口，包括结构化帮助信息、静默模式和统一 JSON 输出。这是为了让第三方工具能够可靠地调用和解析 gallery-dl-auto 的输出。不包括新功能开发，仅涉及输出格式和接口的标准化。

</domain>

<decisions>
## Implementation Decisions

### --json-help 输出结构

- **元数据范围**:
  - 包含完整元数据：命令名称、描述、所有参数、类型、默认值
  - 每个参数包含：name, type, required, default_value, description
  - 提供足够的信息供第三方工具自动生成调用代码

- **字段命名**:
  - 使用 snake_case 命名风格
  - 与项目现有的 Python 代码风格保持一致
  - 例如：command_name, parameter_type, default_value

- **示例代码**:
  - 在 JSON 帮助信息中包含调用示例
  - 每个命令至少提供一个基本调用示例
  - 方便开发者快速上手和验证

- **命令范围**:
  - 返回所有命令的完整元数据
  - 一次性获取所有命令信息，便于第三方工具索引和展示
  - 不需要逐个命令查询

### --quiet 与 --json-output 关系

- **行为差异**:
  - --quiet: 仅抑制进度和日志输出，保持最终结果输出
  - --json-output: 确保所有输出（包括错误）都是有效的 JSON 格式
  - 两个参数功能不同，互为补充

- **默认行为**:
  - 无参数时默认显示进度和文本日志
  - 默认为用户友好的交互式输出
  - 使用参数切换到静默/JSON 模式

- **组合使用**:
  - 允许同时使用 --quiet 和 --json-output
  - 组合效果：静默模式 + 确保 JSON 格式（包括错误）
  - 适合第三方工具的纯 JSON 输出需求

- **静默范围**:
  - --quiet 完全静默：抑制所有进度、日志、警告输出
  - 仅保留最终结果输出
  - 错误信息也会被抑制（仅记录到日志文件）

### 错误 JSON 格式化

- **错误结构**:
  - 使用统一的错误结构：success=false + error_code + message + details
  - 所有错误都遵循相同的 JSON schema
  - 便于第三方工具统一处理

- **调试信息**:
  - 包含堆栈跟踪和详细调试信息
  - 方便开发者在集成阶段排查问题
  - 堆栈跟踪放在 details 字段中

- **错误码设计**:
  - 使用字符串错误码，例如 "AUTH_FAILED", "NETWORK_ERROR"
  - 便于理解和记忆，提高可读性
  - 错误码应该是常量，具有描述性

- **错误位置**:
  - 使用 --json-output 时，错误信息输出到 stdout
  - 确保第三方工具能够统一捕获所有输出
  - 不区分 stdout 和 stderr，统一为 JSON 格式

### 参数组合和冲突处理

- **冲突检测**:
  - 严格检测不兼容的参数组合
  - 检测到冲突时立即报错并拒绝执行
  - 不进行隐式的参数调整

- **错误提示**:
  - 明确指出哪些参数冲突
  - 提供修复建议（例如："--verbose 不能与 --quiet 同时使用，请移除其中一个"）
  - 帮助用户快速理解和解决问题

- **优先级规则**:
  - 根据参数类型确定优先级（类型优先级）
  - 不依赖参数的顺序
  - 确保行为可预测和一致

- **优先级顺序**:
  - --json-output > --quiet > --verbose
  - JSON 输出优先级最高，确保输出格式的一致性
  - 例如：同时使用 --json-output 和 --verbose 时，输出为 JSON 格式，不显示详细日志

### Claude's Discretion

- JSON schema 的精确定义和字段类型
- 错误码的具体枚举值和分类
- 堆栈跟踪的格式化和敏感信息过滤
- 参数冲突检测的具体实现逻辑
- 示例代码的格式和内容组织

</decisions>

<specifics>
## Specific Ideas

- "JSON 帮助信息应该像 OpenAPI 规范一样完整，让工具能自动生成客户端代码"
- "错误输出应该像 Elasticsearch 的错误响应一样，结构清晰且包含调试信息"
- "参数优先级应该明确且可预测，像 curl 的参数处理一样直观"
- "第三方工具调用时应该像调用 API 一样简单，输出格式完全标准化"

</specifics>

<deferred>
## Deferred Ideas

- 参数别名支持（例如 -q 作为 --quiet 的简写）- 可作为后续优化
- JSON 输出版本控制（例如 --json-output=v2）- 未来 API 演进时考虑
- 自定义 JSON 输出字段（例如 --json-fields=command,result）- 增加复杂度
- 错误码到 HTTP 状态码的映射 - 可在文档中说明
- 参数交互式的配置向导 - 超出 CLI API 增强范围

---

*Phase: 08-CLI-API-增强*
*Context gathered: 2026-02-26*
