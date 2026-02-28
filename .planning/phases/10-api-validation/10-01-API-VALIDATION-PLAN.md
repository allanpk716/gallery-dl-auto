---
phase: '10'
plan: '01'
type: auto
wave: 1
depends_on: []
files_modified:
  - tests/validation/conftest.py
  - tests/validation/test_json_schemas.py
  - pyproject.toml
requirements:
  - VAL-01
must_haves:
  jsonschema_installed: jsonschema 依赖已安装
  test_framework_established: tests/validation/ 目录存在,包含 conftest.py 和 test_json_schemas.py
  json_schemas_defined: 所有关键命令的 JSON Schema 在 conftest.py 中定义
  automated_tests_runnable: pytest tests/validation/test_json_schemas.py 命令成功执行
  all_tests_pass: pytest tests/validation/ -v 显示所有测试通过
  val01_satisfied: 可以展示所有命令的 JSON 输出经过验证的证据
autonomous: true
---

# Plan 10-01: JSON 输出格式验证

**Goal**: 验证所有现有命令的 JSON 输出格式,确保符合 INTEGRATION.md 中定义的规范

**Context**:
- Phase 8.1 已实现 CLI API 增强 (--json-help, --quiet, --json-output)
- Phase 9 已完成 INTEGRATION.md 文档,定义了 JSON 输出规范
- 当前缺少系统化的 JSON 输出验证,无法保证输出格式的一致性
- 需要建立自动化测试框架,确保所有命令的 JSON 输出符合 Schema

**Requirements met**:
- VAL-01: 所有现有命令的 JSON 输出格式经过验证,符合 INTEGRATION.md 中定义的规范

---

## Tasks

<task id="1">
<name>安装 jsonschema 依赖并建立测试基础设施</name>
<goal>添加 jsonschema 库到开发依赖,创建 tests/validation/ 目录结构</goal>
<files>
- C:/WorkSpace/gallery-dl-auto/pyproject.toml (更新依赖)
- C:/WorkSpace/gallery-dl-auto/tests/validation/__init__.py (新建)
- C:/WorkSpace/gallery-dl-auto/tests/validation/conftest.py (新建)
</files>
<action>

1. 更新 pyproject.toml,添加 jsonschema 到 dev dependencies:
   ```toml
   [project.optional-dependencies]
   dev = [
       # ... 现有依赖 ...
       "jsonschema>=4.26.0",
   ]
   ```

2. 创建测试目录结构:
   ```
   tests/
   ├── validation/                    # Phase 10 新增
   │   ├── __init__.py
   │   ├── conftest.py               # JSON Schema fixtures
   │   └── test_json_schemas.py      # Schema 验证测试
   ```

3. 创建 tests/validation/__init__.py (空文件)

4. 创建 tests/validation/conftest.py,定义 JSON Schema fixtures:
   - download_result_schema: BatchDownloadResult 的 Schema
   - error_response_schema: StructuredError 的 Schema
   - version_output_schema: version 命令输出的 Schema
   - status_output_schema: status 命令输出的 Schema
   - config_output_schema: config 命令输出的 Schema
</action>
<verify>
```bash
# 安装依赖
pip install -e ".[dev]"

# 验证 jsonschema 可用
python -c "import jsonschema; print(jsonschema.__version__)"

# 验证目录结构
ls tests/validation/
```
</verify>
<done>测试基础设施已建立,jsonschema 可用</done>
</task>

<task id="2">
<name>定义所有命令的 JSON Schema</name>
<goal>基于 INTEGRATION.md 和现有代码,定义完整的 JSON Schema</goal>
<files>
- C:/WorkSpace/gallery-dl-auto/tests/validation/conftest.py (更新)
</files>
<action>

1. 在 conftest.py 中定义 download 命令的 JSON Schema:
   - 基于 src/gallery_dl_auo/models/download_result.py 的 BatchDownloadResult
   - 包含: success, total, downloaded, failed, skipped, success_list, failed_errors, output_dir
   - 定义嵌套的 StructuredError Schema (definitions)

2. 定义错误响应的 JSON Schema:
   - 基于 src/gallery_dl_auo/models/error_response.py 的 StructuredError
   - 包含: error_code, error_type, message, suggestion, severity, illust_id, original_error, timestamp

3. 定义其他命令的 JSON Schema:
   - version 命令: {version: string, python_version: string, platform: string}
   - status 命令: {logged_in: boolean, token_valid: boolean, username: string|null}
   - config 命令: 根据子命令定义不同 Schema (get/set/list)

4. 验证 Schema 本身的完整性:
   - 所有必需字段已定义
   - 类型定义正确 (string, integer, boolean, array, object)
   - 枚举值定义完整 (如 severity: ["warning", "error", "critical"])
</action>
<verify>
```python
# 验证 Schema 可用于验证
from jsonschema import Draft7Validator
from tests.validation.conftest import *

# 验证 download_result_schema 语法正确
Draft7Validator.check_schema(download_result_schema())

# 验证 error_response_schema 语法正确
Draft7Validator.check_schema(error_response_schema())
```
</verify>
<done>所有命令的 JSON Schema 已定义并通过语法检查</done>
</task>

<task id="3">
<name>实现 JSON 输出验证测试</name>
<goal>创建自动化测试验证所有命令的 JSON 输出</goal>
<files>
- C:/WorkSpace/gallery-dl-auto/tests/validation/test_json_schemas.py (新建)
- C:/WorkSpace/gallery-dl-auto/tests/validation/conftest.py (更新,添加 Mock fixtures)
</files>
<action>

