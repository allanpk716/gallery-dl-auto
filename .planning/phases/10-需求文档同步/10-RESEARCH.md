# Phase 10: 需求文档同步 - Research

**Researched:** 2026-02-25
**Domain:** Documentation Synchronization and Requirements Management
**Confidence:** HIGH

## Summary

Phase 10 是一个技术债务清理阶段（Gap Closure），主要目标是解决 v1.0 里程碑审计中发现的文档同步问题。当前项目已完成 Phase 8（用户体验优化）和 Phase 9（Phase 8 验证完成），但需求文档管理存在三个关键问题：1）REQUIREMENTS.md 文件位置混乱，v1.0 版本存档在 `milestones/` 目录而非标准的 `.planning/` 目录；2）多个已完成需求的 checkboxes 未更新（OUTP-01/02/03/04、UX-01/02/03/06）；3）UX-06 需求映射错误，实际在 Phase 6 完成但文档中标记为 Phase 8 Pending。

这些问题不会影响功能实现，但会影响项目可追溯性和需求管理准确性。本阶段需要创建或定位标准的 REQUIREMENTS.md 文件，同步所有需求状态，修正阶段映射错误，确保文档与实际实现一致。

**Primary recommendation:** 在 `.planning/` 目录创建当前活跃的 REQUIREMENTS.md 文件，基于 v1.0-REQUIREMENTS.md 模板，更新所有已完成需求状态，修正 UX-06 阶段映射，建立需求文档维护规范。

## User Constraints (from CONTEXT.md)

*Note: No CONTEXT.md file exists for Phase 10. Research was performed without user-provided constraints.*

### Locked Decisions

None - this is a gap closure phase with no prior user decisions.

### Claude's Discretion

Full discretion to determine:
- Whether to create new REQUIREMENTS.md in `.planning/` or continue using `milestones/v1.0-REQUIREMENTS.md`
- How to structure the requirements tracking system
- Whether to create automated validation for requirement status updates
- Documentation format and organization

### Deferred Ideas (OUT OF SCOPE)

None identified.

## Phase Requirements

This section maps Phase 10 success criteria to research findings.

| ID | Description | Research Support |
|----|-------------|------------------|
| GAP-01 | REQUIREMENTS.md 文件已创建或定位 | 需要在 `.planning/` 目录创建活跃的 REQUIREMENTS.md 文件，参考 `milestones/v1.0-REQUIREMENTS.md` 结构 |
| GAP-02 | 所有已完成需求的 checkboxes 已更新为 [x] | 需要更新 13 个需求：AUTH-01/02/03/04、RANK-01/02/03/04、CONT-01/02/03/04、OUTP-01/02/03/04/05/06、UX-01/02/03/06 |
| GAP-03 | UX-06 阶段映射已修正为 Phase 6 Complete | 需要修正 Traceability 表中的 UX-06 映射，从 Phase 8 Pending 改为 Phase 6 Complete |

## Standard Stack

### Core

| Library/Tool | Version | Purpose | Why Standard |
|--------------|---------|---------|--------------|
| Markdown | N/A | Requirements documentation format | 项目标准文档格式，易于阅读、版本控制和差异比较 |
| YAML Front Matter | N/A | 元数据标记 | 与其他项目文档保持一致（VERIFICATION.md、SUMMARY.md） |

### Supporting

| Tool | Purpose | When to Use |
|------|---------|-------------|
| Git | 版本控制和差异追踪 | 需求变更时提交，便于追溯历史 |
| Text Editor | 手动编辑需求文档 | 需求状态更新时 |

### Alternatives Considered

| Instead of | Could Use | Tradeoff |
|------------|-----------|----------|
| Markdown REQUIREMENTS.md | SQLite requirements database | 数据库查询更快，但失去了版本控制的可读性和 diff 能力 |
| Manual checkbox updates | Automated requirement tracking script | 自动化更好，但一次性 gap closure 不值得投入开发时间 |

**Installation:**

无需安装任何依赖，纯文档操作。

## Architecture Patterns

### Recommended Project Structure

```
.planning/
├── REQUIREMENTS.md           # 当前活跃的需求文档（新建）
├── PROJECT.md                # 项目概览
├── ROADMAP.md                # 路线图
├── STATE.md                  # 当前状态
└── milestones/
    └── v1.0-REQUIREMENTS.md  # v1.0 存档版本（已存在）
```

