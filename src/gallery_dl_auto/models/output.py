"""标准化 JSON 输出模型

提供一致的 CLI 输出格式,支持成功和错误两种场景。
"""

from __future__ import annotations

from typing import Any

from pydantic import BaseModel, ConfigDict, Field

from gallery_dl_auto.utils.error_codes import ErrorCode


class ErrorDetail(BaseModel):
    """错误详情

    Attributes:
        code: 标准化错误码
        message: 用户可读的错误消息
        details: 可选的额外信息
    """

    code: ErrorCode
    message: str
    details: dict[str, Any] | None = None

    model_config = ConfigDict(use_enum_values=True)


class DownloadSuccessData(BaseModel):
    """下载成功时的数据结构

    Attributes:
        total: 总图片数
        success_count: 成功下载数
        failed_count: 失败下载数
        output_dir: 输出目录路径
        date: 排行榜日期
        mode: 排行榜类型
        path_template: 路径模板 (可选)
        success_list: 成功下载列表
        failed_list: 失败下载列表
    """

    total: int = Field(..., description="总图片数")
    success_count: int = Field(..., description="成功下载数")
    failed_count: int = Field(..., description="失败下载数")
    output_dir: str = Field(..., description="输出目录路径")
    date: str = Field(..., description="排行榜日期")
    mode: str = Field(..., description="排行榜类型")
    path_template: str | None = Field(None, description="路径模板")
    success_list: list[dict[str, Any]] = Field(default_factory=list)
    failed_list: list[dict[str, Any]] = Field(default_factory=list)


class DownloadOutput(BaseModel):
    """download 命令的输出结构

    Attributes:
        success: 是否成功
        data: 成功时的数据 (仅当 success=True 时存在)
        error: 失败时的错误详情 (仅当 success=False 时存在)
    """

    success: bool
    data: DownloadSuccessData | None = None
    error: ErrorDetail | None = None

    def to_json(self) -> str:
        """序列化为 JSON 字符串

        使用 Pydantic 的 model_dump_json() 方法,配置:
        - exclude_none=True: 移除 None 字段 (成功时无 error,错误时无 data)
        - indent=2: 美化输出
        - ensure_ascii=False: 支持中文等 Unicode 字符

        Returns:
            格式化的 JSON 字符串
        """
        return self.model_dump_json(exclude_none=True, indent=2, ensure_ascii=False)


class RefreshSuccessData(BaseModel):
    """refresh 命令成功时的数据结构

    Attributes:
        old_token_masked: 旧 token (遮蔽)
        new_token_masked: 新 token (遮蔽)
        expires_in_days: token 有效期 (天)
    """

    old_token_masked: str = Field(..., description="旧 token (遮蔽)")
    new_token_masked: str = Field(..., description="新 token (遮蔽)")
    expires_in_days: int = Field(..., description="token 有效期 (天)")


class RefreshOutput(BaseModel):
    """refresh 命令的输出结构

    Attributes:
        success: 是否成功
        data: 成功时的数据 (仅当 success=True 时存在)
        error: 失败时的错误详情 (仅当 success=False 时存在)
    """

    success: bool
    data: RefreshSuccessData | None = None
    error: ErrorDetail | None = None

    def to_json(self) -> str:
        """序列化为 JSON 字符串

        Returns:
            格式化的 JSON 字符串
        """
        return self.model_dump_json(exclude_none=True, indent=2, ensure_ascii=False)
