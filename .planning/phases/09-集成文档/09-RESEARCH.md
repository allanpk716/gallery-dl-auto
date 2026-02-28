# Phase 9: 集成文档 - Research

**Researched:** 2026-02-26
**Domain:** 技术文档编写、CLI 工具集成指南、示例代码编写
**Confidence:** HIGH

## Summary

Phase 9 是一个文档编写阶段,目标是为第三方开发者提供完整的集成指南和参考文档。该阶段需要创建 INTEGRATION.md 文档,包含 CLI 调用方式、参数说明、最佳实践、Python 和命令行调用示例代码,以及完整的退出码文档。Phase 8.1 已经完成了所有 CLI API 功能的实现(--json-help, --quiet, --json-output),为本阶段的文档编写提供了完整的技术基础。

文档面向有经验的开发者,需要简洁专业的风格,重点说明 API 规范、参数说明和注意事项,避免冗长的基础说明。INTEGRATION.md 是此阶段的唯一交付物(包含示例代码和退出码文档),所有内容整合在一起便于查阅和维护。

**Primary recommendation:** 创建单一的 INTEGRATION.md 文档,采用命令行调用示例为主、Python 调用示例为辅的方式,重点展示 --json-help、--quiet、--json-output 等 CLI API 参数的使用,包含完整的退出码表格和常见集成场景的示例代码。

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions
- **文档结构:** 采用单一 INTEGRATION.md 文件,所有内容整合在一起,包含调用方式、参数说明、最佳实践、示例代码和退出码文档,便于查阅和维护,避免文档分散
- **示例代码覆盖:** 以命令行调用示例为主,Python 调用示例为辅,重点展示 CLI 的 --json-help、--quiet、--json-output 等参数的使用,包含如何解析 JSON 输出的示例,Python 示例使用 subprocess 调用方式
- **文档深度和语气:** 简洁专业的风格,面向有经验的开发者,假设开发者熟悉 CLI 工具集成,重点说明 API 规范、参数说明和注意事项,减少基础说明和手把手教程
- **退出码文档格式:** 在 INTEGRATION.md 中用表格形式呈现,列出所有退出码及其含义,便于开发者快速查阅和理解

### Claude's Discretion
- INTEGRATION.md 的具体章节组织结构
- 示例代码的详细场景选择(哪些常见场景需要示例)
- 文档的具体措辞和排版格式
- Python 示例的详细程度

### Deferred Ideas (OUT OF SCOPE)
None — discussion stayed within phase scope
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| DOCS-01 | 开发者可以查阅 INTEGRATION.md 文档了解如何作为第三方工具集成(包含调用方式、参数说明、最佳实践) | Phase 8.1 已实现完整的 CLI API (--json-help, --quiet, --json-output),提供了 JSON 帮助系统、静默模式和 JSON 输出模式,所有命令已通过集成测试验证一致性。文档需要说明这些参数的使用方式和适用场景。 |
| DOCS-02 | 开发者可以参考 Python 和命令行调用示例代码(包含常见场景的完整示例) | Phase 8.1 提供了完整的 CLI API 基础,可以使用 --json-help 获取命令元数据,使用 --quiet 静默输出,使用 --json-output 确保 JSON 格式。示例代码应展示如何获取帮助、调用命令、解析输出、处理错误。 |
| DOCS-03 | 开发者可以查阅完整的退出码文档,了解每个退出码的含义和使用场景(便于自动化流程判断执行状态) | error_codes.py 定义了 20 个标准化错误码,分为认证(AUTH_*)、API(API_*)、文件系统(FILE_*)、下载(DOWNLOAD_*)、元数据(METADATA_*)、参数(INVALID_*)和内部错误(INTERNAL_*)类别。文档需要用表格列出所有错误码及其含义、使用场景。 |

</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| Markdown | N/A | 文档格式 | 项目使用 Markdown 编写所有文档(ROADMAP.md, REQUIREMENTS.md, CONTEXT.md),保持一致性 |
| Python | 3.10+ | 示例代码语言 | 项目使用 Python 编写,Python 调用示例符合目标受众需求 |
| subprocess | 3.10+ | CLI 调用方式 | Python 标准库,无需额外依赖,符合"Python 示例使用 subprocess 调用方式"的决策 |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| json | 3.10+ | JSON 输出解析 | 示例代码中展示如何解析 --json-output 的输出 |
| shlex | 3.10+ | 命令行参数引用 | Python 示例代码中展示安全的参数传递 |

### Alternatives Considered
无需替代方案 — 本阶段是文档编写,不涉及新功能开发。

**Installation:**
无新依赖需要安装。

## Architecture Patterns

### Recommended Project Structure
```
docs/
├── INTEGRATION.md         # 唯一交付物: 集成文档
└── (无其他文件)           # 所有内容整合在 INTEGRATION.md 中
```

