"""ResumeManager 单元测试"""

import json
import pytest
from pathlib import Path
from gallery_dl_auto.download.resume_manager import ResumeManager, ResumeState


def test_resume_state_creation():
    """测试 ResumeState 创建"""
    state = ResumeState(mode="daily", date="2026-02-25")
    assert state.mode == "daily"
    assert state.date == "2026-02-25"
    assert state.current_index == 0
    assert state.total_count == 0
    assert state.downloaded_count == 0
    assert state.failed_count == 0
    assert state.last_illust_id is None


def test_resume_state_with_data():
    """测试 ResumeState 包含数据"""
    state = ResumeState(
        mode="weekly",
        date="2026-02-25",
        current_index=50,
        total_count=100,
        downloaded_count=45,
        failed_count=5,
        last_illust_id=12345678,
    )
    assert state.mode == "weekly"
    assert state.date == "2026-02-25"
    assert state.current_index == 50
    assert state.total_count == 100
    assert state.downloaded_count == 45
    assert state.failed_count == 5
    assert state.last_illust_id == 12345678


def test_resume_manager_init_new(tmp_path):
    """测试 ResumeManager 初始化(新状态)"""
    manager = ResumeManager(tmp_path, "daily", "2026-02-25")

    assert manager.state.mode == "daily"
    assert manager.state.date == "2026-02-25"
    assert manager.state.current_index == 0
    assert not manager.should_resume()


def test_resume_manager_save_and_load(tmp_path):
    """测试保存和加载状态"""
    # 创建管理器并保存状态
    manager1 = ResumeManager(tmp_path, "daily", "2026-02-25")
    manager1.update(index=50, downloaded=45, failed=5, last_illust_id=12345678)
    manager1.save()

    # 重新加载,验证状态恢复
    manager2 = ResumeManager(tmp_path, "daily", "2026-02-25")
    assert manager2.state.current_index == 50
    assert manager2.state.downloaded_count == 45
    assert manager2.state.failed_count == 5
    assert manager2.state.last_illust_id == 12345678
    assert manager2.should_resume()


def test_resume_manager_atomic_save(tmp_path):
    """测试原子保存操作"""
    manager = ResumeManager(tmp_path, "daily", "2026-02-25")
    manager.update(index=30, downloaded=28, failed=2)
    manager.save()

    # 验证文件存在
    state_file = tmp_path / "daily-2026-02-25" / ".resume.json"
    assert state_file.exists()

    # 验证临时文件不存在
    temp_file = state_file.with_suffix(".tmp")
    assert not temp_file.exists()


def test_resume_manager_clear(tmp_path):
    """测试清除状态文件"""
    manager = ResumeManager(tmp_path, "daily", "2026-02-25")
    manager.update(index=50, downloaded=45, failed=5)
    manager.save()

    # 验证文件存在
    state_file = tmp_path / "daily-2026-02-25" / ".resume.json"
    assert state_file.exists()

    # 清除状态文件
    manager.clear()
    assert not state_file.exists()


def test_resume_manager_corrupted_file(tmp_path):
    """测试状态文件损坏时重新开始"""
    # 创建损坏的状态文件
    state_file = tmp_path / "daily-2026-02-25" / ".resume.json"
    state_file.parent.mkdir(parents=True, exist_ok=True)
    state_file.write_text("invalid json content", encoding="utf-8")

    # 加载时应该重新开始
    manager = ResumeManager(tmp_path, "daily", "2026-02-25")
    assert manager.state.current_index == 0
    assert not manager.should_resume()


def test_resume_manager_get_resume_index(tmp_path):
    """测试获取恢复起始索引"""
    manager = ResumeManager(tmp_path, "daily", "2026-02-25")
    manager.update(index=75, downloaded=70, failed=5)

    assert manager.get_resume_index() == 75


def test_resume_manager_update_multiple_times(tmp_path):
    """测试多次更新状态"""
    manager = ResumeManager(tmp_path, "daily", "2026-02-25")

    # 第一次更新
    manager.update(index=10, downloaded=9, failed=1)
    manager.save()
    assert manager.state.current_index == 10

    # 第二次更新
    manager.update(index=20, downloaded=18, failed=2)
    manager.save()
    assert manager.state.current_index == 20

    # 第三次更新
    manager.update(index=30, downloaded=27, failed=3)
    manager.save()
    assert manager.state.current_index == 30

    # 重新加载验证
    manager2 = ResumeManager(tmp_path, "daily", "2026-02-25")
    assert manager2.state.current_index == 30
    assert manager2.state.downloaded_count == 27
    assert manager2.state.failed_count == 3
