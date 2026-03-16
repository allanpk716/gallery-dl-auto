---
status: resolved
trigger: "Issue #3: success_list 包含重复 ID — 多页作品的每个页面都被独立计入"
created: 2026-03-16T00:00:00Z
updated: 2026-03-16T00:00:00Z
---

## Current Focus

hypothesis: _parse_download_output 方法没有去重逻辑，每个下载的文件路径都会被解析并添加作品 ID，多页作品会有多个文件路径（{id}_p0, {id}_p1, {id}_p2）
test: 检查 _parse_download_output 方法的去重逻辑
expecting: 确认该方法没有去重，并且这是问题的根本原因
next_action: 设计修复方案并实现

## Evidence

- timestamp: 初始调查
  checked: 读取 gallery_dl_wrapper.py, ranking_downloader.py, output.py
  found: 在 _parse_download_output 方法（行 693-742）中，解析下载输出时，每行文件路径都会提取作品 ID 并添加到 success_list，没有去重逻辑
  implication: 多页作品（如 3 页）会生成 3 个文件（{id}_p0, {id}_p1, {id}_p2），每个文件路径被解析后会添加同一个作品 ID 3 次

- timestamp: 对比分析
  checked: 比较 _parse_dry_run_output 和 _parse_download_output
  found: _parse_dry_run_output 方法（行 564-691）有去重逻辑（行 611-620），使用 seen_ids 集合；但 _parse_download_output 没有类似逻辑
  implication: 问题仅在实际下载时出现，dry-run 模式是正确的

## Symptoms

expected: success_list 应该包含唯一的作品 ID，每个作品只计入一次，即使作品有多个页面
actual: 多页作品（如包含 3 张图片的作品）的每个页面都被独立计入 success_list，导致同一作品 ID 出现多次
errors: 没有错误消息，但统计数字不准确，影响用户体验
reproduction: 下载包含多页作品的排行榜（如 daily 排行榜），观察 success_list 内容
started: 最近使用时发现，这个问题是其他 issues (#4 和 #5) 的根本原因

## Eliminated

## Evidence

## Resolution

root_cause: _parse_download_output 方法（gallery_dl_wrapper.py:693-742）在解析下载输出时，对每个下载的文件路径都提取作品 ID 并添加到 success_list，没有去重逻辑。多页作品会生成多个文件路径（{id}_p0, {id}_p1, {id}_p2），导致同一个作品 ID 被添加多次。
fix: 在 _parse_download_output 方法中添加去重逻辑，使用 seen_ids 集合，确保每个作品 ID 只添加一次（与 _parse_dry_run_output 保持一致）
verification:
  - 创建了 4 个新测试用例验证去重逻辑（test_parse_download_output_dedup.py）
  - 所有新测试通过（test_parse_download_output_dedup_multi_page_artwork, test_parse_download_output_single_page_artwork, test_parse_download_output_empty_output, test_parse_download_output_mixed_page_counts）
  - 现有集成测试全部通过（test_gallery_dl_wrapper_dedup.py，8/8 passed）
files_changed: [src/gallery_dl_auto/integration/gallery_dl_wrapper.py, tests/integration/test_parse_download_output_dedup.py]
