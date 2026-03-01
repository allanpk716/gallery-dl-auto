"""Mode 相关的错误类型定义"""


class ModeError(Exception):
    """Mode 相关错误的基类

    所有 mode 相关的异常都应该继承此类。
    """

    pass


class InvalidModeError(ModeError):
    """无效的 mode 值

    当用户输入或代码传递了一个不在支持列表中的 mode 时抛出。

    Attributes:
        mode: 无效的 mode 值
        valid_modes: 所有有效的 mode 列表
    """

    def __init__(self, mode: str, valid_modes: list[str]):
        """初始化 InvalidModeError

        Args:
            mode: 无效的 mode 值
            valid_modes: 所有有效的 mode 列表
        """
        self.mode = mode
        self.valid_modes = valid_modes
        super().__init__(
            f"Invalid mode '{mode}'. Valid modes: {', '.join(sorted(valid_modes))}"
        )


class UnsupportedModeError(ModeError):
    """mode 不被当前引擎支持

    当某个 mode 被当前下载引擎不支持时抛出。

    Attributes:
        mode: 不支持的 mode 值
        engine: 当前引擎名称
        alternative_engine: 建议使用的替代引擎
    """

    def __init__(self, mode: str, engine: str, alternative_engine: str):
        """初始化 UnsupportedModeError

        Args:
            mode: 不支持的 mode 值
            engine: 当前引擎名称
            alternative_engine: 建议使用的替代引擎
        """
        self.mode = mode
        self.engine = engine
        self.alternative_engine = alternative_engine
        super().__init__(
            f"Mode '{mode}' is not supported by {engine}. "
            f"Please use --engine {alternative_engine}"
        )
