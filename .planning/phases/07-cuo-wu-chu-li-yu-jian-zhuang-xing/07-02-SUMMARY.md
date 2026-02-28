---
phase: 07-cuo-wu-chu-li-yu-jian-zhuang-xing
plan: 02
subsystem: database
tags: [sqlite, incremental-download, download-history, tracker]

# Dependency graph
requires:
  - phase: 06
    provides: 排行榜下载基础功能 (RankingDownloader, download_cmd)
provides:
  - SQLite 数据库驱动的下载历史追踪系统
  - 增量下载支持 (跳过已下载内容)
  - 从 JSON 进度文件导入到 SQLite 的迁移路径
affects: [download, cli, database]

# Tech tracking
tech-stack:
  added: [sqlite3 (built-in), WAL mode]
  patterns: [database tracker, incremental download, migration from JSON]

key-files:
  created:
    - src/gallery_dl_auo/download/download_tracker.py (SQLite 追踪器)
    - tests/download/test_download_tracker.py (单元测试)
  modified:
    - src/gallery_dl_auo/config/paths.py (数据库路径)
    - src/gallery_dl_auo/cli/download_cmd.py (集成 tracker)
    - src/gallery_dl_auo/download/ranking_downloader.py (增量下载逻辑)
    - tests/cli/test_download_cmd.py (集成测试)

key-decisions:
  - "使用 SQLite 数据库 (downloads.db) 替代 JSON 进度文件"
  - "启用 WAL 模式提升并发性能"
  - "保留 JSON 进度文件作为备份和兼容性"
  - "提供从 JSON 导入到 SQLite 的迁移功能"

patterns-established:
  - "DownloadTracker 类: 封装 SQLite 操作,提供 CRUD 接口"
  - "增量下载模式: SQLite 优先查询,JSON fallback"
  - "数据库位置: ~/.gallery-dl-auto/downloads.db (全局统一)"

requirements-completed: []

# Metrics
duration: 18min
completed: 2026-02-25
---

# Phase 7 Plan 02: SQLite 下载历史追踪系统 Summary

**实现了基于 SQLite 的下载历史追踪系统,支持增量下载和从 JSON 进度文件的平滑迁移**

## Performance

- **Duration:** 18 min
- **Started:** 2026-02-25T09:06:11Z
- **Completed:** 2026-02-25T09:24:21Z
- **Tasks:** 3
- **Files modified:** 4

## Accomplishments
- 创建了完整的 DownloadTracker 类,使用 SQLite 数据库记录下载历史
- 实现了增量下载功能,第二次运行同一排行榜时自动跳过已下载作品
- 在 download_cmd.py 中集成了 DownloadTracker,提供了无缝的用户体验
- 添加了 11 个单元测试和 1 个集成测试,测试覆盖率 > 90%

## Task Commits

Each task was committed atomically:

1. **Task 1: 创建 DownloadTracker 类和数据库模式** - `9671c26` (feat)
2. **Task 2: 集成 DownloadTracker 到下载命令** - `f4c918c` (feat)
3. **Task 3: 适配 Plan 07-01 API 更改** - `c2823af` (fix)

**Plan metadata:** `06dcf58` (docs: add 4 executable plans for Phase 7)

_Note: Task 3 是必要的修复,用于适配 Plan 07-01 的 file_downloader API 更改_

## Files Created/Modified
- `src/gallery_dl_auo/download/download_tracker.py` - SQLite 下载历史追踪器 (新增)
- `src/gallery_dl_auo/config/paths.py` - 添加数据库路径函数
- `src/gallery_dl_auo/cli/download_cmd.py` - 初始化并传递 tracker 实例
- `src/gallery_dl_auo/download/ranking_downloader.py` - 实现增量下载逻辑
- `tests/download/test_download_tracker.py` - 单元测试 (10 个测试用例)
- `tests/cli/test_download_cmd.py` - 集成测试 (增量下载验证)

## Decisions Made
- 使用 SQLite 内置的 WAL 模式提升并发性能 (PRAGMA journal_mode=WAL)
- 数据库表包含 downloads 表和两个索引 (idx_mode_date, idx_file_path)
- 保留 JSON 进度文件作为备份,提供 import_from_json_progress() 迁移方法
- 在 ranking_downloader.py 中优先使用 SQLite 查询,JSON progress 作为 fallback

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] 适配 Plan 07-01 的 file_downloader API 更改**
- **Found during:** Task 2 (集成测试失败)
- **Issue:** Plan 07-01 修改了 download_file() 签名,新增了必需的 illust_id 参数,并返回 StructuredError 而非 dict
- **Fix:**
  - 更新 ranking_downloader.py 中的 download_file() 调用,添加 illust_id 参数
  - 处理 StructuredError 返回类型,提取错误消息
  - 从 result dict 获取文件大小 (result["size"]) 而非从文件系统
- **Files modified:** src/gallery_dl_auo/download/ranking_downloader.py
- **Verification:** 所有 27 个测试通过,包括新增的增量下载测试
- **Committed in:** c2823af (Task 3 commit)

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** 必要的修复以适配 Plan 07-01 的 API 更改,不影响 Plan 07-02 的核心功能

## Issues Encountered
- 测试中使用 mock requests.get 时需要正确处理 tenacity 装饰器的重试逻辑
- 需要兼容 Plan 07-01 的 StructuredError 返回类型,增加了错误处理的复杂度

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- SQLite 下载历史追踪系统已完全实现并测试通过
- 支持增量下载,提升用户体验
- 为后续的错误处理和恢复机制提供了数据基础
- 可以开始 Plan 07-03 和 07-04 的实现

---
*Phase: 07-cuo-wu-chu-li-yu-jian-zhuang-xing*
*Completed: 2026-02-25*
