# 集成指南

本文档为第三方开发者提供 gallery-dl-auto 的集成指南,包括 CLI 调用方式、参数说明、示例代码和退出码参考。

**适用场景**:
- 自动化脚本集成
- 第三方工具调用
- CI/CD 流程集成
- 批量下载任务编排

**前置要求**:
- Python 3.10+
- 已安装 gallery-dl-auto (pip install gallery-dl-auto)
- 基本熟悉 CLI 工具使用

## CLI 调用方式

### 基本命令格式

gallery-dl-auto 采用 Click CLI 框架,提供一致的命令行接口:

```bash
pixiv-downloader [全局选项] <命令> [命令选项] [参数]
```

**示例**:
```bash
# 下载每日排行榜
pixiv-downloader download --type daily --date 2026-02-25

# 静默模式查询配置
pixiv-downloader --quiet config get download_dir

# JSON 输出获取版本信息
pixiv-downloader --json-output version
```

### 全局参数

所有命令都支持以下全局参数:

| 参数 | 简写 | 说明 | 默认值 |
|------|------|------|--------|
| --verbose | -v | 详细输出模式,显示进度和日志信息 | 关闭 |
| --quiet | -q | 静默模式,禁用所有控制台输出(包括 stderr) | 关闭 |
| --json-output | | JSON 输出模式,确保所有输出都是有效的 JSON 格式 | 关闭 |
| --json-help | | 输出命令元数据的 JSON 格式帮助信息 | 关闭 |

**参数说明**:
- `--verbose`: 启用详细模式,显示下载进度、文件名等信息。适用于交互式使用。
- `--quiet`: 启用静默模式,禁用所有控制台输出,仅保留文件日志。适用于后台任务和第三方工具调用。
- `--json-output`: 启用 JSON 输出模式,确保所有输出(包括错误信息)都是有效的 JSON 格式。适用于第三方工具集成。
- `--json-help`: 输出所有命令的结构化元数据,用于程序化发现 CLI API。不影响命令执行。

### 参数优先级

当多个输出控制参数同时使用时,优先级为:

**--json-output > --quiet > --verbose**

**示例**:
```bash
# 静默模式(verbose 被忽略)
pixiv-downloader --quiet --verbose download --type daily

# JSON 输出模式(quiet 和 verbose 被忽略)
pixiv-downloader --json-output --quiet --verbose download --type daily

# 详细模式(无冲突)
pixiv-downloader --verbose download --type daily
```

## JSON API

### 获取命令元数据 (--json-help)

`--json-help` 参数输出所有命令的结构化元数据,用于程序化发现 CLI API:

```bash
pixiv-downloader --json-help
```

**输出格式**:
```json
{
  "download": {
    "name": "download",
    "description": "Download Pixiv ranking images",
    "parameters": [
      {
        "name": "type",
        "type": "string",
        "required": true,
        "description": "Ranking type: daily, weekly, monthly",
        "default_value": null
      },
      ...
    ]
  },
  ...
}
```

**字段说明**:
- `name`: 命令名称
- `description`: 命令描述
- `parameters`: 参数列表,每个参数包含:
  - `name`: 参数名称
  - `type`: 参数类型(string, integer, boolean, array)
  - `required`: 是否必需
  - `description`: 参数描述
  - `default_value`: 默认值(null 表示无默认值)

**使用场景**:
- 第三方工具自动发现可用命令
- IDE 插件生成命令补全
- 文档生成工具提取 API 信息

### 静默模式 (--quiet)

`--quiet` 参数禁用所有控制台输出,仅保留文件日志:

```bash
pixiv-downloader --quiet download --type daily
```

**行为特性**:
- 禁用所有控制台输出(stdout 和 stderr)
- 保留文件日志(用于调试)
- 不保证 JSON 格式输出
- 适用于后台任务和批处理

**与 --json-output 的区别**:
- `--quiet`: 仅静默输出,不保证 JSON 格式
- `--json-output`: 确保输出为有效的 JSON 格式
- 第三方工具集成推荐使用 `--json-output` 而非 `--quiet`

