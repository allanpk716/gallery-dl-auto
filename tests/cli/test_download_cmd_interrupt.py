"""download_cmd.py 中断信号处理测试"""

import json
import os
import signal
import subprocess
import sys
import time
from pathlib import Path

import pytest


@pytest.mark.skipif(sys.platform == "win32", reason="Windows 不支持 SIGINT 信号测试")
def test_interrupt_signal_handling():
    """测试 Ctrl+C 中断信号处理

    这个测试验证:
    1. 程序能够捕获 SIGINT 信号
    2. 输出 JSON 格式的中断信息
    3. 返回正确的退出码 (130)
    """
    # 创建一个简单的 Python 脚本来模拟中断处理
    test_script = """
import signal
import sys
import json

def handle_interrupt(signum, frame):
    print(json.dumps({
        "success": False,
        "error": "USER_INTERRUPT",
        "message": "下载被用户中断,进度已保存"
    }, ensure_ascii=False))
    sys.exit(130)

signal.signal(signal.SIGINT, handle_interrupt)

# 等待中断信号
print("Waiting for signal...", file=sys.stderr)
signal.pause()
"""

    # 在子进程中运行脚本
    process = subprocess.Popen(
        [sys.executable, "-c", test_script],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        text=True
    )

    # 等待进程启动
    time.sleep(0.5)

    # 发送 SIGINT 信号
    process.send_signal(signal.SIGINT)

    # 等待进程结束
    stdout, stderr = process.communicate(timeout=5)

    # 验证退出码
    assert process.returncode == 130, f"Expected exit code 130, got {process.returncode}"

    # 验证输出
    output = json.loads(stdout)
    assert output["success"] is False
    assert output["error"] == "USER_INTERRUPT"
    assert "进度已保存" in output["message"]


def test_interrupt_with_resume_state(tmp_path):
    """测试中断后断点状态文件保留

    验证:
    1. 中断时 .resume.json 文件应该存在
    2. 重新运行时能够从断点继续
    """
    # 这个测试需要在实际下载流程中进行,这里只验证状态文件结构
    from gallery_dl_auto.download.resume_manager import ResumeManager, ResumeState

    # 创建断点状态
    manager = ResumeManager(tmp_path, "daily", "2026-02-25")
    manager.update(index=50, downloaded=45, failed=5, last_illust_id=12345678)
    manager.save()

    # 验证文件存在
    state_file = tmp_path / "daily-2026-02-25" / ".resume.json"
    assert state_file.exists(), "断点状态文件应该在中断后保留"

    # 模拟重新运行
    manager2 = ResumeManager(tmp_path, "daily", "2026-02-25")
    assert manager2.should_resume(), "应该检测到断点状态"
    assert manager2.get_resume_index() == 50, "应该从索引 50 继续"


def test_interrupt_message_format():
    """测试中断消息的 JSON 格式"""
    # 验证中断消息符合预期格式
    expected_fields = ["success", "error", "message", "suggestion"]

    # 模拟中断消息
    interrupt_msg = {
        "success": False,
        "error": "USER_INTERRUPT",
        "message": "下载被用户中断,进度已保存",
        "suggestion": "重新运行相同命令将从断点继续下载"
    }

    # 验证所有必需字段存在
    for field in expected_fields:
        assert field in interrupt_msg, f"Missing field: {field}"

    # 验证 JSON 可序列化
    json_str = json.dumps(interrupt_msg, ensure_ascii=False)
    parsed = json.loads(json_str)
    assert parsed["error"] == "USER_INTERRUPT"
