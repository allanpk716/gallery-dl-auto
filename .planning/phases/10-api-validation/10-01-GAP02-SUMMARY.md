---
phase: 10-api-validation
plan: 10-01-GAP02
subsystem: CLI
tags: [json-output, status-command, config-command, gap-closure, val-01]
duration: 7min
completed_date: 2026-02-27
key_decisions:
  - 参考 version 命令的实现模式,检查 ctx.obj["output_mode"] 决定输出格式
  - 错误场景也输出 JSON 格式的错误信息,保持一致性
  - config get 子命令测试保持跳过,因为当前 config 命令等同于 list
  - 修复 config_cmd.py 的 Console 初始化问题,从 ctx.obj["console"] 改为创建独立的 Console 实例
files_modified:
  - src/gallery_dl_auo/cli/status_cmd.py
  - src/gallery_dl_auo/cli/config_cmd.py
  - tests/validation/test_json_schemas.py
  - INTEGRATION.md
commits:
  - 6610d1f: feat(10-01-GAP02): 实现 status 命令的 JSON 输出
  - fb7005f: feat(10-01-GAP02): 实现 config 命令的 JSON 输出
  - 5c75f4e: test(10-01-GAP02): 移除 status/config JSON 输出测试的 skip 标记
  - 6854dcb: docs(10-01-GAP02): 更新 INTEGRATION.md 文档反映 JSON 输出支持
---

# Phase 10 Plan 01-GAP02: Gap Closure - 实现 status 和 config 命令的 JSON 输出

## 一句话总结

为 status 和 config 命令添加 --json-output 支持,使所有核心命令符合 INTEGRATION.md 的承诺,完成 VAL-01 验证。

## 背景

在 10-01-GAP01 成功修复测试框架后,重新验证发现 status 和 config 命令**未实现** --json-output 功能,导致 5/9 JSON Schema 测试被跳过,阻塞 VAL-01 需求完整验证。

## 执行的任务

### Task 1: 实现 status 命令的 JSON 输出

**文件**: `src/gallery_dl_auo/cli/status_cmd.py`

**修改内容**:
- 添加 `@click.pass_context` 装饰器获取 ctx 对象
- 添加 `json` 模块导入
- 在所有输出点检查 `ctx.obj.get("output_mode")`
- JSON 模式输出包含 logged_in, token_valid, username, error, suggestion 字段
- 错误场景(无 token、token 无效、解密失败)也输出 JSON 格式
- 保持 Rich 表格输出为默认模式

**验证**: 手动测试和自动化测试通过

### Task 2: 实现 config 命令的 JSON 输出

**文件**: `src/gallery_dl_auo/cli/config_cmd.py`

**修改内容**:
- 添加 `json` 模块导入
- 修改 Console 初始化从 `ctx.obj["console"]` 改为 `Console()` (修复 KeyError)
- 检查 `ctx.obj.get("output_mode")` 决定输出格式
- JSON 模式输出包含 config 对象
- 错误场景(文件不存在、YAML 格式错误)也输出 JSON 格式
- 保持 Rich 表格输出为默认模式

**验证**: 手动测试和自动化测试通过

### Task 3: 移除测试中的 skip 标记并验证

**文件**: `tests/validation/test_json_schemas.py`

**修改内容**:
- 移除 `test_command_json_output_parsable[status]` 的 skip 标记
- 移除 `test_status_command_schema` 的 skip 标记
- 移除 `test_config_list_command_schema` 的 skip 标记
- 保留 `test_config_get_command_schema` 的 skip (子命令未实现)
- 修复 status 测试的 mock 返回值格式 (返回 `{"valid": ...}` 而非 `{"logged_in": ...}`)
- 修复 config 测试使用临时目录创建 config.yaml 文件

**测试结果**: 7 passed, 2 skipped (符合预期)

### Task 4: 更新 INTEGRATION.md 文档

**文件**: `INTEGRATION.md`

**修改内容**:
- 移除过时的限制说明 "命令尚未完全实现 JSON 输出逻辑"
- 添加已知限制说明,明确所有核心命令已支持 --json-output
- 注明 config get/set 子命令尚未实现

**验证**: 文档与实际实现一致

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] 修复 config_cmd.py 的 Console 初始化错误**

- **Found during**: Task 2 执行
- **Issue**: config 命令从 `ctx.obj["console"]` 获取 Console 对象,但主 CLI 未设置该键,导致 KeyError
- **Fix**: 修改为创建独立的 Console 实例 `console = Console()`,与 status_cmd.py 保持一致
- **Files modified**: `src/gallery_dl_auo/cli/config_cmd.py`
- **Commit**: fb7005f

**2. [Rule 1 - Bug] 修复 status 测试的 mock 返回值格式**

- **Found during**: Task 3 测试验证
- **Issue**: 测试 mock 返回 `{"logged_in": ..., "token_valid": ...}`,但 `validate_refresh_token` 实际返回 `{"valid": ...}`
- **Fix**: 修改 mock 返回值格式为 `{"valid": False, "access_token": None, "refresh_token": None, "error": "..."}`
- **Files modified**: `tests/validation/test_json_schemas.py`
- **Commit**: 5c75f4e

