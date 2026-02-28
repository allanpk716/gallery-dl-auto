"""元数据模型

提供作品元数据的结构化建模和 CLI 输出模型。
"""

from gallery_dl_auto.models.artwork import (
    ArtworkMetadata,
    ArtworkStatistics,
    ArtworkTag,
)
from gallery_dl_auto.models.error_response import (
    BatchDownloadResult,
    ErrorSeverity,
    StructuredError,
)
from gallery_dl_auto.models.output import (
    DownloadOutput,
    DownloadSuccessData,
    ErrorDetail,
    RefreshOutput,
    RefreshSuccessData,
)

__all__ = [
    "ArtworkMetadata",
    "ArtworkStatistics",
    "ArtworkTag",
    "BatchDownloadResult",
    "DownloadOutput",
    "DownloadSuccessData",
    "ErrorDetail",
    "ErrorSeverity",
    "RefreshOutput",
    "RefreshSuccessData",
    "StructuredError",
]
