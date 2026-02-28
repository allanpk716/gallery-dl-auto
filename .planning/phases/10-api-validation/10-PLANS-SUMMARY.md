# Phase 10: API 验证 - 计划完成总结

**Created:** 2026-02-26
**Phase:** 10 (API 验证)
**Total Plans:** 6 (3 主计划 + 3 子计划)
**Status:** Ready for execution

---

## 概述

Phase 10 专注于验证 gallery-dl-auto 的 CLI API 一致性和可靠性,确保第三方集成的稳定性。本阶段包含 3 个主计划(10-01, 10-02, 10-03),每个主计划分为 A 和 B 两个子计划,外加 1 个 gap closure 计划(10-01-GAP01),分别验证 JSON 输出格式、退出码和集成场景。

## 计划清单

### Wave 1 (并行执行)

#### 10-01: JSON 输出格式验证
- **Goal**: 验证所有现有命令的 JSON 输出格式,确保符合 INTEGRATION.md 中定义的规范
- **Requirements**: VAL-01
- **Tasks**: 4 个任务
  1. 安装 jsonschema 依赖并建立测试基础设施
  2. 定义所有命令的 JSON Schema
  3. 实现 JSON 输出验证测试
  4. 验证所有命令的 JSON 输出格式
- **Files Modified**:
  - tests/validation/conftest.py (新建)
  - tests/validation/test_json_schemas.py (新建)
  - pyproject.toml (更新依赖)
- **Depends on**: 无
- **Autonomous**: true
- **Status**: ✅ 已完成

#### 10-01-GAP01: 修复 JSON Schema 测试导入路径 (Gap Closure)
- **Goal**: 修复 test_json_schemas.py 中的导入路径错误,使所有测试通过
- **Requirements**: VAL-01 (支持父计划)
- **Type**: Gap Closure
- **Tasks**: 3 个任务
  1. 修复模型导入路径 (BatchDownloadResult, StructuredError)
  2. 修复 monkeypatch 目标路径 (status_cmd, config_cmd)
  3. 验证所有测试通过
- **Files Modified**:
  - tests/validation/test_json_schemas.py (修复导入路径)
- **Depends on**: 10-01
- **Autonomous**: true
- **Status**: ⏳ 待执行

### Wave 2 (依赖 Wave 1)

#### 10-02A: 退出码验证 (认证相关)
- **Goal**: 建立退出码映射表,验证认证错误场景返回正确的退出码
- **Requirements**: VAL-02 (部分)
- **Tasks**: 2 个任务
  1. 建立退出码映射表
  2. 实现认证相关退出码验证
- **Files Modified**:
  - tests/validation/test_exit_codes.py (新建)
  - tests/validation/conftest.py (更新)
- **Depends on**: 10-01-GAP01
- **Autonomous**: true
- **Status**: ⏳ 待执行

#### 10-02B: 退出码验证 (下载和参数错误)
- **Goal**: 验证下载和参数错误场景返回正确的退出码
- **Requirements**: VAL-02 (部分)
- **Tasks**: 3 个任务
  1. 实现下载相关退出码验证
  2. 实现参数错误退出码验证
  3. 验证所有退出码并记录结果
- **Files Modified**:
  - tests/validation/test_exit_codes.py (更新)
  - tests/validation/conftest.py (更新)
- **Depends on**: 10-02A
- **Autonomous**: true
- **Status**: ✅ 已完成

### Wave 3 (依赖 Wave 1 和 Wave 2)

#### 10-03A: 集成测试 (基本和下载)
- **Goal**: 使用 subprocess 模拟第三方工具调用,验证基本命令和下载命令的集成
- **Requirements**: VAL-03 (部分)
- **Tasks**: 2 个任务
  1. 实现基本 subprocess 集成测试
  2. 实现下载命令集成测试
- **Files Modified**:
  - tests/validation/test_integration.py (新建)
  - tests/validation/conftest.py (更新)
- **Depends on**: 10-01-GAP01, 10-02B
- **Autonomous**: true
- **Status**: ⏳ 待执行

#### 10-03B: 集成测试 (批量下载和错误恢复)
- **Goal**: 验证批量下载和错误恢复机制
- **Requirements**: VAL-03 (部分)
- **Tasks**: 3 个任务
  1. 实现批量下载集成测试
  2. 实现错误恢复机制测试
  3. 运行完整集成测试并记录结果
- **Files Modified**:
  - tests/validation/test_integration.py (更新)
  - tests/validation/conftest.py (更新)
  - tests/validation/VALIDATION_RESULTS.md (新建)
- **Depends on**: 10-03A
- **Autonomous**: true
- **Status**: ✅ 已完成

---

## 执行策略

### 并行执行 (Waves)

```
Wave 1:
  10-01 (JSON 输出格式验证) ✅ 已完成
    ↓
  10-01-GAP01 (修复导入路径) ⏳ 待执行

Wave 2: [等待 Wave 1 完成]
  10-02A (认证退出码验证) ⏳ 待执行
    ↓
  10-02B (下载/参数退出码验证) ✅ 已完成

Wave 3: [等待 Wave 1 和 Wave 2 完成]
  10-03A (基本/下载集成测试) ⏳ 待执行
    ↓
  10-03B (批量/错误恢复集成测试) ✅ 已完成
```