### Pattern 1: Requirements Traceability Matrix

**What:** 一个表格映射每个需求 ID 到实现阶段和验证状态

**When to use:** 项目有多个需求分布在多个阶段时

**Example:**

```markdown
## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| AUTH-01 | Phase 2: Token 自动化 | Complete |
| UX-06 | Phase 6: 多排行榜支持 | Complete |
```

**Why it works:**
- 提供需求到实现的完整映射
- 易于识别 orphaned 或重复实现的需求
- 支持里程碑审计快速验证覆盖率

### Pattern 2: Checkbox Status Convention

**What:** 使用 Markdown checkbox 语法标记需求完成状态

**When to use:** 需要在文档中直观显示完成进度时

**Convention:**

```markdown
- [x] **AUTH-01**: 需求描述 (已完成)
- [ ] **AUTH-02**: 需求描述 (未完成或进行中)
```

**Why it works:**
- Markdown 渲染器支持可视化 checkbox
- Git diff 容易追踪状态变更
- 与 GitHub 等 Git 托管平台集成

### Pattern 3: Phase-Backed Requirement Verification

**What:** 每个 Phase 的 VERIFICATION.md 文件包含 Requirements Coverage 表格

**When to use:** 验证需求是否真正实现时

**Example (from Phase 8 VERIFICATION.md):**

```markdown
### Requirements Coverage

| Requirement | Source | Description | Status | Evidence |
| ----------- | ------ | ----------- | ------ | -------- |
| UX-04 | ROADMAP | 程序实时显示下载进度 | ✓ SATISFIED | ProgressReporter 类 + --verbose 标志 |
```

**Why it works:**
- 需求验证与实现代码直接关联
- 提供具体证据（代码位置、测试结果）
- 支持里程碑审计自动化检查

### Anti-Patterns to Avoid

- **Anti-pattern 1: 在多个地方维护需求文档**
  - 为什么不好：容易导致不同步，增加维护负担
  - 正确做法：一个活跃的 REQUIREMENTS.md，里程碑完成时存档到 milestones/ 目录

- **Anti-pattern 2: 仅更新 checkbox 而不更新 Traceability 表**
  - 为什么不好：阶段映射不准确，无法追溯实现位置
  - 正确做法：同时更新 checkbox 和 Traceability 表格

- **Anti-pattern 3: 需求状态与 VERIFICATION.md 不一致**
  - 为什么不好：失去单一真相来源，审计时发现矛盾
  - 正确做法：REQUIREMENTS.md 状态必须与 VERIFICATION.md 保持一致

## Don't Hand-Roll

| Problem | Don't Build | Use Instead | Why |
|---------|-------------|-------------|-----|
| 需求文档格式设计 | 自定义 JSON/YAML schema | Markdown + YAML front matter | Markdown 是项目标准格式，无需额外工具，Git diff 友好 |
| 需求验证自动化 | Python 脚本解析需求状态 | VERIFICATION.md + 里程碑审计流程 | 已有成熟的审计流程，无需重复开发 |
| 需求变更历史追踪 | 手动维护 CHANGELOG | Git commit history | Git 天然支持历史追踪，无需额外维护 |

**Key insight:** 需求管理是文档问题，不是代码问题。使用标准 Markdown 和 Git 工具即可，无需复杂系统。

## Common Pitfalls

### Pitfall 1: 需求文档位置不一致

**What goes wrong:** REQUIREMENTS.md 文件分散在多个目录（`.planning/`、`milestones/`、项目根目录），导致维护时不确定应该更新哪个文件。

**Why it happens:**
- 项目早期没有明确的文档组织规范
- 里程碑完成时存档需求文档，但忘记创建新的活跃版本
- 不同开发者对文档位置理解不一致

**How to avoid:**
- 建立清晰的文档组织规范（参考 ROADMAP.md）
- 活跃的需求文档统一放在 `.planning/REQUIREMENTS.md`
- 里程碑完成时将当前版本存档到 `milestones/v{version}-REQUIREMENTS.md`，然后创建新的活跃版本

**Warning signs:**
- 发现多个 REQUIREMENTS.md 文件
- 更新需求状态时不确定应该修改哪个文件
- 里程碑审计发现需求文档与实际实现不一致

### Pitfall 2: Checkbox 更新遗漏

