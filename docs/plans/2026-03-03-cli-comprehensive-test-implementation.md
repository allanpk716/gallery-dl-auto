# CLI 全面测试实施计划

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** 为 gallery-dl-auto 创建全面的自动化测试套件，覆盖所有 CLI 命令和参数

**Architecture:** 按命令模块分层组织测试，使用 pytest fixtures 管理测试数据，TDD 开发流程，每个命令包含功能、边界、错误处理、输出格式四类测试

**Tech Stack:** Python 3.10+, Pytest, Click testing utilities, pytest-mock, pytest-cov

---

## Phase 1: 基础设施准备（1-2小时）

### Task 1: 创建测试 fixtures 和 Mock 数据

**Files:**
- Create: `tests/fixtures/__init__.py`
- Create: `tests/fixtures/mock_pixiv_responses.py`
- Create: `tests/fixtures/test_data.py`

**实施步骤:**

1. 创建 fixtures 目录
2. 添加 Mock API 响应数据（排行榜、作品详情、Token）
3. 添加测试数据常量（排行榜类型列表、日期格式、测试Token）
4. Commit

**代码示例:**

```python
# tests/fixtures/mock_pixiv_responses.py
MOCK_RANKING_RESPONSE = {
    "contents": [
        {
            "illust_id": 12345678,
            "title": "测试作品1",
            "user_name": "测试作者1",
            "rank": 1
        }
    ]
}

# tests/fixtures/test_data.py
VALID_RANKING_TYPES = ["daily", "weekly", "day_male", "day_r18", ...]
TEST_TOKEN_DATA = {"refresh_token": "test_token", ...}
```

### Task 2: 增强共享 fixtures

**Files:**
- Modify: `tests/conftest.py`

**实施步骤:**

1. 添加 Click CLI 测试运行器 fixture
2. 添加临时目录和文件 fixtures
3. 添加 Mock PixivClient fixture
4. 运行测试验证 fixtures 可用
5. Commit

**代码示例:**

```python
@pytest.fixture
def runner():
    return CliRunner()

@pytest.fixture
def temp_token_file(temp_dir):
    from tests.fixtures.test_data import TEST_TOKEN_DATA
    # 创建临时 Token 文件
    ...
```

### Task 3: 创建测试辅助工具

**Files:**
- Create: `tests/utils/test_helpers.py`

**实施步骤:**

1. 创建 JSON 输出验证函数
2. 创建 JSONL 输出验证函数
3. 创建 CLI 命令运行辅助函数
4. 测试导入正常
5. Commit

---

## Phase 2: 主命令和全局选项测试（1小时）

### Task 4: 主命令测试

**Files:**
- Create: `tests/cli/test_main_commands.py`

**测试覆盖:**

1. **主命令测试**: help, version 输出
2. **全局选项测试**: verbose, quiet, json-output, json-help
3. **选项优先级测试**: json-output > quiet > verbose
4. **错误处理测试**: 无效命令、键盘中断

**代码示例:**

```python
def test_json_help(self, runner):
    result = runner.invoke(cli, ['--json-help'])
    assert result.exit_code == 0
    data = assert_json_output(result.output, ['name', 'commands'])
```

---

## Phase 3: 认证命令测试（2-3小时）

### Task 5-8: 认证命令测试套件

**Files:**
- Create: `tests/cli/test_login_cmd.py`
- Create: `tests/cli/test_logout_cmd.py`
- Create: `tests/cli/test_status_cmd.py`
- Create: `tests/cli/test_refresh_cmd.py`

**测试覆盖:**

**login 命令:**
- 首次登录（需要真实环境，skip）
- 强制重新登录 --force
- 错误处理（取消、网络错误）

**logout 命令:**
- 登出成功并删除Token
- 无Token时的处理
- JSON输出模式

**status 命令:**
- 有效/无效Token状态
- JSON输出模式
- 过期时间信息
- 边界测试（已过期、格式错误）

**refresh 命令:**
- 刷新成功（需要Mock）
- 无Token时刷新
- 错误处理

---

## Phase 4: 辅助命令测试（1-2小时）

### Task 9-11: 辅助命令测试

**Files:**
- Modify: `tests/test_cli/test_config_cmd.py`（增强）
- Create: `tests/cli/test_doctor_cmd.py`
- Create: `tests/cli/test_version_cmd.py`

**测试覆盖:**

**config 命令:** JSON输出、配置优先级
**doctor 命令:** 诊断项覆盖、JSON输出
**version 命令:** 版本输出、JSON格式、版本号验证

---

## Phase 5: Download 命令完整测试（2-3小时）

### Task 12: 增强 download 命令测试

