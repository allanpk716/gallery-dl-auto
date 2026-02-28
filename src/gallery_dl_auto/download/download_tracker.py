"""下载历史追踪器

使用 SQLite 数据库记录下载历史,支持高效查询和断点续传。
"""

import logging
import sqlite3
from datetime import datetime
from pathlib import Path

logger = logging.getLogger("gallery_dl_auto")


class DownloadTracker:
    """下载历史追踪器

    使用 SQLite 数据库记录每个作品的下载状态。
    支持高效查询已下载内容、按排行榜过滤、断点续传检测。

    数据库文件: ~/.gallery-dl-auto/downloads.db
    """

    def __init__(self, db_path: Path) -> None:
        """初始化下载追踪器

        Args:
            db_path: 数据库文件路径
        """
        self.db_path = db_path
        self._init_database()

    def _init_database(self) -> None:
        """初始化数据库表和索引

        创建 downloads 表和索引,启用 WAL 模式。
        """
        # 确保数据库目录存在
        self.db_path.parent.mkdir(parents=True, exist_ok=True)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()

            # 启用 WAL 模式
            cursor.execute("PRAGMA journal_mode=WAL")
            result = cursor.fetchone()
            logger.debug(f"SQLite journal mode: {result[0]}")

            # 创建 downloads 表
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS downloads (
                    illust_id INTEGER PRIMARY KEY,
                    file_path TEXT NOT NULL,
                    mode TEXT NOT NULL,
                    date TEXT NOT NULL,
                    downloaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    file_size INTEGER,
                    checksum TEXT
                )
            """)

            # 创建索引: 加速按排行榜查询
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_mode_date
                ON downloads(mode, date)
            """)

            # 创建索引: 检测重复文件
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_file_path
                ON downloads(file_path)
            """)

            conn.commit()
            logger.info(f"Database initialized: {self.db_path}")

    def is_downloaded(self, illust_id: int) -> bool:
        """查询作品是否已下载

        Args:
            illust_id: 作品 ID

        Returns:
            bool: True 如果已下载, False 如果未下载
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT 1 FROM downloads WHERE illust_id = ?",
                (illust_id,)
            )
            result = cursor.fetchone()
            return result is not None

    def record_download(
        self,
        illust_id: int,
        file_path: Path,
        mode: str,
        date: str,
        file_size: int | None = None,
        checksum: str | None = None
    ) -> None:
        """记录下载完成

        Args:
            illust_id: 作品 ID
            file_path: 文件保存路径
            mode: 排行榜模式 (day, week, month 等)
            date: 日期字符串 (YYYY-MM-DD)
            file_size: 文件大小(字节,可选)
            checksum: 文件校验和(可选)
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                INSERT OR REPLACE INTO downloads
                (illust_id, file_path, mode, date, file_size, checksum)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (illust_id, str(file_path), mode, date, file_size, checksum)
            )
            conn.commit()
            logger.debug(f"Recorded download: illust_id={illust_id}, file={file_path}")

    def get_pending_illusts(
        self,
        mode: str,
        date: str,
        all_illusts: list[int]
    ) -> list[int]:
        """获取待下载作品 ID(排除已下载)

        Args:
            mode: 排行榜模式
            date: 日期字符串
            all_illusts: 所有作品 ID 列表

        Returns:
            list[int]: 待下载的作品 ID 列表
        """
        if not all_illusts:
            return []

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            # 使用 IN 查询批量检查
            placeholders = ",".join("?" * len(all_illusts))
            cursor.execute(
                f"""
                SELECT illust_id FROM downloads
                WHERE illust_id IN ({placeholders})
                """,
                all_illusts
            )
            downloaded_ids = {row[0] for row in cursor.fetchall()}

        # 返回未下载的作品 ID
        pending = [illust_id for illust_id in all_illusts if illust_id not in downloaded_ids]
        logger.debug(
            f"Pending illusts: {len(pending)}/{len(all_illusts)} "
            f"(skipping {len(downloaded_ids)} already downloaded)"
        )
        return pending

    def get_downloaded_count(self, mode: str, date: str) -> int:
        """统计某排行榜已下载数量

        Args:
            mode: 排行榜模式
            date: 日期字符串

        Returns:
            int: 已下载作品数量
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT COUNT(*) FROM downloads
                WHERE mode = ? AND date = ?
                """,
                (mode, date)
            )
            result = cursor.fetchone()
            return result[0] if result else 0

    def get_downloaded_illusts(self, mode: str, date: str) -> list[int]:
        """获取某排行榜已下载的所有作品 ID

        Args:
            mode: 排行榜模式
            date: 日期字符串

        Returns:
            list[int]: 已下载作品 ID 列表
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT illust_id FROM downloads
                WHERE mode = ? AND date = ?
                """,
                (mode, date)
            )
            return [row[0] for row in cursor.fetchall()]

    def cleanup_failed_downloads(self, days: int = 7) -> int:
        """清理失败记录(可选,为未来准备)

        删除指定天数前的记录,用于清理可能失败的下载。

        Args:
            days: 保留天数(默认 7 天)

        Returns:
            int: 删除的记录数
        """
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(
                """
                DELETE FROM downloads
                WHERE datetime(downloaded_at) < datetime('now', ?)
                """,
                (f"-{days} days",)
            )
            deleted_count = cursor.rowcount
            conn.commit()

            if deleted_count > 0:
                logger.info(f"Cleaned up {deleted_count} old download records")

            return deleted_count

    def import_from_json_progress(
        self,
        progress_file: Path,
        mode: str,
        date: str,
        default_file_path: Path | None = None
    ) -> int:
        """从旧的 JSON 进度文件导入数据

        Args:
            progress_file: JSON 进度文件路径
            mode: 排行榜模式
            date: 日期字符串
            default_file_path: 默认文件路径(用于导入时填充)

        Returns:
            int: 导入的记录数
        """
        if not progress_file.exists():
            logger.debug(f"Progress file not found: {progress_file}")
            return 0

        try:
            import json
            with open(progress_file, "r", encoding="utf-8") as f:
                data = json.load(f)

            downloaded_ids = data.get("downloaded_ids", [])
            if not downloaded_ids:
                logger.debug("No downloaded IDs in progress file")
                return 0

            # 批量导入
            imported_count = 0
            for illust_id in downloaded_ids:
                # 检查是否已存在
                if not self.is_downloaded(illust_id):
                    # 使用占位符路径(实际文件可能已存在)
                    file_path = default_file_path or Path(f"imported/{illust_id}.jpg")
                    self.record_download(
                        illust_id=illust_id,
                        file_path=file_path,
                        mode=mode,
                        date=date
                    )
                    imported_count += 1

            logger.info(
                f"Imported {imported_count} records from JSON progress file"
            )
            return imported_count

        except (json.JSONDecodeError, KeyError) as e:
            logger.warning(f"Failed to import from JSON progress: {e}")
            return 0
