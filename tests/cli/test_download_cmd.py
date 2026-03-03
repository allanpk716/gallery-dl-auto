"""Download command tests"""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

from click.testing import CliRunner
from omegaconf import DictConfig

from gallery_dl_auto.api.pixiv_client import PixivAPIError
from gallery_dl_auto.cli.download_cmd import download
from gallery_dl_auto.models.error_response import BatchDownloadResult


def make_mock_config(download_config: dict | None = None) -> DictConfig:
    """创建模拟的配置对象"""
    config_dict = {"download": download_config or {}}
    return DictConfig(config_dict)


def test_download_success(tmp_path: Path) -> None:
    """Test successful download"""
    # Mock token storage
    with (
        patch(
            "gallery_dl_auto.cli.download_cmd.get_default_token_storage"
        ) as mock_storage,
        patch("gallery_dl_auto.cli.download_cmd.PixivClient") as mock_client_class,
        patch(
            "gallery_dl_auto.cli.download_cmd.RankingDownloader"
        ) as mock_downloader_class,
    ):
        # Setup mock token
        mock_storage_instance = MagicMock()
        mock_storage_instance.load_token.return_value = {"refresh_token": "test_token"}
        mock_storage.return_value = mock_storage_instance

        # Setup mock client
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        # Setup mock downloader
        mock_downloader = MagicMock()
        mock_downloader.download_ranking.return_value = BatchDownloadResult(
            success=True,
            total=2,
            downloaded=1,
            failed=0,
            skipped=0,
            success_list=[12345],
            failed_errors=[],
            output_dir=str(tmp_path),
        )
        mock_downloader_class.return_value = mock_downloader

        # Run command with required --type parameter
        runner = CliRunner()
        result = runner.invoke(
            download,
            ["--type", "daily", "--date", "2026-02-25"],
            obj=make_mock_config()
        )

        # Verify output
        assert result.exit_code == 0
        output = json.loads(result.output)
        assert output["success"] is True
        assert output["total"] == 2
        assert output["downloaded"] == 1
        assert output["failed"] == 0


def test_download_no_token() -> None:
    """Test error handling when no token found"""
    # Mock token storage
    with patch(
        "gallery_dl_auto.cli.download_cmd.get_default_token_storage"
    ) as mock_storage:
        # Setup mock token (no token)
        mock_storage_instance = MagicMock()
        mock_storage_instance.load_token.return_value = None
        mock_storage.return_value = mock_storage_instance

        # Run command with required --type parameter
        runner = CliRunner()
        result = runner.invoke(
            download,
            ["--type", "daily"],
            obj=make_mock_config()
        )

        # Verify error handling
        assert result.exit_code == 1
        output = json.loads(result.output)
        assert output["success"] is False
        assert "No token found" in output["error"]["message"]


def test_download_auth_failure() -> None:
    """Test authentication failure handling"""
    # Mock token storage
    with (
        patch(
            "gallery_dl_auto.cli.download_cmd.get_default_token_storage"
        ) as mock_storage,
        patch("gallery_dl_auto.cli.download_cmd.PixivClient") as mock_client_class,
    ):
        # Setup mock token
        mock_storage_instance = MagicMock()
        mock_storage_instance.load_token.return_value = {"refresh_token": "invalid_token"}
        mock_storage.return_value = mock_storage_instance

        # Setup mock client (authentication failure)
        mock_client_class.side_effect = PixivAPIError("Authentication failed")

        # Run command with required --type parameter
        runner = CliRunner()
        result = runner.invoke(
            download,
            ["--type", "daily"],
            obj=make_mock_config()
        )

        # Verify error handling
        assert result.exit_code == 1
        # Check if output is not empty before parsing
        if result.output.strip():
            output = json.loads(result.output)
            assert "error_code" in output or "error" in output
            if "error_code" in output:
                # StructuredError format
                assert "Authentication" in output.get("message", "") or "Authentication" in output.get("original_error", "")
        else:
            # Output is empty, just check exit code
            pass


