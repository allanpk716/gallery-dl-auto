"""Login command implementation

Implements the 'pixiv-downloader login' command for OAuth authentication.
"""

import logging

import click
from rich.console import Console

from gallery_dl_auto.auth.pixiv_auth import PixivOAuth
from gallery_dl_auto.auth.token_storage import get_default_token_storage

logger = logging.getLogger("gallery_dl_auto")


@click.command()
@click.option("--force", is_flag=True, help="Force re-login even if token exists")
def login(force: bool) -> None:
    """Login to Pixiv and save refresh token

    [IMPORTANT] This command MUST be executed by a human user.

    AI/LLM Agents CANNOT automatically complete the login process because:
    - Requires browser interaction and user verification
    - Needs human to enter credentials in the browser
    - Cannot be automated via CLI or API

    \b
    This command will:
    1. Open browser for Pixiv login
    2. Wait for human to complete login
    3. Automatically capture refresh token
    4. Encrypt and save token to ~/.gallery-dl-auto/credentials.enc

    \b
    When to use:
    - First-time setup (required before any download)
    - When token expired or invalid (check with 'pixiv-downloader status')
    - Use --force flag to force refresh
    """
    console = Console()
    storage = get_default_token_storage()

    # Check existing token
    if not force:
        existing = storage.load_token()
        if existing and existing.get("refresh_token"):
            console.print(
                "[yellow]Token already exists. Use --force to re-login.[/yellow]"
            )
            console.print(
                "[dim]Current token status: Use 'pixiv-downloader status' to check[/dim]"
            )
            return

    # Execute login flow
    try:
        console.print("[bold cyan]Starting Pixiv login...[/bold cyan]")
        console.print(
            "[dim]A browser window will open for you to login.[/dim]"
        )
        console.print(
            "[dim]Please complete the login process in the browser.[/dim]"
        )
        console.print(
            "[dim]The program will automatically detect when login is successful.[/dim]"
        )
        console.print()

        oauth = PixivOAuth()
        tokens = oauth.login()

        # Save token
        storage.save_token(
            refresh_token=tokens["refresh_token"],
            access_token=tokens.get("access_token"),
            user=tokens.get("user"),  # 新增: 保存用户信息
        )

        console.print()
        console.print("[bold green]Login successful![/bold green]")
        console.print(f"[dim]Token saved to: {storage.storage_path}[/dim]")
        console.print("[dim]Token is encrypted and secure.[/dim]")

    except Exception as e:
        logger.error(f"Login failed: {e}")
        console.print(f"[bold red]Login failed:[/bold red] {e}")
        console.print(
            "[dim]Please try again. If the problem persists, check your network connection.[/dim]"
        )
        raise click.Abort()
