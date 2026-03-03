"""测试辅助工具函数

提供测试中常用的辅助函数，简化测试代码编写。
"""

import json
from typing import Any

from click.testing import CliRunner, Result

from gallery_dl_auto.cli.main import cli


def assert_json_output(output: str, expected_keys: list[str] | None = None) -> dict[str, Any]:
    """验证 JSON 输出格式正确并返回解析后的数据

    Args:
        output: CLI 输出字符串
        expected_keys: 期望包含的键列表（可选）

    Returns:
        解析后的 JSON 数据

    Raises:
        AssertionError: 如果输出不是有效的 JSON 或缺少期望的键

    Example:
        >>> result = runner.invoke(cli, ['download', '--help'])
        >>> data = assert_json_output(result.output, ['command', 'usage'])
        >>> assert 'command' in data
    """
    try:
        data = json.loads(output)
    except json.JSONDecodeError as e:
        raise AssertionError(f"输出不是有效的 JSON: {e}\n输出内容: {output}")

    if expected_keys:
        for key in expected_keys:
            assert key in data, f"JSON 输出缺少期望的键: {key}"

    return data


def assert_jsonl_output(output: str, expected_keys: list[str] | None = None) -> dict[str, Any]:
    """验证 JSONL 输出格式正确并返回解析后的数据

    JSONL (JSON Lines) 格式要求：
    - 每行是一个独立的 JSON 对象
    - 不包含格式化空白（紧凑格式）
    - 在单行输出场景下只有一行

    Args:
        output: CLI 输出字符串
        expected_keys: 期望包含的键列表（可选）

    Returns:
        解析后的 JSON 数据

    Raises:
        AssertionError: 如果输出不是有效的 JSONL 格式

    Example:
        >>> result = runner.invoke(cli, ['download', '--format', 'jsonl', ...])
        >>> data = assert_jsonl_output(result.output, ['status', 'downloaded'])
        >>> assert data['status'] == 'success'
    """
    # 去除首尾空白
    output = output.strip()

    # JSONL 应该是单行
    lines = output.split('\n')
    assert len(lines) == 1, (
        f"JSONL 输出应该只有一行，实际有 {len(lines)} 行\n"
        f"输出内容: {output}"
    )

    # JSONL 不应该有缩进（紧凑格式）
    # 检查是否使用了紧凑格式（没有冒号后的空格或逗号后的空格）
    # 但要允许值中自然包含的空格（如中文字符串）
    try:
        # 尝试用紧凑格式重新序列化，如果和原输出一致则说明是紧凑格式
        compact = json.dumps(json.loads(output), separators=(",", ":"))
        assert output == compact, (
            "JSONL 输出应该是紧凑格式（不包含多余空格）\n"
            f"期望: {compact}\n"
            f"实际: {output}"
        )
    except json.JSONDecodeError:
        pass  # 如果 JSON 解析失败，让后续的 assert_json_output 处理

    # 复用 JSON 验证逻辑
    return assert_json_output(output, expected_keys)


def run_cli_command(runner: CliRunner, command: list[str], **kwargs) -> Result:
    """运行 CLI 命令并返回结果

    这是对 CliRunner.invoke 的封装，简化了命令调用。

    Args:
        runner: CliRunner 实例
        command: 命令参数列表（不包含主命令名）
        **kwargs: 传递给 invoke 的额外参数（如 input, env 等）

    Returns:
        Click 测试结果对象，包含 exit_code, output 等属性

    Example:
        >>> runner = CliRunner()
        >>> result = run_cli_command(runner, ['--help'])
        >>> assert result.exit_code == 0
        >>> assert 'Usage' in result.output

        >>> # 带交互输入的命令
        >>> result = run_cli_command(
        ...     runner,
        ...     ['auth', 'login'],
        ...     input='test_token\\n'
        ... )

    Note:
        - command 参数不包含主命令（cli），例如运行 `cli download --help`
          只需要传入 `['download', '--help']`
        - 如果需要捕获异常，设置 catch_exceptions=False
    """
    return runner.invoke(cli, command, **kwargs)


def assert_cli_success(result: Result, message: str = "命令执行失败") -> None:
    """断言 CLI 命令执行成功

    Args:
        result: CLI 命令执行结果
        message: 自定义错误消息

    Raises:
        AssertionError: 如果 exit_code 不为 0

    Example:
        >>> result = run_cli_command(runner, ['--help'])
        >>> assert_cli_success(result)
    """
    assert result.exit_code == 0, (
        f"{message}\n"
        f"退出码: {result.exit_code}\n"
        f"输出内容: {result.output}\n"
        f"异常: {result.exception}"
    )


def assert_cli_failure(result: Result, expected_exit_code: int | None = None) -> None:
    """断言 CLI 命令执行失败

    Args:
        result: CLI 命令执行结果
        expected_exit_code: 期望的退出码（可选，如果不提供则只检查非0）

    Raises:
        AssertionError: 如果命令执行成功或退出码不匹配

    Example:
        >>> result = run_cli_command(runner, ['invalid-command'])
        >>> assert_cli_failure(result, expected_exit_code=2)
    """
    if expected_exit_code is not None:
        assert result.exit_code == expected_exit_code, (
            f"期望退出码 {expected_exit_code}，实际为 {result.exit_code}\n"
            f"输出内容: {result.output}"
        )
    else:
        assert result.exit_code != 0, (
            f"命令应该执行失败但成功了\n"
            f"输出内容: {result.output}"
        )
