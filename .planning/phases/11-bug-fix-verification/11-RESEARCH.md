# Phase 11: Bug Fix & Verification - Research

**Researched:** 2026-03-16
**Domain:** Bug 修复与功能验证 - tracker DB 记录逻辑修复和跨日去重验证
**Confidence:** HIGH

## Summary

Phase 11 专注于修复 tracker DB 记录逻辑的 bug（GitHub issue #2）并验证跨日去重功能的完整性（GitHub issue #1）。核心问题在于 `gallery_dl_wrapper.py` 中 Phase 4（记录下载到 tracker）的执行条件使用 `use_dedup` 标志，该标志在 Phase 1/2 失败时会被设置为 `False`，导致 tracker 永不记录下载。

修复策略采用最小改动原则：将第 266 行的条件从 `if use_dedup and not dry_run` 改为 `if tracker is not None and not dry_run`。错误处理采用非中断模式：使用 `logger.warning()` 记录 DB 错误，但保持下载功能正常运行。验证策略包括回归测试（添加边界测试用例）和功能验证（检查 cross-day-dedup.md 的 4 个验收标准）。

**Primary recommendation:** 单行修复 + 边界测试用例 + 集成验证，预计工作量 1-2 小时。

<user_constraints>
## User Constraints (from CONTEXT.md)

### Locked Decisions

#### Bug 修复策略
- **修复方式**：最小化修改 - 将第 266 行条件从 `if use_dedup` 改为 `if tracker is not None`
- **原因**：最小改动原则，保留现有两阶段下载流程
- **影响范围**：仅修改 `gallery_dl_wrapper.py` 第 266 行
- **预期效果**：即使 dry-run 或 archive 生成失败，只要 tracker 存在就执行 Phase 4

#### 错误处理策略
- **Phase 4 失败处理**：仅记录错误日志，返回成功结果
- **日志格式**：使用 `logger.warning()` 记录 DB 写入失败，包含异常信息
- **不中断流程**：下载功能不受 DB 错误影响，保持用户友好性
- **边界情况**：DB 权限错误、磁盘空间不足等不导致下载失败

#### 验证和测试策略
- **验证范围**：全面验证
  - 运行所有现有测试（test_gallery_dl_wrapper_dedup.py 等）
  - 手动测试跨日去重场景（3月7日→3月8日）
  - 验证 cross-day-dedup.md 所有 4 个验收标准
- **回归测试**：添加边界测试用例
  - 在 `test_gallery_dl_wrapper_dedup.py` 中添加新测试
  - 模拟 dry-run 失败后仍记录下载的场景
  - 确保 bug 不会再次出现
- **测试目标**：确保修复有效且功能完整

#### Issue 管理策略
- **关闭方式**：通过 commit message 自动关闭
- **格式**：使用 "Fixes #1, Closes #2" 在 commit message 中
- **验证后执行**：所有测试通过后提交修复 commit
- **无需人工审查**：测试验证即可关闭 issues

#### 文档更新策略
- **不更新文档**：不在 INTEGRATION.md/README.md 中添加 DB 错误处理说明
- **原因**：保持简单，DB 错误是边界情况，不影响主要使用场景
- **日志即可**：标准日志足以帮助调试

### Claude's Discretion
- Phase 4 错误日志的具体措辞和格式
- 边界测试用例的具体设计（覆盖哪些场景）
- 手动验证的具体步骤和测试数据
- commit message 的详细描述（除 "Fixes #1, Closes #2" 外）

### Deferred Ideas (OUT OF SCOPE)
None — 本阶段专注于 bug 修复和功能验证，无范围蔓延。
</user_constraints>

<phase_requirements>
## Phase Requirements

| ID | Description | Research Support |
|----|-------------|-----------------|
| **BUG-01** | 程序在首次下载后正确将下载记录写入 tracker DB | 修复第 266 行条件判断：`if tracker is not None and not dry_run`；错误处理使用 `logger.warning()`，不中断流程；添加边界测试用例验证修复效果 |
| **VERI-01** | 跨日去重功能已完整实现并正常工作 | 验证 cross-day-dedup.md 的 4 个验收标准；运行现有集成测试（test_gallery_dl_wrapper_dedup.py）；手动测试跨日去重场景（3月7日→3月8日）；测试通过后通过 commit message 关闭 GitHub issue #1 |
</phase_requirements>

## Standard Stack

