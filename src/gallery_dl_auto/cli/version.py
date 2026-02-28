"""version 子命令

显示版本信息。
"""

import json
import platform
import sys

import click

from gallery_dl_auto import __version__


@click.command()
@click.pass_context
def version(ctx: click.Context) -> None:
    """显示版本信息"""
    version_info = {
        "version": __version__,
        "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        "platform": platform.system().lower(),
    }

    # 根据输出模式选择输出格式
    if ctx.obj.get("output_mode") == "json":
        click.echo(json.dumps(version_info, ensure_ascii=False))
    else:
        click.echo(f"pixiv-downloader version {__version__}")
