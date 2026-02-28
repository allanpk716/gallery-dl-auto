"""Download command implementation

Implements the 'pixiv-downloader download' command for downloading ranking images.
"""

import datetime
import json
import logging
import signal
import sys
from pathlib import Path

import click
from omegaconf import DictConfig

from gallery_dl_auto.api.pixiv_client import PixivClient
from gallery_dl_auto.auth.token_storage import get_default_token_storage
from gallery_dl_auto.cli.validators import validate_type_param, validate_date_param
from gallery_dl_auto.config.download_config import DownloadConfig
from gallery_dl_auto.config.paths import get_download_db_path
from gallery_dl_auto.download.download_tracker import DownloadTracker
from gallery_dl_auto.download.ranking_downloader import RankingDownloader
from gallery_dl_auto.models.error_response import BatchDownloadResult, StructuredError
from gallery_dl_auto.utils.error_codes import ErrorCode

logger = logging.getLogger("gallery_dl_auto")


def handle_interrupt(signum, frame):
    """处理 Ctrl+C 中断信号

    用户中断下载时,进度已保存到断点状态文件,下次运行将从断点继续。
    """
    logger.warning("用户中断下载,进度已保存,下次运行将从断点继续")

    # 输出 JSON 格式的中断信息
    print(json.dumps({
        "success": False,
        "error": "USER_INTERRUPT",
        "message": "下载被用户中断,进度已保存",
        "suggestion": "重新运行相同命令将从断点继续下载"
    }, ensure_ascii=False, indent=2))

    sys.exit(130)  # 128 + SIGINT(2)


@click.command()
@click.option(
    "--type",
    callback=validate_type_param,
    required=True,
    help="Ranking type (daily, weekly, monthly, day_male, day_female, week_original, week_rookie, day_manga, day_r18, day_male_r18, day_female_r18, week_r18, week_r18g)",
)
@click.option(
    "--date",
    callback=validate_date_param,
    default=None,
    help="Download ranking for specific date (YYYY-MM-DD, default: today)",
)
@click.option(
    "--output",
    "-o",
    type=click.Path(),
    default="./pixiv-downloads",
    help="Output directory (default: ./pixiv-downloads)",
)
@click.option(
    "--path-template",
    default=None,
    help="Path template for saving files (e.g., {author}/{title}.jpg). Variables: {mode}, {date}, {illust_id}, {title}, {author}, {author_id}",
)
@click.option(
    "--verbose",
    "-v",
    is_flag=True,
    default=False,
    help="详细模式:显示实时进度和调试信息",
)
@click.option(
    "--image-delay",
    type=float,
    default=None,
    help="单张图片间隔秒数 (默认: 2.5s, 配置文件: config/download.yaml)",
)
@click.option(
    "--batch-delay",
    type=float,
    default=None,
    help="批次间隔秒数 (默认: 2.0s)",
)
@click.option(
    "--batch-size",
    type=int,
    default=None,
    help="每批次下载的作品数量 (默认: 30)",
)
@click.option(
    "--max-retries",
    type=int,
    default=None,
    help="单张图片最大重试次数 (默认: 3)",
)
@click.pass_obj
def download(
    config: DictConfig,
    type: str,
    date: str | None,
    output: str,
    path_template: str | None,
    verbose: bool,
    image_delay: float | None,
    batch_delay: float | None,
    batch_size: int | None,
    max_retries: int | None
) -> None:
    """Download Pixiv ranking images

    Downloads images from the specified ranking to the output directory.
    Outputs JSON-formatted results for third-party integration.

    Download parameters (batch_size, image_delay, etc.) are loaded from
    configuration file: config/download.yaml

    CLI parameters override configuration file values.

    支持断点续传:如果下载被中断(Ctrl+C),进度会自动保存。
    下次运行相同命令时,将从断点位置继续下载,无需重新下载已完成的作品。
    """
    # 注册中断信号处理器
    signal.signal(signal.SIGINT, handle_interrupt)

    # 重新配置日志(如果 verbose 改变)
    if verbose:
        from gallery_dl_auto.utils.logging import setup_logging
        setup_logging(log_level="DEBUG", verbose=True)

    # type 参数已通过验证器转换为 API mode 参数
    mode = type

    # 1. Load download configuration
    download_config_dict = config.get('download', {})
    download_config = DownloadConfig(**download_config_dict)

    # 2. CLI 参数覆盖配置文件(仅当 CLI 参数非 None 时)
    if image_delay is not None:
        download_config.image_delay = image_delay
    if batch_delay is not None:
        download_config.batch_delay = batch_delay
    if batch_size is not None:
        download_config.batch_size = batch_size
    if max_retries is not None:
        download_config.max_retries = max_retries

    # 2. Load token
    storage = get_default_token_storage()
    token_data = storage.load_token()

    if not token_data or not token_data.get("refresh_token"):
        error = StructuredError(
            error_code=ErrorCode.AUTH_TOKEN_NOT_FOUND,
            error_type="AuthError",
            message="No token found",
            suggestion="Run 'pixiv-downloader login' first",
            severity="error",
        )
        print(error.model_dump_json(indent=2))
        sys.exit(1)

    # 3. Initialize API client
    try:
        client = PixivClient(refresh_token=token_data["refresh_token"])
    except Exception as e:
        error = StructuredError(
            error_code=ErrorCode.AUTH_TOKEN_INVALID,
            error_type="AuthError",
            message=f"Authentication failed: {e}",
            suggestion="Check your token or run 'pixiv-downloader login' again",
            severity="error",
            original_error=str(e),
        )
        print(error.model_dump_json(indent=2))
        sys.exit(1)

    # 4. Initialize downloader with configuration
    output_dir = Path(output)
    downloader = RankingDownloader(
        client=client,
        output_dir=output_dir,
        config=download_config,
        verbose=verbose  # 传递详细模式标志
    )

    # 5. Initialize download tracker for incremental downloads
    tracker = DownloadTracker(get_download_db_path())

    # 6. Execute download
    result = downloader.download_ranking(
        mode=mode,
        date=date,
        path_template=path_template,
        tracker=tracker
    )

    # 7. Output JSON result
    print(result.model_dump_json(indent=2, ensure_ascii=False))

    # 8. Return exit code based on download status
    if result.success:
        sys.exit(0)  # 完全成功
    elif result.downloaded > 0:
        sys.exit(1)  # 部分成功
    else:
        sys.exit(2)  # 完全失败

