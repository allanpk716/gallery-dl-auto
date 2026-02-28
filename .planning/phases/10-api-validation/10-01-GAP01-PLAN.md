---
wave: 2
depends_on: ["10-01"]
files_modified:
  - tests/validation/test_json_schemas.py
autonomous: true
requirements: [VAL-01]
plan_type: gap_closure
parent_plan: 10-01
gap_summary: JSON Schema 测试中的模块导入路径错误,导致 6/9 测试失败
verification_file: .planning/phases/10-api-validation/10-API-VALIDATION-VERIFICATION.md
must_haves:
  truths:
    - 测试文件中的导入语句能够成功加载所需模块
    - 所有 9 个 JSON Schema 测试用例执行并验证通过
    - 父计划 10-01 已实现 JSON Schema 验证功能并通过 VAL-01 验证
  artifacts:
    - tests/validation/test_json_schemas.py (导入路径已修复)
    - pytest 测试报告显示 9/9 passed
  key_links:
    - VAL-01 需求在 10-01 计划中实现和验证
    - 本计划仅修复 10-01 执行后发现的导入路径错误,支持父计划完成 VAL-01 验证
---

# Gap Closure Plan: 修复 JSON Schema 测试导入路径

**Created:** 2026-02-27
**Type:** Gap Closure
**Parent Plan:** 10-01 (JSON 输出格式验证)
**Priority:** HIGH - 阻止 VAL-01 完整验证

## Gap Analysis

### Problem
JSON Schema 测试中存在多个导入路径错误,导致 6/9 测试失败:

1. **错误的模型导入路径**:
   - 测试使用: `from gallery_dl_auo.models.download_result import BatchDownloadResult`
   - 实际路径: `from gallery_dl_auo.models.error_response import BatchDownloadResult`

2. **错误的 StructuredError 导入路径**:
   - 测试使用: `from gallery_dl_auo.utils.error_codes import StructuredError`
   - 实际路径: `from gallery_dl_auo.models.error_response import StructuredError`

3. **错误的 monkeypatch 目标路径**:
   - status 命令: `gallery_dl_auo.cli.status.*` → `gallery_dl_auo.cli.status_cmd.*`
   - config 命令: `gallery_dl_auo.cli.config.*` → `gallery_dl_auo.cli.config_cmd.*`

### Root Cause
测试代码编写时基于预期的模块结构,但实际实现时:
- 模块命名采用了 `_cmd` 后缀约定 (`status_cmd.py`, `config_cmd.py`)
- `BatchDownloadResult` 和 `StructuredError` 模型定义在 `models/error_response.py` 中

### Impact
- **阻塞**: VAL-01 需求无法完全验证
- **测试失败**: 6/9 JSON Schema 测试失败
- **覆盖缺口**: status 和 config 命令的 JSON 输出未验证

## Goal

修复 `tests/validation/test_json_schemas.py` 中的所有导入路径错误,使所有 JSON Schema 测试通过。

**Success Criteria:**
1. ✅ 所有导入路径正确,无 ModuleNotFoundError
2. ✅ 9/9 JSON Schema 测试通过
3. ✅ 10-01 计划的 VAL-01 验证可以正常执行

**Note:** 本计划是 10-01 的 gap closure,仅修复导入路径错误。本计划支持父计划 10-01 完成 VAL-01 验证(VAL-01 的实现和主要验证已在 10-01 计划中完成)。

## Tasks

### Task 1: 修复模型导入路径

**What:** 修复 `BatchDownloadResult` 和 `StructuredError` 的导入路径

**Files:** `tests/validation/test_json_schemas.py`

**Implementation:**

```xml
<task>
<step>
在 test_download_success_schema 方法中,修复导入路径:
</step>
<code>
# Line 41: 修改导入路径
from gallery_dl_auo.models.error_response import BatchDownloadResult
</code>
</task>
```

```xml
<task>
<step>
在 test_download_error_schema 方法中,修复导入路径:
</step>
<code>
# Line 76: 修改导入路径
from gallery_dl_auo.models.error_response import StructuredError
</code>
</task>
```

**Verification:**
```bash
# 运行测试验证导入成功
pytest tests/validation/test_json_schemas.py::TestDownloadCommandJSONSchema::test_download_success_schema -v
pytest tests/validation/test_json_schemas.py::TestDownloadCommandJSONSchema::test_download_error_schema -v
```

### Task 2: 修复 monkeypatch 目标路径

**What:** 修复 status 和 config 命令的 monkeypatch 路径

**Files:** `tests/validation/test_json_schemas.py`

**Implementation:**

```xml
<task>
<step>
在 test_command_json_output_parsable 方法中,修复 status 命令的 monkeypatch 路径:
</step>
<code>
# Line 135: 修改 monkeypatch 目标
monkeypatch.setattr("gallery_dl_auo.cli.status_cmd.get_auth_status", mock_status)
</code>
</task>
```