**Files:**
- Modify: `tests/cli/test_download_cmd.py`

**测试覆盖:**

1. **参数测试** (参数化):
   - 所有有效排行榜类型（daily, weekly, day_male等）
   - 无效类型
   - 日期格式（YYYY-MM-DD）
   - limit参数（1, 10, 50, 100, 0边界）
   - offset参数（0, 10, 50, -1边界）

2. **输出格式测试**:
   - JSON格式验证
   - JSONL格式验证（紧凑、单行）

3. **引擎测试**:
   - gallery-dl引擎
   - internal引擎（已废弃警告）

**代码示例:**

```python
@pytest.mark.parametrize("ranking_type", ["daily", "weekly", "day_male"])
def test_valid_ranking_types(self, runner, ranking_type):
    result = runner.invoke(cli, ['download', '--type', ranking_type, '--dry-run'])
    assert result.exit_code == 0
```

---

## Phase 6: 参数验证器测试（1小时）

### Task 13: 验证器测试

**Files:**
- Modify: `tests/cli/test_validators.py`

**测试覆盖:**

1. **--type 参数验证**:
   - 所有有效类型（参数化）
   - 类型映射（day->daily, week->weekly）
   - 无效类型

2. **--date 参数验证**:
   - 有效格式（YYYY-MM-DD, YYYYMMDD）
   - None值（今天）
   - 无效格式、无效月份、无效日期
   - 未来日期

---

## Phase 7: 集成测试和文档（1-2小时）

### Task 14: 运行完整测试套件

**步骤:**

1. 运行所有CLI测试: `pytest tests/cli/ -v`
2. 生成覆盖率报告: `pytest tests/cli/ --cov=src/gallery_dl_auto/cli --cov-report=html`
3. 分析覆盖率，补充缺失测试
4. 修复失败的测试

### Task 15: 创建测试文档

**Files:**
- Create: `tests/README.md`

**内容:**
- 测试结构说明
- 如何运行测试
- 如何生成覆盖率报告
- 如何编写新测试
- 测试分类说明

### Task 16: 最终验证和提交

**步骤:**

1. 运行完整测试套件
2. 检查并修复所有失败测试
3. 确保覆盖率 >= 80%
4. 提交最终版本

---

## 执行计划总结

### 关键文件清单

**新增文件（12个）:**
```
tests/fixtures/__init__.py
tests/fixtures/mock_pixiv_responses.py
tests/fixtures/test_data.py
tests/utils/test_helpers.py
tests/cli/test_main_commands.py
tests/cli/test_login_cmd.py
tests/cli/test_logout_cmd.py
tests/cli/test_status_cmd.py
tests/cli/test_refresh_cmd.py
tests/cli/test_doctor_cmd.py
tests/cli/test_version_cmd.py
tests/README.md
```

**修改文件（4个）:**
```
tests/conftest.py
tests/cli/test_download_cmd.py
tests/cli/test_validators.py
tests/test_cli/test_config_cmd.py（可选）
```

### 成功标准

- ✅ 所有命令有对应的测试文件
- ✅ 每个命令包含功能、边界、错误处理、输出格式测试
- ✅ 测试覆盖率 >= 80%
- ✅ 所有测试可重复执行
- ✅ 文档完整

### 预计工作量

- Phase 1 (基础设施): 1-2 小时
- Phase 2 (主命令): 1 小时
- Phase 3 (认证命令): 2-3 小时
- Phase 4 (辅助命令): 1-2 小时
- Phase 5 (download命令): 2-3 小时
- Phase 6 (验证器): 1 小时
- Phase 7 (集成和文档): 1-2 小时

**总计**: 约 10-15 小时

### 测试分类

每个命令将包含四类测试：
1. **功能测试** - 验证基本功能正常工作
2. **边界测试** - 测试参数边界值（limit=0, offset<0等）
3. **错误处理测试** - 验证异常场景和错误消息
4. **输出格式测试** - 验证JSON和JSONL输出正确性

---

## 下一步行动

计划已完成并保存到 `docs/plans/2026-03-03-cli-comprehensive-test-implementation.md`

**两种执行方式:**

**选项 1: Subagent-Driven（当前会话）**
- 在当前会话中，我为每个任务派遣新的 subagent
- 任务间进行代码审查
- 快速迭代和反馈
- **适合**: 需要紧密协作、快速反馈的场景

**选项 2: Parallel Session（独立会话）**
- 在独立会话中调用 executing-plans 技能
- 批量执行任务，带检查点
- 独立运行，不占用当前会话
- **适合**: 长时间独立运行、批量执行的场景

**选择哪种方式？**
