"""统一 Mode 转换器

集中管理所有排行榜 mode 的映射和验证。
"""

from typing import TypedDict

from gallery_dl_auto.core.mode_errors import InvalidModeError


class ModeDefinition(TypedDict):
    """Mode 定义

    定义了一个 mode 在不同层次的名称。

    Attributes:
        api_name: Pixiv API 使用的 mode 名称
        gallery_dl_name: Gallery-dl URL 使用的 mode 名称
        description: 该 mode 的描述和用途
    """

    api_name: str
    gallery_dl_name: str
    description: str


class ModeManager:
    """统一 Mode 管理器

    作为 mode 映射的唯一权威来源（Single Source of Truth）。
    集中管理所有排行榜 mode 的名称转换和验证。

    Example:
        >>> # API mode 转为 gallery-dl mode
        >>> ModeManager.api_to_gallery_dl("day_male_r18")
        'male_r18'

        >>> # 验证 mode 是否有效
        >>> ModeManager.validate_api_mode("day")
        'day'
    """

    # Mode 定义注册表（按 API name 索引）
    # 基于 gallery-dl 源码 resource画廊-dl/extractor/pixiv.py:705-724
    MODES: dict[str, ModeDefinition] = {
        # 基础排行榜
        "day": {
            "api_name": "day",
            "gallery_dl_name": "daily",
            "description": "每日排行榜",
        },
        "week": {
            "api_name": "week",
            "gallery_dl_name": "weekly",
            "description": "每周排行榜",
        },
        "month": {
            "api_name": "month",
            "gallery_dl_name": "monthly",
            "description": "每月排行榜",
        },
        # 分类排行榜
        "day_male": {
            "api_name": "day_male",
            "gallery_dl_name": "male",
            "description": "男性热门",
        },
        "day_female": {
            "api_name": "day_female",
            "gallery_dl_name": "female",
            "description": "女性热门",
        },
        "week_original": {
            "api_name": "week_original",
            "gallery_dl_name": "original",
            "description": "原创作品",
        },
        "week_rookie": {
            "api_name": "week_rookie",
            "gallery_dl_name": "rookie",
            "description": "新人作品",
        },
        # R18 排行榜
        "day_r18": {
            "api_name": "day_r18",
            "gallery_dl_name": "daily_r18",
            "description": "每日 R18",
        },
        "day_male_r18": {
            "api_name": "day_male_r18",
            "gallery_dl_name": "male_r18",  # ★ 核心关键修复
            "description": "男性热门 R18",
        },
        "day_female_r18": {
            "api_name": "day_female_r18",
            "gallery_dl_name": "female_r18",
            "description": "女性热门 R18",
        },
        "week_r18": {
            "api_name": "week_r18",
            "gallery_dl_name": "weekly_r18",
            "description": "每周 R18",
        },
        "week_r18g": {
            "api_name": "week_r18g",
            "gallery_dl_name": "r18g",
            "description": "R18G",
        },
    }

    @classmethod
    def api_to_gallery_dl(cls, api_mode: str) -> str:
        """转换 API mode 为 gallery-dl URL mode

        将 Pixiv API 使用的 mode 名称转换为 gallery-dl URL 中使用的 mode 名称。

        Args:
            api_mode: Pixiv API 格式的 mode（如 "day_male_r18"）

        Returns:
            gallery-dl URL 格式的 mode（如 "male_r18"）

        Raises:
            InvalidModeError: mode 不在支持列表中

        Example:
            >>> ModeManager.api_to_gallery_dl("day")
            'daily'

            >>> ModeManager.api_to_gallery_dl("day_male_r18")
            'male_r18'
        """
        if api_mode not in cls.MODES:
            valid_modes = list(cls.MODES.keys())
            raise InvalidModeError(api_mode, valid_modes)

        return cls.MODES[api_mode]["gallery_dl_name"]

    @classmethod
    def validate_api_mode(cls, api_mode: str) -> str:
        """验证 API mode 的有效性

        检查传入的 mode 是否在支持列表中。

        Args:
            api_mode: 待验证的 API mode

        Returns:
            验证通过后的 API mode（原样返回）

        Raises:
            InvalidModeError: mode 无效

        Example:
            >>> ModeManager.validate_api_mode("day")
            'day'

            >>> ModeManager.validate_api_mode("invalid")
            InvalidModeError: Invalid mode 'invalid'. Valid modes: ...
        """
        if api_mode not in cls.MODES:
            valid_modes = list(cls.MODES.keys())
            raise InvalidModeError(api_mode, valid_modes)

        return api_mode

    @classmethod
    def cli_to_api(cls, cli_mode: str) -> str:
        """转换 CLI mode 为 API mode

        将用户输入的 CLI mode 转换为 Pixiv API 使用的 mode。
        支持两种输入：
        1. CLI 友好名称（如 "daily", "weekly"）
        2. API 名称（如 "day", "week"）- 向后兼容

        Args:
            cli_mode: CLI 输入的 mode（可以是友好名称或 API 名称）

        Returns:
            API mode 名称

        Raises:
            InvalidModeError: mode 无效

        Example:
            >>> # CLI 友好名称
            >>> ModeManager.cli_to_api("daily")
            'day'

            >>> # API 名称（向后兼容）
            >>> ModeManager.cli_to_api("day")
            'day'
        """
        # CLI 友好名称到 API 名称的映射
        cli_to_api_map = {
            "daily": "day",
            "weekly": "week",
            "monthly": "month",
            "male": "day_male",
            "female": "day_female",
            "original": "week_original",
            "rookie": "week_rookie",
            "daily_r18": "day_r18",
            "male_r18": "day_male_r18",
            "female_r18": "day_female_r18",
            "weekly_r18": "week_r18",
            "r18g": "week_r18g",
        }

        # 先尝试 CLI 友好名称
        if cli_mode in cli_to_api_map:
            return cli_to_api_map[cli_mode]

        # 再尝试 API 名称（向后兼容）
        if cli_mode in cls.MODES:
            return cli_mode

        # 都不匹配，报错
        valid_modes = list(cli_to_api_map.keys()) + list(cls.MODES.keys())
        raise InvalidModeError(cli_mode, valid_modes)

    @classmethod
    def get_all_cli_modes(cls) -> list[str]:
        """获取所有支持的 CLI mode 名称

        返回所有可用的 CLI 友好名称，用于帮助信息和错误提示。

        Returns:
            CLI mode 名称列表（排序后）

        Example:
            >>> ModeManager.get_all_cli_modes()
            ['daily', 'weekly', 'monthly', 'male', 'female', ...]
        """
        return sorted([
            "daily", "weekly", "monthly",
            "male", "female", "original", "rookie",
            "daily_r18", "male_r18", "female_r18", "weekly_r18", "r18g",
        ])
