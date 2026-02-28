"""Status command implementation

Implements the 'pixiv-downloader status' command for checking token validity.
"""

import datetime
import json
import logging

import click
from rich.console import Console
from rich.table import Table

from gallery_dl_auto.auth.pixiv_auth import PixivOAuth
from gallery_dl_auto.auth.token_storage import get_default_token_storage

logger = logging.getLogger("gallery_dl_auto")


@click.command()
@click.option(
    "--verbose", "-v", is_flag=True, help="Show detailed token information"
)
@click.pass_context
def status(ctx: click.Context, verbose: bool) -> None:
    """Check Pixiv token status

    Shows whether a valid token exists and can be refreshed
    """
    console = Console()
    storage = get_default_token_storage()

    # Check if token file exists
    if not storage.storage_path.exists():
        if ctx.obj.get("output_mode") == "json":
            error_data = {
                "logged_in": False,
                "token_valid": False,
                "username": None,
                "error": "No token found",
                "suggestion": "Run 'pixiv-downloader login' to login"
            }
            click.echo(json.dumps(error_data, ensure_ascii=False))
        else:
            console.print("[yellow]No token found.[/yellow]")
            console.print("[dim]Run 'pixiv-downloader login' to login.[/dim]")
        return

    # Load token
    token_data = storage.load_token()
    if not token_data:
        if ctx.obj.get("output_mode") == "json":
            error_data = {
                "logged_in": False,
                "token_valid": False,
                "username": None,
                "error": "Token file exists but cannot be decrypted",
                "suggestion": "Run 'pixiv-downloader login --force' to re-login"
            }
            click.echo(json.dumps(error_data, ensure_ascii=False))
        else:
            console.print(
                "[red]Token file exists but cannot be decrypted.[/red]"
            )
            console.print(
                "[dim]This may happen if machine info changed or file is corrupted.[/dim]"
            )
            console.print(
                "[dim]Run 'pixiv-downloader login --force' to re-login.[/dim]"
            )
        return

    refresh_token = token_data.get("refresh_token")
    if not refresh_token:
        if ctx.obj.get("output_mode") == "json":
            error_data = {
                "logged_in": False,
                "token_valid": False,
                "username": None,
                "error": "Invalid token data (missing refresh_token)"
            }
            click.echo(json.dumps(error_data, ensure_ascii=False))
        else:
            console.print(
                "[red]Invalid token data (missing refresh_token).[/red]"
            )
        return

    # Validate token
    if ctx.obj.get("output_mode") != "json":
        console.print("[dim]Validating token...[/dim]")

    result = PixivOAuth.validate_refresh_token(refresh_token)

    # JSON output mode
    if ctx.obj.get("output_mode") == "json":
        # 尝试从 token_data 中获取用户信息(向后兼容)
        stored_user = token_data.get("user")
        latest_user = result.get("user")

        # 优先使用最新的用户信息,否则使用存储的
        user_info = latest_user or stored_user

        status_data = {
            "logged_in": result["valid"],
            "token_valid": result["valid"],
        }

        # 添加用户信息(如果可用)
        if user_info:
            status_data["username"] = user_info.get("name")
            status_data["user_account"] = user_info.get("account")
            status_data["user_id"] = user_info.get("id")
        else:
            # 向后兼容: 旧 token 文件无用户信息
            status_data["username"] = None
            status_data["user_account"] = None
            status_data["user_id"] = None
            status_data["user_info_note"] = "User info not available. Re-login to capture user details."

        if not result["valid"]:
            status_data["error"] = result.get("error", "Unknown")
            status_data["suggestion"] = "Run 'pixiv-downloader login --force' to re-login"

        click.echo(json.dumps(status_data, ensure_ascii=False))

        # Still refresh token if valid (silently)
        if result["valid"] and result["refresh_token"]:
            storage.save_token(
                refresh_token=result["refresh_token"],
                access_token=result.get("access_token"),
                user=result.get("user"),  # 新增: 保存用户信息
            )
    else:
        # Rich table output mode (original code)
        table = Table(title="Token Status")
        table.add_column("Property", style="cyan")
        table.add_column("Value", style="green")

        if result["valid"]:
            table.add_row("Status", "[green]Valid[/green]")
            table.add_row("Token File", str(storage.storage_path))

            # 显示用户信息(如果可用)
            user_info = token_data.get("user") or result.get("user")
            if user_info:
                table.add_row("Username", user_info.get("name", "N/A"))
                table.add_row("User Account", user_info.get("account", "N/A"))
                table.add_row("User ID", user_info.get("id", "N/A"))

            if verbose:
                # Show partial token (privacy protection)
                masked_token = (
                    refresh_token[:10] + "..." + refresh_token[-10:]
                )
                table.add_row("Refresh Token", masked_token)

                if result.get("expires_in"):
                    expiry = datetime.datetime.now() + datetime.timedelta(
                        seconds=result["expires_in"]
                    )
                    table.add_row("Expires", expiry.strftime("%Y-%m-%d %H:%M:%S"))

            # If token is valid, update storage (auto-refresh)
            if result["refresh_token"]:
                storage.save_token(
                    refresh_token=result["refresh_token"],
                    access_token=result.get("access_token"),
                    user=result.get("user"),  # 新增: 保存用户信息
                )
                console.print("[dim]Token refreshed and saved.[/dim]")

        else:
            table.add_row("Status", "[red]Invalid[/red]")
            table.add_row("Error", result.get("error", "Unknown"))
            table.add_row(
                "Suggestion", "Run 'pixiv-downloader login --force' to re-login"
            )

        console.print(table)
