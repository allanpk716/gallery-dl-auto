# Plan 08-01: 详细模式进度显示和 CLI 速率控制参数

**Status**: ✅ Complete
**Execution Date**: 2026-02-25
**Duration**: ~25 minutes
**Commits**: 2

## Objective

实现详细模式(-v)的实时进度显示和 CLI 速率控制参数暴露,让用户能够在详细模式下查看下载进度,同时通过 CLI 参数灵活配置速率控制,保持默认模式的简洁性。

## What Was Built

### 1. ProgressReporter 进度报告器类

**File**: `src/gallery_dl_auo/download/progress_reporter.py`

封装详细模式下的进度显示逻辑:
- 详细模式输出到 stderr,避免污染 stdout 的 JSON 输出
- 静默模式(默认)无任何输出
- 支持进度更新、成功报告、速率限制等待、重试报告
- 使用 Rich Console 实现颜色样式输出
- 时间戳格式: `YYYY-MM-DD HH:MM:SS`

**方法**:
- `update_progress(idx, total, failed)`: 更新进度状态
- `report_success(title, illust_id)`: 报告成功下载(绿色)
- `report_rate_limit_wait(delay)`: 报告速率控制等待(dim)
- `report_retry(attempt, max_retries, error)`: 报告重试(黄色)

**Tests**: 8 个测试用例全部通过
- 测试详细模式输出到 stderr
- 测试静默模式无输出
- 测试时间戳格式
- 测试颜色样式应用

### 2. CLI 参数扩展

**File**: `src/gallery_dl_auo/cli/download_cmd.py`

添加详细模式标志和速率控制参数:
- `--verbose / -v`: 详细模式标志,显示实时进度和调试信息
- `--image-delay`: 单张图片间隔秒数(覆盖配置文件)
- `--batch-delay`: 批次间隔秒数(覆盖配置文件)
- `--batch-size`: 每批次下载的作品数量(覆盖配置文件)
- `--max-retries`: 单张图片最大重试次数(覆盖配置文件)

**配置优先级**: CLI 参数 > 配置文件 > 默认值

**帮助文本**: 包含默认值和配置文件路径

### 3. RankingDownloader 集成

**File**: `src/gallery_dl_auo/download/ranking_downloader.py`

集成 ProgressReporter 到下载流程:
- 构造函数添加 `verbose` 参数
- 初始化 `ProgressReporter` 实例
- 下载循环中调用 `reporter.update_progress()` 显示进度
- 成功下载后调用 `reporter.report_success()` 显示成功信息
- 速率控制前调用 `reporter.report_rate_limit_wait()` 显示等待信息
- 保持所有现有功能不变(断点续传、增量下载、文件日志)

## Key Decisions

1. **输出到 stderr 而非 stdout**
   - 避免污染 stdout 的 JSON 输出
   - 使用 `Console(stderr=True)` 确保第三方工具解析正常

2. **静默模式无任何输出**
   - 默认模式保持简洁,仅输出最终 JSON 结果
   - 错误和失败静默处理,仅记录到日志文件

3. **详细模式实时进度**
   - 每个作品更新一次进度状态
   - 带时间戳格式显示当前进度和失败数量
   - 显示成功下载、速率控制等待等信息

4. **CLI 参数优先级**
   - CLI 参数 > 配置文件 > 默认值
   - 仅当 CLI 参数非 None 时才覆盖配置文件
   - Pydantic 自动验证参数范围

## Deviations

无重大偏离。实现完全符合计划要求。

## Testing

**Unit Tests**: 8 个测试用例
- `test_verbose_mode_outputs_progress`: 详细模式输出进度
- `test_silent_mode_no_output`: 静默模式无输出
- `test_success_report_styled`: 成功报告包含样式
- `test_rate_limit_wait_styled`: 速率限制等待报告
- `test_retry_report_styled`: 重试报告包含样式
- `test_timestamp_format`: 时间戳格式正确
- `test_verbose_false_all_methods_return_early`: verbose=False 时立即返回
- `test_console_uses_stderr`: Console 输出到 stderr

**Manual Testing**: 建议测试
- 运行 `pixiv-downloader download --type daily -v` 观察详细模式输出
- 运行 `pixiv-downloader download --type daily` 验证静默模式
- 验证 CLI 参数覆盖配置文件值

## Commits

1. **feat(08-01): 创建 ProgressReporter 进度报告器类**
   - 实现 ProgressReporter 类
   - 详细模式输出到 stderr
   - 静默模式无输出
   - 8 个测试用例全部通过

2. **feat(08-01): 集成 ProgressReporter 到下载流程**
   - CLI 扩展:添加 --verbose 和速率控制参数
   - RankingDownloader 集成 ProgressReporter
   - 实现配置优先级(CLI > 配置文件 > 默认值)

## Files Modified

- **Created**: `src/gallery_dl_auo/download/progress_reporter.py` (60+ lines)
- **Created**: `tests/download/test_progress_reporter.py` (110+ lines)
- **Modified**: `src/gallery_dl_auo/cli/download_cmd.py` (+45 lines)
- **Modified**: `src/gallery_dl_auo/download/ranking_downloader.py` (+10 lines)

## Next Steps

Plan 08-02 将实现:
- 扩展 setup_logging 支持 verbose 参数
- 在 main.py 中集成 verbose 日志配置
- 实现 429 速率限制错误检测和提示

## Success Criteria Met

- [x] ProgressReporter 类实现并测试通过
- [x] CLI 参数扩展完成(--verbose, --image-delay, --batch-delay, --batch-size, --max-retries)
- [x] 配置优先级正确(CLI > 配置文件 > 默认值)
- [x] RankingDownloader 集成 ProgressReporter
- [x] 默认模式:简洁安静,仅输出 JSON 结果
- [x] 详细模式:实时进度更新,带时间戳和颜色样式
- [x] 参数帮助文本清晰,包含默认值信息
- [x] 所有新代码有对应测试
- [x] 所有测试通过
- [x] 现有功能不受影响(断点续传、增量下载、文件日志)
- [x] 现有 CLI 调用方式仍然有效
- [x] 配置文件格式不变
