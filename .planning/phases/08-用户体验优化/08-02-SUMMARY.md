# Plan 08-02: 日志模式切换与 429 错误处理

**Status**: ✅ Complete
**Execution Date**: 2026-02-25
**Duration**: ~20 minutes
**Commits**: 3

## Objective

优化日志系统以支持详细/静默模式,并实现 429 速率限制错误的检测和友好提示,让用户在详细模式下看到丰富的调试信息,在静默模式下保持安静,并在遇到速率限制时提供明确建议。

## What Was Built

### 1. setup_logging 支持 verbose 参数

**Files**: `src/gallery_dl_auo/utils/logging.py`, `src/gallery_dl_auo/config/paths.py`

扩展日志系统支持详细/静默模式:
- 在 paths.py 中添加 `get_log_file_path()` 函数,返回 `~/.gallery-dl-auto/logs/gallery-dl-auto.log`
- `setup_logging()` 添加 `verbose` 参数,控制控制台输出
- 详细模式(`verbose=True`):控制台输出 INFO+,文件 DEBUG+
- 静默模式(`verbose=False`):控制台无输出,文件 DEBUG+
- 文件日志始终启用(记录 DEBUG 级别)
- 使用 `logger.handlers.clear()` 避免重复日志

**日志文件路径**: `~/.gallery-dl-auto/logs/gallery-dl-auto.log`

**Tests**: 7 个测试用例
- 测试详细模式输出到控制台
- 测试静默模式无控制台输出
- 测试文件日志始终启用
- 测试重复初始化清除 handlers
- 测试日志级别正确设置
- 测试 StructuredFileHandler 写入 JSON Lines
- 测试自动创建日志目录

### 2. CLI 集成 verbose 日志配置

**Files**: `src/gallery_dl_auo/cli/main.py`, `src/gallery_dl_auo/cli/download_cmd.py`

在 CLI 中集成日志配置:
- main.py 使用 `setup_logging()` 函数配置日志系统
- 全局 `--verbose` 标志配置日志系统
- download_cmd.py 如果子命令 verbose 为 True,重新配置日志
- 优先级:子命令 `--verbose` > 全局 `--verbose`
- 确保详细模式下控制台输出 INFO 级别日志
- 移除手动配置 handlers 的代码,统一由 `setup_logging()` 管理

**配置优先级**: CLI 参数 > 配置文件 > 默认值

### 3. 429 速率限制错误检测

**Files**: `src/gallery_dl_auo/utils/error_codes.py`, `src/gallery_dl_auo/download/file_downloader.py`

实现 429 错误检测和友好提示:
- 添加 `RATE_LIMIT_EXCEEDED` 错误码到 error_codes.py
- 添加 `DOWNLOAD_NETWORK_ERROR` 错误码
- `download_file()` 检测 HTTP 429 状态码,返回专门的 `RATE_LIMIT_EXCEEDED` 错误
- 429 错误不触发重试(立即失败)
- 错误建议包含 `--image-delay` 和 `--batch-delay` 参数调整示例
- 其他 HTTP 错误(500, 404 等)仍然正常处理

**429 错误提示**:
```
建议增加延迟参数以避免触发反爬虫机制:
  --image-delay 5.0  (当前: 2.5s)
  --batch-delay 4.0  (当前: 2.0s)
```

**Tests**: 更新 429 错误测试用例
- 验证 429 错误返回 `RATE_LIMIT_EXCEEDED` 错误码
- 验证错误建议包含参数调整
- 验证其他 HTTP 错误仍然正常处理
- 验证成功下载不受影响

## Key Decisions

1. **文件日志始终启用**
   - 无论详细/静默模式,文件日志始终记录 DEBUG 级别
   - 便于事后调试和问题诊断

2. **控制台日志分级**
   - 详细模式:控制台输出 INFO 级别
   - 静默模式:控制台无输出
   - 保持默认模式的简洁性

