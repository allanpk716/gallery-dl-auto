"""Pixiv API 客户端测试

测试 PixivClient 类的认证、排行榜获取和数据提取功能。
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from gallery_dl_auto.api.pixiv_client import PixivClient, PixivAPIError


class TestPixivClientInit:
    """测试 PixivClient 初始化和认证"""

    @patch("gallery_dl_auto.api.pixiv_client.AppPixivAPI")
    def test_init_with_valid_token(self, mock_api_class: Mock) -> None:
        """测试使用有效 token 初始化成功"""
        # 模拟 API 认证成功
        mock_api = Mock()
        mock_api_class.return_value = mock_api

        # 初始化客户端
        client = PixivClient(refresh_token="valid_refresh_token")

        # 验证认证调用
        mock_api.auth.assert_called_once_with(refresh_token="valid_refresh_token")
        assert client.api == mock_api

    @patch("gallery_dl_auto.api.pixiv_client.AppPixivAPI")
    def test_init_with_invalid_token(self, mock_api_class: Mock) -> None:
        """测试使用无效 token 初始化失败"""
        # 模拟 API 认证失败
        mock_api = Mock()
        mock_api.auth.side_effect = Exception("Invalid token")
        mock_api_class.return_value = mock_api

        # 验证抛出 PixivAPIError
        with pytest.raises(PixivAPIError) as exc_info:
            PixivClient(refresh_token="invalid_token")

        assert "Authentication failed" in str(exc_info.value)


class TestGetRanking:
    """测试排行榜获取功能"""

    @patch("gallery_dl_auto.api.pixiv_client.AppPixivAPI")
    def test_get_ranking_daily(self, mock_api_class: Mock) -> None:
        """测试获取每日排行榜"""
        # 模拟 API 响应
        mock_api = Mock()
        mock_api_class.return_value = mock_api

        # 创建模拟作品数据
        mock_illust = Mock()
        mock_illust.id = 12345678
        mock_illust.title = "Test Artwork"
        mock_illust.user = Mock()
        mock_illust.user.name = "Test Artist"
        mock_illust.image_urls = Mock()
        mock_illust.image_urls.large = "https://i.pximg.net/test.jpg"

        # 设置 API 返回值
        mock_result = Mock()
        mock_result.illusts = [mock_illust]
        mock_result.next_url = None
        mock_api.illust_ranking.return_value = mock_result

        # 初始化客户端并获取排行榜
        client = PixivClient(refresh_token="test_token")
        works = client.get_ranking(mode="day")

        # 验证结果
        assert len(works) == 1
        assert works[0]["id"] == 12345678
        assert works[0]["title"] == "Test Artwork"
        assert works[0]["author"] == "Test Artist"
        assert works[0]["image_url"] == "https://i.pximg.net/test.jpg"

        # 验证 API 调用参数
        mock_api.illust_ranking.assert_called_once_with(mode="day")

    @patch("gallery_dl_auto.api.pixiv_client.AppPixivAPI")
    def test_get_ranking_with_date(self, mock_api_class: Mock) -> None:
        """测试获取指定日期排行榜"""
        mock_api = Mock()
        mock_api_class.return_value = mock_api

        # 设置 API 返回空结果
        mock_result = Mock()
        mock_result.illusts = []
        mock_result.next_url = None
        mock_api.illust_ranking.return_value = mock_result

        # 初始化客户端并获取排行榜
        client = PixivClient(refresh_token="test_token")
        works = client.get_ranking(mode="day", date="2026-02-25")

        # 验证 API 调用包含日期参数
        mock_api.illust_ranking.assert_called_once_with(mode="day", date="2026-02-25")
        assert works == []

    @patch("gallery_dl_auto.api.pixiv_client.AppPixivAPI")
    def test_get_ranking_empty_result(self, mock_api_class: Mock) -> None:
        """测试空排行榜结果"""
        mock_api = Mock()
        mock_api_class.return_value = mock_api

        # 设置 API 返回空结果
        mock_result = Mock()
        mock_result.illusts = []
        mock_result.next_url = None
        mock_api.illust_ranking.return_value = mock_result

        # 初始化客户端并获取排行榜
        client = PixivClient(refresh_token="test_token")
        works = client.get_ranking()

        assert works == []

    @patch("gallery_dl_auto.api.pixiv_client.AppPixivAPI")
    def test_get_ranking_pagination(self, mock_api_class: Mock) -> None:
        """测试分页获取排行榜(使用 get_ranking_all)"""
        mock_api = Mock()
        mock_api_class.return_value = mock_api

        # 创建两页数据
        mock_illust1 = Mock()
        mock_illust1.id = 111
        mock_illust1.title = "Work 1"
        mock_illust1.user = Mock()
        mock_illust1.user.name = "Artist 1"
        mock_illust1.image_urls = Mock()
        mock_illust1.image_urls.large = "url1"

        mock_illust2 = Mock()
        mock_illust2.id = 222
        mock_illust2.title = "Work 2"
        mock_illust2.user = Mock()
        mock_illust2.user.name = "Artist 2"
        mock_illust2.image_urls = Mock()
        mock_illust2.image_urls.large = "url2"

        # 设置第一页响应
        mock_result1 = Mock()
        mock_result1.illusts = [mock_illust1]
        mock_result1.next_url = "https://api.pixiv.net/next_page"

        # 设置第二页响应
        mock_result2 = Mock()
        mock_result2.illusts = [mock_illust2]
        mock_result2.next_url = None

        # 设置 API 返回值
        mock_api.illust_ranking.side_effect = [mock_result1, mock_result2]
        mock_api.parse_qs.return_value = {"mode": "day", "offset": 30}

        # 初始化客户端并获取排行榜
        client = PixivClient(refresh_token="test_token")
        works = client.get_ranking_all()

        # 验证结果包含两页数据
        assert len(works) == 2
        assert works[0]["id"] == 111
        assert works[1]["id"] == 222

        # 验证分页调用
        mock_api.parse_qs.assert_called_once_with("https://api.pixiv.net/next_page")

    @patch("gallery_dl_auto.api.pixiv_client.AppPixivAPI")
    def test_get_ranking_api_error(self, mock_api_class: Mock) -> None:
        """测试 API 错误处理"""
        mock_api = Mock()
        mock_api_class.return_value = mock_api

        # 设置 API 抛出异常
        mock_api.illust_ranking.side_effect = Exception("Network error")

        # 初始化客户端
        client = PixivClient(refresh_token="test_token")

        # 验证抛出 PixivAPIError
        with pytest.raises(PixivAPIError) as exc_info:
            client.get_ranking()

        assert "Failed to get ranking" in str(exc_info.value)


class TestGetRankingAll:
    """测试 get_ranking_all() 完整分页功能"""

    @patch("gallery_dl_auto.api.pixiv_client.AppPixivAPI")
    def test_get_ranking_all_single_page(self, mock_api_class: Mock) -> None:
        """测试单页排行榜"""
        mock_api = Mock()
        mock_api_class.return_value = mock_api

        # 创建模拟作品数据
        mock_illust1 = Mock()
        mock_illust1.id = 1
        mock_illust1.title = "Work 1"
        mock_illust1.user = Mock()
        mock_illust1.user.name = "Artist 1"
        mock_illust1.image_urls = Mock()
        mock_illust1.image_urls.large = "url1"

        mock_illust2 = Mock()
        mock_illust2.id = 2
        mock_illust2.title = "Work 2"
        mock_illust2.user = Mock()
        mock_illust2.user.name = "Artist 2"
        mock_illust2.image_urls = Mock()
        mock_illust2.image_urls.large = "url2"

        mock_result = Mock()
        mock_result.illusts = [mock_illust1, mock_illust2]
        mock_result.next_url = None
        mock_api.illust_ranking.return_value = mock_result

        client = PixivClient(refresh_token="test_token")
        result = client.get_ranking_all(mode="day")

        assert len(result) == 2
        mock_api.illust_ranking.assert_called_once()

    @patch("gallery_dl_auto.api.pixiv_client.AppPixivAPI")
    def test_get_ranking_all_multiple_pages(self, mock_api_class: Mock) -> None:
        """测试多页排行榜获取"""
        mock_api = Mock()
        mock_api_class.return_value = mock_api

        # 创建第一页作品 (1-50)
        def create_mock_illust(i):
            mock_illust = Mock()
            mock_illust.id = i
            mock_illust.title = f"Work {i}"
            mock_illust.user = Mock()
            mock_illust.user.name = f"Artist {i}"
            mock_illust.image_urls = Mock()
            mock_illust.image_urls.large = f"url{i}"
            return mock_illust

        # 模拟第一页
        page1 = Mock()
        page1.illusts = [create_mock_illust(i) for i in range(1, 51)]
        page1.next_url = "https://api.pixiv.net/ranking?offset=50"

        # 模拟第二页
        page2 = Mock()
        page2.illusts = [create_mock_illust(i) for i in range(51, 101)]
        page2.next_url = None

        mock_api.illust_ranking.side_effect = [page1, page2]
        mock_api.parse_qs.return_value = {"mode": "day", "offset": 50}

        client = PixivClient(refresh_token="test_token")
        result = client.get_ranking_all(mode="day")

        assert len(result) == 100  # 两页共 100 个作品
        assert mock_api.illust_ranking.call_count == 2


class TestGetRankingAllModes:
    """测试所有排行榜模式"""

    @pytest.mark.parametrize("mode", [
        "day", "week", "month",
        "day_male", "day_female", "week_original", "week_rookie", "day_manga",
        "day_r18", "day_male_r18", "day_female_r18", "week_r18", "week_r18g"
    ])
    @patch("gallery_dl_auto.api.pixiv_client.AppPixivAPI")
    def test_get_ranking_different_modes(self, mock_api_class: Mock, mode: str) -> None:
        """测试不同排行榜模式"""
        mock_api = Mock()
        mock_api_class.return_value = mock_api

        # 创建模拟作品数据
        mock_illust = Mock()
        mock_illust.id = 12345678
        mock_illust.title = "Test Artwork"
        mock_illust.user = Mock()
        mock_illust.user.name = "Test Artist"
        mock_illust.image_urls = Mock()
        mock_illust.image_urls.large = "https://i.pximg.net/test.jpg"

        # 设置 API 返回值
        mock_result = Mock()
        mock_result.illusts = [mock_illust]
        mock_result.next_url = None
        mock_api.illust_ranking.return_value = mock_result

        # 初始化客户端并获取排行榜
        client = PixivClient(refresh_token="test_token")
        works = client.get_ranking(mode=mode)

        # 验证结果
        assert len(works) == 1
        assert works[0]["id"] == 12345678

        # 验证 API 调用使用了正确的 mode 参数
        mock_api.illust_ranking.assert_called_once_with(mode=mode)

    @patch("gallery_dl_auto.api.pixiv_client.AppPixivAPI")
    def test_get_ranking_with_date_parameter(self, mock_api_class: Mock) -> None:
        """测试带日期参数的排行榜"""
        mock_api = Mock()
        mock_api_class.return_value = mock_api

        # 创建模拟作品数据
        mock_illust = Mock()
        mock_illust.id = 12345678
        mock_illust.title = "Test Artwork"
        mock_illust.user = Mock()
        mock_illust.user.name = "Test Artist"
        mock_illust.image_urls = Mock()
        mock_illust.image_urls.large = "https://i.pximg.net/test.jpg"

        # 设置 API 返回值
        mock_result = Mock()
        mock_result.illusts = [mock_illust]
        mock_result.next_url = None
        mock_api.illust_ranking.return_value = mock_result

        # 初始化客户端并获取排行榜
        client = PixivClient(refresh_token="test_token")
        works = client.get_ranking(mode="week", date="2026-02-18")

        # 验证结果
        assert len(works) == 1

        # 验证 API 调用包含 mode 和 date 参数
        mock_api.illust_ranking.assert_called_once_with(mode="week", date="2026-02-18")


class TestRankingDataStructure:
    """测试排行榜数据结构"""

    @patch("gallery_dl_auto.api.pixiv_client.AppPixivAPI")
    def test_ranking_data_structure(self, mock_api_class: Mock) -> None:
        """验证返回的数据结构包含必需字段"""
        mock_api = Mock()
        mock_api_class.return_value = mock_api

        # 创建完整的模拟作品数据
        mock_illust = Mock()
        mock_illust.id = 99999999
        mock_illust.title = "完整的测试作品"
        mock_illust.user = Mock()
        mock_illust.user.name = "测试作者"
        mock_illust.image_urls = Mock()
        mock_illust.image_urls.large = "https://i.pximg.net/full-test.jpg"

        # 设置 API 返回值
        mock_result = Mock()
        mock_result.illusts = [mock_illust]
        mock_result.next_url = None
        mock_api.illust_ranking.return_value = mock_result

        # 初始化客户端并获取排行榜
        client = PixivClient(refresh_token="test_token")
        works = client.get_ranking()

        # 验证数据结构
        assert len(works) == 1
        work = works[0]

        # 验证必需字段存在
        assert "id" in work
        assert "title" in work
        assert "author" in work
        assert "image_url" in work

        # 验证字段值
        assert work["id"] == 99999999
        assert work["title"] == "完整的测试作品"
        assert work["author"] == "测试作者"
        assert work["image_url"] == "https://i.pximg.net/full-test.jpg"


class TestGetArtworkMetadata:
    """测试元数据获取功能"""

    @patch("gallery_dl_auto.api.pixiv_client.AppPixivAPI")
    def test_get_artwork_metadata_success(self, mock_api_class: Mock) -> None:
        """测试成功获取元数据"""
        # 模拟 API 客户端
        mock_api = Mock()
        mock_api_class.return_value = mock_api

        # 创建 mock illust 对象
        mock_illust = Mock()
        mock_illust.id = 12345
        mock_illust.title = "Test Artwork"
        mock_illust.user = Mock()
        mock_illust.user.name = "Test Author"
        mock_illust.user.id = 67890

        # 创建标签 mock 对象
        tag1 = Mock()
        tag1.name = "风景"
        tag1.translated_name = "landscape"
        tag2 = Mock()
        tag2.name = "插画"
        tag2.translated_name = "illustration"
        mock_illust.tags = [tag1, tag2]

        mock_illust.total_bookmarks = 1000
        mock_illust.total_view = 5000
        mock_illust.total_comments = 50

        # Mock API 响应
        mock_result = Mock()
        mock_result.illust = mock_illust
        mock_api.illust_detail.return_value = mock_result

        # 初始化客户端并获取元数据
        client = PixivClient(refresh_token="test_token")
        metadata = client.get_artwork_metadata(illust_id=12345)

        # 验证结果
        assert metadata.illust_id == 12345
        assert metadata.title == "Test Artwork"
        assert metadata.author == "Test Author"
        assert metadata.author_id == 67890
        assert len(metadata.tags) == 2
        assert metadata.tags[0].name == "风景"
        assert metadata.tags[0].translated_name == "landscape"
        assert metadata.tags[1].name == "插画"
        assert metadata.tags[1].translated_name == "illustration"
        assert metadata.statistics.bookmark_count == 1000
        assert metadata.statistics.view_count == 5000
        assert metadata.statistics.comment_count == 50

        # 验证 API 调用
        mock_api.illust_detail.assert_called_once_with(12345)

    @patch("gallery_dl_auto.api.pixiv_client.AppPixivAPI")
    def test_get_artwork_metadata_with_translated_tags(self, mock_api_class: Mock) -> None:
        """测试带翻译的标签"""
        mock_api = Mock()
        mock_api_class.return_value = mock_api

        # 创建带翻译标签的 mock illust
        mock_illust = Mock()
        mock_illust.id = 12345
        mock_illust.title = "Test Artwork"
        mock_illust.user = Mock()
        mock_illust.user.name = "Test Author"
        mock_illust.user.id = 67890

        # 创建标签 mock 对象
        tag1 = Mock()
        tag1.name = "風景"
        tag1.translated_name = "Landscape"
        tag2 = Mock()
        tag2.name = "少女"
        tag2.translated_name = "Girl"
        mock_illust.tags = [tag1, tag2]

        mock_illust.total_bookmarks = 500
        mock_illust.total_view = 2000
        mock_illust.total_comments = 25

        mock_result = Mock()
        mock_result.illust = mock_illust
        mock_api.illust_detail.return_value = mock_result

        # 初始化并获取元数据
        client = PixivClient(refresh_token="test_token")
        metadata = client.get_artwork_metadata(illust_id=12345)

        # 验证翻译标签
        assert metadata.tags[0].translated_name == "Landscape"
        assert metadata.tags[1].translated_name == "Girl"

    @patch("gallery_dl_auto.api.pixiv_client.AppPixivAPI")
    def test_get_artwork_metadata_without_translated_tags(self, mock_api_class: Mock) -> None:
        """测试不带翻译的标签"""
        mock_api = Mock()
        mock_api_class.return_value = mock_api

        # 创建不带翻译标签的 mock illust
        mock_illust = Mock()
        mock_illust.id = 12345
        mock_illust.title = "Test Artwork"
        mock_illust.user = Mock()
        mock_illust.user.name = "Test Author"
        mock_illust.user.id = 67890

        # 创建标签 mock 对象
        tag1 = Mock()
        tag1.name = "风景"
        tag1.translated_name = None
        tag2 = Mock()
        tag2.name = "插画"
        tag2.translated_name = None
        mock_illust.tags = [tag1, tag2]

        mock_illust.total_bookmarks = 100
        mock_illust.total_view = 500
        mock_illust.total_comments = 10

        mock_result = Mock()
        mock_result.illust = mock_illust
        mock_api.illust_detail.return_value = mock_result

        # 初始化并获取元数据
        client = PixivClient(refresh_token="test_token")
        metadata = client.get_artwork_metadata(illust_id=12345)

        # 验证没有翻译的标签
        assert metadata.tags[0].translated_name is None
        assert metadata.tags[1].translated_name is None

    @patch("gallery_dl_auto.api.pixiv_client.AppPixivAPI")
    def test_get_artwork_metadata_api_error(self, mock_api_class: Mock) -> None:
        """测试 API 错误处理"""
        mock_api = Mock()
        mock_api_class.return_value = mock_api

        # 设置 API 抛出异常
        mock_api.illust_detail.side_effect = Exception("API error")

        # 初始化客户端
        client = PixivClient(refresh_token="test_token")

        # 验证抛出 PixivAPIError
        with pytest.raises(PixivAPIError) as exc_info:
            client.get_artwork_metadata(illust_id=12345)

        assert "Failed to get metadata for 12345" in str(exc_info.value)
