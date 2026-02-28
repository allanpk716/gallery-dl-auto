"""Token 加密存储模块

使用 Fernet 对称加密保护 refresh token,密钥基于机器信息自动生成。
"""

import base64
import hashlib
import json
import logging
import os
import platform
import socket
from pathlib import Path
from typing import Optional

from cryptography.fernet import Fernet

logger = logging.getLogger("gallery_dl_auto")


def _derive_machine_key() -> bytes:
    """基于机器唯一信息派生 Fernet 密钥

    使用 hostname、username 和 machine_id 组合生成 32 字节密钥,
    并编码为 Fernet 要求的 base64url 格式。

    Returns:
        bytes: base64url 编码的 32 字节 Fernet 密钥
    """
    # 收集机器标识
    hostname = socket.gethostname()
    username = os.getenv("USERNAME") or os.getenv("USER") or "unknown"
    machine_id = hostname  # 简化实现,使用 hostname 作为 machine_id

    # 组合并哈希生成 32 字节密钥
    seed = f"{hostname}:{username}:{machine_id}".encode("utf-8")
    key_bytes = hashlib.sha256(seed).digest()

    # Fernet 要求 base64url 编码的 32 字节密钥
    return base64.urlsafe_b64encode(key_bytes)


class TokenStorage:
    """Token 加密存储管理类

    使用 Fernet 对称加密算法保护 token 数据,密钥基于机器信息自动派生。
    支持加密保存、解密加载和删除 token 操作。
    """

    def __init__(self, storage_path: Path) -> None:
        """初始化 Token 存储

        Args:
            storage_path: token 文件的存储路径
        """
        self.storage_path = Path(storage_path)
        self.key = _derive_machine_key()
        self.fernet = Fernet(self.key)

    def save_token(
        self,
        refresh_token: str,
        access_token: Optional[str] = None,
        user: Optional[dict] = None  # 新增: 用户信息字段
    ) -> None:
        """加密并保存 token 到文件

        将 token 数据加密后写入文件,并在 Unix 系统上设置文件权限为 600。

        Args:
            refresh_token: refresh token 字符串
            access_token: 可选的 access token 字符串
            user: 可选的用户信息字典,包含 id/name/account 字段
        """
        # 构造数据字典
        data = {"refresh_token": refresh_token}
        if access_token:
            data["access_token"] = access_token
        if user:  # 新增: 包含用户信息
            data["user"] = user

        # 加密
        encrypted = self.fernet.encrypt(json.dumps(data).encode("utf-8"))

        # 确保目录存在
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)

        # 写入文件
        self.storage_path.write_bytes(encrypted)

        # 设置文件权限 (Unix: 600, Windows: 跳过)
        if platform.system() != "Windows":
            try:
                os.chmod(self.storage_path, 0o600)
            except OSError as e:
                logger.warning(f"Failed to set file permissions: {e}")
        # Windows: 用户目录权限已足够

    def load_token(self) -> Optional[dict]:
        """解密并加载 token

        从文件读取加密的 token 数据并解密。

        Returns:
            dict | None: 解密后的 token 字典,包含 'refresh_token' 和可选的 'access_token';
                         如果文件不存在或解密失败则返回 None
        """
        if not self.storage_path.exists():
            return None

        try:
            encrypted = self.storage_path.read_bytes()
            decrypted = self.fernet.decrypt(encrypted)
            return json.loads(decrypted)  # type: ignore
        except Exception as e:
            # 解密失败 (密钥变化、文件损坏等)
            logger.error(f"Failed to decrypt token: {e}")
            return None

    def delete_token(self) -> None:
        """删除 token 文件

        如果 token 文件存在则删除。
        """
        if self.storage_path.exists():
            try:
                self.storage_path.unlink()
            except OSError as e:
                logger.error(f"Failed to delete token file: {e}")


def get_default_token_storage() -> TokenStorage:
    """获取默认的 Token 存储实例

    使用默认的凭证文件路径创建 TokenStorage 实例。

    Returns:
        TokenStorage: 配置了默认路径的 Token 存储实例
    """
    from gallery_dl_auto.config.paths import CREDENTIALS_FILE

    return TokenStorage(CREDENTIALS_FILE)
