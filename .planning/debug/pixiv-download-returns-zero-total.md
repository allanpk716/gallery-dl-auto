---
status: awaiting_human_verify
trigger: "执行 `pixiv-downloader download --type day_male_r18` 命令后立即返回，显示 total=0，没有下载任何作品"
created: 2026-03-01T00:00:00Z
updated: 2026-03-01T05:58:00Z
---

## Current Focus
hypothesis: 修复已完成并验证
test: 运行原始用户命令进行验证
expecting: total > 0，能正常开始下载
next_action: 等待用户确认

## Symptoms
expected: 应该找到并下载多个作品，total > 0，显示下载进度
actual: 立即返回 JSON 结果，total=0, downloaded=0, failed=0, skipped=0
errors: 没有看到任何错误消息或警告
reproduction: 执行 `pixiv-downloader download --type day_male_r18`
started: 首次运行此命令

## Eliminated
- hypothesis: API 认证问题
  evidence: API 认证成功，使用 pixivpy3 直接调用时能正常返回数据
  timestamp: 2026-03-01T05:48:00Z

- hypothesis: API 客户端代码错误
  evidence: 独立测试 PixivClient 类时能正常返回 259 个作品
  timestamp: 2026-03-01T05:49:00Z

## Evidence
- timestamp: 2026-03-01T05:47:00Z
  checked: CLI 命令详细日志输出
  found: API 返回 {'illusts': [], 'next_url': None}
  implication: API 层面返回了空数据

- timestamp: 2026-03-01T05:48:00Z
  checked: 直接使用 pixivpy3 调用 API
  found: day_male_r18 排行榜有 27 个作品
  implication: API 本身能正常返回数据，问题在我们的代码中

- timestamp: 2026-03-01T05:49:00Z
  checked: 测试 PixivClient 类
  found: get_ranking_all() 返回 259 个作品
  implication: PixivClient 工作正常

- timestamp: 2026-03-01T05:50:00Z
  checked: 日志中的请求参数
  found: date='2026-03-01'（今天）被显式传递给 API
  implication: 今天的排行榜还未生成

- timestamp: 2026-03-01T05:51:00Z
  checked: 测试不同日期参数
  found: date='2026-03-01' 返回 0 个作品，date=None 返回 259 个作品，date='2026-02-28' 返回 259 个作品
  implication: 当 date 为 None 时，API 自动使用最新可用的排行榜（昨天），当显式传递今天日期时返回空列表

- timestamp: 2026-03-01T05:56:00Z
  checked: 修复后的命令执行（daily）
  found: Fetched 499 works from 18 pages，开始下载流程
  implication: 修复成功，API 能正常返回数据

- timestamp: 2026-03-01T05:57:00Z
  checked: 修复后的命令执行（day_male_r18 - 原始命令）
  found: Fetched 259 works from 11 pages，开始下载流程
  implication: 原始问题已解决，total 不再是 0

## Resolution
root_cause: ranking_downloader.py 将 None 转换为今天的日期（2026-03-01），导致请求一个还未生成的排行榜。Pixiv 排行榜通常是前一天的，今天的排行榜还未生成。
fix: 修改日期处理逻辑，当用户未指定 date 时，不传递给 API（传递 None），让 API 使用默认值（最新可用排行榜）。对于需要日期字符串的地方（如断点续传、输出目录），使用昨天的日期作为默认值。
verification:
  - 运行 `pixiv-downloader download --type daily --verbose`，成功获取 499 个作品
  - 运行 `pixiv-downloader download --type day_male_r18 --verbose`（原始命令），成功获取 259 个作品
files_changed:
  - src/gallery_dl_auto/download/ranking_downloader.py
  - src/gallery_dl_auto/utils/logging.py (恢复配置)