def test_download_with_date() -> None:
    """Test downloading with specific date"""
    # Mock token storage
    with (
        patch(
            "gallery_dl_auto.cli.download_cmd.get_default_token_storage"
        ) as mock_storage,
        patch("gallery_dl_auto.cli.download_cmd.PixivClient") as mock_client_class,
        patch("gallery_dl_auto.cli.download_cmd.RankingDownloader") as mock_downloader_class,
    ):
        # Setup mock token
        mock_storage_instance = MagicMock()
        mock_storage_instance.load_token.return_value = {"refresh_token": "test_token"}
        mock_storage.return_value = mock_storage_instance

        # Setup mock client
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        # Setup mock downloader
        mock_downloader = MagicMock()
        mock_downloader.download_ranking.return_value = BatchDownloadResult(
            success=True,
            total=0,
            downloaded=0,
            failed=0,
            skipped=0,
            success_list=[],
            failed_errors=[],
            output_dir=str(tmp_path),
        )
        mock_downloader_class.return_value = mock_downloader

        # Run command with --type and --date
        runner = CliRunner()
        result = runner.invoke(
            download,
            ["--type", "daily", "--date", "2026-02-20"],
            obj=make_mock_config()
        )

        # Verify date parameter passed correctly (with tracker parameter)
        mock_downloader.download_ranking.assert_called_once()
        call_kwargs = mock_downloader.download_ranking.call_args[1]
        assert call_kwargs["mode"] == "day"
        assert call_kwargs["date"] == "2026-02-20"
        assert call_kwargs["path_template"] is None
        assert "tracker" in call_kwargs
        assert result.exit_code == 0


def test_download_custom_output() -> None:
    """Test custom output directory"""
    # Mock token storage
    with (
        patch(
            "gallery_dl_auto.cli.download_cmd.get_default_token_storage"
        ) as mock_storage,
        patch("gallery_dl_auto.cli.download_cmd.PixivClient") as mock_client_class,
        patch("gallery_dl_auto.cli.download_cmd.RankingDownloader") as mock_downloader_class,
    ):
        # Setup mock token
        mock_storage_instance = MagicMock()
        mock_storage_instance.load_token.return_value = {"refresh_token": "test_token"}
        mock_storage.return_value = mock_storage_instance

        # Setup mock client
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        # Setup mock downloader
        mock_downloader = MagicMock()
        mock_downloader.download_ranking.return_value = BatchDownloadResult(
            success=True,
            total=0,
            downloaded=0,
            failed=0,
            skipped=0,
            success_list=[],
            failed_errors=[],
            output_dir=str(tmp_path),
        )
        mock_downloader_class.return_value = mock_downloader

        # Run command with --type and --output
        runner = CliRunner()
        result = runner.invoke(
            download,
            ["--type", "daily", "--output", "./custom-downloads"],
            obj=make_mock_config()
        )

        # Verify output directory
        call_kwargs = mock_downloader_class.call_args[1]
        assert call_kwargs['output_dir'] == Path("./custom-downloads")
        assert result.exit_code == 0


def test_download_partial_failure() -> None:
    """Test partial failure returns exit code 1"""
    # Mock token storage
    with (
        patch(
            "gallery_dl_auto.cli.download_cmd.get_default_token_storage"
        ) as mock_storage,
        patch("gallery_dl_auto.cli.download_cmd.PixivClient") as mock_client_class,
        patch("gallery_dl_auto.cli.download_cmd.RankingDownloader") as mock_downloader_class,
    ):
        # Setup mock token
        mock_storage_instance = MagicMock()
        mock_storage_instance.load_token.return_value = {"refresh_token": "test_token"}
        mock_storage.return_value = mock_storage_instance

        # Setup mock client
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        # Setup mock downloader (partial failure)
        mock_downloader = MagicMock()
        mock_downloader.download_ranking.return_value = {
            "total": 2,
            "success": [
                {
                    "illust_id": 12345,
                    "title": "美丽的风景",
                    "author": "artist1",
                    "filepath": "/downloads/image1.jpg",
                }
            ],
            "failed": [
                {
                    "illust_id": 67890,
                    "title": "可爱的角色",
                    "error": "HTTP 错误: 404",
                }
            ],
        }
        mock_downloader_class.return_value = mock_downloader

        # Run command with --type
        runner = CliRunner()
        result = runner.invoke(
            download,
            ["--type", "daily"],
            obj=make_mock_config()
        )

        # Verify exit code 1 (partial failure)
        assert result.exit_code == 1
        output = json.loads(result.output)
        assert output["success"] is True
        assert output["data"]["success_count"] == 1
        assert output["data"]["failed_count"] == 1
        assert len(output["data"]["failed_list"]) == 1


