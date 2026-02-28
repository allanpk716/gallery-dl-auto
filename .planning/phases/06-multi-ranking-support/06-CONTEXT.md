# Phase 6: 多排行榜支持 - Context

**Gathered:** 2026-02-25
**Status:** Ready for planning

<domain>
## Phase Boundary

扩展下载器以支持 pixiv 的多种排行榜类型(周榜、月榜、R18 等),并处理月榜大规模数据集(1500+ 张)的 API 限制问题。支持历史排行榜下载和断点续传能力。

</domain>

<decisions>
## Implementation Decisions

### 排行榜类型选择方式
- 使用单命令 + `--type` 参数方式,格式:`pixiv-download download --type weekly --date 2026-02-18`
- `--type` 参数值使用完整单词(非缩写)
- 不支持同时下载多种类型,每次运行仅下载单一排行榜
- 无默认值,必须显式指定 `--type` 参数
- 用户输入无效类型时立即报错并退出,格式:`Invalid ranking type 'xyz'. Valid types: daily, weekly, monthly, ...`
- 支持全部 13 种排行榜类型:
  - 常规: `daily`, `weekly`, `monthly`
  - 分类: `day_male`, `day_female`, `week_original`, `week_rookie`, `day_manga`
  - R18: `day_r18`, `day_male_r18`, `day_female_r18`, `week_r18`, `week_r18g`

### 大规模数据集处理策略
- 用户可通过配置文件自定义下载参数:
  - `batch_size`: 每批次下载的作品数量(默认 30)
  - `batch_delay`: 批次间隔秒数(默认 2.0)
  - `concurrency`: 并发下载数(默认 1)
  - `image_delay`: 单张图片间隔秒数(默认 2.5)
- 进度显示: 静默模式,仅在完成时显示总结
- 自动跟随 `next_url` 持续下载,直到无更多数据,确保月榜完整下载

### 时间范围指定
- 支持历史排行榜下载,使用 `--date` 参数
- 日期格式: `YYYY-MM-DD`(仅支持此格式)
- 用户输入无效日期时立即报错并退出,格式:`Invalid date '2026-13-45'. Format: YYYY-MM-DD`
- 拒绝未来日期,立即报错,格式:`Date '2026-03-01' is in the future`

### 错误恢复行为
- 支持断点续传,记录已下载作品 ID
- 进度记录方式: 在下载目录内创建 `.progress.json` 文件
  - 示例: `./pixiv-downloads/weekly-2026-02-18/.progress.json`
  - 使用路径模板时也遵循此规则
- 单张图片下载失败时重试 3 次,间隔 5 秒
- 检测到未完成下载时自动继续,不询问用户
- 下载完成后自动删除 `.progress.json` 文件

### Claude's Discretion
- `.progress.json` 文件的具体格式和数据结构
- 批次间隔和图片间隔的默认值优化
- 重试间隔的具体实现
- 错误信息的详细程度

</decisions>

<specifics>
## Specific Ideas

- "我希望支持 R18 的排行榜,包括所有类型(day_r18, day_male_r18, day_female_r18, week_r18, week_r18g)"
- 进度文件跟随下载目录,便于管理
- 自动继续未完成的下载,减少用户干预

</specifics>

<deferred>
## Deferred Ideas

None — discussion stayed within phase scope

</deferred>

---

*Phase: 06-multi-ranking-support*
*Context gathered: 2026-02-25*
