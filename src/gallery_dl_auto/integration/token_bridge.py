"""Gallery-dl Token 桥接模块

负责从 token_storage 读取 token 并传递给 gallery-dl。
"""

import logging
from pathlib import Path
from typing import Optional

from gallery_dl_auto.auth.token_storage import TokenStorage

logger = logging.getLogger("gallery_dl_auto")


class TokenBridge:
    """Token 桥接类

    从 token_storage 读取 refresh token,并提供给 gallery-dl 使用。
    """

    def __init__(self, token_storage: TokenStorage):
        """初始化 Token 桥接

        Args:
            token_storage: Token 存储实例
        """
        self.token_storage = token_storage

    def get_refresh_token(self) -> Optional[str]:
        """获取 refresh token

        Returns:
            str | None: refresh token 字符串,如果不存在则返回 None
        """
        token_data = self.token_storage.load_token()

        if not token_data:
            logger.error("Token 数据不存在")
            return None

        refresh_token = token_data.get("refresh_token")
        if not refresh_token:
            logger.error("Token 数据中缺少 refresh_token")
            return None

        return refresh_token

    def create_gallery_dl_config(
        self, output_dir: Path, path_template: Optional[str] = None
    ) -> dict:
        """创建 gallery-dl 配置

        生成 gallery-dl 可以使用的配置字典。

        Args:
            output_dir: 下载目录
            path_template: 路径模板 (可选)

        Returns:
            dict: gallery-dl 配置字典
        """
        config = {
            "extractor": {
                "pixiv": {
                    "refresh-token": self.get_refresh_token(),
                    # 目录和文件名格式
                    "directory": [str(output_dir)],
                    "filename": path_template or "{rank}-{title}-{id}.{extension}",
                }
            },
            "output": {
                "mode": "stdio",  # 使用标准输出模式,方便解析
                "loglevel": "info",
            },
        }

        return config