```xml
<task>
<step>
在 test_status_command_schema 方法中,修复 monkeypatch 路径:
</step>
<code>
# Line 163: 修改 monkeypatch 目标
monkeypatch.setattr("gallery_dl_auo.cli.status_cmd.get_auth_status", mock_status)
</code>
</task>
```

```xml
<task>
<step>
在 test_config_get_command_schema 方法中,修复 monkeypatch 路径:
</step>
<code>
# Line 177: 修改 monkeypatch 目标
monkeypatch.setattr("gallery_dl_auo.cli.config_cmd.get_config_value", mock_config_get)
</code>
</task>
```

```xml
<task>
<step>
在 test_config_list_command_schema 方法中,修复 monkeypatch 路径:
</step>
<code>
# Line 191: 修改 monkeypatch 目标
monkeypatch.setattr("gallery_dl_auo.cli.config_cmd.list_config_values", mock_config_list)
</code>
</task>
```

**Verification:**
```bash
# 运行所有 JSON Schema 测试
pytest tests/validation/test_json_schemas.py -v
# 预期: 9/9 passed
```

### Task 3: 验证所有测试通过

**What:** 运行完整的测试套件并验证 VAL-01 完全满足

**Implementation:**

```bash
# 1. 运行所有 JSON Schema 测试
pytest tests/validation/test_json_schemas.py -v

# 2. 运行所有验证测试
pytest tests/validation/ -v

# 3. 手动验证命令 JSON 输出
pixiv-downloader --json-output version
pixiv-downloader --json-output status
pixiv-downloader --json-output config get download_dir
```

**Expected Output:**
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

**Verification Notes:**
- 此测试验证的是 10-01 计划中实现的 JSON Schema 验证功能
- 本 gap closure 仅修复导入路径,确保测试可以正常运行
- VAL-01 需求的完整验证由 10-01 计划负责

## Must-Haves (Gap Closure Verification)

完成此 gap closure 后,以下条件必须为 TRUE:

| Must-Have | Verification Method | Success Criteria |
| --- | --- | --- |
| 所有导入路径正确 | `pytest tests/validation/test_json_schemas.py -v` | 0 import errors |
| 所有 JSON Schema 测试通过 | `pytest tests/validation/test_json_schemas.py -v` | 9/9 passed |
| BatchDownloadResult 导入成功 | 测试无 ModuleNotFoundError | ✅ |
| StructuredError 导入成功 | 测试无 ImportError | ✅ |
| status 命令 monkeypatch 工作 | test_status_command_schema passed | ✅ |
| config 命令 monkeypatch 工作 | test_config_*_command_schema passed | ✅ |
| 10-01 计划的验证可正常执行 | 依赖 10-01 的测试通过 | ✅ |

## Dependencies

**Depends on:**
- 10-01: JSON 输出格式验证 (已完成,发现导入路径错误)

**Blocks:**
- 10-02A, 10-03A 等依赖 10-01 验证结果的计划
- Phase 10 完成验证

## Risks

### Risk 1: status/config 命令未实现 JSON 输出

**Impact:** 测试通过,但命令在真实场景下失败

**Mitigation:**
1. 运行手动验证命令确认 JSON 输出工作
2. 如果命令未实现 JSON 输出,需要创建额外的 gap closure 计划

**Detection:**
```bash
pixiv-downloader --json-output status
# 如果输出不是有效 JSON,需要实现 JSON 输出
```

## Files Modified Summary

```
tests/validation/test_json_schemas.py
├── Line 41: 修复 BatchDownloadResult 导入
├── Line 76: 修复 StructuredError 导入
├── Line 135: 修复 status 命令 monkeypatch 路径
├── Line 163: 修复 status 命令 monkeypatch 路径
├── Line 177: 修复 config 命令 monkeypatch 路径
└── Line 191: 修复 config 命令 monkeypatch 路径
```

## Verification Commands

```bash
# 1. 验证导入修复
python -c "from gallery_dl_auo.models.error_response import BatchDownloadResult, StructuredError; print('✅ 导入成功')"

# 2. 运行所有 JSON Schema 测试
pytest tests/validation/test_json_schemas.py -v

# 3. 运行完整验证套件
pytest tests/validation/ -v

# 4. 手动验证命令
pixiv-downloader --json-output version
pixiv-downloader --json-output status
pixiv-downloader --json-output config list
```

## Success Criteria

- [x] 所有导入路径修复完成
- [x] 9/9 JSON Schema 测试通过
- [x] 无 ModuleNotFoundError 或 ImportError
- [x] 手动验证命令 JSON 输出正常
- [x] 10-01 计划的 VAL-01 验证可以正常执行

---

**Plan Type:** Gap Closure (依赖: 10-01)
**Wave:** 2
**Estimated Duration:** ~5 minutes
**Executor Notes:** 简单的导入路径修复,无需复杂逻辑。此 gap 修复 10-01 执行后发现的导入路径错误。
