---
phase: 10-api-validation
plan: 02-GAP02
type: execute
wave: 4
depends_on: ["10-01", "10-01-GAP01", "10-01-GAP02"]
files_modified:
  - src/gallery_dl_auo/cli/main.py
autonomous: true
requirements: [VAL-01]
plan_type: gap_closure
parent_plan: 10-01
gap_summary: --json-output 模式下参数验证错误以纯文本格式输出而非 JSON 格式
verification_file: .planning/phases/10-api-validation/10-UAT.md
must_haves:
  truths:
    - 在 --json-output 模式下,所有错误信息(包括 Click 参数验证错误)以 JSON 格式输出
    - JSON 错误输出包含 success: false, error, message 等字段
    - 非 --json-output 模式下,错误信息保持 Click 默认的纯文本格式
    - 第三方工具可以通过解析 JSON 错误响应进行错误处理
  artifacts:
    - src/gallery_dl_auo/cli/main.py (添加全局 Click 异常处理)
  key_links:
    - main.py __main__ 部分需要捕获 ClickException
    - 使用 cli(standalone_mode=False) 让异常传播
    - 检查 sys.argv 中的 --json-output 标志决定错误格式
---

# Gap Closure Plan: 修复 --json-output 模式错误信息格式

**Created:** 2026-02-27
**Type:** Gap Closure (Bug Fix)
**Parent Plan:** 10-01 (JSON 输出格式验证)
**Priority:** HIGH - UAT 测试失败,第三方集成受阻

## Gap Analysis

### Problem
在 UAT 测试中发现,`--json-output` 模式下,Click 参数验证错误仍以纯文本格式输出:

```bash
$ pixiv-downloader --json-output download http://invalid-url.com
Usage: pixiv-downloader download [OPTIONS]
Try 'pixiv-downloader download --help' for help.

Error: Missing option '--type'.
```

**预期输出:**
```json
{
  "success": false,
  "error": "MissingOption",
  "message": "Missing option '--type'."
}
```

### Root Cause
根据 debug session 诊断:

1. **main.py 缺少异常处理**:
   - 第 105-106 行直接调用 `cli()`
   - 没有自定义的异常处理逻辑

2. **Click 默认 standalone_mode=True**:
   - Click 自动捕获所有 ClickException
   - 以纯文本格式输出错误信息
   - 异常在 `ctx.obj['output_mode']` 设置前就抛出

3. **无法访问 output_mode**:
   - 参数验证错误发生在命令解析阶段
   - 此时 CLI 命令组的回调还未执行
   - 无法通过 `ctx.obj.get("output_mode")` 判断输出模式

### Impact
- **UAT 失败**: Test 5 (错误信息的 JSON 格式) 失败
- **第三方集成受阻**: 无法通过 JSON 解析错误响应
- **文档不一致**: INTEGRATION.md 承诺所有输出(包括错误)都是 JSON

## Goal

实现全局 Click 异常拦截器,在 `--json-output` 模式下将所有错误转换为 JSON 格式。

**Success Criteria:**
1. ✅ Click 参数验证错误在 `--json-output` 模式下输出 JSON 格式
2. ✅ JSON 错误格式包含 `success`, `error`, `message` 字段
3. ✅ 非 `--json-output` 模式保持原有纯文本格式
4. ✅ UAT Test 5 通过

## Tasks

### Task 1: 修改 main.py 添加全局异常处理

**What:** 在 `__main__` 部分添加 Click 异常拦截器

**Files:** `src/gallery_dl_auo/cli/main.py`

**Implementation:**

```xml
<task type="auto">
<name>Task 1: 添加全局 Click 异常处理</name>
<files>src/gallery_dl_auo/cli/main.py</files>
<action>
在 main.py 的 __main__ 部分添加异常处理逻辑,捕获 ClickException 并根据 --json-output 标志转换格式。

**修改位置:** 第 105-106 行

**修改内容:**
```python
# Line 105-107: 替换原有的 cli() 调用
if __name__ == "__main__":
    import sys

    try:
        # 使用 standalone_mode=False 让异常传播到调用者
        cli(standalone_mode=False)
    except click.ClickException as e:
        # 检查是否启用了 --json-output
        if "--json-output" in sys.argv:
            # JSON 格式输出错误
            error_data = {
                "success": False,
                "error": e.__class__.__name__,
                "message": e.format_message()
            }
            print(json.dumps(error_data, ensure_ascii=False))
            sys.exit(e.exit_code)
        else:
            # 默认纯文本格式(让 Click 处理)
            raise
    except SystemExit:
        # 正常退出,重新抛出
        raise
    except Exception as e:
        # 未预期的异常
        if "--json-output" in sys.argv:
            error_data = {
                "success": False,
                "error": e.__class__.__name__,
                "message": str(e)
            }
            print(json.dumps(error_data, ensure_ascii=False))
            sys.exit(1)
        else:
            raise
