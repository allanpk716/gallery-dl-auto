---
phase: 11-bug-fix-verification
plan: 01
subsystem: integration
tags: [bug-fix, tracker, dedup, tdd, regression-test]
dependency_graph:
  requires: [phase-7-download-tracker]
  provides: [tracker-recording-fix]
  affects: [gallery_dl_wrapper.py, test_gallery_dl_wrapper_dedup.py]
tech_stack:
  added: []
  patterns: [tdd-red-green-refactor, single-line-fix, non-breaking-error-handling]
key_files:
  created: []
  modified:
    - path: src/gallery_dl_auto/integration/gallery_dl_wrapper.py
      change: Phase 4 条件从 use_dedup 改为 tracker is not None
      lines: 1
    - path: tests/integration/test_gallery_dl_wrapper_dedup.py
      change: 新增回归测试 test_record_downloads_with_tracker_enabled
      lines: 45
decisions:
  - 使用 tracker is not None 替代 use_dedup，解耦 Phase 4 与 Phase 1/2/3
  - 添加边界测试用例验证修复，确保 bug 不会再次出现
  - 保持最小改动原则，仅修改第 266 行条件判断
metrics:
  duration: 167s
  completed_date: 2026-03-16T08:56:48Z
  tasks_completed: 3/3
  files_modified: 2
  tests_added: 1
  tests_passed: 20
  commits: 2
---

# Phase 11 Plan 01: 修复 tracker DB 记录逻辑 Summary

## 一句话总结

修复 tracker DB 记录逻辑 bug，将 Phase 4 条件从 `if use_dedup` 改为 `if tracker is not None`，确保即使 Phase 1/2 失败时 tracker 仍能记录下载，并添加边界测试用例验证修复效果。

## 完成的工作

### Task 1: 创建回归测试（TDD RED）

- 在 `test_gallery_dl_wrapper_dedup.py` 中添加新测试 `test_record_downloads_with_tracker_enabled`
- 测试场景：tracker 存在时，即使 Phase 1/2 失败（use_dedup=False），Phase 4 仍能记录下载
- 验证目标：确保修复后 tracker 记录逻辑不受 use_dedup 标志影响
- 提交：3bfb5f7

### Task 2: 修复 Phase 4 条件

- 修改 `gallery_dl_wrapper.py` 第 266 行
- 原代码：`if use_dedup and not dry_run and batch_result.success_list:`
- 新代码：`if tracker is not None and not dry_run and batch_result.success_list:`
- 修复原理：Phase 4 条件改为直接检查 tracker 是否存在，与 use_dedup 解耦
- 影响范围：仅修改 1 行代码，保留现有两阶段下载流程
- 提交：2208b3d

### Task 3: 运行完整测试套件

- 运行 `pytest tests/integration/test_gallery_dl_wrapper_dedup.py -v`：8 个测试全部通过
- 运行 `pytest tests/ -k "tracker or dedup" --tb=short`：20 个相关测试全部通过
- 无回归问题，所有现有测试保持通过
- 验证修复有效且功能完整

## 技术细节

### Bug 根因分析

**问题现象**：
- 用户首次下载排行榜后，tracker DB 为空（没有记录）
- 第二次下载相同排行榜时，程序重新下载所有作品（应该跳过）

**根本原因**：
- Phase 4（记录下载到 tracker）的执行条件使用 `use_dedup` 标志
- 该标志在 Phase 1（dry-run）或 Phase 2（archive 生成）失败时会被设置为 `False`
- 导致 Phase 4 永不执行，tracker 无法记录下载

**修复策略**：
- 将 Phase 4 条件从 `if use_dedup` 改为 `if tracker is not None`
- 确保只要 tracker 对象存在且非 dry_run，Phase 4 就能执行
- 与 Phase 1/2/3 的 use_dedup 逻辑解耦

### 代码修改

**修改文件**：`src/gallery_dl_auto/integration/gallery_dl_wrapper.py`

