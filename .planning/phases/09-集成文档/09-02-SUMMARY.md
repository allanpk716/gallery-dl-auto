---
phase: 09-集成文档
plan: 02
subsystem: documentation
tags: [cli, integration, examples, subprocess]

# Dependency graph
requires:
  - phase: 08.1-cli-api-enhancement
    provides: CLI API 实现,包含 --json-help、--json-output、--quiet、--verbose 参数
  - phase: 09-集成文档
    plan: 01
    provides: INTEGRATION.md 基础文档结构和 CLI 调用方式章节
provides:
  - 完整的命令行调用示例(5个场景)
  - 完整的 Python 调用示例(5个模式)
  - 可直接使用的集成代码片段
affects: [third-party-integration, automation, batch-processing]

# Tech tracking
tech-stack:
  added: []
  patterns: [subprocess-integration, json-api-consumption, error-handling-patterns]

key-files:
  created: []
  modified:
    - INTEGRATION.md

key-decisions:
  - "Python 示例全部使用 subprocess 调用方式(符合 09-CONTEXT.md 决策)"
  - "错误处理示例包含超时、文件未找到、JSON 解析错误等完整场景"
  - "批量下载示例包含速率限制保护(time.sleep(2))"

patterns-established:
  - "subprocess.run(capture_output=True, text=True) 标准调用模式"
  - "JSON 输出解析优先使用 --json-output 参数"
  - "错误处理函数返回 (returncode, output_dict, error_message) 三元组"

requirements-completed: [DOCS-02]

# Metrics
duration: 5min
completed: 2026-02-26
---

# Phase 09 Plan 02: 示例代码章节 Summary

**完整的 CLI 集成示例代码,包含命令行调用和 Python subprocess 调用两种方式,覆盖获取帮助、下载、配置管理、token 管理、批量任务等常见集成场景**

## Performance

- **Duration:** 5 min
- **Started:** 2026-02-26T07:01:12Z
- **Completed:** 2026-02-26T07:06:03Z
- **Tasks:** 2
- **Files modified:** 1

## Accomplishments
- 完整的命令行调用示例,覆盖 5 大场景(帮助、下载、配置、token、批量)
- 完整的 Python 调用示例,使用 subprocess 模块
- 包含错误处理、JSON 解析、元数据获取、批量下载等完整模式
- 所有示例代码可直接运行,语法正确

## Task Commits

Each task was committed atomically:

1. **Task 1: 编写命令行调用示例** - `d702f92` (docs)
2. **Task 2: 编写 Python 调用示例** - `ae39415` (docs)

## Files Created/Modified
- `INTEGRATION.md` - 添加完整的示例代码章节(命令行 + Python)

## Decisions Made
- Python 示例全部使用 subprocess 调用方式,符合 09-CONTEXT.md 中"不提供 Python SDK,仅使用 subprocess"的决策
- 错误处理示例包含超时、文件未找到、JSON 解析等完整场景,提供健壮的集成参考
- 批量下载示例包含 time.sleep(2) 速率限制保护,避免触发 API 限制

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered
None

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- 示例代码章节完成,INTEGRATION.md 文档主体完整
- 准备执行 09-03: 添加退出码参考和最佳实践章节

## Self-Check: PASSED
- INTEGRATION.md: FOUND
- Task 1 commit (d702f92): FOUND
- Task 2 commit (ae39415): FOUND
- SUMMARY.md: FOUND

---
*Phase: 09-集成文档*
*Completed: 2026-02-26*
