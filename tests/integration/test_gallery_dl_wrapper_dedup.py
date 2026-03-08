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
