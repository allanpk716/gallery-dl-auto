---
phase: 10-api-validation
plan: 02-GAP01
type: execute
wave: 4
depends_on: ["10-01", "10-01-GAP01", "10-01-GAP02"]
files_modified:
  - src/gallery_dl_auo/auth/pixiv_auth.py
  - src/gallery_dl_auo/cli/status_cmd.py
  - src/gallery_dl_auo/auth/token_storage.py
autonomous: true
requirements: [VAL-01]
plan_type: gap_closure
parent_plan: 10-01
gap_summary: status 命令 username 字段在 token 有效时仍为 null,产生歧义
verification_file: .planning/phases/10-api-validation/10-UAT.md
must_haves:
  truths:
    - status 命令在 --json-output 模式下,当 token 有效时提供明确的 username 信息或移除该字段
    - 用户可以从 token 验证响应中获取 Pixiv 用户信息(name, account, id)
    - 用户信息被正确存储在 token 文件中,并在后续 status 查询时显示
    - 旧的 token 文件(无 user 字段)被向后兼容处理,username 显示为 null 但不产生歧义
  artifacts:
    - src/gallery_dl_auo/auth/pixiv_auth.py (validate_refresh_token 返回 user 字段)
    - src/gallery_dl_auo/auth/token_storage.py (save_token 存储 user 字段)
    - src/gallery_dl_auo/cli/status_cmd.py (使用存储的 user 字段)
  key_links:
    - Pixiv OAuth API 响应包含 user 字段,需在 validate_refresh_token 中提取
    - TokenStorage.save_token 需接受 user 参数并存储到加密文件
    - status_cmd 需从 token_data 读取 user 字段并显示
---

# Gap Closure Plan: 修复 status 命令 username 字段歧义

**Created:** 2026-02-27
**Type:** Gap Closure (Feature Enhancement)
**Parent Plan:** 10-01 (JSON 输出格式验证)
**Priority:** HIGH - UAT 测试失败,产生用户歧义

## Gap Analysis

### Problem
在 UAT 测试中发现,status 命令的 JSON 输出在 `token_valid: true` 时 `username` 仍为 `null`,产生歧义:

```json
{
  "logged_in": true,
  "token_valid": true,
  "username": null  // 歧义: token 有效但 username 为 null
}
```

用户反馈:"我看到 username 是null,当 token_valid 为 true 时 username 仍为 null 产生歧义。应该明确:如果 token 有效是否能获取 username,如果不能获取则应移除该字段避免歧义"

### Root Cause
根据 debug session 诊断:

1. **用户信息未被提取**:
   - Pixiv OAuth API 响应包含 `user` 字段 (name, account, id)
   - `validate_refresh_token()` 方法(第 412-470 行)仅提取 token 字段,忽略 `user` 字段

2. **用户信息未被存储**:
   - `TokenStorage.save_token()` 方法(第 60-90 行)仅保存 `refresh_token` 和 `access_token`
   - 未提供 `user` 字段的存储能力

3. **status 命令硬编码 username**:
   - `status_cmd.py` 第 100 行硬编码 `"username": None`
   - 未从 token 数据中读取用户信息

### Impact
- **UAT 失败**: Test 2 (status 命令 JSON 输出) 失败
- **用户体验差**: 无法知道当前登录的是哪个 Pixiv 账号
- **文档不一致**: INTEGRATION.md 承诺提供用户信息,但实际未提供

## Goal

实现完整的用户信息提取、存储和显示流程,消除 `username: null` 的歧义。

**Success Criteria:**
1. ✅ `validate_refresh_token()` 返回 `user` 字段(包含 name, account, id)
2. ✅ `TokenStorage.save_token()` 接受并存储 `user` 字段
3. ✅ status 命令从 token 数据读取并显示用户信息
4. ✅ 旧的 token 文件(无 user 字段)向后兼容,username 显示为 null 但添加说明
5. ✅ UAT Test 2 通过

## Tasks

### Task 1: 修改 validate_refresh_token 提取用户信息

**What:** 从 Pixiv OAuth API 响应中提取 `user` 字段并返回

**Files:** `src/gallery_dl_auo/auth/pixiv_auth.py`

**Implementation:**

