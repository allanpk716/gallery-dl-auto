# Phase 10 执行快速参考

**Phase:** 10 - API 验证
**Mode:** Gap Closure
**Last Updated:** 2026-02-27T11:00:00Z

---

## 当前状态

- ✅ **原始计划完成**: 10-01, 10-02A, 10-02B, 10-03A, 10-03B
- ✅ **Wave 2 完成**: 10-01-GAP01 (修复测试框架导入路径)
- 🚧 **Wave 3 待执行**: 10-01-GAP02 (实现 status/config JSON 输出)
- 📊 **Phase 进度**: 83% (2.5/3 requirements)

---

## Gap Closure 执行清单

### Wave 3: 10-01-GAP02 (待执行)

**计划文件:** `.planning/phases/10-api-validation/10-01-GAP02-PLAN.md`

**执行命令:**
```bash
/gsd:execute-phase --gap-closure --plan 10-01-GAP02
```

**预计时间:** ~15 分钟

**核心任务:**
1. ✏️ 修改 `status_cmd.py` - 添加 JSON 输出支持
2. ✏️ 修改 `config_cmd.py` - 添加 JSON 输出支持
3. ✏️ 修改 `test_json_schemas.py` - 移除 skip 标记
4. ✏️ 修改 `INTEGRATION.md` - 更新限制说明

**关键参考:**
- 参考文件: `src/gallery_dl_auo/cli/version.py` (已实现 JSON 输出)
- Schema 定义: `tests/validation/conftest.py`
- 验证报告: `.planning/phases/10-api-validation/10-API-VALIDATION-VERIFICATION.md`

---

## 原始计划执行顺序 (已完成)

```bash
# Wave 1: JSON 输出格式验证 (约 20 分钟)
/gsd:execute-phase --plan 10-01

# Wave 2: 退出码验证 (约 10 分钟)
/gsd:execute-phase --plan 10-02A
/gsd:execute-phase --plan 10-02B

# Wave 3: 集成测试 (约 15 分钟)
/gsd:execute-phase --plan 10-03A
/gsd:execute-phase --plan 10-03B
```

---

## 验证命令

### Gap Closure 验证 (Wave 3)

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
# 预期: 8 passed, 2 skipped (或 9 passed, 1 skipped)
```

### 完整验证

```bash
# 验证所有测试通过
pytest tests/validation/ -v

# 分别验证各部分
pytest tests/validation/test_json_schemas.py -v      # VAL-01
pytest tests/validation/test_exit_codes.py -v        # VAL-02
pytest tests/validation/test_integration.py -v       # VAL-03

# 检查测试覆盖率
pytest tests/validation/ --cov=gallery_dl_auo.cli --cov-report=term-missing
```

---

## 实现模式参考

### status 命令 JSON 输出模式

```python
# 在 status_cmd.py 中添加:
import json

@click.command()
@click.option("--verbose", "-v", is_flag=True, help="...")
@click.pass_context  # 添加这个装饰器
def status(ctx: click.Context, verbose: bool) -> None:
    # ... 现有代码 ...

    # 在显示结果前检查输出模式
    if ctx.obj.get("output_mode") == "json":
        # JSON 输出
        status_data = {
            "logged_in": result["valid"],
            "token_valid": result["valid"],
            "username": None
        }
        click.echo(json.dumps(status_data, ensure_ascii=False))
    else:
        # Rich 表格输出 (保持原样)
        table = Table(title="Token Status")
        # ... 现有表格代码 ...
```

### config 命令 JSON 输出模式

```python
# 在 config_cmd.py 中添加:
import json

@click.command()
@click.pass_context
def config_cmd(ctx: click.Context) -> None:
    # ... 现有代码 ...

    # 在显示结果前检查输出模式
    if ctx.obj.get("output_mode") == "json":
        # JSON 输出
        output_data = {"config": config}
        click.echo(json.dumps(output_data, ensure_ascii=False))
    else:
        # Rich 表格输出 (保持原样)
        table = Table(title="当前配置", ...)
        # ... 现有表格代码 ...
```

### 错误场景处理

```python
# 错误场景也需要 JSON 输出
if ctx.obj.get("output_mode") == "json":
    error_data = {
        "logged_in": False,
        "token_valid": False,
        "error": "错误信息",
        "suggestion": "建议操作"
    }
    click.echo(json.dumps(error_data, ensure_ascii=False))
else:
    console.print("[red]错误信息[/red]")
