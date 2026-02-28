---
phase: 04-nei-rong-yu-yuan-shu-ju
plan: 03
subsystem: download-integration
tags: [path-template, metadata, integration, cli, download]

requires: [04-01, 04-02]
provides:
  - 路径模板集成到下载流程
  - 元数据获取和 fallback 机制
  - download 命令 --path-template 参数
  - 下载结果包含完整元数据
affects: []

tech-stack:
  added: []
  patterns:
    - 路径模板集成到 RankingDownloader
    - 元数据获取失败时使用排行榜基础数据作为 fallback
    - CLI 参数传递到下载器
    - JSON 输出包含元数据字段

key-files:
  created: []
  modified:
    - src/gallery_dl_auo/download/ranking_downloader.py
    - src/gallery_dl_auo/cli/download_cmd.py
    - tests/download/test_ranking_downloader.py
    - tests/cli/test_download_cmd.py

key-decisions:
  - "元数据获取失败时使用排行榜基础数据作为 fallback (不中断下载流程)"
  - "路径模板可选,未提供时使用默认目录结构"
  - "使用路径模板时,确保父目录存在"
  - "成功结果包含 tags 和 statistics 字段 (如果有元数据)"

patterns-established:
  - "可选功能通过参数控制 (path_template 可选)"
  - "Fallback 策略保证健壮性 (元数据获取失败不中断流程)"
  - "测试覆盖所有场景 (成功、失败、fallback、所有变量)"

requirements-completed: [CONT-02, CONT-03, CONT-04]

duration: 9min
completed: 2026-02-25
---

# Phase 04 Plan 03: 集成元数据和路径模板到下载流程

**集成元数据获取和路径模板系统到下载流程 - 让用户能够使用自定义路径模板保存图片,并在下载结果中获取完整的元数据**

## Performance

- **Duration:** 9 min
- **Started:** 2026-02-25T04:04:29Z
- **Completed:** 2026-02-25T04:13:11Z
- **Tasks:** 2
- **Files modified:** 4 (created 0, modified 4)

## Accomplishments
- RankingDownloader 成功集成元数据获取和路径模板系统
- 元数据获取失败时使用排行榜基础数据作为 fallback,保证下载流程不中断
- download 命令添加 --path-template 参数,支持 6 个模板变量
- 下载结果包含完整的元数据(标签和统计数据)
- 新增 7 个测试用例,全部通过 (11 + 10 = 21 个测试)

## Task Commits

Each task was committed atomically:

1. **Task 1: 扩展 RankingDownloader 集成元数据和路径模板** - `dedce14` (feat)
   - 添加 path_template 参数到 download_ranking() 方法
   - 集成元数据获取,支持 fallback
   - 支持所有 6 个模板变量
   - 下载结果包含 tags 和 statistics 字段
   - 新增 4 个测试用例

2. **Task 2: 扩展 download CLI 命令添加路径模板参数** - `dacea48` (feat)
   - 添加 --path-template 选项,包含详细的帮助文本
   - 传递 path_template 参数到 RankingDownloader
   - JSON 输出包含 path_template 字段
   - 更新现有测试,新增 3 个测试用例

**Plan metadata:** (pending commit)

_Note: All commits follow conventional commit format_

## Files Created/Modified
- `src/gallery_dl_auo/download/ranking_downloader.py` - 集成元数据获取和路径模板
- `src/gallery_dl_auo/cli/download_cmd.py` - 添加 --path-template 参数
- `tests/download/test_ranking_downloader.py` - 新增 4 个测试 (11 total)
- `tests/cli/test_download_cmd.py` - 更新现有测试,新增 3 个测试 (10 total)

## Decisions Made
- **元数据获取失败时使用 fallback:** 当 get_artwork_metadata() 失败时,使用排行榜基础数据继续下载,不中断流程。这提供了更健壮的用户体验。
- **路径模板可选:** 未提供 path_template 时使用默认的 {mode}-{date}/ 目录结构,保证向后兼容。
- **确保父目录存在:** 使用路径模板时,调用 `filepath.parent.mkdir(parents=True, exist_ok=True)` 确保目录结构存在。
- **结果包含可选元数据:** 只有成功获取元数据时,结果才包含 tags 和 statistics 字段,避免虚假数据。

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

**Issue 1: Mock 对象缺少属性**
- **Problem:** 测试中使用 `MagicMock(spec=ArtworkMetadata)` 但未设置 `tags` 和 `statistics` 属性,导致访问这些属性时抛出 AttributeError
- **Solution:** 在 Mock 对象中显式设置 `mock_metadata.tags = []` 和 `mock_metadata.statistics = MagicMock()`
- **Type:** Bug fix (Rule 1)
- **Commit:** 包含在 dedce14 中

**Issue 2: 测试参数不匹配**
- **Problem:** 现有测试 `test_download_with_date` 验证调用时未包含新的 `path_template` 参数
- **Solution:** 更新测试断言,包含 `path_template=None` 参数
- **Type:** Bug fix (Rule 1)
- **Commit:** 包含在 dacea48 中

## User Setup Required

None - no external service configuration required.

## Verification Results

**Wave 3 验证:**
- ✅ download_ranking() 方法支持 path_template 参数
- ✅ 元数据获取失败时使用 fallback
- ✅ 路径模板支持所有 6 个变量
- ✅ 下载结果包含 tags 和 statistics 字段
- ✅ download 命令支持 --path-template 参数
- ✅ JSON 输出包含元数据字段
- ✅ 所有测试通过: 32/32 tests passed
- ⚠️ mypy 类型检查发现 1 个错误 (pixiv_client.py:116) - 但这是预存在的问题,不在本次任务范围内

**Goal-Backward Verification:**
1. ✅ **用户能够通过 --path-template 参数指定保存路径** - download 命令添加参数,传递给 downloader
2. ✅ **下载结果包含完整的元数据** - success_list 包含 tags 和 statistics 字段
3. ✅ **路径模板能够使用元数据字段构建目录结构** - 支持 6 个变量,包括 author, title 等
4. ✅ **元数据获取失败时使用排行榜基础数据作为 fallback** - try-except 捕获 PixivAPIError,使用 illust 数据

## Deferred Items

**mypy 类型错误 (pixiv_client.py:116):**
- **Issue:** `Argument after ** must be a mapping, not "dict[str, Any] | None"`
- **Location:** src/gallery_dl_auo/api/pixiv_client.py:116
- **Type:** 预存在的类型错误,不是本次任务导致
- **Action:** 不修复 (超出范围,遵循偏差规则的范围边界)
- **File:** `.planning/phases/04-nei-rong-yu-yuan-shu-ju/deferred-items.md`

## Self-Check: PASSED

- ✅ src/gallery_dl_auo/download/ranking_downloader.py exists
- ✅ src/gallery_dl_auo/cli/download_cmd.py exists
- ✅ tests/download/test_ranking_downloader.py exists
- ✅ tests/cli/test_download_cmd.py exists
- ✅ Commit dedce14 found in git history
- ✅ Commit dacea48 found in git history

---
*Phase: 04-nei-rong-yu-yuan-shu-ju*
*Completed: 2026-02-25*
