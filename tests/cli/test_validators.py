"""验证器模块单元测试

测试 CLI 参数验证器的正确性和错误处理。
"""

from datetime import date, timedelta

import pytest
from click import BadParameter

from gallery_dl_auto.cli.validators import (
    validate_ranking_date,
    validate_ranking_type,
    validate_date_param,
    validate_type_param,
    RANKING_MODES,
)


class TestRankingTypeValidation:
    """排行榜类型验证测试"""

    def test_valid_daily_type(self):
        """测试有效类型: daily -> day"""
        result = validate_ranking_type("daily")
        assert result == "day"

    def test_valid_weekly_type(self):
        """测试有效类型: weekly -> week"""
        result = validate_ranking_type("weekly")
        assert result == "week"

    def test_valid_monthly_type(self):
        """测试有效类型: monthly -> month"""
        result = validate_ranking_type("monthly")
        assert result == "month"

    def test_valid_day_male_type(self):
        """测试有效类型: day_male (无需转换)"""
        result = validate_ranking_type("day_male")
        assert result == "day_male"

    def test_valid_day_female_type(self):
        """测试有效类型: day_female"""
        result = validate_ranking_type("day_female")
        assert result == "day_female"

    def test_valid_week_original_type(self):
        """测试有效类型: week_original"""
        result = validate_ranking_type("week_original")
        assert result == "week_original"

    def test_valid_week_rookie_type(self):
        """测试有效类型: week_rookie"""
        result = validate_ranking_type("week_rookie")
        assert result == "week_rookie"

    def test_valid_day_manga_type(self):
        """测试有效类型: day_manga"""
        result = validate_ranking_type("day_manga")
        assert result == "day_manga"

    def test_valid_day_r18_type(self):
        """测试有效类型: day_r18"""
        result = validate_ranking_type("day_r18")
        assert result == "day_r18"

    def test_valid_day_male_r18_type(self):
        """测试有效类型: day_male_r18"""
        result = validate_ranking_type("day_male_r18")
        assert result == "day_male_r18"

    def test_valid_day_female_r18_type(self):
        """测试有效类型: day_female_r18"""
        result = validate_ranking_type("day_female_r18")
        assert result == "day_female_r18"

    def test_valid_week_r18_type(self):
        """测试有效类型: week_r18"""
        result = validate_ranking_type("week_r18")
        assert result == "week_r18"

    def test_valid_week_r18g_type(self):
        """测试有效类型: week_r18g"""
        result = validate_ranking_type("week_r18g")
        assert result == "week_r18g"

    def test_invalid_type_raises_error(self):
        """测试无效类型抛出 ValueError"""
        with pytest.raises(ValueError) as exc_info:
            validate_ranking_type("invalid_type")

        assert "Invalid ranking type 'invalid_type'" in str(exc_info.value)
        assert "Valid types:" in str(exc_info.value)

    def test_invalid_type_includes_all_valid_types(self):
        """测试错误信息包含所有有效类型"""
        with pytest.raises(ValueError) as exc_info:
            validate_ranking_type("xyz")

        error_msg = str(exc_info.value)
        # 验证包含主要类型
        assert "daily" in error_msg
        assert "weekly" in error_msg
        assert "monthly" in error_msg
        assert "day_male" in error_msg

    def test_all_ranking_types_in_mapping(self):
        """测试所有 13 种类型都在映射中"""
        assert len(RANKING_MODES) == 13


class TestDateValidation:
    """日期验证测试"""

    def test_valid_date_format(self):
        """测试有效日期格式"""
        result = validate_ranking_date("2026-02-18")
        assert result == "2026-02-18"

    def test_today_date(self):
        """测试今天的日期"""
        today = date.today().strftime("%Y-%m-%d")
        result = validate_ranking_date(today)
        assert result == today

    def test_past_date(self):
        """测试过去的日期"""
        past_date = (date.today() - timedelta(days=30)).strftime("%Y-%m-%d")
        result = validate_ranking_date(past_date)
        assert result == past_date

    def test_future_date_raises_error(self):
        """测试未来日期抛出 ValueError"""
        future_date = (date.today() + timedelta(days=1)).strftime("%Y-%m-%d")

        with pytest.raises(ValueError) as exc_info:
            validate_ranking_date(future_date)

        assert f"Date '{future_date}' is in the future" in str(exc_info.value)

    def test_invalid_format_raises_error(self):
        """测试无效格式抛出 ValueError"""
        with pytest.raises(ValueError) as exc_info:
            validate_ranking_date("2026/02/18")

        assert "Invalid date '2026/02/18'" in str(exc_info.value)
        assert "Format: YYYY-MM-DD" in str(exc_info.value)

    def test_invalid_month_raises_error(self):
        """测试无效月份"""
        with pytest.raises(ValueError) as exc_info:
            validate_ranking_date("2026-13-01")

        assert "Invalid date" in str(exc_info.value)

    def test_invalid_day_raises_error(self):
        """测试无效日期"""
        with pytest.raises(ValueError) as exc_info:
            validate_ranking_date("2026-02-30")

        assert "Invalid date" in str(exc_info.value)


class TestClickValidators:
    """Click 参数验证器集成测试"""

    def test_validate_type_param_with_valid_value(self):
        """测试 Click 验证器: 有效类型"""
        result = validate_type_param(None, None, "weekly")
        assert result == "week"

    def test_validate_type_param_with_none(self):
        """测试 Click 验证器: None 值"""
        result = validate_type_param(None, None, None)
        assert result is None

    def test_validate_type_param_with_invalid_value(self):
        """测试 Click 验证器: 无效类型"""
        with pytest.raises(BadParameter) as exc_info:
            validate_type_param(None, None, "invalid")

        assert "Invalid ranking type" in str(exc_info.value)

    def test_validate_date_param_with_valid_value(self):
        """测试 Click 验证器: 有效日期"""
        today = date.today().strftime("%Y-%m-%d")
        result = validate_date_param(None, None, today)
        assert result == today

    def test_validate_date_param_with_none(self):
        """测试 Click 验证器: None 值"""
        result = validate_date_param(None, None, None)
        assert result is None

    def test_validate_date_param_with_future_date(self):
        """测试 Click 验证器: 未来日期"""
        future_date = (date.today() + timedelta(days=1)).strftime("%Y-%m-%d")

        with pytest.raises(BadParameter) as exc_info:
            validate_date_param(None, None, future_date)

        assert "is in the future" in str(exc_info.value)

    def test_validate_date_param_with_invalid_format(self):
        """测试 Click 验证器: 无效格式"""
        with pytest.raises(BadParameter) as exc_info:
            validate_date_param(None, None, "2026/02/18")

        assert "Invalid date" in str(exc_info.value)