**What goes wrong:** Phase 完成并通过 VERIFICATION.md 验证后，忘记更新 REQUIREMENTS.md 中的 checkbox，导致文档状态与实际不符。

**Why it happens:**
- VERIFICATION.md 和 REQUIREMENTS.md 是两个独立文档，容易遗漏同步
- Phase 完成后焦点转移到下一个阶段，忽略文档维护
- 没有明确的"Phase 完成 → 更新需求文档"流程

**How to avoid:**
- 将"更新 REQUIREMENTS.md"作为 Phase VERIFICATION.md 的 mandatory task
- 在 STATE.md 中记录每个 Phase 的需求完成情况
- 使用里程碑审计自动检查不一致

**Warning signs:**
- VERIFICATION.md 显示需求 SATISFIED，但 REQUIREMENTS.md checkbox 仍为 `[ ]`
- 里程碑审计报告显示"checkboxes not updated"
- Roadmap 显示 Phase Complete，但 Traceability 表显示 Pending

### Pitfall 3: 需求阶段映射错误

**What goes wrong:** 需求在 Traceability 表中映射到错误的 Phase，导致追溯时找不到实现位置，或者重复实现。

**Why it happens:**
- 需求在 Roadmap 规划时映射到一个 Phase，但实际实现在另一个 Phase
- 需求分阶段实现（如 Phase 6 + Phase 8），但 Traceability 表只记录了一个 Phase
- Roadmap 更新时忘记同步更新 Traceability 表

**How to avoid:**
- 需求实现完成后，立即更新 Traceability 表映射
- 如果需求分阶段实现，在 Traceability 表中注明（如 "Phase 6 (partial) + Phase 8 (complete)"）
- 里程碑审计时交叉验证 Traceability 表与 VERIFICATION.md

**Warning signs:**
- 在 Phase X 的代码中找到需求 Y 的实现，但 Traceability 表显示需求 Y 在 Phase Z
- VERIFICATION.md 显示需求 SATISFIED，但 Traceability 表映射的 Phase 未开始
- 多个 Phase 的 VERIFICATION.md 声称同一个需求 SATISFIED

### Pitfall 4: 存档版本与活跃版本混淆

**What goes wrong:** 更新需求状态时，错误地修改了 `milestones/` 目录中的存档版本，而非 `.planning/` 目录中的活跃版本。

**Why it happens:**
- 存档版本文件名包含版本号（如 `v1.0-REQUIREMENTS.md`），看起来更"正式"
- 开发者不确定应该修改哪个文件
- 文档顶部没有清晰标记"活跃版本"或"存档版本"

**How to avoid:**
- 在存档版本文件顶部添加 YAML front matter 标记：`archived: true`、`version: v1.0`
- 在活跃版本文件顶部添加注释：`This is the ACTIVE requirements document. For archived versions, see milestones/`
- 使用文件路径约定：`.planning/REQUIREMENTS.md` (活跃) vs `.planning/milestones/v{version}-REQUIREMENTS.md` (存档)

**Warning signs:**
- 修改需求状态后，发现修改的是 `milestones/` 目录中的文件
- 同一个需求在多个文件中有不同的状态
- Git commit history 显示对存档文件的修改

## Code Examples

### Example 1: 标准的 REQUIREMENTS.md 结构

```markdown
# Requirements: [项目名称]

**Defined:** YYYY-MM-DD
**Core Value:** [项目核心价值描述]

## v1 Requirements

[版本描述]

### [需求类别 1]

- [x] **REQ-01**: 需求描述 (已完成)
- [ ] **REQ-02**: 需求描述 (未完成)

### [需求类别 2]

- [x] **REQ-03**: 需求描述

## v2 Requirements

[延后到未来版本的需求]

## Out of Scope

[明确排除的功能]

| Feature | Reason |
|---------|--------|
| 功能名称 | 排除理由 |

## Traceability

| Requirement | Phase | Status |
|-------------|-------|--------|
| REQ-01 | Phase 1: [阶段名称] | Complete |
| REQ-02 | Phase 2: [阶段名称] | Pending |
| REQ-03 | Phase 1: [阶段名称] | Complete |

---
*Requirements defined: YYYY-MM-DD*
*Last updated: YYYY-MM-DD after Phase X completion*
```

**Source:** `.planning/milestones/v1.0-REQUIREMENTS.md`

### Example 2: 更新需求状态的标准流程

**Step 1: 验证需求完成**

