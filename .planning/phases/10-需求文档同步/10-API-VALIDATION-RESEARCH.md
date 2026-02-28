# Phase 10: API 验证 - Research

**Researched:** 2026-02-26
**Domain:** CLI API Validation and Testing
**Confidence:** HIGH

## Summary

Phase 10 的核心目标是验证 gallery-dl-auto 的 CLI API 一致性和可靠性,确保第三方集成的稳定性。当前项目已完成 Phase 8.1(CLI API 增强)和 Phase 9(集成文档),具备了完整的 JSON 输出能力、结构化错误码系统和集成文档。然而,这些功能的实际实现尚未经过系统化验证,存在三个关键风险:1) JSON 输出格式可能与 INTEGRATION.md 中定义的规范不一致;2) 退出码可能与文档说明不完全一致,导致第三方工具无法准确判断执行状态;3) 第三方工具实际调用场景缺乏集成测试验证。

本阶段需要建立系统化的验证框架,包括 JSON Schema 定义、自动化测试套件和真实场景集成测试,确保所有 API 承诺得到兑现。

**Primary recommendation:** 采用 jsonschema 库定义 JSON Schema,使用 Click.testing.CliRunner 进行单元/集成测试,结合 subprocess 进行端到端集成测试,建立三层验证体系确保 API 稳定性。

## User Constraints (from CONTEXT.md)

*Note: No CONTEXT.md file exists for Phase 10. Research was performed without user-provided constraints.*

### Locked Decisions

None - this is a validation phase with no prior user decisions.

### Claude's Discretion

Full discretion to determine:
- Validation framework architecture (JSON Schema definition approach)
- Test organization and structure
- Integration test scenarios and coverage
- Error handling verification approach
- Documentation verification methodology

### Deferred Ideas (OUT OF SCOPE)

- API 版本控制验证 (v1.2 专注于验证现有 API)
- 性能测试和压力测试 (超出 API 验证范围)
- 跨平台兼容性测试 (Windows 为主,其他平台可选)

## Phase Requirements

This section maps Phase 10 success criteria to research findings.

| ID | Description | Research Support |
|----|-------------|------------------|
| VAL-01 | 所有现有命令的 JSON 输出格式经过验证,符合 INTEGRATION.md 中定义的规范 | 使用 jsonschema 库定义 JSON Schema,对每个命令的输出进行 Schema 验证,详见 "JSON Schema 验证" 章节 |
| VAL-02 | 所有退出码经过验证,与文档说明完全一致,第三方工具可依赖退出码判断执行状态 | 基于当前 error_codes.py 中定义的 22 个错误码,建立退出码映射表,使用 CliRunner 和 subprocess 进行验证 |
| VAL-03 | 第三方工具调用场景经过集成测试验证,真实场景下工作可靠 | 使用 subprocess 模拟第三方工具调用,结合 Click.testing.CliRunner 进行集成测试,详见 "集成测试策略" 章节 |

## Standard Stack

### Core

| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| jsonschema | 4.26.0+ | JSON Schema 验证 | Python 生态标准 JSON Schema 验证库,支持 Draft 2020-12/2019-09/7/6/4/3,提供详细的 ValidationError 信息 |
| pytest | 8.0.0+ | 测试框架 | 项目已使用,提供 fixture、parametrize、marker 等功能,支持 capsys/capfd 捕获输出 |
| Click.testing | 8.1.0+ | CLI 测试工具 | 项目使用 Click 框架,CliRunner 提供隔离的命令执行环境,返回 Result 对象包含 exit_code/output/exception |

### Supporting

| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| subprocess | stdlib | 真实进程调用 | 模拟第三方工具调用场景,验证端到端集成 |
| pydantic | 2.12.0+ | 数据模型验证 | 项目已用于 StructuredError 和 BatchDownloadResult,可用于 JSON 输出类型验证 |
| json | stdlib | JSON 解析 | 所有 JSON 输出解析和验证 |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| jsonschema | 手动 JSON 验证 | 手动验证容易遗漏边界情况,jsonschema 提供声明式 Schema 定义,可复用且易维护 |
| CliRunner | subprocess 专用测试 | CliRunner 提供更好的测试隔离和调试能力,但 subprocess 更接近真实调用场景,两者结合使用 |
| pytest | unittest | 项目已使用 pytest,unittest 会增加维护成本,pytest fixture 和 parametrize 更适合数据驱动测试 |

