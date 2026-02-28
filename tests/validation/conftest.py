"""
JSON Schema fixtures for validation tests
"""
import pytest
from typing import Dict, Any


# 退出码映射表 (基于 INTEGRATION.md 和 error_codes.py)
EXIT_CODE_MAPPING = {
    # 成功场景
    "SUCCESS": 0,

    # 认证错误 (stderr 包含错误码)
    "AUTH_TOKEN_NOT_FOUND": 1,
    "AUTH_TOKEN_EXPIRED": 1,
    "AUTH_TOKEN_INVALID": 1,
    "AUTH_REFRESH_FAILED": 1,

    # API 错误
    "API_NETWORK_ERROR": 1,
    "API_RATE_LIMIT": 1,
    "API_SERVER_ERROR": 1,
    "API_INVALID_RESPONSE": 1,

    # 文件系统错误
    "FILE_PERMISSION_ERROR": 1,
    "FILE_DISK_FULL": 1,
    "FILE_INVALID_PATH": 1,

    # 下载错误
    "DOWNLOAD_FAILED": 1,
    "DOWNLOAD_TIMEOUT": 1,
    "DOWNLOAD_PERMISSION_DENIED": 1,
    "DOWNLOAD_DISK_FULL": 1,
    "DOWNLOAD_FILE_EXISTS": 1,
    "DOWNLOAD_NETWORK_ERROR": 1,
    "RATE_LIMIT_EXCEEDED": 1,

    # 元数据错误
    "METADATA_FETCH_FAILED": 1,

    # 参数错误
    "INVALID_ARGUMENT": 2,
    "INVALID_DATE_FORMAT": 2,

    # 内部错误
    "INTERNAL_ERROR": 1,

    # 下载结果状态
    "PARTIAL_SUCCESS": 1,  # 部分下载成功
    "COMPLETE_FAILURE": 2,  # 完全失败
}


def verify_exit_code(result, expected_error_code: str):
    """
    验证退出码和错误码是否匹配

    Args:
        result: Click 测试运行器的结果对象
        expected_error_code: 预期的错误码字符串

    Raises:
        AssertionError: 如果退出码不匹配
    """
    expected_exit_code = EXIT_CODE_MAPPING[expected_error_code]
    assert result.exit_code == expected_exit_code, \
        f"Expected exit code {expected_exit_code}, got {result.exit_code}"


def _download_result_schema() -> Dict[str, Any]:
    """
    download 命令成功响应的 JSON Schema

    基于 src/gallery_dl_auto/models/download_result.py 的 BatchDownloadResult
    """
    return {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "required": ["success", "total", "downloaded", "failed", "skipped", "success_list", "failed_errors", "output_dir"],
        "properties": {
            "success": {
                "type": "boolean",
                "description": "Overall download success status"
            },
            "total": {
                "type": "integer",
                "minimum": 0,
                "description": "Total number of items to download"
            },
            "downloaded": {
                "type": "integer",
                "minimum": 0,
                "description": "Number of successfully downloaded items"
            },
            "failed": {
                "type": "integer",
                "minimum": 0,
                "description": "Number of failed downloads"
            },
            "skipped": {
                "type": "integer",
                "minimum": 0,
                "description": "Number of skipped items"
            },
            "success_list": {
                "type": "array",
                "items": {"type": "integer"},
                "description": "List of successfully downloaded illust IDs"
            },
            "failed_errors": {
                "type": "array",
                "items": {"$ref": "#/definitions/StructuredError"},
                "description": "List of error details for failed downloads"
            },
            "output_dir": {
                "type": "string",
                "description": "Output directory path"
            }
        },
        "definitions": {
            "StructuredError": {
                "type": "object",
                "required": ["error_code", "error_type", "message", "severity"],
                "properties": {
                    "error_code": {
                        "type": "string",
                        "description": "Structured error code (e.g., AUTH_TOKEN_NOT_FOUND)"
                    },
                    "error_type": {
                        "type": "string",
                        "enum": ["auth", "api", "download", "file", "metadata", "internal"],
                        "description": "Error category"
                    },
                    "message": {
                        "type": "string",
                        "description": "Human-readable error message"
                    },
                    "suggestion": {
                        "type": "string",
                        "description": "Suggested action to resolve the error"
                    },
                    "severity": {
                        "type": "string",
                        "enum": ["warning", "error", "critical"],
                        "description": "Error severity level"
                    },
                    "illust_id": {
                        "type": "integer",
                        "description": "Related illust ID (if applicable)"
                    },
                    "original_error": {
                        "type": "string",
                        "description": "Original exception message"
                    },
                    "timestamp": {
                        "type": "string",
                        "format": "date-time",
                        "description": "Error timestamp in ISO format"
                    }
                }
            }
        }
    }


