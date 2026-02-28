# Deferred Items - Phase 04

## Item 1: mypy 类型错误 (pixiv_client.py)

**Date:** 2026-02-25
**Plan:** 04-03
**Status:** Deferred

**Issue:**
```
src\gallery_dl_auo\api\pixiv_client.py:116: error: Argument after ** must be a mapping, not "dict[str, Any] | None"  [arg-type]
```

**Location:** `src/gallery_dl_auo/api/pixiv_client.py:116`

**Type:** Pre-existing type error (not caused by current task)

**Decision:** Do not fix - out of scope per deviation rules (scope boundary: "Only auto-fix issues DIRECTLY caused by the current task's changes")

**Rationale:**
- This error exists in pixiv_client.py, which was modified in 04-02 but the error is unrelated to our 04-03 changes
- Our task only modified ranking_downloader.py and download_cmd.py
- Fixing this would require modifying a file not touched by our task
- Per Rule 3 (blocking issues), this is not blocking our task completion
- Per scope boundary, pre-existing issues in unrelated files are out of scope

**Action Required:** None for 04-03. Consider fixing in future maintenance task.