**修改位置**：第 266 行

**修改内容**：
```python
# 修改前：
if use_dedup and not dry_run and batch_result.success_list:
    logger.info("Phase 4: Recording downloads to tracker...")
    self._record_downloads(batch_result, tracker, mode, actual_date)

# 修改后：
if tracker is not None and not dry_run and batch_result.success_list:
    logger.info("Phase 4: Recording downloads to tracker...")
    self._record_downloads(batch_result, tracker, mode, actual_date)
```

**测试用例**：`tests/integration/test_gallery_dl_wrapper_dedup.py`

**新增测试**：
```python
def test_record_downloads_with_tracker_enabled(tmp_path):
    """测试 tracker 存在时，即使 dedup 阶段失败仍能记录下载

    回归测试：确保 Phase 4 条件判断使用 tracker is not None 而非 use_dedup 标志。
    场景：Phase 1 (dry-run) 或 Phase 2 (archive 生成) 失败时，use_dedup=False，
    但只要 tracker 存在且非 dry_run，Phase 4 仍应执行。
    """
    # ... 测试实现（45 行）
```

### 测试结果

**新增测试**：
- 1 个回归测试（test_record_downloads_with_tracker_enabled）
- 验证 tracker 存在时 Phase 4 能独立执行

**测试通过率**：
- test_gallery_dl_wrapper_dedup.py: 8/8 (100%)
- tracker 和 dedup 相关测试: 20/20 (100%)

**无回归**：
- 所有现有测试保持通过
- Phase 1/2/3 的 use_dedup 逻辑不受影响

## 偏差记录

### 无偏差

计划执行完全符合预期：
- 单行修复（第 266 行）
- 添加边界测试用例
- 所有测试通过

未发现需要应用偏差规则的问题。

## 验证清单

### BUG-01 验证

- [x] Line 266 条件从 `if use_dedup` 改为 `if tracker is not None`
- [x] use_dedup 逻辑保持不变（第 183、221 行未修改）
- [x] 新测试 `test_record_downloads_with_tracker_enabled` 通过
- [x] 所有现有测试通过（8/8）
- [x] 相关测试套件通过（20/20）
- [x] Tracker 记录逻辑正确（即使 Phase 1/2 失败）

### 准备 VERI-01 验证

- [x] Bug 修复完成，代码稳定
- [x] 测试覆盖充分，无回归问题
- [ ] 手动验证跨日去重功能（Plan 11-02）

## 后续步骤

Plan 11-01 已完成，准备执行 Plan 11-02（VERI-01 验证）：

1. 验证 cross-day-dedup.md 的 4 个验收标准
2. 手动测试跨日去重场景（3月7日→3月8日）
3. 关闭 GitHub issue #1 和 #2（通过 commit message）

## 文件清单

**修改的文件**：
- `src/gallery_dl_auto/integration/gallery_dl_wrapper.py` (1 行修改)
- `tests/integration/test_gallery_dl_wrapper_dedup.py` (45 行新增)

**未修改的文件**：
- `src/gallery_dl_auto/download/download_tracker.py` (已稳定，无需修改)
- 其他所有项目文件

## 提交历史

```
2208b3d fix(11-01): ensure tracker records downloads even when dedup phases fail
3bfb5f7 test(11-01): add failing test for tracker recording
```

## Self-Check: PASSED

**验证项目**：
- [x] 修改的文件存在：`gallery_dl_wrapper.py`, `test_gallery_dl_wrapper_dedup.py`
- [x] 提交存在：3bfb5f7, 2208b3d
- [x] 测试通过：8/8 dedup tests, 20/20 related tests
- [x] Bug 修复验证：Line 266 条件正确修改
- [x] 回归测试：test_record_downloads_with_tracker_enabled 存在且通过

---

**Phase:** 11-bug-fix-verification
**Plan:** 01
**Status:** Complete
**Next:** Plan 11-02 (VERI-01 验证)
