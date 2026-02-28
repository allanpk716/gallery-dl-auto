---
wave: 3
depends_on: ["10-01", "10-01-GAP01"]
files_modified:
  - src/gallery_dl_auo/cli/status_cmd.py
  - src/gallery_dl_auo/cli/config_cmd.py
  - tests/validation/test_json_schemas.py
autonomous: true
requirements: [VAL-01]
plan_type: gap_closure
parent_plan: 10-01
gap_summary: status 和 config 命令未实现 --json-output 模式,导致 5/9 JSON Schema 测试被跳过
verification_file: .planning/phases/10-api-validation/10-API-VALIDATION-VERIFICATION.md
must_haves:
  truths:
    - status 命令在 --json-output 模式下输出有效的 JSON,包含 logged_in、token_valid 等字段
    - config 命令在 --json-output 模式下输出有效的 JSON,包含 config 键值对
    - 所有 9 个 JSON Schema 测试执行并验证通过(或合理跳过)
    - INTEGRATION.md 承诺的全局参数 --json-output 在所有命令上工作
  artifacts:
    - src/gallery_dl_auo/cli/status_cmd.py (支持 --json-output)
    - src/gallery_dl_auo/cli/config_cmd.py (支持 --json-output)
    - tests/validation/test_json_schemas.py (移除 skip 标记)
    - pytest 测试报告显示 9/9 passed 或 8/9 passed(保留 download error 跳过)
  key_links:
    - status/config 命令检查 ctx.obj["output_mode"] 以决定输出格式
    - version 命令已实现 JSON 输出,作为参考模式
    - JSON Schema 已在 conftest.py 中定义,指导输出结构
---

# Gap Closure Plan: 实现 status 和 config 命令的 JSON 输出

**Created:** 2026-02-27
**Type:** Gap Closure (Feature Implementation)
**Parent Plan:** 10-01 (JSON 输出格式验证)
**Priority:** HIGH - 阻止 VAL-01 完整验证
**Previous Gap:** 10-01-GAP01 (测试框架修复 - 已完成)

## Gap Analysis

### Problem
在 10-01-GAP01 成功修复测试框架后,重新验证发现 status 和 config 命令**未实现** --json-output 功能:

1. **status 命令**:
   - 当前行为: 总是输出 Rich 表格,忽略 --json-output 参数
   - 代码分析: 未检查 `ctx.obj["output_mode"]`,直接使用 `Console.print(table)`
   - 影响: 2/9 测试被跳过 (test_command_json_output_parsable[status], test_status_command_schema)

2. **config 命令**:
   - 当前行为: 总是输出 Rich 表格,忽略 --json-output 参数
   - 代码分析: 未检查 `ctx.obj["output_mode"]`,直接使用 `Console.print(table)`
   - 影响: 3/9 测试被跳过 (test_command_json_output_parsable[config], test_config_get_command_schema, test_config_list_command_schema)

3. **文档不一致**:
   - INTEGRATION.md 第 46 行承诺: "--json-output ... 所有命令都支持"
   - INTEGRATION.md 第 158 行说明: "当前版本命令尚未完全实现 JSON 输出逻辑"
   - 实际状态: version 和 download 命令已支持,status 和 config 未支持

### Root Cause
- status 和 config 命令在 Phase 2-3 期间开发,当时未考虑 JSON 输出需求
- Phase 8.1 (CLI API 增强) 计划实现 --json-output 全局参数,但未完全执行
- version 命令已实现 JSON 输出模式,可作为参考模式

### Impact
- **阻塞**: VAL-01 需求无法完全验证 (2.5/3 requirements)
- **测试跳过**: 5/9 JSON Schema 测试因功能未实现而被跳过
- **文档不一致**: INTEGRATION.md 的承诺与实际不符
- **第三方集成**: 第三方工具无法使用 --json-output 调用 status/config 命令

## Goal

实现 status 和 config 命令的 --json-output 支持,使所有命令符合 INTEGRATION.md 的承诺,完成 VAL-01 验证。

**Success Criteria:**
1. ✅ status 命令在 --json-output 模式下输出有效 JSON,符合 _status_output_schema
2. ✅ config 命令在 --json-output 模式下输出有效 JSON,符合 _config_*_output_schema
3. ✅ 移除测试中的 @pytest.mark.skip 标记
4. ✅ 9/9 JSON Schema 测试通过(或 8/9,保留 download error 合理跳过)
5. ✅ INTEGRATION.md 第 158 行的限制说明可移除或更新
6. ✅ VAL-01 需求完全满足

