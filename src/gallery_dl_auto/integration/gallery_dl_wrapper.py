"""Gallery-dl 封装类

封装 gallery-dl 命令行工具,提供排行榜下载功能。
"""

import json
import logging
import sqlite3
import subprocess
import sys
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from typing import TYPE_CHECKING, Optional

from gallery_dl_auto.auth.token_storage import get_default_token_storage
from gallery_dl_auto.config.download_config import DownloadConfig
from gallery_dl_auto.core.mode_errors import InvalidModeError
from gallery_dl_auto.core.mode_manager import ModeManager
from gallery_dl_auto.integration.token_bridge import TokenBridge
from gallery_dl_auto.models.error_response import BatchDownloadResult, StructuredError
from gallery_dl_auto.utils.error_codes import ErrorCode

if TYPE_CHECKING:
    from gallery_dl_auto.download.download_tracker import DownloadTracker

logger = logging.getLogger("gallery_dl_auto")


class GalleryDLWrapper:
    """Gallery-dl 封装类

    封装 gallery-dl 命令行调用,提供排行榜下载功能。
    """

    def __init__(self, config: DownloadConfig):
        """初始化 Gallery-dl 封装

        Args:
            config: 下载配置
        """
        self.config = config
        self.token_storage = get_default_token_storage()
        self.token_bridge = TokenBridge(self.token_storage)

        # 检查 gallery-dl 是否安装
        self._check_gallery_dl_installed()

    def _check_gallery_dl_installed(self) -> None:
        """检查 gallery-dl 是否已安装

        Raises:
            RuntimeError: 如果 gallery-dl 未安装
        """
        try:
            result = subprocess.run(
                ["gallery-dl", "--version"],
                capture_output=True,
                text=True,
                timeout=10
            )
            if result.returncode == 0:
                logger.info(f"gallery-dl 版本: {result.stdout.strip()}")
        except FileNotFoundError:
            raise RuntimeError(
                "gallery-dl 未安装。请运行: pip install gallery-dl>=1.28.0"
            )
        except subprocess.TimeoutExpired:
            logger.warning("检查 gallery-dl 版本超时")

    def download_ranking(
        self,
        mode: str,
        date: Optional[str],
        output_dir: Path,
        path_template: Optional[str] = None,
        limit: Optional[int] = None,
        offset: int = 0,
        dry_run: bool = False,
        verbose: bool = False,
        tracker: Optional['DownloadTracker'] = None,
    ) -> BatchDownloadResult:
        """下载排行榜

        Args:
            mode: 排行榜类型 (daily, weekly, day_male_r18 等)
            date: 日期 (YYYY-MM-DD), None 表示今天
            output_dir: 下载目录
            path_template: 路径模板
            limit: 最多下载的作品数量
            offset: 跳过前 N 个作品
            dry_run: 预览模式,只获取信息不下载
            verbose: 详细输出模式
            tracker: 下载历史追踪器（可选，用于去重）

        Returns:
            BatchDownloadResult: 下载结果
        """
        # 1. 获取 refresh token
        refresh_token = self.token_bridge.get_refresh_token()
        if not refresh_token:
            return BatchDownloadResult(
                success=False,
                total=0,
                downloaded=0,
                failed=0,
                skipped=0,
                output_dir=str(output_dir),
                actual_download_dir=None,
                success_list=[],
                failed_errors=[
                    StructuredError(
                        error_code=ErrorCode.AUTH_TOKEN_NOT_FOUND,
                        error_type="AuthError",
                        message="无法获取 refresh token",
                        suggestion="运行 'pixiv-downloader login' 登录",
                        severity="error",
                    )
                ],
            )

        # 2. 构建排行榜 URL 并计算实际下载路径
        url = self._build_ranking_url(mode, date)

        # 计算实际下载路径（gallery-dl 的默认路径格式）
        # 格式: {output_dir}/pixiv/rankings/{mode}/{date}/
        # 注意：gallery-dl 使用原始的 API mode，而不是转换后的 gallery-dl mode

        # 如果未指定日期，使用前天的日期（与 _build_ranking_url 逻辑一致）
        actual_date = date
        if not actual_date:
            day_before = datetime.now() - timedelta(days=2)
            actual_date = day_before.strftime("%Y-%m-%d")

        # 构建实际下载路径（使用原始 mode）
        actual_download_path = output_dir.joinpath("pixiv", "rankings", mode, actual_date)

        # 转换为绝对路径
        actual_download_path = actual_download_path.resolve()

        # 如果提供了 tracker 且不是 dry_run，执行两阶段下载
        use_dedup = tracker is not None and not dry_run

        if use_dedup:
            logger.info("Deduplication enabled: will check existing downloads first")

        # 3. 执行命令
        temp_config_file = None
        archive_file = None
        all_ids = []
        skipped_ids = []

        try:
            # 阶段 1: 如果启用去重，先执行 dry-run 检查
            if use_dedup:
                logger.info("Phase 1: Checking existing downloads (dry-run)...")

                # 执行 dry-run 获取作品列表
                dry_run_cmd, temp_config_file = self._build_command(
                    url=url,
                    refresh_token=refresh_token,
                    output_dir=output_dir,
                    path_template=path_template,
                    limit=limit,
                    offset=offset,
                    dry_run=True,  # 强制 dry-run
                    verbose=verbose,
                )

                logger.debug(f"Dry-run command: {' '.join(dry_run_cmd)}")

                dry_run_result = subprocess.run(
                    dry_run_cmd,
                    capture_output=True,
                    text=True,
                    timeout=300,  # 5 分钟超时
                )

                if dry_run_result.returncode != 0:
                    logger.error(f"Dry-run failed: {dry_run_result.stderr}")
                    # 降级：不使用去重，继续正常下载
                    logger.warning("Deduplication disabled due to dry-run failure")
                    use_dedup = False
                else:
                    # 解析 dry-run 结果
                    dry_run_batch_result = self._parse_result(
                        dry_run_result, True, output_dir, limit, offset, actual_download_path
                    )

                    # 检查已下载作品
                    all_ids = dry_run_batch_result.success_list
                    pending_ids, skipped_ids = self._check_existing_downloads(
                        dry_run_batch_result, tracker
                    )

                    # 如果全部已下载，直接返回成功
                    if not pending_ids:
                        logger.info("All works already downloaded, skipping actual download")
                        return BatchDownloadResult(
                            success=True,
                            total=len(all_ids),
                            downloaded=0,
                            failed=0,
                            skipped=len(skipped_ids),
                            output_dir=str(output_dir),
                            actual_download_dir=str(actual_download_path),
                            success_list=[],
                            failed_errors=[],
                        )

                    logger.info(f"Will download {len(pending_ids)} new works")

            # 阶段 2: 生成 archive 文件（如果启用去重）
            if use_dedup:
                logger.info("Phase 2: Generating archive file...")
                temp_dir = Path.home() / ".gallery-dl-auto" / "temp"
                archive_file = self._generate_archive_file(tracker, temp_dir)

                if not archive_file:
                    logger.warning("Archive generation failed, deduplication disabled")
                    use_dedup = False

            # 阶段 3: 执行实际下载
            logger.info("Phase 3: Executing download..." if use_dedup else "Executing download...")

            cmd, temp_config_file_new = self._build_command(
                url=url,
                refresh_token=refresh_token,
                output_dir=output_dir,
                path_template=path_template,
                limit=limit,
                offset=offset,
                dry_run=dry_run,
                verbose=verbose,
                archive_file=archive_file,  # 传递 archive 文件
            )

            # 如果之前已经有 temp_config_file，先删除
            if temp_config_file and temp_config_file.exists():
                try:
                    temp_config_file.unlink()
                except OSError:
                    pass

            temp_config_file = temp_config_file_new

            logger.info(f"执行 gallery-dl 命令: {' '.join(cmd)}")

            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                timeout=600,  # 10 分钟超时
            )

            # 记录输出用于调试
            if result.stdout:
                logger.debug(f"gallery-dl stdout 长度: {len(result.stdout)}")
            if result.stderr:
                logger.debug(f"gallery-dl stderr: {result.stderr[:500]}")

            # 阶段 4: 解析结果
            batch_result = self._parse_result(result, dry_run, output_dir, limit, offset, actual_download_path)

            # 阶段 5: 记录下载到 tracker（仅在实际下载成功后）
            if tracker is not None and not dry_run and batch_result.success_list:
                logger.info("Phase 4: Recording downloads to tracker...")
                self._record_downloads(batch_result, tracker, mode, actual_date)

            # 添加去重统计信息
            if use_dedup and skipped_ids:
                batch_result.skipped = len(skipped_ids)
                batch_result.total = len(all_ids) if all_ids else batch_result.total

                # 添加 dedup_stats（需要修改 BatchDownloadResult 模型）
                # 这里先记录日志
                logger.info(
                    f"Dedup stats: checked={batch_result.total}, "
                    f"already_exists={len(skipped_ids)}, "
                    f"new_downloads={batch_result.downloaded}"
                )

            return batch_result

        except subprocess.TimeoutExpired:
            return BatchDownloadResult(
                success=False,
                total=0,
                downloaded=0,
                failed=0,
                skipped=0,
                output_dir=str(output_dir),
                actual_download_dir=str(actual_download_path),
                success_list=[],
                failed_errors=[
                    StructuredError(
                        error_code=ErrorCode.DOWNLOAD_TIMEOUT,
                        error_type="DownloadError",
                        message="下载超时",
                        suggestion="增加超时时间或减少下载数量",
                        severity="error",
                    )
                ],
            )
        except Exception as e:
            logger.error(f"gallery-dl 执行失败: {e}")
            return BatchDownloadResult(
                success=False,
                total=0,
                downloaded=0,
                failed=0,
                skipped=0,
                output_dir=str(output_dir),
                actual_download_dir=str(actual_download_path),
                success_list=[],
                failed_errors=[
                    StructuredError(
                        error_code=ErrorCode.INTERNAL_ERROR,
                        error_type="DownloadError",
                        message=f"下载失败: {e}",
                        suggestion="查看日志了解详细错误",
                        severity="error",
                        original_error=str(e),
                    )
                ],
            )
        finally:
            # 清理临时配置文件
            if temp_config_file and temp_config_file.exists():
                try:
                    temp_config_file.unlink()
                except OSError:
                    pass

    def _build_ranking_url(self, mode: str, date: Optional[str]) -> str:
        """构建排行榜 URL

        Args:
            mode: 排行榜类型 (Pixiv API format: day, week, day_male_r18 等)
            date: 日期 (YYYY-MM-DD), None 表示今天

        Returns:
            str: 排行榜 URL

        Raises:
            InvalidModeError: 当 mode 不在支持列表中时
        """
        # 使用 ModeManager 进行统一转换
        # API mode (day_male_r18) -> gallery-dl mode (male_r18)
        try:
            gallery_dl_mode = ModeManager.api_to_gallery_dl(mode)
            logger.debug(f"Mode 转换: {mode} -> {gallery_dl_mode}")
        except InvalidModeError as e:
            logger.error(f"无效的排行榜 mode: {mode}")
            raise

        # 如果用户未指定日期，使用前天的日期
        # 原因：Pixiv 排行榜通常需要 1 天时间更新，昨天的排行榜可能还没有数据
        if not date:
            day_before = datetime.now() - timedelta(days=2)
            date = day_before.strftime("%Y-%m-%d")
            logger.info(f"未指定日期，使用前天的日期: {date}")

        # gallery-dl 支持的排行榜 URL 格式
        # https://www.pixiv.net/ranking.php?mode=daily&content=illust&date=20240101
        # 注意：gallery-dl 需要 YYYYMMDD 格式，而不是 YYYY-MM-DD
        base_url = f"https://www.pixiv.net/ranking.php?mode={gallery_dl_mode}&content=illust"

        # 将 YYYY-MM-DD 转换为 YYYYMMDD（移除连字符）
        formatted_date = date.replace("-", "")
        base_url += f"&date={formatted_date}"
        logger.debug(f"日期格式转换: {date} -> {formatted_date}")

        logger.debug(f"构建排行榜 URL: {base_url}")
        return base_url

    def _build_command(
        self,
        url: str,
        refresh_token: str,
        output_dir: Path,
        path_template: Optional[str],
        limit: Optional[int],
        offset: int,
        dry_run: bool,
        verbose: bool,
        archive_file: Optional[Path] = None,
    ) -> tuple[list[str], Path]:
        """构建 gallery-dl 命令

        Args:
            url: 排行榜 URL
            refresh_token: refresh token
            output_dir: 下载目录
            path_template: 路径模板
            limit: 最多下载的作品数量
            offset: 跳过前 N 个作品
            dry_run: 预览模式
            verbose: 详细输出模式
            archive_file: archive 文件路径（可选，用于去重）

        Returns:
            tuple[list[str], Path]: 命令参数列表和临时配置文件路径
        """
        # 创建临时配置文件
        config_file = self._create_temp_config(refresh_token, output_dir, path_template, archive_file)

        cmd = ["gallery-dl"]

        # 使用临时配置文件
        cmd.extend(["--config", str(config_file)])

        # 范围限制：使用 gallery-dl 的 max-posts 选项精确控制作品数量
        # 注意：max-posts 限制的是作品（posts）数量，不是图片页面数
        # 这比 --range 更精确，因为 --range 是基于图片页面数
        if limit is not None:
            # 如果有 offset，需要请求 offset + limit 个作品
            # 然后在解析输出时切片
            total_posts = offset + limit
            cmd.extend(["-o", f"max-posts={total_posts}"])
            logger.debug(f"限制下载作品数量: max-posts={total_posts} (offset={offset}, limit={limit})")
        elif offset > 0:
            # 只有 offset 没有 limit：请求足够多的作品（offset + 一个大数）
            # 然后在解析输出时跳过前 offset 个
            # 使用一个保守的大数（1000）作为上限
            cmd.extend(["-o", f"max-posts={offset + 1000}"])
            logger.debug(f"从第 {offset + 1} 个作品开始下载（无上限）")

        # 预览模式
        if dry_run:
            cmd.append("--simulate")
            cmd.append("--dump-json")  # 只在 simulate 模式下使用 dump-json
        else:
            # 真实下载时，不使用 --print，让 gallery-dl 正常下载
            # gallery-dl 会输出下载的文件路径
            pass

        # 详细输出
        if verbose:
            cmd.append("--verbose")

        # 排行榜 URL
        cmd.append(url)

        return cmd, config_file

    def _create_temp_config(
        self, refresh_token: str, output_dir: Path, path_template: Optional[str], archive_file: Optional[Path] = None
    ) -> Path:
        """创建临时 gallery-dl 配置文件

        Args:
            refresh_token: refresh token
            output_dir: 下载目录
            path_template: 路径模板
            archive_file: archive 文件路径（可选，用于去重）

        Returns:
            Path: 临时配置文件路径
        """
        config = {
            "extractor": {
                "pixiv": {
                    "refresh-token": refresh_token,
                    "filename": path_template if path_template else "{id}_p{num}.{extension}",
                }
            },
            "downloader": {
                "part-directory": str(output_dir / ".parts"),
            },
            "base-directory": str(output_dir),  # 设置基础目录
        }

        # 添加 archive 配置（如果提供）
        if archive_file:
            config["extractor"]["pixiv"]["archive"] = str(archive_file)
            logger.debug(f"Archive enabled: {archive_file}")

        # 创建临时文件
        temp_file = tempfile.NamedTemporaryFile(
            mode='w', suffix='.json', delete=False
        )
        json.dump(config, temp_file, indent=2)
        temp_file.close()

        logger.debug(f"创建临时配置文件: {temp_file.name}")
        logger.debug(f"配置内容: base-directory={output_dir}")

        return Path(temp_file.name)

    def _parse_result(
        self, result: subprocess.CompletedProcess, dry_run: bool, output_dir: Path, limit: Optional[int] = None, offset: int = 0, actual_download_path: Optional[Path] = None
    ) -> BatchDownloadResult:
        """解析 gallery-dl 执行结果

        Args:
            result: subprocess 执行结果
            dry_run: 是否为预览模式
            output_dir: 输出目录
            limit: 最多返回的作品数量
            offset: 跳过前 N 个作品
            actual_download_path: 实际下载路径

        Returns:
            BatchDownloadResult: 下载结果
        """
        # gallery-dl 的 JSON 输出格式示例:
        # dry-run: JSON 数组，包含作品元数据
        # 正常下载: 每行一个作品 ID (--print {id})

        if result.returncode != 0:
            # gallery-dl 执行失败
            logger.error(f"gallery-dl 失败: {result.stderr}")
            logger.debug(f"gallery-dl stdout: {result.stdout}")
            return BatchDownloadResult(
                success=False,
                total=0,
                downloaded=0,
                failed=0,
                skipped=0,
                output_dir=str(output_dir),
                actual_download_dir=str(actual_download_path) if actual_download_path else None,
                success_list=[],
                failed_errors=[
                    StructuredError(
                        error_code=ErrorCode.INTERNAL_ERROR,
                        error_type="DownloadError",
                        message=f"gallery-dl 执行失败: {result.stderr}",
                        suggestion="检查 gallery-dl 日志了解详细错误",
                        severity="error",
                        original_error=result.stderr,
                    )
                ],
            )

        # 解析输出
        downloaded = 0
        failed = 0
        success_list = []
        failed_errors = []

        if not result.stdout:
            logger.warning("gallery-dl 没有输出")
            return BatchDownloadResult(
                success=True,
                total=0,
                downloaded=0,
                failed=0,
                skipped=0,
                output_dir=str(output_dir),
                actual_download_dir=str(actual_download_path) if actual_download_path else None,
                success_list=[],
                failed_errors=[],
            )

        if dry_run:
            # 预览模式：解析 JSON 输出
            return self._parse_dry_run_output(result.stdout, output_dir, limit, offset, actual_download_path)
        else:
            # 正常下载模式：解析 ID 列表
            return self._parse_download_output(result.stdout, output_dir, actual_download_path, limit, offset)

    def _parse_dry_run_output(
        self, stdout: str, output_dir: Path, limit: Optional[int] = None, offset: int = 0, actual_download_path: Optional[Path] = None
    ) -> BatchDownloadResult:
        """解析预览模式输出（JSON）

        Args:
            stdout: gallery-dl 标准输出
            output_dir: 输出目录
            limit: 最多返回的作品数量
            offset: 跳过前 N 个作品
            actual_download_path: 实际下载路径

        Returns:
            BatchDownloadResult: 下载结果
        """
        downloaded = 0
        failed = 0
        success_list = []
        failed_errors = []

        try:
            data = json.loads(stdout.strip())
            logger.debug(f"解析的 JSON 类型: {type(data)}")

            # 递归提取所有字典对象
            def extract_items(obj):
                items = []
                if isinstance(obj, dict):
                    items.append(obj)
                    for value in obj.values():
                        if isinstance(value, (list, dict)):
                            items.extend(extract_items(value))
                elif isinstance(obj, list):
                    for item in obj:
                        items.extend(extract_items(item))
                return items

            all_items = extract_items(data)
            logger.debug(f"提取到 {len(all_items)} 个字典对象")

            # 过滤出包含 id 的作品项
            items = [
                item
                for item in all_items
                if isinstance(item, dict) and item.get("id")
            ]

            # 去重（基于 id）
            seen_ids = set()
            unique_items = []
            for item in items:
                item_id = item.get("id")
                if item_id and item_id not in seen_ids:
                    seen_ids.add(item_id)
                    unique_items.append(item)

            logger.debug(f"去重后剩余 {len(unique_items)} 个作品项")

            # 应用 limit 和 offset 限制（在去重后切片）
            if offset > 0:
                unique_items = unique_items[offset:]
                logger.debug(f"应用 offset={offset}，剩余 {len(unique_items)} 个作品")

            if limit is not None and limit > 0:
                unique_items = unique_items[:limit]
                logger.debug(f"应用 limit={limit}，最终 {len(unique_items)} 个作品")

            for item in unique_items:
                if "error" in item:
                    failed += 1
                    error_msg = item.get("error", "未知错误")
                    logger.error(f"下载失败: {error_msg}")
                    failed_errors.append(
                        StructuredError(
                            error_code=ErrorCode.DOWNLOAD_FAILED,
                            error_type="DownloadError",
                            message=str(error_msg),
                            suggestion="重试或检查网络连接",
                            severity="warning",
                        )
                    )
                else:
                    downloaded += 1
                    illust_id = item.get("id")
                    if illust_id:
                        try:
                            success_list.append(int(illust_id))
                        except (ValueError, TypeError):
                            logger.warning(f"无法转换 illust_id: {illust_id}")
                    logger.debug(f"下载成功: {item.get('title', item.get('id', 'unknown'))}")

            total = downloaded + failed

            return BatchDownloadResult(
                success=(failed == 0),
                total=total,
                downloaded=downloaded,
                failed=failed,
                skipped=0,
                output_dir=str(output_dir),
                actual_download_dir=str(actual_download_path) if actual_download_path else None,
                success_list=success_list,
                failed_errors=failed_errors,
            )

        except json.JSONDecodeError as e:
            logger.error(f"无法解析 gallery-dl JSON 输出: {e}")
            logger.debug(f"输出前500字符: {stdout[:500]}")
            return BatchDownloadResult(
                success=False,
                total=0,
                downloaded=0,
                failed=0,
                skipped=0,
                output_dir=str(output_dir),
                actual_download_dir=str(actual_download_path) if actual_download_path else None,
                success_list=[],
                failed_errors=[
                    StructuredError(
                        error_code=ErrorCode.INTERNAL_ERROR,
                        error_type="DownloadError",
                        message=f"无法解析 gallery-dl 输出: {e}",
                        suggestion="查看调试日志了解详细错误",
                        severity="error",
                        original_error=str(e),
                    )
                ],
            )

    def _parse_download_output(
        self, stdout: str, output_dir: Path, actual_download_path: Optional[Path] = None, limit: Optional[int] = None, offset: int = 0
    ) -> BatchDownloadResult:
        """解析正常下载输出（文件路径）

        Args:
            stdout: gallery-dl 标准输出（每行一个文件路径）
            output_dir: 输出目录
            actual_download_path: 实际下载路径
            limit: 最多返回的作品数量
            offset: 跳过前 N 个作品

        Returns:
            BatchDownloadResult: 下载结果
        """
        success_list = []
        seen_ids = set()  # 用于去重

        for line in stdout.strip().split("\n"):
            line = line.strip()
            if not line:
                continue

            # gallery-dl 输出下载的文件路径
            # 格式: tmp/test-fixed\pixiv\rankings\day\2026-02-28\141708029_p0.png
            # 提取作品 ID（文件名格式: {id}_p{num}.{extension}）

            try:
                filename = Path(line).stem  # 141708029_p0
                # 提取 ID（去掉 _p{num} 部分）
                if "_p" in filename:
                    illust_id_str = filename.split("_p")[0]
                    illust_id = int(illust_id_str)

                    # 去重：只添加第一次出现的作品 ID
                    if illust_id not in seen_ids:
                        seen_ids.add(illust_id)
                        success_list.append(illust_id)
                        logger.debug(f"下载成功: {illust_id} -> {line}")
                    else:
                        logger.debug(f"跳过重复的作品 ID: {illust_id} ({line})")
                else:
                    logger.warning(f"无法解析文件名: {line}")
            except (ValueError, IndexError) as e:
                logger.warning(f"无法解析文件路径: {line}, 错误: {e}")

        # 应用 offset 和 limit 限制（在去重后切片）
        if offset > 0:
            success_list = success_list[offset:]
            logger.debug(f"应用 offset={offset}，剩余 {len(success_list)} 个作品")

        if limit is not None and limit > 0:
            success_list = success_list[:limit]
            logger.debug(f"应用 limit={limit}，最终 {len(success_list)} 个作品")

        downloaded = len(success_list)

        return BatchDownloadResult(
            success=True,
            total=downloaded,
            downloaded=downloaded,
            failed=0,
            skipped=0,
            output_dir=str(output_dir),
            actual_download_dir=str(actual_download_path) if actual_download_path else None,
            success_list=success_list,
            failed_errors=[],
        )

    def _check_existing_downloads(
        self,
        dry_run_result: BatchDownloadResult,
        tracker: 'DownloadTracker'
    ) -> tuple[list[int], list[int]]:
        """检查已下载作品，返回待下载和已跳过的作品 ID

        Args:
            dry_run_result: dry-run 预检查的结果
            tracker: 下载历史追踪器

        Returns:
            tuple[list[int], list[int]]: (待下载作品ID列表, 已跳过作品ID列表)
        """
        if not dry_run_result.success_list:
            logger.info("No works to check")
            return [], []

        all_ids = dry_run_result.success_list
        logger.info(f"Checking {len(all_ids)} works against tracker...")

        # 使用 tracker 查询待下载作品
        # 注意：这里需要修改 tracker.get_pending_illusts() 以支持不指定 mode/date
        # 暂时使用 is_downloaded() 逐个检查
        pending_ids = []
        skipped_ids = []

        for illust_id in all_ids:
            if tracker.is_downloaded(illust_id):
                skipped_ids.append(illust_id)
                logger.debug(f"Skipping already downloaded: {illust_id}")
            else:
                pending_ids.append(illust_id)

        logger.info(
            f"Dedup check result: {len(pending_ids)} pending, "
            f"{len(skipped_ids)} already downloaded"
        )

        return pending_ids, skipped_ids

    def _generate_archive_file(
        self,
        tracker: 'DownloadTracker',
        temp_dir: Path
    ) -> Optional[Path]:
        """生成 gallery-dl archive 文件

        Args:
            tracker: 下载历史追踪器
            temp_dir: 临时文件目录

        Returns:
            Optional[Path]: archive 文件路径，失败返回 None
        """
        try:
            import time
            from gallery_dl_auto.download.download_tracker import DownloadTracker

            # 创建临时目录
            temp_dir.mkdir(parents=True, exist_ok=True)

            # 生成唯一的文件名
            timestamp = int(time.time())
            archive_file = temp_dir / f"archive_{timestamp}.txt"

            # 从 tracker 数据库读取所有已下载的 illust_id
            # 注意：需要在 DownloadTracker 中添加新方法 get_all_downloaded_ids()
            # 这里先使用占位符实现
            with sqlite3.connect(tracker.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT illust_id FROM downloads")
                all_ids = [row[0] for row in cursor.fetchall()]

            if not all_ids:
                logger.info("No existing downloads in tracker, skipping archive generation")
                return None

            # 写入 archive 文件（gallery-dl 格式：每行一个 ID）
            with open(archive_file, 'w', encoding='utf-8') as f:
                for illust_id in all_ids:
                    f.write(f"{illust_id}\n")

            logger.info(
                f"Generated archive file: {archive_file} "
                f"({len(all_ids)} downloaded works)"
            )
            return archive_file

        except Exception as e:
            logger.warning(f"Failed to generate archive file: {e}, deduplication disabled")
            return None

    def _record_downloads(
        self,
        result: BatchDownloadResult,
        tracker: 'DownloadTracker',
        mode: str,
        date: str
    ) -> None:
        """记录下载成功的作品到 tracker

        Args:
            result: 下载结果
            tracker: 下载历史追踪器
            mode: 排行榜模式
            date: 日期字符串
        """
        if not result.success_list:
            logger.debug("No successful downloads to record")
            return

        logger.info(f"Recording {len(result.success_list)} downloads to tracker...")

        # 将 actual_download_dir 转换为 Path 对象
        download_dir = Path(result.actual_download_dir) if result.actual_download_dir else None

        recorded_count = 0
        for illust_id in result.success_list:
            try:
                # 查找对应的文件路径
                # 从 success_list 中的 ID 推断文件路径（简化版本）
                # 实际文件路径格式：{output_dir}/pixiv/rankings/{mode}/{date}/{illust_id}_p0.jpg
                if not download_dir:
                    logger.warning(f"No download directory for {illust_id}")
                    continue

                file_path = download_dir / f"{illust_id}_p0.jpg"

                # 如果文件不存在，尝试其他扩展名
                if not file_path.exists():
                    for ext in ['.png', '.jpg', '.gif']:
                        test_path = download_dir / f"{illust_id}_p0{ext}"
                        if test_path.exists():
                            file_path = test_path
                            break

                # 获取文件大小（如果文件存在）
                file_size = None
                if file_path.exists():
                    file_size = file_path.stat().st_size

                # 记录到 tracker
                tracker.record_download(
                    illust_id=illust_id,
                    file_path=file_path,
                    mode=mode,
                    date=date,
                    file_size=file_size
                )
                recorded_count += 1

            except Exception as e:
                logger.warning(f"Failed to record download for {illust_id}: {e}")

        logger.info(f"Recorded {recorded_count}/{len(result.success_list)} downloads to tracker")
