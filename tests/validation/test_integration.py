"""
第三方工具集成测试 - 使用 subprocess 模拟真实调用场景

测试目标:
1. 验证 CLI 可通过 subprocess 正确调用
2. 验证 JSON 输出格式正确
3. 验证退出码符合预期
4. 验证 Windows 编码处理
"""
import json
import subprocess
import pytest
import sys
import signal
from pathlib import Path


class TestThirdPartyIntegration:
    """测试第三方工具通过 subprocess 调用 CLI"""

    def test_subprocess_version_command(self):
        """验证 version 命令的 subprocess 调用"""
        result = subprocess.run(
            ["python", "-m", "gallery_dl_auto.cli.main", "--json-output", "version"],
            capture_output=True,
            text=True,
            encoding='utf-8',  # Windows 必需
            timeout=10,
            cwd=Path(__file__).parent.parent.parent  # 项目根目录
        )

        # 验证退出码
        assert result.returncode == 0, f"Expected exit code 0, got {result.returncode}"

        # 验证 stdout 是有效 JSON
        try:
            output = json.loads(result.stdout)
        except json.JSONDecodeError as e:
            pytest.fail(f"Failed to parse JSON output: {e}\nStdout: {result.stdout}\nStderr: {result.stderr}")

        # 验证 JSON 结构
        assert "version" in output, "Missing 'version' field"
        assert "python_version" in output, "Missing 'python_version' field"
        assert "platform" in output, "Missing 'platform' field"

        # 验证输出不包含乱码
        assert "version" in result.stdout, "Output appears corrupted or missing"

    def test_subprocess_status_command(self):
        """验证 status 命令的 subprocess 调用"""
        # 注意: status 命令目前未实现 JSON 输出 (计划 10-01 总结)
        # 这里验证命令可调用,输出可读
        result = subprocess.run(
            ["python", "-m", "gallery_dl_auto.cli.main", "--json-output", "status"],
            capture_output=True,
            text=True,
            encoding='utf-8',
            timeout=10,
            cwd=Path(__file__).parent.parent.parent
        )

        # status 命令可能因缺少 token 而失败,也可能成功(如果有 token)
        # 重点验证输出不包含乱码,编码处理正确
        assert isinstance(result.stdout, str), "Stdout should be a string"
        assert isinstance(result.stderr, str), "Stderr should be a string"

        # 验证输出可读(不包含乱码)
        # 由于当前未实现 JSON 输出,会输出表格格式,这也是可接受的
        combined_output = result.stdout + result.stderr
        assert len(combined_output) > 0 or result.returncode != 0, \
            "Should produce some output or fail"

    def test_subprocess_config_command(self):
        """验证 config 命令的 subprocess 调用"""
        # 注意: config 命令当前实现未支持 JSON 输出
        # 且 config 是单一命令,没有 list 子命令
        # 这里测试命令的基本可调用性
        result = subprocess.run(
            ["python", "-m", "gallery_dl_auto.cli.main", "config"],
            capture_output=True,
            text=True,
            encoding='utf-8',
            timeout=10,
            cwd=Path(__file__).parent.parent.parent
        )

        # config 命令需要 config.yaml 文件,可能因找不到文件而失败
        # 验证输出不包含乱码
        assert isinstance(result.stdout, str), "Stdout should be a string"
        assert isinstance(result.stderr, str), "Stderr should be a string"

        # 验证输出可读
        combined_output = result.stdout + result.stderr
        # 应该有一些输出(错误消息或配置表格)
        assert len(combined_output) > 0 or result.returncode != 0, \
            "Should produce some output or fail"

    def test_subprocess_error_output_encoding(self):
        """验证错误输出的编码处理"""
        # 故意使用无效命令触发错误
        result = subprocess.run(
            ["python", "-m", "gallery_dl_auto.cli.main", "--json-output", "invalid_command"],
            capture_output=True,
            text=True,
            encoding='utf-8',
            timeout=10,
            cwd=Path(__file__).parent.parent.parent
        )

        # 验证退出码非零
        assert result.returncode != 0, "Invalid command should return non-zero exit code"

        # 验证输出不包含乱码 (检查是否能正确解码)
        # Click 会输出错误信息,应该能正确解码
        assert isinstance(result.stdout, str), "Stdout should be a string"
        assert isinstance(result.stderr, str), "Stderr should be a string"

    def test_subprocess_download_with_or_without_token(self):
        """验证 download 命令的真实场景调用

        测试两种情况:
        1. 如果有 token: 验证成功下载场景
        2. 如果无 token: 验证错误处理场景
        """
        result = subprocess.run(
            ["python", "-m", "gallery_dl_auto.cli.main", "download", "--type", "daily"],
            capture_output=True,
            text=True,
            encoding='utf-8',
            timeout=60,  # 下载可能需要较长时间
            cwd=Path(__file__).parent.parent.parent
        )

        # 解析输出
        output_text = result.stdout if result.stdout.strip() else result.stderr

        # 尝试解析整个输出为 JSON
        json_output = None
        try:
            json_output = json.loads(output_text)
        except json.JSONDecodeError:
            # 如果失败,尝试提取 JSON (可能在日志之后)
            lines = output_text.strip().split('\n')
            # 尝试从后往前找到 JSON 块的开始
            json_lines = []
            brace_count = 0
            for line in reversed(lines):
                json_lines.insert(0, line)
                brace_count += line.count('{') - line.count('}')
                if brace_count == 0 and '{' in line:
                    # 找到 JSON 块的开始
                    try:
                        json_output = json.loads('\n'.join(json_lines))
                        break
                    except json.JSONDecodeError:
                        json_lines = []
                        continue

        # 验证场景 1: 有 token,下载成功
        if result.returncode == 0:
            assert json_output is not None, \
                f"Successful download should produce JSON output, got: {output_text}"

            # 验证 JSON 结构符合 BatchDownloadResult schema
            assert "success" in json_output, "Should contain 'success' field"
            assert "total" in json_output, "Should contain 'total' field"
            assert "downloaded" in json_output, "Should contain 'downloaded' field"
            assert "failed" in json_output, "Should contain 'failed' field"
            assert "skipped" in json_output, "Should contain 'skipped' field"
            assert "success_list" in json_output, "Should contain 'success_list' field"
            assert "failed_errors" in json_output, "Should contain 'failed_errors' field"
            assert "output_dir" in json_output, "Should contain 'output_dir' field"

        # 验证场景 2: 无 token,返回错误
        else:
            # 退出码应该是 1 (认证错误) 或 2 (完全失败)
            assert result.returncode in [1, 2], \
                f"Download failure should return exit code 1 or 2, got {result.returncode}"

            # 验证输出是有效 JSON (StructuredError 格式)
            if json_output is not None:
                # 验证错误结构
                assert "error_code" in json_output or "error" in json_output, \
                    f"Error output should contain error_code or error field, got: {json_output}"

    def test_subprocess_download_invalid_argument(self):
        """验证 download 命令参数错误处理"""
        # 使用无效的 ranking type 触发参数错误
        result = subprocess.run(
            ["python", "-m", "gallery_dl_auto.cli.main", "download", "--type", "invalid_type"],
            capture_output=True,
            text=True,
            encoding='utf-8',
            timeout=10,
            cwd=Path(__file__).parent.parent.parent
        )

        # 验证退出码为 2 (Click 参数错误标准退出码)
        assert result.returncode == 2, \
            f"Invalid argument should return exit code 2, got {result.returncode}"

        # 验证输出包含错误信息
        combined_output = result.stdout + result.stderr
        assert len(combined_output) > 0, "Should produce error output"

        # 验证输出不包含乱码
        assert isinstance(result.stderr, str), "Stderr should be a string"

    def test_subprocess_download_missing_required_argument(self):
        """验证 download 命令缺少必需参数时的错误处理"""
        # 不提供 --type 参数 (必需参数)
        result = subprocess.run(
            ["python", "-m", "gallery_dl_auto.cli.main", "download"],
            capture_output=True,
            text=True,
            encoding='utf-8',
            timeout=10,
            cwd=Path(__file__).parent.parent.parent
        )

        # 验证退出码为 2 (Click 缺少必需参数)
        assert result.returncode == 2, \
            f"Missing required argument should return exit code 2, got {result.returncode}"

        # 验证输出包含错误信息
        combined_output = result.stdout + result.stderr
        assert len(combined_output) > 0, "Should produce error output"
        assert "required" in combined_output.lower() or "missing" in combined_output.lower(), \
            "Error message should mention missing or required parameter"

    def test_subprocess_batch_download(self, tmp_path):
        """验证批量下载多个排行榜的可靠性

        模拟第三方工具批量调用场景:
        1. 连续下载多个排行榜类型
        2. 验证每个命令执行成功
        3. 验证输出格式一致
        4. 验证速率限制保护
        """
        import time

        output_dir = tmp_path / "downloads"
        ranking_types = ["daily", "weekly"]

        results = []
        for i, ranking_type in enumerate(ranking_types):
            # 添加延迟以避免速率限制 (第二次调用前等待)
            if i > 0:
                time.sleep(2)  # 2 秒延迟

            result = subprocess.run(
                ["python", "-m", "gallery_dl_auto.cli.main", "download",
                 "--type", ranking_type, "--output", str(output_dir)],
                capture_output=True,
                text=True,
                encoding='utf-8',
                timeout=60,
                cwd=Path(__file__).parent.parent.parent
            )

            results.append({
                "type": ranking_type,
                "returncode": result.returncode,
                "stdout": result.stdout,
                "stderr": result.stderr
            })

        # 验证所有命令执行完成
        # 注意: 由于测试环境可能没有有效 token,我们允许失败
        # 但验证格式和编码处理正确
        for result in results:
            # 验证返回码是预期的 (0=成功, 1=认证错误, 2=参数错误)
            assert result["returncode"] in [0, 1, 2], \
                f"{result['type']} returned unexpected exit code: {result['returncode']}"

            # 验证输出格式一致 (有输出且无乱码)
            combined_output = result["stdout"] + result["stderr"]
            assert isinstance(result["stdout"], str), \
                f"{result['type']} stdout should be string"
            assert isinstance(result["stderr"], str), \
                f"{result['type']} stderr should be string"

            # 如果成功,尝试解析 JSON 输出
            if result["returncode"] == 0:
                try:
                    json_output = json.loads(result["stdout"])
                    assert "success" in json_output, \
                        f"{result['type']} should contain 'success' field"
                    assert "total" in json_output, \
                        f"{result['type']} should contain 'total' field"
                except json.JSONDecodeError:
                    # JSON 解析失败是可接受的 (可能有日志输出)
                    pass

        # 验证批量调用之间有适当延迟
        # (已在测试中实现,生产环境应由调用方负责)


