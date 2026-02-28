"""Logout command implementation

Implements the 'pixiv-downloader logout' command for removing saved tokens.
"""

import click
from rich.console import Console

from gallery_dl_auto.auth.token_storage import get_default_token_storage


@click.command()
def logout() -> None:
    """Logout from Pixiv and delete saved token

    This will remove the encrypted token file from ~/.gallery-dl-auto/credentials.enc
    """
    console = Console()
    storage = get_default_token_storage()

    # Check if token exists
    if not storage.storage_path.exists():
        console.print("[yellow]No token found. Already logged out.[/yellow]")
        return

    # Confirm deletion
    if not click.confirm("Are you sure you want to logout?"):
        console.print("[dim]Logout cancelled.[/dim]")
        return

    # Delete token
    try:
        storage.delete_token()
        console.print("[bold green]Logged out successfully![/bold green]")
        console.print("[dim]Token file has been removed.[/dim]")
        console.print("[dim]Run 'pixiv-downloader login' to login again.[/dim]")
    except Exception as e:
        console.print(f"[bold red]Logout failed:[/bold red] {e}")
        raise click.Abort()
