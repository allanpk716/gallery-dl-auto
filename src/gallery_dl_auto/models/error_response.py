"""结构化错误响应模型

定义统一的 JSON 错误响应格式,用于第三方程序调用。
"""

from datetime import datetime
from enum import Enum
from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ErrorSeverity(str, Enum):
    """错误严重性级别"""

    WARNING = "warning"  # 跳过单个项目,继续执行
    ERROR = "error"  # 操作失败,但程序继续
    CRITICAL = "critical"  # 程序终止


class StructuredError(BaseModel):
    """结构化错误模型

    用于表示单个错误的详细信息,包含错误码、类型、消息、建议操作等。
    """

    model_config = ConfigDict(use_enum_values=True)

    error_code: str = Field(..., description="错误码,如 DOWNLOAD_FAILED")
    error_type: str = Field(..., description="错误类型,如 NetworkError")
    message: str = Field(..., description="用户友好的错误消息")
    suggestion: str = Field(..., description="建议的操作步骤")
    severity: ErrorSeverity = Field(..., description="错误严重性")
    illust_id: Optional[int] = Field(None, description="相关作品 ID")
    original_error: Optional[str] = Field(None, description="原始异常信息")
    timestamp: str = Field(
        default_factory=lambda: datetime.now().isoformat(),
        description="错误发生时间",
    )


class BatchDownloadResult(BaseModel):
    """批量下载结果模型

    用于表示批量下载的整体结果,包含成功和失败的详细信息。
    """

    success: bool = Field(..., description="整体是否成功")
    total: int = Field(..., description="总作品数")
    downloaded: int = Field(..., description="成功下载数")
    failed: int = Field(..., description="失败数")
    skipped: int = Field(..., description="跳过数(已下载)")
    success_list: list[int] = Field(default_factory=list, description="成功作品 ID")
    failed_errors: list[StructuredError] = Field(
        default_factory=list, description="失败错误列表"
    )
    output_dir: str = Field(..., description="输出目录(相对路径)")
    actual_download_dir: Optional[str] = Field(None, description="实际下载目录(绝对路径,包含mode和date)")