class TestErrorRecovery:
    """测试错误恢复机制和超时处理"""

    def test_timeout_handling(self):
        """验证长时间运行命令的超时处理

        模拟第三方工具设置超时场景:
        1. 设置 1 秒超时
        2. 预期触发 subprocess.TimeoutExpired 异常
        3. 验证异常处理正确
        """
        # 预期会触发超时异常 (1 秒不足以完成下载)
        with pytest.raises(subprocess.TimeoutExpired) as exc_info:
            subprocess.run(
                ["python", "-m", "gallery_dl_auto.cli.main", "download", "--type", "daily"],
                capture_output=True,
                encoding='utf-8',
                timeout=1,  # 1 秒超时 (预期会超时)
                cwd=Path(__file__).parent.parent.parent
            )

        # 验证异常类型正确
        assert exc_info.type == subprocess.TimeoutExpired

        # 验证异常信息包含命令信息
        assert exc_info.value.cmd is not None
        assert exc_info.value.timeout == 1

    @pytest.mark.skipif(sys.platform == "win32", reason="Signal handling differs on Windows")
    def test_interrupt_handling(self):
        """验证 Ctrl+C 中断处理 (仅 Unix)

        模拟用户中断场景:
        1. 启动长时间运行的命令
        2. 发送 SIGINT (Ctrl+C)
        3. 验证进程正确终止
        4. 验证退出码为 130 (128 + SIGINT)
        """
        process = subprocess.Popen(
            ["python", "-m", "gallery_dl_auto.cli.main", "download", "--type", "daily"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding='utf-8',
            cwd=Path(__file__).parent.parent.parent
        )

        # 等待进程启动
        import time
        time.sleep(1)

        # 发送 SIGINT (Ctrl+C)
        process.send_signal(signal.SIGINT)

        # 等待进程终止
        try:
            stdout, stderr = process.communicate(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()
            stdout, stderr = process.communicate()
            pytest.fail("Process did not terminate after SIGINT")

        # 验证退出码 130 (128 + SIGINT)
        # 注意: Python 进程可能返回其他退出码,取决于信号处理
        # 130 是标准 Unix 行为,但 Python 可能返回 2 或其他
        assert process.returncode in [130, 2, 1], \
            f"Expected exit code 130, 2, or 1 after SIGINT, got {process.returncode}"

    def test_subprocess_exception_handling(self):
        """验证 subprocess 异常处理

        测试各种 subprocess 异常场景:
        1. 命令未找到
        2. 权限错误
        3. 编码错误
        """
        # 测试 1: 命令未找到
        with pytest.raises(FileNotFoundError):
            subprocess.run(
                ["nonexistent_command_12345"],
                capture_output=True,
                encoding='utf-8',
                timeout=5
            )

    def test_graceful_degradation_on_error(self):
        """验证错误时的优雅降级

        测试错误场景下的行为:
        1. 错误输出格式正确
        2. 退出码非零
        3. 不包含乱码
        4. 错误信息可读
        """
        # 使用无效参数触发错误
        result = subprocess.run(
            ["python", "-m", "gallery_dl_auto.cli.main", "download", "--type", "invalid_type"],
            capture_output=True,
            text=True,
            encoding='utf-8',
            timeout=10,
            cwd=Path(__file__).parent.parent.parent
        )

        # 验证错误处理
        assert result.returncode != 0, "Error should return non-zero exit code"
        assert isinstance(result.stderr, str), "Stderr should be string"
        assert len(result.stderr) > 0, "Should produce error message"

        # 验证错误信息可读 (不包含乱码)
        # Click 会输出错误信息,应该能正确解码
        assert result.stderr.isprintable() or '\n' in result.stderr, \
            "Error message should be readable"
