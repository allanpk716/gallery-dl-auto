"""pytest fixtures for gallery-dl-auto testing

This package contains shared test fixtures, mock data, and test utilities.
"""

from .mock_pixiv_responses import (
    MockPixivResponses,
    create_mock_artwork_detail_response,
    create_mock_illust,
    create_mock_ranking_response,
)
from .test_data import (
    RANKING_TYPES_API,
    RANKING_TYPES_CLI,
    TEST_DATES,
    TEST_TOKENS,
    TestData,
)

__all__ = [
    # Mock responses
    "MockPixivResponses",
    "create_mock_illust",
    "create_mock_ranking_response",
    "create_mock_artwork_detail_response",
    # Test data
    "TestData",
    "RANKING_TYPES_API",
    "RANKING_TYPES_CLI",
    "TEST_DATES",
    "TEST_TOKENS",
]
