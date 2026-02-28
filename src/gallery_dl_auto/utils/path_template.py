"""路径模板系统

支持变量替换和路径清理的模板系统。
"""

from __future__ import annotations

from pathlib import Path

from pathvalidate import sanitize_filepath


class PathTemplate:
    """路径模板解析器

    支持变量替换和路径清理。
    """

    # 支持的模板变量
    VARIABLES = {"mode", "date", "illust_id", "title", "author", "author_id"}

    def __init__(self, template: str) -> None:
        """初始化模板

        Args:
            template: 模板字符串,例如 "{mode}/{date}/{title}.jpg"
        """
        self.template = template

    def render(self, context: dict[str, str | int]) -> Path:
        """渲染路径模板

        Args:
            context: 包含模板变量的字典

        Returns:
            清理后的 Path 对象

        Examples:
            >>> template = PathTemplate("{mode}/{date}/{author}/{title}.jpg")
            >>> path = template.render({
            ...     "mode": "daily",
            ...     "date": "2026-02-25",
            ...     "author": "Artist Name",
            ...     "title": "Beautiful Sunset"
            ... })
            >>> str(path)
            'daily/2026-02-25/Artist Name/Beautiful Sunset.jpg'
        """
        # 1. 替换模板变量
        path_str = self.template
        for var in self.VARIABLES:
            placeholder = f"{{{var}}}"
            if placeholder in path_str:
                value = str(context.get(var, "unknown"))
                path_str = path_str.replace(placeholder, value)

        # 2. 清理非法字符
        path_str = str(sanitize_filepath(path_str))

        return Path(path_str)
