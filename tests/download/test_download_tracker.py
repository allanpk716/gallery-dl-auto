"""DownloadTracker 单元测试

测试 SQLite 数据库的下载历史追踪功能。
"""

import sqlite3
import threading
from pathlib import Path

import pytest

from gallery_dl_auto.download.download_tracker import DownloadTracker


@pytest.fixture
def tracker(tmp_path: Path) -> DownloadTracker:
    """创建临时数据库的 DownloadTracker 实例"""
    db_path = tmp_path / "test_downloads.db"
    return DownloadTracker(db_path)


def test_init_database(tracker: DownloadTracker) -> None:
    """测试数据库初始化"""
    # 验证数据库文件已创建
    assert tracker.db_path.exists()

    # 验证表和索引创建
    with sqlite3.connect(tracker.db_path) as conn:
        cursor = conn.cursor()

        # 检查 downloads 表
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='table' AND name='downloads'"
        )
        assert cursor.fetchone() is not None

        # 检查索引
        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='index' AND name='idx_mode_date'"
        )
        assert cursor.fetchone() is not None

        cursor.execute(
            "SELECT name FROM sqlite_master WHERE type='index' AND name='idx_file_path'"
        )
        assert cursor.fetchone() is not None


def test_record_and_query(tracker: DownloadTracker) -> None:
    """测试记录下载和查询"""
    illust_id = 12345678
    file_path = Path("./pixiv-downloads/daily-2026-02-25/12345678_artwork.jpg")

    # 记录下载
    tracker.record_download(
        illust_id=illust_id,
        file_path=file_path,
        mode="day",
        date="2026-02-25",
        file_size=1024000,
        checksum="abc123"
    )

    # 验证记录已保存
    with sqlite3.connect(tracker.db_path) as conn:
        cursor = conn.cursor()
        cursor.execute(
            "SELECT file_path, mode, date, file_size, checksum FROM downloads WHERE illust_id = ?",
            (illust_id,)
        )
        result = cursor.fetchone()

        assert result is not None
        assert result[0] == str(file_path)
        assert result[1] == "day"
        assert result[2] == "2026-02-25"
        assert result[3] == 1024000
        assert result[4] == "abc123"


def test_is_downloaded(tracker: DownloadTracker) -> None:
    """测试检查作品是否已下载"""
    illust_id = 11111111

    # 初始状态: 未下载
    assert not tracker.is_downloaded(illust_id)

    # 记录下载
    tracker.record_download(
        illust_id=illust_id,
        file_path=Path("./test.jpg"),
        mode="day",
        date="2026-02-25"
    )

    # 验证已下载
    assert tracker.is_downloaded(illust_id)

    # 其他 ID 仍然是未下载
    assert not tracker.is_downloaded(99999999)


def test_get_pending_illusts(tracker: DownloadTracker) -> None:
    """测试获取待下载作品列表"""
    # 记录部分下载
    downloaded_ids = [1, 2, 3]
    for illust_id in downloaded_ids:
        tracker.record_download(
            illust_id=illust_id,
            file_path=Path(f"./{illust_id}.jpg"),
            mode="day",
            date="2026-02-25"
        )

    # 所有作品 ID
    all_illusts = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]

    # 获取待下载列表
    pending = tracker.get_pending_illusts("day", "2026-02-25", all_illusts)

    # 验证: 已下载的 1, 2, 3 被排除
    assert set(pending) == {4, 5, 6, 7, 8, 9, 10}
    assert len(pending) == 7

    # 测试空列表
    assert tracker.get_pending_illusts("day", "2026-02-25", []) == []


def test_get_downloaded_count(tracker: DownloadTracker) -> None:
    """测试统计已下载数量"""
    # 记录不同排行榜的下载
    tracker.record_download(1, Path("./1.jpg"), "day", "2026-02-25")
    tracker.record_download(2, Path("./2.jpg"), "day", "2026-02-25")
    tracker.record_download(3, Path("./3.jpg"), "day", "2026-02-25")
    tracker.record_download(4, Path("./4.jpg"), "week", "2026-02-25")

    # 验证计数
    assert tracker.get_downloaded_count("day", "2026-02-25") == 3
    assert tracker.get_downloaded_count("week", "2026-02-25") == 1
    assert tracker.get_downloaded_count("month", "2026-02-25") == 0