### JSON 输出模式 (--json-output)

`--json-output` 参数确保所有输出都是有效的 JSON 格式:

```bash
pixiv-downloader --json-output download --type daily
```

**行为特性**:
- 所有输出(stdout 和 stderr)都是有效的 JSON 格式
- 错误信息也以 JSON 格式返回
- 适用于第三方工具集成和自动化流程
- 可靠的 JSON 解析保证

**适用场景**:
- 第三方工具集成
- CI/CD 流程集成
- 批量任务编排
- 结果解析和监控

**错误处理**:

在 `--json-output` 模式下,**所有**错误(包括参数验证错误)都以 JSON 格式输出:

```json
{
  "success": false,
  "error": "MissingParameter",
  "message": "Missing option '--type'."
}
```

**错误字段说明**:
- `success`: 布尔值,始终为 `false`
- `error`: 错误类型(Click 异常类名)
- `message`: 人类可读的错误详细信息

**常见错误类型**:
- `MissingParameter`: 缺少必需参数
- `BadParameter`: 参数值无效
- `NoSuchOption`: 未知选项
- `NoSuchCommand`: 未知命令
- `UsageError`: 命令用法错误

**错误处理示例 (Python)**:
```python
import subprocess
import json

result = subprocess.run(
    ["pixiv-downloader", "--json-output", "download", "http://example.com"],
    capture_output=True,
    text=True
)

if result.returncode != 0:
    # 解析错误响应
    error_data = json.loads(result.stdout)
    print(f"Error: {error_data['error']}")
    print(f"Message: {error_data['message']}")
```

**已知限制**:
- ✅ 所有核心命令 (version, download, status, config) 已支持 `--json-output` 参数
- ✅ 所有错误信息(包括 Click 参数验证错误)在 `--json-output` 模式下都以 JSON 格式输出
- ⚠️ config get/set 子命令尚未实现,当前 `config` 命令显示所有配置

## 示例代码

### 命令行调用示例

#### 1. 获取帮助信息

**获取 JSON 格式的命令元数据**:
```bash
pixiv-downloader --json-help | jq .
```

**获取特定命令的帮助**:
```bash
pixiv-downloader download --help
```

#### 2. 下载排行榜内容

**下载每日排行榜**:
```bash
pixiv-downloader download --type daily --date 2026-02-25
```

**下载每周排行榜(详细模式)**:
```bash
pixiv-downloader --verbose download --type weekly
```

**下载月度排行榜(静默模式)**:
```bash
pixiv-downloader --quiet download --type monthly --date 2026-01
```

**下载指定日期范围(结合 --json-output)**:
```bash
pixiv-downloader --json-output download --type daily --date 2026-02-20
```

#### 3. 查询和修改配置

**查询配置(静默模式)**:
```bash
pixiv-downloader --quiet config get download_dir
```

**修改配置(详细模式)**:
```bash
pixiv-downloader --verbose config set download_dir /path/to/downloads
```

#### 4. Token 管理

**检查登录状态**:
```bash
pixiv-downloader status
```

**刷新 token**:
```bash
pixiv-downloader refresh
```

**登录(首次使用)**:
```bash
pixiv-downloader login
```

**登出**:
```bash
pixiv-downloader logout
```

#### 5. 批量任务示例

**下载多个排行榜类型**:
```bash
#!/bin/bash
for type in daily weekly monthly; do
  pixiv-downloader --quiet download --type "$type"
done
```

**结合 cron 定时任务**:
```bash
# 每天凌晨 2 点下载每日排行榜
0 2 * * * /usr/local/bin/pixiv-downloader --quiet download --type daily
```

### Python 调用示例

#### 1. 基本调用模式

**使用 subprocess 调用 CLI**:
```python
import subprocess

# 基本调用
result = subprocess.run(
    ["pixiv-downloader", "download", "--type", "daily"],
    capture_output=True,
    text=True
)

if result.returncode == 0:
    print("下载成功")
    print(result.stdout)
else:
    print(f"下载失败,退出码: {result.returncode}")
    print(result.stderr)
```

