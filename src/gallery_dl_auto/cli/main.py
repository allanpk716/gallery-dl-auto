"""主 CLI 命令组

提供主命令入口点和全局选项,注册所有子命令。
"""

import json
import logging

import click

from gallery_dl_auto.cli.json_help import generate_json_help
from gallery_dl_auto.utils.logging import setup_logging


def _handle_json_help(ctx: click.Context, param: click.Parameter, value: bool) -> None:
    """处理 --json-help 参数

    当用户指定 --json-help 时,输出 JSON 帮助并退出程序。

    Args:
        ctx: Click 上下文
        param: 参数对象
        value: 参数值(True 如果用户指定了 --json-help)
    """
    if value:
        # 生成 JSON 帮助
        help_data = generate_json_help(cli)

        # 输出 JSON 到 stdout,使用 ensure_ascii=False 正确显示中文
        print(json.dumps(help_data, ensure_ascii=False, indent=2))

        # 退出程序
        ctx.exit(0)


@click.group()
@click.option("--verbose", "-v", is_flag=True, help="详细模式:显示调试信息(与 --quiet/--json-output 冲突时被忽略)")
@click.option("--quiet", "-q", is_flag=True, help="静默模式:禁用所有输出")
@click.option("--json-output", is_flag=True, help="JSON 输出模式:所有输出为 JSON 格式")
@click.option(
    "--json-help",
    is_flag=True,
    is_eager=True,
    expose_value=False,
    callback=_handle_json_help,
    help="输出结构化 JSON 帮助信息",
)
@click.pass_context
def cli(ctx: click.Context, verbose: bool, quiet: bool, json_output: bool) -> None:
    """Pixiv 排行榜下载器 - 自动化获取 token 并下载排行榜内容

    用户首次手动登录后,程序自动捕获、存储和更新 refresh token,
    无需手动从浏览器开发者工具中复制,实现真正的自动化下载流程。

    \b
    [首次使用必读]
    - 必须先运行 'pixiv-downloader login' 完成登录
    - AI Agent 调用前请确认人类已完成登录操作
    - Token 失效时需要人类重新运行 'pixiv-downloader login'

    \b
    常用命令:
      pixiv-downloader login           登录并保存 token (首次使用必须)
      pixiv-downloader status          查看 token 状态
      pixiv-downloader version         显示版本信息
      pixiv-downloader config          查看当前配置
      pixiv-downloader doctor          诊断环境和配置
      pixiv-downloader download        下载排行榜内容
    """
    ctx.ensure_object(dict)

    # 确定输出模式(优先级: --json-output > --quiet > --verbose)
    if json_output:
        ctx.obj["output_mode"] = "json"
    elif quiet:
        ctx.obj["output_mode"] = "quiet"
    else:
        ctx.obj["output_mode"] = "normal"

    # verbose 仅在 normal 模式下生效
    effective_verbose = verbose and ctx.obj["output_mode"] == "normal"

    # 配置日志系统
    setup_logging(
        log_level="DEBUG" if effective_verbose else "INFO",
        verbose=effective_verbose,
        quiet=(ctx.obj["output_mode"] in ["quiet", "json"]),
    )

    # 将 verbose 保存到上下文,供子命令使用
    ctx.obj["verbose"] = effective_verbose


# 注册子命令(在文件末尾)
from gallery_dl_auto.cli.config_cmd import config_cmd  # noqa: E402
from gallery_dl_auto.cli.doctor import doctor  # noqa: E402
from gallery_dl_auto.cli.download_cmd import download  # noqa: E402
from gallery_dl_auto.cli.login_cmd import login  # noqa: E402
from gallery_dl_auto.cli.logout_cmd import logout  # noqa: E402
from gallery_dl_auto.cli.refresh_cmd import refresh  # noqa: E402
from gallery_dl_auto.cli.status_cmd import status  # noqa: E402
from gallery_dl_auto.cli.version import version  # noqa: E402

cli.add_command(version)
cli.add_command(config_cmd, name="config")
cli.add_command(doctor)
cli.add_command(download)
cli.add_command(login)
cli.add_command(logout)
cli.add_command(refresh)
cli.add_command(status)

def main() -> int:
    """CLI 入口点,包含全局异常处理

    Returns:
        退出码
    """
    import sys

    # 保存 --json-output 标志供异常处理使用
    json_mode = "--json-output" in sys.argv

    try:
        # 调用 CLI,在 JSON 模式下使用 standalone_mode=False
        cli(standalone_mode=not json_mode, prog_name="pixiv-downloader")
        sys.exit(0)
    except SystemExit as e:
        # SystemExit 可能包含退出码
        if isinstance(e.code, int):
            sys.exit(e.code)
        elif e.code is None:
            sys.exit(0)
        else:
            sys.exit(1)
    except click.ClickException as e:
        # 只在 JSON 模式下捕获异常
        if json_mode:
            # JSON 格式输出错误
            error_data = {
                "success": False,
                "error": e.__class__.__name__,
                "message": e.format_message()
            }
            print(json.dumps(error_data, ensure_ascii=False))
            sys.exit(e.exit_code)
        else:
            # 非 JSON 模式,不应该到这里,因为 standalone_mode=True
            # 但以防万一,重新抛出
            raise
    except KeyboardInterrupt:
        # 用户中断
        sys.exit(130)
    except Exception as e:
        # 未预期的异常
        if json_mode:
            error_data = {
                "success": False,
                "error": e.__class__.__name__,
                "message": str(e)
            }
            print(json.dumps(error_data, ensure_ascii=False))
            sys.exit(1)
        else:
            # 其他异常,重新抛出让 Python 处理
            raise


if __name__ == "__main__":
    main()