def test_download_json_output_encoding() -> None:
    """Test JSON output supports Chinese characters"""
    # Mock token storage
    with (
        patch(
            "gallery_dl_auto.cli.download_cmd.get_default_token_storage"
        ) as mock_storage,
        patch("gallery_dl_auto.cli.download_cmd.PixivClient") as mock_client_class,
        patch("gallery_dl_auto.cli.download_cmd.RankingDownloader") as mock_downloader_class,
    ):
        # Setup mock token
        mock_storage_instance = MagicMock()
        mock_storage_instance.load_token.return_value = {"refresh_token": "test_token"}
        mock_storage.return_value = mock_storage_instance

        # Setup mock client
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        # Setup mock downloader
        mock_downloader = MagicMock()
        mock_downloader.download_ranking.return_value = {
            "total": 1,
            "success": [
                {
                    "illust_id": 12345,
                    "title": "美丽的风景",
                    "author": "艺术家",
                    "filepath": "/downloads/美丽的风景.jpg",
                }
            ],
            "failed": [],
        }
        mock_downloader_class.return_value = mock_downloader

        # Run command with --type
        runner = CliRunner()
        result = runner.invoke(
            download,
            ["--type", "daily"],
            obj=make_mock_config()
        )

        # Verify Chinese characters are not escaped
        assert "美丽的风景" in result.output
        assert "艺术家" in result.output
        assert result.exit_code == 0


def test_download_with_path_template() -> None:
    """Test download with path template parameter"""
    # Mock token storage
    with (
        patch(
            "gallery_dl_auto.cli.download_cmd.get_default_token_storage"
        ) as mock_storage,
        patch("gallery_dl_auto.cli.download_cmd.PixivClient") as mock_client_class,
        patch("gallery_dl_auto.cli.download_cmd.RankingDownloader") as mock_downloader_class,
    ):
        # Setup mock token
        mock_storage_instance = MagicMock()
        mock_storage_instance.load_token.return_value = {"refresh_token": "test_token"}
        mock_storage.return_value = mock_storage_instance

        # Setup mock client
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        # Setup mock downloader
        mock_downloader = MagicMock()
        mock_downloader.download_ranking.return_value = {
            "total": 1,
            "success": [
                {
                    "illust_id": 12345,
                    "title": "Beautiful Sunset",
                    "author": "artist1",
                    "filepath": "/downloads/artist1/Beautiful Sunset.jpg",
                }
            ],
            "failed": [],
        }
        mock_downloader_class.return_value = mock_downloader

        # Run command with --type and path template
        runner = CliRunner()
        result = runner.invoke(
            download,
            ["--type", "daily", "--path-template", "{author}/{title}.jpg"],
            obj=make_mock_config()
        )

        # Verify path_template parameter passed correctly
        mock_downloader.download_ranking.assert_called_once()
        call_kwargs = mock_downloader.download_ranking.call_args[1]
        assert call_kwargs["path_template"] == "{author}/{title}.jpg"
        assert result.exit_code == 0