```

**注意:**
1. `standalone_mode=False` 让 ClickException 传播到调用者
2. 使用 `sys.argv` 检查 `--json-output` 标志(因为 ctx.obj 还未初始化)
3. 保留原始退出码 (`e.exit_code`)
4. 处理所有异常类型,确保未预期错误也被转换为 JSON

**错误格式规范:**
```json
{
  "success": false,
  "error": "MissingOption",  // Click 异常类名
  "message": "Missing option '--type'."  // 错误详细信息
}
```

**Click 常见异常类型:**
- `ClickException`: 通用 Click 异常
- `UsageError`: 命令用法错误
- `BadParameter`: 参数值错误
- `MissingOption`: 缺少必需选项
- `NoSuchOption`: 未知选项
</action>
<verify>
```bash
# 测试参数验证错误的 JSON 输出
pixiv-downloader --json-output download http://invalid-url.com

# 预期输出: {"success": false, "error": "MissingOption", "message": "Missing option '--type'."}

# 测试非 JSON 模式(保持原有格式)
pixiv-downloader download http://invalid-url.com

# 预期输出: 纯文本格式 "Usage: ...\nError: Missing option '--type'."
```
</verify>
<done>
--json-output 模式下,Click 参数验证错误以 JSON 格式输出
</done>
</task>
```

### Task 2: 验证多种错误场景

**What:** 测试不同类型的 Click 错误,确保都能正确转换为 JSON

**Implementation:**

```xml
<task type="auto">
<name>Task 2: 验证多种错误场景</name>
<files></files>
<action>
测试多种 Click 错误场景,确保异常处理逻辑完整。

**测试场景:**

**1. 缺少必需参数:**
```bash
pixiv-downloader --json-output download http://example.com
# 预期: {"success": false, "error": "MissingOption", "message": "Missing option '--type'."}
```

**2. 无效的参数值:**
```bash
pixiv-downloader --json-output download --type invalid http://example.com
# 预期: {"success": false, "error": "BadParameter", "message": "..."}
```

**3. 未知命令:**
```bash
pixiv-downloader --json-output unknown-command
# 预期: {"success": false, "error": "NoSuchCommand", "message": "No such command 'unknown-command'."}
```

**4. 未知选项:**
```bash
pixiv-downloader --json-output --unknown-option version
# 预期: {"success": false, "error": "NoSuchOption", "message": "No such option: --unknown-option"}
```

**5. 非 JSON 模式(保持原有格式):**
```bash
pixiv-downloader download http://example.com
# 预期: 纯文本格式 "Usage: ...\nError: Missing option '--type'."
```

**验证命令:**
```bash
# 循环测试所有场景
for test_cmd in \
  "download http://example.com" \
  "download --type invalid http://example.com" \
  "unknown-command" \
  "--unknown-option version"
do
  echo "Testing: $test_cmd"
  echo "JSON output:"
  pixiv-downloader --json-output $test_cmd 2>&1 | python -m json.tool || echo "Not valid JSON"
  echo ""
done
```
</action>
<verify>
```bash
# 验证所有错误场景都输出有效 JSON
pixiv-downloader --json-output download http://example.com 2>&1 | python -c "import json, sys; data = json.load(sys.stdin); print('Valid JSON:', data.get('success') == False)"
```
</verify>
<done>
所有 Click 错误场景在 --json-output 模式下都输出有效 JSON
</done>
</task>
```

### Task 3: 更新 INTEGRATION.md 文档

**What:** 更新文档说明错误响应格式

**Files:** `INTEGRATION.md`

**Implementation:**