```xml
<task type="auto">
<name>Task 1: 提取 Pixiv OAuth API 响应中的用户信息</name>
<files>src/gallery_dl_auo/auth/pixiv_auth.py</files>
<action>
在 validate_refresh_token 方法中,从成功的 API 响应中提取 user 字段。

**修改位置:** 第 445-453 行 (status_code == 200 分支)

**修改内容:**
1. 从 response.json() 中提取 user 字段
2. 在返回的字典中添加 user 字段
3. 在失败分支也添加 user: None 保持结构一致

**代码修改:**
```python
# Line 445-453: 成功响应处理
if response.status_code == 200:
    data = response.json()
    return {
        "valid": True,
        "access_token": data["access_token"],
        "refresh_token": data["refresh_token"],
        "expires_in": data.get("expires_in", 3600),
        "user": data.get("user"),  # 新增: 提取用户信息
        "error": None,
    }
```

```python
# Line 454-462: 失败响应处理
else:
    error_data = response.json()
    return {
        "valid": False,
        "access_token": None,
        "refresh_token": None,
        "expires_in": None,
        "user": None,  # 新增: 失败时无用户信息
        "error": error_data.get("error", "Unknown error"),
    }
```

```python
# Line 463-470: 异常处理
except Exception as e:
    return {
        "valid": False,
        "access_token": None,
        "refresh_token": None,
        "expires_in": None,
        "user": None,  # 新增: 异常时无用户信息
        "error": str(e),
    }
```

**注意:** Pixiv OAuth API 响应结构:
```json
{
  "access_token": "...",
  "refresh_token": "...",
  "expires_in": 3600,
  "user": {
    "id": "123456",
    "name": "用户名",
    "account": "user_account"
  }
}
```
</action>
<verify>
```bash
# 验证代码修改
python -c "from gallery_dl_auo.auth.pixiv_auth import PixivOAuth; import inspect; sig = inspect.signature(PixivOAuth.validate_refresh_token); print('Method signature:', sig)"
```
</verify>
<done>
validate_refresh_token 返回字典包含 user 字段,成功时包含用户信息(name/account/id),失败时为 None
</done>
</task>
```

### Task 2: 修改 TokenStorage 支持存储用户信息

**What:** 扩展 `save_token` 方法接受并存储 `user` 字段

**Files:** `src/gallery_dl_auo/auth/token_storage.py`

**Implementation:**

```xml
<task type="auto">
<name>Task 2: 扩展 TokenStorage 存储用户信息</name>
<files>src/gallery_dl_auo/auth/token_storage.py</files>
<action>
修改 TokenStorage.save_token 方法,支持存储可选的 user 字段。

**修改位置:** 第 60-90 行

**修改内容:**
1. 修改方法签名,添加 user 参数
2. 在构造 data 字典时包含 user 字段(如果提供)
3. 更新 docstring 说明新参数

**代码修改:**
```python
# Line 60-90: 修改 save_token 方法
def save_token(
    self,
    refresh_token: str,
    access_token: Optional[str] = None,
    user: Optional[dict] = None  # 新增: 用户信息字段
) -> None:
    """加密并保存 token 到文件

    将 token 数据加密后写入文件,并在 Unix 系统上设置文件权限为 600。

    Args:
        refresh_token: refresh token 字符串
        access_token: 可选的 access token 字符串
        user: 可选的用户信息字典,包含 id/name/account 字段
    """
    # 构造数据字典
    data = {"refresh_token": refresh_token}
    if access_token:
        data["access_token"] = access_token
    if user:  # 新增: 包含用户信息
        data["user"] = user

    # 加密
    encrypted = self.fernet.encrypt(json.dumps(data).encode("utf-8"))

    # 确保目录存在
    self.storage_path.parent.mkdir(parents=True, exist_ok=True)

    # 写入文件
    self.storage_path.write_bytes(encrypted)

    # 设置文件权限 (Unix: 600, Windows: 跳过)
    if platform.system() != "Windows":
        try:
            os.chmod(self.storage_path, 0o600)
        except OSError as e:
            logger.warning(f"Failed to set file permissions: {e}")
```
</action>
<verify>
```bash
# 验证方法签名
python -c "from gallery_dl_auo.auth.token_storage import TokenStorage; import inspect; sig = inspect.signature(TokenStorage.save_token); print('Method signature:', sig)"
```
</verify>
<done>
TokenStorage.save_token 接受 user 参数,存储到加密文件中,load_token 返回的字典包含 user 字段
</done>
</task>
```