**Installation:**
```bash
# 已在 pyproject.toml 中配置
pip install jsonschema  # 需要添加到 dev dependencies
```

## Architecture Patterns

### Recommended Project Structure

```
tests/
├── validation/                    # Phase 10 新增验证测试目录
│   ├── __init__.py
│   ├── conftest.py               # 共享 fixtures (JSON Schemas, test data)
│   ├── test_json_schemas.py      # JSON Schema 定义和验证
│   ├── test_exit_codes.py        # 退出码验证
│   └── test_integration.py       # 第三方集成测试
├── cli/                          # 现有 CLI 测试
│   ├── test_json_output.py       # 已有:测试 --quiet/--json-output
│   └── test_integration.py       # 已有:测试 --json-help
└── conftest.py                   # 全局 fixtures
```

### Pattern 1: JSON Schema 定义和验证

**What:** 使用 jsonschema 库定义每个命令输出的 JSON Schema,在测试中验证实际输出符合 Schema

**When to use:** VAL-01 验证所有命令的 JSON 输出格式

**Example:**

```python
# tests/validation/conftest.py
import pytest
from pathlib import Path

@pytest.fixture
def download_result_schema():
    """BatchDownloadResult 的 JSON Schema"""
    return {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "properties": {
            "success": {"type": "boolean"},
            "total": {"type": "integer", "minimum": 0},
            "downloaded": {"type": "integer", "minimum": 0},
            "failed": {"type": "integer", "minimum": 0},
            "skipped": {"type": "integer", "minimum": 0},
            "success_list": {
                "type": "array",
                "items": {"type": "integer"}
            },
            "failed_errors": {
                "type": "array",
                "items": {"$ref": "#/definitions/StructuredError"}
            },
            "output_dir": {"type": "string"}
        },
        "required": ["success", "total", "downloaded", "failed", "skipped", "output_dir"],
        "definitions": {
            "StructuredError": {
                "type": "object",
                "properties": {
                    "error_code": {"type": "string"},
                    "error_type": {"type": "string"},
                    "message": {"type": "string"},
                    "suggestion": {"type": "string"},
                    "severity": {"type": "string", "enum": ["warning", "error", "critical"]},
                    "illust_id": {"type": ["integer", "null"]},
                    "original_error": {"type": ["string", "null"]},
                    "timestamp": {"type": "string", "format": "date-time"}
                },
                "required": ["error_code", "error_type", "message", "suggestion", "severity", "timestamp"]
            }
        }
    }

@pytest.fixture
def error_response_schema():
    """StructuredError 的 JSON Schema (认证错误等)"""
    return {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "properties": {
            "error_code": {"type": "string"},
            "error_type": {"type": "string"},
            "message": {"type": "string"},
            "suggestion": {"type": "string"},
            "severity": {"type": "string", "enum": ["warning", "error", "critical"]},
            "illust_id": {"type": ["integer", "null"]},
            "original_error": {"type": ["string", "null"]},
            "timestamp": {"type": "string", "format": "date-time"}
        },
        "required": ["error_code", "error_type", "message", "suggestion", "severity", "timestamp"]
    }
```

