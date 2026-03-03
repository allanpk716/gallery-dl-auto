"""测试数据常量

提供测试中使用的常量数据，包括排行榜类型、日期格式、测试 Token 等。
"""

from typing import Final


class TestData:
    """测试数据常量集合

    集中管理所有测试中使用的常量数据，确保数据一致性和可维护性。
    """

    # ==================== 排行榜类型 ====================

    # API 使用的排行榜模式名称
    RANKING_MODES_API: Final[list[str]] = [
        "day",
        "week",
        "month",
        "day_male",
        "day_female",
        "week_original",
        "week_rookie",
        "day_r18",
        "day_male_r18",
        "day_female_r18",
        "week_r18",
        "week_r18g",
    ]

    # CLI 友好名称
    RANKING_MODES_CLI: Final[list[str]] = [
        "daily",
        "weekly",
        "monthly",
        "male",
        "female",
        "original",
        "rookie",
        "daily_r18",
        "male_r18",
        "female_r18",
        "weekly_r18",
        "r18g",
    ]

    # CLI 名称到 API 名称的映射
    CLI_TO_API_MAP: Final[dict[str, str]] = {
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

    # 基础排行榜类型（非 R18）
    BASIC_RANKING_MODES: Final[list[str]] = [
        "day",
        "week",
        "month",
    ]

    # 分类排行榜类型
    CATEGORY_RANKING_MODES: Final[list[str]] = [
        "day_male",
        "day_female",
        "week_original",
        "week_rookie",
    ]

    # R18 排行榜类型
    R18_RANKING_MODES: Final[list[str]] = [
        "day_r18",
        "day_male_r18",
        "day_female_r18",
        "week_r18",
        "week_r18g",
    ]

    # ==================== 日期相关 ====================

    # 有效的测试日期
    VALID_DATES: Final[list[str]] = [
        "2026-02-24",
        "2026-02-25",
        "2026-02-26",
        "2026-03-01",
        "2026-03-02",
    ]

    # 无效的日期格式（用于验证测试）
    INVALID_DATE_FORMATS: Final[list[str]] = [
        "2026/02/24",  # 错误的分隔符
        "24-02-2026",  # 错误的顺序
        "20260224",    # 缺少分隔符
        "2026-2-24",   # 月份缺少前导零
        "2026-02-2",   # 日期缺少前导零
    ]

    # 未来日期（应该被拒绝）
    FUTURE_DATES: Final[list[str]] = [
        "2030-01-01",
        "2027-12-31",
    ]

    # ==================== Token 相关 ====================

    # 测试用的 refresh token（格式正确但不是真实 token）
    VALID_REFRESH_TOKEN: Final[str] = (
        "1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef"
    )

    # 另一个测试 token（用于多用户测试）
    ALT_REFRESH_TOKEN: Final[str] = (
        "abcdef1234567890abcdef1234567890abcdef1234567890abcdef1234567890"
    )

    # 无效的 token 格式
    INVALID_TOKENS: Final[list[str]] = [
        "",
        "short",
        "invalid-token-format",
        "123",  # 太短
    ]

    # ==================== 作品相关 ====================

    # 测试用的作品 ID
    TEST_ILLUST_IDS: Final[list[int]] = [
        12345678,
        23456789,
        34567890,
        99999999,
        100000001,
    ]

    # 测试用的作者信息
    TEST_AUTHORS: Final[list[dict[str, int | str]]] = [
        {"id": 11111111, "name": "TestArtist1"},
        {"id": 22222222, "name": "TestArtist2"},
        {"id": 33333333, "name": "测试作者3"},  # 包含中文
    ]

    # 测试用的作品标题
    TEST_TITLES: Final[list[str]] = [
        "Test Artwork",
        "Beautiful Landscape",
        "美丽的风景",  # 中文标题
        "Portrait Study #1",
        "作品タイトル",  # 日文标题
    ]

    # ==================== URL 相关 ====================

    # 测试用的图片 URL
    TEST_IMAGE_URLS: Final[list[str]] = [
        "https://i.pximg.net/img-original/img/2026/02/24/00/00/00/12345678_p0.jpg",
        "https://i.pximg.net/img-original/img/2026/02/25/12/30/45/23456789_p0.png",
        "https://i.pximg.net/c/600x1200_90/img-master/img/2026/02/26/08/15/30/34567890_p0_master1200.jpg",
    ]

    # ==================== 文件路径相关 ====================

    # 测试用的下载目录
    TEST_DOWNLOAD_DIR: Final[str] = "./pixiv-downloads"

    # 测试用的配置文件路径
    TEST_CONFIG_PATH: Final[str] = "./config/test-config.yaml"

    # ==================== 统计数据相关 ====================

    # 测试用的统计数据
    TEST_STATISTICS: Final[list[dict[str, int]]] = [
        {"bookmarks": 1000, "views": 5000, "comments": 50},
        {"bookmarks": 500, "views": 2000, "comments": 25},
        {"bookmarks": 10000, "views": 50000, "comments": 500},
    ]

    # ==================== 标签相关 ====================

    # 测试用的标签（带翻译）
    TEST_TAGS: Final[list[dict[str, str | None]]] = [
        {"name": "风景", "translated_name": "landscape"},
        {"name": "插画", "translated_name": "illustration"},
        {"name": "少女", "translated_name": "girl"},
        {"name": "原创", "translated_name": None},  # 无翻译
        {"name": "風景", "translated_name": "Landscape"},  # 日文
    ]


# 为了向后兼容和方便导入，创建模块级常量
RANKING_TYPES_API = TestData.RANKING_MODES_API
RANKING_TYPES_CLI = TestData.RANKING_MODES_CLI
TEST_DATES = TestData.VALID_DATES
TEST_TOKENS = {
    "valid": TestData.VALID_REFRESH_TOKEN,
    "alt": TestData.ALT_REFRESH_TOKEN,
    "invalid": TestData.INVALID_TOKENS,
}