def test_get_downloaded_illusts(tracker: DownloadTracker) -> None:
    """测试获取已下载作品列表"""
    # 记录下载
    expected_ids = [10, 20, 30]
    for illust_id in expected_ids:
        tracker.record_download(
            illust_id=illust_id,
            file_path=Path(f"./{illust_id}.jpg"),
            mode="day",
            date="2026-02-25"
        )

    # 获取已下载列表
    downloaded = tracker.get_downloaded_illusts("day", "2026-02-25")

    # 验证
    assert set(downloaded) == set(expected_ids)


def test_concurrent_access(tracker: DownloadTracker) -> None:
    """测试多线程并发访问"""
    num_threads = 5
    downloads_per_thread = 20
    threads = []

    def download_worker(thread_id: int) -> None:
        """每个线程下载一批作品"""
        for i in range(downloads_per_thread):
            illust_id = thread_id * 1000 + i
            tracker.record_download(
                illust_id=illust_id,
                file_path=Path(f"./thread_{thread_id}/{illust_id}.jpg"),
                mode="day",
                date="2026-02-25"
            )

    # 创建并启动线程
    for thread_id in range(num_threads):
        thread = threading.Thread(target=download_worker, args=(thread_id,))
        threads.append(thread)
        thread.start()

    # 等待所有线程完成
    for thread in threads:
        thread.join()

    # 验证所有下载都被记录
    total_expected = num_threads * downloads_per_thread
    assert tracker.get_downloaded_count("day", "2026-02-25") == total_expected


def test_wal_mode(tracker: DownloadTracker) -> None:
    """测试 WAL 模式已启用"""
    with sqlite3.connect(tracker.db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("PRAGMA journal_mode")
        result = cursor.fetchone()
        assert result[0].lower() == "wal"


def test_import_from_json_progress(tracker: DownloadTracker, tmp_path: Path) -> None:
    """测试从 JSON 进度文件导入"""
    import json

    # 创建模拟的 JSON 进度文件
    progress_file = tmp_path / ".progress.json"
    progress_data = {
        "mode": "day",
        "date": "2026-02-25",
        "downloaded_ids": [100, 200, 300]
    }
    with open(progress_file, "w", encoding="utf-8") as f:
        json.dump(progress_data, f)

    # 导入数据
    imported_count = tracker.import_from_json_progress(
        progress_file=progress_file,
        mode="day",
        date="2026-02-25",
        default_file_path=Path("./imported/artwork.jpg")
    )

    # 验证导入
    assert imported_count == 3
    assert tracker.is_downloaded(100)
    assert tracker.is_downloaded(200)
    assert tracker.is_downloaded(300)


def test_import_from_json_progress_skip_existing(tracker: DownloadTracker, tmp_path: Path) -> None:
    """测试导入时跳过已存在的记录"""
    import json

    # 预先记录部分下载
    tracker.record_download(100, Path("./100.jpg"), "day", "2026-02-25")

    # 创建 JSON 进度文件(包含已存在的 ID)
    progress_file = tmp_path / ".progress.json"
    progress_data = {
        "mode": "day",
        "date": "2026-02-25",
        "downloaded_ids": [100, 200, 300]
    }
    with open(progress_file, "w", encoding="utf-8") as f:
        json.dump(progress_data, f)

    # 导入数据
    imported_count = tracker.import_from_json_progress(
        progress_file=progress_file,
        mode="day",
        date="2026-02-25"
    )

    # 验证: 只导入了 200 和 300(ID 100 已存在)
    assert imported_count == 2
    assert tracker.get_downloaded_count("day", "2026-02-25") == 3
