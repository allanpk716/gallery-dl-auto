"""Gallery-dl 封装类

封装 gallery-dl 命令行工具,提供排行榜下载功能。
"""

import json
import logging
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
    from gallery_dl_auto.history.download_tracker import DownloadTracker

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

        # 3. 执行命令
        temp_config_file = None
        try:
            # 构建命令和临时配置文件
            cmd, temp_config_file = self._build_command(
                url=url,
                refresh_token=refresh_token,
                output_dir=output_dir,
                path_template=path_template,
                limit=limit,
                offset=offset,
                dry_run=dry_run,
                verbose=verbose,
            )

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

            # 5. 解析结果
            return self._parse_result(result, dry_run, output_dir, limit, offset, actual_download_path)

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

        Returns:
            tuple[list[str], Path]: 命令参数列表和临时配置文件路径
        """
        # 创建临时配置文件
        config_file = self._create_temp_config(refresh_token, output_dir, path_template)

        cmd = ["gallery-dl"]

        # 使用临时配置文件
        cmd.extend(["--config", str(config_file)])

        # 范围限制：
        # 注意：gallery-dl 的 --range 限制的是图片页面，不是作品数量
        # 所以我们需要请求更多页面来确保获得足够的作品
        # 这里使用一个保守的估算：每个作品平均 1.5 页
        if limit is not None or offset > 0:
            # 计算需要请求的页面范围
            start_page = offset + 1
            if limit:
                # 请求 limit * 2 的页面，确保获得足够的作品
                # （假设最坏情况每个作品有 2 页）
                end_page = offset + limit * 2
            else:
                end_page = ""  # 无上限

            cmd.extend(["--range", f"{start_page}-{end_page}"])
            logger.debug(f"请求图片页面范围: {start_page}-{end_page}")

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
        self, refresh_token: str, output_dir: Path, path_template: Optional[str]
    ) -> Path:
        """创建临时 gallery-dl 配置文件

        Args:
            refresh_token: refresh token
            output_dir: 下载目录
            path_template: 路径模板

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
            return self._parse_download_output(result.stdout, output_dir, actual_download_path)

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
        self, stdout: str, output_dir: Path, actual_download_path: Optional[Path] = None
    ) -> BatchDownloadResult:
        """解析正常下载输出（文件路径）

        Args:
            stdout: gallery-dl 标准输出（每行一个文件路径）
            output_dir: 输出目录
            actual_download_path: 实际下载路径

        Returns:
            BatchDownloadResult: 下载结果
        """
        success_list = []

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
                    success_list.append(illust_id)
                    logger.debug(f"下载成功: {illust_id} -> {line}")
                else:
                    logger.warning(f"无法解析文件名: {line}")
            except (ValueError, IndexError) as e:
                logger.warning(f"无法解析文件路径: {line}, 错误: {e}")

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
