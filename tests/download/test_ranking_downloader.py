"""排行榜下载编排器测试"""

import datetime
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

from gallery_dl_auto.api.pixiv_client import PixivAPIError, PixivClient
from gallery_dl_auto.config.download_config import DownloadConfig
from gallery_dl_auto.download.ranking_downloader import RankingDownloader
from gallery_dl_auto.models.artwork import ArtworkMetadata, ArtworkStatistics, ArtworkTag


def test_download_ranking_success(tmp_path: Path) -> None:
    """测试成功下载排行榜"""
    # Mock API 客户端
    mock_client = MagicMock(spec=PixivClient)
    mock_client.get_ranking_all.return_value = [
        {
            "id": 12345,
            "title": "美丽的风景",
            "author": "artist1",
            "image_url": "https://example.com/image1.jpg",
        },
        {
            "id": 67890,
            "title": "可爱的角色",
            "author": "artist2",
            "image_url": "https://example.com/image2.jpg",
        },
    ]

    # Mock download_file
    with patch("gallery_dl_auto.download.ranking_downloader.download_file") as mock_download:
        mock_download.return_value = {
            "success": True,
            "filepath": str(tmp_path / "day-2026-02-25" / "12345_美丽的风景.jpg"),
            "error": None,
        }

        downloader = RankingDownloader(mock_client, tmp_path)
        results = downloader.download_ranking(mode="day", date="2026-02-25")

        # 验证结果结构
        assert results["total"] == 2
        assert len(results["success"]) == 2
        assert len(results["failed"]) == 0

        # 验证 API 调用
        mock_client.get_ranking_all.assert_called_once_with(mode="day", date="2026-02-25")

        # 验证下载调用
        assert mock_download.call_count == 2


def test_download_ranking_api_error(tmp_path: Path) -> None:
    """测试 API 错误处理"""
    # Mock API 客户端抛出错误
    mock_client = MagicMock(spec=PixivClient)
    mock_client.get_ranking_all.side_effect = PixivAPIError("Authentication failed")

    downloader = RankingDownloader(mock_client, tmp_path)
    results = downloader.download_ranking(mode="day", date="2026-02-25")

    # 验证错误处理
    assert results["total"] == 0
    assert len(results["success"]) == 0
    assert len(results["failed"]) == 0
    assert "API 错误" in results["error"]


def test_download_ranking_partial_failure(tmp_path: Path) -> None:
    """测试部分图片下载失败"""
    # Mock API 客户端
    mock_client = MagicMock(spec=PixivClient)
    mock_client.get_ranking_all.return_value = [
        {
            "id": 12345,
            "title": "美丽的风景",
            "author": "artist1",
            "image_url": "https://example.com/image1.jpg",
        },
        {
            "id": 67890,
            "title": "可爱的角色",
            "author": "artist2",
            "image_url": "https://example.com/image2.jpg",
        },
    ]

    # Mock download_file - 第一次成功,第二次失败3次
    with patch("gallery_dl_auto.download.ranking_downloader.download_file") as mock_download:
        mock_download.side_effect = [
            {
                "success": True,
                "filepath": str(tmp_path / "day-2026-02-25" / "12345_美丽的风景.jpg"),
                "error": None,
            },
        ] + [
            {
                "success": False,
                "filepath": str(tmp_path / "day-2026-02-25" / "67890_可爱的角色.jpg"),
                "error": "HTTP 错误: 404",
            }
        ] * 3  # 重试3次

        # 使用自定义配置加速测试
        config = DownloadConfig(retry_delay=0.01)
        downloader = RankingDownloader(mock_client, tmp_path, config)
        results = downloader.download_ranking(mode="day", date="2026-02-25")

        # 验证部分失败处理
        assert results["total"] == 2
        assert len(results["success"]) == 1
        assert len(results["failed"]) == 1
        assert results["failed"][0]["illust_id"] == 67890
        assert "HTTP 错误: 404" in results["failed"][0]["error"]


def test_download_ranking_creates_directory(tmp_path: Path) -> None:
    """测试目录创建"""
    # Mock API 客户端
    mock_client = MagicMock(spec=PixivClient)
    mock_client.get_ranking_all.return_value = []

    downloader = RankingDownloader(mock_client, tmp_path)
    downloader.download_ranking(mode="day", date="2026-02-25")

    # 验证目录创建
    expected_dir = tmp_path / "day-2026-02-25"
    assert expected_dir.exists()
    assert expected_dir.is_dir()