### Task 3: 修改 status 命令显示用户信息

**What:** 从 token 数据中读取用户信息并显示,处理向后兼容

**Files:** `src/gallery_dl_auo/cli/status_cmd.py`

**Implementation:**

```xml
<task type="auto">
<name>Task 3: status 命令显示用户信息并处理向后兼容</name>
<files>src/gallery_dl_auo/cli/status_cmd.py</files>
<action>
修改 status 命令,从 token_data 读取用户信息并显示。

**修改位置 1:** 第 110-114 行 (token 刷新后保存用户信息)

**修改内容:**
```python
# Line 110-114: 保存 token 时包含用户信息
if result["valid"] and result["refresh_token"]:
    storage.save_token(
        refresh_token=result["refresh_token"],
        access_token=result.get("access_token"),
        user=result.get("user"),  # 新增: 保存用户信息
    )
```

**修改位置 2:** 第 93-107 行 (JSON 输出部分,重构整个逻辑)

**修改内容:**
```python
# Line 93-107: 重构 JSON 输出逻辑,使用存储的用户信息
result = PixivOAuth.validate_refresh_token(refresh_token)

# JSON output mode
if ctx.obj.get("output_mode") == "json":
    # 尝试从 token_data 中获取用户信息(向后兼容)
    stored_user = token_data.get("user")
    latest_user = result.get("user")

    # 优先使用最新的用户信息,否则使用存储的
    user_info = latest_user or stored_user

    status_data = {
        "logged_in": result["valid"],
        "token_valid": result["valid"],
    }

    # 添加用户信息(如果可用)
    if user_info:
        status_data["username"] = user_info.get("name")
        status_data["user_account"] = user_info.get("account")
        status_data["user_id"] = user_info.get("id")
    else:
        # 向后兼容: 旧 token 文件无用户信息
        status_data["username"] = None
        status_data["user_account"] = None
        status_data["user_id"] = None
        status_data["user_info_note"] = "User info not available. Re-login to capture user details."

    if not result["valid"]:
        status_data["error"] = result.get("error", "Unknown")
        status_data["suggestion"] = "Run 'pixiv-downloader login --force' to re-login"

    click.echo(json.dumps(status_data, ensure_ascii=False))

    # Still refresh token if valid (silently)
    if result["valid"] and result["refresh_token"]:
        storage.save_token(
            refresh_token=result["refresh_token"],
            access_token=result.get("access_token"),
            user=result.get("user"),
        )
```

**注意:**
- 使用 `token_data.get("user")` 处理旧 token 文件(无 user 字段)
- 提供详细的用户信息字段: username (name), user_account, user_id
- 向后兼容时添加说明字段 user_info_note
</action>
<verify>
```bash
# 测试 status 命令 JSON 输出
pixiv-downloader --json-output status

# 预期输出:
# - token 有效且有用户信息: {"logged_in": true, "token_valid": true, "username": "用户名", "user_account": "...", "user_id": "..."}
# - token 有效但无用户信息(旧文件): {"logged_in": true, "token_valid": true, "username": null, ..., "user_info_note": "..."}
```
</verify>
<done>
status 命令在 token 有效时显示用户信息,旧 token 文件向后兼容并显示说明
</done>
</task>
```

### Task 4: 修改 login/refresh 命令保存用户信息

**What:** 确保登录和刷新命令保存用户信息

**Files:** `src/gallery_dl_auo/cli/login_cmd.py`, `src/gallery_dl_auo/cli/refresh_cmd.py`

**Implementation:**

```xml
<task type="auto">
<name>Task 4: 登录和刷新命令保存用户信息</name>
<files>src/gallery_dl_auo/cli/login_cmd.py, src/gallery_dl_auo/cli/refresh_cmd.py</files>
<action>
在 login 和 refresh 命令中,调用 storage.save_token 时包含用户信息。

**login_cmd.py 修改:**
找到调用 `storage.save_token()` 的位置,添加 user 参数。

**refresh_cmd.py 修改:**
找到调用 `storage.save_token()` 的位置,添加 user 参数。

**注意:** 这些命令调用 PixivOAuth 的 login() 或 refresh_tokens() 方法,
这些方法返回的 token_data 应包含 user 字段(如果 API 响应中有)。

如果 login() 和 refresh_tokens() 方法未返回 user 字段,需要同步修改这些方法。
</action>
<verify>
```bash
# 验证登录流程
pixiv-downloader login --force

