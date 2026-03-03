# CLI 命令全面测试方案设计

## 设计日期
2026-03-03

## 背景

gallery-dl-auto 项目需要一个全面的自动化测试套件，覆盖所有 CLI 命令和参数，确保功能正确性和代码质量。

## 目标

创建按命令模块分层的自动化测试代码，实现全面质量保证：
- ✅ 功能正确性验证
- ✅ 边界条件测试
- ✅ 错误处理验证
- ✅ 输出格式兼容性测试

## 测试策略

### 分层方法

按命令模块分层组织测试，每个命令有独立的测试文件。

**优点：**
- 结构清晰，易于维护
- 每个命令独立测试，互不干扰
- 易于定位和修复问题
- 支持增量开发

### 测试环境

- 有真实环境可用（测试账号、Token、网络）
- 支持 Mock 和真实 API 调用
- Windows 开发环境

### 输出形式

- Pytest 自动化测试代码
- 使用 fixtures 管理测试数据
- 参数化测试提高覆盖率

## 测试架构

```
tests/
├── cli/                          # CLI 命令测试模块
│   ├── test_main.py             # 主命令和全局选项
│   ├── test_download_cmd.py     # download 命令完整测试
│   ├── test_login_cmd.py        # login 命令测试（新增）
│   ├── test_logout_cmd.py       # logout 命令测试（新增）
│   ├── test_status_cmd.py       # status 命令测试（新增）
│   ├── test_config_cmd.py       # config 命令测试（已存在）
│   ├── test_doctor_cmd.py       # doctor 命令测试（新增）
│   ├── test_version_cmd.py      # version 命令测试（新增）
│   ├── test_refresh_cmd.py      # refresh 命令测试（新增）
│   └── test_validators.py       # 参数验证器测试（已存在）
├── fixtures/                     # 测试数据和 Mock 对象（新增）
│   ├── mock_pixiv_responses.py  # Pixiv API Mock 响应
│   └── test_data.py             # 测试数据常量
└── conftest.py                   # 共享 fixtures（增强）
```

## 每个命令的测试覆盖范围

### 1. 主命令 (main.py)

**全局选项测试：**
- `--verbose, -v`: 详细模式
- `--quiet, -q`: 静默模式
- `--json-output`: JSON 输出模式
- `--json-help`: 结构化 JSON 帮助

**测试场景：**
- ✅ 正常启动和退出
- ✅ 全局选项组合（verbose + quiet, json-output + verbose）
- ✅ JSON 帮助输出格式验证
- ✅ 错误处理和异常捕获

### 2. download 命令

**参数测试：**
- `--type`: 排行榜类型（必需）
- `--date`: 日期（可选）
- `--output, -o`: 输出目录
- `--path-template`: 路径模板
- `--verbose, -v`: 详细模式
- `--image-delay`: 单张图片间隔
- `--batch-delay`: 批次间隔
- `--batch-size`: 批次大小
- `--max-retries`: 最大重试次数
- `--limit`: 最多下载作品数
- `--offset`: 跳过前 N 个作品
- `--dry-run`: 预览模式
- `--engine`: 下载引擎（gallery-dl/internal）
- `--format`: 输出格式（json/jsonl）

**测试场景：**
- ✅ 功能测试：正常下载流程
- ✅ 参数边界：limit=0, offset<0, 日期格式验证
- ✅ 错误处理：Token 失效、网络错误、参数无效
- ✅ 输出格式：验证 JSON 和 JSONL 输出正确性
- ✅ 引擎切换：gallery-dl 和 internal 引擎对比
- ✅ 断点续传：中断恢复测试
- ✅ dry-run 模式：预览功能测试

### 3. login 命令

**参数测试：**
- `--force`: 强制重新登录

**测试场景：**
- ✅ 功能测试：首次登录流程
- ✅ 强制重新登录：--force 参数测试
- ✅ Token 存储：验证 Token 正确保存
- ✅ 错误处理：登录失败、网络错误

### 4. logout 命令

**测试场景：**
- ✅ 功能测试：登出流程
- ✅ Token 清理：验证 Token 被正确删除
- ✅ 错误处理：Token 不存在时的处理

### 5. status 命令

**测试场景：**
- ✅ 功能测试：显示 Token 状态
- ✅ JSON 输出：--json-output 模式验证
- ✅ Token 有效/无效状态测试

### 6. config 命令

**测试场景：**
- ✅ 功能测试：显示当前配置
- ✅ JSON 输出：--json-output 模式验证
- ✅ 配置文件加载和优先级测试

### 7. doctor 命令

**测试场景：**
- ✅ 功能测试：环境和配置诊断
- ✅ JSON 输出：--json-output 模式验证
- ✅ 诊断项覆盖：Token、配置、网络、依赖

