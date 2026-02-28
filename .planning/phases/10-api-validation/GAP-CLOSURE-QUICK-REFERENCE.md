# Phase 10: Gap Closure 执行快速参考

**Created:** 2026-02-27
**Updated:** 2026-02-28
**Phase:** 10 (API 验证)
**Mode:** Gap Closure
**Total Waves:** 5
**Total Plans:** 6

---

## ⚠️ 重要更新 (2026-02-28)

**Wave 5 新增:**
- **10-03-GAP01**: 修复 Wave 4 引入的退出码回归
- **优先级**: CRITICAL
- **状态**: Ready for execution

---

## 快速开始

### 执行 Wave 5 Gap Closure (推荐)

```bash
# 方式 1: 使用 gsd:execute-phase
/gsd:execute-phase --gap-closure --plan 10-03-GAP01

# 方式 2: 直接执行计划
# 读取: .planning/phases/10-api-validation/10-03-GAP01-PLAN.md
# 执行其中的 4 个任务
```

### 执行所有 Gap Closure

```bash
# 依次执行 Wave 2-5
/gsd:execute-phase --phase 10 --gap-closure
```

### 验证修复

```bash
# 1. 运行 JSON Schema 测试
pytest tests/validation/test_json_schemas.py -v
# 预期: 7 passed, 2 skipped

# 2. 运行退出码测试
pytest tests/validation/test_exit_codes.py -v
# 预期: 10 passed

# 3. 运行集成测试
pytest tests/validation/test_integration.py -v
# 预期: 9 passed, 1 skipped, 2 failed (Windows 编码问题)

# 4. 运行完整验证套件
pytest tests/validation/ -v
# 预期: 26+ passed
```

---

## Gap Closure 波次总览

### Wave 2: 测试框架修复 (已完成 ✅)
**计划:** 10-01-GAP01
**状态:** 完成
**修复:** 测试框架导入路径错误

### Wave 3: JSON 输出实现 (已完成 ✅)
**计划:** 10-01-GAP02
**状态:** 完成
**修复:** status/config 命令 JSON 输出

### Wave 4: JSON 错误格式 (已完成 ✅)
**计划:** 10-02-GAP02
**状态:** 完成
**修复:** --json-output 模式错误格式
**⚠️ 引入回归:** 退出码功能失效

### Wave 5: 退出码回归修复 (待执行 🚧)
**计划:** 10-03-GAP01
**状态:** Ready for execution
**修复:** main() 函数退出码传递
**优先级:** CRITICAL
**详情:** 见 [WAVE-05-EXECUTION-QUICK-REFERENCE.md](./WAVE-05-EXECUTION-QUICK-REFERENCE.md)

---

## 计划清单

### Wave 2: 10-01-GAP01 - 修复 JSON Schema 测试导入路径 ✅

**Status:** 已完成
**Duration:** ~5 分钟
**Completed:** 2026-02-27

**Tasks:**
1. ✅ 修复 BatchDownloadResult 导入路径 (Line 41)
2. ✅ 修复 StructuredError 导入路径 (Line 76)
3. ✅ 修复 monkeypatch 目标路径 (Lines 135, 163, 177, 191)

**File:** `tests/validation/test_json_schemas.py`

---

### Wave 3: 10-01-GAP02 - 实现 status/config JSON 输出 ✅

**Status:** 已完成
**Duration:** ~15 分钟
**Completed:** 2026-02-27

**Tasks:**
1. ✅ 实现 status 命令 --json-output 支持
2. ✅ 实现 config 命令 --json-output 支持
3. ✅ 移除测试 skip 标记
4. ✅ 更新 INTEGRATION.md 文档

---

### Wave 4: 10-02-GAP02 - 修复 JSON 错误格式 ✅

**Status:** 已完成
**Duration:** ~10 分钟
**Completed:** 2026-02-27

**Tasks:**
1. ✅ 添加全局 Click 异常处理
2. ✅ 验证多种错误场景
3. ✅ 更新 INTEGRATION.md
4. ✅ 运行 UAT 测试验证

**⚠️ 引入回归:** main() 函数返回退出码但未调用 sys.exit()

---

### Wave 5: 10-03-GAP01 - 修复退出码回归 🚧

**Status:** Ready for execution
**Priority:** CRITICAL
**Estimated Duration:** ~15 分钟

**Tasks:**
1. ⏳ 修复 main() 函数退出码传递 (5 分钟)
   - Line 119: `return 0` → `sys.exit(0)`
   - Line 123, 125, 127: `return e.code` → `sys.exit(e.code)`
   - Line 145: `return 130` → `sys.exit(130)`

2. ⏳ 验证退出码修复 (5 分钟)
   - 运行 3 个失败的集成测试
   - 手动验证退出码

3. ⏳ 更新验证报告 (3 分钟)
   - 更新状态为 verified
   - 更新分数为 3/3

4. ⏳ 更新项目状态 (2 分钟)
   - 更新 STATE.md 和 ROADMAP.md

**File:** `src/gallery_dl_auo/cli/main.py`

**详细参考:** [WAVE-05-EXECUTION-QUICK-REFERENCE.md](./WAVE-05-EXECUTION-QUICK-REFERENCE.md)

---

## Gap Closure 进度

### 整体进度

