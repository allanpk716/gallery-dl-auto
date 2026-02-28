# Phase 2: Token 自动化 - Context

**Gathered:** 2026-02-24
**Status:** Ready for planning

<domain>
## Phase Boundary

实现完全自动化的 refresh token 管理，包括首次登录自动捕获、安全存储、有效性验证和刷新功能。用户首次手动登录后，程序自动捕获和存储 token，后续使用支持手动刷新和状态查询。Token 刷新和下载功能是独立的命令。

此阶段专注于 token 的获取、存储、验证和刷新。下载排行榜内容属于 Phase 3。

</domain>

<decisions>
## Implementation Decisions

### 登录引导体验
- 自动打开系统默认浏览器访问 Pixiv 登录页面，用户无需手动复制 URL
- 无超时限制，程序持续等待用户完成登录（包括验证码等步骤）
- 显示友好的登录指导信息，包括操作步骤和注意事项
- 程序自动检测登录成功并捕获 refresh token，用户无需手动操作
- 使用系统默认浏览器（非无痕模式）
- 如果用户关闭浏览器或登录失败，引导用户重新运行程序
- 单账号模式，每次只保存一个账号的 token

### 存储方案选择
- 使用加密配置文件存储 token，存储在用户目录下的标准位置（~/.gallery-dl-auto/credentials.enc）
- 使用 Python 加密库（如 cryptography 库的 Fernet）进行加密，跨平台一致
- 加密密钥基于机器唯一信息（主机名、用户名等）自动生成，用户无需设置密码
- 设置严格的文件权限（仅当前用户可读写：600/400），防止其他用户访问
- 仅保存最新的 token，不保留历史版本

### 刷新策略与错误
- 手动触发刷新：使用 `--login` 参数主动触发重新登录（会自动刷新 token）
- 每次程序启动时验证 token 有效性
- Token 刷新过程完全无感知，静默完成
- 如果 token 刷新失败，提示用户重新登录
- 不在后台自动刷新（因为工具不是常驻服务）

### Token 生命周期
- Token 失效时（如用户在 Pixiv 网站登出），程序报错退出
- 显示详细的错误信息和解决步骤，帮助用户理解问题
- 支持 `--logout` 命令主动清除 token（用于切换账号等场景）
- 支持 `--status` 命令查询 token 状态（有效期、是否有效等）

### Claude's Discretion
- 登录指导信息的具体措辞和格式
- 加密密钥生成的具体算法（基于机器信息的哈希方式）
- Token 有效性验证的具体实现方式
- 错误信息的详细程度和格式
- 状态查询输出的格式（文本表格、JSON 等）

</decisions>

<specifics>
## Specific Ideas

- 用户希望工具简单易用，首次登录后后续使用完全自动化
- 工具不是常驻后台服务，而是按需运行的命令行工具，因此刷新策略需要适应这种使用模式
- 用户希望能够主动管理 token（查询状态、主动刷新、清除重新登录）
- 安全性要求：token 加密存储，文件权限严格控制

</specifics>

<deferred>
## Deferred Ideas

None — 讨论保持在阶段范围内

</deferred>

---

*Phase: 02-token-automation*
*Context gathered: 2026-02-24*