```python
# tests/validation/test_json_schemas.py
import json
import pytest
from jsonschema import validate, ValidationError, Draft7Validator
from gallery_dl_auo.cli.main import cli
from click.testing import CliRunner

class TestDownloadCommandJSONSchema:
    """验证 download 命令的 JSON 输出符合 Schema"""

    def test_download_success_schema(self, runner, download_result_schema):
        """验证成功下载结果的 JSON Schema"""
        # Mock 成功下载场景
        result = runner.invoke(cli, ["--json-output", "download", "--type", "daily"])

        # 解析 JSON 输出
        output = json.loads(result.output)

        # 验证符合 Schema
        try:
            validate(instance=output, schema=download_result_schema)
        except ValidationError as e:
            pytest.fail(f"JSON Schema 验证失败: {e.message}\n路径: {list(e.path)}")

    def test_download_error_schema(self, runner, error_response_schema):
        """验证错误响应的 JSON Schema (无 token 场景)"""
        # Mock 错误场景
        result = runner.invoke(cli, ["--json-output", "download", "--type", "daily"])

        # 期望认证错误
        assert result.exit_code != 0

        output = json.loads(result.output)

        # 验证符合错误 Schema
        try:
            validate(instance=output, schema=error_response_schema)
        except ValidationError as e:
            pytest.fail(f"错误响应 Schema 验证失败: {e.message}")

    def test_schema_completeness(self, download_result_schema):
        """验证 Schema 本身完整性"""
        # 检查必需字段
        required_fields = ["success", "total", "downloaded", "failed", "skipped", "output_dir"]
        assert set(download_result_schema["required"]) == set(required_fields)

        # 检查类型定义
        assert "definitions" in download_result_schema
        assert "StructuredError" in download_result_schema["definitions"]

class TestAllCommandsJSONSchema:
    """验证所有命令的 JSON 输出"""

    @pytest.mark.parametrize("command", [
        "version",
        "status",
        "config",
        "doctor"
    ])
    def test_command_json_output_valid(self, runner, command):
        """验证每个命令的 JSON 输出可以被解析"""
        result = runner.invoke(cli, ["--json-output", command])

        # 验证 JSON 可解析
        try:
            output = json.loads(result.output)
        except json.JSONDecodeError as e:
            pytest.fail(f"命令 {command} 的输出不是有效的 JSON: {e}\n输出: {result.output}")
```

### Pattern 2: 退出码验证

**What:** 建立 INTEGRATION.md 中定义的退出码映射表,在测试中验证每种错误场景返回正确的退出码

**When to use:** VAL-02 验证所有退出码与文档一致

**Example:**

```python
# tests/validation/test_exit_codes.py
import pytest
from gallery_dl_auo.cli.main import cli
from gallery_dl_auo.utils.error_codes import ErrorCode
from click.testing import CliRunner

# 退出码映射表 (基于 INTEGRATION.md 和 error_codes.py)
EXIT_CODE_MAPPING = {
    # 成功场景
    "SUCCESS": 0,

    # 认证错误 (stderr 包含错误码)
    "AUTH_TOKEN_NOT_FOUND": 1,
    "AUTH_TOKEN_EXPIRED": 1,
    "AUTH_TOKEN_INVALID": 1,
    "AUTH_REFRESH_FAILED": 1,

    # API 错误
    "API_NETWORK_ERROR": 1,
    "API_RATE_LIMIT": 1,
    "API_SERVER_ERROR": 1,
    "API_INVALID_RESPONSE": 1,

    # 下载错误
    "DOWNLOAD_FAILED": 1,
    "DOWNLOAD_TIMEOUT": 1,
    "DOWNLOAD_PERMISSION_DENIED": 1,

    # 参数错误
    "INVALID_ARGUMENT": 2,  # Click 参数错误
    "INVALID_DATE_FORMAT": 2,

    # 下载结果状态
    "PARTIAL_SUCCESS": 1,  # 部分下载成功
    "COMPLETE_FAILURE": 2,  # 完全失败
}

class TestAuthExitCodes:
    """验证认证相关退出码"""

    def test_no_token_exit_code(self, runner, mock_no_token):
        """无 token 时应返回退出码 1"""
        result = runner.invoke(cli, ["download", "--type", "daily"])

        assert result.exit_code == EXIT_CODE_MAPPING["AUTH_TOKEN_NOT_FOUND"]
        assert "AUTH_TOKEN_NOT_FOUND" in result.output

    def test_invalid_token_exit_code(self, runner, mock_invalid_token):
        """无效 token 时应返回退出码 1"""
        result = runner.invoke(cli, ["download", "--type", "daily"])

        assert result.exit_code == EXIT_CODE_MAPPING["AUTH_TOKEN_INVALID"]
        assert "AUTH_TOKEN_INVALID" in result.output

class TestDownloadExitCodes:
    """验证下载命令退出码"""

    def test_success_exit_code(self, runner, mock_successful_download):
        """完全成功时返回退出码 0"""
        result = runner.invoke(cli, ["download", "--type", "daily"])

        assert result.exit_code == EXIT_CODE_MAPPING["SUCCESS"]

    def test_partial_success_exit_code(self, runner, mock_partial_download):
        """部分成功时返回退出码 1"""
        result = runner.invoke(cli, ["download", "--type", "daily"])

        assert result.exit_code == EXIT_CODE_MAPPING["PARTIAL_SUCCESS"]

    def test_complete_failure_exit_code(self, runner, mock_failed_download):
        """完全失败时返回退出码 2"""
        result = runner.invoke(cli, ["download", "--type", "daily"])

        assert result.exit_code == EXIT_CODE_MAPPING["COMPLETE_FAILURE"]

class TestArgumentExitCodes:
    """验证参数错误退出码"""

    def test_invalid_ranking_type(self, runner):
        """无效排行榜类型应返回退出码 2"""
        result = runner.invoke(cli, ["download", "--type", "invalid_type"])

        assert result.exit_code == EXIT_CODE_MAPPING["INVALID_ARGUMENT"]

    def test_invalid_date_format(self, runner):
        """无效日期格式应返回退出码 2"""
        result = runner.invoke(cli, ["download", "--type", "daily", "--date", "invalid-date"])

        assert result.exit_code == EXIT_CODE_MAPPING["INVALID_DATE_FORMAT"]
```

