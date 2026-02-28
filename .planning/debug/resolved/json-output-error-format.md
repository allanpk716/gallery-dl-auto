---
status: resolved
trigger: "--json-output 模式下错误信息不是 JSON 格式"
created: 2026-02-27T00:00:00Z
updated: 2026-02-27T15:10:00Z
resolved_date: 2026-02-27T15:10:00Z
symptoms_prefilled: true
goal: find_root_cause_only
---

## Current Focus

hypothesis: main.py 缺少自定义的 Click 异常处理,导致 Click 参数验证错误以默认纯文本格式输出而非 JSON 格式
test: 检查 main.py 的 __main__ 部分,验证是否直接调用 cli() 而没有捕获 ClickException
expecting: 确认 main.py 的 __main__ 部分需要添加异常处理逻辑,捕获 ClickException 并根据 --json-output 参数转换为 JSON 格式
next_action: 检查 main.py 的 __main__ 部分实现

## Symptoms

expected: 在 --json-output 模式下,参数验证错误应以 JSON 格式输出,包含 error 字段
actual: 参数验证错误仍以 Click 默认的纯文本格式输出
errors: "Usage: pixiv-downloader download [OPTIONS]\nTry 'pixiv-downloader download --help' for help.\n\nError: Missing option '--type'."
reproduction: 运行 `pixiv-downloader --json-output download http://invalid-url.com`
started: 未知,功能实现后一直存在

## Eliminated

## Evidence

- timestamp: 2026-02-27T00:05:00Z
  checked: 运行命令 `pixiv-downloader --json-output download http://invalid-url.com`
  found: 错误信息以 Click 默认纯文本格式输出,而非 JSON 格式。错误消息出现两次(可能是 stderr 和 stdout 都输出)
  implication: Click 框架的参数验证错误在 CLI 命令处理前就抛出,无法被命令内的错误处理捕获

- timestamp: 2026-02-27T00:10:00Z
  checked: Click 框架的 standalone_mode 参数和异常处理机制
  found: Click 默认使用 standalone_mode=True,会自动捕获所有 ClickException 并以纯文本格式输出错误。设置 standalone_mode=False 可以让异常传播到调用者,从而自定义错误格式
  implication: 需要在 CLI 入口处包装 cli() 调用,捕获 ClickException 并根据 --json-output 参数转换为 JSON 格式

- timestamp: 2026-02-27T00:15:00Z
  checked: 创建测试文件验证方案可行性
  found: 使用 standalone_mode=False + 捕获 ClickException + 检查 sys.argv 中的 --json-output 标志,可以成功将 Click 参数验证错误转换为 JSON 格式
  implication: 解决方案已验证,需要在 main.py 的 __main__ 部分实现此方案

- timestamp: 2026-02-27T00:20:00Z
  checked: main.py 的 __main__ 部分(第 105-106 行)
  found: __main__ 部分只是简单地调用 cli(),没有自定义的异常处理逻辑
  implication: 这是根本原因 - 所有 Click 参数验证错误都会被 Click 默认处理,无法转换为 JSON 格式

## Resolution

root_cause: main.py 的 __main__ 部分直接调用 cli(),没有自定义异常处理逻辑。当 Click 参数验证失败时(如缺少必需参数 --type),Click 框架使用默认的纯文本格式输出错误信息,无法根据 --json-output 标志转换为 JSON 格式。这是因为:(1) Click 默认使用 standalone_mode=True,自动捕获并处理所有 ClickException;(2) 异常处理发生在 ctx.obj['output_mode'] 设置之前,无法访问 output_mode 状态;(3) 缺少全局的 Click 异常拦截器来将错误转换为 JSON 格式。
fix: "在 main.py 中实现全局异常处理:(1) 创建 main() 函数包装 cli() 调用;(2) 使用 cli(standalone_mode=False) 让异常传播;(3) 捕获 ClickException 和 Exception;(4) 检查 sys.argv 中的 --json-output 标志;(5) 将错误转换为 JSON 格式 {success: false, error: ..., message: ...}"
verification: "测试多种错误场景(缺少参数、无效参数、未知命令、未知选项),所有错误在 --json-output 模式下都输出为 JSON 格式,非 JSON 模式保持原有纯文本格式。UAT Test 5 通过。"
resolved_by: "10-02-GAP02"
files_changed: ["src/gallery_dl_auo/cli/main.py"]
