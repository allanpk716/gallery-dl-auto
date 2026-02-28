"""断点续传管理器"""

import json
import logging
from pathlib import Path
from typing import Optional

from pydantic import BaseModel

logger = logging.getLogger(__name__)


class ResumeState(BaseModel):
    """断点续传状态"""

    mode: str
    date: str
    current_index: int = 0
    total_count: int = 0
    downloaded_count: int = 0
    failed_count: int = 0
    last_illust_id: Optional[int] = None


class ResumeManager:
    """断点续传管理器,支持程序中断后从断点继续下载"""

    def __init__(self, output_dir: Path, mode: str, date: str):
        """
        初始化断点续传管理器

        Args:
            output_dir: 输出目录
            mode: 排行榜模式
            date: 排行榜日期
        """
        self.state_file = output_dir / f"{mode}-{date}" / ".resume.json"
        self.state = self._load_or_create(mode, date)

    def _load_or_create(self, mode: str, date: str) -> ResumeState:
        """
        加载现有状态或创建新状态

        Args:
            mode: 排行榜模式
            date: 排行榜日期

        Returns:
            ResumeState: 断点续传状态
        """
        if self.state_file.exists():
            try:
                with open(self.state_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                logger.info(f"加载断点状态: {self.state_file}")
                return ResumeState(**data)
            except (json.JSONDecodeError, KeyError) as e:
                # 状态文件损坏,重新开始
                logger.warning(f"断点状态文件损坏,重新开始: {e}")

        return ResumeState(mode=mode, date=date)

    def update(
        self,
        index: int,
        downloaded: int,
        failed: int,
        last_illust_id: Optional[int] = None,
    ):
        """
        更新状态

        Args:
            index: 当前索引
            downloaded: 已下载数量
            failed: 失败数量
            last_illust_id: 最后一个作品ID
        """
        self.state.current_index = index
        self.state.downloaded_count = downloaded
        self.state.failed_count = failed
        self.state.last_illust_id = last_illust_id

    def save(self):
        """
        保存状态到文件(原子操作)

        使用临时文件+重命名的方式确保原子性,避免程序崩溃导致状态文件损坏
        """
        # 确保父目录存在
        self.state_file.parent.mkdir(parents=True, exist_ok=True)

        # 临时文件+重命名
        temp_file = self.state_file.with_suffix(".tmp")
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(self.state.model_dump(), f, ensure_ascii=False, indent=2)

        # Windows 兼容:先删除再重命名
        if self.state_file.exists():
            self.state_file.unlink()
        temp_file.rename(self.state_file)

        logger.debug(f"保存断点状态: 索引={self.state.current_index}")

    def should_resume(self) -> bool:
        """
        判断是否需要恢复

        Returns:
            bool: 如果需要恢复返回True,否则返回False
        """
        return self.state.current_index > 0

    def get_resume_index(self) -> int:
        """
        获取恢复起始索引

        Returns:
            int: 恢复起始索引
        """
        return self.state.current_index

    def clear(self):
        """清除状态文件(下载完成)"""
        if self.state_file.exists():
            self.state_file.unlink()
            logger.info(f"清除断点状态文件: {self.state_file}")
