"""doctor 子命令

诊断环境和配置。
"""

import os
import sys

import click
from rich.console import Console


@click.command()
@click.pass_context
def doctor(ctx: click.Context) -> None:
    """诊断环境和配置

    检查 Python 版本、依赖项和配置文件。
    """
    console: Console = ctx.obj["console"]

    console.print("[bold blue]运行诊断检查...[/bold blue]\n")

    # 检查 Python 版本
    python_version = sys.version_info
    if python_version >= (3, 10):
        console.print(
            f"[green]OK[/green] Python 版本: {python_version.major}.{python_version.minor}.{python_version.micro}"
        )
    else:
        console.print(
            f"[red]X[/red] Python 版本过低: {python_version.major}.{python_version.minor}.{python_version.micro}"
        )
        console.print("  需要 Python 3.10 或更高版本")

    # 检查配置文件
    if os.path.exists("config.yaml"):
        console.print("[green]OK[/green] 配置文件: config.yaml")
    else:
        console.print("[red]X[/red] 配置文件: config.yaml (不存在)")
        console.print("  提示: 程序将使用默认配置")

    # 检查依赖项
    dependencies = ["click", "hydra", "omegaconf", "rich"]
    for dep in dependencies:
        try:
            __import__(dep)
            console.print(f"[green]OK[/green] 依赖项: {dep}")
        except ImportError:
            console.print(f"[red]X[/red] 依赖项: {dep} (未安装)")

    console.print("\n[bold green]诊断完成[/bold green]")