def test_download_json_output_with_metadata() -> None:
    """Test JSON output includes metadata"""
    # Mock token storage
    with (
        patch(
            "gallery_dl_auto.cli.download_cmd.get_default_token_storage"
        ) as mock_storage,
        patch("gallery_dl_auto.cli.download_cmd.PixivClient") as mock_client_class,
        patch("gallery_dl_auto.cli.download_cmd.RankingDownloader") as mock_downloader_class,
    ):
        # Setup mock token
        mock_storage_instance = MagicMock()
        mock_storage_instance.load_token.return_value = {"refresh_token": "test_token"}
        mock_storage.return_value = mock_storage_instance

        # Setup mock client
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        # Setup mock downloader with metadata
        mock_downloader = MagicMock()
        mock_downloader.download_ranking.return_value = {
            "total": 1,
            "success": [
                {
                    "illust_id": 12345,
                    "title": "Beautiful Sunset",
                    "author": "artist1",
                    "filepath": "/downloads/image1.jpg",
                    "tags": [
                        {"name": "sunset", "translated_name": "夕阳"},
                        {"name": "landscape", "translated_name": None},
                    ],
                    "statistics": {
                        "bookmark_count": 100,
                        "view_count": 500,
                        "comment_count": 20,
                    },
                }
            ],
            "failed": [],
        }
        mock_downloader_class.return_value = mock_downloader

        # Run command with --type
        runner = CliRunner()
        result = runner.invoke(
            download,
            ["--type", "daily"],
            obj=make_mock_config()
        )

        # Verify JSON output includes metadata fields
        assert result.exit_code == 0
        output = json.loads(result.output)
        assert output["success"] is True
        assert len(output["data"]["success_list"]) == 1

        success_item = output["data"]["success_list"][0]
        assert "tags" in success_item
        assert "statistics" in success_item
        assert len(success_item["tags"]) == 2
        assert success_item["statistics"]["bookmark_count"] == 100


def test_download_without_path_template() -> None:
    """Test download without path template uses default structure"""
    # Mock token storage
    with (
        patch(
            "gallery_dl_auto.cli.download_cmd.get_default_token_storage"
        ) as mock_storage,
        patch("gallery_dl_auto.cli.download_cmd.PixivClient") as mock_client_class,
        patch("gallery_dl_auto.cli.download_cmd.RankingDownloader") as mock_downloader_class,
    ):
        # Setup mock token
        mock_storage_instance = MagicMock()
        mock_storage_instance.load_token.return_value = {"refresh_token": "test_token"}
        mock_storage.return_value = mock_storage_instance

        # Setup mock client
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        # Setup mock downloader
        mock_downloader = MagicMock()
        mock_downloader.download_ranking.return_value = {
            "total": 1,
            "success": [
                {
                    "illust_id": 12345,
                    "title": "Beautiful Sunset",
                    "author": "artist1",
                    "filepath": "/downloads/day-2026-02-25/12345_Beautiful Sunset.jpg",
                }
            ],
            "failed": [],
        }
        mock_downloader_class.return_value = mock_downloader

        # Run command with --type and --date, without path template
        runner = CliRunner()
        result = runner.invoke(
            download,
            ["--type", "daily", "--date", "2026-02-25"],
            obj=make_mock_config()
        )

        # Verify path_template is None (default structure)
        mock_downloader.download_ranking.assert_called_once()
        call_kwargs = mock_downloader.download_ranking.call_args[1]
        assert call_kwargs["path_template"] is None
        assert result.exit_code == 0

        # Verify JSON output (path_template is excluded when None)
        output = json.loads(result.output)
        # path_template field is excluded by exclude_none=True
        assert "path_template" not in output["data"] or output["data"]["path_template"] is None


def test_download_weekly_ranking() -> None:
    """Test downloading weekly ranking (weekly -> week mapping)"""
    # Mock token storage
    with (
        patch(
            "gallery_dl_auto.cli.download_cmd.get_default_token_storage"
        ) as mock_storage,
        patch("gallery_dl_auto.cli.download_cmd.PixivClient") as mock_client_class,
        patch("gallery_dl_auto.cli.download_cmd.RankingDownloader") as mock_downloader_class,
    ):
        # Setup mock token
        mock_storage_instance = MagicMock()
        mock_storage_instance.load_token.return_value = {"refresh_token": "test_token"}
        mock_storage.return_value = mock_storage_instance

        # Setup mock client
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        # Setup mock downloader
        mock_downloader = MagicMock()
        mock_downloader.download_ranking.return_value = BatchDownloadResult(
            success=True,
            total=0,
            downloaded=0,
            failed=0,
            skipped=0,
            success_list=[],
            failed_errors=[],
            output_dir=str(tmp_path),
        )
        mock_downloader_class.return_value = mock_downloader

        # Run command with --type weekly
        runner = CliRunner()
        result = runner.invoke(
            download,
            ["--type", "weekly"],
            obj=make_mock_config()
        )

        # Verify mode is "week" (mapped from "weekly")
        mock_downloader.download_ranking.assert_called_once()
        call_kwargs = mock_downloader.download_ranking.call_args[1]
        assert call_kwargs["mode"] == "week"
        assert result.exit_code == 0