#### 2. 解析 JSON 输出

**使用 --json-output 参数**:
```python
import subprocess
import json

# 调用 CLI 并获取 JSON 输出
result = subprocess.run(
    ["pixiv-downloader", "--json-output", "download", "--type", "daily"],
    capture_output=True,
    text=True
)

if result.returncode == 0:
    # 解析 JSON 输出
    try:
        output = json.loads(result.stdout)
        print(f"下载完成: {output}")
    except json.JSONDecodeError as e:
        print(f"JSON 解析错误: {e}")
else:
    print(f"命令执行失败,退出码: {result.returncode}")
    # 尝试解析错误信息(JSON 格式)
    try:
        error_info = json.loads(result.stderr)
        print(f"错误信息: {error_info}")
    except json.JSONDecodeError:
        print(f"原始错误输出: {result.stderr}")
```

#### 3. 获取命令元数据

**使用 --json-help 获取命令信息**:
```python
import subprocess
import json

# 获取所有命令的元数据
result = subprocess.run(
    ["pixiv-downloader", "--json-help"],
    capture_output=True,
    text=True
)

if result.returncode == 0:
    metadata = json.loads(result.stdout)

    # 遍历所有命令
    for command_name, command_info in metadata.items():
        print(f"命令: {command_name}")
        print(f"描述: {command_info['description']}")
        print(f"参数数量: {len(command_info['parameters'])}")
        print("---")

    # 检查特定命令是否存在
    if "download" in metadata:
        download_cmd = metadata["download"]
        print(f"download 命令参数:")
        for param in download_cmd["parameters"]:
            print(f"  - {param['name']}: {param['type']} ({'必需' if param['required'] else '可选'})")
```

#### 4. 错误处理示例

**完整的错误处理模式**:
```python
import subprocess
import json
from typing import Dict, Any, Optional

def run_pixiv_downloader(args: list[str]) -> tuple[int, Optional[Dict[str, Any]], Optional[str]]:
    """
    调用 pixiv-downloader CLI 并处理结果

    Args:
        args: 命令行参数列表(不包含程序名)

    Returns:
        (returncode, output_dict, error_message)
    """
    try:
        result = subprocess.run(
            ["pixiv-downloader", "--json-output"] + args,
            capture_output=True,
            text=True,
            timeout=300  # 5 分钟超时
        )

        if result.returncode == 0:
            # 成功,解析 JSON 输出
            try:
                output = json.loads(result.stdout) if result.stdout.strip() else {}
                return (result.returncode, output, None)
            except json.JSONDecodeError as e:
                return (result.returncode, None, f"JSON 解析错误: {e}")
        else:
            # 失败,尝试解析错误信息
            try:
                error_info = json.loads(result.stderr) if result.stderr.strip() else {}
                error_msg = error_info.get("error", result.stderr)
                return (result.returncode, None, error_msg)
            except json.JSONDecodeError:
                return (result.returncode, None, result.stderr)

    except subprocess.TimeoutExpired:
        return (-1, None, "命令执行超时")
    except FileNotFoundError:
        return (-1, None, "pixiv-downloader 命令未找到,请检查安装")
    except Exception as e:
        return (-1, None, f"未知错误: {e}")

# 使用示例
returncode, output, error = run_pixiv_downloader(["download", "--type", "daily"])

if returncode == 0:
    print(f"下载成功: {output}")
else:
    print(f"下载失败: {error} (退出码: {returncode})")
```

#### 5. 批量下载示例

