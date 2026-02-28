"""进度管理器

管理下载进度,支持断点续传。
"""

import json
import logging
from pathlib import Path

from pydantic import BaseModel, ConfigDict

logger = logging.getLogger("gallery_dl_auto")


class DownloadProgress(BaseModel):
    """下载进度模型"""

    model_config = ConfigDict(json_encoders={set: list})  # 序列化时转换为列表

    mode: str
    date: str
    downloaded_ids: set[int] = set()
    failed_ids: set[int] = set()

    def save(self, progress_file: Path) -> None:
        """保存进度到文件

        Args:
            progress_file: 进度文件路径
        """
        # 确保父目录存在
        progress_file.parent.mkdir(parents=True, exist_ok=True)

        # 序列化: set → list
        data = {
            "mode": self.mode,
            "date": self.date,
            "downloaded_ids": sorted(list(self.downloaded_ids)),
            "failed_ids": sorted(list(self.failed_ids)),
        }

        # 原子写入: 先写临时文件,再重命名
        temp_file = progress_file.with_suffix(".tmp")
        with open(temp_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

        # Windows: rename() 不能覆盖已存在的文件,先删除
        if progress_file.exists():
            progress_file.unlink()

        # 重命名临时文件
        temp_file.rename(progress_file)
        logger.debug(
            f"Progress saved: {len(self.downloaded_ids)} downloaded, {len(self.failed_ids)} failed"
        )

    @classmethod
    def load(cls, progress_file: Path) -> "DownloadProgress | None":
        """从文件加载进度

        Args:
            progress_file: 进度文件路径

        Returns:
            DownloadProgress 对象,或 None (文件不存在)
        """
        if not progress_file.exists():
            return None

        try:
            with open(progress_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            # 反序列化: list → set
            data["downloaded_ids"] = set(data.get("downloaded_ids", []))
            data["failed_ids"] = set(data.get("failed_ids", []))

            progress = cls(**data)
            logger.info(
                f"Progress loaded: {len(progress.downloaded_ids)} already downloaded, "
                f"{len(progress.failed_ids)} previously failed"
            )
            return progress

        except (json.JSONDecodeError, KeyError) as e:
            logger.warning(f"Failed to load progress file: {e}, starting fresh")
            return None

    def mark_downloaded(self, illust_id: int) -> None:
        """标记作品为已下载"""
        self.downloaded_ids.add(illust_id)
        # 如果之前失败过,从失败列表移除
        self.failed_ids.discard(illust_id)

    def mark_failed(self, illust_id: int) -> None:
        """标记作品为失败"""
        self.failed_ids.add(illust_id)

    def is_downloaded(self, illust_id: int) -> bool:
        """检查作品是否已下载"""
        return illust_id in self.downloaded_ids

    def get_progress_file_path(
        self, output_dir: Path, mode: str, date: str
    ) -> Path:
        """获取进度文件路径

        Args:
            output_dir: 输出目录
            mode: 排行榜模式
            date: 日期字符串

        Returns:
            进度文件路径
        """
        # 用户决策: 进度文件在下载目录内
        # 示例: ./pixiv-downloads/weekly-2026-02-18/.progress.json
        return output_dir / f"{mode}-{date}" / ".progress.json"
