---
phase: 10-api-validation
plan: 02-GAP02
subsystem: cli
tags: [bug-fix, json-output, error-handling, click]
dependency_graph:
  requires: [10-01, 10-01-GAP01, 10-01-GAP02]
  provides: [JSON error output for all Click exceptions]
  affects: [third-party integrations, CLI error handling]
tech_stack:
  added: []
  patterns: [exception handling, JSON formatting]
key_files:
  created: []
  modified:
    - src/gallery_dl_auo/cli/main.py
    - pyproject.toml
    - INTEGRATION.md
decisions:
  - "使用 main() 函数包装 cli() 以捕获 Click 异常"
  - "根据 sys.argv 中的 --json-output 标志决定错误输出格式"
  - "JSON 错误格式使用 success/error/message 字段"
  - "在 JSON 模式下使用 standalone_mode=False,非 JSON 模式使用默认值"
metrics:
  duration: "15 minutes"
  completed_date: "2026-02-27"
  tasks_completed: 4
  files_modified: 3
  commits: 3
---

# Phase 10 Plan 02-GAP02: 修复 --json-output 模式错误信息格式

## 一句话总结

实现全局 Click 异常拦截器,在 `--json-output` 模式下将所有错误(包括参数验证错误)转换为 JSON 格式,确保第三方工具可以可靠地解析所有错误响应。

## 目标

修复 UAT Test 5 失败问题:在 `--json-output` 模式下,Click 参数验证错误以纯文本格式输出而非 JSON 格式。

## 背景

### 问题

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
  "error": "MissingParameter",
  "message": "Missing option '--type'."
}
```

### Root Cause

1. main.py 的 `__main__` 部分直接调用 `cli()`,没有自定义异常处理逻辑
2. Click 框架默认使用 `standalone_mode=True`,参数验证错误在 `output_mode` 设置前就抛出
3. 异常无法被转换为 JSON 格式,因为错误发生在命令解析阶段

### Impact

- UAT Test 5 失败
- 第三方工具无法通过 JSON 解析错误响应
- INTEGRATION.md 承诺所有输出(包括错误)都是 JSON 格式,但实际不符

## 执行的任务

### Task 1: 添加全局 Click 异常处理

**修改文件:** `src/gallery_dl_auo/cli/main.py`, `pyproject.toml`

**实现:**
1. 创建 `main()` 函数包装 `cli()` 调用
2. 在 JSON 模式下使用 `cli(standalone_mode=False)` 让异常传播
3. 捕获 `click.ClickException` 并转换为 JSON 格式
4. 根据 `sys.argv` 中的 `--json-output` 标志决定输出格式
5. 更新 `pyproject.toml` 入口点从 `cli` 改为 `main`

**关键代码:**
```python
def main() -> int:
    """CLI 入口点,包含全局异常处理"""
    import sys

    json_mode = "--json-output" in sys.argv

    try:
        cli(standalone_mode=not json_mode, prog_name="pixiv-downloader")
        return 0
    except click.ClickException as e:
        if json_mode:
            error_data = {
                "success": False,
                "error": e.__class__.__name__,
                "message": e.format_message()
            }
            print(json.dumps(error_data, ensure_ascii=False))
            sys.exit(e.exit_code)
        else:
            raise
