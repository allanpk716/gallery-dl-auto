---
phase: 09-集成文档
plan: 03
subsystem: documentation
tags:
  - integration
  - exit-codes
  - best-practices
  - documentation
  - developer-guide
dependency_graph:
  requires:
    - Phase 08.1 (JSON API 实现)
    - error_codes.py (错误码定义)
  provides:
    - 完整的退出码参考文档
    - 第三方集成最佳实践指南
  affects:
    - 第三方开发者集成体验
    - 自动化流程错误处理
tech_stack:
  added: []
  patterns:
    - 标准化错误码体系
    - 集成文档编写规范
key_files:
  created: []
  modified:
    - INTEGRATION.md
decisions:
  - 基于 error_codes.py 实际定义记录所有 22 个错误码(而非计划中估计的 20 个)
  - 错误码按类别分组(AUTH、API、FILE、DOWNLOAD、METADATA、INVALID、INTERNAL)便于查阅
  - 最佳实践包含完整代码示例,便于开发者快速上手
metrics:
  duration: 3 min
  tasks: 2
  files: 1
  completed_date: "2026-02-26"
---

# Phase 09 Plan 03: 退出码参考和最佳实践

## 一句话总结

为 INTEGRATION.md 添加完整的 22 个退出码参考表格和第三方集成最佳实践指南,包含参数选择、错误处理和性能优化建议。

## 计划目标

编写 INTEGRATION.md 的退出码参考和最佳实践章节,为第三方开发者提供完整的错误码文档和集成指南。

**主要目标**:
- ✅ 记录所有 22 个标准化错误码
- ✅ 按类别组织错误码表格
- ✅ 提供错误码使用示例(Bash 和 Python)
- ✅ 提供参数选择建议
- ✅ 提供错误处理和重试机制建议
- ✅ 提供性能优化建议
- ✅ 提供集成测试建议

## 执行的任务

### Task 1: 编写退出码参考章节

**完成内容**:
- ✅ 添加"退出码参考"章节
- ✅ 包含所有 22 个错误码(基于 error_codes.py)
- ✅ 按 7 个类别分组:
  - 认证相关 (4 个): AUTH_TOKEN_NOT_FOUND、AUTH_TOKEN_EXPIRED、AUTH_TOKEN_INVALID、AUTH_REFRESH_FAILED
  - API 相关 (4 个): API_NETWORK_ERROR、API_RATE_LIMIT、API_SERVER_ERROR、API_INVALID_RESPONSE
  - 文件系统相关 (3 个): FILE_PERMISSION_ERROR、FILE_DISK_FULL、FILE_INVALID_PATH
  - 下载相关 (7 个): DOWNLOAD_FAILED、DOWNLOAD_TIMEOUT、DOWNLOAD_PERMISSION_DENIED、DOWNLOAD_DISK_FULL、DOWNLOAD_FILE_EXISTS、DOWNLOAD_NETWORK_ERROR、RATE_LIMIT_EXCEEDED
  - 元数据相关 (1 个): METADATA_FETCH_FAILED
  - 参数相关 (2 个): INVALID_ARGUMENT、INVALID_DATE_FORMAT
  - 内部错误 (1 个): INTERNAL_ERROR
- ✅ 提供错误码使用示例(Bash 和 Python)
- ✅ 包含注意事项说明

**验证结果**:
```bash
✓ 退出码参考章节存在
✓ 退出码分类存在
✓ 所有 22 个错误码已记录
```

### Task 2: 编写最佳实践章节

**完成内容**:
- ✅ 添加"最佳实践"章节
- ✅ 参数选择建议:
  - 输出控制参数选择表格
  - 推荐参数组合示例
- ✅ 错误处理建议:
  - 完整的错误处理流程(包含超时和异常处理)
  - 重试机制(根据错误类型选择重试策略)
- ✅ 性能优化建议:
  - 避免触发速率限制(请求间隔建议)
  - 使用静默模式减少 I/O
  - 并行下载注意事项
- ✅ 集成测试建议:
  - 验证 CLI 可用性
  - 测试错误处理场景
- ✅ 文档和注释建议:
  - 代码注释推荐
  - README 集成说明模板

**验证结果**:
```bash
✓ 最佳实践章节存在
✓ 参数选择建议存在
✓ 错误处理建议存在
✓ 性能优化建议存在
```

## 偏差和调整

### 偏差 1: 错误码数量调整

**计划预期**: 20 个错误码
**实际情况**: 22 个错误码

**原因**: 计划编写时未精确统计 error_codes.py 中的实际定义数量

**处理**: 按照 error_codes.py 实际定义记录所有 22 个错误码,确保文档与代码完全一致

