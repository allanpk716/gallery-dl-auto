"""Mock Pixiv API 响应数据

提供创建 Mock Pixiv API 响应对象的工厂函数。
这些函数返回的对象模拟 pixivpy3 API 的响应结构。
"""

from typing import Any
from unittest.mock import Mock


class MockPixivResponses:
    """Mock Pixiv API 响应数据工厂类

    提供创建各种 Mock API 响应的静态方法。
    所有方法都返回 Mock 对象，模拟 pixivpy3 的响应结构。
    """

    @staticmethod
    def create_mock_illust(
        illust_id: int,
        title: str = "Test Artwork",
        author_name: str = "Test Artist",
        author_id: int = 11111111,
        image_url: str = "https://i.pximg.net/test.jpg",
        **kwargs: Any,
    ) -> Mock:
        """创建 Mock illust 对象

        模拟 Pixiv API 返回的作品对象。

        Args:
            illust_id: 作品 ID
            title: 作品标题
            author_name: 作者名
            author_id: 作者 ID
            image_url: 图片 URL
            **kwargs: 其他自定义属性

        Returns:
            Mock 对象，模拟 illust 结构

        Example:
            >>> illust = MockPixivResponses.create_mock_illust(
            ...     illust_id=12345678,
            ...     title="Beautiful Sunset"
            ... )
            >>> illust.id
            12345678
            >>> illust.title
            'Beautiful Sunset'
        """
        mock_illust = Mock()
        mock_illust.id = illust_id
        mock_illust.title = title

        # 设置作者信息
        mock_illust.user = Mock()
        mock_illust.user.id = author_id
        mock_illust.user.name = author_name

        # 设置图片 URL
        mock_illust.image_urls = Mock()
        mock_illust.image_urls.large = image_url
        mock_illust.image_urls.medium = image_url.replace("test.jpg", "test_m.jpg")
        mock_illust.image_urls.square_medium = image_url.replace(
            "test.jpg", "test_sq.jpg"
        )

        # 设置默认统计数据
        mock_illust.total_bookmarks = kwargs.get("bookmarks", 1000)
        mock_illust.total_view = kwargs.get("views", 5000)
        mock_illust.total_comments = kwargs.get("comments", 50)

        # 设置默认标签
        mock_illust.tags = []

        # 设置其他可选属性
        for key, value in kwargs.items():
            if not hasattr(mock_illust, key):
                setattr(mock_illust, key, value)

        return mock_illust

    @staticmethod
    def create_mock_tag(
        name: str, translated_name: str | None = None
    ) -> Mock:
        """创建 Mock tag 对象

        Args:
            name: 标签名
            translated_name: 翻译后的标签名（可选）

        Returns:
            Mock 对象，模拟 tag 结构

        Example:
            >>> tag = MockPixivResponses.create_mock_tag("风景", "landscape")
            >>> tag.name
            '风景'
            >>> tag.translated_name
            'landscape'
        """
        mock_tag = Mock()
        mock_tag.name = name
        mock_tag.translated_name = translated_name
        return mock_tag

    @staticmethod
    def create_mock_ranking_response(
        illusts: list[Mock] | None = None,
        next_url: str | None = None,
    ) -> Mock:
        """创建 Mock 排行榜响应

        模拟 illust_ranking() API 的响应。

        Args:
            illusts: 作品列表（Mock 对象）
            next_url: 下一页的 URL（用于分页测试）

        Returns:
            Mock 对象，模拟 API 响应结构

        Example:
            >>> # 单页排行榜
            >>> response = MockPixivResponses.create_mock_ranking_response(
            ...     illusts=[illust1, illust2]
            ... )
            >>> len(response.illusts)
            2

            >>> # 带分页的排行榜
            >>> response = MockPixivResponses.create_mock_ranking_response(
            ...     illusts=[illust1],
            ...     next_url="https://api.pixiv.net/next"
            ... )
            >>> response.next_url
            'https://api.pixiv.net/next'
        """
        mock_response = Mock()
        mock_response.illusts = illusts if illusts is not None else []
        mock_response.next_url = next_url
        return mock_response

    @staticmethod
    def create_mock_artwork_detail_response(
        illust: Mock,
    ) -> Mock:
        """创建 Mock 作品详情响应

        模拟 illust_detail() API 的响应。

        Args:
            illust: Mock illust 对象

        Returns:
            Mock 对象，模拟 API 响应结构

        Example:
            >>> illust = MockPixivResponses.create_mock_illust(12345678)
            >>> response = MockPixivResponses.create_mock_artwork_detail_response(illust)
            >>> response.illust.id
            12345678
        """
        mock_response = Mock()
        mock_response.illust = illust
        return mock_response

    @staticmethod
    def create_sample_ranking_data(
        count: int = 10,
        start_id: int = 10000000,
    ) -> list[Mock]:
        """创建示例排行榜数据

        批量创建 Mock illust 对象，用于测试排行榜下载。

        Args:
            count: 创建的作品数量
            start_id: 起始作品 ID

        Returns:
            Mock illust 对象列表

        Example:
            >>> works = MockPixivResponses.create_sample_ranking_data(count=5)
            >>> len(works)
            5
            >>> works[0].id
            10000000
        """
        illusts = []
        for i in range(count):
            illust_id = start_id + i
            illust = MockPixivResponses.create_mock_illust(
                illust_id=illust_id,
                title=f"Test Artwork {i + 1}",
                author_name=f"Artist {i + 1}",
                author_id=20000000 + i,
                image_url=f"https://i.pximg.net/img-{illust_id}.jpg",
                bookmarks=1000 - i * 10,  # 排名越靠后，收藏数越少
                views=5000 - i * 50,
                comments=50 - i,
            )
            illusts.append(illust)
        return illusts

    @staticmethod
    def create_sample_ranking_with_tags(
        illust_id: int = 12345678,
        tags: list[dict[str, str | None]] | None = None,
    ) -> Mock:
        """创建带标签的示例作品

        用于测试元数据获取功能。

        Args:
            illust_id: 作品 ID
            tags: 标签列表，每个标签包含 name 和 translated_name

        Returns:
            Mock illust 对象，包含标签

        Example:
            >>> tags = [
            ...     {"name": "风景", "translated_name": "landscape"},
            ...     {"name": "插画", "translated_name": "illustration"}
            ... ]
            >>> illust = MockPixivResponses.create_sample_ranking_with_tags(
            ...     illust_id=12345678,
            ...     tags=tags
            ... )
            >>> len(illust.tags)
            2
            >>> illust.tags[0].name
            '风景'
        """
        if tags is None:
            tags = [
                {"name": "风景", "translated_name": "landscape"},
                {"name": "插画", "translated_name": "illustration"},
            ]

        mock_tags = [
            MockPixivResponses.create_mock_tag(**tag_data)
            for tag_data in tags
        ]

        illust = MockPixivResponses.create_mock_illust(illust_id=illust_id)
        illust.tags = mock_tags

        return illust


# 为了方便使用，创建模块级函数别名
def create_mock_illust(*args: Any, **kwargs: Any) -> Mock:
    """创建 Mock illust 对象的便捷函数"""
    return MockPixivResponses.create_mock_illust(*args, **kwargs)


def create_mock_ranking_response(*args: Any, **kwargs: Any) -> Mock:
    """创建 Mock 排行榜响应的便捷函数"""
    return MockPixivResponses.create_mock_ranking_response(*args, **kwargs)


def create_mock_artwork_detail_response(*args: Any, **kwargs: Any) -> Mock:
    """创建 Mock 作品详情响应的便捷函数"""
    return MockPixivResponses.create_mock_artwork_detail_response(*args, **kwargs)
