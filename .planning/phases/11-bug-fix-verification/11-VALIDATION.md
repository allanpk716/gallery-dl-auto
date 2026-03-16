---
phase: 11
slug: bug-fix-verification
status: draft
nyquist_compliant: false
wave_0_complete: false
created: 2026-03-16
---

# Phase 11 — Validation Strategy

> Per-phase validation contract for feedback sampling during execution.

---

## Test Infrastructure

| Property | Value |
|----------|-------|
| **Framework** | pytest 9.0.2 |
| **Config file** | pyproject.toml (lines 142-150) |
| **Quick run command** | `pytest tests/integration/test_gallery_dl_wrapper_dedup.py -v -x` |
| **Full suite command** | `pytest tests/ -v --tb=short` |
| **Estimated runtime** | ~60 seconds |

---

## Sampling Rate

- **After every task commit:** Run `pytest tests/integration/test_gallery_dl_wrapper_dedup.py -v -x`
- **After every plan wave:** Run `pytest tests/ -k "tracker or dedup" --tb=short`
- **Before `/gsd:verify-work`:** Full suite must be green
- **Max feedback latency:** 60 seconds

---

## Per-Task Verification Map

| Task ID | Plan | Wave | Requirement | Test Type | Automated Command | File Exists | Status |
|---------|------|------|-------------|-----------|-------------------|-------------|--------|
| 11-01-01 | 01 | 1 | BUG-01 | unit | `pytest tests/integration/test_gallery_dl_wrapper_dedup.py::test_record_downloads_with_tracker_enabled -x` | ❌ W0 | ⬜ pending |
| 11-01-02 | 01 | 1 | BUG-01 | unit | `pytest tests/integration/test_gallery_dl_wrapper_dedup.py::test_record_downloads_with_missing_files -x` | ✅ 现有 | ⬜ pending |
| 11-01-03 | 01 | 1 | VERI-01 | unit | `pytest tests/integration/test_gallery_dl_wrapper_dedup.py::test_record_downloads -x` | ✅ 现有 | ⬜ pending |
| 11-01-04 | 01 | 1 | VERI-01 | unit | `pytest tests/integration/test_gallery_dl_wrapper_dedup.py::test_check_existing_downloads_partial_skip -x` | ✅ 现有 | ⬜ pending |
| 11-01-05 | 01 | 1 | VERI-01 | integration | `pytest tests/integration/test_gallery_dl_wrapper_dedup.py -v` | ✅ 现有（7 tests） | ⬜ pending |
| 11-01-06 | 01 | 1 | VERI-01 | manual | N/A（手动验证） | ❌ 手动 | ⬜ pending |

*Status: ⬜ pending · ✅ green · ❌ red · ⚠️ flaky*

---

## Wave 0 Requirements

- [ ] `tests/integration/test_gallery_dl_wrapper_dedup.py::test_record_downloads_with_tracker_enabled` — 边界测试用例，覆盖 dry-run 失败场景（BUG-01）
- [ ] 手动验证清单 — 验证 cross-day-dedup.md 的 4 个验收标准（VERI-01）

*Existing infrastructure covers most phase requirements. Only 1 new test and manual verification checklist needed.*

---

## Manual-Only Verifications

| Behavior | Requirement | Why Manual | Test Instructions |
|----------|-------------|------------|-------------------|
| 跨日去重完整流程验证 | VERI-01 | 需要验证 cross-day-dedup.md 的 4 个验收标准 | 1. 下载 3月7日 日榜 → tracker DB 应包含所有下载作品<br>2. 下载 3月7日 日榜（再次）→ 程序应跳过所有作品（从 DB 读取）<br>3. 下载 3月8日 日榜 → 程序应识别并跳过 3月7日 已下载的重复作品<br>4. 验证 cross-day-dedup.md 所有 4 个验收标准 |

---

## Validation Sign-Off

- [x] All tasks have `<automated>` verify or Wave 0 dependencies
- [x] Sampling continuity: no 3 consecutive tasks without automated verify
- [x] Wave 0 covers all MISSING references
- [x] No watch-mode flags
- [x] Feedback latency < 60s
- [ ] `nyquist_compliant: true` set in frontmatter

**Approval:** pending