def test_download_invalid_type() -> None:
    """Test invalid ranking type error"""
    # Mock token storage
    with patch(
        "gallery_dl_auto.cli.download_cmd.get_default_token_storage"
    ) as mock_storage:
        # Setup mock token
        mock_storage_instance = MagicMock()
        mock_storage_instance.load_token.return_value = {"refresh_token": "test_token"}
        mock_storage.return_value = mock_storage_instance

        # Run command with invalid --type
        runner = CliRunner()
        result = runner.invoke(
            download,
            ["--type", "invalid_type"],
            obj=make_mock_config()
        )

        # Verify error message
        assert result.exit_code != 0
        assert "Invalid ranking type" in result.output
        assert "Valid types:" in result.output


def test_download_future_date() -> None:
    """Test future date validation error"""
    # Mock token storage
    with patch(
        "gallery_dl_auto.cli.download_cmd.get_default_token_storage"
    ) as mock_storage:
        # Setup mock token
        mock_storage_instance = MagicMock()
        mock_storage_instance.load_token.return_value = {"refresh_token": "test_token"}
        mock_storage.return_value = mock_storage_instance

        # Run command with future date
        runner = CliRunner()
        result = runner.invoke(
            download,
            ["--type", "daily", "--date", "2099-12-31"],
            obj=make_mock_config()
        )

        # Verify error message
        assert result.exit_code != 0
        assert "is in the future" in result.output


def test_download_missing_type() -> None:
    """Test missing required --type parameter"""
    # Mock token storage
    with patch(
        "gallery_dl_auto.cli.download_cmd.get_default_token_storage"
    ) as mock_storage:
        # Setup mock token
        mock_storage_instance = MagicMock()
        mock_storage_instance.load_token.return_value = {"refresh_token": "test_token"}
        mock_storage.return_value = mock_storage_instance

        # Run command without --type
        runner = CliRunner()
        result = runner.invoke(
            download,
            [],
            obj=make_mock_config()
        )

        # Verify error message
        assert result.exit_code != 0
        assert "Missing option" in result.output or "--type" in result.output


def test_download_with_custom_config_file() -> None:
    """测试从配置文件读取下载参数"""
    # Mock token storage
    with (
        patch(
            "gallery_dl_auto.cli.download_cmd.get_default_token_storage"
        ) as mock_storage,
        patch("gallery_dl_auto.cli.download_cmd.PixivClient") as mock_client_class,
        patch("gallery_dl_auto.cli.download_cmd.RankingDownloader") as mock_downloader_class,
    ):
        # Setup mock token
        mock_storage_instance = MagicMock()
        mock_storage_instance.load_token.return_value = {"refresh_token": "test_token"}
        mock_storage.return_value = mock_storage_instance

        # Setup mock client
        mock_client = MagicMock()
        mock_client_class.return_value = mock_client

        # Setup mock downloader
        mock_downloader = MagicMock()
        mock_downloader.download_ranking.return_value = BatchDownloadResult(
            success=True,
            total=0,
            downloaded=0,
            failed=0,
            skipped=0,
            success_list=[],
            failed_errors=[],
            output_dir=str(tmp_path),
        )
        mock_downloader_class.return_value = mock_downloader

        # Run command with custom config
        custom_config = {
            "batch_size": 50,
            "image_delay": 1.5,
            "max_retries": 2
        }
        runner = CliRunner()
        result = runner.invoke(
            download,
            ["--type", "daily"],
            obj=make_mock_config(custom_config)
        )

        # Verify config was passed to RankingDownloader
        assert result.exit_code == 0
        # Check that downloader was initialized with config
        call_kwargs = mock_downloader_class.call_args[1]
        config_arg = call_kwargs['config']
        assert config_arg.batch_size == 50
        assert config_arg.image_delay == 1.5
        assert config_arg.max_retries == 2