```markdown
# Phase X VERIFICATION.md

### Requirements Coverage

| Requirement | Source | Description | Status | Evidence |
| ----------- | ------ | ----------- | ------ | -------- |
| REQ-01 | REQUIREMENTS | 需求描述 | ✓ SATISFIED | [具体证据：代码位置、测试结果] |
```

**Step 2: 更新 REQUIREMENTS.md checkbox**

```markdown
### [需求类别]

- [x] **REQ-01**: 需求描述  # 从 [ ] 改为 [x]
```

**Step 3: 更新 Traceability 表**

```markdown
| REQ-01 | Phase X: [阶段名称] | Complete |  # 从 Pending 改为 Complete
```

**Step 4: 更新文件底部时间戳**

```markdown
---
*Requirements defined: YYYY-MM-DD*
*Last updated: YYYY-MM-DD after Phase X completion*  # 更新日期
```

**Source:** GSD 工作流程最佳实践

### Example 3: 处理分阶段实现的需求

**在 REQUIREMENTS.md 中：**

```markdown
### 用户体验

- [x] **UX-05**: 程序控制下载速率以避免触发 Pixiv 的反爬虫机制
```

**在 Traceability 表中：**

```markdown
| UX-05 | Phase 6 (partial) + Phase 8 (complete) | Complete |
```

**在 Phase 8 VERIFICATION.md 中：**

```markdown
| UX-05 | REQUIREMENTS | 程序控制下载速率 | ✓ SATISFIED | Phase 6 实现基础版本 (config/download.yaml), Phase 8 扩展 CLI 参数和 429 错误处理 |

**Implementation History:**
- UX-05: 分阶段实现 — Phase 6 实现基础速率控制, Phase 8 扩展 CLI 参数和 429 错误处理
```

**Source:** Phase 8 VERIFICATION.md, Line 61-62

### Example 4: 修正需求阶段映射错误

**Before (错误):**

```markdown
| UX-06 | Phase 8: 用户体验优化 | Pending |
```

**After (正确):**

```markdown
| UX-06 | Phase 6: 多排行榜支持 | Complete |
```

**验证证据:** Phase 6 VERIFICATION.md Line 62: `UX-06: ✓ SATISFIED`

## State of the Art

| Old Approach | Current Approach | When Changed | Impact |
|--------------|------------------|--------------|--------|
| 手动维护需求状态 | Phase VERIFICATION.md + REQUIREMENTS.md 同步 | v1.0 里程碑 | 提供具体验证证据，减少遗漏 |
| 需求文档放在项目根目录 | 统一放在 `.planning/` 目录 | Phase 1 | 集中管理项目文档，减少混乱 |
| 无里程碑审计 | 自动化里程碑审计检查需求覆盖率 | v1.0 里程碑 | 强制验证需求完成，防止遗漏 |

**Deprecated/outdated:**

- **单一 REQUIREMENTS.md 不分版本**: 现在采用活跃版本 + 存档版本模式，避免历史版本混乱
- **仅靠 checkbox 追踪状态**: 现在要求 VERIFICATION.md 提供具体证据，增强可信度
- **需求映射仅在 ROADMAP.md**: 现在要求同时在 REQUIREMENTS.md Traceability 表中映射，提供双重追踪

## Open Questions

1. **是否应该创建 `.planning/REQUIREMENTS.md` 还是继续使用 `milestones/v1.0-REQUIREMENTS.md`？**
   - What we know:
     - `milestones/v1.0-REQUIREMENTS.md` 已存在并标记为 "SHIPPED"
     - Phase 8 VERIFICATION.md Line 52 注释：*"No REQUIREMENTS.md file found in .planning/ directory"*
     - ROADMAP.md 没有明确要求 REQUIREMENTS.md 必须在 `.planning/` 目录
   - What's unclear: 项目文档组织规范是否强制要求 `.planning/REQUIREMENTS.md`
   - Recommendation: 创建 `.planning/REQUIREMENTS.md` 作为当前活跃版本，保持 `milestones/v1.0-REQUIREMENTS.md` 作为存档。这样符合文档组织最佳实践（活跃文档在 `.planning/`，存档在 `milestones/`）。