```

---

## 关键验收标准

### VAL-01: JSON 输出格式验证
- ✅ jsonschema 依赖已安装
- ✅ tests/validation/ 目录结构完整
- ✅ 所有命令的 JSON Schema 已定义
- 🚧 所有 JSON 输出验证测试通过 (Wave 3 目标: 8/9 或 9/9)

### VAL-02: 退出码验证
- ✅ EXIT_CODE_MAPPING 已建立
- ✅ 认证退出码验证通过 (4/4)
- ✅ 下载退出码验证通过 (3/3)
- ✅ 参数错误退出码验证通过 (3/3)

### VAL-03: 集成测试
- ✅ 基本 subprocess 集成测试通过
- ✅ 下载命令集成测试通过
- ✅ 批量下载测试通过
- ✅ 错误恢复机制测试通过

---

## 常见问题处理

### 问题 1: test_config_get_command_schema 应该移除 skip 吗?

**答:** ❌ 不移除。保持跳过,因为 config get 子命令未实现。

**原因:**
- 当前 config 命令仅支持 list 所有配置
- test_config_get_command_schema 预期 config get <key> 子命令
- 实现 get/set 子命令超出 gap closure 范围

### 问题 2: status JSON 输出需要包含 username 吗?

**答:** 不强制。Schema 允许 username 为 null。

**原因:**
- 当前实现不返回 username
- Schema 定义: `"type": ["string", "null"]`
- 未来可从 token 中提取用户名

### 问题 3: Windows 编码问题

**解决方案:**
```python
# 在 subprocess.run 中显式指定编码
result = subprocess.run(
    ["pixiv-downloader", "--json-output", "version"],
    capture_output=True,
    text=True,
    encoding='utf-8'  # Windows 必需
)
```

### 问题 4: 测试依赖真实 token

**解决方案:**
```python
# 在 conftest.py 中添加 Mock fixture
@pytest.fixture
def mock_no_token(monkeypatch):
    def mock_load_token():
        raise TokenNotFoundError("No token found")
    monkeypatch.setattr("gallery_dl_auo.auth.token.load_token", mock_load_token)
```

---

## 验证检查清单

### Wave 3 完成检查

#### 代码修改
- [ ] status_cmd.py 添加了 @click.pass_context
- [ ] status_cmd.py 检查 ctx.obj["output_mode"]
- [ ] status_cmd.py 在 JSON 模式下输出有效 JSON
- [ ] config_cmd.py 检查 ctx.obj["output_mode"]
- [ ] config_cmd.py 在 JSON 模式下输出有效 JSON
- [ ] 测试中的 status 相关 skip 已移除
- [ ] 测试中的 config list 相关 skip 已移除
- [ ] test_config_get_command_schema 保持 skip

#### 手动验证
- [ ] `pixiv-downloader --json-output status` 输出有效 JSON
- [ ] `pixiv-downloader --json-output config` 输出有效 JSON
- [ ] `pixiv-downloader status` 仍然输出 Rich 表格(默认模式)
- [ ] `pixiv-downloader config` 仍然输出 Rich 表格(默认模式)

#### 测试验证
- [ ] `pytest tests/validation/test_json_schemas.py -v` 通过
- [ ] 至少 8/9 测试通过
- [ ] 最多 2/9 测试跳过(config get, download error)

#### 文档验证
- [ ] INTEGRATION.md 第 158 行已更新
- [ ] 无矛盾的说明
- [ ] 所有命令的 JSON 输出支持已记录

### Phase 10 整体检查

- [x] 10-01 计划执行完成
- [x] 10-02A 计划执行完成
- [x] 10-02B 计划执行完成
- [x] 10-03A 计划执行完成
- [x] 10-03B 计划执行完成
- [x] 10-01-GAP01 执行完成
- [ ] 10-01-GAP02 执行完成
- [ ] 所有验证测试通过
- [ ] VAL-01 需求完全满足
- [ ] VALIDATION_RESULTS.md 已更新
- [ ] STATE.md 已更新
- [ ] ROADMAP.md 已更新

---

## 下一步行动

### 立即行动

```bash
# 1. 执行 gap closure 计划
/gsd:execute-phase --gap-closure --plan 10-01-GAP02

# 2. 验证执行结果
pytest tests/validation/test_json_schemas.py -v

# 3. 手动测试
pixiv-downloader --json-output status | python -m json.tool
pixiv-downloader --json-output config | python -m json.tool

# 4. 运行完整测试套件
pytest tests/validation/ -v
```

### 更新文档

```bash
# 1. 更新验证报告
# 编辑 .planning/phases/10-api-validation/10-API-VALIDATION-VERIFICATION.md

# 2. 更新状态文件
# 编辑 .planning/STATE.md

# 3. 更新路线图
# 编辑 .planning/ROADMAP.md
```

### 完成 Phase 10

```bash
# 1. 确认所有需求满足
# - VAL-01: ✅ VERIFIED (9/9 或 8/9 passed)
# - VAL-02: ✅ VERIFIED (10/10 passed)
# - VAL-03: ✅ VERIFIED (25+/31 passed)

# 2. 更新 STATE.md
# - status: completed
# - progress: 100% (3/3 requirements)

# 3. 准备发布 v1.2
```

---

## 紧急联系

**遇到问题?**

1. **查看详细计划:** `.planning/phases/10-api-validation/10-01-GAP02-PLAN.md`
2. **查看验证报告:** `.planning/phases/10-api-validation/10-API-VALIDATION-VERIFICATION.md`
3. **查看研究文档:** `.planning/phases/10-api-validation/10-API-VALIDATION-RESEARCH.md`
4. **查看 Gap Closure 总结:** `.planning/phases/10-api-validation/GAP-CLOSURE-SUMMARY.md`
5. **查看之前成功的实现:** `src/gallery_dl_auo/cli/version.py`

**常见错误:**

- ❌ `ModuleNotFoundError`: 检查导入路径 (应该在 GAP01 已修复)
- ❌ `KeyError: 'output_mode'`: 检查 ctx.obj 是否初始化 (main.py 应该已处理)
- ❌ JSON 解析失败: 检查输出是否包含非 JSON 内容(日志、进度等)

---

**Quick Reference created:** 2026-02-26
**Last updated:** 2026-02-27T11:00:00Z for Gap Closure Wave 3
**Status:** Wave 2 完成, Wave 3 待执行