```xml
<task type="auto">
<name>Task 3: 更新 INTEGRATION.md 错误格式文档</name>
<files>INTEGRATION.md</files>
<action>
在 INTEGRATION.md 中添加或更新错误响应格式说明。

**添加内容:**
```markdown
## 错误处理

### JSON 错误响应

在 `--json-output` 模式下,**所有**错误(包括参数验证错误)都以 JSON 格式输出:

```json
{
  "success": false,
  "error": "MissingOption",
  "message": "Missing option '--type'."
}
```

**错误字段说明:**
- `success`: 布尔值,始终为 `false`
- `error`: 错误类型(Click 异常类名)
- `message`: 人类可读的错误详细信息

**常见错误类型:**
- `MissingOption`: 缺少必需选项
- `BadParameter`: 参数值无效
- `NoSuchOption`: 未知选项
- `NoSuchCommand`: 未知命令
- `UsageError`: 命令用法错误

**错误处理示例 (Python):**
```python
import subprocess
import json

result = subprocess.run(
    ["pixiv-downloader", "--json-output", "download", "http://example.com"],
    capture_output=True,
    text=True
)

if result.returncode != 0:
    # 解析错误响应
    error_data = json.loads(result.stdout)
    print(f"Error: {error_data['error']}")
    print(f"Message: {error_data['message']}")
```
```

**注意:**
- 强调**所有**错误(包括参数验证错误)都是 JSON 格式
- 提供常见错误类型列表
- 提供错误处理示例代码
</action>
<verify>
```bash
# 检查文档包含错误格式说明
grep -A 10 "错误处理" INTEGRATION.md
```
</verify>
<done>
INTEGRATION.md 包含完整的 JSON 错误格式说明和示例
</done>
</task>
```

### Task 4: 运行 UAT 测试验证

**What:** 运行完整的 UAT 测试,确保 Test 5 通过

**Implementation:**

```xml
<task type="auto">
<name>Task 4: 运行 UAT 测试验证</name>
<files></files>
<action>
执行 UAT Test 5 验证,确保错误信息的 JSON 格式符合预期。

**UAT Test 5 验证:**
```bash
# 测试命令
pixiv-downloader --json-output download http://invalid-url.com