# 验证刷新流程
pixiv-downloader refresh

# 检查 token 文件内容(需要解密)
python -c "from gallery_dl_auo.auth.token_storage import get_default_token_storage; import json; storage = get_default_token_storage(); data = storage.load_token(); print(json.dumps(data, indent=2, ensure_ascii=False))"
```
</verify>
<done>
login 和 refresh 命令保存 token 时包含用户信息,token 文件包含 user 字段
</done>
</task>
```

### Task 5: 验证完整流程和 UAT 测试

**What:** 端到端验证用户信息流程,运行 UAT 测试

**Implementation:**

```xml
<task type="auto">
<name>Task 5: 端到端验证和 UAT 测试</name>
<files></files>
<action>
执行完整的验证流程,确保所有改动协同工作。

**验证步骤:**
1. 清除现有 token: `pixiv-downloader logout`
2. 重新登录: `pixiv-downloader login`
3. 验证 token 文件包含 user 字段
4. 验证 status 命令显示用户信息
5. 测试向后兼容性(使用旧 token 文件)
6. 运行 UAT Test 2

**测试命令:**
```bash
# 1. 清除 token
pixiv-downloader logout

# 2. 重新登录
pixiv-downloader login

# 3. 验证 token 文件包含 user 字段
python -c "from gallery_dl_auo.auth.token_storage import get_default_token_storage; import json; storage = get_default_token_storage(); data = storage.load_token(); print('user' in data, data.get('user'))"

# 4. 验证 status 命令
pixiv-downloader --json-output status

# 预期输出包含: "username": "实际用户名", "user_account": "...", "user_id": "..."

# 5. 测试向后兼容性(模拟旧 token 文件)
python -c "
from gallery_dl_auo.auth.token_storage import get_default_token_storage
import json

storage = get_default_token_storage()
data = storage.load_token()
if 'user' in data:
    del data['user']  # 移除 user 字段模拟旧文件
    print('Simulated old token file (no user field)')
"

# 6. 再次验证 status 命令(向后兼容)
pixiv-downloader --json-output status

# 预期输出包含: "username": null, "user_info_note": "User info not available..."

# 7. 恢复用户信息(刷新 token)
pixiv-downloader refresh

# 8. 最终验证
pixiv-downloader --json-output status
```
</action>
<verify>
```bash
# 运行 UAT Test 2 相关验证
pixiv-downloader --json-output status | python -m json.tool

# 预期:
# - token 有效时,username 字段有实际值或 null(向后兼容)
# - 如果 null,必须有 user_info_note 说明原因
# - 无歧义: 用户能明确知道为什么 username 为 null
```
</verify>
<done>
完整流程验证通过,UAT Test 2 (status 命令 JSON 输出) 通过
</done>
</task>
```

## Must-Haves (Gap Closure Verification)

完成此 gap closure 后,以下条件必须为 TRUE:

| Must-Have | Verification Method | Success Criteria |
| --- | --- | --- |
| validate_refresh_token 返回 user 字段 | `python -c "from gallery_dl_auo.auth.pixiv_auth import PixivOAuth; ..."` | 返回字典包含 user 字段 |
| TokenStorage.save_token 接受 user 参数 | `python -c "from gallery_dl_auo.auth.token_storage import TokenStorage; ..."` | 方法签名包含 user 参数 |
| status 命令显示用户信息 | `pixiv-downloader --json-output status` | 输出包含 username/user_account/user_id |
| 向后兼容处理 | 使用旧 token 文件测试 | username 为 null 但有 user_info_note |
| UAT Test 2 通过 | UAT 测试 | status 命令 JSON 输出无歧义 |

## Dependencies

**Depends on:**
- 10-01: JSON 输出格式验证 (已完成)
- 10-01-GAP01: 测试框架修复 (已完成)
- 10-01-GAP02: status/config JSON 输出实现 (已完成)

**Blocks:**
- Phase 10 UAT 完成
- VAL-01 需求完全满足

## Risks

### Risk 1: Pixiv OAuth API 响应可能不包含 user 字段

**Impact:** 无法提取用户信息

**Mitigation:**
1. 使用 `data.get("user")` 安全访问,避免 KeyError
2. 如果 API 不提供 user 字段,username 保持 null 但添加说明
3. 考虑使用 access token 调用用户信息 API 获取

