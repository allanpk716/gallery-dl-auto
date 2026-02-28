# Pixiv 排行榜下载器 (gallery-dl-auto)

[![Python 3.10+](https://img.shields.io/badge/python-3.10+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

自动化获取 pixiv refresh token 并下载排行榜内容 — 用户首次手动登录后,程序自动捕获、存储和更新 refresh token,无需手动从浏览器开发者工具中复制,实现真正的自动化下载流程。

## 核心特性

- ✨ **自动化 Token 管理**: 首次登录后自动捕获和刷新 token
- 📥 **排行榜下载**: 支持日榜、周榜、月榜
- 📊 **完整元数据**: 获取作品标题、作者、标签、统计数据
- 🎯 **CLI 优先**: 命令行工具,易于集成和自动化
- 📦 **JSON 输出**: 结构化输出,支持程序化调用
- 🔧 **灵活配置**: YAML 配置文件 + CLI 参数覆盖

## 快速开始

### 安装

```bash
# 克隆仓库
git clone https://github.com/yourusername/gallery-dl-auto.git
cd gallery-dl-auto

# 安装依赖
pip install -e .
```

### 基本使用

```bash
# 查看帮助
pixiv-downloader --help

# 查看版本
pixiv-downloader version

# 查看当前配置
pixiv-downloader config

# 诊断环境
pixiv-downloader doctor
```

## 配置

程序从当前目录的 `config.yaml` 加载配置。首次运行会使用默认配置。

### 配置文件示例

```yaml
# 下载配置
save_path: ./downloads        # 图片保存路径
concurrent_downloads: 3       # 并发下载数
request_interval: 1.0         # 请求间隔(秒)

# 日志配置
log_level: INFO               # 日志级别: DEBUG, INFO, WARNING, ERROR, CRITICAL

# 网络配置
api_timeout: 30               # API 超时(秒)
max_retries: 3                # 重试次数
```

### 配置优先级

命令行参数 > 环境变量 > 配置文件 > 默认值

## 开发

### 安装开发依赖

```bash
pip install -e ".[dev]"
```

### 运行测试

```bash
pytest tests/ -v
```

### 代码质量检查

```bash
# 格式化代码
black src/ tests/

# Lint 检查
ruff check src/ tests/

# 类型检查
mypy src/
```

### Pre-commit 钩子

```bash
# 安装 pre-commit 钩子
pre-commit install

# 手动运行所有检查
pre-commit run --all-files
```

## 路线图

- [x] Phase 1: 项目基础 ✅
- [ ] Phase 2: Token 自动化
- [ ] Phase 3: 排行榜基础下载
- [ ] Phase 4: 内容与元数据
- [ ] Phase 5: JSON 输出
- [ ] Phase 6: 多排行榜支持
- [ ] Phase 7: 错误处理与健壮性
- [ ] Phase 8: 用户体验优化

## 许可证

[MIT License](LICENSE)

## 贡献

欢迎贡献!请查看 [CONTRIBUTING.md](CONTRIBUTING.md) 了解详情。

## 致谢

- [Click](https://click.palletsprojects.com/) - CLI 框架
- [Hydra](https://hydra.cc/) - 配置管理
- [Rich](https://github.com/Textualize/rich) - 终端美化
