# Phase 1: 项目基础 - Context

**Gathered:** 2026-02-24
**Status:** Ready for planning

<domain>
## Phase Boundary

搭建项目基础设施,包括项目结构、配置管理、CLI 框架和核心依赖。这个阶段交付一个能够运行的 CLI 程序,可以显示帮助信息并加载配置文件。核心目标是建立稳定的项目基础,为后续的 token 自动化、下载功能等提供支撑。

</domain>

<decisions>
## Implementation Decisions

### CLI 框架与入口
- 使用 **Click** 作为 CLI 框架,支持子命令、自动补全、彩色输出
- 采用**子命令模式**,主命令为 `pixiv-downloader`,支持以下子命令:
  - `download` - 主要功能,未来排行榜下载命令
  - `config` - 配置管理功能,查看/编辑配置
  - `version` - 版本查看功能
  - `doctor` - 调试和诊断功能,测试配置
- 安装后用户可直接运行 `pixiv-downloader` 命令,配置 pyproject.toml 的 `[project.scripts]`
- 使用 **rich** 库处理日志输出和用户提示,支持彩色和格式化

### 项目结构
- 采用 **src 布局**:
  ```
  gallery-dl-auto/
  ├── src/
  │   └── gallery_dl_auo/     # 主包
  │       ├── __init__.py
  │       ├── cli/             # CLI 相关代码
  │       ├── config/          # 配置管理
  │       ├── core/            # 核心功能(未来)
  │       └── utils/           # 工具函数
  ├── tests/                   # 测试代码
  ├── docs/                    # 文档
  ├── pyproject.toml
  └── README.md
  ```
- 源码目录名为 `gallery_dl_auo`,与仓库名一致,符合 Python 包命名规范

### 配置管理
- 使用 **hydra + OmegaConf** 管理配置
- 配置文件位于**当前目录**(便于开发和测试),文件名为 `config.yaml`
- 配置优先级:**命令行参数 > 环境变量 > 配置文件 > 默认值**
- **启动时严格验证**所有配置,错误时明确提示
- 代码中定义默认值,用户无需配置即可使用
- Phase 1 定义未来需要的配置项:
  - `save_path` - 图片保存路径
  - `concurrent_downloads` - 并发下载数
  - `request_interval` - 请求间隔(秒)
  - `log_level` - 日志级别

### 依赖管理
- 使用 **pyproject.toml** 管理依赖(现代 Python 标准)
- 最低支持 **Python 3.10**
- 核心依赖:
  - `click` - CLI 框架
  - `hydra-core` - 配置管理
  - `omegaconf` - 配置解析
  - `rich` - 日志和输出格式化

### 测试策略
- 使用 **pytest** 作为测试框架
- 测试代码放在项目根目录的 **tests/** 目录
- Phase 1 建立基础测试框架,为后续阶段做准备
- 测试内容:
  - CLI 入口测试
  - 配置加载和验证测试
  - 默认值测试

### 代码质量
- 建立完整的代码质量工具链:
  - **black** - 代码格式化
  - **ruff** - 快速 linting
  - **mypy** - 静态类型检查
- 配置 **pre-commit** 钩子,自动运行质量检查

### 文档策略
- Phase 1 建立完整文档体系:
  - **README.md** - 项目介绍、安装、快速开始
  - **CLI --help** - 命令行帮助信息
  - **docstrings** - 代码文档字符串
- 文档内容:
  - 项目简介和核心价值
  - 安装指南
  - 快速开始示例
  - CLI 命令说明

### 错误处理
- 使用 **rich** 的结构化错误输出,带颜色和格式化
- 错误信息包含:
  - 错误类型
  - 错误描述
  - 建议的解决方案
- 友好的用户提示,避免技术术语

### 日志策略
- 默认日志级别为 **INFO**,可通过 `--verbose` 或 `--quiet` 调整
- 日志输出使用 **rich** 格式化,支持彩色和进度条
- 日志级别:
  - `DEBUG` - 调试信息(--verbose)
  - `INFO` - 一般信息(默认)
  - `WARNING` - 警告信息
  - `ERROR` - 错误信息
  - `CRITICAL` - 严重错误

### Claude's Discretion
- 确切的目录结构细节(如是否需要 `exceptions.py` 文件)
- 配置验证的具体规则和错误提示文案
- pre-commit 钩子的具体配置选项
- 测试覆盖率目标(Phase 1 可设置为较低目标,如 50%)
- 文档的详细内容组织

</decisions>

<specifics>
## Specific Ideas

- CLI 命令名 `pixiv-downloader` - 比 `pixiv-dl` 更明确说明用途,虽然较长但描述性强
- 子命令模式设计 - 参考了 git、docker 等工具的设计,清晰易扩展
- 配置文件在当前目录 - 方便开发和测试,用户也容易找到和修改
- 启动时严格验证配置 - 早期发现问题,避免运行时错误
- 完整的工具链和文档 - 重视代码质量和用户体验,为长期维护做准备

</specifics>

<deferred>
## Deferred Ideas

None - 讨论严格保持在 Phase 1 范围内,未涉及未来阶段的功能

</deferred>

---

*Phase: 01-项目基础*
*Context gathered: 2026-02-24*