### 预计时间

- **10-01**: ✅ 已完成
- **10-01-GAP01**: ~5 分钟 (导入路径修复)
- **10-02A**: ~10 分钟 (建立映射表、实现验证测试)
- **10-02B**: ✅ 已完成
- **10-03A**: ~15 分钟 (实现基本和下载集成测试)
- **10-03B**: ✅ 已完成
- **待执行总计**: ~30 分钟

---

## 需求覆盖

| Requirement | Plans | Status |
|-------------|-------|--------|
| VAL-01: 所有现有命令的 JSON 输出格式经过验证 | 10-01 ✅ + 10-01-GAP01 ⏳ | Gap Closure 待执行 |
| VAL-02: 所有退出码经过验证,与文档说明完全一致 | 10-02A ⏳ + 10-02B ✅ | 部分完成 |
| VAL-03: 第三方工具调用场景经过集成测试验证 | 10-03A ⏳ + 10-03B ✅ | 部分完成 |

**Coverage**: 3/6 计划已完成 (50%)

**Note**: 10-02B 和 10-03B 已完成,但依赖 10-01-GAP01 的 Wave 2 和 Wave 3 计划需在 gap closure 后执行。

---

## 成功标准 (Phase Goal Verification)

完成所有计划后,以下条件必须为 TRUE:

1. ✅ **VAL-01**: 所有现有命令的 JSON 输出格式经过验证,符合 INTEGRATION.md 中定义的规范
2. ⏳ **VAL-02**: 所有退出码经过验证,与文档说明完全一致,第三方工具可依赖退出码判断执行状态
3. ⏳ **VAL-03**: 第三方工具调用场景经过集成测试验证,真实场景下工作可靠

**验证命令**:
```bash
# 运行所有验证测试
pytest tests/validation/ -v

# 预期输出
# X passed, Y warnings
# ✅ 所有 API 验证测试通过 (VAL-01, VAL-02, VAL-03)
```

---

## 关键文件

### 测试框架

```
tests/validation/
├── __init__.py                    # 包初始化
├── conftest.py                    # 共享 fixtures 和 JSON Schema
├── test_json_schemas.py           # JSON Schema 验证测试
├── test_exit_codes.py             # 退出码验证测试
├── test_integration.py            # 第三方集成测试
└── VALIDATION_RESULTS.md          # 验证结果报告
```

### 依赖

```toml
# pyproject.toml
[project.optional-dependencies]
dev = [
    # ... 现有依赖 ...
    "jsonschema>=4.26.0",  # JSON Schema 验证
]
```

---

## 风险和缓解措施

### 风险 1: 现有命令的 JSON 输出格式与 INTEGRATION.md 不一致
- **影响**: VAL-01 失败,需要修复 CLI 实现
- **缓解**: 优先验证高频命令,更新文档或代码以保持一致
- **应急**: 更新 INTEGRATION.md 以匹配实际实现

### 风险 2: 部分错误场景难以在测试中模拟
- **影响**: VAL-02 测试覆盖不完整
- **缓解**: 优先验证高频错误场景,低频错误手动验证
- **应急**: 记录未验证场景,在文档中说明

### 风险 3: subprocess 集成测试在 Windows 上失败
- **影响**: VAL-03 测试不稳定
- **缓解**: 显式指定 encoding='utf-8',使用绝对路径
- **应急**: 标记 Windows 特定测试为可选

---

## 依赖关系

### 外部依赖
- Phase 8.1: CLI API 增强 (--json-help, --quiet, --json-output)
- Phase 9: INTEGRATION.md 集成文档
- Phase 7: 结构化错误码系统 (error_codes.py)

### 内部依赖
- 10-01 → 10-02: 退出码验证需要 JSON Schema 测试框架
- 10-01 + 10-02 → 10-03: 集成测试需要 JSON 和退出码验证结果

---

## 验证清单

在提交 Phase 10 完成之前,确认:

- [ ] 所有测试通过: `pytest tests/validation/ -v`
- [ ] JSON 输出格式验证: `pytest tests/validation/test_json_schemas.py -v`
- [ ] 退出码验证: `pytest tests/validation/test_exit_codes.py -v`
- [ ] 集成测试: `pytest tests/validation/test_integration.py -v`
- [ ] 验证结果报告: tests/validation/VALIDATION_RESULTS.md 已更新
- [ ] VAL-01, VAL-02, VAL-03 需求全部满足
- [ ] 手动验证: CLI 命令在真实场景下工作正常

---

## 后续步骤

完成 Phase 10 后:

1. **更新 STATE.md**: 标记 Phase 10 完成,更新进度
2. **更新 ROADMAP.md**: 标记 v1.2 里程碑完成
3. **准备发布**: v1.2 第三方 CLI 集成优化版本
4. **收集反馈**: 从第三方集成开发者处收集反馈

---

## 参考

- Research: .planning/phases/10-api-validation/10-API-VALIDATION-RESEARCH.md
- Integration Doc: ./INTEGRATION.md
- Error Codes: src/gallery_dl_auo/utils/error_codes.py
- Requirements: .planning/REQUIREMENTS.md

---

*Plans created: 2026-02-26*
*Ready for execution: /gsd:execute-phase*