def test_download_all_ranking_types() -> None:
    """测试所有排行榜类型"""
    ranking_types = [
        "daily", "weekly", "monthly",
        "day_male", "day_female", "week_original", "week_rookie", "day_manga",
        "day_r18", "day_male_r18", "day_female_r18", "week_r18", "week_r18g"
    ]

    for ranking_type in ranking_types:
        # Mock token storage
        with (
            patch(
                "gallery_dl_auto.cli.download_cmd.get_default_token_storage"
            ) as mock_storage,
            patch("gallery_dl_auto.cli.download_cmd.PixivClient") as mock_client_class,
            patch("gallery_dl_auto.cli.download_cmd.RankingDownloader") as mock_downloader_class,
        ):
            # Setup mock token
            mock_storage_instance = MagicMock()
            mock_storage_instance.load_token.return_value = {"refresh_token": "test_token"}
            mock_storage.return_value = mock_storage_instance

            # Setup mock client
            mock_client = MagicMock()
            mock_client_class.return_value = mock_client

            # Setup mock downloader
            mock_downloader = MagicMock()
            mock_downloader.download_ranking.return_value = {
                "total": 0,
                "success": [],
                "failed": [],
            }
            mock_downloader_class.return_value = mock_downloader

            # Run command
            runner = CliRunner()
            result = runner.invoke(
                download,
                ["--type", ranking_type],
                obj=make_mock_config()
            )

            # Verify each type works
            assert result.exit_code == 0, f"Failed for type: {ranking_type}"


def test_incremental_download_with_tracker(tmp_path: Path) -> None:
    """测试增量下载:使用 SQLite tracker 跳过已下载作品"""
    from gallery_dl_auto.download.download_tracker import DownloadTracker
    from gallery_dl_auto.download.ranking_downloader import RankingDownloader
    from gallery_dl_auto.config.download_config import DownloadConfig

    # Mock token storage
    with (
        patch(
            "gallery_dl_auto.cli.download_cmd.get_default_token_storage"
        ) as mock_storage,
        patch("gallery_dl_auto.cli.download_cmd.PixivClient") as mock_client_class,
        patch("requests.get") as mock_get,
    ):
        # Setup mock token
        mock_storage_instance = MagicMock()
        mock_storage_instance.load_token.return_value = {"refresh_token": "test_token"}
        mock_storage.return_value = mock_storage_instance

        # Setup mock client with ranking data
        mock_client = MagicMock()
        mock_client.get_ranking_all.return_value = [
            {
                "id": 100,
                "title": "Artwork 100",
                "author": "Artist A",
                "image_url": "https://example.com/100.jpg",
            },
            {
                "id": 200,
                "title": "Artwork 200",
                "author": "Artist B",
                "image_url": "https://example.com/200.jpg",
            },
            {
                "id": 300,
                "title": "Artwork 300",
                "author": "Artist C",
                "image_url": "https://example.com/300.jpg",
            },
        ]

        # Mock metadata
        def get_metadata(illust_id):
            from gallery_dl_auto.models.artwork import ArtworkMetadata, ArtworkStatistics, ArtworkTag
            return ArtworkMetadata(
                illust_id=illust_id,
                title=f"Artwork {illust_id}",
                author=f"Artist {illust_id}",
                author_id=illust_id * 10,
                tags=[ArtworkTag(name="test", translated_name="测试")],
                statistics=ArtworkStatistics(
                    bookmark_count=10,
                    view_count=100,
                    comment_count=5
                )
            )

        mock_client.get_artwork_metadata.side_effect = get_metadata
        mock_client_class.return_value = mock_client

        # Mock requests.get for file download
        mock_response = MagicMock()
        mock_response.raise_for_status.return_value = None
        mock_response.iter_content.return_value = [b"fake_image_data"]
        mock_response.__enter__ = MagicMock(return_value=mock_response)
        mock_response.__exit__ = MagicMock(return_value=False)
        mock_get.return_value = mock_response

        # Create tracker with temp database
        db_path = tmp_path / "downloads.db"
        tracker = DownloadTracker(db_path)

        # First run: download all
        output_dir = tmp_path / "downloads"
        downloader = RankingDownloader(
            client=mock_client,
            output_dir=output_dir,
            config=DownloadConfig()
        )

        # First download
        results1 = downloader.download_ranking(
            mode="day",
            date="2026-02-25",
            tracker=tracker
        )

        # Verify: all 3 artworks downloaded
        assert results1["total"] == 3
        assert len(results1["success"]) == 3
        assert len(results1["failed"]) == 0

        # Verify: database has 3 records
        assert tracker.get_downloaded_count("day", "2026-02-25") == 3

        # Second download: should skip all artworks
        results2 = downloader.download_ranking(
            mode="day",
            date="2026-02-25",
            tracker=tracker
        )

        # Verify: all artworks skipped
        assert results2["total"] == 3
        assert len(results2["success"]) == 0
        assert len(results2["failed"]) == 0

        # Verify: requests.get was only called 3 times (first run only)
        assert mock_get.call_count == 3


