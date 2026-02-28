"""文件名清理工具

移除 Windows 非法字符,确保跨平台兼容。
"""

import re


def sanitize_filename(filename: str, max_length: int = 200) -> str:
    """清理文件名,移除 Windows 非法字符。

    Windows 非法字符: < > : " / \\ | ? *
    保留字符: 空格、下划线、连字符、中文

    Args:
        filename: 原始文件名
        max_length: 最大长度限制 (默认 200)

    Returns:
        清理后的安全文件名

    Examples:
        >>> sanitize_filename("美丽的风景<测试>.jpg")
        '美丽的风景测试.jpg'
        >>> sanitize_filename("test:file*.txt")
        'testfile.txt'
    """
    # 移除非法字符
    filename = re.sub(r'[<>:"/\\|?*]', "", filename)
    # 移除首尾空格和点
    filename = filename.strip(". ")
    # 限制长度
    return filename[:max_length]
