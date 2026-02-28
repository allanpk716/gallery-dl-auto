---
phase: '10'
plan: '02A'
subsystem: 'api-validation'
tags:
  - exit-codes
  - authentication
  - validation
  - testing
dependencies:
  requires:
    - 10-01  # JSON 输出格式验证
  provides:
    - EXIT_CODE_MAPPING  # 退出码映射表
    - TestAuthExitCodes  # 认证退出码测试套件
  affects:
    - 10-02B  # 下载和参数退出码验证
    - 10-03A  # JSON 格式错误验证
tech_stack:
  added:
    - pytest fixtures (EXIT_CODE_MAPPING, verify_exit_code)
    - unittest.mock (Mock, patch)
  patterns:
    - Exit code mapping table (single source of truth)
    - Mock-based error scenario testing
key_files:
  created:
    - tests/validation/test_exit_codes.py
  modified:
    - tests/validation/conftest.py
decisions:
  - title: "退出码映射表设计"
    choice: "使用字典常量 EXIT_CODE_MAPPING 作为单一事实来源"
    rationale: "便于测试引用,与 INTEGRATION.md 保持一致,支持退出码到错误码的反向映射"
    alternatives:
      - "使用枚举类(可读性更好但灵活性稍差)"
  - title: "测试策略"
    choice: "使用 monkeypatch mock 关键函数而非真实调用"
    rationale: "隔离测试,避免真实 API 调用,测试执行速度快(0.37s)"
    alternatives:
      - "使用真实 token 进行集成测试(需要维护测试账号)"
metrics:
  duration: 125
  tasks_completed: 2
  files_modified: 2
  tests_added: 4
  tests_passed: 4
  completed_date: "2026-02-27"
---

# Phase 10 Plan 02A: 退出码验证(认证相关) Summary

## 一句话总结

建立退出码映射表并验证认证相关退出码(无 token、过期、无效、刷新失败)均返回退出码 1 且包含对应错误码字符串。

## 执行概况

**计划类型:** 自动执行(autonomous=true)
**执行状态:** 完成
**任务完成度:** 2/2 (100%)
**执行时长:** 125 秒(约 2 分钟)
**测试覆盖:** 4/4 测试通过(100%)

### 已完成任务

| Task | 名称 | 提交 Hash | 修改文件 |
| ---- | ---- | --------- | -------- |
| 1 | 建立退出码映射表 | bb3db3b | tests/validation/conftest.py |
| 2 | 实现认证相关退出码验证 | 3a7f23c | tests/validation/test_exit_codes.py |

## 技术实现

### 1. 退出码映射表(EXIT_CODE_MAPPING)

基于 `INTEGRATION.md` 和 `src/gallery_dl_auo/utils/error_codes.py` 建立:

```python
EXIT_CODE_MAPPING = {
    # 成功场景
    "SUCCESS": 0,

    # 认证错误
    "AUTH_TOKEN_NOT_FOUND": 1,
    "AUTH_TOKEN_EXPIRED": 1,
    "AUTH_TOKEN_INVALID": 1,
    "AUTH_REFRESH_FAILED": 1,

    # API 错误
    "API_NETWORK_ERROR": 1,
    "API_RATE_LIMIT": 1,
    # ... (共 22 个错误码)

    # 参数错误
    "INVALID_ARGUMENT": 2,
    "INVALID_DATE_FORMAT": 2,
}
```

**关键设计决策:**
- 使用字典常量作为单一事实来源
- 退出码分类: 0(成功)、1(通用错误)、2(参数错误)
- 包含 `verify_exit_code()` 辅助函数用于测试断言

### 2. 认证退出码验证测试(TestAuthExitCodes)

实现 4 个测试用例,覆盖所有认证错误场景:

