"""Click CLI 测试共享 fixture"""

import pytest
from click.testing import CliRunner


@pytest.fixture
def runner():
    """提供 Click CliRunner 实例"""
    return CliRunner()