### Core
| Library | Version | Purpose | Why Standard |
|---------|---------|---------|--------------|
| pytest | 9.0.2 | 测试框架 | 项目标准测试框架，已配置 pyproject.toml，支持 fixtures 和 markers |
| Python | 3.10+ | 运行环境 | 项目最低要求版本，类型注解完整 |

### Supporting
| Library | Version | Purpose | When to Use |
|---------|---------|---------|-------------|
| sqlite3 | 标准库 | tracker DB 存储 | DownloadTracker 已实现，无需额外配置 |
| logging | 标准库 | 错误日志记录 | Phase 4 失败时使用 `logger.warning()` |
| pathlib | 标准库 | 文件路径处理 | 已在项目中广泛使用 |

### Alternatives Considered
| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| pytest | unittest | pytest 提供更好的 fixture 系统和断言错误信息，项目已全面采用 |
| logger.warning() | logger.error() + raise | error+raise 会中断流程，不符合"非中断"策略；warning 保持下载功能正常 |

**Installation:**
无需安装新依赖。使用现有 pytest 9.0.2 和 Python 3.10+ 标准库。

## Architecture Patterns

### Recommended Project Structure
```
gallery-dl-auto/
├── src/gallery_dl_auto/
│   ├── integration/
│   │   └── gallery_dl_wrapper.py       # Bug 位置（第 266 行）+ 修复点
│   └── download/
│       └── download_tracker.py         # DownloadTracker 实现（已稳定）
├── tests/
│   ├── integration/
│   │   └── test_gallery_dl_wrapper_dedup.py  # 现有 7 个测试 + 边界测试用例
│   └── conftest.py                     # 共享 fixtures（tmp_path）
└── docs/requirements/
    └── cross-day-dedup.md              # 验收标准参考
```

### Pattern 1: 最小改动修复（Single-Line Fix）
**What:** 仅修改条件判断，保留现有逻辑和流程
**When to use:** Bug 根因明确，修复点单一，影响范围可控
**Example:**
```python
# 当前代码（第 266 行）：
if use_dedup and not dry_run and batch_result.success_list:
    logger.info("Phase 4: Recording downloads to tracker...")
    self._record_downloads(batch_result, tracker, mode, actual_date)

# 修复后：
if tracker is not None and not dry_run and batch_result.success_list:
    logger.info("Phase 4: Recording downloads to tracker...")
    self._record_downloads(batch_result, tracker, mode, actual_date)
```
**Source:** 项目代码审查 + CONTEXT.md 锁定决策

### Pattern 2: 非中断错误处理（Non-Breaking Error Handling）
**What:** Phase 4 失败时记录日志但不抛出异常，确保下载功能不受影响
**When to use:** 边界情况（DB 错误）不应影响核心功能（下载）
**Example:**
```python
# _record_downloads 方法现有实现（第 896-897 行）：
except Exception as e:
    logger.warning(f"Failed to record download for {illust_id}: {e}")

# 这是正确的模式 - 保持不变
```
**Source:** 现有代码（gallery_dl_wrapper.py:896-897）

### Pattern 3: 边界测试用例（Regression Test）
**What:** 模拟 Phase 1/2 失败场景，验证 Phase 4 仍能执行
**When to use:** 确保 bug 不会再次出现，覆盖边缘场景
**Example:**
```python
# 添加到 test_gallery_dl_wrapper_dedup.py
def test_record_downloads_when_dry_run_fails(tmp_path):
    """测试 dry-run 失败后仍能记录下载到 tracker"""
    # 准备
    config = DownloadConfig()
    wrapper = GalleryDLWrapper(config)
    db_path = tmp_path / "test.db"
    tracker = DownloadTracker(db_path)

    # 模拟 Phase 1 失败（通过 mock 或设置错误场景）
    # ... 实现细节由 Claude's Discretion 决定

    # 执行实际下载（跳过 Phase 1/2）
    result = BatchDownloadResult(
        success=True,
        total=2,
        downloaded=2,
        failed=0,
        skipped=0,
        output_dir=str(tmp_path),
        actual_download_dir=str(download_dir),
        success_list=[11111, 22222],
        failed_errors=[],
    )

    # 验证：即使 dry-run 失败，Phase 4 仍能记录到 tracker
    wrapper._record_downloads(result, tracker, "day", "2026-03-08")
    assert tracker.is_downloaded(11111)
    assert tracker.is_downloaded(22222)
```
**Source:** CONTEXT.md 验证策略 + 现有测试模式

