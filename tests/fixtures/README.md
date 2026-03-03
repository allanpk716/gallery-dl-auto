# Fixtures 使用指南

## 概述

`tests/fixtures` 目录包含测试基础设施，提供 Mock 数据和测试常量。

## 目录结构

```
tests/fixtures/
├── __init__.py              # 导出公共 API
├── test_data.py             # 测试数据常量
├── mock_pixiv_responses.py  # Mock API 响应工厂
└── test_fixtures.py         # fixtures 功能测试
```

## 快速开始

### 导入 Fixtures

```python
from tests.fixtures import (
    TestData,
    MockPixivResponses,
    create_mock_illust,
    create_mock_ranking_response,
)
```

### 使用测试数据常量

```python
from tests.fixtures import TestData

# 获取排行榜类型
api_modes = TestData.RANKING_MODES_API  # ['day', 'week', 'month', ...]
cli_modes = TestData.RANKING_MODES_CLI  # ['daily', 'weekly', 'monthly', ...]

# 获取测试日期
test_dates = TestData.VALID_DATES  # ['2026-02-24', '2026-02-25', ...]

# 获取测试 Token
valid_token = TestData.VALID_REFRESH_TOKEN
```

### 创建 Mock 数据

```python
from tests.fixtures import create_mock_illust, create_mock_ranking_response

# 创建单个作品
illust = create_mock_illust(
    illust_id=12345678,
    title="Test Artwork",
    author_name="Test Artist"
)

# 创建排行榜响应
response = create_mock_ranking_response(
    illusts=[illust],
    next_url=None  # 或 "https://..." 用于分页测试
)
```

## 主要功能

### 1. TestData 类

集中管理所有测试常量：

- **排行榜类型**: `RANKING_MODES_API`, `RANKING_MODES_CLI`, `CLI_TO_API_MAP`
- **日期**: `VALID_DATES`, `INVALID_DATE_FORMATS`, `FUTURE_DATES`
- **Token**: `VALID_REFRESH_TOKEN`, `ALT_REFRESH_TOKEN`, `INVALID_TOKENS`
- **作品**: `TEST_ILLUST_IDS`, `TEST_AUTHORS`, `TEST_TITLES`
- **URL**: `TEST_IMAGE_URLS`
- **统计**: `TEST_STATISTICS`
- **标签**: `TEST_TAGS`

### 2. MockPixivResponses 类

提供 Mock API 响应工厂方法：

- `create_mock_illust()`: 创建作品对象
- `create_mock_tag()`: 创建标签对象
- `create_mock_ranking_response()`: 创建排行榜响应
- `create_mock_artwork_detail_response()`: 创建作品详情响应
- `create_sample_ranking_data()`: 批量创建测试数据
- `create_sample_ranking_with_tags()`: 创建带标签的作品

## 使用示例

### 测试排行榜下载

```python
def test_ranking_download():
    # 创建测试数据
    illusts = MockPixivResponses.create_sample_ranking_data(count=30)
    response = create_mock_ranking_response(illusts=illusts)

    # 使用 Mock 数据测试
    mock_api.illust_ranking.return_value = response

    # 验证结果
    assert len(response.illusts) == 30
```

### 测试参数验证

```python
@pytest.mark.parametrize("mode", TestData.RANKING_MODES_CLI)
def test_all_ranking_modes(mode):
    # 使用所有 CLI 模式进行测试
    result = validate_ranking_type(mode)
    assert result in TestData.RANKING_MODES_API
```

### 测试分页

```python
def test_pagination():
    # 第一页
    page1 = MockPixivResponses.create_sample_ranking_data(count=30)
    response1 = create_mock_ranking_response(
        illusts=page1,
        next_url="https://api.pixiv.net/next"
    )

    # 第二页
    page2 = MockPixivResponses.create_sample_ranking_data(
        count=30,
        start_id=10000030
    )
    response2 = create_mock_ranking_response(illusts=page2)

    # 测试分页逻辑
    mock_api.illust_ranking.side_effect = [response1, response2]
```

## 最佳实践

1. **使用常量**: 优先使用 `TestData` 中的常量，而不是硬编码值
2. **工厂方法**: 使用 `MockPixivResponses` 工厂方法创建 Mock 对象
3. **一致性**: 在所有测试中使用相同的数据源
4. **可维护性**: 集中管理测试数据，便于更新和维护

## 代码质量

- ✅ 通过 ruff 代码检查
- ✅ 17 个单元测试全部通过
- ✅ 类型注解完整
- ✅ 文档字符串完整

## 扩展

如需添加新的测试数据或 Mock 对象：

1. 常量数据添加到 `test_data.py` 的 `TestData` 类
2. Mock 工厂方法添加到 `mock_pixiv_responses.py` 的 `MockPixivResponses` 类
3. 在 `__init__.py` 中导出新的 API
4. 添加相应的测试到 `test_fixtures.py`
