"""测试作品元数据模型"""

from gallery_dl_auto.models.artwork import (
    ArtworkMetadata,
    ArtworkStatistics,
    ArtworkTag,
)


def test_artwork_statistics() -> None:
    """测试统计数据模型创建"""
    stats = ArtworkStatistics(
        bookmark_count=1000,
        view_count=5000,
        comment_count=50,
    )

    assert stats.bookmark_count == 1000
    assert stats.view_count == 5000
    assert stats.comment_count == 50


def test_artwork_tag_with_translation() -> None:
    """测试带翻译的标签"""
    tag = ArtworkTag(name="风景", translated_name="landscape")

    assert tag.name == "风景"
    assert tag.translated_name == "landscape"


def test_artwork_tag_without_translation() -> None:
    """测试不带翻译的标签"""
    tag = ArtworkTag(name="插画")

    assert tag.name == "插画"
    assert tag.translated_name is None


def test_artwork_metadata() -> None:
    """测试完整元数据模型创建"""
    metadata = ArtworkMetadata(
        illust_id=12345,
        title="Beautiful Sunset",
        author="Artist",
        author_id=67890,
        tags=[
            ArtworkTag(name="风景", translated_name="landscape"),
            ArtworkTag(name="插画", translated_name="illustration"),
        ],
        statistics=ArtworkStatistics(
            bookmark_count=1000,
            view_count=5000,
            comment_count=50,
        ),
    )

    assert metadata.illust_id == 12345
    assert metadata.title == "Beautiful Sunset"
    assert metadata.author == "Artist"
    assert metadata.author_id == 67890
    assert len(metadata.tags) == 2
    assert metadata.statistics.bookmark_count == 1000


def test_artwork_metadata_serialization() -> None:
    """测试序列化为 dict/JSON"""
    metadata = ArtworkMetadata(
        illust_id=12345,
        title="Test",
        author="Artist",
        author_id=67890,
        tags=[ArtworkTag(name="tag1")],
        statistics=ArtworkStatistics(
            bookmark_count=100,
            view_count=500,
            comment_count=10,
        ),
    )

    # 序列化为 dict
    data = metadata.model_dump()
    assert isinstance(data, dict)
    assert data["illust_id"] == 12345
    assert data["title"] == "Test"
    assert isinstance(data["tags"], list)
    assert isinstance(data["statistics"], dict)

    # 序列化为 JSON
    json_str = metadata.model_dump_json()
    assert isinstance(json_str, str)
    assert "Test" in json_str
    assert "12345" in json_str


def test_artwork_metadata_from_dict() -> None:
    """测试从字典构建"""
    data = {
        "illust_id": 12345,
        "title": "Test Artwork",
        "author": "Test Author",
        "author_id": 67890,
        "tags": [
            {"name": "风景", "translated_name": "landscape"},
            {"name": "插画", "translated_name": None},
        ],
        "statistics": {
            "bookmark_count": 1000,
            "view_count": 5000,
            "comment_count": 50,
        },
    }

    metadata = ArtworkMetadata(**data)

    assert metadata.illust_id == 12345
    assert metadata.title == "Test Artwork"
    assert metadata.author == "Test Author"
    assert metadata.author_id == 67890
    assert len(metadata.tags) == 2
    assert metadata.tags[0].name == "风景"
    assert metadata.tags[0].translated_name == "landscape"
    assert metadata.tags[1].name == "插画"
    assert metadata.tags[1].translated_name is None
    assert metadata.statistics.bookmark_count == 1000
    assert metadata.statistics.view_count == 5000
    assert metadata.statistics.comment_count == 50