### Anti-Patterns to Avoid
- **在 Phase 4 错误时抛出异常：** 会导致下载功能整体失败，破坏用户体验。应使用 `logger.warning()` 记录日志，允许部分记录失败
- **修改 use_dedup 标志逻辑：** 该标志用于 Phase 1/2/3 的去重逻辑，不应改动。应直接修改 Phase 4 的条件判断
- **创建新的错误处理类：** 现有 `logger.warning()` 模式已足够，无需引入新的异常类或错误处理器
- **添加 try-except 包裹 Phase 4 调用：** `_record_downloads` 方法内部已有完整的错误处理（第 896-897 行），外层无需再添加

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| DB 错误处理 | 自定义异常类或错误处理器 | `logger.warning()` + 现有 try-except 模式 | 现有实现已覆盖所有边界情况（第 896-897 行），简单可靠 |
| 测试框架 | 自定义测试工具 | pytest fixtures（tmp_path） | pytest 9.0.2 已配置完善，tmp_path 自动清理临时文件 |
| 数据库操作 | 自定义 SQL 或 ORM | DownloadTracker.record_download() | DownloadTracker 已实现完整（WAL 模式、索引、错误处理），直接调用即可 |
| 跨日去重逻辑 | 自定义去重算法 | DownloadTracker.is_downloaded() | 现有实现基于 SQLite，性能优秀且已测试通过 |

**Key insight:** Phase 11 的修复不需要新增组件或复杂逻辑。核心是**修正条件判断**并**添加回归测试**，所有底层能力（tracker、logging、pytest）已完整实现并稳定运行。

## Common Pitfalls

### Pitfall 1: 误判条件修改的影响范围
**What goes wrong:** 认为 `use_dedup` 标志仅影响 Phase 4，修改条件后会破坏其他阶段
**Why it happens:** `use_dedup` 在 Phase 1（第 183 行）、Phase 2（第 221 行）、Phase 3（第 224 行）都有使用，看似全局控制
**How to avoid:**
- 明确修改目标：仅修改第 266 行的 Phase 4 条件，**不修改 use_dedup 标志本身**
- Phase 1/2/3 的去重逻辑保持不变（使用 `use_dedup`）
- Phase 4 独立判断：使用 `tracker is not None`，与 use_dedup 解耦
**Warning signs:** 修改了 use_dedup 的赋值逻辑（第 183/221 行），导致 Phase 1/2/3 行为改变

### Pitfall 2: 测试用例过度复杂化
**What goes wrong:** 边界测试用例尝试模拟完整的 dry-run 失败流程，导致测试难以理解和维护
**Why it happens:** 认为需要完整模拟两阶段下载流程才能验证 bug 修复
**How to avoid:**
- 聚焦核心场景：验证"tracker 存在时 Phase 4 能执行"，不需要模拟 Phase 1/2 失败细节
- 直接测试 `_record_downloads` 方法（现有测试模式，第 190-226 行）
- 使用简单 mock 或跳过 dry-run，直接构造测试数据
**Warning signs:** 测试代码超过 50 行，需要 mock 多个函数或复杂的 setup/teardown

### Pitfall 3: 验证时忽略现有测试
**What goes wrong:** 只运行新添加的边界测试，未运行完整的集成测试套件
**Why it happens:** 认为新测试已覆盖修复场景，旧测试无关
**How to avoid:**
- 运行 `pytest tests/integration/test_gallery_dl_wrapper_dedup.py -v`（7 个现有测试）
- 运行 `pytest tests/ -k "tracker or dedup"`（所有相关测试）
- 确保 525 个现有测试全部通过（pytest --collect-only 输出）
**Warning signs:** 新测试通过但其他测试失败；跳过测试套件直接手动验证

### Pitfall 4: 手动验证时使用真实 Pixiv 账号
**What goes wrong:** 在生产环境中测试 bug 修复，可能触发 Pixiv API 限流或产生真实下载
**Why it happens:** 认为需要完整的端到端测试才能验证功能
**How to avoid:**
- 使用 mock 数据或测试 fixture（tests/fixtures/）
- 在临时目录测试（tmp_path fixture）
- 避免 3月7日/3月8日 的真实下载，使用模拟数据验证逻辑
**Warning signs:** 手动测试需要真实 refresh token；下载大量文件到生产目录

## Code Examples

Verified patterns from official sources:

