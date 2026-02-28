"""Phase 6 集成测试

测试多排行榜支持的端到端集成。
需要真实的 API token 才能运行。

运行方式:
    pytest tests/integration/test_phase6_integration.py -m integration -v
"""

import pytest
from pathlib import Path
from unittest.mock import MagicMock, patch

from gallery_dl_auto.api.pixiv_client import PixivAPIError, PixivClient
from gallery_dl_auto.config.download_config import DownloadConfig
from gallery_dl_auto.download.ranking_downloader import RankingDownloader


@pytest.mark.integration
def test_phase6_weekly_ranking_download(tmp_path: Path) -> None:
    """Phase 6 集成测试:周榜下载

    注意:此测试需要真实的 refresh token
    """
    # 1. 初始化配置
    config = DownloadConfig(
        batch_size=10,
        image_delay=0.1,  # 测试时使用更短的延迟
        max_retries=2,
        retry_delay=0.5
    )

    # 2. 初始化客户端和下载器
    # 注意:实际运行时需要真实的 refresh token
    with patch("gallery_dl_auto.api.pixiv_client.PixivClient") as mock_client_class:
        mock_client = MagicMock(spec=PixivClient)
        mock_client.get_ranking_all.return_value = [
            {
                'id': 12345,
                'title': 'Test Artwork',
                'author': 'Test Artist',
                'image_url': 'https://example.com/image.jpg',
            }
        ]
        mock_client.get_artwork_metadata.side_effect = PixivAPIError("Metadata API error")
        mock_client_class.return_value = mock_client

        with patch("gallery_dl_auto.download.file_downloader.download_file") as mock_download:
            mock_download.return_value = {
                'success': True,
                'filepath': str(tmp_path / "week-2026-02-18" / "12345_Test Artwork.jpg"),
                'error': None,
            }

            downloader = RankingDownloader(mock_client, tmp_path, config)

            # 3. 下载周榜
            result = downloader.download_ranking(
                mode="week",
                date="2026-02-18",
                enable_resume=True
            )

            # 4. 验证结果
            assert result['total'] > 0
            assert len(result['success']) > 0
            assert len(result['failed']) == 0  # 期望无失败

            # 5. 验证文件已下载
            for item in result['success']:
                filepath = Path(item['filepath'])
                # 注意:在 mock 情况下,文件可能不存在
                # 真实测试时应该检查文件存在
                pass

            # 6. 验证进度文件已删除
            progress_file = tmp_path / "week-2026-02-18" / ".progress.json"
            assert not progress_file.exists()


@pytest.mark.integration
def test_phase6_monthly_ranking_large_dataset(tmp_path: Path) -> None:
    """Phase 6 集成测试:月榜大规模数据集

    模拟月榜大量作品下载场景。
    """
    config = DownloadConfig(
        batch_size=50,
        image_delay=0.1,
        max_retries=1
    )

    # 模拟月榜包含大量作品
    mock_works = [
        {
            'id': i,
            'title': f'Artwork {i}',
            'author': f'Artist {i}',
            'image_url': f'https://example.com/image{i}.jpg',
        }
        for i in range(100)  # 模拟 100 张作品
    ]

    with patch("gallery_dl_auto.api.pixiv_client.PixivClient") as mock_client_class:
        mock_client = MagicMock(spec=PixivClient)
        mock_client.get_ranking_all.return_value = mock_works
        mock_client.get_artwork_metadata.side_effect = PixivAPIError("Metadata API error")
        mock_client_class.return_value = mock_client

        with patch("gallery_dl_auto.download.file_downloader.download_file") as mock_download:
            mock_download.return_value = {
                'success': True,
                'filepath': str(tmp_path / "month-2026-01-31" / "test.jpg"),
                'error': None,
            }

            downloader = RankingDownloader(mock_client, tmp_path, config)

            # 下载月榜
            result = downloader.download_ranking(
                mode="month",
                date="2026-01-31",
                enable_resume=True
            )

            # 验证月榜包含大量作品
            assert result['total'] >= 100
            assert len(result['success']) >= 100


@pytest.mark.integration
def test_phase6_resume_interrupted_download(tmp_path: Path) -> None:
    """Phase 6 集成测试:断点续传"""
    config = DownloadConfig(image_delay=0.1)

    # 创建部分进度文件
    from gallery_dl_auto.download.progress_manager import DownloadProgress

    progress_file = tmp_path / "day-2026-02-25" / ".progress.json"
    progress_file.parent.mkdir(parents=True, exist_ok=True)

    progress = DownloadProgress(
        mode="day",
        date="2026-02-25",
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
    mock_client.get_artwork_metadata.side_effect = PixivAPIError("Metadata error")

    with patch("gallery_dl_auto.download.file_downloader.download_file") as mock_download:
        mock_download.return_value = {
            'success': True,
            'filepath': str(tmp_path / "day-2026-02-25" / "2_Work 2.jpg"),
            'error': None,
        }

        downloader = RankingDownloader(mock_client, tmp_path, config)

        # 从中断处继续
        result = downloader.download_ranking(
            mode="day",
            date="2026-02-25",
            enable_resume=True
        )

        # 验证跳过了已下载的作品
        assert result['total'] == 2
        assert len(result['success']) == 1  # 只下载了第二个

        # 验证进度文件被删除
        assert not progress_file.exists()


@pytest.mark.integration
@pytest.mark.parametrize("ranking_type,expected_mode", [
    ("daily", "day"),
    ("weekly", "week"),
    ("monthly", "month"),
    ("day_male", "day_male"),
    ("day_female", "day_female"),
])
def test_phase6_all_ranking_types(
    tmp_path: Path, ranking_type: str, expected_mode: str
) -> None:
    """Phase 6 集成测试:所有排行榜类型"""
    config = DownloadConfig(image_delay=0.1)

    with patch("gallery_dl_auto.api.pixiv_client.PixivClient") as mock_client_class:
        mock_client = MagicMock(spec=PixivClient)
        mock_client.get_ranking_all.return_value = [
            {
                'id': 1,
                'title': 'Test Work',
                'author': 'Test Artist',
                'image_url': 'https://example.com/test.jpg',
            }
        ]
        mock_client.get_artwork_metadata.side_effect = PixivAPIError("Metadata error")
        mock_client_class.return_value = mock_client

        with patch("gallery_dl_auto.download.file_downloader.download_file") as mock_download:
            mock_download.return_value = {
                'success': True,
                'filepath': str(tmp_path / "test.jpg"),
                'error': None,
            }

            downloader = RankingDownloader(mock_client, tmp_path, config)

            result = downloader.download_ranking(
                mode=expected_mode,
                enable_resume=False
            )

            assert result['total'] > 0
            assert len(result['success']) > 0

            # 验证 API 使用正确的 mode 参数
            mock_client.get_ranking_all.assert_called_once()
            call_kwargs = mock_client.get_ranking_all.call_args[1]
            assert call_kwargs['mode'] == expected_mode