| 测试方法 | 模拟场景 | 验证点 |
| -------- | -------- | ------ |
| test_no_token_exit_code | token_storage.load_token() 返回 None | 退出码 1,输出包含 AUTH_TOKEN_NOT_FOUND |
| test_expired_token_exit_code | PixivClient 初始化抛出 "Token expired" | 退出码 1,输出包含 AUTH_TOKEN_INVALID/EXPIRED |
| test_invalid_token_exit_code | PixivClient 初始化抛出 "Invalid token format" | 退出码 1,输出包含 AUTH_TOKEN_INVALID |
| test_refresh_failed_exit_code | PixivClient 初始化抛出 OAuthError("Refresh failed") | 退出码 1,输出包含 AUTH 错误码 |

**测试策略:**
- 使用 `monkeypatch` mock 关键函数(`get_default_token_storage`, `PixivClient`)
- 隔离测试,避免真实 API 调用
- 验证退出码和错误码字符串双重断言

## 验证结果

### Must-haves 验证

所有 must-have 条件均已满足:

- ✅ **退出码映射表已建立**: EXIT_CODE_MAPPING 在 conftest.py 中定义,包含 22 个错误码
- ✅ **认证退出码已验证**: TestAuthExitCodes 所有 4 个测试通过
- ✅ **测试通过**: `pytest tests/validation/test_exit_codes.py::TestAuthExitCodes -v` 显示 4/4 passed
- ✅ **VAL-02 需求部分满足**: 可以展示认证相关退出码经过验证的证据

**测试执行输出:**
```
tests/validation/test_exit_codes.py::TestAuthExitCodes::test_no_token_exit_code PASSED [ 25%]
tests/validation/test_exit_codes.py::TestAuthExitCodes::test_expired_token_exit_code PASSED [ 50%]
tests/validation/test_exit_codes.py::TestAuthExitCodes::test_invalid_token_exit_code PASSED [ 75%]
tests/validation/test_exit_codes.py::TestAuthExitCodes::test_refresh_failed_exit_code PASSED [100%]

======================== 4 passed, 2 warnings in 0.37s ========================
```

## 需求满足情况

### VAL-02 (部分): 退出码验证

- ✅ 认证相关退出码(4 个场景)已验证
- ⏳ 下载和参数退出码验证将在 10-02B 中完成
- ⏳ 完整的 VAL-02 需求将在完成 10-02B 后满足

## 依赖关系

### 依赖的上游计划

- ✅ **10-01 (JSON 输出格式验证)**: 提供了测试框架和 conftest.py 基础设施

### 被依赖的下游计划

- **10-02B (下载和参数退出码验证)**: 将使用本计划建立的 EXIT_CODE_MAPPING
- **10-03A (JSON 格式错误验证)**: 将使用测试框架扩展更多验证场景

## 偏离计划情况

**无偏离** - 计划执行完全符合 PLAN.md 描述。

## 质量指标

- **测试覆盖:** 4/4 测试通过(100%)
- **代码质量:** 遵循项目编码规范,使用类型提示
- **文档完整性:** 代码注释清晰,测试意图明确
- **执行速度:** 0.37 秒(快速反馈)

## 后续工作

本计划专注于认证相关退出码验证,后续计划将继续验证其他场景:

- **10-02B**: 下载错误和参数错误退出码验证
- **10-03A**: JSON 格式错误验证(使用 --json-output 模式)
- **10-03B**: 静默模式和详细模式验证

## 提交记录

1. **bb3db3b** - feat(10-02A): establish exit code mapping table
   - 添加 EXIT_CODE_MAPPING 字典(22 个错误码)
   - 添加 verify_exit_code() 辅助函数

2. **3a7f23c** - feat(10-02A): implement authentication exit code validation tests
   - 创建 TestAuthExitCodes 测试类
   - 实现 4 个认证退出码测试方法
   - 所有测试通过,验证 VAL-02(部分)

---

**执行时间:** 2026-02-27
**执行者:** Claude Sonnet 4.6
**状态:** 完成 ✅

## Self-Check: PASSED

- ✅ tests/validation/test_exit_codes.py 文件已创建
- ✅ 提交 bb3db3b (退出码映射表)已存在
- ✅ 提交 3a7f23c (认证退出码测试)已存在
- ✅ 所有 must-have 条件验证通过
- ✅ 测试套件执行成功(4/4 passed)