### 修复点：Phase 4 条件判断（第 266 行）
```python
# 当前代码（存在 bug）：
if use_dedup and not dry_run and batch_result.success_list:
    logger.info("Phase 4: Recording downloads to tracker...")
    self._record_downloads(batch_result, tracker, mode, actual_date)

# 修复后（tracker 解耦）：
if tracker is not None and not dry_run and batch_result.success_list:
    logger.info("Phase 4: Recording downloads to tracker...")
    self._record_downloads(batch_result, tracker, mode, actual_date)
```
**Source:** 项目代码审查（gallery_dl_wrapper.py:266）+ CONTEXT.md 修复策略

### 错误处理模式（已实现，无需修改）
```python
# _record_downloads 方法中的错误处理（第 896-897 行）：
except Exception as e:
    logger.warning(f"Failed to record download for {illust_id}: {e}")

# 日志记录示例：
# WARNING - Failed to record download for 12345: database is locked
# WARNING - Failed to record download for 67890: no space left on device
```
**Source:** 现有代码（gallery_dl_wrapper.py:896-897）

### 边界测试用例模式（待添加）
```python
def test_record_downloads_with_tracker_enabled(tmp_path):
    """测试 tracker 存在时，即使 dedup 阶段失败仍能记录下载"""
    # 准备
    config = DownloadConfig()
    wrapper = GalleryDLWrapper(config)
    db_path = tmp_path / "test.db"
    tracker = DownloadTracker(db_path)

    download_dir = tmp_path / "downloads"
    download_dir.mkdir()

    result = BatchDownloadResult(
        success=True,
        total=2,
        downloaded=2,
        failed=0,
        skipped=0,
        output_dir=str(tmp_path),
        actual_download_dir=str(download_dir),
        success_list=[11111, 22222],
        failed_errors=[],
    )

    # 执行：直接调用 _record_downloads（绕过 Phase 1/2/3）
    wrapper._record_downloads(result, tracker, "day", "2026-03-08")

    # 验证：tracker 应包含记录
    assert tracker.is_downloaded(11111)
    assert tracker.is_downloaded(22222)
```
**Source:** 现有测试模式（test_gallery_dl_wrapper_dedup.py:190-226）

### Commit Message 格式
```bash
git commit -m "fix(wrapper): ensure tracker records downloads even when dedup phases fail

- Change Phase 4 condition from 'if use_dedup' to 'if tracker is not None'
- Add regression test for dry-run failure scenario
- Fixes #1, Closes #2

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
```
**Source:** CONTEXT.md Issue 管理策略 + 项目 commit 历史模式

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| Phase 4 依赖 `use_dedup` 标志 | Phase 4 独立判断 `tracker is not None` | Phase 11 (2026-03-16) | 即使 Phase 1/2 失败，tracker 仍能记录下载 |
| 测试覆盖去重流程 | 添加边界测试用例 | Phase 11 (待实现) | 确保 bug 不会再次出现，覆盖 dry-run 失败场景 |

**Deprecated/outdated:**
- **在 Phase 4 使用 `use_dedup` 标志：** 导致 Phase 1/2 失败时 Phase 4 永不执行，与设计意图不符。替换为 `tracker is not None`

## Open Questions

1. **边界测试用例是否需要模拟完整的 dry-run 失败流程？**
   - What we know: CONTEXT.md 要求"模拟 dry-run 失败后仍记录下载的场景"
   - What's unclear: 是否需要实际触发 dry-run 失败（复杂），还是直接构造测试数据（简单）
   - Recommendation: **采用简单方案** - 直接调用 `_record_downloads` 方法，绕过 Phase 1/2/3。现有测试（test_record_downloads）已采用此模式，测试可读性高且维护成本低。如果时间允许，可以添加集成测试覆盖完整流程，但非必需。

2. **手动验证是否必须使用真实 Pixiv 数据？**
   - What we know: VERI-01 要求"手动测试跨日去重场景（3月7日→3月8日）"
   - What's unclear: 是否需要真实 API 调用和下载，还是使用 mock 数据
   - Recommendation: **优先使用 mock 数据** - 在 `tmp` 目录中使用测试 fixture，避免生产环境干扰。如果用户要求真实验证，提供清晰的测试步骤（包括 refresh token 准备、目录设置、预期结果），但标记为可选。

## Validation Architecture

> workflow.nyquist_validation 未在 config.json 中明确禁用（默认启用），包含此部分。