def test_download_ranking_rate_limiting(tmp_path: Path) -> None:
    """测试速率控制调用"""
    # Mock API 客户端
    mock_client = MagicMock(spec=PixivClient)
    mock_client.get_ranking_all.return_value = [
        {
            "id": 12345,
            "title": "美丽的风景",
            "author": "artist1",
            "image_url": "https://example.com/image1.jpg",
        }
    ]

    # Mock download_file 和 rate_limit_delay
    with (
        patch("gallery_dl_auto.download.ranking_downloader.download_file") as mock_download,
        patch("gallery_dl_auto.download.ranking_downloader.rate_limit_delay") as mock_delay,
    ):
        mock_download.return_value = {
            "success": True,
            "filepath": str(tmp_path / "day-2026-02-25" / "12345_美丽的风景.jpg"),
            "error": None,
        }

        downloader = RankingDownloader(mock_client, tmp_path)
        downloader.download_ranking(mode="day", date="2026-02-25")

        # 验证速率控制调用
        mock_delay.assert_called_once_with(2.5, jitter=1.0)  # 使用默认配置


def test_download_ranking_filename_sanitization(tmp_path: Path) -> None:
    """测试文件名清理"""
    # Mock API 客户端 - 标题包含 Windows 非法字符
    mock_client = MagicMock(spec=PixivClient)
    mock_client.get_ranking_all.return_value = [
        {
            "id": 12345,
            "title": "美丽的风景<测试>",
            "author": "artist1",
            "image_url": "https://example.com/image1.jpg",
        }
    ]

    # Mock 元数据获取失败,使用基础数据
    mock_client.get_artwork_metadata.side_effect = PixivAPIError("Metadata API error")

    # Mock download_file
    with patch("gallery_dl_auto.download.ranking_downloader.download_file") as mock_download:
        mock_download.return_value = {
            "success": True,
            "filepath": str(tmp_path / "day-2026-02-25" / "12345_美丽的风景测试.jpg"),
            "error": None,
        }

        # 使用自定义配置加速测试
        config = DownloadConfig(retry_delay=0.01)
        downloader = RankingDownloader(mock_client, tmp_path, config)
        downloader.download_ranking(mode="day", date="2026-02-25")

        # 验证文件名已清理 (非法字符 < 和 > 被移除)
        called_filepath = mock_download.call_args[0][1]
        assert called_filepath.name == "12345_美丽的风景测试.jpg"


def test_download_ranking_default_date(tmp_path: Path) -> None:
    """测试默认日期 (今天)"""
    # Mock API 客户端
    mock_client = MagicMock(spec=PixivClient)
    mock_client.get_ranking_all.return_value = []

    downloader = RankingDownloader(mock_client, tmp_path)
    today = datetime.date.today().strftime("%Y-%m-%d")
    downloader.download_ranking(mode="day")

    # 验证使用今天的日期
    expected_dir = tmp_path / f"day-{today}"
    assert expected_dir.exists()


def test_download_with_path_template(tmp_path: Path) -> None:
    """测试使用路径模板"""
    # Mock API 客户端
    mock_client = MagicMock(spec=PixivClient)
    mock_client.get_ranking_all.return_value = [
        {
            "id": 12345,
            "title": "美丽的风景",
            "author": "artist1",
            "image_url": "https://example.com/image1.jpg",
        }
    ]

    # Mock 元数据
    mock_metadata = MagicMock(spec=ArtworkMetadata)
    mock_metadata.title = "美丽的风景"
    mock_metadata.author = "artist1"
    mock_metadata.author_id = 111
    mock_metadata.tags = []  # 添加 tags 属性
    mock_metadata.statistics = MagicMock()  # 添加 statistics 属性
    mock_client.get_artwork_metadata.return_value = mock_metadata

    # Mock download_file
    with patch("gallery_dl_auto.download.ranking_downloader.download_file") as mock_download:
        mock_download.return_value = {
            "success": True,
            "filepath": str(tmp_path / "artist1" / "美丽的风景.jpg"),
            "error": None,
        }

        downloader = RankingDownloader(mock_client, tmp_path)
        results = downloader.download_ranking(
            mode="day",
            date="2026-02-25",
            path_template="{author}/{title}.jpg"
        )

        # 验证结果
        assert results["total"] == 1
        assert len(results["success"]) == 1

        # 验证文件路径按模板构建
        called_filepath = mock_download.call_args[0][1]
        assert called_filepath == tmp_path / "artist1" / "美丽的风景.jpg"


