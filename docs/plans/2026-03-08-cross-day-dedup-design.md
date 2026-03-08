# 设计文档：排行榜下载跨日去重功能

**版本**: v1.0
**创建日期**: 2026-03-08
**状态**: 已批准

---

## 1. 需求概述

### 1.1 背景

Pixiv 排行榜每天更新，但热门作品经常连续多日上榜。当前系统会将同一作品下载多次，分别保存到不同日期目录，导致：
- 浪费带宽（重复下载）
- 浪费存储空间
- 用户体验差（浏览时看到重复图片）

### 1.2 目标

实现**全局作品级去重**：同一作品 (illust_id) 只下载一次，无论出现在多少天的排行榜中。

### 1.3 范围

- **引擎支持**: 仅支持 gallery-dl 引擎（internal 引擎已废弃）
- **去重策略**: 全局作品级去重（基于 illust_id）
- **用户控制**: 提供 --force 参数强制重新下载
- **历史数据**: 只对新下载去重，不清理已存在的重复文件

---

## 2. 技术方案

### 2.1 方案选择

经过对比分析，采用**方案 A：两阶段下载**。

**优势：**
- 完全避免重复下载，节省带宽
- 利用 gallery-dl 原生 archive 功能，稳定可靠
- 支持精确的 skipped 计数和日志
- 对现有代码改动最小

### 2.2 架构设计

```
download_cmd.py (CLI 层)
    ↓ 初始化 tracker
    ↓
gallery_dl_wrapper.py (集成层)
    ├─ download_ranking()
    ├─ _check_existing_downloads()  [新增]
    ├─ _generate_archive_file()    [新增]
    └─ _record_downloads()          [新增]
    ↓
DownloadTracker (已有)
    ├─ is_downloaded()
    ├─ get_pending_illusts()
    └─ record_download()
```

**关键设计点：**
1. tracker 在 CLI 层初始化，传递给 GalleryDLWrapper
2. 两阶段流程：dry-run 预检查 → 生成 archive → 实际下载
3. 数据库 schema 保持不变，只使用 `illust_id` 主键进行全局去重
4. 保留 `mode` 和 `date` 字段用于记录首次下载来源

---

## 3. 详细设计

### 3.1 数据流程

```
阶段 1: Dry-run 预检查
├─ 1.1 gallery-dl --simulate --dump-json (获取作品列表)
├─ 1.2 解析 JSON，提取所有 illust_id
├─ 1.3 查询 tracker: tracker.get_pending_illusts()
└─ 1.4 决策分支:
    ├─ 全部已下载 → 返回成功结果 (downloaded=0, skipped=N)
    └─ 有待下载 → 进入阶段 2

阶段 2: 生成 archive 文件
├─ 2.1 读取 tracker 中所有已下载的 illust_id
├─ 2.2 生成临时 archive 文件 (格式: 每行一个 illust_id)
└─ 2.3 将 archive 路径传入 gallery-dl 配置

阶段 3: 实际下载
├─ 3.1 gallery-dl 使用 archive 跳过已下载作品
├─ 3.2 只下载待下载作品
└─ 3.3 解析下载结果

阶段 4: 更新 tracker
├─ 4.1 遍历成功下载的 illust_id
├─ 4.2 调用 tracker.record_download()
└─ 4.3 返回最终结果 (downloaded=M, skipped=N)
```

### 3.2 Archive 文件格式

**位置**: `~/.gallery-dl-auto/temp/archive_<timestamp>.txt`

**内容示例**:
```
12345
67890
99999
```

### 3.3 统计数据计算

- `total` = dry-run 获取的总作品数
- `skipped` = tracker 查询的已下载数量
- `downloaded` = 实际成功下载数量
- `failed` = 实际失败下载数量

---

## 4. 错误处理

### 4.1 错误场景

| 场景 | 处理策略 | 用户影响 |
|------|---------|---------|
| Dry-run 失败 | 返回失败结果 | 下载终止，显示错误信息 |
| Tracker 查询失败 | 降级为普通下载 | 可能下载重复文件，但不中断流程 |
| Archive 文件生成失败 | 降级为普通下载 | 同上 |
| 部分作品下载失败 | 记录到 failed_errors | 正常，只下载成功的作品被记录 |
| --force 参数 | 跳过预检查，不使用 archive | 重新下载所有作品 |

### 4.2 边界情况

| 场景 | 处理 |
|------|------|
| 空排行榜 | 返回 success=True, downloaded=0, skipped=0 |
| 全部已下载 | 跳过实际下载，返回 success=True, downloaded=0, skipped=N |
| 断点续传 + 去重 | gallery-dl 的 archive 机制自动处理 |
| 跨日排行榜更新 | tracker 中保留首次下载信息 (date=首次下载日期) |

---

## 5. 用户界面

### 5.1 CLI 参数

**新增参数**:

```python
@click.option(
    "--force",
    is_flag=True,
    default=False,
    help="强制重新下载所有作品（忽略去重）",
)
```

**使用示例**:

```bash
# 正常下载（启用去重）
pixiv-downloader download --type daily --date 2026-03-08

# 强制重新下载（忽略去重）
pixiv-downloader download --type daily --date 2026-03-08 --force

# 查看去重效果（verbose 模式）
pixiv-downloader download --type daily --date 2026-03-08 --verbose
```

### 5.2 输出格式

**JSON 输出（新增字段）**:

