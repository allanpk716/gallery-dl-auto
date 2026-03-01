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
            assert ModeManager.validate_api_mode(mode) is True

    def test_validate_api_mode_invalid(self):
        """Test validation of invalid API modes raises error."""
        with pytest.raises(ValueError, match="Invalid API mode"):
            ModeManager.validate_api_mode("invalid_mode")

    def test_api_to_gallery_dl_invalid_mode(self):
        """Test conversion of invalid mode raises error."""
        with pytest.raises(ValueError, match="Invalid API mode"):
            ModeManager.api_to_gallery_dl("invalid_mode")
