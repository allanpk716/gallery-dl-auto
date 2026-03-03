"""测试 fixtures 模块的功能

验证 Mock 数据工厂函数和测试数据常量的正确性。
"""

import pytest

from tests.fixtures import (
    MockPixivResponses,
    TestData,
    create_mock_illust,
    create_mock_ranking_response,
)


class TestTestData:
    """测试 TestData 常量类"""

    def test_ranking_modes_count(self) -> None:
        """测试排行榜类型数量"""
        assert len(TestData.RANKING_MODES_API) == 12
        assert len(TestData.RANKING_MODES_CLI) == 12

    def test_cli_to_api_map_completeness(self) -> None:
        """测试 CLI 到 API 映射的完整性"""
        assert len(TestData.CLI_TO_API_MAP) == 12
        # 验证所有 CLI 模式都有对应的 API 模式
        for cli_mode in TestData.RANKING_MODES_CLI:
            assert cli_mode in TestData.CLI_TO_API_MAP

    def test_valid_dates_format(self) -> None:
        """测试有效日期格式"""
        from datetime import datetime

        for date_str in TestData.VALID_DATES:
            # 应该能成功解析
            parsed = datetime.strptime(date_str, "%Y-%m-%d")
            assert parsed is not None

    def test_invalid_date_formats(self) -> None:
        """测试无效日期格式常量存在"""
        # 这个测试验证 TestData.INVALID_DATE_FORMATS 包含各种无效格式
        # 注意：strptime 可能比较宽松，某些格式可能仍然有效
        assert len(TestData.INVALID_DATE_FORMATS) > 0

        # 验证至少有几个确定无效的格式
        definitely_invalid = ["2026/02/24", "24-02-2026", "20260224"]
        from datetime import datetime

        for date_str in definitely_invalid:
            with pytest.raises(ValueError):
                datetime.strptime(date_str, "%Y-%m-%d")

    def test_test_tokens_not_empty(self) -> None:
        """测试 Token 不为空"""
        assert TestData.VALID_REFRESH_TOKEN != ""
        assert TestData.ALT_REFRESH_TOKEN != ""
        assert len(TestData.INVALID_TOKENS) > 0