| Wave | 计划 | 状态 | 优先级 | 完成日期 |
|------|------|------|--------|----------|
| Wave 2 | 10-01-GAP01 | ✅ 完成 | HIGH | 2026-02-27 |
| Wave 3 | 10-01-GAP02 | ✅ 完成 | HIGH | 2026-02-27 |
| Wave 4 | 10-02-GAP01 | ✅ 完成 | HIGH | 2026-02-27 |
| Wave 4 | 10-02-GAP02 | ✅ 完成 (引入回归) | HIGH | 2026-02-27 |
| Wave 5 | 10-03-GAP01 | 🚧 待执行 | CRITICAL | - |

**总计划:** 6 个 (5 个已完成,1 个待执行)

### 需求覆盖进度

| 需求 | Wave 2 后 | Wave 3 后 | Wave 4 后 | Wave 5 后 (预期) |
|------|-----------|-----------|-----------|------------------|
| VAL-01 | 83% ✅ | 100% ✅ | 100% ✅ | 100% ✅ |
| VAL-02 | 100% ✅ | 100% ✅ | REGRESSION ❌ | 100% ✅ |
| VAL-03 | 75% ✅ | 75% ✅ | 50% ❌ | 75% ✅ |

**Overall:** 67% → 83% → 83% → 预期 100%

---

## 验证命令

### 1. 导入验证

```bash
python -c "from gallery_dl_auo.models.error_response import BatchDownloadResult, StructuredError; print('✅ 导入成功')"
```

### 2. JSON Schema 测试

```bash
pytest tests/validation/test_json_schemas.py -v
```

**预期输出:**
```
tests/validation/test_json_schemas.py::TestDownloadCommandJSONSchema::test_download_success_schema PASSED
tests/validation/test_json_schemas.py::TestDownloadCommandJSONSchema::test_download_error_schema PASSED
tests/validation/test_json_schemas.py::TestDownloadCommandJSONSchema::test_schema_completeness PASSED
tests/validation/test_json_schemas.py::TestAllCommandsJSONSchema::test_command_json_output_parsable[command0-expected_fields0] PASSED
tests/validation/test_json_schemas.py::TestAllCommandsJSONSchema::test_command_json_output_parsable[command1-expected_fields1] PASSED
tests/validation/test_json_schemas.py::TestAllCommandsJSONSchema::test_version_command_schema PASSED
tests/validation/test_json_schemas.py::TestAllCommandsJSONSchema::test_status_command_schema PASSED
tests/validation/test_json_schemas.py::TestAllCommandsJSONSchema::test_config_get_command_schema PASSED
tests/validation/test_json_schemas.py::TestAllCommandsJSONSchema::test_config_list_command_schema PASSED

=================== 9 passed in X.XXs ===================
```

### 3. 完整验证套件

```bash
pytest tests/validation/ -v
```

**预期:** 30+ passed (JSON Schema 9 + Exit Codes 10 + Integration 11+)

### 4. 手动验证

```bash
# version 命令
pixiv-downloader --json-output version
# 预期: {"version": "0.1.0", "python_version": "3.14.2", "platform": "windows"}

# status 命令
pixiv-downloader --json-output status
# 预期: {"logged_in": ..., "token_valid": ..., ...}

# config 命令
pixiv-downloader --json-output config list
# 预期: {"config": {...}}

# download 命令
pixiv-downloader --json-output download --type daily
# 预期: BatchDownloadResult JSON
```

---

## 成功标准

### Wave 2 (已完成 ✅)
- [x] 所有导入路径修复完成
- [x] 7/9 JSON Schema 测试通过
- [x] 无 ModuleNotFoundError 或 ImportError

### Wave 3 (已完成 ✅)
- [x] status 命令 --json-output 支持
- [x] config 命令 --json-output 支持
- [x] 8/9 JSON Schema 测试通过
- [x] INTEGRATION.md 文档更新

### Wave 4 (已完成 ✅)
- [x] --json-output 模式错误格式正确
- [x] UAT Test 5 通过
- [x] INTEGRATION.md 错误格式文档

### Wave 5 (待执行)
- [ ] main() 函数所有退出点使用 sys.exit()
- [ ] 错误场景返回正确的非零退出码
- [ ] 成功场景返回退出码 0
- [ ] 3 个失败的集成测试通过
- [ ] VAL-02 需求完全满足
- [ ] 验证报告更新为 verified

### Phase 10 整体标准
- [ ] 所有 gap closure 计划执行完成
- [ ] VAL-01, VAL-02, VAL-03 需求完全满足
- [ ] Phase 10 完成度达到 100%
- [ ] 准备 v1.2 发布

---

## 完成后操作

### Wave 5 完成后 (Phase 10 完成)

1. **验证执行结果:**
   ```bash
   pytest tests/validation/ -v
   # 预期: 26 passed, 3 skipped, 2 failed (Windows 编码)
   ```

2. **更新验证报告:**
   - 编辑: `.planning/phases/10-api-validation/10-API-VALIDATION-VERIFICATION.md`
   - 更新状态: `status: verified`
   - 更新分数: `score: 3/3 requirements fully verified`

3. **更新 STATE.md:**
   - 标记 Phase 10 完全完成
   - 更新进度: 100%
   - 更新状态: `status: complete`

4. **更新 ROADMAP.md:**
   - 标记 Phase 10: Complete
   - 标记 v1.2 里程碑: Complete

5. **准备发布:**
   - v1.2 第三方 CLI 集成优化版本
   - 准备发布说明

---

**Executor Notes:**
- Wave 2-4 已完成
- Wave 5 是最后一个 gap closure
- Wave 5 修复 Wave 4 引入的退出码回归
- 预计 15 分钟完成 Wave 5
- 完成后 Phase 10 和 v1.2 里程碑全部完成
