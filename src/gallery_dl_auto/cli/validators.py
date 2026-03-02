"""CLI 参数验证器

提供 Click 参数验证器,用于验证排行榜类型和日期参数。
"""

from datetime import date, datetime
from typing import Literal

import click

from gallery_dl_auto.core.mode_manager import ModeManager

# 类型别名: 排行榜类型
# 保持向后兼容，支持 CLI 友好名称
RankingType = Literal[
    "daily",
    "weekly",
    "monthly",
    "day_male",
    "day_female",
    "week_original",
    "week_rookie",
    "day_manga",
    "day_r18",
    "day_male_r18",
    "day_female_r18",
    "week_r18",
    "week_r18g",
]


def validate_ranking_type(type_str: str) -> str:
    """验证排行榜类型并返回 API mode 参数

    Args:
        type_str: 用户输入的排行榜类型（CLI 名称或 API 名称）

    Returns:
        API mode 参数 (day, week, month 等)

    Raises:
        ValueError: 无效的排行榜类型
    """
    try:
        return ModeManager.cli_to_api(type_str)
    except Exception as e:
        # 获取所有支持的 CLI modes 用于错误提示
        valid_types = ", ".join(ModeManager.get_all_cli_modes())
        raise ValueError(
            f"Invalid ranking type '{type_str}'. Valid types: {valid_types}"
        )


def validate_ranking_date(date_str: str) -> str:
    """验证日期格式和有效性

    Args:
        date_str: 用户输入的日期字符串

    Returns:
        验证后的日期字符串 (YYYY-MM-DD)

    Raises:
        ValueError: 日期格式无效或为未来日期
    """
    # 验证格式
    try:
        parsed = datetime.strptime(date_str, "%Y-%m-%d").date()
    except ValueError:
        raise ValueError(f"Invalid date '{date_str}'. Format: YYYY-MM-DD")

    # 验证不是未来日期
    today = date.today()
    if parsed > today:
        raise ValueError(f"Date '{date_str}' is in the future")

    return date_str


def validate_type_param(ctx, param, value: str | None) -> str | None:
    """Click 参数验证器: 排行榜类型

    Args:
        ctx: Click 上下文
        param: 参数对象
        value: 用户输入值

    Returns:
        验证后的 API mode 参数,或 None

    Raises:
        click.BadParameter: 无效的排行榜类型
    """
    if value is None:
        return None
    try:
        return validate_ranking_type(value)
    except ValueError as e:
        raise click.BadParameter(str(e))


def validate_date_param(ctx, param, value: str | None) -> str | None:
    """Click 参数验证器: 日期

    Args:
        ctx: Click 上下文
        param: 参数对象
        value: 用户输入值

    Returns:
        验证后的日期字符串,或 None

    Raises:
        click.BadParameter: 日期格式无效或为未来日期
    """
    if value is None:
        return None
    try:
        return validate_ranking_date(value)
    except ValueError as e:
        raise click.BadParameter(str(e))
