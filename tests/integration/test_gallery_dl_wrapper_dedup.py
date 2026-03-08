"""Gallery-dl wrapper 去重功能单元测试"""

from pathlib import Path

import pytest

from gallery_dl_auto.config.download_config import DownloadConfig
from gallery_dl_auto.integration.gallery_dl_wrapper import GalleryDLWrapper
from gallery_dl_auto.download.download_tracker import DownloadTracker
from gallery_dl_auto.models.error_response import BatchDownloadResult


def test_check_existing_downloads_no_skip(tmp_path):
    """测试首次下载（没有已下载作品）"""
    # 准备
    config = DownloadConfig()
    wrapper = GalleryDLWrapper(config)

    db_path = tmp_path / "test.db"
    tracker = DownloadTracker(db_path)

    # 模拟 dry-run 结果（3 个作品）
    dry_run_result = BatchDownloadResult(
        success=True,
        total=3,
        downloaded=3,
        failed=0,
        skipped=0,
        output_dir=str(tmp_path),
        actual_download_dir=None,
        success_list=[11111, 22222, 33333],
        failed_errors=[],
    )

    # 执行
    pending_ids, skipped_ids = wrapper._check_existing_downloads(
        dry_run_result, tracker
    )

    # 验证
    assert len(pending_ids) == 3
    assert len(skipped_ids) == 0
    assert set(pending_ids) == {11111, 22222, 33333}


def test_check_existing_downloads_partial_skip(tmp_path):
    """测试部分作品已下载"""
    # 准备
    config = DownloadConfig()
    wrapper = GalleryDLWrapper(config)

    db_path = tmp_path / "test.db"
    tracker = DownloadTracker(db_path)

    # 预先记录一些下载
    tracker.record_download(
        illust_id=11111,
        file_path=tmp_path / "11111_p0.jpg",
        mode="day",
        date="2026-03-07"
    )
    tracker.record_download(
        illust_id=22222,
        file_path=tmp_path / "22222_p0.jpg",
        mode="day",
        date="2026-03-07"
    )

    # 模拟 dry-run 结果（5 个作品，其中 2 个已下载）
    dry_run_result = BatchDownloadResult(
        success=True,
        total=5,
        downloaded=5,
        failed=0,
        skipped=0,
        output_dir=str(tmp_path),
        actual_download_dir=None,
        success_list=[11111, 22222, 33333, 44444, 55555],
        failed_errors=[],
    )

    # 执行
    pending_ids, skipped_ids = wrapper._check_existing_downloads(
        dry_run_result, tracker
    )

    # 验证
    assert len(pending_ids) == 3
    assert len(skipped_ids) == 2
    assert set(skipped_ids) == {11111, 22222}
    assert set(pending_ids) == {33333, 44444, 55555}


def test_check_existing_downloads_all_skipped(tmp_path):
    """测试所有作品都已下载"""
    # 准备
    config = DownloadConfig()
    wrapper = GalleryDLWrapper(config)

    db_path = tmp_path / "test.db"
    tracker = DownloadTracker(db_path)

    # 预先记录所有下载
    for illust_id in [11111, 22222, 33333]:
        tracker.record_download(
            illust_id=illust_id,
            file_path=tmp_path / f"{illust_id}_p0.jpg",
            mode="day",
            date="2026-03-07"
        )

    # 模拟 dry-run 结果（3 个作品，全部已下载）
    dry_run_result = BatchDownloadResult(
        success=True,
        total=3,
        downloaded=3,
        failed=0,
        skipped=0,
        output_dir=str(tmp_path),
        actual_download_dir=None,
        success_list=[11111, 22222, 33333],
        failed_errors=[],
    )

    # 执行
    pending_ids, skipped_ids = wrapper._check_existing_downloads(
        dry_run_result, tracker
    )

    # 验证
    assert len(pending_ids) == 0
    assert len(skipped_ids) == 3
    assert set(skipped_ids) == {11111, 22222, 33333}


def test_generate_archive_file(tmp_path):
    """测试 archive 文件生成"""
    # 准备
    config = DownloadConfig()
    wrapper = GalleryDLWrapper(config)

    db_path = tmp_path / "test.db"
    tracker = DownloadTracker(db_path)

    # 记录一些下载
    for illust_id in [11111, 22222, 33333]:
        tracker.record_download(
            illust_id=illust_id,
            file_path=tmp_path / f"{illust_id}_p0.jpg",
            mode="day",
            date="2026-03-07"
        )

    temp_dir = tmp_path / "temp"

    # 执行
    archive_file = wrapper._generate_archive_file(tracker, temp_dir)

    # 验证
    assert archive_file is not None
    assert archive_file.exists()

    # 读取并验证内容
    with open(archive_file, 'r', encoding='utf-8') as f:
        lines = [line.strip() for line in f.readlines()]

    assert len(lines) == 3
    assert '11111' in lines
    assert '22222' in lines
    assert '33333' in lines


def test_generate_archive_file_empty_tracker(tmp_path):
    """测试 tracker 为空时的 archive 生成"""
    # 准备
    config = DownloadConfig()
    wrapper = GalleryDLWrapper(config)

    db_path = tmp_path / "test.db"
    tracker = DownloadTracker(db_path)
    temp_dir = tmp_path / "temp"

    # 执行
    archive_file = wrapper._generate_archive_file(tracker, temp_dir)

    # 验证：空 tracker 应该返回 None
    assert archive_file is None


def test_record_downloads(tmp_path):
    """测试记录下载到 tracker"""
    # 准备
    config = DownloadConfig()
    wrapper = GalleryDLWrapper(config)

    db_path = tmp_path / "test.db"
    tracker = DownloadTracker(db_path)

    # 创建模拟的下载结果
    download_dir = tmp_path / "downloads"
    download_dir.mkdir()

    # 创建模拟的下载文件
    for illust_id in [11111, 22222]:
        file_path = download_dir / f"{illust_id}_p0.jpg"
        file_path.write_text("fake image data")

    result = BatchDownloadResult(
        success=True,
        total=2,
        downloaded=2,
        failed=0,
        skipped=0,
        output_dir=str(tmp_path),
        actual_download_dir=str(download_dir),
        success_list=[11111, 22222],
        failed_errors=[],
    )

    # 执行
    wrapper._record_downloads(result, tracker, "day", "2026-03-08")

    # 验证：tracker 中应该有记录
    assert tracker.is_downloaded(11111)
    assert tracker.is_downloaded(22222)


def test_record_downloads_with_missing_files(tmp_path):
    """测试记录下载时文件不存在的情况"""
    # 准备
    config = DownloadConfig()
    wrapper = GalleryDLWrapper(config)

    db_path = tmp_path / "test.db"
    tracker = DownloadTracker(db_path)

    download_dir = tmp_path / "downloads"
    download_dir.mkdir()

    result = BatchDownloadResult(
        success=True,
        total=2,
        downloaded=2,
        failed=0,
        skipped=0,
        output_dir=str(tmp_path),
        actual_download_dir=str(download_dir),
        success_list=[11111, 22222],
        failed_errors=[],
    )

    # 执行（文件不存在，但不应失败）
    wrapper._record_downloads(result, tracker, "day", "2026-03-08")

    # 验证：仍然应该记录到 tracker（即使文件不存在）
    assert tracker.is_downloaded(11111)
    assert tracker.is_downloaded(22222)
