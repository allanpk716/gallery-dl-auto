"""config 子命令

查看当前配置。
"""

import json

import click
import yaml
from rich.console import Console
from rich.table import Table


@click.command()
@click.pass_context
def config_cmd(ctx: click.Context) -> None:
    """查看当前配置

    显示从 config.yaml 加载的配置值。
    """
    console = Console()

    try:
        # 加载配置文件
        with open("config.yaml", encoding="utf-8") as f:
            config = yaml.safe_load(f)

        # 根据输出模式选择输出格式
        if ctx.obj.get("output_mode") == "json":
            # JSON 输出模式
            output_data = {
                "config": config
            }
            click.echo(json.dumps(output_data, ensure_ascii=False))
        else:
            # Rich 表格输出模式
            table = Table(title="当前配置", show_header=True, header_style="bold blue")
            table.add_column("配置项", style="cyan")
            table.add_column("值", style="green")

            for key, value in config.items():
                table.add_row(key, str(value))

            console.print(table)

    except FileNotFoundError:
        if ctx.obj.get("output_mode") == "json":
            error_data = {
                "error": "FileNotFoundError",
                "message": "找不到 config.yaml 文件",
                "suggestion": "请确保 config.yaml 在当前目录下"
            }
            click.echo(json.dumps(error_data, ensure_ascii=False))
            ctx.exit(1)
        else:
            console.print("[bold red]错误:[/bold red] 找不到 config.yaml 文件")
            console.print("请确保 config.yaml 在当前目录下")
            raise click.Abort() from None
    except yaml.YAMLError as e:
        if ctx.obj.get("output_mode") == "json":
            error_data = {
                "error": "YAMLError",
                "message": "config.yaml 格式错误",
                "details": str(e)
            }
            click.echo(json.dumps(error_data, ensure_ascii=False))
            ctx.exit(1)
        else:
            console.print("[bold red]错误:[/bold red] config.yaml 格式错误")
            console.print(f"详细信息: {e}")
            raise click.Abort() from None
