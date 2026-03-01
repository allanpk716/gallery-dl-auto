"""排行榜下载编排器

编排排行榜下载流程,整合 API、下载、速率控制和文件管理。
"""

import datetime
import logging
from pathlib import Path

from gallery_dl_auto.api.pixiv_client import PixivAPIError, PixivClient
from gallery_dl_auto.config.download_config import DownloadConfig
from gallery_dl_auto.download.download_tracker import DownloadTracker
from gallery_dl_auto.download.file_downloader import download_file
from gallery_dl_auto.download.progress_manager import DownloadProgress
from gallery_dl_auto.download.progress_reporter import ProgressReporter
from gallery_dl_auto.download.rate_limiter import rate_limit_delay
from gallery_dl_auto.download.resume_manager import ResumeManager
from gallery_dl_auto.download.retry_handler import retry_download_file
from gallery_dl_auto.models.artwork import ArtworkMetadata
from gallery_dl_auto.models.error_response import BatchDownloadResult, StructuredError
from gallery_dl_auto.utils.filename_sanitizer import sanitize_filename
from gallery_dl_auto.utils.path_template import PathTemplate

logger = logging.getLogger("gallery_dl_auto")


class RankingDownloader:
    """排行榜下载编排器

    整合 API、下载、速率控制和文件管理,实现完整的排行榜下载流程.
    """

    def __init__(
        self,
        client: PixivClient,
        output_dir: Path,
        config: DownloadConfig | None = None,
        verbose: bool = False,
        output_mode: str = "normal"
    ) -> None:
        """初始化排行榜下载器

        Args:
            client: Pixiv API 客户端
            output_dir: 输出目录 (默认 ./pixiv-downloads/)
            config: 下载配置 (可选,使用默认配置)
            verbose: 是否启用详细模式 (默认 False)
            output_mode: 输出模式 (normal, json, quiet, 默认 normal)
        """
        self.client = client
        self.output_dir = output_dir
        self.config = config or DownloadConfig()
        self.verbose = verbose
        self.output_mode = output_mode

    def download_ranking(
        self,
        mode: str = "day",
        date: str | None = None,
        path_template: str | None = None,
        enable_resume: bool = True,
        tracker: DownloadTracker | None = None,
        limit: int | None = None,
        offset: int = 0,
    ) -> BatchDownloadResult:
        """下载指定排行榜的所有图片(支持断点续传和范围控制)

        Args:
            mode: 排行榜类型 (day, week, month 等)
            date: 日期字符串 YYYY-MM-DD (默认今天)
            path_template: 路径模板字符串 (可选)
            enable_resume: 是否启用断点续传 (默认 True)
            tracker: 下载历史追踪器 (可选,用于增量下载)
            limit: 最多下载的作品数 (None = 无限制)
            offset: 跳过的作品数 (默认 0)

        Returns:
            BatchDownloadResult: 批量下载结果

        Note:
            下载参数 (batch_delay, image_delay, max_retries, retry_delay)
            从 self.config 读取

            当使用 limit 或 offset 时,断点续传会自动禁用,因为:
            - 分批下载的本质是手动控制范围
            - offset 与断点续传的 start_index 会产生逻辑冲突
            - 用户可以通过调整 offset 手动实现"断点续传"效果
        """
        # 1. 获取排行榜数据(使用 get_ranking_range 支持范围控制)
        # 注意: 如果用户未指定日期，不传递 date 参数，让 API 使用默认值（最新可用排行榜）
        # Pixiv 排行榜通常是前一天的，今天的排行榜可能还未生成

        # 如果指定了范围,禁用断点续传
        if limit is not None or offset > 0:
            enable_resume = False
            logger.info(f"分批下载模式: limit={limit}, offset={offset}, 断点续传已禁用")

        try:
            # 对于日志和断点续传，使用实际请求的日期（如果有）
            display_date = date if date else "latest"
            logger.info(f"Fetching ranking: mode={mode}, date={display_date}, limit={limit}, offset={offset}")

            # 使用 get_ranking_range 支持范围控制
            ranking_data = self.client.get_ranking_range(
                mode=mode, date=date, limit=limit, offset=offset
            )

            # 获取数据后，如果 date 为 None，使用获取到的第一个作品的日期作为实际日期
            # 如果没有获取到数据，使用昨天的日期作为默认值
            actual_date = date
            if actual_date is None:
                if ranking_data and len(ranking_data) > 0:
                    # 尝试从第一个作品推断日期（但 API 响应中可能没有日期信息）
                    # 使用昨天的日期作为最佳猜测
                    import datetime
                    actual_date = (datetime.date.today() - datetime.timedelta(days=1)).strftime("%Y-%m-%d")
                else:
                    # 没有数据时，使用昨天的日期
                    import datetime
                    actual_date = (datetime.date.today() - datetime.timedelta(days=1)).strftime("%Y-%m-%d")
        except PixivAPIError as e:
            logger.error(f"API error: {e}")
            # 返回失败结果
            return BatchDownloadResult(
                success=False,
                total=0,
                downloaded=0,
                failed=0,
                skipped=0,
                success_list=[],
                failed_errors=[
                    StructuredError(
                        error_code="API_SERVER_ERROR",
                        error_type="PixivAPIError",
                        message=f"API 错误: {e}",
                        suggestion="检查网络连接或稍后重试",
                        severity="error",
                        original_error=str(e),
                    )
                ],
                output_dir=str(self.output_dir),
            )

        # 2. 初始化断点续传管理器
        resume_manager = ResumeManager(self.output_dir, mode, actual_date)

        # 检查是否需要从断点恢复
        start_index = 0
        if enable_resume and resume_manager.should_resume():
            logger.info(
                f"从断点恢复: 已下载 {resume_manager.state.downloaded_count}/"
                f"{resume_manager.state.total_count}, 从索引 {resume_manager.get_resume_index()} 继续"
            )
            start_index = resume_manager.get_resume_index()

        # 3. 初始化路径模板
        template = PathTemplate(path_template) if path_template else None

        # 4. 创建输出目录
        if not template:
            ranking_dir = self.output_dir / f"{mode}-{actual_date}"
            ranking_dir.mkdir(parents=True, exist_ok=True)
            logger.info(f"Output directory: {ranking_dir}")
        else:
            logger.info(f"Using path template: {path_template}")

        # 5. 使用 SQLite tracker 过滤已下载作品(优先)
        if tracker:
            all_illust_ids = [illust['id'] for illust in ranking_data]
            pending_ids = set(tracker.get_pending_illusts(mode, actual_date, all_illust_ids))
            logger.info(
                f"Incremental download: {len(pending_ids)}/{len(ranking_data)} pending "
                f"(skipping {len(ranking_data) - len(pending_ids)} already downloaded)"
            )
        else:
            # 没有 tracker,下载所有作品
            pending_ids = None

        # 6. 遍历排行榜(从断点位置开始)
        success_list: list[int] = []
        failed_errors: list[StructuredError] = []
        skipped = 0
        total_count = len(ranking_data)

        # 更新总数
        resume_manager.state.total_count = total_count

        # 初始化进度报告器 (根据 output_mode 控制输出)
        reporter = ProgressReporter(verbose=self.verbose, output_mode=self.output_mode)

        for idx, illust in enumerate(ranking_data[start_index:], start=start_index):
            illust_id = illust['id']

            # 更新进度(详细模式)
            reporter.update_progress(idx + 1, total_count, len(failed_errors))

            # 使用 SQLite tracker 检查(优先)
            if tracker and illust_id not in pending_ids:
                logger.debug(f"Skipping already downloaded (SQLite): {illust_id}")
                skipped += 1
                continue

            # 获取元数据
            metadata = self._fetch_metadata_safe(illust_id)

            # 构建文件路径
            filepath = self._build_filepath(
                illust, metadata, template, mode, actual_date, ranking_dir if not template else None
            )

            logger.info(f"Downloading: {illust['title']} (ID: {illust_id})")

            # 下载图片(带重试)
            result = download_file(illust["image_url"], filepath, illust_id)

            # 记录结果
            if isinstance(result, dict) and result.get("success"):
                success_list.append(illust_id)
                logger.debug(f"Successfully downloaded: {filepath}")

                # 报告成功下载(详细模式)
                title = metadata.title if metadata else illust['title']
                reporter.report_success(title, illust_id)

                # 记录到 SQLite tracker
                if tracker:
                    file_size = result.get("size") or (filepath.stat().st_size if filepath.exists() else None)
                    tracker.record_download(
                        illust_id=illust_id,
                        file_path=filepath,
                        mode=mode,
                        date=actual_date,
                        file_size=file_size
                    )
            else:
                # result 应该是 StructuredError
                if isinstance(result, StructuredError):
                    failed_errors.append(result)
                else:
                    # 兼容旧的错误格式(不应该发生)
                    logger.warning(f"Unexpected error format: {result}")
                    from gallery_dl_auto.models.error_response import ErrorSeverity
                    failed_errors.append(
                        StructuredError(
                            error_code="INTERNAL_ERROR",
                            error_type="InternalError",
                            message=f"下载失败:作品 {illust_id}",
                            suggestion="未知错误",
                            severity=ErrorSeverity.ERROR,
                            illust_id=illust_id,
                            original_error=str(result),
                        )
                    )

            # 每 10 个作品保存一次断点状态
            if enable_resume and (idx + 1) % 10 == 0:
                resume_manager.update(
                    index=idx + 1,
                    downloaded=len(success_list),
                    failed=len(failed_errors),
                    last_illust_id=illust_id
                )
                resume_manager.save()

            # 速率控制
            reporter.report_rate_limit_wait(self.config.image_delay)
            rate_limit_delay(self.config.image_delay, jitter=1.0)

        # 7. 下载完成,清除断点状态文件
        if enable_resume:
            resume_manager.clear()
            logger.info("Download complete, resume state cleared")

        logger.info(
            f"Download complete: {len(success_list)} success, {len(failed_errors)} failed, {skipped} skipped"
        )

        # 8. 返回批量下载结果
        return BatchDownloadResult(
            success=len(failed_errors) == 0,
            total=len(ranking_data),
            downloaded=len(success_list),
            failed=len(failed_errors),
            skipped=skipped,
            success_list=success_list,
            failed_errors=failed_errors,
            output_dir=str(self.output_dir),
        )

    def _fetch_metadata_safe(self, illust_id: int) -> ArtworkMetadata | None:
        """安全获取元数据(失败时返回 None)

        Args:
            illust_id: 作品 ID

        Returns:
            ArtworkMetadata 或 None
        """
        try:
            metadata = self.client.get_artwork_metadata(illust_id)
            logger.debug(f"Metadata fetched: {metadata.title}")
            return metadata
        except PixivAPIError as e:
            logger.warning(f"Failed to get metadata for {illust_id}: {e}, using basic data")
            return None

    def _build_filepath(
        self,
        illust: dict,
        metadata: ArtworkMetadata | None,
        template: PathTemplate | None,
        mode: str,
        date: str,
        ranking_dir: Path | None,
    ) -> Path:
        """构建文件路径

        Args:
            illust: 排行榜作品数据
            metadata: 元数据(可能为 None)
            template: 路径模板(可能为 None)
            mode: 排行榜模式
            date: 日期字符串
            ranking_dir: 排行榜目录(仅未使用模板时)

        Returns:
            文件路径
        """
        if template:
            # 使用路径模板
            context = {
                "mode": mode,
                "date": date,
                "illust_id": illust['id'],
                "title": metadata.title if metadata else illust['title'],
                "author": metadata.author if metadata else illust['author'],
                "author_id": metadata.author_id if metadata else 0,
            }
            filepath = self.output_dir / template.render(context)
            # 确保父目录存在
            filepath.parent.mkdir(parents=True, exist_ok=True)
        else:
            # 默认路径: {output_dir}/{mode}-{date}/{illust_id}_{title}.jpg
            filename = sanitize_filename(f"{illust['id']}_{metadata.title if metadata else illust['title']}.jpg")
            filepath = ranking_dir / filename

        return filepath

    def _build_success_item(
        self, illust: dict, metadata: ArtworkMetadata | None, result: dict
    ) -> dict:
        """构建成功结果项

        Args:
            illust: 排行榜作品数据
            metadata: 元数据(可能为 None)
            result: 下载结果

        Returns:
            成功结果字典
        """
        success_item = {
            "illust_id": illust['id'],
            "title": metadata.title if metadata else illust['title'],
            "author": metadata.author if metadata else illust['author'],
            "filepath": result["filepath"],
        }

        # 添加元数据字段 (如果有)
        if metadata:
            success_item["tags"] = [tag.model_dump() for tag in metadata.tags]
            success_item["statistics"] = metadata.statistics.model_dump()

        return success_item