### Pattern 1: 文档章节结构
**What:** INTEGRATION.md 的标准章节组织
**When to use:** 创建集成文档时
**Example:**
```markdown
# 集成指南

## 概述
- 工具简介和适用场景
- 集成方式概述

## CLI 调用方式
- 基本命令格式
- 全局参数说明
- 参数优先级

## JSON API
- --json-help 获取命令元数据
- --quiet 静默模式
- --json-output JSON 输出模式

## 示例代码
### 命令行调用
- 获取帮助
- 下载排行榜
- 查询配置

### Python 调用
- 基本调用模式
- 解析 JSON 输出
- 错误处理

## 退出码参考
- 退出码表格(所有 20 个错误码)
- 退出码分类说明
- 使用场景示例

## 最佳实践
- 参数选择建议
- 错误处理建议
- 性能优化建议
```

### Pattern 2: 示例代码模式
**What:** 展示 CLI 调用的标准方式
**When to use:** 编写示例代码时
**Example:**
```bash
# 命令行示例
pixiv-downloader --json-help | jq .

# Python 示例
import subprocess
import json

result = subprocess.run(
    ["pixiv-downloader", "--json-output", "download", "--type", "daily"],
    capture_output=True,
    text=True
)
output = json.loads(result.stdout)
```

### Anti-Patterns to Avoid
- **冗长的教程:** 开发者熟悉 CLI 工具,不需要手把手指导,直接展示参数和示例即可
- **分散的文档:** 不要创建多个文档文件(INTEGRATION.md, EXAMPLES.md, ERROR_CODES.md),所有内容整合在一起
- **过度详细的 Python 示例:** Python 示例应该是辅助性的,不要深入讲解 Python 错误处理细节
- **忽略错误处理:** 示例代码应该包含基本的错误处理,但不需要过于复杂

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| 命令元数据获取 | 手动编写命令列表 | --json-help API | Phase 8.1 已实现,动态获取保证准确性 |
| 退出码列表 | 手动编写退出码表格 | 从 error_codes.py 提取 | 确保退出码文档与代码一致 |
| JSON 输出示例 | 手动编写 JSON 格式 | 实际运行命令获取输出 | 真实示例比虚构示例更可靠 |

**Key insight:** 文档应该基于 Phase 8.1 已实现的功能编写,不要假设或虚构 API 行为。所有示例应该是可运行的、经过验证的。

## Common Pitfalls

### Pitfall 1: 文档与实际 API 不一致
**What goes wrong:** 文档描述的参数或行为与实际 CLI 不符,导致开发者集成失败
**Why it happens:** 文档编写时未实际运行命令验证,或者文档未随代码更新
**How to avoid:**
1. 所有示例代码必须是实际运行过的命令
2. 参数说明必须基于 --json-help 输出
3. 退出码列表必须基于 error_codes.py 定义
4. 编写完成后运行集成测试验证示例

**Warning signs:**
- 文档中的命令参数与 --json-help 输出不符
- 示例代码无法运行
- 退出码列表不完整或有拼写错误

### Pitfall 2: 过度详细的教程
**What goes wrong:** 文档过于冗长,包含大量基础说明,有经验的开发者难以快速找到关键信息
**Why it happens:** 假设开发者不熟悉 CLI 工具,编写了过多的背景知识
**How to avoid:**
1. 遵循"简洁专业的风格"决策
2. 假设开发者熟悉 CLI 工具集成
3. 重点说明 API 规范、参数说明和注意事项
4. 减少基础说明和手把手教程
5. 使用表格和代码块提高信息密度

**Warning signs:**
- 文档超过 500 行
- 包含"什么是 CLI"之类的入门内容
- 段落文字多于代码和表格

### Pitfall 3: 示例代码不可运行
**What goes wrong:** 示例代码包含拼写错误、缺少必要参数或使用已废弃的功能
**Why it happens:** 示例代码是手动编写的,未经测试验证
**How to avoid:**
1. 所有命令行示例必须实际运行并复制输出
2. 所有 Python 代码必须实际测试
3. 使用真实的命令输出而非虚构的示例
4. 编写完成后运行所有示例验证

**Warning signs:**
- 示例中的 JSON 输出格式看起来不对
- 命令参数拼写错误
- Python 代码缺少必要的 import

### Pitfall 4: 退出码文档不完整或不准确
**What goes wrong:** 退出码列表缺少某些错误码,或者含义描述不准确
**Why it happens:** 手动编写退出码列表,未基于 error_codes.py 提取
**How to avoid:**
1. 从 error_codes.py 中提取所有错误码
2. 确保所有 20 个错误码都包含在文档中
3. 错误码分类清晰(AUTH_*, API_*, FILE_*, DOWNLOAD_*, METADATA_*, INVALID_*, INTERNAL_*)
4. 每个错误码的含义描述基于代码注释

**Warning signs:**
- 退出码表格少于 20 行
- 错误码命名与 error_codes.py 不符
- 缺少某些类别的错误码

