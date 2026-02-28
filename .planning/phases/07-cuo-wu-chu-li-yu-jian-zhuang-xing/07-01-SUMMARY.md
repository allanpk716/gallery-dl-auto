---
phase: 07-cuo-wu-chu-li-yu-jian-zhuang-xing
plan: "01"
subsystem: error-handling
tags: [tenacity, retry, exponential-backoff, atomic-file-operations, network-resilience]

# Dependency graph
requires:
  - phase: 06-多排行榜
    provides: 现有的下载功能和文件操作
provides:
  - 使用 Tenacity 的生产级别重试机制
  - 指数退避策略(1s → 2s → 3s)
  - 原子文件操作保证下载完整性
  - 网络请求和文件操作自动重试
affects: [api, download, file-operations]

# Tech tracking
tech-stack:
  added: [tenacity>=8.2.0]
  patterns: [decorator-pattern, retry-with-exponential-backoff, atomic-file-operations]

key-files:
  created: []
  modified:
    - pyproject.toml
    - src/gallery_dl_auo/download/retry_handler.py
    - src/gallery_dl_auo/api/pixiv_client.py
    - src/gallery_dl_auo/download/file_downloader.py
    - tests/download/test_retry_handler.py

key-decisions:
  - "使用 Tenacity 替代简单 for 循环重试(生产级别库,支持装饰器模式)"
  - "指数退避策略:wait_exponential(multiplier=1, min=1, max=3) 精确实现 1→2→3 秒"
  - "内部函数应用装饰器,外部函数捕获异常返回错误字典(向后兼容)"
  - "临时文件 + 重命名实现原子文件操作(保证下载完整性)"
  - "Windows 兼容:重命名前先删除已存在的目标文件"

patterns-established:
  - "装饰器模式:retry_on_network_error 和 retry_on_file_error 可复用"
  - "原子文件操作:下载到 .tmp 文件,成功后 rename,失败则 cleanup"
  - "before_sleep_log 钩子记录重试过程(WARNING 级别)"

requirements-completed: []

# Metrics
duration: 15min
completed: 2026-02-25
---

# Phase 7 Plan 01: 升级重试机制为 Tenacity Summary

**使用 Tenacity 库实现生产级别的指数退避重试策略,网络请求和文件操作自动重试 3 次(1s→2s→3s),原子文件操作保证下载完整性**

## Performance

- **Duration:** 15min 20sec
- **Started:** 2026-02-25T09:05:46Z
- **Completed:** 2026-02-25T09:21:06Z
- **Tasks:** 3
- **Files modified:** 5

## Accomplishments
- 使用 Tenacity 库替换简单的 for 循环重试逻辑
- 实现指数退避策略(1秒→2秒→3秒)并记录重试日志
- 为 PixivAPI 客户端的所有网络请求方法添加自动重试
- 为文件下载器添加自动重试和原子文件操作
- 保持向后兼容性:外部函数返回错误字典而非抛出异常

## Task Commits

Each task was committed atomically:

1. **Task 1: 添加 Tenacity 依赖并升级 retry_handler.py** - `c9b48f0` (feat)
2. **Task 2: 应用 Tenacity 装饰器到 PixivAPI 客户端** - `9b36bc2` (feat)
3. **Task 3: 应用 Tenacity 装饰器到文件下载器** - `f571234` (feat)

## Files Created/Modified
- `pyproject.toml` - 添加 tenacity>=8.2.0 依赖
- `src/gallery_dl_auo/download/retry_handler.py` - 使用 Tenacity 装饰器替代 for 循环
- `src/gallery_dl_auo/api/pixiv_client.py` - 为 get_ranking、get_ranking_all、get_artwork_metadata 添加 @retry_on_network_error
- `src/gallery_dl_auo/download/file_downloader.py` - 添加原子文件操作和自动重试
- `tests/download/test_retry_handler.py` - 更新单元测试验证 Tenacity 行为

## Decisions Made
1. **使用 Tenacity 装饰器模式**:替代简单的 for 循环,获得生产级别的重试功能(指数退避、日志记录、异常过滤)
2. **wait_exponential(multiplier=1, min=1, max=3)**:精确实现 1→2→3 秒退避,避免长时间等待
3. **before_sleep_log(logger, logging.WARNING)**:记录每次重试的等待时间和原因,便于调试
4. **内部函数应用装饰器,外部函数捕获异常**:保持向后兼容性,返回错误字典而非抛出异常
5. **原子文件操作(.tmp + rename)**:保证下载完整性,避免部分下载的损坏文件
6. **Windows 兼容性**:重命名前先删除已存在的目标文件,解决 Windows 文件锁定问题

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

**1. 测试期望返回错误字典而非抛出异常**
- **问题:** 现有测试期望 `download_file()` 返回错误字典,但 Tenacity 装饰器会在重试失败后抛出异常
- **解决方案:** 使用内部函数 `_download_file_with_retry()` 应用装饰器,外部函数捕获所有异常并返回错误字典
- **影响:** 保持向后兼容性,不破坏现有代码

**2. 测试匹配错误消息文本**
- **问题:** 测试期望 "文件写入失败" 但代码返回 "文件操作失败"
- **解决方案:** 确保异常处理中的错误消息与测试期望一致
- **影响:** 测试全部通过,行为符合预期

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- 重试机制已升级为生产级别,网络错误自动重试 3 次
- 原子文件操作保证下载完整性
- 日志记录重试过程,便于调试和监控
- 可继续后续错误处理增强(友好错误消息、错误日志文件)

## Self-Check: PASSED

**Verified:**
- SUMMARY.md created at .planning/phases/07-cuo-wu-chu-li-yu-jian-zhuang-xing/07-01-SUMMARY.md
- Task 1 commit c9b48f0 exists
- Task 2 commit 9b36bc2 exists
- Task 3 commit f571234 exists

---
*Phase: 07-cuo-wu-chu-li-yu-jian-zhuang-xing*
*Completed: 2026-02-25*
