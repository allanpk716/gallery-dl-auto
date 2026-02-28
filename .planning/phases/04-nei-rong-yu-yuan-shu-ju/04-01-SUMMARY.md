---
phase: 04-nei-rong-yu-yuan-shu-ju
plan: 01
subsystem: data-modeling
tags: [pydantic, pathvalidate, metadata, path-template, validation]

requires: []
provides:
  - Pydantic 元数据模型 (ArtworkMetadata, ArtworkStatistics, ArtworkTag)
  - 路径模板系统 (PathTemplate 类)
  - 结构化元数据基础设施
affects: [04-02, 04-03]

tech-stack:
  added: [pydantic>=2.12.0, pathvalidate>=3.0.0]
  patterns:
    - Pydantic v2 BaseModel with ConfigDict
    - Optional fields using str | None = None syntax
    - from_attributes=True for pixivpy3 object compatibility
    - Path template with variable substitution and sanitization

key-files:
  created:
    - src/gallery_dl_auo/models/__init__.py
    - src/gallery_dl_auo/models/artwork.py
    - src/gallery_dl_auo/utils/path_template.py
    - tests/models/__init__.py
    - tests/models/test_artwork.py
    - tests/utils/test_path_template.py
  modified:
    - pyproject.toml

key-decisions:
  - "使用 Pydantic v2 (而非 dataclasses) - 提供自动验证、序列化和类型强制"
  - "使用 pathvalidate (而非手动实现) - 处理所有边界情况,跨平台更可靠"
  - "简单字符串模板 {var} (而非 Jinja2) - 降低复杂度,满足当前需求"
  - "缺失模板变量替换为 'unknown' (而非抛出错误) - 提供更友好的用户体验"

patterns-established:
  - "Pydantic 嵌套模型: ArtworkMetadata 包含 list[ArtworkTag] 和 ArtworkStatistics"
  - "可选字段使用 str | None = None (Python 3.10+ 语法)"
  - "启用 from_attributes=True 支持从 pixivpy3 对象构建"
  - "路径模板返回 Path 对象,与 pathlib 集成"
  - "所有路径通过 sanitize_filepath() 清理,自动处理 Windows 非法字符"

requirements-completed: [CONT-02, CONT-03, CONT-04]

duration: 5min
completed: 2026-02-25
---

# Phase 04 Plan 01: 元数据建模和路径模板系统

**Pydantic 元数据模型和路径模板系统 - 为 Phase 4 提供结构化的元数据基础设施**

## Performance

- **Duration:** 5 min
- **Started:** 2026-02-25T03:42:11Z
- **Completed:** 2026-02-25T03:47:07Z
- **Tasks:** 2
- **Files modified:** 6 (created 6, modified 1)

## Accomplishments
- 建立 Pydantic 元数据模型体系,支持结构化存储作品标签和统计数据
- 实现路径模板系统,支持变量替换和跨平台路径清理
- 所有模型支持从 pixivpy3 对象构建,为后续集成做好准备

## Task Commits

Each task was committed atomically:

1. **Task 1: 创建 Pydantic 元数据模型** - `e2d4f01` (feat)
   - pydantic>=2.12.0 and pathvalidate>=3.0.0 dependencies
   - ArtworkMetadata, ArtworkStatistics, ArtworkTag models
   - 6 comprehensive tests

2. **Task 2: 实现路径模板系统** - `1561059` (feat)
   - PathTemplate class with variable substitution
   - Support 6 template variables
   - 5 comprehensive tests

**Plan metadata:** (pending commit)

_Note: All commits follow conventional commit format_

## Files Created/Modified
- `pyproject.toml` - Added pydantic and pathvalidate dependencies
- `src/gallery_dl_auo/models/__init__.py` - Models package init with exports
- `src/gallery_dl_auo/models/artwork.py` - Pydantic models for metadata
- `src/gallery_dl_auo/utils/path_template.py` - Path template system
- `tests/models/__init__.py` - Test package init
- `tests/models/test_artwork.py` - Model tests (6 tests)
- `tests/utils/test_path_template.py` - Template tests (5 tests)

## Decisions Made
- **Pydantic v2 over dataclasses:** Chose Pydantic for automatic validation, serialization, and type coercion. Provides better integration with pixivpy3 objects via from_attributes.
- **pathvalidate over manual implementation:** Standard library handles all edge cases (Windows reserved names, length limits, encoding issues) better than custom regex.
- **Simple string templates over Jinja2:** Current requirements only need variable substitution. Avoids over-engineering and reduces complexity.
- **"unknown" for missing variables:** Graceful degradation instead of errors, providing better user experience when template variables are unavailable.

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None - implementation followed research patterns closely.

## User Setup Required

None - no external service configuration required. Dependencies are installed automatically via pip.

## Next Phase Readiness

**Ready for Wave 2 (04-02):**
- Pydantic models available for PixivClient.get_artwork_metadata() return type
- from_attributes=True enables direct construction from pixivpy3 objects
- Models support serialization via model_dump() and model_dump_json()

**Ready for Wave 3 (04-03):**
- PathTemplate class ready for integration into RankingDownloader
- Template supports all required variables (mode, date, illust_id, title, author, author_id)
- Path sanitization handles Windows illegal characters automatically

**No blockers or concerns.**

---
*Phase: 04-nei-rong-yu-yuan-shu-ju*
*Completed: 2026-02-25*
