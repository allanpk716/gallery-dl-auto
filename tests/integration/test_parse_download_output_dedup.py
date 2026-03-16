"""测试 _parse_download_output 去重逻辑

测试多页作品的重复 ID 去重问题（Issue #3）
"""

from pathlib import Path

from gallery_dl_auto.config.download_config import DownloadConfig
from gallery_dl_auto.integration.gallery_dl_wrapper import GalleryDLWrapper


def test_parse_download_output_dedup_multi_page_artwork(tmp_path):
    """测试多页作品的 ID 去重

    场景：
    - 作品 12345 有 3 页（p0, p1, p2）
    - 作品 67890 有 2 页（p0, p1）
    - success_list 应该只包含每个作品 ID 一次
    """
    # 准备
    config = DownloadConfig()
    wrapper = GalleryDLWrapper(config)

    # 模拟 gallery-dl 输出（多行文件路径）
    stdout = """pixiv\\rankings\\day\\2026-03-15\\12345_p0.jpg
pixiv\\rankings\\day\\2026-03-15\\12345_p1.jpg
pixiv\\rankings\\day\\2026-03-15\\12345_p2.jpg
pixiv\\rankings\\day\\2026-03-15\\67890_p0.jpg
pixiv\\rankings\\day\\2026-03-15\\67890_p1.jpg"""

    # 执行
    result = wrapper._parse_download_output(
        stdout=stdout,
        output_dir=tmp_path,
        actual_download_path=tmp_path / "pixiv" / "rankings" / "day" / "2026-03-15"
    )

    # 验证
    assert result.success is True
    assert result.downloaded == 2, f"Expected 2 unique artworks, got {result.downloaded}"
    assert result.total == 2
    assert len(result.success_list) == 2
    assert set(result.success_list) == {12345, 67890}, f"Expected {{12345, 67890}}, got {set(result.success_list)}"


def test_parse_download_output_single_page_artwork(tmp_path):
    """测试单页作品的正常解析

    场景：
    - 每个作品只有 1 页
    - success_list 应该包含所有作品 ID
    """
    # 准备
    config = DownloadConfig()
    wrapper = GalleryDLWrapper(config)

    # 模拟 gallery-dl 输出
    stdout = """pixiv\\rankings\\day\\2026-03-15\\11111_p0.jpg
pixiv\\rankings\\day\\2026-03-15\\22222_p0.jpg
pixiv\\rankings\\day\\2026-03-15\\33333_p0.jpg"""

    # 执行
    result = wrapper._parse_download_output(
        stdout=stdout,
        output_dir=tmp_path,
        actual_download_path=tmp_path / "pixiv" / "rankings" / "day" / "2026-03-15"
    )

    # 验证
    assert result.success is True
    assert result.downloaded == 3
    assert result.total == 3
    assert len(result.success_list) == 3
    assert set(result.success_list) == {11111, 22222, 33333}


def test_parse_download_output_empty_output(tmp_path):
    """测试空输出的情况"""
    # 准备
    config = DownloadConfig()
    wrapper = GalleryDLWrapper(config)

    # 执行
    result = wrapper._parse_download_output(
        stdout="",
        output_dir=tmp_path,
        actual_download_path=tmp_path
    )

    # 验证
    assert result.success is True
    assert result.downloaded == 0
    assert result.total == 0
    assert len(result.success_list) == 0


def test_parse_download_output_mixed_page_counts(tmp_path):
    """测试混合页数的情况

    场景：
    - 作品 A 有 5 页
    - 作品 B 有 1 页
    - 作品 C 有 3 页
    - success_list 应该只包含 3 个唯一的 ID
    """
    # 准备
    config = DownloadConfig()
    wrapper = GalleryDLWrapper(config)

    # 模拟 gallery-dl 输出
    stdout = """pixiv\\rankings\\day\\2026-03-15\\11111_p0.jpg
pixiv\\rankings\\day\\2026-03-15\\11111_p1.jpg
pixiv\\rankings\\day\\2026-03-15\\11111_p2.jpg
pixiv\\rankings\\day\\2026-03-15\\11111_p3.jpg
pixiv\\rankings\\day\\2026-03-15\\11111_p4.jpg
pixiv\\rankings\\day\\2026-03-15\\22222_p0.jpg
pixiv\\rankings\\day\\2026-03-15\\33333_p0.jpg
pixiv\\rankings\\day\\2026-03-15\\33333_p1.jpg
pixiv\\rankings\\day\\2026-03-15\\33333_p2.jpg"""

    # 执行
    result = wrapper._parse_download_output(
        stdout=stdout,
        output_dir=tmp_path,
        actual_download_path=tmp_path / "pixiv" / "rankings" / "day" / "2026-03-15"
    )

    # 验证
    assert result.success is True
    assert result.downloaded == 3, f"Expected 3 unique artworks, got {result.downloaded}"
    assert result.total == 3
    assert len(result.success_list) == 3
    assert set(result.success_list) == {11111, 22222, 33333}