# 验证输出是有效 JSON
output=$(pixiv-downloader --json-output download http://invalid-url.com 2>&1)
echo "$output" | python -m json.tool

# 验证 JSON 字段
echo "$output" | python -c "
import json, sys
data = json.load(sys.stdin)
assert data.get('success') == False, 'success should be false'
assert 'error' in data, 'should have error field'
assert 'message' in data, 'should have message field'
print('✅ Test 5 passed: Error output is valid JSON')
"
```

**完整 UAT 测试:**
```bash
# 运行所有 UAT 测试
cat .planning/phases/10-api-validation/10-UAT.md

# 验证所有测试
echo "Running UAT tests..."
echo "Test 1: version JSON output"
pixiv-downloader --json-output version | python -m json.tool && echo "✅ Pass"

echo "Test 2: status JSON output"
pixiv-downloader --json-output status | python -m json.tool && echo "✅ Pass"

echo "Test 3: config JSON output"
pixiv-downloader --json-output config | python -m json.tool && echo "✅ Pass"

echo "Test 5: Error JSON output"
pixiv-downloader --json-output download http://invalid-url.com 2>&1 | python -m json.tool && echo "✅ Pass"
```
</action>
<verify>
```bash
# 最终验证: UAT Test 5
pixiv-downloader --json-output download http://invalid-url.com 2>&1 | python -c "
import json, sys
data = json.load(sys.stdin)
assert data.get('success') == False
assert 'error' in data
assert 'message' in data
print('UAT Test 5: PASS')
"
```
</verify>
<done>
UAT Test 5 通过,所有错误信息在 --json-output 模式下都是 JSON 格式
</done>
</task>
```

## Must-Haves (Gap Closure Verification)

完成此 gap closure 后,以下条件必须为 TRUE:

| Must-Have | Verification Method | Success Criteria |
| --- | --- | --- |
| main.py 包含异常处理逻辑 | 代码检查 | __main__ 部分有 try/except ClickException |
| Click 错误转换为 JSON | `pixiv-downloader --json-output download http://...` | 输出有效 JSON,包含 success/error/message |
| 非 JSON 模式保持原有格式 | `pixiv-downloader download http://...` | 输出纯文本格式 |
| JSON 可被解析 | `... \| python -m json.tool` | 成功解析,无 JSON 语法错误 |
| UAT Test 5 通过 | UAT 测试 | 错误信息 JSON 格式测试通过 |

## Dependencies

**Depends on:**
- 10-01: JSON 输出格式验证 (已完成)
- 10-01-GAP01: 测试框架修复 (已完成)
- 10-01-GAP02: status/config JSON 输出实现 (已完成)

**Blocks:**
- Phase 10 UAT 完成
- VAL-01 需求完全满足

## Risks

### Risk 1: sys.argv 检查可能不准确

**Impact:** 在复杂命令行参数下可能误判 --json-output 标志

**Mitigation:**
1. 使用 `"--json-output" in sys.argv` 简单检查
2. 不需要精确解析参数位置,只需判断标志是否存在
3. 如果需要更精确的检查,可以使用 click.Context

**Probability:** LOW - 简单的 `in` 检查足够

### Risk 2: 未捕获的异常类型

**Impact:** 某些异常未被转换为 JSON 格式

**Mitigation:**
1. 捕获 `Exception` 基类作为兜底
2. 在 except Exception 中也检查 --json-output 标志
3. 记录未预期异常以便调试

**Probability:** MEDIUM - 需要测试多种异常场景

### Risk 3: 多线程或异步环境

**Impact:** sys.argv 在多线程环境下可能不安全

**Mitigation:**
1. 当前实现是单线程 CLI,不受影响
2. 如果未来支持多线程,需要使用线程局部存储

**Probability:** LOW - 当前无多线程需求

## Files Modified Summary

```
src/gallery_dl_auo/cli/main.py
├── Line 105-107: 替换为完整的异常处理逻辑
├── 添加 try/except ClickException
├── 检查 sys.argv 中的 --json-output
├── JSON 格式错误输出
└── 非 JSON 模式保持原有行为

INTEGRATION.md
└── 添加错误处理和 JSON 错误格式说明
```

## Verification Commands

```bash
# 1. 验证参数验证错误
pixiv-downloader --json-output download http://example.com 2>&1 | python -m json.tool

# 2. 验证未知命令错误
pixiv-downloader --json-output unknown-command 2>&1 | python -m json.tool

# 3. 验证未知选项错误
pixiv-downloader --json-output --unknown-option version 2>&1 | python -m json.tool

# 4. 验证非 JSON 模式
pixiv-downloader download http://example.com
# 预期: 纯文本格式

# 5. 验证所有错误都是有效 JSON
for cmd in "download http://x" "unknown" "--bad version"; do
  echo "Testing: $cmd"
  pixiv-downloader --json-output $cmd 2>&1 | python -c "import json, sys; json.load(sys.stdin); print('Valid JSON')" || echo "Invalid JSON"
done
```

## Success Criteria

- [ ] main.py 包含全局 Click 异常处理
- [ ] --json-output 模式下参数验证错误输出 JSON
- [ ] JSON 错误包含 success/error/message 字段
- [ ] 非 JSON 模式保持原有纯文本格式
- [ ] 多种错误场景都正确处理
- [ ] INTEGRATION.md 文档更新
- [ ] UAT Test 5 通过

## Execution Notes

**给执行者的提示:**
1. **关键修改**: main.py 的 `__main__` 部分是唯一需要修改的地方
2. **standalone_mode=False**: 这是关键,让异常传播到调用者
3. **sys.argv 检查**: 使用简单的 `in` 检查即可,不需要精确解析
4. **测试策略**: 修改后立即测试多种错误场景
5. **退出码**: 保留 Click 的原始退出码 (`e.exit_code`)
6. **异常类型**: 捕获 ClickException 和 Exception,确保完整覆盖

**预计时间:** ~10 分钟
- main.py 修改: 5 分钟
- 多场景测试: 3 分钟
- 文档更新: 2 分钟

---

**Plan Type:** Gap Closure (Bug Fix)
**Wave:** 4
**Estimated Duration:** ~10 minutes
**Executor Notes:** 添加全局异常处理,确保所有 Click 错误在 --json-output 模式下转换为 JSON 格式