### Pattern 3: 第三方集成测试

**What:** 使用 subprocess 模拟第三方工具调用,验证真实场景下的 CLI 行为

**When to use:** VAL-03 验证第三方工具调用场景

**Example:**

```python
# tests/validation/test_integration.py
import subprocess
import json
import pytest
from pathlib import Path

class TestThirdPartyIntegration:
    """模拟第三方工具调用场景"""

    def test_subprocess_download_success(self, tmp_path):
        """使用 subprocess 调用 download 命令 (成功场景)"""
        output_dir = tmp_path / "downloads"

        result = subprocess.run(
            ["pixiv-downloader", "--json-output", "download", "--type", "daily", "--output", str(output_dir)],
            capture_output=True,
            text=True,
            timeout=60
        )

        # 验证返回码
        assert result.returncode == 0

        # 验证 stdout 是有效 JSON
        try:
            output = json.loads(result.stdout)
        except json.JSONDecodeError:
            pytest.fail(f"stdout 不是有效的 JSON: {result.stdout}")

        # 验证 JSON 结构
        assert "success" in output
        assert "total" in output
        assert "downloaded" in output

    def test_subprocess_no_token_error(self):
        """使用 subprocess 验证认证错误处理"""
        # 确保 credentials 文件不存在
        result = subprocess.run(
            ["pixiv-downloader", "--json-output", "download", "--type", "daily"],
            capture_output=True,
            text=True,
            timeout=10
        )

        # 验证返回码
        assert result.returncode != 0

        # 验证 stderr 或 stdout 包含错误信息
        # Note: --json-output 模式下错误可能在 stdout 或 stderr
        output_text = result.stdout if result.stdout else result.stderr

        try:
            error = json.loads(output_text)
            assert "error_code" in error
            assert error["error_code"] == "AUTH_TOKEN_NOT_FOUND"
        except json.JSONDecodeError:
            pytest.fail(f"错误输出不是有效的 JSON: {output_text}")

    def test_subprocess_batch_download(self, tmp_path):
        """模拟第三方工具批量下载多个排行榜"""
        output_dir = tmp_path / "downloads"
        ranking_types = ["daily", "weekly"]

        results = []
        for ranking_type in ranking_types:
            result = subprocess.run(
                ["pixiv-downloader", "--quiet", "download", "--type", ranking_type, "--output", str(output_dir)],
                capture_output=True,
                text=True,
                timeout=60
            )
            results.append({
                "type": ranking_type,
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr
            })

        # 验证所有命令执行完成
        for result in results:
            assert result["returncode"] == 0, f"{result['type']} 下载失败"

    def test_subprocess_timeout_handling(self):
        """验证长时间运行命令的超时处理"""
        # 模拟第三方工具设置超时
        with pytest.raises(subprocess.TimeoutExpired):
            subprocess.run(
                ["pixiv-downloader", "download", "--type", "daily"],
                capture_output=True,
                timeout=1  # 1 秒超时 (预期会超时)
            )

class TestErrorRecovery:
    """验证错误恢复机制"""

    def test_interrupt_handling(self):
        """验证 Ctrl+C 中断处理"""
        # 使用 subprocess 启动长时间运行的命令
        process = subprocess.Popen(
            ["pixiv-downloader", "download", "--type", "daily"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True
        )

        # 发送 SIGINT (Ctrl+C)
        process.send_signal(subprocess.signal.SIGINT)

        stdout, stderr = process.communicate(timeout=5)

        # 验证退出码 130 (128 + SIGINT)
        assert process.returncode == 130

        # 验证输出包含中断信息
        assert "USER_INTERRUPT" in stdout or "中断" in stdout
```

