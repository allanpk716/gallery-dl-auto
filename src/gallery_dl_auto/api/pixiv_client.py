"""Pixiv API 客户端封装

使用 pixivpy3 库封装 Pixiv API 访问,提供认证和排行榜获取功能。
"""

import logging
from typing import Any

from pixivpy3 import AppPixivAPI

from gallery_dl_auto.download.retry_handler import retry_on_network_error
from gallery_dl_auto.models.artwork import (
    ArtworkMetadata,
    ArtworkStatistics,
    ArtworkTag,
)

logger = logging.getLogger("gallery_dl_auto")


class PixivAPIError(Exception):
    """Pixiv API 错误

    当 API 认证失败、网络错误或 API 限制时抛出。
    """

    def __init__(self, message: str) -> None:
        """初始化 API 错误

        Args:
            message: 错误描述
        """
        self.message = message
        super().__init__(self.message)

    def __str__(self) -> str:
        """返回错误的字符串表示"""
        return f"Pixiv API Error: {self.message}"


class PixivClient:
    """Pixiv API 客户端

    封装 pixivpy3 的 AppPixivAPI,提供认证和排行榜获取功能。
    """

    def __init__(self, refresh_token: str) -> None:
        """初始化 API 客户端并认证

        Args:
            refresh_token: Pixiv refresh token

        Raises:
            PixivAPIError: 认证失败时抛出
        """
        self.api = AppPixivAPI()

        try:
            # 使用 refresh token 认证
            self.api.auth(refresh_token=refresh_token)
            logger.info("Pixiv API authentication successful")
        except Exception as e:
            error_msg = f"Authentication failed: {e}"
            logger.error(error_msg)
            raise PixivAPIError(error_msg) from e

    @retry_on_network_error
    def get_ranking(
        self, mode: str = "day", date: str | None = None
    ) -> list[dict[str, Any]]:
        """获取排行榜数据(仅第一页)

        获取指定模式和日期的排行榜第一页数据。

        Args:
            mode: 排行榜模式
                - 常规: day, week, month
                - 分类: day_male, day_female, week_original, week_rookie, day_manga
                - R18: day_r18, day_male_r18, day_female_r18, week_r18, week_r18g
            date: 日期字符串 YYYY-MM-DD (默认为今天)

        Returns:
            作品列表,每个作品包含:
                - id: 作品 ID
                - title: 标题
                - author: 作者名
                - image_url: 图片 URL

        Raises:
            PixivAPIError: API 调用失败时抛出
        """
        try:
            # 构建参数
            params: dict[str, Any] = {"mode": mode}
            if date:
                params["date"] = date

            # 获取第一页数据
            logger.info(f"Fetching ranking: mode={mode}, date={date}")
            json_result = self.api.illust_ranking(**params)

            if not json_result or not hasattr(json_result, "illusts"):
                raise PixivAPIError("Empty ranking result")

            # 提取作品数据
            works = self._extract_works(json_result.illusts)

            logger.info(f"Fetched {len(works)} works from ranking")
            return works

        except PixivAPIError:
            raise
        except Exception as e:
            error_msg = f"Failed to get ranking: {e}"
            logger.error(error_msg)
            raise PixivAPIError(error_msg) from e

    @retry_on_network_error
    def get_ranking_all(
        self, mode: str = "day", date: str | None = None
    ) -> list[dict[str, Any]]:
        """获取排行榜所有数据(自动跟随 next_url)

        获取指定模式和日期的排行榜所有数据,包括所有分页。

        Args:
            mode: 排行榜模式
                - 常规: day, week, month
                - 分类: day_male, day_female, week_original, week_rookie, day_manga
                - R18: day_r18, day_male_r18, day_female_r18, week_r18, week_r18g
            date: 日期字符串 YYYY-MM-DD (默认为今天)

        Returns:
            作品列表,包含所有页面的数据,每个作品包含:
                - id: 作品 ID
                - title: 标题
                - author: 作者名
                - image_url: 图片 URL

        Raises:
            PixivAPIError: API 调用失败时抛出
        """
        try:
            # 构建参数
            params: dict[str, Any] = {"mode": mode}
            if date:
                params["date"] = date

            # 获取第一页数据
            logger.info(f"Fetching ranking: mode={mode}, date={date}")
            json_result = self.api.illust_ranking(**params)

            if not json_result or not hasattr(json_result, "illusts"):
                raise PixivAPIError("Empty ranking result")

            # 累积作品
            all_works = []
            all_works.extend(self._extract_works(json_result.illusts))
            page_count = 1

            # 自动跟随 next_url
            next_url = getattr(json_result, "next_url", None)
            while next_url:
                page_count += 1
                logger.debug(f"Fetching page {page_count}: {next_url}")
                next_qs = self.api.parse_qs(next_url)
                json_result = self.api.illust_ranking(**next_qs)

                if not json_result or not hasattr(json_result, "illusts"):
                    break

                all_works.extend(self._extract_works(json_result.illusts))
                next_url = getattr(json_result, "next_url", None)

            logger.info(
                f"Fetched {len(all_works)} works from {page_count} pages"
            )
            return all_works

        except PixivAPIError:
            raise
        except Exception as e:
            error_msg = f"Failed to get ranking: {e}"
            logger.error(error_msg)
            raise PixivAPIError(error_msg) from e

    def get_ranking_range(
        self,
        mode: str = "day",
        date: str | None = None,
        limit: int | None = None,
        offset: int = 0
    ) -> list[dict[str, Any]]:
        """获取排行榜指定范围数据

        复用 get_ranking_all() 获取所有数据,然后在内存中进行切片。

        Args:
            mode: 排行榜模式
                - 常规: day, week, month
                - 分类: day_male, day_female, week_original, week_rookie, day_manga
                - R18: day_r18, day_male_r18, day_female_r18, week_r18, week_r18g
            date: 日期字符串 YYYY-MM-DD (None = 最新可用排行榜)
            limit: 最多获取的作品数 (None = 无限制)
            offset: 跳过的作品数 (默认 0)

        Returns:
            作品列表 (已应用范围过滤)

        Note:
            底层仍然调用 get_ranking_all() 获取所有数据,然后在内存中切片。
            这是 Pixiv API 的限制 - API 使用 next_url 分页机制,不支持直接指定 offset。

        Example:
            >>> client.get_ranking_range(mode="day", limit=10)  # 前 10 个作品
            >>> client.get_ranking_range(mode="day", offset=100)  # 从第 100 个开始
            >>> client.get_ranking_range(mode="day", limit=50, offset=100)  # 第 100-149 个
        """
        # 获取所有数据
        all_works = self.get_ranking_all(mode=mode, date=date)

        # 应用范围过滤
        start = offset
        end = offset + limit if limit is not None else len(all_works)

        logger.info(f"Returning works [{start}:{end}] of {len(all_works)} total")
        return all_works[start:end]

    def _extract_works(self, illusts: list) -> list[dict]:
        """从 illusts 列表提取作品数据

        Args:
            illusts: API 返回的 illusts 列表

        Returns:
            作品字典列表
        """
        works = []
        for illust in illusts:
            work = {
                "id": illust.id,
                "title": illust.title,
                "author": illust.user.name,
                "image_url": illust.image_urls.large,
            }
            works.append(work)
        return works

    @retry_on_network_error
    def get_artwork_metadata(self, illust_id: int) -> ArtworkMetadata:
        """获取单个作品的完整元数据

        Args:
            illust_id: 作品 ID

        Returns:
            ArtworkMetadata: 包含完整元数据的模型对象

        Raises:
            PixivAPIError: API 调用失败时抛出
        """
        try:
            logger.info(f"Fetching metadata for illust_id={illust_id}")
            result = self.api.illust_detail(illust_id)
            illust = result.illust

            # 提取标签
            tags = [
                ArtworkTag(
                    name=tag.name,
                    translated_name=tag.translated_name
                )
                for tag in illust.tags
            ]

            # 提取统计数据
            statistics = ArtworkStatistics(
                bookmark_count=illust.total_bookmarks,
                view_count=illust.total_view,
                comment_count=illust.total_comments,
            )

            # 构建元数据模型
            metadata = ArtworkMetadata(
                illust_id=illust.id,
                title=illust.title,
                author=illust.user.name,
                author_id=illust.user.id,
                tags=tags,
                statistics=statistics,
            )

            logger.debug(f"Metadata fetched: {metadata.title} ({len(tags)} tags)")
            return metadata

        except Exception as e:
            error_msg = f"Failed to get metadata for {illust_id}: {e}"
            logger.error(error_msg)
            raise PixivAPIError(error_msg) from e
