# Gallery-dl-auto 测试文档

本文档介绍 gallery-dl-auto 项目的测试套件，包括测试结构、运行方法、覆盖率报告、编写指南和测试分类。

## 目录

- [测试结构](#测试结构)
- [运行测试](#运行测试)
- [覆盖率报告](#覆盖率报告)
- [编写新测试](#编写新测试)
- [测试分类](#测试分类)
- [最佳实践](#最佳实践)

---

## 测试结构

```
tests/
├── conftest.py              # pytest 共享 fixtures
├── fixtures/                # 测试数据和 Mock 数据
│   ├── __init__.py
│   ├── mock_pixiv_responses.py  # Mock API 响应数据
│   ├── test_data.py            # 测试数据常量
│   └── test_fixtures.py        # 测试专用 fixtures
├── utils/                   # 测试辅助工具
│   ├── test_helpers.py      # 测试辅助函数
│   └── ...
├── cli/                     # CLI 命令测试
│   ├── test_main_commands.py    # 主命令和全局选项
│   ├── test_login_cmd.py        # 登录命令
│   ├── test_logout_cmd.py       # 登出命令
│   ├── test_status_cmd.py       # 状态查询命令
│   ├── test_refresh_cmd.py      # Token 刷新命令
│   ├── test_download_cmd.py     # 下载命令
│   ├── test_version_cmd.py      # 版本命令
│   ├── test_doctor_cmd.py       # 诊断命令
│   └── test_validators.py       # 参数验证器
├── api/                     # API 客户端测试
├── download/                # 下载器测试
├── models/                  # 数据模型测试
├── config/                  # 配置管理测试
├── core/                    # 核心功能测试
├── integration/             # 集成测试
└── validation/              # 验证测试
```

### 测试文件命名规范

- 单元测试: `test_<module_name>.py`
- 集成测试: `test_<feature>_integration.py`
- Fixture 文件: `<category>_fixtures.py` 或 `test_data.py`

---

## 运行测试

### 运行所有测试

```bash
# 运行所有测试
pytest

# 详细输出
pytest -v

# 显示测试函数名
pytest -v --tb=short
```

### 运行特定测试

```bash
# 运行特定文件
pytest tests/cli/test_download_cmd.py

# 运行特定测试类
pytest tests/cli/test_download_cmd.py::TestDownloadCommand

# 运行特定测试函数
pytest tests/cli/test_download_cmd.py::TestDownloadCommand::test_download_success

# 使用关键字过滤
pytest -k "download"  # 运行所有包含 "download" 的测试
```

### 运行特定标记的测试

```bash
# 运行慢速测试
pytest -m slow

# 跳过慢速测试
pytest -m "not slow"

# 运行集成测试
pytest -m integration
```

### 并行运行测试

```bash
# 使用 pytest-xdist 并行运行
pytest -n auto  # 自动检测CPU核心数

# 指定进程数
pytest -n 4
```

### 常用选项

```bash
# 失败时停止
pytest -x

# 失败N次后停止
pytest --maxfail=3

# 显示局部变量
pytest -l

# 进入调试模式（失败时）
pytest --pdb

# 只运行上次失败的测试
pytest --lf

# 先运行上次失败的测试
pytest --ff
```

---

## 覆盖率报告

### 生成覆盖率报告

```bash
# 终端输出覆盖率
pytest --cov=src/gallery_dl_auto

# 详细输出每个文件的覆盖率
pytest --cov=src/gallery_dl_auto --cov-report=term-missing

# 生成 HTML 报告
pytest --cov=src/gallery_dl_auto --cov-report=html

# 同时生成多种报告
pytest --cov=src/gallery_dl_auto --cov-report=html --cov-report=term --cov-report=xml
```

### 查看覆盖率报告

生成 HTML 报告后，打开 `htmlcov/index.html`：

```bash
# Windows
start htmlcov/index.html

# Linux
xdg-open htmlcov/index.html

# macOS
open htmlcov/index.html
```

### 覆盖率目标

- **总体覆盖率**: >= 80%
- **CLI 命令覆盖率**: >= 90%
- **核心业务逻辑**: >= 85%

### 覆盖率配置

项目使用 `pyproject.toml` 配置覆盖率：

```toml
[tool.coverage.run]
source = ["src/gallery_dl_auto"]
omit = [
    "*/tests/*",
    "*/__pycache__/*",
]

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise NotImplementedError",
    "if __name__ == .__main__.:",
]
```

---

## 编写新测试

### 基本测试模板

```python
"""Module description"""

import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch


class TestFeature:
    """测试类描述"""

    def test_success_case(self, runner, temp_dir):
        """测试成功场景"""
        # Arrange - 准备测试数据
        expected = "result"

        # Act - 执行被测试的代码
        result = some_function()

        # Assert - 验证结果
        assert result == expected

    def test_error_case(self):
        """测试错误场景"""
        with pytest.raises(ValueError) as exc_info:
            some_function(invalid_input)

        assert "expected error message" in str(exc_info.value)
```

### CLI 命令测试模板

```python
"""CLI command tests"""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch
from click.testing import CliRunner

from gallery_dl_auto.cli.command import command


class TestCommand:
    """Command tests"""

    def test_command_success(self, runner: CliRunner, tmp_path: Path):
        """Test successful command execution"""
        # Mock dependencies
        with patch("gallery_dl_auto.cli.command.dependency") as mock_dep:
            mock_dep.return_value = expected_result

            # Run command
            result = runner.invoke(command, ["--option", "value"])

            # Verify
            assert result.exit_code == 0
            output = json.loads(result.output)
            assert output["success"] is True

    def test_command_no_token(self, runner: CliRunner):
        """Test error when no token found"""
        result = runner.invoke(command, [])

        assert result.exit_code == 1
        output = json.loads(result.output)
        assert output["success"] is False
        assert "No token" in output["error"]["message"]
```

### 使用 Fixtures

```python
# 在 conftest.py 中定义 fixture
@pytest.fixture
def mock_client():
    """Mock PixivClient"""
    client = MagicMock()
    client.get_ranking.return_value = {"contents": [...]}
    return client


# 在测试中使用 fixture
def test_with_mock(mock_client):
    """Test using mock client"""
    result = some_function(mock_client)
    assert result is not None
```

### 参数化测试

```python
@pytest.mark.parametrize("input,expected", [
    ("daily", "day"),
    ("weekly", "week"),
    ("monthly", "month"),
])
def test_type_mapping(input, expected):
    """Test type parameter mapping"""
    result = validate_type(input)
    assert result == expected


@pytest.mark.parametrize("invalid_type", [
    "invalid",
    "unknown",
    "test",
])
def test_invalid_types(invalid_type):
    """Test invalid type raises error"""
    with pytest.raises(click.BadParameter):
        validate_type(invalid_type)
```

### Mock 和 Patch

```python
# Mock 类
with patch("module.ClassName") as mock_class:
    mock_instance = MagicMock()
    mock_class.return_value = mock_instance
    mock_instance.method.return_value = expected_value

    # 测试代码
    result = function_under_test()

# Mock 函数
with patch("module.function_name") as mock_func:
    mock_func.return_value = expected_value
    result = function_under_test()

# Mock 上下文管理器
with patch("module.ContextManager") as mock_cm:
    mock_cm.return_value.__enter__.return_value = mock_object
    result = function_under_test()
```

---

## 测试分类

### 1. 功能测试 (Functional Tests)

验证功能是否按预期工作。

```python
def test_download_success():
    """Test successful download"""
    result = download_ranking(mode="daily", date="2026-02-25")
    assert result.success is True
    assert result.downloaded > 0
```

### 2. 边界测试 (Boundary Tests)

测试参数边界值和极限情况。

```python
@pytest.mark.parametrize("limit", [0, 1, 50, 100, -1])
def test_download_limit(limit):
    """Test download with different limit values"""
    result = download_ranking(limit=limit)
    if limit <= 0:
        assert result.total == 0
    else:
        assert result.total <= limit
```

### 3. 错误处理测试 (Error Handling Tests)

验证异常场景和错误消息。

```python
def test_download_no_token():
    """Test error when no token available"""
    with patch("module.get_token", return_value=None):
        with pytest.raises(AuthenticationError) as exc:
            download_ranking()

        assert "No token found" in str(exc.value)
```

### 4. 输出格式测试 (Output Format Tests)

验证 JSON 和其他输出格式的正确性。

```python
def test_json_output_format():
    """Test JSON output format"""
    result = runner.invoke(command, ["--json-output"])

    assert result.exit_code == 0

    # 验证 JSON 格式有效
    output = json.loads(result.output)
    assert "success" in output
    assert "data" in output

    # 验证中文字符不被转义
    assert "美丽的风景" in result.output
```

### 5. 集成测试 (Integration Tests)

测试多个组件协同工作。

```python
@pytest.mark.integration
def test_full_download_workflow():
    """Test complete download workflow"""
    # 1. 登录
    # 2. 获取排行榜
    # 3. 下载图片
    # 4. 验证结果
    pass
```

---

## 最佳实践

### 1. 测试命名

```python
# 好的命名：清晰描述测试场景
def test_download_with_valid_token_succeeds():
    pass

def test_download_with_expired_token_fails():
    pass

# 不好的命名：过于模糊
def test_download():
    pass

def test_error():
    pass
```

### 2. 测试结构 (AAA 模式)

```python
def test_feature():
    # Arrange - 准备
    input_data = "test"
    expected = "TEST"

    # Act - 执行
    result = transform(input_data)

    # Assert - 断言
    assert result == expected
```

### 3. 一个测试一个断言原则

```python
# 好的：每个测试验证一个行为
def test_download_creates_directory():
    result = download()
    assert result.output_dir.exists()

def test_download_saves_files():
    result = download()
    assert len(result.success_list) > 0

# 不好的：一个测试验证多个行为
def test_download():
    result = download()
    assert result.output_dir.exists()
    assert len(result.success_list) > 0
    assert result.failed == 0
    # ... 更多断言
```

### 4. 使用 Fixture 隔离测试

```python
# 使用 fixture 创建隔离的测试环境
@pytest.fixture
def isolated_env(tmp_path):
    config_file = tmp_path / "config.yaml"
    config_file.write_text("key: value")
    return tmp_path

def test_with_isolation(isolated_env):
    # 测试在隔离环境中运行
    pass
```

### 5. Mock 外部依赖

```python
# Mock HTTP 请求
with patch("requests.get") as mock_get:
    mock_get.return_value.json.return_value = {"data": "test"}
    result = fetch_data()

# Mock 文件系统
with patch("builtins.open", mock_open(read_data="data")):
    result = read_file("test.txt")
```

### 6. 测试错误消息

```python
def test_error_message():
    """Test that error messages are helpful"""
    with pytest.raises(ValueError) as exc:
        validate_input("invalid")

    # 验证错误消息包含有用信息
    assert "invalid input" in str(exc.value)
    assert "expected format" in str(exc.value)
```

### 7. 避免测试实现细节

```python
# 好的：测试行为
def test_download_returns_result():
    result = download()
    assert isinstance(result, BatchDownloadResult)
    assert result.success is True

# 不好的：测试实现细节
def test_download_calls_internal_method():
    with patch("module.internal_method") as mock:
        download()
        mock.assert_called_once()  # 过于关注实现
```

### 8. 清理测试数据

```python
def test_with_cleanup(tmp_path):
    """Test that cleans up after itself"""
    # 使用 tmp_path fixture 自动清理
    test_file = tmp_path / "test.txt"
    test_file.write_text("test data")

    # 测试代码
    result = process_file(test_file)

    # tmp_path 会在测试后自动清理
```

---

## 常见问题

### Q: 如何跳过特定测试？

```python
@pytest.mark.skip(reason="功能尚未实现")
def test_future_feature():
    pass

@pytest.mark.skipif(sys.version_info < (3, 10), reason="需要 Python 3.10+")
def test_python310_feature():
    pass
```

### Q: 如何标记慢速测试？

```python
@pytest.mark.slow
def test_slow_integration():
    """这个测试需要10秒以上"""
    pass

# 运行时跳过慢速测试
pytest -m "not slow"
```

### Q: 如何调试失败的测试？

```bash
# 显示详细的 traceback
pytest -v --tb=long

# 进入 pdb 调试器
pytest --pdb

# 显示局部变量
pytest -l

# 只运行失败的测试
pytest --lf
```

### Q: 如何测试需要真实环境的场景？

```python
@pytest.mark.skip(reason="需要真实的 Pixiv Token")
def test_real_login():
    """这个测试需要真实的用户交互"""
    pass

# 或者使用环境变量控制
@pytest.mark.skipif(not os.getenv("ENABLE_INTEGRATION_TESTS"),
                    reason="设置 ENABLE_INTEGRATION_TESTS=1 启用")
def test_integration():
    pass
```

---

## 持续集成

项目使用 GitHub Actions 自动运行测试。每次提交都会触发：

1. **单元测试**: 所有模块的单元测试
2. **集成测试**: 标记为 `@pytest.mark.integration` 的测试
3. **覆盖率检查**: 确保覆盖率 >= 80%

查看 `.github/workflows/test.yml` 了解详情。

---

## 参考资料

- [Pytest 文档](https://docs.pytest.org/)
- [Pytest Fixtures](https://docs.pytest.org/en/stable/fixture.html)
- [Pytest Parametrize](https://docs.pytest.org/en/stable/how-to/parametrize.html)
- [pytest-cov](https://pytest-cov.readthedocs.io/)
- [unittest.mock](https://docs.python.org/3/library/unittest.mock.html)

---

## 更新日志

- 2026-03-04: 初始版本，创建全面的测试文档