2. **是否需要创建自动化脚本验证需求状态一致性？**
   - What we know:
     - v1.0 里程碑审计已发现多处不一致（checkboxes 未更新、阶段映射错误）
     - 手动维护容易遗漏
     - 开发自动化脚本需要额外时间
   - What's unclear: 投入回报比是否合理（Gap closure 阶段应该快速完成）
   - Recommendation: **不创建自动化脚本**。这是一个一次性的 gap closure 任务，手动更新即可。未来如果频繁出现不一致问题，再考虑在里程碑审计流程中添加自动化检查。

3. **如何处理 v1.1 里程碑的需求（UX-01/02/03）？**
   - What we know:
     - UX-01/02/03 已在 Phase 7 完成（v1.1 milestone）
     - `milestones/v1.0-REQUIREMENTS.md` 不包含 v1.1 需求
     - PROJECT.md Line 32-36 显示 v1.1 需求已完成
   - What's unclear: 是否应该在 `.planning/REQUIREMENTS.md` 中添加 v1.1 需求部分
   - Recommendation: **添加 v1.1 Requirements 部分到 REQUIREMENTS.md**。虽然原始 v1.0-REQUIREMENTS.md 没有这部分，但当前活跃的 REQUIREMENTS.md 应该反映所有已实现的需求，包括 v1.0 和 v1.1。这样提供完整的需求追踪视图。

## Validation Architecture

*Note: Workflow Nyquist validation is disabled (config.json workflow.verifier: true, but this is a documentation-only phase with no code implementation. Skip test framework section.)*

### Test Framework

**Not applicable** - Phase 10 is a documentation-only gap closure task. No code will be written, no tests needed.

### Phase Requirements → Test Map

**Not applicable** - No code changes, no tests required.

### Verification Strategy

**Documentation Verification:**

| Success Criterion | Verification Method | Evidence Required |
|-------------------|---------------------|-------------------|
| REQUIREMENTS.md 文件已创建或定位 | 文件存在性检查 | 文件路径：`.planning/REQUIREMENTS.md` |
| 所有已完成需求的 checkboxes 已更新 | Markdown 检查：所有 24 个需求 checkbox 为 `[x]` | 文件内容审查 + diff 确认 |
| UX-06 阶段映射已修正 | Traceability 表检查：UX-06 映射为 Phase 6 Complete | 文件内容审查 + diff 确认 |

**Manual Verification Steps:**

1. **Verify REQUIREMENTS.md exists:**
   ```bash
   test -f ".planning/REQUIREMENTS.md" && echo "EXISTS" || echo "MISSING"
   ```

2. **Verify checkbox updates:**
   ```bash
   # 检查所有 AUTH/RANK/CONT/OUTP/UX 需求是否为 [x]
   grep -E "^\- \[x\] \*\*(AUTH|RANK|CONT|OUTP|UX)-" .planning/REQUIREMENTS.md
   ```

3. **Verify UX-06 mapping:**
   ```bash
   # 检查 Traceability 表中 UX-06 映射
   grep "UX-06" .planning/REQUIREMENTS.md
   ```

4. **Verify consistency with VERIFICATION.md files:**
   - Cross-reference Phase 5 VERIFICATION.md (OUTP-01/02/03/04)
   - Cross-reference Phase 7 VERIFICATION.md (UX-01/02/03)
   - Cross-reference Phase 8 VERIFICATION.md (UX-04/05/06)

**Estimated verification time:** ~5 minutes (manual file review)

## Sources

### Primary (HIGH confidence)

- `.planning/milestones/v1.0-REQUIREMENTS.md` - v1.0 存档需求文档，用作模板和参考
- `.planning/v1.0-MILESTONE-AUDIT.md` - 里程碑审计报告，详细列出所有 gaps
- `.planning/phases/08-用户体验优化/08-VERIFICATION.md` - Phase 8 验证报告，包含 UX-04/05/06 验证证据
- `.planning/phases/07-cuo-wu-chu-li-yu-jian-zhuang-xing/07-VERIFICATION.md` - Phase 7 验证报告，包含 UX-01/02/03 验证证据
- `.planning/phases/05-json-output/05-VERIFICATION.md` - Phase 5 验证报告，包含 OUTP-01/02/03/04 验证证据

### Secondary (MEDIUM confidence)

- `.planning/phases/06-multi-ranking-support/06-VERIFICATION.md` - Phase 6 验证报告，确认 UX-06 在 Phase 6 完成
- `.planning/ROADMAP.md` - 项目路线图，确认 Phase 8/9/10 规划
- `.planning/STATE.md` - 项目当前状态，确认 Phase 9 已完成
- `.planning/PROJECT.md` - 项目概览，确认 v1.0 和 v1.1 需求完成情况