3. **429 错误立即失败**
   - 不触发重试,避免加剧速率限制
   - 提供明确的参数调整建议
   - 包含当前值和建议值

4. **日志配置统一管理**
   - 使用 `setup_logging()` 函数统一管理日志配置
   - 避免在多处手动配置 handlers
   - 使用 `logger.handlers.clear()` 避免重复日志

## Deviations

无重大偏离。实现完全符合计划要求。

## Testing

**Unit Tests**: 7 个测试用例(test_main_logging.py)
- `test_verbose_mode_outputs_to_console`: 详细模式输出到控制台
- `test_silent_mode_no_console_output`: 静默模式无控制台输出
- `test_file_logging_always_enabled`: 文件日志始终启用
- `test_handlers_cleared_on_reinit`: 重复初始化清除 handlers
- `test_log_levels_correct`: 日志级别正确设置
- `test_writes_json_lines`: StructuredFileHandler 写入 JSON Lines
- `test_creates_log_directory`: 自动创建日志目录

**Integration Tests**: 1 个测试用例(test_file_downloader.py)
- `test_download_http_error_429`: 验证 429 错误检测和提示

**Manual Testing**: 建议测试
- 运行 `pixiv-downloader -v download --type daily` 验证详细模式日志
- 运行 `pixiv-downloader download --type daily` 验证静默模式
- 模拟 429 错误,验证错误提示格式

## Commits

1. **feat(08-02): 扩展 setup_logging 支持 verbose 参数**
   - 添加 get_log_file_path() 函数
   - setup_logging() 添加 verbose 参数
   - 详细模式:控制台 INFO+,文件 DEBUG+
   - 静默模式:控制台无输出,文件 DEBUG+
   - 7 个测试用例全部通过

2. **feat(08-02): 集成 verbose 日志配置到 CLI**
   - main.py 简化日志配置,使用 setup_logging()
   - download_cmd.py 重新配置日志(如果 verbose 改变)
   - 优先级:子命令 --verbose > 全局 --verbose

3. **feat(08-02): 实现 429 速率限制错误检测和提示**
   - 添加 RATE_LIMIT_EXCEEDED 错误码
   - download_file() 检测 429 状态码
   - 错误建议包含参数调整
   - 更新 429 错误测试用例

## Files Modified

- **Modified**: `src/gallery_dl_auo/utils/logging.py` (+30 lines)
- **Modified**: `src/gallery_dl_auo/config/paths.py` (+9 lines)
- **Created**: `tests/cli/test_main_logging.py` (160+ lines)
- **Modified**: `src/gallery_dl_auo/cli/main.py` (-33 lines, +11 lines)
- **Modified**: `src/gallery_dl_auo/cli/download_cmd.py` (+5 lines)
- **Modified**: `src/gallery_dl_auo/utils/error_codes.py` (+2 lines)
- **Modified**: `src/gallery_dl_auo/download/file_downloader.py` (+18 lines)
- **Modified**: `tests/download/test_file_downloader.py` (+4 lines)

## Next Steps

Phase 8 全部完成,项目已具备完整的用户体验优化功能:
- 详细模式实时进度显示
- 静默模式简洁安静
- CLI 参数灵活配置
- 429 错误友好提示

## Success Criteria Met

- [x] setup_logging() 支持 verbose 参数
- [x] 全局和子命令 --verbose 标志正常工作
- [x] 429 错误检测和友好提示实现
- [x] ErrorCode.RATE_LIMIT_EXCEEDED 定义
- [x] 详细模式:控制台 INFO,文件 DEBUG
- [x] 静默模式:控制台无输出,文件 DEBUG
- [x] 无重复日志输出
- [x] 429 错误立即失败,不重试
- [x] 错误建议包含具体参数调整示例
- [x] 错误记录到文件日志
- [x] 所有新代码有对应测试
- [x] 所有测试通过
- [x] 代码风格一致
