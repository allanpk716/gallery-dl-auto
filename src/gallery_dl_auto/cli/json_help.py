"""JSON 帮助生成器

为第三方工具提供结构化的 CLI 元数据,包括命令名称、参数、类型等信息。
"""

import click


def generate_json_help(cli_group: click.Group) -> dict:
    """生成结构化 JSON 帮助信息

    Args:
        cli_group: Click 主命令组

    Returns:
        命令映射字典,格式为:
        {
            "command_name": {
                "name": "command_name",
                "description": "命令描述",
                "parameters": [
                    {
                        "name": "参数名",
                        "type": "参数类型",
                        "required": 是否必需,
                        "description": "参数描述",
                        "default_value": 默认值
                    }
                ]
            }
        }

    Example:
        >>> from gallery_dl_auto.cli.main import cli
        >>> help_data = generate_json_help(cli)
        >>> print(json.dumps(help_data, ensure_ascii=False, indent=2))
    """
    commands_metadata = {}

    # 遍历所有注册命令
    for cmd_name, cmd in cli_group.commands.items():
        # 跳过隐藏命令
        if getattr(cmd, "hidden", False):
            continue

        # 提取参数信息
        parameters = []
        for param in cmd.params:
            param_info = {
                "name": param.name,
                "type": _map_param_type(param.type),
                "required": getattr(param, "required", False),
                "description": param.help or "",
                "default_value": param.default if param.default is not click.core.UNSET else None,
            }
            parameters.append(param_info)

        # 添加全局选项到每个命令的参数列表
        global_options = _get_global_options()
        parameters.extend(global_options)

        # 构建命令元数据
        commands_metadata[cmd_name] = {
            "name": cmd_name,
            "description": cmd.help.strip().split("\n")[0] if cmd.help else "",
            "parameters": parameters,
        }

    return commands_metadata


def _map_param_type(param_type: click.types.ParamType) -> str:
    """将 Click 参数类型映射为简单类型字符串

    Args:
        param_type: Click 参数类型对象

    Returns:
        简单类型字符串: "string", "integer", "boolean", "number", "array"

    Example:
        >>> _map_param_type(click.INT)
        'integer'
        >>> _map_param_type(click.BOOL)
        'boolean'
    """
    if isinstance(param_type, click.types.IntParamType):
        return "integer"
    elif isinstance(param_type, click.types.BoolParamType):
        return "boolean"
    elif isinstance(param_type, click.types.FloatParamType):
        return "number"
    elif isinstance(param_type, (click.types.StringParamType, click.types.Path)):
        return "string"
    elif isinstance(param_type, click.types.Tuple):
        return "array"
    else:
        return "string"  # 默认类型


def _get_global_options() -> list[dict]:
    """获取全局选项的元数据

    Returns:
        全局选项列表,每个选项包含完整的参数字段

    Note:
        全局选项会合并到每个命令的参数列表中,便于第三方工具直接使用。
    """
    return [
        {
            "name": "verbose",
            "type": "boolean",
            "required": False,
            "description": "详细模式:显示调试信息(与 --quiet/--json-output 冲突时被忽略)",
            "default_value": False,
        },
        {
            "name": "quiet",
            "type": "boolean",
            "required": False,
            "description": "静默模式:禁用所有输出",
            "default_value": False,
        },
        {
            "name": "json_output",
            "type": "boolean",
            "required": False,
            "description": "JSON 输出模式:所有输出为 JSON 格式",
            "default_value": False,
        },
        {
            "name": "json_help",
            "type": "boolean",
            "required": False,
            "description": "输出结构化 JSON 帮助信息",
            "default_value": False,
        },
    ]
