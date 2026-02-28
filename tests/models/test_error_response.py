"""测试结构化错误响应模型"""

import json

from gallery_dl_auto.models import BatchDownloadResult, ErrorSeverity, StructuredError


def test_structured_error_creation():
    """测试 StructuredError 创建和字段"""
    error = StructuredError(
        error_code="DOWNLOAD_FAILED",
        error_type="NetworkError",
        message="下载失败:作品 12345",
        suggestion="检查网络连接,错误将持续重试 3 次",
        severity=ErrorSeverity.WARNING,
        illust_id=12345,
        original_error="Connection timeout",
    )

    assert error.error_code == "DOWNLOAD_FAILED"
    assert error.error_type == "NetworkError"
    assert error.illust_id == 12345
    assert error.severity == ErrorSeverity.WARNING
    assert error.timestamp is not None


def test_structured_error_json_serialization():
    """测试 StructuredError 序列化为 JSON"""
    error = StructuredError(
        error_code="DOWNLOAD_PERMISSION_DENIED",
        error_type="PermissionError",
        message="无法写入文件: artwork.jpg",
        suggestion="检查目录权限或以管理员身份运行",
        severity=ErrorSeverity.ERROR,
        illust_id=67890,
        original_error="Permission denied",
    )

    # 序列化为 JSON
    json_str = error.model_dump_json()
    json_dict = json.loads(json_str)

    # 验证 JSON 格式
    assert json_dict["error_code"] == "DOWNLOAD_PERMISSION_DENIED"
    assert json_dict["error_type"] == "PermissionError"
    assert json_dict["illust_id"] == 67890
    assert json_dict["severity"] == "error"  # Enum 序列化为值
    assert "timestamp" in json_dict


def test_batch_download_result_success():
    """测试 BatchDownloadResult 成功场景"""
    result = BatchDownloadResult(
        success=True,
        total=10,
        downloaded=8,
        failed=0,
        skipped=2,
        success_list=[1, 2, 3, 4, 5, 6, 7, 8],
        failed_errors=[],
        output_dir="/downloads/pixiv",
    )

    assert result.success is True
    assert result.total == 10
    assert result.downloaded == 8
    assert result.failed == 0
    assert result.skipped == 2
    assert len(result.success_list) == 8
    assert len(result.failed_errors) == 0


def test_batch_download_result_partial_failure():
    """测试 BatchDownloadResult 部分失败场景"""
    errors = [
        StructuredError(
            error_code="DOWNLOAD_TIMEOUT",
            error_type="TimeoutError",
            message="下载超时:作品 999",
            suggestion="检查网络连接或稍后重试",
            severity=ErrorSeverity.WARNING,
            illust_id=999,
            original_error="Timeout",
        ),
        StructuredError(
            error_code="DOWNLOAD_FAILED",
            error_type="NetworkError",
            message="下载失败:作品 1000",
            suggestion="检查网络连接",
            severity=ErrorSeverity.WARNING,
            illust_id=1000,
            original_error="Network error",
        ),
    ]

    result = BatchDownloadResult(
        success=False,
        total=10,
        downloaded=6,
        failed=2,
        skipped=2,
        success_list=[1, 2, 3, 4, 5, 6],
        failed_errors=errors,
        output_dir="/downloads/pixiv",
    )

    assert result.success is False
    assert result.downloaded == 6
    assert result.failed == 2
    assert len(result.failed_errors) == 2
    assert result.failed_errors[0].illust_id == 999
    assert result.failed_errors[1].illust_id == 1000


def test_batch_download_result_json_serialization():
    """测试 BatchDownloadResult 序列化为 JSON"""
    errors = [
        StructuredError(
            error_code="DOWNLOAD_FAILED",
            error_type="NetworkError",
            message="下载失败:作品 123",
            suggestion="检查网络连接",
            severity=ErrorSeverity.WARNING,
            illust_id=123,
            original_error="Network error",
        )
    ]

    result = BatchDownloadResult(
        success=False,
        total=5,
        downloaded=3,
        failed=1,
        skipped=1,
        success_list=[1, 2, 3],
        failed_errors=errors,
        output_dir="/downloads/pixiv",
    )

    # 序列化为 JSON
    json_str = result.model_dump_json(indent=2)
    json_dict = json.loads(json_str)

    # 验证 JSON 格式
    assert json_dict["success"] is False
    assert json_dict["total"] == 5
    assert json_dict["downloaded"] == 3
    assert json_dict["failed"] == 1
    assert json_dict["skipped"] == 1
    assert json_dict["success_list"] == [1, 2, 3]
    assert len(json_dict["failed_errors"]) == 1
    assert json_dict["failed_errors"][0]["illust_id"] == 123


def test_error_severity_enum():
    """测试 ErrorSeverity 枚举值"""
    assert ErrorSeverity.WARNING.value == "warning"
    assert ErrorSeverity.ERROR.value == "error"
    assert ErrorSeverity.CRITICAL.value == "critical"


def test_structured_error_optional_fields():
    """测试 StructuredError 可选字段"""
    error = StructuredError(
        error_code="INTERNAL_ERROR",
        error_type="InternalError",
        message="内部错误",
        suggestion="请联系开发者",
        severity=ErrorSeverity.CRITICAL,
    )

    assert error.illust_id is None
    assert error.original_error is None
    assert error.timestamp is not None