**Probability:** LOW - OAuth 标准响应通常包含用户信息

### Risk 2: 旧 token 文件向后兼容性

**Impact:** 用户需要重新登录才能看到用户信息

**Mitigation:**
1. 使用 `token_data.get("user")` 处理缺失字段
2. 添加 user_info_note 说明原因
3. 刷新 token 时自动捕获用户信息

**Probability:** HIGH - 现有用户都有旧格式 token 文件

### Risk 3: login/refresh 方法可能未返回 user 字段

**Impact:** 无法在登录/刷新时保存用户信息

**Mitigation:**
1. 检查 _exchange_token 和 refresh_tokens 方法返回值
2. 如果未返回 user 字段,需要修改这些方法
3. 确保所有 token 获取路径都提取用户信息

**Probability:** MEDIUM - 需要验证代码实现

## Files Modified Summary

```
src/gallery_dl_auo/auth/pixiv_auth.py
├── Line 447-453: validate_refresh_token 成功响应添加 user 字段
├── Line 456-462: 失败响应添加 user: None
└── Line 465-470: 异常响应添加 user: None

src/gallery_dl_auo/auth/token_storage.py
├── Line 60: save_token 方法签名添加 user 参数
├── Line 72-74: data 字典包含 user 字段
└── Docstring 更新

src/gallery_dl_auo/cli/status_cmd.py
├── Line 96-130: 重构 JSON 输出逻辑,显示用户信息
├── Line 110-114: 保存 token 时包含 user 字段
└── 向后兼容处理(user_info_note)

src/gallery_dl_auo/cli/login_cmd.py
└── save_token 调用添加 user 参数

src/gallery_dl_auo/cli/refresh_cmd.py
└── save_token 调用添加 user 参数
```

## Verification Commands

```bash
# 1. 验证方法签名
python -c "from gallery_dl_auo.auth.pixiv_auth import PixivOAuth; import inspect; print(inspect.signature(PixivOAuth.validate_refresh_token))"
python -c "from gallery_dl_auo.auth.token_storage import TokenStorage; import inspect; print(inspect.signature(TokenStorage.save_token))"

# 2. 测试完整流程
pixiv-downloader logout
pixiv-downloader login
pixiv-downloader --json-output status

# 3. 验证 token 文件
python -c "from gallery_dl_auo.auth.token_storage import get_default_token_storage; import json; storage = get_default_token_storage(); data = storage.load_token(); print(json.dumps(data, indent=2, ensure_ascii=False))"

# 4. 测试向后兼容
pixiv-downloader --json-output status | python -m json.tool

# 5. 验证 JSON 输出格式
pixiv-downloader --json-output status | python -c "import json, sys; data = json.load(sys.stdin); print('username:', data.get('username')); print('user_account:', data.get('user_account')); print('user_id:', data.get('user_id'))"
```

## Success Criteria

- [ ] validate_refresh_token 返回 user 字段
- [ ] TokenStorage.save_token 接受 user 参数
- [ ] status 命令显示用户信息(username, user_account, user_id)
- [ ] 旧 token 文件向后兼容,显示 user_info_note
- [ ] login/refresh 命令保存用户信息
- [ ] UAT Test 2 通过
- [ ] 无 username 歧义

## Execution Notes

**给执行者的提示:**
1. **优先级**: 先修改 pixiv_auth.py 和 token_storage.py,再修改 status_cmd.py
2. **向后兼容**: 使用 `dict.get()` 方法处理缺失字段,避免 KeyError
3. **用户信息结构**: Pixiv user 对象包含 id (字符串), name (显示名), account (账号名)
4. **测试策略**: 每完成一个文件修改,立即测试相关功能
5. **login/refresh 修改**: 可能需要同步修改这些命令,确保完整流程
6. **JSON 输出格式**: 确保输出符合 INTEGRATION.md 的规范

**预计时间:** ~20 分钟
- pixiv_auth.py 修改: 3 分钟
- token_storage.py 修改: 3 分钟
- status_cmd.py 修改: 5 分钟
- login/refresh_cmd.py 修改: 5 分钟
- 验证和测试: 4 分钟

---

**Plan Type:** Gap Closure (Feature Enhancement)
**Wave:** 4
**Estimated Duration:** ~20 minutes
**Executor Notes:** 实现用户信息提取和显示,注意向后兼容性,确保完整流程测试