**下载多个排行榜类型**:
```python
import subprocess
import time
from typing import List

def download_rankings(ranking_types: List[str], date: str = None) -> dict:
    """
    批量下载多个排行榜类型

    Args:
        ranking_types: 排行榜类型列表
        date: 日期字符串(可选)

    Returns:
        下载结果统计
    """
    results = {
        "success": [],
        "failed": []
    }

    for ranking_type in ranking_types:
        print(f"正在下载 {ranking_type} 排行榜...")

        args = ["pixiv-downloader", "--quiet", "download", "--type", ranking_type]
        if date:
            args.extend(["--date", date])

        result = subprocess.run(args, capture_output=True, text=True)

        if result.returncode == 0:
            results["success"].append(ranking_type)
            print(f"✓ {ranking_type} 排行榜下载完成")
        else:
            results["failed"].append({
                "type": ranking_type,
                "error": result.stderr,
                "returncode": result.returncode
            })
            print(f"✗ {ranking_type} 排行榜下载失败: {result.returncode}")

        # 避免触发速率限制
        time.sleep(2)

    return results

# 使用示例
ranking_types = ["daily", "weekly", "monthly"]
results = download_rankings(ranking_types)

print(f"\n下载完成:")
print(f"  成功: {len(results['success'])}")
print(f"  失败: {len(results['failed'])}")
```

## 退出码参考

gallery-dl-auto 使用标准化的错误码标识不同的错误类型,便于自动化流程判断执行状态。

### 退出码分类

#### 认证相关错误 (AUTH_*)

| 错误码 | 含义 | 使用场景 |
|--------|------|---------|
| AUTH_TOKEN_NOT_FOUND | Token 未找到 | 系统中不存在 refresh token,需要先登录 |
| AUTH_TOKEN_EXPIRED | Token 已过期 | Refresh token 已失效,需要重新登录 |
| AUTH_TOKEN_INVALID | Token 无效 | Token 格式错误或已被撤销 |
| AUTH_REFRESH_FAILED | Token 刷新失败 | 自动刷新 token 失败,需要重新登录 |

#### API 相关错误 (API_*)

| 错误码 | 含义 | 使用场景 |
|--------|------|---------|
| API_NETWORK_ERROR | 网络错误 | 网络连接失败或超时 |
| API_RATE_LIMIT | API 速率限制 | 触发 Pixiv API 速率限制,需要等待 |
| API_SERVER_ERROR | 服务器错误 | Pixiv API 返回 5xx 错误 |
| API_INVALID_RESPONSE | API 响应无效 | API 返回格式错误或数据损坏 |

#### 文件系统相关错误 (FILE_*)

| 错误码 | 含义 | 使用场景 |
|--------|------|---------|
| FILE_PERMISSION_ERROR | 文件权限错误 | 没有读写文件的权限 |
| FILE_DISK_FULL | 磁盘空间不足 | 磁盘空间不足,无法保存文件 |
| FILE_INVALID_PATH | 路径无效 | 文件路径格式错误或不存在 |

#### 下载相关错误 (DOWNLOAD_*)

| 错误码 | 含义 | 使用场景 |
|--------|------|---------|
| DOWNLOAD_FAILED | 下载失败 | 通用下载失败错误 |
| DOWNLOAD_TIMEOUT | 下载超时 | 下载文件超时 |
| DOWNLOAD_PERMISSION_DENIED | 下载权限拒绝 | 没有下载该作品的权限 |
| DOWNLOAD_DISK_FULL | 磁盘空间不足 | 下载过程中磁盘空间不足 |
| DOWNLOAD_FILE_EXISTS | 文件已存在 | 文件已存在且未启用覆盖 |
| DOWNLOAD_NETWORK_ERROR | 下载网络错误 | 下载过程中网络连接失败 |
| RATE_LIMIT_EXCEEDED | 速率限制超出 | 下载速率超出限制 |

#### 元数据相关错误 (METADATA_*)

| 错误码 | 含义 | 使用场景 |
|--------|------|---------|
| METADATA_FETCH_FAILED | 元数据获取失败 | 获取作品元数据失败 |

#### 参数相关错误 (INVALID_*)

| 错误码 | 含义 | 使用场景 |
|--------|------|---------|
| INVALID_ARGUMENT | 参数无效 | 命令行参数格式错误或不存在 |
| INVALID_DATE_FORMAT | 日期格式无效 | 日期参数格式错误 |

#### 内部错误 (INTERNAL_*)

| 错误码 | 含义 | 使用场景 |
|--------|------|---------|
| INTERNAL_ERROR | 内部错误 | 程序内部错误,通常是未处理的异常 |

