# GSD Debug Knowledge Base

Resolved debug sessions. Used by `gsd-debugger` to surface known-pattern hypotheses at the start of new investigations.

---

## success-list-duplicate-ids-multi-page-artworks — 多页作品的每个页面被独立计入 success_list 导致重复 ID
- **Date:** 2026-03-16
- **Error patterns:** success_list, 重复 ID, 多页作品, 统计数字不准确, downloaded count wrong
- **Root cause:** _parse_download_output 方法在解析下载输出时，对每个下载的文件路径都提取作品 ID 并添加到 success_list，没有去重逻辑。多页作品会生成多个文件路径（{id}_p0, {id}_p1, {id}_p2），导致同一个作品 ID 被添加多次。
- **Fix:** 在 _parse_download_output 方法中添加去重逻辑，使用 seen_ids 集合，确保每个作品 ID 只添加一次（与 _parse_dry_run_output 保持一致）
- **Files changed:** src/gallery_dl_auto/integration/gallery_dl_wrapper.py, tests/integration/test_parse_download_output_dedup.py
---
