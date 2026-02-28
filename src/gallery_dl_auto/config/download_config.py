"""下载配置模型

定义下载相关的配置参数,支持 Pydantic 验证和序列化。
"""

from pydantic import BaseModel, Field


class DownloadConfig(BaseModel):
    """下载配置模型"""

    batch_size: int = Field(
        default=30,
        ge=1,
        le=100,
        description="每批次下载的作品数量"
    )
    batch_delay: float = Field(
        default=2.0,
        ge=0.0,
        description="批次间隔秒数"
    )
    concurrency: int = Field(
        default=1,
        ge=1,
        le=10,
        description="并发下载数(Phase 6 仅支持 1)"
    )
    image_delay: float = Field(
        default=2.5,
        ge=0.0,
        description="单张图片间隔秒数"
    )
    max_retries: int = Field(
        default=3,
        ge=1,
        le=10,
        description="单张图片最大重试次数"
    )
    retry_delay: float = Field(
        default=5.0,
        ge=0.0,
        description="重试间隔秒数"
    )

    model_config = {
        "validate_default": True,
        "extra": "forbid"
    }