### Anti-Patterns to Avoid

- **不要依赖手动测试**: JSON 格式和退出码验证必须自动化,手动测试不可靠且难以重复
- **不要忽略 stderr**: Click 在某些情况下会将错误输出到 stderr,验证时需要同时检查 stdout 和 stderr
- **不要硬编码 JSON 输出**: 使用 JSON Schema 验证结构,而非字符串比较,这样能适应非关键字段的变化
- **不要跳过边界情况**: 部分成功、完全失败、空结果等边界情况必须验证,这些是第三方集成最容易出错的场景

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| JSON 验证 | 手动遍历 JSON 字段 | jsonschema | jsonschema 提供声明式 Schema,自动检查类型、必需字段、枚举值等,支持详细的错误信息 |
| CLI 测试 | subprocess 模拟所有交互 | Click.testing.CliRunner | CliRunner 提供隔离环境,自动处理输入输出,提供 Result 对象包含 exit_code/exception/output |
| 输出捕获 | 手动重定向 stdout/stderr | pytest capsys/capfd | pytest fixture 自动捕获和清理,支持多次 readouterr() 调用 |
| 进程调用 | os.system/os.popen | subprocess.run | subprocess 提供更好的控制(timeout、capture_output、text mode)和错误处理 |

**Key insight:** JSON Schema 验证和 CLI 测试是成熟领域,标准库和社区提供了完善的工具链,自定义实现会增加维护成本且容易出错。

## Common Pitfalls

### Pitfall 1: JSON 输出包含非 JSON 内容

**What goes wrong:** 命令在 --json-output 模式下仍然输出日志或进度信息,导致 JSON 解析失败

**Why it happens:** 日志系统没有正确响应 --json-output 标志,或者某个模块直接 print() 而非通过统一输出接口

**How to avoid:**
1. 在测试中验证整个输出是有效的 JSON
2. 使用 json.loads() 尝试解析,失败时输出原始内容帮助调试
3. 在 logging 配置中检查 --json-output 标志,禁用控制台输出

**Warning signs:**
- JSON 解析失败,错误信息显示 "Expecting value: line 1 column 1 (char 0)"
- 输出中混入了日志时间戳或进度条
- stderr 包含预期外的内容

**Example fix:**
```python
# 错误示例:直接 print 日志
print(f"Downloading {illust_id}...")

# 正确示例:使用 logging,在 --json-output 时禁用
logger.info(f"Downloading {illust_id}...")  # logging 会检查 quiet/json 标志
```

### Pitfall 2: 退出码不一致

**What goes wrong:** 相同错误场景有时返回 1,有时返回 2,或者文档中记录为 1 但实际返回 2

**Why it happens:**
1. Click 框架的默认错误处理返回 1,而自定义错误处理返回不同值
2. 多层错误处理(Click + Pydantic + 自定义)导致退出码覆盖
3. 文档更新滞后于代码实现

**How to avoid:**
1. 建立退出码映射表(如上文 Pattern 2),在测试中强制验证
2. 使用 Click 的 @click.pass_context 和 ctx.exit(code) 统一退出
3. 文档和测试同步更新,将退出码映射表作为单一事实来源

**Warning signs:**
- 测试中 exit_code 断言失败
- 不同 Python 版本或 Click 版本下退出码不同
- 手动测试和自动化测试结果不一致

### Pitfall 3: 子进程输出编码问题

**What goes wrong:** subprocess 在 Windows 上返回的 stdout/stderr 包含乱码,导致 JSON 解析失败

**Why it happens:**
1. Windows 默认使用 GBK/CP936 编码,而非 UTF-8
2. Python subprocess 的 text=True 使用系统默认编码
3. JSON 输出包含中文,但编码不一致

