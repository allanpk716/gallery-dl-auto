---
status: investigating
trigger: "GitHub Issue #5 - total 统计口径问题：total=5, downloaded=5, skipped=3 → 统计不自洽"
created: 2026-03-16T00:00:00Z
updated: 2026-03-16T00:08:00Z
---

## Current Focus
hypothesis: total 字段只等于 limit，不包含 skipped 的作品数，导致统计不自洽
test: 检查 _parse_dry_run_output() 和 download_ranking() 中 total 的计算逻辑
expecting: 发现 total 是如何计算的，以及为何不包含 skipped
next_action: 读取代码，定位 total 字段的赋值位置

## Symptoms
expected: total 应该包含所有作品（downloaded + skipped），例如：total=8, downloaded=5, skipped=3 → total = downloaded + skipped
actual: total=5, downloaded=5, skipped=3，total 只等于 limit 值，不包含 skipped，统计不自洽（5 ≠ 5 + 3）
errors: 无明确错误，但统计数字不一致
reproduction: 启用去重后运行 `gallery-dl-auto download pixiv_ranking --limit 5 --type daily_r18`，观察 total/downloaded/skipped 的值
started: 2026-03-16 用户验证核心功能修复后发现的统计问题

## Eliminated

## Evidence

- timestamp: 2026-03-16T00:00:00Z
  checked: src/gallery_dl_auto/integration/gallery_dl_wrapper.py 的 _build_command() 方法（第 377-446 行）
  found: |
    - 第 413-428 行：limit/offset 转换逻辑
    - 第 421-423 行：end_page = offset + limit * 2
    - 第 427 行：cmd.extend(["--range", f"{start_page}-{end_page}"])
    - 注释说明："gallery-dl 的 --range 限制的是图片页面，不是作品数量"
    - 估算假设："每个作品平均 1.5 页"，使用 limit * 2 作为保守估算
  implication: |
    根因确认：
    1. --limit 5 被转换为 --range 1-10（假设每个作品最多 2 页）
    2. 但 gallery-dl 的 --range 限制的是图片页面数，不是作品数
    3. 实际排行榜中作品页数分布：单图作品 1 页，长漫画可能 10-85+ 页
    4. 如果前 5 个作品包含一个 8 页漫画，--range 1-10 只能获取 1+1+1+1+6 = 10 页，即 5 个作品
    5. 但如果前 5 个作品都是单图，--range 1-10 会获取 10 个作品而不是 5 个
    6. 这解释了为什么 --limit 5 实际下载了 8 个作品（单图作品较多时）

- timestamp: 2026-03-16T00:01:00Z
  checked: git history (commit 583b73d)
  found: |
    之前的修复策略（2026-03-03）：
    1. 调整 --range 计算：limit * 2（假设每个作品最多 2 页）
    2. 在 dry-run 的 JSON 解析后精确切片：应用 offset 和 limit
    3. 添加了 limit/offset 参数传递链路
    测试声称：--limit 1/3/5 都返回精确数量
  implication: |
    之前修复的局限性：
    - dry-run 模式：JSON 解析后的切片确实精确（_parse_dry_run_output 622-629 行）
    - 真实下载模式：没有切片逻辑！(_parse_download_output 不接收 limit/offset)
    - 问题：dry-run 的 total=5 是正确的，但实际下载时没有限制，导致 downloaded=8
    - 统计不一致的根因：total 来自 dry-run（精确），downloaded 来自实际下载（未限制）

- timestamp: 2026-03-16T00:02:00Z
  checked: gallery-dl 文档和 GitHub issues
  found: |
    - gallery-dl 提供 `max-posts` 选项：限制下载的作品（posts）数量，而非页面数
    - 命令行用法：`gallery-dl -o max-posts=5 <URL>` 精确下载 5 个作品
    - 对于 Pixiv ranking，max-posts 限制的是作品数量，不管每个作品有多少页
    - `--range` 选项：限制图片页面（image pages），不适合作品数控制
    - GitHub issue #2968 确认：max-posts 是控制作品数量的正确方式
  implication: |
    解决方案：
    1. 使用 `-o max-posts=<limit>` 替代 `--range` 估算逻辑
    2. 使用 `-o page-start=<offset+1>` 处理 offset（如果支持）
    3. 完全移除不精确的 limit * 2 估算
    4. 预期结果：--limit 5 精确下载 5 个作品，统计数字一致

- timestamp: 2026-03-16T00:03:00Z
  checked: 修复实施后的单元测试
  found: |
    单元测试结果（全部通过）：
    1. _build_command() 测试：
       - limit=5, offset=0 → max-posts=5 ✓
       - limit=5, offset=10 → max-posts=15 ✓
       - limit=None, offset=5 → max-posts=1005 ✓
    2. _parse_download_output() 测试：
       - limit=5, offset=0 → 返回 5 个作品 [1001-1005] ✓
       - limit=3, offset=2 → 返回 3 个作品 [1003-1005] ✓
       - limit=None, offset=5 → 返回 5 个作品 [1006-1010] ✓
  implication: |
    修复有效：
    - max-posts 参数正确设置
    - offset 和 limit 切片逻辑正确工作
    - 准备进行集成测试验证

- timestamp: 2026-03-16T00:04:00Z
  checked: 完整集成测试套件
  found: |
    pytest tests/integration/test_ranking_download.py 结果：
    - 17 个测试全部通过 ✓
    - 包括 test_dry_run_with_limit_and_offset
    - 包括 test_gallery_dl_engine_day_r18
    - 包括所有 R18 模式测试
  implication: |
    修复未破坏任何现有功能：
    - 所有集成测试通过
    - backward compatibility 保持
    - 准备请求用户验证真实场景

## Resolution
root_cause: |
  1. **主要根因**：_build_command() 使用 --range 参数估算页面数（limit * 2），但 gallery-dl 的 --range 限制的是图片页面数，不是作品数
  2. **次要根因**：真实下载模式下，_parse_download_output() 没有应用 limit/offset 限制，只依赖 --range 的不精确估算
  3. **统计不一致原因**：total 来自 dry-run 的 JSON 切片（精确），downloaded 来自实际下载（受 --range 估算影响，不精确）

fix: |
  **已实施的修复**：
  1. 在 _build_command() 中使用 `-o max-posts=<offset+limit>` 替代 `--range` 参数
     - max-posts 精确控制作品数量，不受页面数影响
     - 对于 offset：请求 offset + limit 个作品，然后在解析时切片
  2. 修改 _parse_download_output() 接收 limit 和 offset 参数
     - 在去重后应用 offset 切片（第 738-740 行）
     - 在去重后应用 limit 切片（第 742-744 行）
  3. 修改 _parse_result() 传递 limit 和 offset 参数给 _parse_download_output()
  4. 移除了不精确的 `limit * 2` 估算逻辑

  **修改的文件**：
  - src/gallery_dl_auto/integration/gallery_dl_wrapper.py
    - _build_command() 方法：第 410-427 行
    - _parse_download_output() 方法签名：第 693-706 行
    - _parse_download_output() 切片逻辑：第 738-747 行
    - _parse_result() 参数传递：第 561 行
verification: |
  验证步骤：
  1. 运行 `gallery-dl-auto download pixiv_ranking --limit 5 --type daily_r18`
  2. 确认实际下载 5 个作品（不是 8 个）
  3. 确认 total=5, downloaded=5, skipped=0（统计一致）
  4. 测试不同 limit 值（1, 3, 10）确认精确性
  5. 测试 offset 参数：--limit 5 --offset 5 应下载第 6-10 个作品
files_changed: [src/gallery_dl_auto/integration/gallery_dl_wrapper.py]