**Implementation Strategy:**
- 参考 version 命令的实现模式 (检查 ctx.obj["output_mode"])
- 使用已定义的 JSON Schema 指导输出结构
- 保持 Rich 表格输出为默认模式,JSON 输出为可选模式

## Tasks

### Task 1: 实现 status 命令的 JSON 输出

**What:** 为 status 命令添加 --json-output 支持

**Files:** `src/gallery_dl_auo/cli/status_cmd.py`

**Reference Pattern:** `src/gallery_dl_auo/cli/version.py`

**Implementation:**

```xml
<task>
<step>
1. 添加 click.pass_context 装饰器,获取 ctx 对象
2. 在显示结果前检查 ctx.obj["output_mode"]
3. 如果是 "json",输出 JSON 格式;否则输出 Rich 表格
</step>
<code location="src/gallery_dl_auo/cli/status_cmd.py">
# Line 19: 添加 @click.pass_context
@click.command()
@click.option(
    "--verbose", "-v", is_flag=True, help="Show detailed token information"
)
@click.pass_context
def status(ctx: click.Context, verbose: bool) -> None:
    """Check Pixiv token status

    Shows whether a valid token exists and can be refreshed
    """
    console = Console()
    storage = get_default_token_storage()

    # Check if token file exists
    if not storage.storage_path.exists():
        if ctx.obj.get("output_mode") == "json":
            import json
            error_data = {
                "logged_in": False,
                "token_valid": False,
                "username": None,
                "error": "No token found",
                "suggestion": "Run 'pixiv-downloader login' to login"
            }
            click.echo(json.dumps(error_data, ensure_ascii=False))
        else:
            console.print("[yellow]No token found.[/yellow]")
            console.print("[dim]Run 'pixiv-downloader login' to login.[/dim]")
        return

    # Load token
    token_data = storage.load_token()
    if not token_data:
        if ctx.obj.get("output_mode") == "json":
            import json
            error_data = {
                "logged_in": False,
                "token_valid": False,
                "username": None,
                "error": "Token file exists but cannot be decrypted",
                "suggestion": "Run 'pixiv-downloader login --force' to re-login"
            }
            click.echo(json.dumps(error_data, ensure_ascii=False))
        else:
            console.print(
                "[red]Token file exists but cannot be decrypted.[/red]"
            )
            console.print(
                "[dim]This may happen if machine info changed or file is corrupted.[/dim]"
            )
            console.print(
                "[dim]Run 'pixiv-downloader login --force' to re-login.[/dim]"
            )
        return

    refresh_token = token_data.get("refresh_token")
    if not refresh_token:
        if ctx.obj.get("output_mode") == "json":
            import json
            error_data = {
                "logged_in": False,
                "token_valid": False,
                "username": None,
                "error": "Invalid token data (missing refresh_token)"
            }
            click.echo(json.dumps(error_data, ensure_ascii=False))
        else:
            console.print(
                "[red]Invalid token data (missing refresh_token).[/red]"
            )
        return

    # Validate token
    if ctx.obj.get("output_mode") != "json":
        console.print("[dim]Validating token...[/dim]")

    result = PixivOAuth.validate_refresh_token(refresh_token)

    # JSON output mode
    if ctx.obj.get("output_mode") == "json":
        import json

        status_data = {
            "logged_in": result["valid"],
            "token_valid": result["valid"],
            "username": None,  # Not available in current implementation
        }

        if not result["valid"]:
            status_data["error"] = result.get("error", "Unknown")
            status_data["suggestion"] = "Run 'pixiv-downloader login --force' to re-login"

        click.echo(json.dumps(status_data, ensure_ascii=False))

        # Still refresh token if valid (silently)
        if result["valid"] and result["refresh_token"]:
            storage.save_token(
                refresh_token=result["refresh_token"],
                access_token=result.get("access_token"),
            )
    else:
        # Rich table output mode (original code)
        table = Table(title="Token Status")
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="green")

        if result["valid"]:
            table.add_row("Status", "[green]Valid[/green]")
            table.add_row("Token File", str(storage.storage_path))

            if verbose:
                # Show partial token (privacy protection)
                masked_token = (
                    refresh_token[:10] + "..." + refresh_token[-10:]
                )
                table.add_row("Refresh Token", masked_token)

                if result.get("expires_in"):
                    expiry = datetime.datetime.now() + datetime.timedelta(
                        seconds=result["expires_in"]
                    )
                    table.add_row("Expires", expiry.strftime("%Y-%m-%d %H:%M:%S"))

            # If token is valid, update storage (auto-refresh)
            if result["refresh_token"]:
                storage.save_token(
                    refresh_token=result["refresh_token"],
                    access_token=result.get("access_token"),
                )
                console.print("[dim]Token refreshed and saved.[/dim]")

        else:
            table.add_row("Status", "[red]Invalid[/red]")
            table.add_row("Error", result.get("error", "Unknown"))
            table.add_row(
                "Suggestion", "Run 'pixiv-downloader login --force' to re-login"
            )

        console.print(table)
</code>
</task>
```

