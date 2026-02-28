---
phase: 05-json-output
plan: 01
subsystem: output
tags: [pydantic, json, cli, error-handling]

# Dependency graph
requires:
  - phase: 04
    provides: 元数据模型和路径模板系统
provides:
  - 标准化 JSON 输出模型 (DownloadOutput, ErrorDetail, DownloadSuccessData)
  - 标准化错误码枚举 (ErrorCode)
  - 一致的 CLI 输出格式
affects: [download, refresh, error-handling, json-output]

# Tech tracking
tech-stack:
  added: []
  patterns:
    - Pydantic v2 model_dump_json() for serialization
    - exclude_none=True pattern for cleaner output
    - ErrorCode str+Enum pattern for string serialization

key-files:
  created:
    - src/gallery_dl_auo/models/output.py
    - src/gallery_dl_auo/utils/error_codes.py
  modified:
    - src/gallery_dl_auo/models/__init__.py
    - src/gallery_dl_auo/utils/__init__.py

key-decisions:
  - "使用 Pydantic v2 的 model_dump_json() 方法而非 json.dumps(model_dump()) (更简洁)"
  - "exclude_none=True 避免成功响应中出现 'error': null (更简洁)"
  - "ErrorCode 继承 str 和 Enum 确保序列化时输出字符串 (如 'AUTH_TOKEN_NOT_FOUND' 而非 1)"
  - "错误码按模块分组 (AUTH_, API_, FILE_, DOWNLOAD_, INVALID_, INTERNAL_)"

patterns-established:
  - "标准化输出结构: success + data (成功时) 或 success + error (失败时)"
  - "错误码命名规范: {模块}_{错误类型}"
  - "所有字符串字段使用 str 类型,Pydantic 自动处理序列化"

requirements-completed: [OUTP-01, OUTP-02, OUTP-03, OUTP-04]

# Metrics
duration: 10min
completed: 2026-02-25
---

# Phase 05: JSON 输出 Summary

**标准化输出模型和错误码系统,为所有 CLI 命令提供一致的 JSON 输出格式**

## Performance

- **Duration:** 10 min
- **Started:** 2026-02-25T12:00:00Z
- **Completed:** 2026-02-25T12:10:00Z
- **Tasks:** 2
- **Files modified:** 4

## Accomplishments
- 创建了完整的输出模型体系 (DownloadOutput, ErrorDetail, DownloadSuccessData)
- 定义了覆盖所有错误场景的错误码枚举 (17 个错误码,6 个模块)
- 实现了 exclude_none=True 模式,确保输出简洁
- 验证了枚举序列化为字符串 (ErrorCode.AUTH_TOKEN_NOT_FOUND → "AUTH_TOKEN_NOT_FOUND")

## Task Commits

Each task was committed atomically:

1. **Task 1: 创建标准化输出模型和错误码** - `7733cb0` (feat)
2. **Task 2: 导出模型和错误码** - `c3066e3` (chore)

## Files Created/Modified
- `src/gallery_dl_auo/models/output.py` - 标准化输出模型 (DownloadOutput, ErrorDetail, DownloadSuccessData)
- `src/gallery_dl_auo/utils/error_codes.py` - 错误码枚举 (17 个错误码)
- `src/gallery_dl_auo/models/__init__.py` - 导出输出模型
- `src/gallery_dl_auo/utils/__init__.py` - 导出错误码枚举

## Decisions Made
1. **使用 Pydantic v2 的 model_dump_json() 方法** - 比手动 json.dumps(model_dump()) 更简洁
2. **exclude_none=True 配置** - 成功响应不包含 "error": null,错误响应不包含 "data": null
3. **ErrorCode 继承 str + Enum** - 确保序列化时输出字符串而非数字
4. **错误码按模块分组** - AUTH_, API_, FILE_, DOWNLOAD_, INVALID_, INTERNAL_

## Deviations from Plan

None - plan executed exactly as written

## Issues Encountered
None

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- 输出模型和错误码系统已完成,可以集成到 download 和 refresh 命令
- 下一个计划 (05-02) 将更新 CLI 命令使用这些模型

---
*Phase: 05-json-output*
*Completed: 2026-02-25*
