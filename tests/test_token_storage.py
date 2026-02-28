"""TokenStorage 测试套件

测试 Token 加密存储功能的各个方面。
"""

import json
import os
from pathlib import Path
from unittest.mock import patch

import pytest
from cryptography.fernet import Fernet

from gallery_dl_auto.auth.token_storage import (
    TokenStorage,
    _derive_machine_key,
    get_default_token_storage,
)


class TestDeriveMachineKey:
    """测试密钥生成逻辑"""

    def test_derive_machine_key_returns_bytes(self) -> None:
        """验证返回 bytes 类型"""
        key = _derive_machine_key()
        assert isinstance(key, bytes)

    def test_derive_machine_key_deterministic(self) -> None:
        """验证相同环境生成相同密钥"""
        key1 = _derive_machine_key()
        key2 = _derive_machine_key()
        assert key1 == key2

    def test_derive_machine_key_is_base64url(self) -> None:
        """验证是有效的 base64url 编码"""
        key = _derive_machine_key()
        # Fernet 密钥应该是 44 字节的 base64url 编码 (32 字节 * 4/3)
        assert len(key) == 44
        # 验证可以用于创建 Fernet 实例
        fernet = Fernet(key)
        assert fernet is not None

    @patch("gallery_dl_auto.auth.token_storage.socket.gethostname")
    @patch("gallery_dl_auto.auth.token_storage.os.getenv")
    def test_derive_machine_key_uses_env_vars(
        self, mock_getenv: pytest.MonkeyPatch, mock_gethostname: pytest.MonkeyPatch
    ) -> None:
        """验证密钥生成使用环境变量"""
        mock_gethostname.return_value = "test-host"
        mock_getenv.side_effect = lambda x: "test-user" if x in ("USERNAME", "USER") else None

        key = _derive_machine_key()
        assert isinstance(key, bytes)


class TestTokenStorage:
    """测试 Token 存储功能"""

    def test_save_and_load_token_success(self, tmp_path: Path) -> None:
        """测试保存并加载 token,验证数据一致"""
        storage = TokenStorage(tmp_path / "credentials.enc")

        refresh_token = "test-refresh-token-123"
        access_token = "test-access-token-456"

        # 保存 token
        storage.save_token(refresh_token, access_token)

        # 加载 token
        loaded = storage.load_token()

        assert loaded is not None
        assert loaded["refresh_token"] == refresh_token
        assert loaded["access_token"] == access_token

    def test_load_nonexistent_token_returns_none(self, tmp_path: Path) -> None:
        """测试加载不存在的文件返回 None"""
        storage = TokenStorage(tmp_path / "nonexistent.enc")
        result = storage.load_token()
        assert result is None

    def test_delete_token_removes_file(self, tmp_path: Path) -> None:
        """测试删除 token 文件"""
        storage = TokenStorage(tmp_path / "credentials.enc")

        # 保存 token
        storage.save_token("test-refresh-token")

        # 确认文件存在
        assert storage.storage_path.exists()

        # 删除 token
        storage.delete_token()

        # 确认文件不存在
        assert not storage.storage_path.exists()

    def test_save_token_creates_directory(self, tmp_path: Path) -> None:
        """测试保存时自动创建目录"""
        storage = TokenStorage(tmp_path / "subdir" / "credentials.enc")

        # 目录不应该存在
        assert not storage.storage_path.parent.exists()

        # 保存 token
        storage.save_token("test-refresh-token")

        # 目录应该被创建
        assert storage.storage_path.parent.exists()
        assert storage.storage_path.exists()

    def test_save_token_without_access_token(self, tmp_path: Path) -> None:
        """测试只保存 refresh token"""
        storage = TokenStorage(tmp_path / "credentials.enc")

        refresh_token = "test-refresh-token-only"
        storage.save_token(refresh_token)

        loaded = storage.load_token()
        assert loaded is not None
        assert loaded["refresh_token"] == refresh_token
        assert "access_token" not in loaded


class TestEncryption:
    """测试加密验证"""

    def test_encrypted_file_not_plaintext(self, tmp_path: Path) -> None:
        """验证文件内容不是明文"""
        storage = TokenStorage(tmp_path / "credentials.enc")

        refresh_token = "secret-token-123"
        storage.save_token(refresh_token)

        # 读取文件原始内容
        raw_content = storage.storage_path.read_bytes()

        # 验证不是明文
        assert refresh_token.encode("utf-8") not in raw_content
        # 验证是 Fernet token 格式 (以特定字节开头)
        assert raw_content.startswith(b"gAAAAAB")  # Fernet token 标识

    def test_different_keys_cannot_decrypt(self, tmp_path: Path) -> None:
        """验证密钥错误无法解密"""
        storage1 = TokenStorage(tmp_path / "credentials.enc")

        # 使用 storage1 保存 token
        refresh_token = "secret-token-123"
        storage1.save_token(refresh_token)

        # 使用不同密钥的 storage2 尝试加载
        with patch(
            "gallery_dl_auto.auth.token_storage._derive_machine_key",
            return_value=Fernet.generate_key(),
        ):
            storage2 = TokenStorage(tmp_path / "credentials.enc")
            result = storage2.load_token()

        # 解密应该失败并返回 None
        assert result is None


class TestErrorHandling:
    """测试错误处理"""

    def test_load_corrupted_file_returns_none(self, tmp_path: Path) -> None:
        """测试加载损坏文件返回 None"""
        storage = TokenStorage(tmp_path / "credentials.enc")

        # 写入损坏的数据
        storage.storage_path.parent.mkdir(parents=True, exist_ok=True)
        storage.storage_path.write_bytes(b"corrupted data")

        # 加载应该返回 None
        result = storage.load_token()
        assert result is None

    def test_load_invalid_json_returns_none(self, tmp_path: Path) -> None:
        """测试解密后不是有效 JSON 返回 None"""
        storage = TokenStorage(tmp_path / "credentials.enc")

        # 加密无效的 JSON 数据
        encrypted = storage.fernet.encrypt(b"not valid json")

        storage.storage_path.parent.mkdir(parents=True, exist_ok=True)
        storage.storage_path.write_bytes(encrypted)

        # 加载应该返回 None
        result = storage.load_token()
        assert result is None

    def test_delete_nonexistent_token_no_error(self, tmp_path: Path) -> None:
        """测试删除不存在的 token 不会出错"""
        storage = TokenStorage(tmp_path / "nonexistent.enc")

        # 删除不存在的文件应该静默处理
        storage.delete_token()

        # 确认没有异常
        assert not storage.storage_path.exists()


class TestFilePermissions:
    """测试文件权限 (Unix)"""

    @pytest.mark.skipif(
        os.name == "nt", reason="File permissions test only applicable on Unix"
    )
    def test_unix_file_permissions_600(self, tmp_path: Path) -> None:
        """验证 Unix 系统文件权限为 600"""
        storage = TokenStorage(tmp_path / "credentials.enc")
        storage.save_token("test-refresh-token")

        # 获取文件权限
        file_stat = storage.storage_path.stat()
        file_mode = oct(file_stat.st_mode)[-3:]

        # 验证权限为 600
        assert file_mode == "600"


class TestConvenienceFunctions:
    """测试便捷函数"""

    def test_get_default_token_storage(self) -> None:
        """测试获取默认 Token 存储实例"""
        storage = get_default_token_storage()

        assert isinstance(storage, TokenStorage)
        # 验证路径指向用户目录
        assert ".gallery-dl-auto" in str(storage.storage_path)
        assert storage.storage_path.name == "credentials.enc"