### 退出码使用示例

**Bash 脚本中判断退出码**:
```bash
pixiv-downloader download --type daily

case $? in
  0)
    echo "下载成功"
    ;;
  1)
    echo "通用错误"
    ;;
  *)
    # 根据 stderr 输出判断具体错误类型
    echo "下载失败,退出码: $?"
    ;;
esac
```

**Python 中处理错误码**:
```python
import subprocess

result = subprocess.run(
    ["pixiv-downloader", "download", "--type", "daily"],
    capture_output=True,
    text=True
)

if result.returncode != 0:
    # 解析 stderr 获取错误码
    if "AUTH_TOKEN_NOT_FOUND" in result.stderr:
        print("需要先登录: pixiv-downloader login")
    elif "API_RATE_LIMIT" in result.stderr:
        print("触发速率限制,请稍后重试")
    else:
        print(f"下载失败: {result.stderr}")
```

### 注意事项

1. **退出码 0**: 表示命令执行成功
2. **退出码 1**: 表示通用错误(通常是 Click 框架返回)
3. **非零退出码**: 检查 stderr 输出获取具体错误码和错误信息
4. **JSON 输出模式**: 错误信息以 JSON 格式返回,包含 `error_code` 字段

## 最佳实践

### 参数选择建议

#### 输出控制参数选择

| 场景 | 推荐参数 | 说明 |
|------|---------|------|
| 交互式使用 | `--verbose` | 查看详细进度和日志信息 |
| 后台任务 | `--quiet` | 禁用控制台输出,保留文件日志 |
| 第三方工具集成 | `--json-output` | 确保 JSON 格式输出,便于解析 |
| CI/CD 流程 | `--json-output` | 可靠的 JSON 输出,便于结果判断 |
| 定时任务(cron) | `--quiet` | 避免不必要的输出,减少日志量 |

**推荐组合**:
```bash
# 第三方工具集成(推荐)
pixiv-downloader --json-output download --type daily

# 后台批处理(推荐)
pixiv-downloader --quiet download --type daily

# 交互式使用(推荐)
pixiv-downloader --verbose download --type daily
```

### 错误处理建议

#### 1. 完整的错误处理流程

**推荐模式**:
```python
import subprocess
import json

def safe_download(ranking_type: str, date: str = None) -> bool:
    """
    安全的下载函数,包含完整的错误处理

    Returns:
        True 表示成功, False 表示失败
    """
    args = ["pixiv-downloader", "--json-output", "download", "--type", ranking_type]
    if date:
        args.extend(["--date", date])

    try:
        result = subprocess.run(
            args,
            capture_output=True,
            text=True,
            timeout=300  # 设置超时
        )

        if result.returncode == 0:
            return True

        # 解析错误信息
        try:
            error = json.loads(result.stderr)
            error_code = error.get("error_code", "UNKNOWN")

            # 根据错误类型采取不同措施
            if error_code.startswith("AUTH_"):
                print("认证错误,需要重新登录")
                # 执行重新登录逻辑
            elif error_code.startswith("API_RATE_LIMIT"):
                print("触发速率限制,等待后重试")
                time.sleep(60)
                # 重试逻辑
            else:
                print(f"下载失败: {error_code}")

        except json.JSONDecodeError:
            print(f"未知错误: {result.stderr}")

        return False

    except subprocess.TimeoutExpired:
        print("命令执行超时")
        return False
    except Exception as e:
        print(f"异常: {e}")
        return False
```

#### 2. 重试机制

**推荐的重试策略**:
- 网络错误: 重试 3 次,每次间隔 5 秒
- 速率限制: 等待 60 秒后重试
- 认证错误: 不重试,提示用户重新登录
- 文件系统错误: 不重试,提示用户检查权限