1. 创建 tests/validation/test_json_schemas.py

2. 实现 TestDownloadCommandJSONSchema 测试类:
   - test_download_success_schema: 验证成功下载结果符合 Schema
   - test_download_error_schema: 验证错误响应符合 Schema (如无 token 场景)
   - test_schema_completeness: 验证 Schema 包含所有必需字段

3. 实现 TestAllCommandsJSONSchema 测试类:
   - 使用 @pytest.mark.parametrize 装饰器
   - 测试所有命令: version, status, config, doctor, refresh, login, logout
   - 验证每个命令的 JSON 输出可以被解析

4. 使用 Click.testing.CliRunner 进行测试:
   - runner.invoke(cli, ["--json-output", command])
   - 解析 JSON 输出: json.loads(result.output)
   - 使用 jsonschema.validate() 验证符合 Schema

5. 处理 Mock 数据:
   - 在 conftest.py 中定义共享 fixtures
   - Mock token 加载,避免依赖真实 token
   - Mock API 调用,避免真实网络请求
</action>
<verify>
```bash
# 运行所有 JSON Schema 验证测试
pytest tests/validation/test_json_schemas.py -v

# 验证测试覆盖率
pytest tests/validation/test_json_schemas.py --cov=gallery_dl_auo.cli --cov-report=term-missing
```
</verify>
<done>JSON 输出验证测试已实现,测试可运行</done>
</task>

<task id="4">
<name>验证所有命令的 JSON 输出格式</name>
<goal>运行测试并修复发现的问题,确保所有命令符合规范</goal>
<files>
- C:/WorkSpace/gallery-dl-auto/src/gallery_dl_auo/cli/*.py (修复问题)
- C:/WorkSpace/gallery-dl-auto/tests/validation/VALIDATION_RESULTS.md (新建)
</files>
<action>

1. 运行完整的 JSON Schema 验证测试:
   ```bash
   pytest tests/validation/ -v --tb=short
   ```

2. 分析测试失败原因:
   - JSON 解析失败: 输出包含非 JSON 内容 (日志、进度条)
   - Schema 验证失败: 缺少必需字段、类型错误、枚举值不匹配

3. 修复发现的问题:
   - 更新 CLI 命令实现,确保 --json-output 模式下仅输出 JSON
   - 更新 logging 配置,在 --json-output 模式下禁用控制台输出
   - 补充缺失的 JSON 字段
   - 修正字段类型或枚举值

4. 重新运行测试,确保所有测试通过:
   ```bash
   pytest tests/validation/test_json_schemas.py -v
   ```

5. 记录测试结果和发现的问题:
   - 创建 tests/validation/VALIDATION_RESULTS.md
   - 记录每个命令的验证状态
   - 记录发现的问题和修复措施
</action>
<verify>
```bash
# 所有测试通过
pytest tests/validation/ -v
# 应看到: X passed, Y warnings

# 手动验证命令输出
pixiv-downloader --json-output version | jq .
pixiv-downloader --json-output status | jq .
```
</verify>
<done>所有命令的 JSON 输出格式已验证,测试全部通过,VAL-01 需求满足</done>
</task>

## Must-haves (Goal-backward verification)

执行此计划后,以下条件必须为 TRUE:

1. ✅ **jsonschema 依赖已安装**: pip list | grep jsonschema 显示版本号
2. ✅ **测试框架已建立**: tests/validation/ 目录存在,包含 conftest.py 和 test_json_schemas.py
3. ✅ **JSON Schema 已定义**: 所有关键命令的 JSON Schema 在 conftest.py 中定义
4. ✅ **自动化测试可运行**: pytest tests/validation/test_json_schemas.py 命令成功执行
5. ✅ **所有测试通过**: pytest tests/validation/ -v 显示所有测试通过
6. ✅ **VAL-01 需求满足**: 可以展示所有命令的 JSON 输出经过验证的证据

**验证命令**:
```bash
# 验证所有 must-haves
pytest tests/validation/ -v && \
echo "✅ 所有 JSON 输出格式验证测试通过"
```

---

## Dependencies

**Depends on**: 无 (Wave 1)

**Blocks**:
- 10-02 (退出码验证): 需要本计划建立的测试框架
- 10-03 (集成测试): 需要本计划验证的 JSON Schema

---

## Risk mitigation

**风险 1: 现有命令的 JSON 输出格式与 INTEGRATION.md 不一致**
- 缓解措施: 优先验证高频命令 (download, version, status),低频命令可手动验证
- 回滚策略: 如果问题严重,更新 INTEGRATION.md 以匹配实际实现

**风险 2: Mock 数据不完整,测试依赖真实环境**
- 缓解措施: 在 conftest.py 中集中管理 Mock fixtures,确保测试隔离
- 回滚策略: 标记依赖真实环境的测试为 @pytest.mark.integration

**风险 3: Windows 编码问题导致 JSON 解析失败**
- 缓解措施: 在 CliRunner 中显式设置 encoding='utf-8'
- 回滚策略: 记录编码问题,在后续计划中解决

---

## Notes

- 本计划专注于 JSON Schema 验证,不涉及退出码验证 (10-02) 或 subprocess 集成测试 (10-03)
- 优先验证 --json-output 模式,--quiet 模式的验证可选
- 测试结果将记录在 tests/validation/VALIDATION_RESULTS.md,便于后续查阅