## Code Examples

Verified patterns from official sources:

### 命令行调用示例
```bash
# 获取所有命令的 JSON 帮助
pixiv-downloader --json-help

# 静默模式下下载排行榜
pixiv-downloader --quiet download --type daily --date 2026-02-25

# JSON 输出模式下下载排行榜
pixiv-downloader --json-output download --type daily --date 2026-02-25

# 参数优先级: --json-output > --quiet > --verbose
pixiv-downloader --json-output --quiet --verbose download --type daily
```

来源: Phase 8.1 SUMMARY.md

### Python 调用示例
```python
import subprocess
import json

# 基本调用模式
result = subprocess.run(
    ["pixiv-downloader", "--json-output", "download", "--type", "daily"],
    capture_output=True,
    text=True
)

if result.returncode == 0:
    output = json.loads(result.stdout)
    print(f"Downloaded {len(output['downloaded'])} images")
else:
    print(f"Error: {result.returncode}")
    print(result.stderr)
```

来源: CONTEXT.md "Python 示例使用 subprocess 调用方式"

### 获取命令元数据
```python
import subprocess
import json

result = subprocess.run(
    ["pixiv-downloader", "--json-help"],
    capture_output=True,
    text=True
)

metadata = json.loads(result.stdout)
for command_name, command_info in metadata.items():
    print(f"{command_name}: {command_info['description']}")
```

来源: Phase 8.1 Plan 01

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| 手写文档,手动维护 | 基于 API 自动生成部分内容 | Phase 8.1 | --json-help API 确保文档与代码一致 |
| 分散的多个文档 | 单一 INTEGRATION.md | Phase 9 | 便于查阅和维护,避免文档分散 |
| 详细的入门教程 | 简洁的 API 参考 | Phase 9 | 面向有经验的开发者,减少冗余内容 |

**Deprecated/outdated:**
- 纯文本错误码列表:被结构化表格取代
- 手动维护的命令列表:被 --json-help API 取代
- 分散的文档文件(INTEGRATION.md, EXAMPLES.md, ERROR_CODES.md):被单一 INTEGRATION.md 取代

## Open Questions

1. **INTEGRATION.md 的放置位置?**
   - What we know: 文档应该便于开发者查找
   - What's unclear: 应该放在项目根目录还是 docs/ 目录?
   - Recommendation: 放在项目根目录,与 README.md 平级,便于开发者快速找到。理由:大多数开源项目的集成文档都在根目录。

2. **是否需要包含中文和英文双语文档?**
   - What we know: 项目现有的文档(ROADMAP.md, REQUIREMENTS.md)都是中文
   - What's unclear: INTEGRATION.md 是否应该提供英文版本以支持国际开发者?
   - Recommendation: 仅中文版本,与项目其他文档保持一致。如果未来有国际开发者需求,再考虑英文版本。

3. **Python 示例的详细程度?**
   - What we know: CONTEXT.md 规定"以命令行调用示例为主,Python 调用示例为辅"
   - What's unclear: Python 示例应该包含多少错误处理和边界情况?
   - Recommendation: 基本的错误处理示例(returncode 检查,JSON 解析错误),不包含所有可能的异常情况。理由:开发者熟悉 Python,可以根据自己的需求扩展错误处理。

## Validation Architecture

> 跳过此部分 — workflow.nyquist_validation 未在 .planning/config.json 中配置,默认为 false

## Sources

### Primary (HIGH confidence)
- `.planning/phases/08.1-cli-api-enhancement/08.1-01-SUMMARY.md` - JSON 帮助系统实现细节
- `.planning/phases/08.1-cli-api-enhancement/08.1-02-SUMMARY.md` - 静默和 JSON 输出模式实现细节
- `.planning/phases/08.1-cli-api-enhancement/08.1-03-SUMMARY.md` - CLI API 集成测试验证
- `.planning/phases/09-集成文档/09-CONTEXT.md` - 文档编写决策和约束
- `src/gallery_dl_auo/utils/error_codes.py` - 退出码定义

### Secondary (MEDIUM confidence)
- `.planning/REQUIREMENTS.md` - DOCS-01, DOCS-02, DOCS-03 需求定义
- `.planning/ROADMAP.md` - Phase 9 目标和成功标准
- `src/gallery_dl_auo/cli/main.py` - CLI 参数实现

### Tertiary (LOW confidence)
- 无 — 所有信息都来自项目内部文件和 Phase 8.1 实现结果

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - 文档编写不需要技术栈,使用 Markdown 和 Python 示例即可
- Architecture: HIGH - 基于CONTEXT.md 决策和 Phase 8.1 已实现的 API
- Pitfalls: HIGH - 基于 Phase 8.1 实际实现和文档编写最佳实践

**Research date:** 2026-02-26
**Valid until:** 30 days - 文档结构和内容相对稳定,除非 CLI API 发生变化