def test_download_with_metadata(tmp_path: Path) -> None:
    """测试元数据获取"""
    # Mock API 客户端
    mock_client = MagicMock(spec=PixivClient)
    mock_client.get_ranking_all.return_value = [
        {
            "id": 12345,
            "title": "美丽的风景",
            "author": "artist1",
            "image_url": "https://example.com/image1.jpg",
        }
    ]

    # Mock 元数据
    mock_tag1 = MagicMock(spec=ArtworkTag)
    mock_tag1.name = "风景"
    mock_tag1.translated_name = "landscape"
    mock_tag1.model_dump.return_value = {"name": "风景", "translated_name": "landscape"}

    mock_tag2 = MagicMock(spec=ArtworkTag)
    mock_tag2.name = "原创"
    mock_tag2.translated_name = None
    mock_tag2.model_dump.return_value = {"name": "原创", "translated_name": None}

    mock_statistics = MagicMock(spec=ArtworkStatistics)
    mock_statistics.bookmark_count = 100
    mock_statistics.view_count = 500
    mock_statistics.comment_count = 20
    mock_statistics.model_dump.return_value = {
        "bookmark_count": 100,
        "view_count": 500,
        "comment_count": 20
    }

    mock_metadata = MagicMock(spec=ArtworkMetadata)
    mock_metadata.title = "美丽的风景"
    mock_metadata.author = "artist1"
    mock_metadata.author_id = 111
    mock_metadata.tags = [mock_tag1, mock_tag2]
    mock_metadata.statistics = mock_statistics

    mock_client.get_artwork_metadata.return_value = mock_metadata

    # Mock download_file
    with patch("gallery_dl_auto.download.ranking_downloader.download_file") as mock_download:
        mock_download.return_value = {
            "success": True,
            "filepath": str(tmp_path / "day-2026-02-25" / "12345_美丽的风景.jpg"),
            "error": None,
        }

        downloader = RankingDownloader(mock_client, tmp_path)
        results = downloader.download_ranking(mode="day", date="2026-02-25")

        # 验证结果包含元数据字段
        assert len(results["success"]) == 1
        success_item = results["success"][0]
        assert "tags" in success_item
        assert "statistics" in success_item
        assert len(success_item["tags"]) == 2
        assert success_item["statistics"]["bookmark_count"] == 100


def test_download_metadata_fallback(tmp_path: Path) -> None:
    """测试元数据获取失败的 fallback"""
    # Mock API 客户端
    mock_client = MagicMock(spec=PixivClient)
    mock_client.get_ranking_all.return_value = [
        {
            "id": 12345,
            "title": "美丽的风景",
            "author": "artist1",
            "image_url": "https://example.com/image1.jpg",
        }
    ]

    # Mock 元数据获取失败
    mock_client.get_artwork_metadata.side_effect = PixivAPIError("Metadata API error")

    # Mock download_file
    with patch("gallery_dl_auto.download.ranking_downloader.download_file") as mock_download:
        mock_download.return_value = {
            "success": True,
            "filepath": str(tmp_path / "day-2026-02-25" / "12345_美丽的风景.jpg"),
            "error": None,
        }

        downloader = RankingDownloader(mock_client, tmp_path)
        results = downloader.download_ranking(mode="day", date="2026-02-25")

        # 验证使用排行榜基础数据继续下载
        assert len(results["success"]) == 1
        success_item = results["success"][0]
        assert success_item["illust_id"] == 12345
        assert success_item["title"] == "美丽的风景"
        assert success_item["author"] == "artist1"

        # 验证结果不包含 tags 和 statistics 字段
        assert "tags" not in success_item
        assert "statistics" not in success_item