class TestMockPixivResponses:
    """测试 Mock 数据工厂函数"""

    def test_create_mock_illust_basic(self) -> None:
        """测试创建基本的 Mock illust"""
        illust = create_mock_illust(
            illust_id=12345678,
            title="Test Artwork",
            author_name="Test Artist",
        )

        assert illust.id == 12345678
        assert illust.title == "Test Artwork"
        assert illust.user.name == "Test Artist"
        assert illust.user.id == 11111111  # 默认值

    def test_create_mock_illust_with_custom_values(self) -> None:
        """测试创建带自定义值的 Mock illust"""
        illust = create_mock_illust(
            illust_id=99999999,
            title="Custom Artwork",
            author_name="Custom Artist",
            author_id=88888888,
            image_url="https://custom.url/image.jpg",
            bookmarks=5000,
            views=20000,
            comments=200,
        )

        assert illust.id == 99999999
        assert illust.title == "Custom Artwork"
        assert illust.user.name == "Custom Artist"
        assert illust.user.id == 88888888
        assert illust.image_urls.large == "https://custom.url/image.jpg"
        assert illust.total_bookmarks == 5000
        assert illust.total_view == 20000
        assert illust.total_comments == 200

    def test_create_mock_tag(self) -> None:
        """测试创建 Mock tag"""
        tag = MockPixivResponses.create_mock_tag("风景", "landscape")

        assert tag.name == "风景"
        assert tag.translated_name == "landscape"

    def test_create_mock_tag_without_translation(self) -> None:
        """测试创建无翻译的 Mock tag"""
        tag = MockPixivResponses.create_mock_tag("原创")

        assert tag.name == "原创"
        assert tag.translated_name is None

    def test_create_mock_ranking_response_single_page(self) -> None:
        """测试创建单页排行榜响应"""
        illusts = [
            create_mock_illust(illust_id=1, title="Work 1"),
            create_mock_illust(illust_id=2, title="Work 2"),
        ]

        response = create_mock_ranking_response(illusts=illusts)

        assert len(response.illusts) == 2
        assert response.illusts[0].id == 1
        assert response.illusts[1].id == 2
        assert response.next_url is None

    def test_create_mock_ranking_response_with_pagination(self) -> None:
        """测试创建带分页的排行榜响应"""
        illusts = [create_mock_illust(illust_id=1)]

        response = create_mock_ranking_response(
            illusts=illusts,
            next_url="https://api.pixiv.net/next_page"
        )

        assert len(response.illusts) == 1
        assert response.next_url == "https://api.pixiv.net/next_page"

    def test_create_sample_ranking_data(self) -> None:
        """测试创建示例排行榜数据"""
        works = MockPixivResponses.create_sample_ranking_data(count=5, start_id=100)

        assert len(works) == 5
        assert works[0].id == 100
        assert works[1].id == 101
        # 验证排名靠前的作品收藏数更多
        assert works[0].total_bookmarks > works[1].total_bookmarks

    def test_create_sample_ranking_with_tags(self) -> None:
        """测试创建带标签的示例作品"""
        tags = [
            {"name": "风景", "translated_name": "landscape"},
            {"name": "插画", "translated_name": "illustration"},
        ]

        illust = MockPixivResponses.create_sample_ranking_with_tags(
            illust_id=12345678,
            tags=tags
        )

        assert illust.id == 12345678
        assert len(illust.tags) == 2
        assert illust.tags[0].name == "风景"
        assert illust.tags[0].translated_name == "landscape"
        assert illust.tags[1].name == "插画"
        assert illust.tags[1].translated_name == "illustration"

    def test_create_mock_artwork_detail_response(self) -> None:
        """测试创建作品详情响应"""
        illust = create_mock_illust(illust_id=12345678, title="Test")
        response = MockPixivResponses.create_mock_artwork_detail_response(illust)

        assert response.illust.id == 12345678
        assert response.illust.title == "Test"


class TestMockDataIntegration:
    """测试 Mock 数据的集成使用场景"""

    def test_simulate_ranking_workflow(self) -> None:
        """模拟排行榜获取工作流"""
        # 创建第一页数据
        page1_illusts = MockPixivResponses.create_sample_ranking_data(
            count=30, start_id=10000000
        )
        page1_response = create_mock_ranking_response(
            illusts=page1_illusts,
            next_url="https://api.pixiv.net/ranking?offset=30"
        )

        # 创建第二页数据
        page2_illusts = MockPixivResponses.create_sample_ranking_data(
            count=30, start_id=10000030
        )
        page2_response = create_mock_ranking_response(
            illusts=page2_illusts
        )

        # 验证第一页
        assert len(page1_response.illusts) == 30
        assert page1_response.next_url is not None

        # 验证第二页
        assert len(page2_response.illusts) == 30
        assert page2_response.next_url is None

    def test_simulate_artwork_detail_workflow(self) -> None:
        """模拟作品详情获取工作流"""
        # 创建带标签的作品
        tags = [
            {"name": "风景", "translated_name": "landscape"},
            {"name": "原创", "translated_name": None},
        ]

        illust = MockPixivResponses.create_sample_ranking_with_tags(
            illust_id=12345678,
            tags=tags
        )

        # 创建详情响应
        detail_response = MockPixivResponses.create_mock_artwork_detail_response(illust)

        # 验证数据结构
        assert detail_response.illust.id == 12345678
        assert len(detail_response.illust.tags) == 2
        assert detail_response.illust.tags[1].translated_name is None

    def test_using_test_data_constants(self) -> None:
        """测试使用 TestData 常量创建 Mock 数据"""
        # 使用 TestData 中的作品 ID
        illusts = []
        for illust_id in TestData.TEST_ILLUST_IDS[:3]:
            illust = create_mock_illust(
                illust_id=illust_id,
                title=f"Artwork {illust_id}"
            )
            illusts.append(illust)

        response = create_mock_ranking_response(illusts=illusts)

        assert len(response.illusts) == 3
        assert response.illusts[0].id == TestData.TEST_ILLUST_IDS[0]