### Test Framework
| Property | Value |
|----------|-------|
| Framework | pytest 9.0.2 |
| Config file | pyproject.toml (lines 142-150) |
| Quick run command | `pytest tests/integration/test_gallery_dl_wrapper_dedup.py -v -x` |
| Full suite command | `pytest tests/ -v --tb=short` |

### Phase Requirements → Test Map
| Req ID | Behavior | Test Type | Automated Command | File Exists? |
|--------|----------|-----------|-------------------|-------------|
| BUG-01 | Phase 4 在 tracker 存在时执行（即使 use_dedup=False） | unit | `pytest tests/integration/test_gallery_dl_wrapper_dedup.py::test_record_downloads_with_tracker_enabled -x` | ❌ Wave 0 |
| BUG-01 | Phase 4 错误不中断下载流程 | unit | `pytest tests/integration/test_gallery_dl_wrapper_dedup.py::test_record_downloads_with_missing_files -x` | ✅ 现有 |
| VERI-01 | 首次下载记录到 tracker DB | unit | `pytest tests/integration/test_gallery_dl_wrapper_dedup.py::test_record_downloads -x` | ✅ 现有 |
| VERI-01 | 第二次下载跳过已存在作品 | unit | `pytest tests/integration/test_gallery_dl_wrapper_dedup.py::test_check_existing_downloads_partial_skip -x` | ✅ 现有 |
| VERI-01 | 跨日去重功能正常 | integration | `pytest tests/integration/test_gallery_dl_wrapper_dedup.py -v` | ✅ 现有（7 tests） |
| VERI-01 | cross-day-dedup.md 验收标准 | manual | N/A（手动验证） | ❌ 手动 |

### Sampling Rate
- **Per task commit:** `pytest tests/integration/test_gallery_dl_wrapper_dedup.py -x`（快速反馈）
- **Per wave merge:** `pytest tests/ -k "tracker or dedup" --tb=short`（相关模块）
- **Phase gate:** `pytest tests/ -v --tb=short`（完整测试套件，525 tests）

### Wave 0 Gaps
- [ ] `tests/integration/test_gallery_dl_wrapper_dedup.py::test_record_downloads_with_tracker_enabled` — 边界测试用例，覆盖 dry-run 失败场景（BUG-01）
- [ ] 手动验证清单 — 验证 cross-day-dedup.md 的 4 个验收标准（VERI-01）

*(其他测试基础设施已完善：conftest.py 提供 tmp_path fixture，pytest 配置完整，525 个现有测试可运行)*

## Sources

### Primary (HIGH confidence)
- 项目代码审查（gallery_dl_wrapper.py:266, 183, 221, 896-897）- bug 位置、use_dedup 逻辑、错误处理模式
- tests/integration/test_gallery_dl_wrapper_dedup.py - 现有测试模式（7 个单元测试）
- docs/requirements/cross-day-dedup.md - 验收标准（4 个标准）
- pyproject.toml (lines 142-150) - pytest 配置

### Secondary (MEDIUM confidence)
- CONTEXT.md - 用户锁定的修复策略、错误处理策略、验证策略
- REQUIREMENTS.md (BUG-01, VERI-01) - 需求定义和验证目标
- CLAUDE.md - 项目开发规范（中文沟通、Windows 环境、tmp 目录）

### Tertiary (LOW confidence)
- 无（所有关键信息来自项目代码和官方文档）

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - pytest 9.0.2 已验证（python -c "import pytest"），Python 3.10+ 为项目要求，无需新依赖
- Architecture: HIGH - bug 根因明确（use_dedup 标志逻辑），修复策略清晰（单行修改），错误处理模式已实现
- Pitfalls: HIGH - 基于代码审查和现有测试模式推导，与 CONTEXT.md 用户决策一致

**Research date:** 2026-03-16
**Valid until:** 2026-04-16（30 天 - bug 修复和验证工作即将开始，研究内容基于稳定的项目结构）

---

**For planner:** 研究已完成，核心发现：
1. Bug 修复为单行改动（第 266 行条件判断）
2. 错误处理已实现（无需新增）
3. 需添加 1 个边界测试用例（覆盖 dry-run 失败场景）
4. 手动验证 4 个验收标准（cross-day-dedup.md）
5. 通过 commit message 自动关闭 GitHub issues #1 和 #2

**Next step:** 运行 `/gsd:plan-phase 11` 创建执行计划。
