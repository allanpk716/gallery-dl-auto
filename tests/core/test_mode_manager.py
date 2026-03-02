"""Unit tests for ModeManager class.

Tests cover:
- Basic mode conversions (day/week/month)
- Category mode conversions
- R18 mode conversions
- Error handling for invalid modes
"""

import pytest

from gallery_dl_auto.core.mode_manager import ModeManager


class TestModeManagerBasicModes:
    """Test basic mode conversions (day/week/month)."""

    def test_api_to_gallery_dl_day(self):
        """Test API mode 'day' converts to gallery-dl mode 'daily'."""
        assert ModeManager.api_to_gallery_dl("day") == "daily"

    def test_api_to_gallery_dl_week(self):
        """Test API mode 'week' converts to gallery-dl mode 'weekly'."""
        assert ModeManager.api_to_gallery_dl("week") == "weekly"

    def test_api_to_gallery_dl_month(self):
        """Test API mode 'month' converts to gallery-dl mode 'monthly'."""
        assert ModeManager.api_to_gallery_dl("month") == "monthly"


class TestModeManagerCategoryModes:
    """Test category mode conversions."""

    def test_api_to_gallery_dl_day_male(self):
        """Test API mode 'day_male' converts to gallery-dl mode 'male'."""
        assert ModeManager.api_to_gallery_dl("day_male") == "male"

    def test_api_to_gallery_dl_day_female(self):
        """Test API mode 'day_female' converts to gallery-dl mode 'female'."""
        assert ModeManager.api_to_gallery_dl("day_female") == "female"

    def test_api_to_gallery_dl_week_original(self):
        """Test API mode 'week_original' converts to gallery-dl mode 'original'."""
        assert ModeManager.api_to_gallery_dl("week_original") == "original"

    def test_api_to_gallery_dl_week_rookie(self):
        """Test API mode 'week_rookie' converts to gallery-dl mode 'rookie'."""
        assert ModeManager.api_to_gallery_dl("week_rookie") == "rookie"


class TestModeManagerR18Modes:
    """Test R18 mode conversions."""

    def test_api_to_gallery_dl_day_r18(self):
        """Test API mode 'day_r18' converts to gallery-dl mode 'daily_r18'."""
        assert ModeManager.api_to_gallery_dl("day_r18") == "daily_r18"

    def test_api_to_gallery_dl_day_male_r18(self):
        """Test API mode 'day_male_r18' converts to gallery-dl mode 'male_r18'.

        This is the core fix for the bug where day_male_r18 was incorrectly
        converted to 'daily_male_r18' instead of 'male_r18'.
        """
        assert ModeManager.api_to_gallery_dl("day_male_r18") == "male_r18"

    def test_api_to_gallery_dl_day_female_r18(self):
        """Test API mode 'day_female_r18' converts to gallery-dl mode 'female_r18'."""
        assert ModeManager.api_to_gallery_dl("day_female_r18") == "female_r18"

    def test_api_to_gallery_dl_week_r18(self):
        """Test API mode 'week_r18' converts to gallery-dl mode 'weekly_r18'."""
        assert ModeManager.api_to_gallery_dl("week_r18") == "weekly_r18"

    def test_api_to_gallery_dl_week_r18g(self):
        """Test API mode 'week_r18g' converts to gallery-dl mode 'r18g'."""
        assert ModeManager.api_to_gallery_dl("week_r18g") == "r18g"


class TestModeManagerValidation:
    """Test mode validation."""

    def test_validate_api_mode_valid(self):
        """Test validation of valid API modes."""
        valid_modes = [
            "day", "week", "month",
            "day_male", "day_female", "week_original", "week_rookie",
            "day_r18", "day_male_r18", "day_female_r18", "week_r18", "week_r18g"
        ]
        for mode in valid_modes:
            assert ModeManager.validate_api_mode(mode) == mode

    def test_validate_api_mode_invalid(self):
        """Test validation of invalid API modes raises error."""
        from gallery_dl_auto.core.mode_errors import InvalidModeError
        with pytest.raises(InvalidModeError, match="Invalid mode"):
            ModeManager.validate_api_mode("invalid_mode")

    def test_api_to_gallery_dl_invalid_mode(self):
        """Test conversion of invalid mode raises error."""
        from gallery_dl_auto.core.mode_errors import InvalidModeError
        with pytest.raises(InvalidModeError, match="Invalid mode"):
            ModeManager.api_to_gallery_dl("invalid_mode")


class TestModeManagerCLIMethods:
    """Test CLI-related methods."""

    def test_cli_to_api_cli_names(self):
        """Test CLI friendly names conversion."""
        assert ModeManager.cli_to_api("daily") == "day"
        assert ModeManager.cli_to_api("weekly") == "week"
        assert ModeManager.cli_to_api("monthly") == "month"
        assert ModeManager.cli_to_api("male") == "day_male"
        assert ModeManager.cli_to_api("female") == "day_female"
        assert ModeManager.cli_to_api("original") == "week_original"
        assert ModeManager.cli_to_api("rookie") == "week_rookie"
        assert ModeManager.cli_to_api("daily_r18") == "day_r18"
        assert ModeManager.cli_to_api("male_r18") == "day_male_r18"
        assert ModeManager.cli_to_api("female_r18") == "day_female_r18"
        assert ModeManager.cli_to_api("weekly_r18") == "week_r18"
        assert ModeManager.cli_to_api("r18g") == "week_r18g"

    def test_cli_to_api_api_names_backward_compat(self):
        """Test API names still work (backward compatibility)."""
        assert ModeManager.cli_to_api("day") == "day"
        assert ModeManager.cli_to_api("week") == "week"
        assert ModeManager.cli_to_api("month") == "month"
        assert ModeManager.cli_to_api("day_male") == "day_male"
        assert ModeManager.cli_to_api("day_female") == "day_female"
        assert ModeManager.cli_to_api("week_original") == "week_original"
        assert ModeManager.cli_to_api("week_rookie") == "week_rookie"
        assert ModeManager.cli_to_api("day_r18") == "day_r18"
        assert ModeManager.cli_to_api("day_male_r18") == "day_male_r18"
        assert ModeManager.cli_to_api("day_female_r18") == "day_female_r18"
        assert ModeManager.cli_to_api("week_r18") == "week_r18"
        assert ModeManager.cli_to_api("week_r18g") == "week_r18g"

    def test_cli_to_api_invalid_mode(self):
        """Test invalid CLI mode raises error."""
        from gallery_dl_auto.core.mode_errors import InvalidModeError
        with pytest.raises(InvalidModeError, match="Invalid mode"):
            ModeManager.cli_to_api("invalid_mode")

    def test_get_all_cli_modes(self):
        """Test getting all CLI mode names."""
        cli_modes = ModeManager.get_all_cli_modes()

        # 验证返回的是列表
        assert isinstance(cli_modes, list)

        # 验证包含关键 mode
        assert "daily" in cli_modes
        assert "weekly" in cli_modes
        assert "monthly" in cli_modes
        assert "male" in cli_modes
        assert "female" in cli_modes

        # 验证列表已排序
        assert cli_modes == sorted(cli_modes)