**影响**: 无负面影响,文档更完整准确

### 偏差 2: 任务合并执行

**情况**: Task 1 和 Task 2 同时完成(编辑同一文件的两个章节)

**原因**: 两个任务都是编辑 INTEGRATION.md,在单次编辑中完成效率更高

**处理**: 一次性完成两个章节的编写,单次提交

**影响**: 提高执行效率,减少提交次数

## 验证结果

### 自动化验证

✅ 所有必需章节存在:
```bash
grep -q "## 退出码参考" INTEGRATION.md  # 通过
grep -q "### 退出码分类" INTEGRATION.md  # 通过
grep -q "## 最佳实践" INTEGRATION.md    # 通过
grep -q "### 参数选择建议" INTEGRATION.md # 通过
grep -q "### 错误处理建议" INTEGRATION.md # 通过
grep -q "### 性能优化建议" INTEGRATION.md # 通过
```

✅ 所有错误码已记录(22 个):
```bash
# 验证所有错误码名称存在
AUTH_TOKEN_NOT_FOUND, AUTH_TOKEN_EXPIRED, AUTH_TOKEN_INVALID, AUTH_REFRESH_FAILED
API_NETWORK_ERROR, API_RATE_LIMIT, API_SERVER_ERROR, API_INVALID_RESPONSE
FILE_PERMISSION_ERROR, FILE_DISK_FULL, FILE_INVALID_PATH
DOWNLOAD_FAILED, DOWNLOAD_TIMEOUT, DOWNLOAD_PERMISSION_DENIED, DOWNLOAD_DISK_FULL
DOWNLOAD_FILE_EXISTS, DOWNLOAD_NETWORK_ERROR, RATE_LIMIT_EXCEEDED
METADATA_FETCH_FAILED, INVALID_ARGUMENT, INVALID_DATE_FORMAT, INTERNAL_ERROR
```

### 手动验证

✅ 文档格式规范,易于查阅
✅ 错误码分类清晰,表格格式整齐
✅ 代码示例完整,包含 Bash 和 Python 示例
✅ 最佳实践实用,基于实际使用场景
✅ DOCS-03 需求完全满足

## DOCS-03 需求满足情况

**需求描述**: 完整的退出码文档

**完成情况**:
- ✅ 包含所有 22 个错误码(超出预期的 20 个)
- ✅ 错误码名称与 error_codes.py 完全一致
- ✅ 分类清晰,便于查阅
- ✅ 提供使用示例
- ✅ 包含最佳实践指南
- ✅ 提供错误处理和性能优化建议

**需求状态**: 完全满足

## 输出产物

### 主要产物

**文件**: `INTEGRATION.md`

**新增章节**:
1. 退出码参考 (第 450-544 行)
   - 退出码分类(7 个类别,22 个错误码)
   - 退出码使用示例
   - 注意事项

2. 最佳实践 (第 546-828 行)
   - 参数选择建议
   - 错误处理建议
   - 性能优化建议
   - 集成测试建议
   - 文档和注释

**文档统计**:
- 新增行数: 377 行
- 错误码数量: 22 个
- 代码示例: 15+ 个

## 提交记录

**Commit**: 338114b
```
docs(09-03): add exit code reference and best practices

- Add complete exit code reference with 22 error codes
- Include error code categories: AUTH, API, FILE, DOWNLOAD, METADATA, INVALID, INTERNAL
- Provide bash and Python usage examples for exit codes
- Add best practices section covering parameter selection, error handling, and performance optimization
- Include retry strategies and integration testing guidelines
- Add documentation recommendations for third-party integrations
```

## 成功标准

- ✅ 退出码参考章节完整,包含所有 22 个错误码
- ✅ 最佳实践章节实用,包含代码示例
- ✅ DOCS-03 需求完全满足
- ✅ 文档格式规范,易于查阅
- ✅ 错误码名称与代码定义完全一致
- ✅ 提供实际可用的集成建议

## 后续工作

Phase 09-集成文档的所有计划已完成:
- ✅ 09-01: INTEGRATION.md 基础文档
- ✅ 09-02: 示例代码章节
- ✅ 09-03: 退出码参考和最佳实践

**下一步**:
- 继续 Phase 10: 发布准备
- 准备 v1.2 版本发布
- 完成 CHANGELOG.md 和版本标签

## 执行时间

- **开始时间**: 2026-02-26T07:10:02Z
- **结束时间**: 2026-02-26T07:12:54Z
- **总耗时**: 3 分钟
- **任务数**: 2 个(合并执行)
- **文件数**: 1 个(INTEGRATION.md)
