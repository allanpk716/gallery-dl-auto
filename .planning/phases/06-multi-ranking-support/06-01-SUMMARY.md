---
phase: 06-multi-ranking-support
plan: 01
subsystem: CLI/API
tags: [ranking, validation, api-extension, cli-parameters]
requires: []
provides: [ranking-type-validation, date-validation, multi-ranking-support]
affects: [download-command, pixiv-client, validators]
tech_stack:
  added: []
  patterns: [parameter-validation, type-mapping, click-callbacks]
key_files:
  created:
    - src/gallery_dl_auo/cli/validators.py
    - tests/cli/test_validators.py
  modified:
    - src/gallery_dl_auo/api/pixiv_client.py
    - tests/api/test_pixiv_client.py
    - src/gallery_dl_auo/cli/download_cmd.py
    - tests/cli/test_download_cmd.py
decisions:
  - 使用 13 种排行榜类型的映射表 (RANKING_MODES)
  - 用户友好的类型名称 (weekly) 映射到 API mode 参数 (week)
  - Click 参数验证器使用 callback 模式
  - 必需参数无默认值,强制用户显式指定
metrics:
  duration: 25 min
  tasks_completed: 3
  files_modified: 4
  files_created: 2
  test_cases_added: 47
  test_cases_passed: 47
  completed_date: 2026-02-25
---

# Phase 6 Plan 01: 排行榜类型扩展和验证 Summary

## 一句话总结

扩展 CLI 和 API 支持 13 种排行榜类型,实现类型验证、日期验证和 mode 参数映射,用户可通过 --type 参数指定任何排行榜类型。

## 完成的任务

### Task 1: 创建类型和日期验证器模块

**创建文件:**
- `src/gallery_dl_auo/cli/validators.py` - 验证器模块
- `tests/cli/test_validators.py` - 单元测试

**实现内容:**
1. 排行榜类型映射表 (RANKING_MODES),包含 13 种类型:
   - 常规: daily, weekly, monthly
   - 分类: day_male, day_female, week_original, week_rookie, day_manga
   - R18: day_r18, day_male_r18, day_female_r18, week_r18, week_r18g

2. 核心验证函数:
   - `validate_ranking_type()`: 验证类型并返回 API mode 参数
   - `validate_ranking_date()`: 验证日期格式和未来日期

3. Click 参数验证器:
   - `validate_type_param()`: 排行榜类型验证器
   - `validate_date_param()`: 日期验证器

**测试覆盖:** 30 个测试用例,覆盖所有验证场景

**Commit:** 76dab34

### Task 2: 扩展 PixivClient.get_ranking() 支持 mode 参数

**修改文件:**
- `src/gallery_dl_auo/api/pixiv_client.py` - 更新文档字符串
- `tests/api/test_pixiv_client.py` - 添加测试用例

**实现内容:**
1. 更新 `get_ranking()` 方法文档,明确列出所有 13 种支持的 mode 值
2. 添加参数化测试,覆盖所有排行榜类型
3. 添加带日期参数的测试用例

**测试覆盖:** 14 个新测试用例,验证所有 mode 参数

**Commit:** 1eec542

### Task 3: 集成验证器到 download 命令

**修改文件:**
- `src/gallery_dl_auo/cli/download_cmd.py` - 命令实现
- `tests/cli/test_download_cmd.py` - 测试更新

**实现内容:**
1. 将 `--mode` 参数替换为 `--type` 参数(必需)
2. 集成 `validate_type_param` 和 `validate_date_param` 验证器
3. `--type` 参数自动转换为 API mode (weekly -> week)
4. 更新所有现有测试以使用 `--type` 参数
5. 新增测试用例:
   - 无效排行榜类型验证
   - 未来日期验证
   - 缺少必需参数验证

**测试覆盖:** 14 个测试用例全部通过

**Commit:** 23835f9

## 技术实现细节

### 类型映射机制

```python
RANKING_MODES = {
    "daily": "day",      # 用户输入 -> API 参数
    "weekly": "week",
    "monthly": "month",
    # ... 共 13 种
}
```

### 验证流程

1. 用户输入: `--type weekly`
2. Click 验证器调用: `validate_type_param("weekly")`
3. 类型验证: `validate_ranking_type("weekly")`
4. 返回 API mode: `"week"`
5. 传递给 `get_ranking(mode="week")`

### 错误信息示例

```python
# 无效类型
"Invalid ranking type 'xyz'. Valid types: daily, day_female, day_male, ..."

# 未来日期
"Date '2099-12-31' is in the future"

# 无效日期格式
"Invalid date '2026/02/18'. Format: YYYY-MM-DD"
```

## 偏差记录

**None** - 计划执行完全按照 PLAN.md 文档进行,无偏差。

## 关键决策

1. **参数名称选择**: 使用 `--type` 而非 `--mode`,更符合用户认知 (类型 vs 模式)
2. **必需参数**: `--type` 无默认值,强制用户显式指定,避免意外下载错误的排行榜
3. **类型映射**: 用户友好名称 (weekly) 与 API 参数 (week) 分离,提升用户体验
4. **错误信息**: 包含所有有效类型列表,帮助用户快速纠正错误

## 测试总结

**总测试用例:** 47 个
- 验证器测试: 30 个
- API 客户端测试: 14 个
- CLI 命令测试: 14 个 (包含 3 个新测试)

**测试通过率:** 100% (47/47)

**测试覆盖场景:**
- 所有 13 种排行榜类型的验证和映射
- 有效日期、无效日期格式、未来日期验证
- Click 验证器集成测试
- 无效类型和缺失参数的错误处理

## 满足的需求

| 需求 ID | 描述 | 实现状态 |
|---------|------|---------|
| RANK-02 | 用户能够下载 pixiv 每周排行榜 | ✅ 已完成 (weekly -> week 映射) |
| RANK-03 | 用户能够下载 pixiv 每月排行榜 | ✅ 已完成 (monthly -> month 映射) |

## 后续计划

**Plan 02:** 大规模数据集处理和断点续传
- 扩展 `get_ranking()` 自动跟随 `next_url`
- 实现进度文件和重试机制
- 支持月榜 1500+ 张完整下载

## 执行指标

- **执行时间:** 25 分钟
- **任务完成率:** 100% (3/3)
- **测试通过率:** 100% (47/47)
- **代码文件:** 6 个 (2 新建, 4 修改)
- **提交次数:** 3 次 (每个任务一次)

---

**执行日期:** 2026-02-25
**执行者:** Claude Sonnet 4.6
**状态:** ✅ 完成

## Self-Check: PASSED

**验证项目:**
- ✅ validators.py 文件存在
- ✅ test_validators.py 文件存在
- ✅ Commit 76dab34 存在
- ✅ Commit 1eec542 存在
- ✅ Commit 23835f9 存在
- ✅ 06-01-SUMMARY.md 文件存在

所有声明的文件和提交均已验证存在。