**3. [Rule 3 - Blocking] 修复 config 测试需要 config.yaml 文件**

- **Found during**: Task 3 测试验证
- **Issue**: config 测试调用真实命令,需要 config.yaml 文件存在
- **Fix**: 在测试中使用临时目录创建 config.yaml 文件,测试完成后清理
- **Files modified**: `tests/validation/test_json_schemas.py`
- **Commit**: 5c75f4e

None - plan executed with minor bug fixes only.

## 成果

### 功能验证

**所有核心命令已支持 --json-output**:
- ✅ `pixiv-downloader --json-output version` → `{"version": "0.1.0", ...}`
- ✅ `pixiv-downloader --json-output status` → `{"logged_in": true, "token_valid": true, ...}`
- ✅ `pixiv-downloader --json-output config` → `{"config": {...}}`
- ✅ `pixiv-downloader --json-output download` (已在 Phase 10-01 中实现)

**测试结果**:
```
tests/validation/test_json_schemas.py::TestDownloadCommandJSONSchema::test_download_success_schema PASSED
tests/validation/test_json_schemas.py::TestDownloadCommandJSONSchema::test_download_error_schema SKIPPED
tests/validation/test_json_schemas.py::TestDownloadCommandJSONSchema::test_schema_completeness PASSED
tests/validation/test_json_schemas.py::TestAllCommandsJSONSchema::test_command_json_output_parsable[command0-expected_fields0] PASSED
tests/validation/test_json_schemas.py::TestAllCommandsJSONSchema::test_command_json_output_parsable[command1-expected_fields1] PASSED
tests/validation/test_json_schemas.py::TestAllCommandsJSONSchema::test_version_command_schema PASSED
tests/validation/test_json_schemas.py::TestAllCommandsJSONSchema::test_status_command_schema PASSED
tests/validation/test_json_schemas.py::TestAllCommandsJSONSchema::test_config_get_command_schema SKIPPED
tests/validation/test_json_schemas.py::TestAllCommandsJSONSchema::test_config_list_command_schema PASSED

结果: 7 passed, 2 skipped
```

### Must-Haves 验证

| Must-Have | Status | Verification |
| --- | --- | --- |
| status 命令支持 --json-output | ✅ PASS | 输出有效 JSON,包含 logged_in, token_valid 字段 |
| config 命令支持 --json-output | ✅ PASS | 输出有效 JSON,包含 config 对象 |
| status 测试不再跳过 | ✅ PASS | test_status_command_schema passed |
| config list 测试不再跳过 | ✅ PASS | test_config_list_command_schema passed |
| JSON 输出符合 Schema | ✅ PASS | validate(instance=output, schema=schema) 成功 |
| INTEGRATION.md 文档一致 | ✅ PASS | 无矛盾的限制说明 |
| VAL-01 需求满足 | ✅ PASS | 7/9 passed, 2/9 skipped (合理跳过) |

## 关键决策

1. **参考 version 命令模式**: 使用 `ctx.obj.get("output_mode")` 检查输出模式,保持代码风格一致
2. **错误场景 JSON 输出**: 所有错误场景(无 token、token 无效、文件不存在等)都输出 JSON 格式,便于第三方工具解析
3. **config get 子命令**: 保持测试跳过,因为当前 config 命令等同于 list,get/set 子命令可在 Phase 8.1 中实现
4. **Console 初始化**: 使用独立的 Console 实例,避免依赖主 CLI 的 ctx.obj 设置

## 影响和依赖

**满足的需求**:
- VAL-01: JSON 输出格式验证 (2.5/3 → 3/3 requirements)

**解除的阻塞**:
- Phase 10 完整验证
- VAL-01 需求完全满足

**下游影响**:
- 第三方工具现在可以使用 --json-output 调用 status 和 config 命令
- INTEGRATION.md 的承诺与实际实现一致

## 后续工作

- Phase 8.1: 实现 config get/set 子命令,移除 test_config_get_command_schema 的 skip 标记
- 考虑在主 CLI 中设置 ctx.obj["console"] 以保持一致性(可选)

## Self-Check

**验证创建的文件存在**:
```bash
[ -f "src/gallery_dl_auo/cli/status_cmd.py" ] && echo "FOUND: status_cmd.py"
[ -f "src/gallery_dl_auo/cli/config_cmd.py" ] && echo "FOUND: config_cmd.py"
[ -f "tests/validation/test_json_schemas.py" ] && echo "FOUND: test_json_schemas.py"
[ -f "INTEGRATION.md" ] && echo "FOUND: INTEGRATION.md"
```

**验证提交存在**:
```bash
git log --oneline | grep -q "6610d1f" && echo "FOUND: 6610d1f"
git log --oneline | grep -q "fb7005f" && echo "FOUND: fb7005f"
git log --oneline | grep -q "5c75f4e" && echo "FOUND: 5c75f4e"
git log --oneline | grep -q "6854dcb" && echo "FOUND: 6854dcb"
```

**结果**: 所有文件和提交已验证存在

## Self-Check: PASSED

---

**Plan Type**: Gap Closure (Feature Implementation)
**Wave**: 3
**Duration**: 7 minutes
**Status**: COMPLETED