**Verification:**
```bash
# 测试 JSON 输出
pixiv-downloader --json-output status

# 预期输出: {"logged_in": true, "token_valid": true, "username": null, ...}
# 或错误场景: {"logged_in": false, "token_valid": false, "error": "...", ...}
```

### Task 2: 实现 config 命令的 JSON 输出

**What:** 为 config 命令添加 --json-output 支持

**Files:** `src/gallery_dl_auo/cli/config_cmd.py`

**Challenge:** 当前 config 命令实现较简单,需要扩展以支持 get/list 子命令

**Design Decision:**
- **方案 A**: 扩展 config 命令为命令组,支持 `config get` 和 `config list`
- **方案 B**: 保持当前 config 命令,输出所有配置(相当于 list)

**推荐方案 B** (保持简单):
- 当前命令已显示所有配置,JSON 输出直接返回整个配置对象
- 未来如需 get/set 子命令,可在 Phase 8.1 中实现
- 符合测试中的 _config_list_output_schema

**Implementation:**

```xml
<task>
<step>
1. 在输出配置前检查 ctx.obj["output_mode"]
2. 如果是 "json",输出 JSON 格式;否则输出 Rich 表格
3. 错误场景也需要输出 JSON 格式的错误信息
</step>
<code location="src/gallery_dl_auo/cli/config_cmd.py">
"""config 子命令

查看当前配置。
"""

import json

import click
import yaml
from rich.console import Console
from rich.table import Table


@click.command()
@click.pass_context
def config_cmd(ctx: click.Context) -> None:
    """查看当前配置

    显示从 config.yaml 加载的配置值。
    """
    console: Console = ctx.obj["console"]

    try:
        # 加载配置文件
        with open("config.yaml", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        # 根据输出模式选择输出格式
        if ctx.obj.get("output_mode") == "json":
            # JSON 输出模式
            output_data = {
                "config": config
            }
            click.echo(json.dumps(output_data, ensure_ascii=False))
        else:
            # Rich 表格输出模式
            table = Table(title="当前配置", show_header=True, header_style="bold blue")
            table.add_column("配置项", style="cyan")
            table.add_column("值", style="green")

            for key, value in config.items():
                table.add_row(key, str(value))

            console.print(table)

    except FileNotFoundError:
        if ctx.obj.get("output_mode") == "json":
            error_data = {
                "error": "FileNotFoundError",
                "message": "找不到 config.yaml 文件",
                "suggestion": "请确保 config.yaml 在当前目录下"
            }
            click.echo(json.dumps(error_data, ensure_ascii=False))
            ctx.exit(1)
        else:
            console.print("[bold red]错误:[/bold red] 找不到 config.yaml 文件")
            console.print("请确保 config.yaml 在当前目录下")
            raise click.Abort() from None
    except yaml.YAMLError as e:
        if ctx.obj.get("output_mode") == "json":
            error_data = {
                "error": "YAMLError",
                "message": "config.yaml 格式错误",
                "details": str(e)
            }
            click.echo(json.dumps(error_data, ensure_ascii=False))
            ctx.exit(1)
        else:
            console.print("[bold red]错误:[/bold red] config.yaml 格式错误")
            console.print(f"详细信息: {e}")
            raise click.Abort() from None
</code>
</task>
```

**Verification:**
```bash
# 创建测试配置文件
cat > config.yaml <<EOF
download_dir: ./downloads
max_concurrent: 5
EOF

# 测试 JSON 输出
pixiv-downloader --json-output config

# 预期输出: {"config": {"download_dir": "./downloads", "max_concurrent": 5}}
```

### Task 3: 移除测试中的 skip 标记并验证

**What:** 移除 status 和 config 相关测试的 @pytest.mark.skip,运行测试验证

**Files:** `tests/validation/test_json_schemas.py`

**Implementation:**