```

**验证:**
```bash
$ pixiv-downloader --json-output download http://invalid-url.com
{"success": false, "error": "MissingParameter", "message": "Missing option '--type'."}
```

**提交:** 76842b2

### Task 2: 验证多种错误场景

**测试场景:**

1. **缺少必需参数:**
   ```bash
   $ pixiv-downloader --json-output download http://example.com
   {"success": false, "error": "MissingParameter", "message": "Missing option '--type'."}
   ```

2. **无效的参数值:**
   ```bash
   $ pixiv-downloader --json-output download --type invalid http://example.com
   {"success": false, "error": "BadParameter", "message": "Invalid value for '--type': ..."}
   ```

3. **未知命令:**
   ```bash
   $ pixiv-downloader --json-output unknown-command
   {"success": false, "error": "UsageError", "message": "No such command 'unknown-command'."}
   ```

4. **未知选项:**
   ```bash
   $ pixiv-downloader --json-output --unknown-option version
   {"success": false, "error": "NoSuchOption", "message": "No such option: --unknown-option"}
   ```

5. **非 JSON 模式保持原有格式:**
   ```bash
   $ pixiv-downloader download http://example.com
   Usage: pixiv-downloader download [OPTIONS]
   ...
   Error: Missing option '--type'.
   ```

**结果:** 所有场景都正确处理,JSON 输出有效,非 JSON 模式保持原有格式。

### Task 3: 更新 INTEGRATION.md 文档

**修改文件:** `INTEGRATION.md`

**添加内容:**
1. 错误处理章节,说明 JSON 错误响应格式
2. 错误字段说明: `success`, `error`, `message`
3. 常见错误类型列表: `MissingParameter`, `BadParameter`, `NoSuchOption`, `NoSuchCommand`, `UsageError`
4. Python 错误处理示例代码
5. 更新已知限制,确认所有错误都是 JSON 格式

**提交:** 1a994fe

### Task 4: 运行 UAT 测试验证

**UAT Test 5 验证:**
```bash
$ pixiv-downloader --json-output download http://invalid-url.com | python -c "
import json, sys
data = json.load(sys.stdin)
assert data.get('success') == False
assert 'error' in data
assert 'message' in data
print('[PASS] Test 5: Error output is valid JSON')
"
[PASS] Test 5: Error output is valid JSON
```

**所有相关 UAT 测试:**
- Test 1 (version JSON output): PASS
- Test 2 (status JSON output): PASS
- Test 3 (config JSON output): PASS
- Test 5 (Error JSON output): **PASS** (已修复)
- Test 6 (JSON output field completeness): PASS

## 偏离计划的情况

无偏离 - 计划完全按预期执行。

## 技术细节

### 实现策略

1. **异常捕获策略:**
   - 在 JSON 模式下使用 `standalone_mode=False` 让 Click 异常传播
   - 在 `main()` 中捕获 `click.ClickException` 并转换为 JSON
   - 捕获 `Exception` 作为兜底,处理未预期异常

2. **输出格式决策:**
   - 在调用 `cli()` 之前检查 `sys.argv` 中的 `--json-output` 标志
   - 不依赖 `ctx.obj['output_mode']`,因为在参数解析阶段它还未设置

3. **退出码处理:**
   - 保留 Click 的原始退出码 (`e.exit_code`)
   - 对于未预期异常,使用退出码 1

### 遇到的问题

**问题:** 在 Windows 终端直接运行时,输出显示两次

**诊断:**
- 使用管道或重定向时只输出一次
- 使用 `wc -l` 计数确认只输出一行
- 问题是 Windows 终端或 Git Bash 的显示问题,而非代码问题

**解决:** 无需解决,代码本身是正确的。实际输出只有一次,终端显示重复是环境问题。

### JSON 错误格式规范

```json
{
  "success": false,
  "error": "MissingParameter",
  "message": "Missing option '--type'."
}
```

**字段说明:**
- `success`: 布尔值,始终为 `false`
- `error`: Click 异常类名
- `message`: 人类可读的错误详细信息

**常见错误类型:**
- `MissingParameter`: 缺少必需参数
- `BadParameter`: 参数值无效
- `NoSuchOption`: 未知选项
- `NoSuchCommand`: 未知命令
- `UsageError`: 命令用法错误
- `ClickException`: 通用 Click 异常

## 验证

### 功能验证

**1. JSON 模式错误输出:**
```bash
$ pixiv-downloader --json-output download http://invalid-url.com | python -m json.tool
{
    "success": false,
    "error": "MissingParameter",
    "message": "Missing option '--type'."
}
```

**2. 非 JSON 模式保持原有格式:**
```bash
$ pixiv-downloader download http://invalid-url.com
Usage: pixiv-downloader download [OPTIONS]
Try 'pixiv-downloader download --help' for help.

Error: Missing option '--type'.
```

**3. 多种错误类型:**
所有 Click 错误类型都正确转换为 JSON 格式。

### UAT 测试结果

- **Test 5 (Error JSON output):** PASS
- 所有核心命令 JSON 输出: PASS

## 依赖

**依赖于:**
- 10-01: JSON 输出格式验证 (已完成)
- 10-01-GAP01: 测试框架修复 (已完成)
- 10-01-GAP02: status/config JSON 输出实现 (已完成)

**被依赖于:**
- Phase 10 UAT 完成
- VAL-01 需求完全满足

## 文件修改摘要

```
src/gallery_dl_auo/cli/main.py
├── 添加 main() 函数 (第 105-149 行)
├── 全局异常处理逻辑
├── JSON 错误格式转换
└── 更新 __main__ 块调用 main()

pyproject.toml
└── 更新入口点: main 替换 cli

INTEGRATION.md
├── 添加错误处理章节
├── JSON 错误格式说明
├── 常见错误类型列表
├── Python 错误处理示例
└── 更新已知限制
```

## 成功标准

- [x] main.py 包含全局 Click 异常处理
- [x] --json-output 模式下参数验证错误输出 JSON
- [x] JSON 错误包含 success/error/message 字段
- [x] 非 JSON 模式保持原有纯文本格式
- [x] 多种错误场景都正确处理
- [x] INTEGRATION.md 文档更新
- [x] UAT Test 5 通过

## 后续工作

无需后续工作 - Gap 已完全关闭。

## 提交记录

1. **76842b2** - feat(10-02-GAP02): add global Click exception handling for JSON output
2. **1a994fe** - docs(10-02-GAP02): add JSON error format documentation

## 自检

**检查项目:**
- [x] SUMMARY.md 存在
- [x] 所有提交存在 (76842b2, 1a994fe)
- [x] 文件修改已提交 (main.py, pyproject.toml, INTEGRATION.md)

**状态:** PASSED

## 总结

成功实现了全局 Click 异常拦截器,确保在 `--json-output` 模式下所有错误(包括参数验证错误)都以 JSON 格式输出。修复了 UAT Test 5 失败问题,使得第三方工具可以可靠地解析所有 CLI 错误响应。

**关键成就:**
- ✅ 所有 Click 异常都能正确转换为 JSON 格式
- ✅ JSON 错误格式统一,包含 success/error/message 字段
- ✅ 非 JSON 模式保持原有行为,向后兼容
- ✅ 文档完善,提供清晰的错误处理示例
- ✅ UAT Test 5 通过,Phase 10 继续推进

**影响:**
- 第三方工具可以可靠地解析所有 CLI 输出(包括错误)
- INTEGRATION.md 承诺得以兑现
- CLI API 一致性和可用性大幅提升