```python
import time
from typing import Callable

def retry_on_error(
    func: Callable,
    max_retries: int = 3,
    delay: float = 5.0,
    errors_to_retry: list = ["API_NETWORK_ERROR", "API_SERVER_ERROR"]
) -> bool:
    """
    带重试的执行函数
    """
    for attempt in range(max_retries):
        success, error_code = func()

        if success:
            return True

        if error_code not in errors_to_retry:
            print(f"不可重试的错误: {error_code}")
            return False

        if attempt < max_retries - 1:
            print(f"重试 {attempt + 1}/{max_retries},等待 {delay} 秒...")
            time.sleep(delay)

    return False
```

### 性能优化建议

#### 1. 避免触发速率限制

**推荐的请求间隔**:
- 批量下载时,每次请求间隔至少 2 秒
- 下载多个排行榜类型时,类型之间间隔 5 秒
- 触发速率限制后,等待 60 秒再继续

```python
import time

def download_multiple_rankings(types: list):
    for i, ranking_type in enumerate(types):
        print(f"下载 {ranking_type} 排行榜...")

        # 下载排行榜
        subprocess.run(["pixiv-downloader", "download", "--type", ranking_type])

        # 类型之间间隔 5 秒
        if i < len(types) - 1:
            time.sleep(5)
```

#### 2. 使用静默模式减少 I/O

**推荐做法**:
- 后台任务使用 `--quiet` 减少控制台 I/O
- 文件日志自动记录所有操作(用于调试)
- 仅在需要时查看文件日志

```bash
# 后台任务(推荐)
pixiv-downloader --quiet download --type daily > /dev/null 2>&1

# 查看日志(需要时)
tail -f ~/.gallery-dl-auto/logs/app.log
```

#### 3. 并行下载(谨慎使用)

**注意事项**:
- 不建议并行下载同一排行榜类型(可能触发速率限制)
- 可以并行下载不同排行榜类型,但需要控制并发数
- 推荐使用队列系统而非并行进程

```python
# 不推荐:并行下载同一类型
# 可能触发速率限制

# 推荐:串行下载,控制间隔
for ranking_type in ["daily", "weekly", "monthly"]:
    subprocess.run(["pixiv-downloader", "download", "--type", ranking_type])
    time.sleep(5)
```

### 集成测试建议

#### 1. 验证 CLI 可用性

**在集成前检查**:
```python
import subprocess

# 检查命令是否存在
result = subprocess.run(
    ["which", "pixiv-downloader"],
    capture_output=True
)

if result.returncode != 0:
    raise RuntimeError("pixiv-downloader 未安装")

# 检查版本
result = subprocess.run(
    ["pixiv-downloader", "version"],
    capture_output=True,
    text=True
)

print(f"CLI 版本: {result.stdout.strip()}")
```

#### 2. 测试错误处理

**测试各种错误场景**:
```python
def test_error_handling():
    # 测试认证错误
    result = subprocess.run(
        ["pixiv-downloader", "download", "--type", "daily"],
        capture_output=True,
        text=True
    )

    if "AUTH_TOKEN_NOT_FOUND" in result.stderr:
        print("✓ 认证错误处理正常")

    # 测试参数错误
    result = subprocess.run(
        ["pixiv-downloader", "download", "--type", "invalid_type"],
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        print("✓ 参数错误处理正常")
```

### 文档和注释

#### 1. 记录集成代码

**推荐在代码中添加注释**:
```python
# 集成 gallery-dl-auto CLI
# 文档: ./INTEGRATION.md
# CLI API: pixiv-downloader --json-help

def download_pixiv_ranking(ranking_type: str):
    """
    下载 Pixiv 排行榜

    Args:
        ranking_type: 排行榜类型 (daily, weekly, monthly)

    Returns:
        True 表示成功, False 表示失败

    References:
        - CLI 帮助: pixiv-downloader download --help
        - 集成文档: ./INTEGRATION.md
    """
    ...
```

#### 2. 更新 README

**在项目 README 中添加集成说明**:
```markdown
## 集成 gallery-dl-auto

本项目使用 gallery-dl-auto CLI 工具下载 Pixiv 排行榜内容。

- [集成文档](./INTEGRATION.md)
- [CLI API 参考](./INTEGRATION.md#json-api)
- [示例代码](./INTEGRATION.md#示例代码)
```