```xml
<task>
<step>
1. 定位所有跳过的 status 和 config 测试
2. 移除 @pytest.mark.skip 装饰器
3. 运行测试验证 JSON 输出工作正常
</step>
<code location="tests/validation/test_json_schemas.py">
# 移除以下测试的 @pytest.mark.skip:

# Line ~139: test_command_json_output_parsable[status]
def test_command_json_output_parsable(self, runner, command, expected_fields, monkeypatch):
    """验证每个命令的 JSON 输出可以被解析"""
    # ... (移除 @pytest.mark.skip)

# Line ~170: test_status_command_schema
def test_status_command_schema(self, runner, monkeypatch):
    """验证 status 命令输出的 JSON Schema"""
    # ... (移除 @pytest.mark.skip)

# Line ~185: test_config_get_command_schema
def test_config_get_command_schema(self, runner, monkeypatch):
    """验证 config get 命令输出的 JSON Schema"""
    # ... (移除 @pytest.mark.skip)

# Line ~200: test_config_list_command_schema
def test_config_list_command_schema(self, runner, monkeypatch):
    """验证 config list 命令输出的 JSON Schema"""
    # ... (移除 @pytest.mark.skip)
</code>
</task>
```

**Note:** 由于 config 命令当前实现为显示所有配置(相当于 list),`test_config_get_command_schema` 测试可能需要调整:
- 方案 A: 保留 skip,注释说明 "config get 子命令未实现"
- 方案 B: 修改测试使用 `config list` 场景
- 方案 C: 跳过该测试,等待 Phase 8.1 实现 config get/set

**推荐方案 A** (保持诚实):
```python
@pytest.mark.skip(reason="config get 子命令未实现,当前 config 命令等同于 list")
def test_config_get_command_schema(self, runner, monkeypatch):
    ...
```

**Verification:**
```bash
# 运行所有 JSON Schema 测试
pytest tests/validation/test_json_schemas.py -v

# 预期输出:
# - test_command_json_output_parsable[version] PASSED
# - test_command_json_output_parsable[status] PASSED (之前 skip)
# - test_command_json_output_parsable[config] PASSED (之前 skip)
# - test_version_command_schema PASSED
# - test_status_command_schema PASSED (之前 skip)
# - test_config_get_command_schema SKIPPED (保持 skip,子命令未实现)
# - test_config_list_command_schema PASSED (之前 skip)
# - test_download_success_schema PASSED
# - test_download_error_schema SKIPPED (合理跳过)
# - test_schema_completeness PASSED
#
# 结果: 8 passed, 2 skipped (合理)
```

### Task 4: 更新 INTEGRATION.md 文档

**What:** 更新 INTEGRATION.md 移除或更新第 158 行的限制说明

**Files:** `INTEGRATION.md`

**Implementation:**

```xml
<task>
<step>
1. 定位第 158 行的限制说明
2. 更新说明,反映所有命令已支持 JSON 输出
3. 保留 config get 子命令的限制说明(如适用)
</step>
<code location="INTEGRATION.md">
# Line ~158: 更新限制说明

## 已知限制

### 当前版本
- ✅ 所有核心命令 (version, download, status, config) 已支持 `--json-output` 参数
- ⚠️ config get/set 子命令尚未实现,当前 `config` 命令显示所有配置

### 推荐使用方式
- 第三方集成: 使用 `--json-output` 获取结构化输出
- 批量下载: 使用 `--quiet` 避免进度输出干扰
- 错误处理: 所有命令在 `--json-output` 模式下返回有效 JSON,包括错误信息
</code>
</task>
```

**Verification:**
```bash
# 检查文档一致性
grep -n "json-output" INTEGRATION.md

# 预期: 所有提及 json-output 的地方都说明命令支持此参数
```

## Must-Haves (Gap Closure Verification)

完成此 gap closure 后,以下条件必须为 TRUE:

| Must-Have | Verification Method | Success Criteria |
| --- | --- | --- |
| status 命令支持 --json-output | `pixiv-downloader --json-output status` | 输出有效 JSON,包含 logged_in, token_valid 字段 |
| config 命令支持 --json-output | `pixiv-downloader --json-output config` | 输出有效 JSON,包含 config 对象 |
| status 测试不再跳过 | `pytest tests/validation/test_json_schemas.py -v` | test_status_command_schema passed |
| config list 测试不再跳过 | `pytest tests/validation/test_json_schemas.py -v` | test_config_list_command_schema passed |
| JSON 输出符合 Schema | jsonschema 验证 | validate(instance=output, schema=schema) 成功 |
| INTEGRATION.md 文档一致 | 人工检查 | 无矛盾的限制说明 |
| VAL-01 需求满足 | 完整测试套件 | 8/9 或 9/9 passed (合理跳过) |

## Dependencies

**Depends on:**
- 10-01: JSON 输出格式验证 (已完成,发现功能缺口)
- 10-01-GAP01: 修复测试导入路径 (已完成,测试框架可用)

**Blocks:**
- Phase 10 完成验证
- VAL-01 需求完全满足

## Risks

