---
status: resolved
phase: 10-api-validation
source: 10-01-SUMMARY.md, GAP-CLOSURE-SUMMARY.md, 10-PLANS-SUMMARY.md
started: 2026-02-27T14:07:00Z
updated: 2026-02-27T15:10:00Z
---

## Current Test

[testing complete]

## Tests

### 1. version 命令 JSON 输出
expected: pixiv-downloader --json-output version 命令输出有效 JSON 格式,包含版本信息,而非表格格式
result: pass

### 2. status 命令 JSON 输出
expected: pixiv-downloader --json-output status 命令输出有效 JSON 格式,包含认证状态和用户信息(如已登录),而非表格格式
result: pass

### 3. config 命令 JSON 输出
expected: pixiv-downloader --json-output config 命令输出有效 JSON 格式,列出所有配置项及其值,而非表格格式
result: pass

### 4. 退出码验证
expected: 当命令执行失败时(如缺少 token),CLI 返回非零退出码;成功时返回 0。第三方工具可通过退出码判断执行状态
result: pass

### 5. 错误信息的 JSON 格式
expected: 在 --json-output 模式下,错误信息也以 JSON 格式输出,包含 error 字段和详细信息,而非纯文本错误消息
result: pass

### 6. JSON 输出字段完整性
expected: JSON 输出包含 INTEGRATION.md 文档中定义的所有必需字段,第三方工具可依赖这些字段进行解析和处理
result: pass

## Summary

total: 6
passed: 6
issues: 0
pending: 0
skipped: 0

## Gaps

- truth: "status 命令 JSON 输出在 token 有效时应提供明确的 username 信息或移除该字段"
  status: resolved
  resolved_by: "10-02-GAP01"
  resolution: "实现了用户信息提取、存储和显示功能。status 命令现在显示 username, user_account, user_id 字段,并支持旧 token 文件的向后兼容"
  severity: major
  test: 2
  root_cause: "用户信息提取功能未实现。Pixiv OAuth API 响应包含 user 字段(name, account, id),但 validate_refresh_token() 未提取,token_storage.py 未存储,status_cmd.py 硬编码 username=None"
  artifacts:
    - path: "src/gallery_dl_auo/auth/pixiv_auth.py"
      issue: "validate_refresh_token() 方法忽略 API 响应中的 user 字段"
    - path: "src/gallery_dl_auo/cli/status_cmd.py"
      issue: "硬编码 username: None,未使用用户信息"
    - path: "src/gallery_dl_auo/auth/token_storage.py"
      issue: "只存储 token,未存储用户信息"
  missing:
    - "提取 user 字段: validate_refresh_token() 返回 user 信息"
    - "存储用户信息: TokenStorage.save_token() 支持 user 字段"
    - "显示用户信息: status_cmd.py 使用存储的用户信息"
    - "向后兼容: 处理旧 token 文件无 user 字段的情况"
  debug_session: ".planning/debug/status-username-null.md"

- truth: "--json-output 模式下所有输出(包括错误)应为 JSON 格式"
  status: resolved
  resolved_by: "10-02-GAP02"
  resolution: "在 main.py 中实现全局 Click 异常处理,使用 standalone_mode=False 让异常传播,并根据 --json-output 标志转换为 JSON 格式"
  severity: major
  test: 5
  root_cause: "main.py 的 __main__ 部分直接调用 cli(),没有自定义异常处理逻辑。Click 框架默认使用 standalone_mode=True,参数验证错误在 output_mode 设置前就抛出,以纯文本格式输出,无法转换为 JSON 格式"
  artifacts:
    - path: "src/gallery_dl_auo/cli/main.py"
      issue: "第 105-106 行,缺少异常处理逻辑,未使用 standalone_mode=False"
  missing:
    - "使用 cli(standalone_mode=False) 让异常传播到调用者"
    - "捕获 click.ClickException 异常"
    - "检查 sys.argv 中的 --json-output 标志"
    - "将错误转换为 JSON 格式输出: {success: false, error: ..., message: ...}"
  debug_session: ".planning/debug/json-output-error-format.md"
