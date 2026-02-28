"""进度管理器单元测试"""

from pathlib import Path

from gallery_dl_auto.download.progress_manager import DownloadProgress


def test_progress_save_and_load(tmp_path):
    """测试进度保存和加载"""
    progress_file = tmp_path / ".progress.json"

    # 创建进度
    progress = DownloadProgress(
        mode="week", date="2026-02-18", downloaded_ids={1, 2, 3}, failed_ids={4}
    )

    # 保存
    progress.save(progress_file)
    assert progress_file.exists()

    # 加载
    loaded = DownloadProgress.load(progress_file)
    assert loaded is not None
    assert loaded.mode == "week"
    assert loaded.date == "2026-02-18"
    assert loaded.downloaded_ids == {1, 2, 3}
    assert loaded.failed_ids == {4}


def test_progress_load_nonexistent(tmp_path):
    """测试加载不存在的进度文件"""
    progress_file = tmp_path / "nonexistent.json"
    loaded = DownloadProgress.load(progress_file)
    assert loaded is None


def test_progress_load_corrupted(tmp_path):
    """测试加载损坏的进度文件"""
    progress_file = tmp_path / "corrupted.json"
    progress_file.write_text("invalid json {")

    loaded = DownloadProgress.load(progress_file)
    assert loaded is None  # 优雅降级


def test_mark_operations():
    """测试标记操作"""
    progress = DownloadProgress(mode="day", date="2026-02-25")

    # 标记已下载
    progress.mark_downloaded(1)
    assert progress.is_downloaded(1)
    assert 1 in progress.downloaded_ids

    # 标记失败
    progress.mark_failed(2)
    assert 2 in progress.failed_ids

    # 重新下载成功的作品,从失败列表移除
    progress.mark_failed(3)
    progress.mark_downloaded(3)
    assert 3 not in progress.failed_ids
    assert 3 in progress.downloaded_ids


def test_progress_file_path():
    """测试进度文件路径生成"""
    output_dir = Path("./pixiv-downloads")
    path = DownloadProgress(mode="week", date="2026-02-18").get_progress_file_path(
        output_dir, "week", "2026-02-18"
    )

    expected = Path("./pixiv-downloads/week-2026-02-18/.progress.json")
    assert path == expected