### Risk 1: config get 子命令需求

**Impact:** test_config_get_command_schema 测试无法通过

**Mitigation:**
1. 保持该测试跳过,说明 "config get 子命令未实现"
2. 在 INTEGRATION.md 中明确说明当前 config 命令等同于 list
3. Phase 8.1 可实现 config get/set 子命令

**Probability:** HIGH - 当前测试设计预期 get 子命令

### Risk 2: status 命令 JSON 输出缺少 username

**Impact:** JSON Schema 验证可能失败(username: null 不符合预期?)

**Mitigation:**
1. JSON Schema 允许 username 为 null: `"type": ["string", "null"]`
2. 如果测试预期非 null username,需要调整测试或从 token 中提取用户名

**Probability:** LOW - Schema 已允许 null

### Risk 3: 错误场景 JSON 输出格式

**Impact:** 错误场景可能不符合 Schema

**Mitigation:**
1. 错误场景输出应包含 error 字段,而非仅 logged_in/token_valid
2. 可能需要调整 Schema 或输出格式以适应错误场景

**Probability:** MEDIUM - 需要测试验证

## Files Modified Summary

```
src/gallery_dl_auo/cli/status_cmd.py
├── 添加 @click.pass_context 装饰器
├── 添加 JSON 输出逻辑 (检查 ctx.obj["output_mode"])
├── 错误场景 JSON 输出
└── 保持 Rich 表格输出为默认

src/gallery_dl_auo/cli/config_cmd.py
├── 添加 json import
├── 添加 JSON 输出逻辑 (检查 ctx.obj["output_mode"])
├── 错误场景 JSON 输出
└── 保持 Rich 表格输出为默认

tests/validation/test_json_schemas.py
├── 移除 test_command_json_output_parsable[status] 的 skip
├── 移除 test_status_command_schema 的 skip
├── 移除 test_command_json_output_parsable[config] 的 skip
├── 保留 test_config_get_command_schema 的 skip (子命令未实现)
└── 移除 test_config_list_command_schema 的 skip

INTEGRATION.md
├── 更新第 158 行的限制说明
└── 添加 config get 子命令限制说明
```

## Verification Commands

```bash
# 1. 验证 status 命令 JSON 输出
pixiv-downloader --json-output status
# 预期: {"logged_in": true/false, "token_valid": true/false, ...}

# 2. 验证 config 命令 JSON 输出
pixiv-downloader --json-output config
# 预期: {"config": {...}}

# 3. 验证 JSON 可解析
pixiv-downloader --json-output status | python -m json.tool

# 4. 运行 JSON Schema 测试
pytest tests/validation/test_json_schemas.py -v
# 预期: 8 passed, 2 skipped

# 5. 运行完整验证套件
pytest tests/validation/ -v
# 预期: 30+ passed, 6 skipped

# 6. 验证所有命令 JSON 输出
for cmd in version status config; do
    echo "Testing $cmd..."
    pixiv-downloader --json-output $cmd | python -m json.tool || echo "FAILED: $cmd"
done
```

## Success Criteria

- [ ] status 命令在 --json-output 模式下输出有效 JSON
- [ ] config 命令在 --json-output 模式下输出有效 JSON
- [ ] test_status_command_schema 测试通过
- [ ] test_config_list_command_schema 测试通过
- [ ] test_command_json_output_parsable[status] 测试通过
- [ ] test_command_json_output_parsable[config] 测试通过
- [ ] JSON Schema 验证成功
- [ ] INTEGRATION.md 文档更新
- [ ] VAL-01 需求完全满足

## Execution Notes

**给执行者的提示:**
1. **参考 version 命令**: version.py 已实现 JSON 输出,是最佳参考模式
2. **保持向后兼容**: Rich 表格输出保持为默认,JSON 输出仅在 --json-output 时启用
3. **错误处理一致性**: 错误场景也需输出 JSON 格式(在 --json-output 模式下)
4. **测试调整**: test_config_get_command_schema 保持跳过,因为 get 子命令未实现
5. **文档同步**: 修改代码后立即更新 INTEGRATION.md,保持一致性
6. **增量验证**: 每完成一个命令的实现,立即运行相关测试验证

**预计时间:** ~15 分钟
- status 命令实现: 5 分钟
- config 命令实现: 3 分钟
- 测试调整和验证: 5 分钟
- 文档更新: 2 分钟

---

**Plan Type:** Gap Closure (Feature Implementation)
**Wave:** 3
**Estimated Duration:** ~15 minutes
**Executor Notes:** 实现 JSON 输出功能,参考 version 命令模式,保持向后兼容,注意 config get 子命令限制