def test_format_parameter_exists() -> None:
    """测试 --format 参数存在且接受正确的值"""
    runner = CliRunner()
    result = runner.invoke(download, ['--help'])
    assert result.exit_code == 0
    assert '--format' in result.output
    assert 'json' in result.output
    assert 'jsonl' in result.output


def test_jsonl_output_format(tmp_path: Path) -> None:
    """测试 JSONL 输出格式是单行且紧凑的"""
    with (
        patch(
            "gallery_dl_auto.cli.download_cmd.get_default_token_storage"
        ) as mock_storage,
        patch(
            "gallery_dl_auto.integration.gallery_dl_wrapper.GalleryDLWrapper"
        ) as mock_wrapper_class,
    ):
        # Setup mock token
        mock_storage_instance = MagicMock()
        mock_storage_instance.load_token.return_value = {"refresh_token": "test_token"}
        mock_storage.return_value = mock_storage_instance

        # Setup mock wrapper
        mock_wrapper = MagicMock()
        mock_result = BatchDownloadResult(
            success=True,
            total=2,
            downloaded=2,
            failed=0,
            skipped=0,
            output_dir=str(tmp_path),
            success_list=[12345, 67890],
            failed_errors=[],
        )
        mock_wrapper.download_ranking.return_value = mock_result
        mock_wrapper_class.return_value = mock_wrapper

        # Run with JSONL format
        runner = CliRunner()
        result = runner.invoke(
            download,
            [
                "--type",
                "daily",
                "--output",
                str(tmp_path),
                "--engine",
                "gallery-dl",
                "--format",
                "jsonl",
                "--dry-run",
            ],
            obj=make_mock_config(),
        )

        assert result.exit_code == 0

        # 验证输出是单行（JSONL 格式）
        output_lines = result.output.strip().split('\n')
        assert len(output_lines) == 1, f"JSONL 输出应该是单行，但有 {len(output_lines)} 行"

        # 验证输出可以被解析为 JSON
        output_json = json.loads(output_lines[0])
        assert output_json["success"] is True
        assert output_json["total"] == 2
        assert output_json["downloaded"] == 2

        # 验证输出没有多余的空格（紧凑格式）
        # JSONL 格式应该比美化的 JSON 更短
        json_output = json.dumps(output_json, ensure_ascii=False, indent=2)
        jsonl_output = output_lines[0]
        assert len(jsonl_output) < len(json_output), "JSONL 格式应该比美化的 JSON 更紧凑"