### 8. version 命令

**测试场景：**
- ✅ 功能测试：显示版本信息
- ✅ JSON 输出：--json-output 模式验证

### 9. refresh 命令

**测试场景：**
- ✅ 功能测试：刷新 Token
- ✅ Token 更新验证
- ✅ 错误处理：Token 失效、网络错误

### 10. 参数验证器 (validators.py)

**测试场景：**
- ✅ `--type` 参数验证：支持的所有排行榜类型
- ✅ `--date` 参数验证：日期格式验证
- ✅ 参数转换：CLI 名称到 API 名称的映射

## 测试类型

每个命令将包含以下测试类型：

### 1. 功能测试 (Functional Tests)
- 验证命令的基本功能
- 测试正常使用场景
- 验证输出内容正确性

### 2. 边界测试 (Boundary Tests)
- 测试参数的有效/无效值
- 测试边界条件（limit=0, offset<0 等）
- 测试参数组合

### 3. 错误处理测试 (Error Handling Tests)
- 验证异常场景
- 测试错误消息和退出码
- 验证错误恢复机制

### 4. 输出格式测试 (Output Format Tests)
- 验证 JSON 输出格式
- 验证 JSONL 输出格式
- 验证 JSON Schema 合规性

## 测试数据管理

### Fixtures

使用 pytest fixtures 管理测试数据：

```python
# conftest.py
@pytest.fixture
def mock_token():
    """提供测试用 Token"""
    return {
        "refresh_token": "test_refresh_token",
        "expires_at": "2026-12-31T23:59:59"
    }

@pytest.fixture
def temp_config(tmp_path):
    """提供临时配置文件"""
    config_file = tmp_path / "config.yaml"
    config_file.write_text("""
save_path: ./downloads
concurrent_downloads: 3
""")
    return config_file
```

### Mock 对象

为 API 调用创建 Mock 对象：

```python
# fixtures/mock_pixiv_responses.py
MOCK_RANKING_RESPONSE = {
    "contents": [
        {
            "illust_id": 12345678,
            "title": "测试作品",
            "user_name": "测试作者",
            # ...
        }
    ]
}
```

## 测试执行

### 运行所有测试
```bash
pytest tests/cli/ -v
```

### 运行特定命令测试
```bash
pytest tests/cli/test_download_cmd.py -v
```

### 运行特定测试类型
```bash
# 只运行功能测试
pytest tests/cli/ -v -k "functional"

# 只运行边界测试
pytest tests/cli/ -v -k "boundary"
```

## 测试报告

使用 pytest-cov 生成覆盖率报告：

```bash
pytest tests/cli/ --cov=src/gallery_dl_auto/cli --cov-report=html
```

## 实施计划

### 阶段 1: 基础设施准备
- 创建 fixtures 目录和共享 fixtures
- 设置 Mock 对象和测试数据
- 增强现有 conftest.py

### 阶段 2: 主命令和全局选项测试
- 增强 test_main.py
- 测试全局选项组合
- 测试 JSON 帮助输出

### 阶段 3: download 命令测试（增强）
- 增强现有 test_download_cmd.py
- 添加完整的参数测试
- 添加输出格式测试

### 阶段 4: 认证相关命令测试
- 创建 test_login_cmd.py
- 创建 test_logout_cmd.py
- 创建 test_status_cmd.py
- 创建 test_refresh_cmd.py

### 阶段 5: 辅助命令测试
- 创建 test_config_cmd.py（如需要增强）
- 创建 test_doctor_cmd.py
- 创建 test_version_cmd.py

### 阶段 6: 参数验证器测试
- 增强 test_validators.py
- 测试所有参数验证逻辑

### 阶段 7: 集成测试和回归测试
- 运行完整测试套件
- 修复发现的问题
- 生成测试覆盖率报告

## 成功标准

- ✅ 所有命令测试覆盖率达到 80% 以上
- ✅ 所有测试用例通过
- ✅ 边界条件和错误处理完整覆盖
- ✅ 输出格式测试验证 JSON/JSONL 正确性
- ✅ 测试可重复执行，无环境依赖问题

## 维护指南

### 添加新命令测试
1. 在 `tests/cli/` 创建新测试文件
2. 使用共享 fixtures
3. 遵循现有测试命名约定
4. 确保覆盖功能、边界、错误、输出格式

### 更新现有测试
1. 修改对应的测试文件
2. 更新 fixtures（如需要）
3. 运行完整测试套件确保无回归

## 参考资料

- [Pytest 官方文档](https://docs.pytest.org/)
- [Click 测试指南](https://click.palletsprojects.com/en/8.1.x/testing/)
- 项目现有测试：`tests/` 目录
