"""测试路径模板系统"""

from pathlib import Path

from gallery_dl_auto.utils.path_template import PathTemplate


def test_template_render_basic() -> None:
    """测试基本变量替换"""
    template = PathTemplate("{mode}/{date}/{title}.jpg")
    context = {
        "mode": "daily",
        "date": "2026-02-25",
        "title": "Sunset",
    }

    path = template.render(context)

    assert path == Path("daily/2026-02-25/Sunset.jpg")


def test_template_render_all_variables() -> None:
    """测试所有变量"""
    template = PathTemplate(
        "{mode}/{date}/{illust_id}/{title}/{author}/{author_id}.jpg"
    )
    context = {
        "mode": "daily",
        "date": "2026-02-25",
        "illust_id": 12345,
        "title": "Test Title",
        "author": "Test Author",
        "author_id": 67890,
    }

    path = template.render(context)

    # 验证所有变量都被替换
    path_str = str(path)
    assert "daily" in path_str
    assert "2026-02-25" in path_str
    assert "12345" in path_str
    assert "Test Title" in path_str
    assert "Test Author" in path_str
    assert "67890" in path_str
    # 不应包含未替换的占位符
    assert "{" not in path_str
    assert "}" not in path_str


def test_template_missing_variable() -> None:
    """测试缺失变量替换为 'unknown'"""
    template = PathTemplate("{mode}/{author}/{title}.jpg")
    context = {
        "mode": "daily",
        "title": "Test Title",
        # 缺失 author
    }

    path = template.render(context)

    path_str = str(path)
    assert "unknown" in path_str
    assert path_str.startswith("daily")
    assert path_str.endswith("Test Title.jpg")


def test_template_sanitization() -> None:
    """测试路径清理

    Windows 非法字符: : * ? " < > | 应被清理
    """
    template = PathTemplate("{mode}/{author}/{title}.jpg")
    context = {
        "mode": "daily",
        "author": "Artist: Name",  # 包含非法字符 ":"
        "title": "Title? With*Chars",  # 包含非法字符 "?" 和 "*"
    }

    path = template.render(context)

    path_str = str(path)
    # Windows 非法字符应被清理
    assert ":" not in path_str
    assert "?" not in path_str
    assert "*" not in path_str
    # 应保留合法部分
    assert "Artist" in path_str or "Name" in path_str
    assert "Title" in path_str or "WithChars" in path_str


def test_template_with_author_id() -> None:
    """测试 author_id 变量"""
    template = PathTemplate("{author_id}/{title}.jpg")
    context = {
        "author_id": 67890,
        "title": "Test Artwork",
    }

    path = template.render(context)

    path_str = str(path)
    # 数字应转换为字符串
    assert "67890" in path_str
    assert "Test Artwork" in path_str