**How to avoid:**
1. 在 subprocess.run() 中显式指定 encoding='utf-8'
2. 测试中使用 runner.invoke() 而非 subprocess,CliRunner 自动处理编码
3. 如果必须使用 subprocess,在 CLI 启动时设置 PYTHONIOENCODING=utf-8

**Warning signs:**
- JSON 解析失败,错误信息包含乱码
- 输出中中文显示为 `\uXXXX` 转义序列(这实际上正常)或乱码
- Windows 上测试失败,Linux/macOS 上正常

**Example fix:**
```python
# 错误示例:依赖系统默认编码
result = subprocess.run(["pixiv-downloader", "--json-output", "version"], capture_output=True, text=True)

# 正确示例:显式指定 UTF-8
result = subprocess.run(
    ["pixiv-downloader", "--json-output", "version"],
    capture_output=True,
    text=True,
    encoding='utf-8'  # Windows 必需
)
```

### Pitfall 4: 测试中的 Mock 不完整

**What goes wrong:** Mock 了 API 调用但忘记 Mock token 加载,导致测试依赖真实 token,在不同环境下测试结果不一致

**Why it happens:**
1. 测试数据准备不充分,部分依赖真实环境
2. Mock 粒度不正确(过度 Mock 或 Mock 不足)
3. 缺少测试隔离,测试之间共享状态

**How to avoid:**
1. 在 conftest.py 中定义共享 fixtures,统一管理 Mock
2. 使用 pytest-mock 或 unittest.mock 确保所有外部依赖被 Mock
3. 使用 tmp_path fixture 隔离文件系统操作
4. 每个测试前清理环境(如删除 credentials 文件)

**Warning signs:**
- 本地测试通过,CI/CD 失败
- 测试顺序影响结果(先运行 A 再运行 B 失败,单独运行 B 成功)
- 测试依赖 ~/.gallery-dl-auto/ 目录下的真实数据

## Code Examples

Verified patterns from official sources:

### JSON Schema 验证 (jsonschema 官方文档)

```python
# Source: https://python-jsonschema.readthedocs.io/
from jsonschema import validate, ValidationError, Draft7Validator

# 定义 Schema
schema = {
    "type": "object",
    "properties": {
        "success": {"type": "boolean"},
        "total": {"type": "integer", "minimum": 0},
        "errors": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "error_code": {"type": "string"},
                    "message": {"type": "string"}
                },
                "required": ["error_code", "message"]
            }
        }
    },
    "required": ["success", "total"]
}

# 简单验证
try:
    validate(instance={"success": True, "total": 10}, schema=schema)
except ValidationError as e:
    print(f"Validation failed: {e.message}")

# 详细错误收集
validator = Draft7Validator(schema)
errors = list(validator.iter_errors({"success": True, "total": -5}))
for error in errors:
    print(f"Error at {list(error.path)}: {error.message}")
```

### Click CLI 测试 (Click 官方文档)

```python
# Source: https://click.palletsprojects.com/en/stable/testing/
from click.testing import CliRunner
from gallery_dl_auo.cli.main import cli

def test_download_command():
    runner = CliRunner()

    # 测试成功场景
    result = runner.invoke(cli, ["download", "--type", "daily"])
    assert result.exit_code == 0
    assert "success" in result.output

    # 测试错误场景
    result = runner.invoke(cli, ["download", "--type", "invalid"])
    assert result.exit_code != 0

    # 访问异常信息
    if result.exception:
        print(f"Exception: {result.exception}")

    # 测试环境变量
    result = runner.invoke(cli, ["config"], env={"APP_CONFIG": "/path/to/config"})

    # 测试文件系统隔离
    with runner.isolated_filesystem():
        with open("test.txt", "w") as f:
            f.write("test content")
        result = runner.invoke(cli, ["process", "test.txt"])
```

### Subprocess 集成测试 (Python 官方文档)

