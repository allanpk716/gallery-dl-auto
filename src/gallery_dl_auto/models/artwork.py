"""作品元数据 Pydantic 模型

提供结构化的元数据建模,包括标签和统计数据。
"""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict


class ArtworkStatistics(BaseModel):
    """作品统计数据

    Attributes:
        bookmark_count: 收藏数
        view_count: 浏览量
        comment_count: 评论数
    """

    bookmark_count: int
    view_count: int
    comment_count: int


class ArtworkTag(BaseModel):
    """作品标签

    Attributes:
        name: 标签名称
        translated_name: 翻译后的标签名 (可选)
    """

    name: str
    translated_name: str | None = None


class ArtworkMetadata(BaseModel):
    """作品完整元数据

    Attributes:
        illust_id: 作品 ID
        title: 作品标题
        author: 作者名
        author_id: 作者 ID
        tags: 标签列表
        statistics: 统计数据
    """

    model_config = ConfigDict(from_attributes=True)

    illust_id: int
    title: str
    author: str
    author_id: int
    tags: list[ArtworkTag]
    statistics: ArtworkStatistics
