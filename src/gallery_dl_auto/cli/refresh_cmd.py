"""Refresh command implementation

Implements the 'pixiv-downloader refresh' command for manually refreshing tokens.
"""

import sys

import click

from gallery_dl_auto.auth.pixiv_auth import PixivOAuth
from gallery_dl_auto.auth.token_storage import get_default_token_storage
from gallery_dl_auto.models.output import (
    ErrorDetail,
    RefreshOutput,
    RefreshSuccessData,
)
from gallery_dl_auto.utils.error_codes import ErrorCode


def mask_token(token: str, prefix_len: int = 10, suffix_len: int = 10) -> str:
    """Mask the middle part of a token, showing only prefix and suffix.

    Args:
        token: Complete token string
        prefix_len: Number of characters to show at the start (default 10)
        suffix_len: Number of characters to show at the end (default 10)

    Returns:
        Masked token (e.g., "abc...xyz")
    """
    if len(token) <= prefix_len + suffix_len:
        # Token is too short, show less
        if len(token) > 10:
            return token[:5] + "..." + token[-5:]
        return token

    return token[:prefix_len] + "..." + token[-suffix_len:]


@click.command()
def refresh() -> None:
    """Refresh Pixiv token

    Refreshes the stored refresh token and saves the new token.
    Outputs result in JSON format for third-party integration.
    """
    storage = get_default_token_storage()

    # 1. Load token
    token_data = storage.load_token()
    if not token_data or not token_data.get("refresh_token"):
        error_output = RefreshOutput(
            success=False,
            error=ErrorDetail(
                code=ErrorCode.AUTH_TOKEN_NOT_FOUND,
                message="No token found. Run 'pixiv-downloader login' first.",
                details=None
            )
        )
        print(error_output.to_json())
        sys.exit(1)

    refresh_token = token_data.get("refresh_token")

    # 2. Refresh token
    try:
        result = PixivOAuth.validate_refresh_token(refresh_token)

        if not result["valid"]:
            # Refresh failed
            error_msg = result.get("error", "Unknown error")
            suggestion = "Run 'pixiv-downloader login' to re-login."
            error_output = RefreshOutput(
                success=False,
                error=ErrorDetail(
                    code=ErrorCode.AUTH_REFRESH_FAILED,
                    message=f"{error_msg} {suggestion}",
                    details=None
                )
            )
            print(error_output.to_json())
            sys.exit(1)

        # Save new token
        storage.save_token(
            refresh_token=result["refresh_token"],
            access_token=result.get("access_token"),
            user=result.get("user"),  # 新增: 保存用户信息
        )

        # Output success JSON
        success_data = RefreshSuccessData(
            old_token_masked=mask_token(refresh_token),
            new_token_masked=mask_token(result["refresh_token"]),
            expires_in_days=30  # Pixiv token 有效期约 30 天
        )

        output = RefreshOutput(success=True, data=success_data)
        print(output.to_json())
        sys.exit(0)

    except Exception as e:
        error_output = RefreshOutput(
            success=False,
            error=ErrorDetail(
                code=ErrorCode.INTERNAL_ERROR,
                message=f"Unexpected error: {e}",
                details={"exception_type": type(e).__name__}
            )
        )
        print(error_output.to_json())
        sys.exit(1)