```python
# Source: https://docs.python.org/3/library/subprocess.html
import subprocess
import json

def test_cli_integration():
    # 基本调用
    result = subprocess.run(
        ["pixiv-downloader", "--json-output", "version"],
        capture_output=True,
        text=True,
        encoding='utf-8',  # Windows 必需
        timeout=10
    )

    # 验证返回码
    assert result.returncode == 0

    # 验证 JSON 输出
    output = json.loads(result.stdout)
    assert "version" in output

    # 错误处理
    result = subprocess.run(
        ["pixiv-downloader", "download", "--type", "daily"],
        capture_output=True,
        text=True,
        timeout=60
    )

    if result.returncode != 0:
        error = json.loads(result.stdout if result.stdout else result.stderr)
        print(f"Error: {error['error_code']}: {error['message']}")

    # 超时处理
    try:
        subprocess.run(
            ["pixiv-downloader", "download", "--type", "daily"],
            capture_output=True,
            timeout=1
        )
    except subprocess.TimeoutExpired:
        print("Command timed out")
```

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| 手动 JSON 验证 | JSON Schema 验证 | 2020+ | 声明式 Schema,自动类型检查,详细错误信息,可复用 |
| os.system | subprocess.run | Python 3.5+ | 更好的控制(timeout, capture_output),更安全的参数传递 |
| unittest | pytest | 项目初始 | fixture 系统,parametrize,更好的断言错误信息 |
| 手动测试 | 自动化测试 | 本项目 | 可重复性,CI/CD 集成,回归测试 |

**Deprecated/outdated:**
- os.system/os.popen: 使用 subprocess.run 替代,提供更好的控制和安全性
- 手动字符串验证: 使用 JSON Schema 验证,声明式且易维护
- 硬编码测试数据: 使用 pytest fixtures 和 parametrize,数据驱动测试

## Open Questions

1. **JSON Schema 存储位置**
   - What we know: Schema 可以定义在测试代码中,或单独的 .json 文件中
   - What's unclear: 是否需要将 Schema 文件放在 docs/ 目录供第三方开发者参考
   - Recommendation: 初始阶段将 Schema 定义在 tests/validation/conftest.py,如果第三方开发者反馈需要,再提取到独立文件并添加到文档

2. **错误码验证覆盖率**
   - What we know: error_codes.py 定义了 22 个错误码,但并非所有错误场景都能在测试中轻松模拟
   - What's unclear: 是否需要 Mock 所有 22 个错误场景,还是专注于最常见的 5-10 个
   - Recommendation: 优先验证高频错误(AUTH_TOKEN_NOT_FOUND, DOWNLOAD_FAILED 等),低频错误(如 FILE_DISK_FULL)可以手动验证或依赖集成测试

3. **集成测试环境隔离**
   - What we know: 测试需要隔离,避免依赖真实 token 和文件系统
   - What's unclear: 是否需要 Docker 容器提供完全隔离的测试环境
   - Recommendation: Phase 10 使用 tmp_path 和 Mock 提供基本隔离,如果后续需要跨平台测试或复杂集成测试,再引入 Docker

## Sources

### Primary (HIGH confidence)
- jsonschema 官方文档 - https://python-jsonschema.readthedocs.io/ - JSON Schema 验证库使用方法和最佳实践
- Click 测试文档 - https://click.palletsprojects.com/en/stable/testing/ - CliRunner 使用方法和 Result 对象
- pytest 文档 - https://docs.pytest.org/ - fixture, parametrize, capsys/capfd 使用方法
- Python subprocess 文档 - https://docs.python.org/3/library/subprocess.html - subprocess.run 参数和错误处理

### Secondary (MEDIUM confidence)
- Stack Overflow: JSON Schema validation best practices - https://stackoverflow.com/questions/78190479/ - 实际使用中的问题和解决方案
- pytest-subprocess 文档 - https://pytest-subprocess.readthedocs.io/ - subprocess Mock 和测试模式

### Tertiary (LOW confidence)
- python-cli-test-helpers - https://github.com/painless-software/python-cli-test-helpers - CLI 测试辅助工具(未在项目中使用,仅作参考)

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - jsonschema 和 Click.testing 是 Python 生态标准工具,文档完善
- Architecture: HIGH - 三层验证体系(单元测试、集成测试、端到端测试)是业界标准模式
- Pitfalls: MEDIUM - 基于实际项目经验和常见问题,但需要实际测试验证是否完整

**Research date:** 2026-02-26
**Valid until:** 2027-02-26 (1 年 - JSON Schema 和 Click 测试 API 相对稳定)