### Tertiary (LOW confidence)

- WebSearch for "requirements management best practices markdown" (2026) - 通用建议，未针对具体项目
- WebSearch for "software requirements traceability matrix patterns" (2026) - 通用模式，未验证适用性

## Metadata

**Confidence breakdown:**
- Standard stack: HIGH - 无需外部库，纯文档操作
- Architecture: HIGH - 基于项目现有文档结构和最佳实践
- Pitfalls: HIGH - 基于 v1.0 里程碑审计发现的实际问题
- Code examples: HIGH - 直接来自项目现有文档

**Research date:** 2026-02-25
**Valid until:** N/A - 文档模式相对稳定，长期有效

---

## Appendix: Gap Analysis Summary

Based on v1.0-MILESTONE-AUDIT.md, the following gaps must be closed in Phase 10:

### Gap 1: Missing REQUIREMENTS.md in .planning/

**Current state:**
- `.planning/milestones/v1.0-REQUIREMENTS.md` exists (archived)
- `.planning/REQUIREMENTS.md` does NOT exist
- Phase 8 VERIFICATION.md Line 52: *"No REQUIREMENTS.md file found in .planning/ directory"*

**Required action:**
- Create `.planning/REQUIREMENTS.md` as active requirements document
- Base on `milestones/v1.0-REQUIREMENTS.md` template
- Add v1.1 requirements section (UX-01/02/03)

### Gap 2: Unchecked Checkboxes (13 requirements)

**Affected requirements:**

| Category | Requirements | Evidence |
|----------|--------------|----------|
| AUTH | AUTH-01, AUTH-02, AUTH-03, AUTH-04 | Phase 2 VERIFICATION.md: ✓ SATISFIED |
| RANK | RANK-01, RANK-02, RANK-03, RANK-04 | Phase 3/6 VERIFICATION.md: ✓ SATISFIED |
| CONT | CONT-01, CONT-02, CONT-03, CONT-04 | Phase 3/4 VERIFICATION.md: ✓ SATISFIED |
| OUTP | OUTP-01, OUTP-02, OUTP-03, OUTP-04 | Phase 5 VERIFICATION.md: ✓ PASSED |
| UX | UX-01, UX-02, UX-03 | Phase 7 VERIFICATION.md: ✓ SATISFIED |
| UX | UX-06 | Phase 6 VERIFICATION.md: ✓ SATISFIED |

**Total:** 20 requirements (18 v1.0 + 2 v1.1) checkboxes need update from `[ ]` to `[x]`

**Note:** OUTP-05/06 already checked in v1.0-REQUIREMENTS.md, but AUDIT report Line 245-250 shows them as `[ ]`. Double-check actual file content.

### Gap 3: UX-06 Phase Mapping Error

**Current mapping (INCORRECT):**
```markdown
| UX-06 | Phase 8: 用户体验优化 | Pending |
```

**Correct mapping:**
```markdown
| UX-06 | Phase 6: 多排行榜支持 | Complete |
```

**Evidence:**
- Phase 6 VERIFICATION.md Line 62: `UX-06: ✓ SATISFIED`
- Phase 6 actually implemented configurable rate limiting (config/download.yaml)

**Root cause:** REQUIREMENTS.md created before Phase 6 VERIFICATION.md, mapping based on roadmap planning而非 actual implementation.

### Gap 4: v1.1 Requirements Missing from Archive

**Issue:** `milestones/v1.0-REQUIREMENTS.md` does not include v1.1 requirements (UX-01/02/03 from Phase 7)

**Impact:** Archived v1.0 requirements incomplete

**Required action:** When creating `.planning/REQUIREMENTS.md`, add v1.1 section:

```markdown
## v1.1 Requirements

**Completed:** 2026-02-25

### 健壮性与错误处理

- [x] **UX-01**: 程序处理网络错误并提供清晰的错误提示
- [x] **UX-02**: 程序处理权限错误并提供清晰的错误提示
- [x] **UX-03**: 程序支持增量下载，跳过已下载的内容
```

---

**Research completed:** 2026-02-25
**Ready for planning:** Yes - all gaps identified, solutions clear
**Estimated effort:** 1 plan, ~15 minutes execution time