def test_json_output_format(tmp_path: Path) -> None:
    """测试 JSON 输出格式是美化且带缩进的"""
    with (
        patch(
            "gallery_dl_auto.cli.download_cmd.get_default_token_storage"
        ) as mock_storage,
        patch(
            "gallery_dl_auto.integration.gallery_dl_wrapper.GalleryDLWrapper"
        ) as mock_wrapper_class,
    ):
        # Setup mock token
        mock_storage_instance = MagicMock()
        mock_storage_instance.load_token.return_value = {"refresh_token": "test_token"}
        mock_storage.return_value = mock_storage_instance

        # Setup mock wrapper
        mock_wrapper = MagicMock()
        mock_result = BatchDownloadResult(
            success=True,
            total=2,
            downloaded=2,
            failed=0,
            skipped=0,
            output_dir=str(tmp_path),
            success_list=[12345, 67890],
            failed_errors=[],
        )
        mock_wrapper.download_ranking.return_value = mock_result
        mock_wrapper_class.return_value = mock_wrapper

        # Run with JSON format
        runner = CliRunner()
        result = runner.invoke(
            download,
            [
                "--type",
                "daily",
                "--output",
                str(tmp_path),
                "--engine",
                "gallery-dl",
                "--format",
                "json",
                "--dry-run",
            ],
            obj=make_mock_config(),
        )

        assert result.exit_code == 0

        # 验证输出是多行（JSON 格式）
        output_lines = result.output.strip().split('\n')
        assert len(output_lines) > 1, f"JSON 输出应该是多行，但只有 {len(output_lines)} 行"

        # 验证输出可以被解析为 JSON
        output_json = json.loads(result.output)
        assert output_json["success"] is True
        assert output_json["total"] == 2
        assert output_json["downloaded"] == 2


def test_jsonl_vs_json_size_comparison(tmp_path: Path) -> None:
    """测试 JSONL 格式比 JSON 格式更紧凑"""
    with (
        patch(
            "gallery_dl_auto.cli.download_cmd.get_default_token_storage"
        ) as mock_storage,
        patch(
            "gallery_dl_auto.integration.gallery_dl_wrapper.GalleryDLWrapper"
        ) as mock_wrapper_class,
    ):
        # Setup mock token
        mock_storage_instance = MagicMock()
        mock_storage_instance.load_token.return_value = {"refresh_token": "test_token"}
        mock_storage.return_value = mock_storage_instance

        # Setup mock wrapper with larger data
        mock_wrapper = MagicMock()
        mock_result = BatchDownloadResult(
            success=True,
            total=50,
            downloaded=50,
            failed=0,
            skipped=0,
            output_dir=str(tmp_path),
            success_list=list(range(1, 51)),  # 50 个作品
            failed_errors=[],
        )
        mock_wrapper.download_ranking.return_value = mock_result
        mock_wrapper_class.return_value = mock_wrapper

        # Run with JSON format
        runner = CliRunner()
        json_result = runner.invoke(
            download,
            [
                "--type",
                "daily",
                "--output",
                str(tmp_path),
                "--engine",
                "gallery-dl",
                "--format",
                "json",
                "--dry-run",
            ],
            obj=make_mock_config(),
        )

        # Run with JSONL format
        jsonl_result = runner.invoke(
            download,
            [
                "--type",
                "daily",
                "--output",
                str(tmp_path),
                "--engine",
                "gallery-dl",
                "--format",
                "jsonl",
                "--dry-run",
            ],
            obj=make_mock_config(),
        )

        assert json_result.exit_code == 0
        assert jsonl_result.exit_code == 0

        # 验证 JSONL 格式更紧凑
        json_size = len(json_result.output)
        jsonl_size = len(jsonl_result.output)
        compression_ratio = (json_size - jsonl_size) / json_size * 100

        # JSONL 应该比 JSON 小至少 10%（对于大数据集通常在 20-40%）
        assert (
            jsonl_size < json_size
        ), f"JSONL ({jsonl_size} bytes) 应该比 JSON ({json_size} bytes) 更小"

        # 打印压缩率（用于文档说明）
        print(f"JSONL 压缩率: {compression_ratio:.1f}%")