def test_download_with_all_template_variables(tmp_path: Path) -> None:
    """测试所有模板变量"""
    # Mock API 客户端
    mock_client = MagicMock(spec=PixivClient)
    mock_client.get_ranking_all.return_value = [
        {
            "id": 12345,
            "title": "美丽的风景",
            "author": "artist1",
            "image_url": "https://example.com/image1.jpg",
        }
    ]

    # Mock 元数据
    mock_metadata = MagicMock(spec=ArtworkMetadata)
    mock_metadata.title = "美丽的风景"
    mock_metadata.author = "artist1"
    mock_metadata.author_id = 111
    mock_metadata.tags = []  # 添加 tags 属性
    mock_metadata.statistics = MagicMock()  # 添加 statistics 属性
    mock_client.get_artwork_metadata.return_value = mock_metadata

    # Mock download_file
    with patch("gallery_dl_auto.download.ranking_downloader.download_file") as mock_download:
        mock_download.return_value = {
            "success": True,
            "filepath": str(tmp_path / "day" / "2026-02-25" / "12345" / "美丽的风景_artist1_111.jpg"),
            "error": None,
        }

        downloader = RankingDownloader(mock_client, tmp_path)
        results = downloader.download_ranking(
            mode="day",
            date="2026-02-25",
            path_template="{mode}/{date}/{illust_id}/{title}_{author}_{author_id}.jpg"
        )

        # 验证结果
        assert len(results["success"]) == 1

        # 验证文件路径包含所有变量
        called_filepath = mock_download.call_args[0][1]
        assert "day" in str(called_filepath)
        assert "2026-02-25" in str(called_filepath)
        assert "12345" in str(called_filepath)
        assert "美丽的风景" in str(called_filepath)
        assert "artist1" in str(called_filepath)
        assert "111" in str(called_filepath)


def test_download_ranking_with_resume(tmp_path: Path) -> None:
    """测试断点续传"""
    # 创建部分进度文件
    progress_file = tmp_path / "week-2026-02-18" / ".progress.json"
    progress_file.parent.mkdir(parents=True, exist_ok=True)

    from gallery_dl_auto.download.progress_manager import DownloadProgress
    progress = DownloadProgress(
        mode="week",
        date="2026-02-18",
        downloaded_ids={1},  # 已下载第一个作品
        failed_ids=set()
    )
    progress.save(progress_file)

    # 模拟排行榜数据
    mock_client = MagicMock(spec=PixivClient)
    mock_client.get_ranking_all.return_value = [
        {'id': 1, 'title': 'Work 1', 'author': 'Author 1', 'image_url': 'url1'},
        {'id': 2, 'title': 'Work 2', 'author': 'Author 2', 'image_url': 'url2'},
    ]

    with patch("gallery_dl_auto.download.ranking_downloader.download_file") as mock_download:
        mock_download.return_value = {
            'success': True,
            'filepath': str(tmp_path / "week-2026-02-18" / "2_Work 2.jpg"),
            'error': None,
        }

        downloader = RankingDownloader(mock_client, tmp_path)
        result = downloader.download_ranking(mode="week", date="2026-02-18")

        # 验证跳过了已下载的作品
        assert result['total'] == 2
        assert len(result['success']) == 1  # 只下载了第二个

        # 验证进度文件被删除
        assert not progress_file.exists()


def test_download_ranking_retry_on_failure(tmp_path: Path) -> None:
    """测试下载失败重试"""
    mock_client = MagicMock(spec=PixivClient)
    mock_client.get_ranking_all.return_value = [
        {'id': 1, 'title': 'Work 1', 'author': 'Author 1', 'image_url': 'url1'},
    ]

    call_count = 0

    def mock_download(url, path):
        nonlocal call_count
        call_count += 1
        if call_count == 1:
            return {'success': False, 'error': 'Network error'}
        return {'success': True, 'filepath': str(path), 'error': None}

    with patch("gallery_dl_auto.download.ranking_downloader.download_file", side_effect=mock_download):
        # 使用自定义配置减少重试延迟
        config = DownloadConfig(max_retries=3, retry_delay=0.1)
        downloader = RankingDownloader(mock_client, tmp_path, config)
        result = downloader.download_ranking(
            mode="day",
            date="2026-02-25"
        )

        # 验证重试成功
        assert len(result['success']) == 1
        assert call_count == 2  # 第一次失败,第二次成功


def test_download_with_custom_config(tmp_path: Path) -> None:
    """测试自定义配置"""
    # 创建自定义配置
    config = DownloadConfig(
        batch_size=50,
        image_delay=1.0,
        max_retries=2
    )

    mock_client = MagicMock(spec=PixivClient)
    mock_client.get_ranking_all.return_value = []

    downloader = RankingDownloader(mock_client, tmp_path, config)

    # 验证配置被应用
    assert downloader.config.batch_size == 50
    assert downloader.config.image_delay == 1.0
    assert downloader.config.max_retries == 2
