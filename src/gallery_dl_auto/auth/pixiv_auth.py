"""
Pixiv OAuth authentication module.

This module implements the Pixiv OAuth login flow using PKCE.
"""

import logging
import webbrowser
from typing import Any

import requests
from rich.console import Console

from .oauth import (
    AUTH_URL,
    CLIENT_ID,
    CLIENT_SECRET,
    REDIRECT_URI,
    TOKEN_URL,
    OAuthError,
    generate_pkce_challenge,
    generate_pkce_verifier,
)

logger = logging.getLogger(__name__)
console = Console()


class PixivOAuth:
    """
    Pixiv OAuth authentication handler.

    Manages the complete OAuth PKCE login flow for Pixiv API access.
    """

    def __init__(self) -> None:
        """Initialize OAuth handler with PKCE parameters."""
        self.code_verifier = generate_pkce_verifier()
        self.code_challenge = generate_pkce_challenge(self.code_verifier)

    def login(self) -> dict[str, Any]:
        """
        Execute complete OAuth login flow.

        Opens browser for user authentication, waits for authorization code,
        and exchanges it for access/refresh tokens.

        Returns:
            Dictionary containing:
                - access_token: API access token
                - refresh_token: Long-lived refresh token
                - expires_in: Token expiration time in seconds
                - token_type: Token type (usually "Bearer")

        Raises:
            OAuthError: If login or token exchange fails
        """
        # Construct authorization URL with PKCE parameters
        # Note: Must include client=pixiv-android parameter
        auth_url = (
            f"{AUTH_URL}?"
            f"code_challenge={self.code_challenge}&"
            f"code_challenge_method=S256&"
            f"client=pixiv-android"
        )

        console.print("\n[bold cyan]Pixiv 自动化登录流程[/bold cyan]")
        console.print("[dim]将自动打开浏览器并捕获授权码[/dim]")

        # Wait for callback (automated via Playwright)
        code = self._wait_for_callback()

        # Exchange code for tokens
        tokens = self._exchange_token(code)

        console.print("[bold green]✓ 登录成功![/bold green]")
        logger.info("OAuth login successful")

        return tokens

    def _wait_for_callback(self) -> str:
        """
        Wait for OAuth callback and extract authorization code.

        First tries Playwright automation, falls back to manual input if failed.

        Returns:
            Authorization code string

        Raises:
            OAuthError: If code is not captured
        """
        # Try automated Playwright approach first
        try:
            return self._wait_for_callback_playwright()
        except Exception as e:
            logger.warning(f"Playwright automation failed: {e}")
            console.print(f"\n[yellow]⚠ 自动化登录失败,切换到手动模式[/yellow]")
            console.print("[dim]请按照提示手动获取授权码[/dim]\n")
            return self._wait_for_callback_manual()

    def _wait_for_callback_manual(self) -> str:
        """
        Manual fallback: prompt user to input authorization code.

        Returns:
            Authorization code string
        """
        from rich.prompt import Prompt

        console.print(
            "\n[bold yellow]重要提示: 登录后需要获取授权码[/bold yellow]"
        )
        console.print("\n[bold]方法 1: 使用开发者工具 (推荐)[/bold]")
        console.print("1. 在浏览器中打开登录页面并完成登录")
        console.print("2. 按 [cyan]F12[/cyan] 打开开发者工具")
        console.print("3. 切换到 [cyan]Network[/cyan] (网络) 标签")
        console.print("4. 勾选 [cyan]Preserve log[/cyan] (保留日志)")
        console.print("5. 在过滤框中输入: [cyan]callback?[/cyan]")
        console.print("6. 会看到一个请求 URL 类似:")
        console.print("   [dim]https://app-api.pixiv.net/.../callback?state=...&code=...[/dim]")
        console.print("7. 复制完整 URL 或只复制 code 值\n")

        user_input = Prompt.ask("[cyan]请粘贴 URL 或 code 值[/cyan]")

        # Extract code from URL or use directly
        if "code=" in user_input:
            import urllib.parse
            parsed = urllib.parse.urlparse(user_input)
            params = urllib.parse.parse_qs(parsed.query)
            if "code" in params:
                code = params["code"][0]
                logger.debug("Extracted authorization code from URL")
                console.print("[green]✓ 成功提取授权码[/green]\n")
                return code
            else:
                raise OAuthError("URL 中未找到 code 参数")
        else:
            code = user_input.strip()
            if not code:
                raise OAuthError("未提供授权码")
            logger.debug("Using authorization code from direct input")
            console.print("[green]✓ 接收到授权码[/green]\n")
            return code

    def _wait_for_callback_playwright(self) -> str:
        """
        Automated approach: use Playwright to capture authorization code.

        Returns:
            Authorization code string

        Raises:
            OAuthError: If automation fails
        """
        try:
            from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout
        except ImportError:
            raise OAuthError("Playwright 未安装")

        auth_url = (
            f"{AUTH_URL}?"
            f"code_challenge={self.code_challenge}&"
            f"code_challenge_method=S256&"
            f"client=pixiv-android"
        )

        console.print("\n[bold cyan]正在启动自动化浏览器...[/bold cyan]")
        console.print("[dim]请在打开的浏览器窗口中完成登录[/dim]")
        console.print("[dim]程序将自动检测登录成功并捕获授权码[/dim]\n")

        captured_code = None

        try:
            with sync_playwright() as p:
                # Launch browser with anti-detection settings
                browser = p.chromium.launch(
                    headless=False,
                    args=[
                        '--disable-blink-features=AutomationControlled',
                        '--disable-features=IsolateOrigins,site-per-process',
                    ]
                )
                context = browser.new_context(
                    user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                    viewport={'width': 1280, 'height': 720}
                )
                page = context.new_page()

                # Listen for navigation events to capture callback URL
                def handle_request(request):
                    nonlocal captured_code
                    url = request.url

                    # Check if this is the callback URL with code parameter
                    if 'callback' in url and 'code=' in url:
                        logger.debug(f"Captured callback URL: {url}")
                        import urllib.parse
                        parsed = urllib.parse.urlparse(url)
                        params = urllib.parse.parse_qs(parsed.query)

                        if 'code' in params:
                            captured_code = params['code'][0]
                            logger.info("Successfully captured authorization code")
                            console.print("\n[green]✓ 登录成功!已自动捕获授权码[/green]\n")
                            # Don't close browser here - set flag and let main loop handle it

                page.on('request', handle_request)

                # Navigate to login page with more lenient wait strategy
                console.print("[dim]正在打开登录页面...[/dim]")
                try:
                    page.goto(auth_url, wait_until='domcontentloaded', timeout=60000)
                except PlaywrightTimeout:
                    # If timeout, the page might still be loading, that's OK
                    logger.debug("Page load timeout, but continuing...")
                    pass

                # Wait for navigation to callback (no timeout limit as per user requirement)
                console.print("[bold yellow]等待登录...[/bold yellow]")
                console.print("[dim](无超时限制,请按照正常速度完成登录)[/dim]\n")

                try:
                    # Poll for captured code
                    import time
                    while not captured_code:
                        page.wait_for_timeout(100)  # Check every 100ms
                        time.sleep(0.1)
                except Exception:
                    # Browser was closed by user, that's OK
                    pass
                finally:
                    # Clean close
                    try:
                        browser.close()
                    except:
                        pass

        except Exception as e:
            logger.error(f"Playwright automation failed: {e}")
            raise OAuthError(f"浏览器自动化失败: {e}")

        if not captured_code:
            raise OAuthError("未能捕获授权码,登录可能未完成或浏览器被提前关闭")

        return captured_code

    def _exchange_token(self, code: str) -> dict[str, Any]:
        """
        Exchange authorization code for access/refresh tokens.

        Makes POST request to Pixiv token endpoint with PKCE verifier.

        Args:
            code: Authorization code from callback

        Returns:
            Token response dictionary

        Raises:
            OAuthError: If token exchange fails
        """
        logger.debug("Exchanging authorization code for tokens")
        logger.debug(f"Code: {code[:20]}...")
        logger.debug(f"Code verifier: {self.code_verifier[:20]}...")

        headers = {
            "User-Agent": "PixivAndroidApp/5.0.234 (Android 11; Pixel 5)",
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
        }

        data = {
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "code": code,
            "code_verifier": self.code_verifier,
            "grant_type": "authorization_code",
            "include_policy": "true",
            "redirect_uri": REDIRECT_URI,
        }

        # Log request data (escape special chars for Rich)
        import json
        logger.debug(f"Token exchange request data: {json.dumps(data, indent=2)}")

        try:
            response = requests.post(TOKEN_URL, data=data, headers=headers, timeout=30)
            logger.debug(f"Token exchange response status: {response.status_code}")
            logger.debug(f"Token exchange response: {response.text[:500]}")

            # Check for non-200 status codes
            if response.status_code != 200:
                logger.error(f"Token exchange failed with status {response.status_code}")
                logger.error(f"Response body: {response.text}")

                # Try to parse error
                try:
                    error_data = response.json()
                    error_msg = f"Token 交换失败 (HTTP {response.status_code})"
                    if "error" in error_data:
                        error_msg = f"{error_msg}: {error_data['error']}"
                    if "error_description" in error_data:
                        error_msg = f"{error_msg} - {error_data['error_description']}"
                    raise OAuthError(error_msg, response.status_code)
                except ValueError:
                    # Can't parse JSON, use raw text
                    raise OAuthError(f"Token 交换失败 (HTTP {response.status_code}): {response.text[:200]}", response.status_code)

            response.raise_for_status()
        except requests.exceptions.Timeout:
            logger.error("Token exchange request timed out")
            raise OAuthError("网络请求超时,请检查网络连接")
        except requests.exceptions.ConnectionError as e:
            logger.error(f"Network error during token exchange: {e}")
            raise OAuthError(f"网络连接失败: {e}")
        except OAuthError:
            # Re-raise OAuthError as-is
            raise
        except requests.exceptions.HTTPError as e:
            status_code = e.response.status_code if e.response else None
            error_msg = "Token 交换失败"

            # Try to extract error details from response
            if e.response:
                try:
                    error_data = e.response.json()
                    logger.error(f"Token exchange error response: {error_data}")
                    if "error" in error_data:
                        error_msg = f"{error_msg}: {error_data['error']}"
                    if "error_description" in error_data:
                        error_msg = f"{error_msg} - {error_data['error_description']}"
                except Exception as parse_error:
                    logger.error(f"Failed to parse error response: {parse_error}")
                    logger.error(f"Raw response text: {e.response.text}")

            logger.error(f"HTTP error {status_code}: {error_msg}")
            raise OAuthError(error_msg, status_code)
        except requests.exceptions.RequestException as e:
            logger.error(f"Request error during token exchange: {e}")
            raise OAuthError(f"请求失败: {e}")

        # Parse response
        try:
            token_data = response.json()
        except ValueError as e:
            logger.error(f"Failed to parse token response: {e}")
            raise OAuthError("服务器响应格式错误")

        # Validate response contains required fields
        required_fields = ["access_token", "refresh_token"]
        for field in required_fields:
            if field not in token_data:
                logger.error(f"Token response missing required field: {field}")
                raise OAuthError(f"服务器响应缺少必需字段: {field}")

        logger.info(
            f"Token exchange successful, expires in {token_data.get('expires_in', 'unknown')} seconds"
        )
        return token_data

    def refresh_tokens(self, refresh_token: str) -> dict[str, Any]:
        """
        Refresh access token using refresh token.

        Args:
            refresh_token: Valid refresh token

        Returns:
            New token response dictionary

        Raises:
            OAuthError: If token refresh fails
        """
        logger.debug("Refreshing access token")

        headers = {
            "User-Agent": "PixivAndroidApp/5.0.234 (Android 11; Pixel 5)",
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json",
        }

        data = {
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "grant_type": "refresh_token",
            "include_policy": "true",
            "refresh_token": refresh_token,
        }

        try:
            response = requests.post(TOKEN_URL, data=data, headers=headers, timeout=30)
            response.raise_for_status()
        except requests.exceptions.HTTPError as e:
            status_code = e.response.status_code if e.response else None
            logger.error(f"Token refresh failed with status {status_code}")
            raise OAuthError("Token 刷新失败,可能需要重新登录", status_code)
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error during token refresh: {e}")
            raise OAuthError(f"网络请求失败: {e}")

        try:
            token_data = response.json()
        except ValueError as e:
            logger.error(f"Failed to parse refresh response: {e}")
            raise OAuthError("服务器响应格式错误")

        logger.info("Token refresh successful")
        return token_data

    @staticmethod
    def validate_refresh_token(refresh_token: str) -> dict[str, Any]:
        """验证 refresh_token 是否有效,返回 token 信息

        Args:
            refresh_token: 要验证的 refresh token

        Returns:
            dict: {
                'valid': bool,
                'access_token': str | None,
                'refresh_token': str | None,
                'expires_in': int | None,
                'user': dict | None,  # 用户信息 (name, account, id)
                'error': str | None
            }
        """
        try:
            response = requests.post(
                TOKEN_URL,
                data={
                    "client_id": CLIENT_ID,
                    "client_secret": CLIENT_SECRET,
                    "grant_type": "refresh_token",
                    "include_policy": "true",
                    "refresh_token": refresh_token,
                },
                headers={
                    "User-Agent": "PixivAndroidApp/5.0.234 (Android 11; Pixel 5)",
                    "Content-Type": "application/x-www-form-urlencoded",
                    "Accept": "application/json",
                },
                timeout=30,
            )

            if response.status_code == 200:
                data = response.json()
                return {
                    "valid": True,
                    "access_token": data["access_token"],
                    "refresh_token": data["refresh_token"],
                    "expires_in": data.get("expires_in", 3600),
                    "user": data.get("user"),  # 新增: 提取用户信息
                    "error": None,
                }
            else:
                error_data = response.json()
                return {
                    "valid": False,
                    "access_token": None,
                    "refresh_token": None,
                    "expires_in": None,
                    "user": None,  # 新增: 失败时无用户信息
                    "error": error_data.get("error", "Unknown error"),
                }
        except Exception as e:
            return {
                "valid": False,
                "access_token": None,
                "refresh_token": None,
                "expires_in": None,
                "user": None,  # 新增: 异常时无用户信息
                "error": str(e),
            }