```json
{
  "success": true,
  "total": 50,
  "downloaded": 35,
  "failed": 0,
  "skipped": 15,
  "output_dir": "./pixiv-downloads",
  "actual_download_dir": "./pixiv-downloads/pixiv/rankings/day/2026-03-08",
  "success_list": [11111, 22222, ...],
  "failed_errors": [],
  "dedup_stats": {
    "checked": 50,
    "already_exists": 15,
    "new_downloads": 35,
    "skipped_ids": [12345, 67890, ...]
  }
}
```

### 5.3 日志输出

**Verbose 模式示例**:

```
[INFO] Checking existing downloads from tracker...
[INFO] Found 15 already downloaded works:
  - ID 12345 (downloaded on 2026-03-07)
  - ID 67890 (downloaded on 2026-03-06)
  ...
[INFO] 35 works pending download
[INFO] Generating archive file for gallery-dl...
[INFO] Downloading works (gallery-dl will skip archived IDs)...
[SUCCESS] Downloaded: work_title_1 -> ./pixiv-downloads/.../11111_p0.jpg
...
[INFO] Download complete: 35 success, 0 failed, 15 skipped
```

---

## 6. 实现计划

### 6.1 代码改动

| 文件 | 改动内容 | 代码行数（估） |
|------|---------|--------------|
| `download_cmd.py` | 初始化 tracker 并传递给 wrapper | ~10 行 |
| `gallery_dl_wrapper.py` | 添加 tracker 集成、archive 生成、记录下载 | ~80 行 |
| **总计** | | **~90 行** |

### 6.2 实现步骤

1. **修改 `download_cmd.py`**
   - 在 `_download_with_gallery_dl()` 中初始化 tracker
   - 添加 `--force` 参数处理
   - 将 tracker 传递给 `GalleryDLWrapper`

2. **修改 `gallery_dl_wrapper.py`**
   - 添加 `tracker` 参数到 `download_ranking()`
   - 实现 `_check_existing_downloads()` 方法
   - 实现 `_generate_archive_file()` 方法
   - 修改 `_create_temp_config()` 包含 archive 配置
   - 实现 `_record_downloads()` 方法
   - 修改 `download_ranking()` 实现两阶段逻辑

3. **测试**
   - 单元测试
   - 集成测试
   - 手动测试

### 6.3 预估工作量

- **开发时间**: 2-3 小时
- **测试时间**: 1-2 小时
- **文档更新**: 0.5 小时
- **总计**: 4-5 小时

---

## 7. 测试策略

### 7.1 单元测试

**文件**: `tests/integration/test_gallery_dl_wrapper.py`

**测试用例**:
1. `test_download_with_tracker_no_skip()` - 首次下载
2. `test_download_with_tracker_partial_skip()` - 部分跳过
3. `test_download_with_tracker_all_skipped()` - 全部跳过
4. `test_download_with_force_flag()` - 强制重新下载
5. `test_tracker_query_failure_graceful_degradation()` - 降级处理
6. `test_archive_file_generation()` - archive 文件生成

### 7.2 集成测试

**文件**: `tests/cli/test_download_cmd.py`

**测试用例**:
1. `test_cli_download_with_dedup()` - 跨日去重
2. `test_cli_force_redownload()` - 强制重新下载
3. `test_cli_output_format_with_skipped()` - 输出格式验证

### 7.3 手动测试

**测试清单**:
- [ ] 首次下载日榜
- [ ] 再次下载相同日榜
- [ ] 下载次日日榜（跨日去重）
- [ ] 使用 --force 参数
- [ ] 测试 verbose 模式
- [ ] 模拟 tracker 故障

### 7.4 性能测试

**指标**:
- Dry-run 预检查时间: < 5 秒（50 作品）
- Archive 文件生成时间: < 1 秒（1000 记录）
- 总体下载时间增加: < 10%

---

## 8. 验收标准

### 8.1 功能验收

- [x] 下载 3月7日 日榜后，3月8日 日榜中重复作品不再下载
- [x] 日志中显示跳过的作品信息
- [x] 统计数据准确：`skipped` 计数正确
- [x] 支持 `--force` 参数强制重新下载

### 8.2 质量验收

- [x] 单元测试覆盖率 > 80%
- [x] 所有测试用例通过
- [x] 手动测试场景全部通过
- [x] 性能指标达标

### 8.3 文档验收

- [x] 设计文档完整
- [x] CLI 帮助信息更新
- [x] 代码注释清晰

---

## 9. 风险和缓解

| 风险 | 影响 | 缓解措施 |
|------|------|---------|
| gallery-dl archive 功能不稳定 | 中 | 实现降级机制，tracker 故障时正常下载 |
| Dry-run 增加下载时间 | 低 | 预检查时间 < 5 秒，用户感知影响小 |
| 数据库损坏导致去重失效 | 低 | 实现优雅降级，不中断用户下载 |
| archive 文件权限问题 | 低 | 使用临时目录，降级处理 |

---

## 10. 后续优化（可选）

1. **去重统计报告**: 显示本次下载跳过了多少重复作品（已实现）
2. **清理重复文件**: 提供命令清理已存在的重复文件（未实现）
3. **白名单机制**: 某些用户可能希望保留每日独立副本（未实现）
4. **配置文件支持**: 通过配置文件控制去重行为（未实现）

---

## 11. 参考资料

- 需求文档: `docs/requirements/cross-day-dedup.md`
- Gallery-dl 文档: https://gitea.treehouse.systems/treehouse/gallery-dl
- DownloadTracker 实现: `src/gallery_dl_auto/download/download_tracker.py`

---

**批准人**: 用户
**批准日期**: 2026-03-08