def _error_response_schema() -> Dict[str, Any]:
    """
    错误响应的 JSON Schema

    基于 src/gallery_dl_auto/models/error_response.py 的 StructuredError
    """
    return {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "required": ["error_code", "error_type", "message", "severity"],
        "properties": {
            "error_code": {
                "type": "string",
                "description": "Structured error code (e.g., AUTH_TOKEN_NOT_FOUND)"
            },
            "error_type": {
                "type": "string",
                "enum": ["auth", "api", "download", "file", "metadata", "internal"],
                "description": "Error category"
            },
            "message": {
                "type": "string",
                "description": "Human-readable error message"
            },
            "suggestion": {
                "type": "string",
                "description": "Suggested action to resolve the error"
            },
            "severity": {
                "type": "string",
                "enum": ["warning", "error", "critical"],
                "description": "Error severity level"
            },
            "illust_id": {
                "type": "integer",
                "description": "Related illust ID (if applicable)"
            },
            "original_error": {
                "type": "string",
                "description": "Original exception message"
            },
            "timestamp": {
                "type": "string",
                "format": "date-time",
                "description": "Error timestamp in ISO format"
            }
        }
    }


def _version_output_schema() -> Dict[str, Any]:
    """
    version 命令输出的 JSON Schema
    """
    return {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "required": ["version", "python_version", "platform"],
        "properties": {
            "version": {
                "type": "string",
                "description": "Application version"
            },
            "python_version": {
                "type": "string",
                "description": "Python version"
            },
            "platform": {
                "type": "string",
                "description": "Platform information"
            }
        }
    }


def _status_output_schema() -> Dict[str, Any]:
    """
    status 命令输出的 JSON Schema
    """
    return {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "required": ["logged_in", "token_valid"],
        "properties": {
            "logged_in": {
                "type": "boolean",
                "description": "Whether user is logged in"
            },
            "token_valid": {
                "type": "boolean",
                "description": "Whether token is valid"
            },
            "username": {
                "type": ["string", "null"],
                "description": "Username if logged in"
            }
        }
    }


def _config_get_output_schema() -> Dict[str, Any]:
    """
    config get 命令输出的 JSON Schema
    """
    return {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "required": ["key", "value"],
        "properties": {
            "key": {
                "type": "string",
                "description": "Configuration key"
            },
            "value": {
                "description": "Configuration value (can be any type)"
            }
        }
    }


def _config_list_output_schema() -> Dict[str, Any]:
    """
    config list 命令输出的 JSON Schema
    """
    return {
        "$schema": "http://json-schema.org/draft-07/schema#",
        "type": "object",
        "required": ["config"],
        "properties": {
            "config": {
                "type": "object",
                "description": "All configuration key-value pairs"
            }
        }
    }


# Export as pytest fixtures
@pytest.fixture
def download_result_schema():
    return _download_result_schema()


@pytest.fixture
def error_response_schema():
    return _error_response_schema()


@pytest.fixture
def version_output_schema():
    return _version_output_schema()


@pytest.fixture
def status_output_schema():
    return _status_output_schema()


@pytest.fixture
def config_get_output_schema():
    return _config_get_output_schema()


@pytest.fixture
def config_list_output_schema():
    return _config_list_output_schema()
