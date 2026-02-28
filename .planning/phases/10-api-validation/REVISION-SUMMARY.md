# Phase 10 计划修订总结

## 修订日期
2026-02-26

## 修订原因
根据 GSD planner checker 的反馈,所有 Phase 10 计划缺少必需的 frontmatter 字段和 XML 任务元素。

## Blocker 问题修复

### 1. 添加必需的 frontmatter 字段

所有计划现在都包含以下必需字段:
- `phase`: Phase 编号 (例如 '10')
- `plan`: 计划编号 (例如 '01', '02A', '02B')
- `type`: 计划类型 (auto)
- `must_haves`: 目标验证条件

**示例 (10-01)**:
```yaml
---
phase: '10'
plan: '01'
type: auto
must_haves:
  jsonschema_installed: jsonschema 依赖已安装
  test_framework_established: tests/validation/ 目录存在,包含 conftest.py 和 test_json_schemas.py
  json_schemas_defined: 所有关键命令的 JSON Schema 在 conftest.py 中定义
  # ...
---
```

### 2. 将任务转换为 XML 元素

所有任务现在使用 `<task>` XML 元素,包含以下子元素:
- `<name>`: 任务名称
- `<goal>`: 任务目标
- `<files>`: 修改的文件列表
- `<action>`: 执行步骤
- `<verify>`: 验证命令
- `<done>`: 完成条件

**示例**:
```xml
<task id="1">
<name>安装 jsonschema 依赖并建立测试基础设施</name>
<goal>添加 jsonschema 库到开发依赖,创建 tests/validation/ 目录结构</goal>
<files>
- C:/WorkSpace/gallery-dl-auto/pyproject.toml (更新依赖)
- C:/WorkSpace/gallery-dl-auto/tests/validation/__init__.py (新建)
</files>
<action>
1. 更新 pyproject.toml,添加 jsonschema 到 dev dependencies
2. 创建测试目录结构
3. 创建 conftest.py,定义 JSON Schema fixtures
</action>
<verify>
```bash
pip install -e ".[dev]"
python -c "import jsonschema; print(jsonschema.__version__)"
```
</verify>
<done>测试基础设施已建立,jsonschema 可用</done>
</task>
```

## Warnings 问题修复

### 1. 拆分任务过多的计划

**原计划 10-02 (5 个任务)**:
- 拆分为 **10-02A** (2 个任务): 退出码映射表 + 认证验证
- 拆分为 **10-02B** (3 个任务): 下载验证 + 参数验证 + 结果记录

**原计划 10-03 (5 个任务)**:
- 拆分为 **10-03A** (2 个任务): 基本集成测试 + 下载集成测试
- 拆分为 **10-03B** (3 个任务): 批量下载测试 + 错误恢复测试 + 结果记录

### 2. 在 frontmatter 中定义 must_haves

所有计划现在都在 frontmatter 中明确定义了 `must_haves`,而非仅在文档正文中列出。

## 计划文件变更

### 修改的文件
- ✏️ `10-01-API-VALIDATION-PLAN.md` - 添加 frontmatter 和 XML 任务元素

### 新增的文件
- ➕ `10-02A-API-VALIDATION-PLAN.md` - 退出码映射表和认证验证 (从 10-02 拆分)
- ➕ `10-02B-API-VALIDATION-PLAN.md` - 下载和参数退出码验证 (从 10-02 拆分)
- ➕ `10-03A-API-VALIDATION-PLAN.md` - 基本和下载集成测试 (从 10-03 拆分)
- ➕ `10-03B-API-VALIDATION-PLAN.md` - 批量下载和错误恢复测试 (从 10-03 拆分)

### 删除的文件
- ❌ `10-02-API-VALIDATION-PLAN.md` - 已拆分为 10-02A 和 10-02B
- ❌ `10-03-API-VALIDATION-PLAN.md` - 已拆分为 10-03A 和 10-03B

## 最终计划结构

```
Phase 10 API 验证
├── Wave 1
│   └── 10-01: JSON 输出格式验证 (4 个任务)
├── Wave 2
│   ├── 10-02A: 退出码映射表和认证验证 (2 个任务) [依赖 10-01]
│   └── 10-02B: 下载和参数退出码验证 (3 个任务) [依赖 10-02A]
└── Wave 3
    ├── 10-03A: 基本和下载集成测试 (2 个任务) [依赖 10-01, 10-02B]
    └── 10-03B: 批量下载和错误恢复测试 (3 个任务) [依赖 10-03A]
```

## 验证清单

- ✅ 所有计划包含必需的 frontmatter 字段 (`phase`, `plan`, `type`, `must_haves`)
- ✅ 所有任务转换为 `<task>` XML 元素
- ✅ 没有计划超过 3 个任务
- ✅ `must_haves` 在 frontmatter 中定义
- ✅ 依赖关系正确更新 (10-02B 依赖 10-02A, 10-03A 依赖 10-02B)
- ✅ 旧的计划文件已删除

## 预期影响

1. **可执行性提升**: XML 任务元素提供清晰的结构,便于执行器解析
2. **质量保证**: 每个计划 2-3 个任务,避免执行器过载
3. **验证清晰**: `must_haves` 在 frontmatter 中明确定义,便于目标验证
4. **依赖清晰**: 拆分后的依赖关系更明确,执行顺序更合理

---

## 第二次修订 (2026-02-27)

### 修订原因
根据 GSD planner checker 的反馈,10-01-GAP01 存在以下问题:
- **requirement_coverage (blocker)**: 计划声明满足 VAL-01,但任务只修复导入路径
- **dependency_correctness (blocker)**: Gap closure 的 wave 为 1,没有依赖父计划 10-01
- **verification_derivation (warning)**: 缺少 must_haves frontmatter 结构

### 修复方案

#### 1. 更新 10-01-GAP01 frontmatter

**修改内容:**
```yaml
# 修改前
wave: 1
depends_on: []
requirements: [VAL-01]

# 修改后
wave: 2
depends_on: ["10-01"]
requirements: []
must_haves:
  truths:
    - 所有导入路径正确,无 ModuleNotFoundError
    - 所有 JSON Schema 测试通过 (9/9)
    - VAL-01 需求在父计划 10-01 中完全验证
  artifacts:
    - tests/validation/test_json_schemas.py (导入路径已修复)
    - pytest 测试报告显示 9/9 passed
  key_links:
    - VAL-01 需求在 10-01 计划中实现和验证
    - 本计划仅修复 10-01 执行后发现的导入路径错误
```

#### 2. 更新计划内容说明

- Goal 部分明确说明这是 gap closure,不实现 VAL-01
- Must-Haves 表格移除 VAL-01 相关条目
- Dependencies 部分明确说明依赖 10-01 (已完成,发现导入路径错误)
- Success Criteria 更新为确保 10-01 的 VAL-01 验证可正常执行

#### 3. 更新下游计划依赖

**修改的计划:**
- **10-02A**: `depends_on: ["10-01"]` → `depends_on: ["10-01-GAP01"]`
- **10-03A**: `depends_on: ["10-01", ...]` → `depends_on: ["10-01-GAP01", ...]`

**理由:**
- 确保下游计划在导入路径错误修复后执行
- 维护正确的执行顺序

### 修复后的执行顺序

```
Wave 1: 10-01 (JSON 输出格式验证)
  ↓
Wave 2: 10-01-GAP01 (修复导入路径错误)
  ↓
Wave 2: 10-02A (依赖 10-01-GAP01)
  ↓
Wave 3: 10-03A (依赖 10-01-GAP01 和 10-02B)
```

### 问题解决状态

| 问题 | 严重性 | 状态 |
|------|--------|------|
| requirement_coverage | blocker | ✅ 已解决 (移除 VAL-01) |
| dependency_correctness | blocker | ✅ 已解决 (wave: 2, depends_on: ["10-01"]) |
| verification_derivation | warning | ✅ 已解决 (添加 must_haves) |

### 文件变更列表

**修改的文件:**
1. `10-01-GAP01-PLAN.md` - 更新 frontmatter 和计划内容
2. `10-02A-API-VALIDATION-PLAN.md` - 更新依赖关系
3. `10-03A-API-VALIDATION-PLAN.md` - 更新依赖关系

### 预期影响

1. **角色明确**: 10-01-GAP01 明确为 gap closure,不实现需求
2. **依赖正确**: 设置正确的 wave 和依赖关系,确保执行顺序
3. **验证清晰**: 添加 must_haves 结构,明确验证标准
4. **下游一致**: 更新所有下游计划的依赖关系

---

## 第三次修订 (2026-02-27 - FINAL)

### 修订原因
根据 GSD planner checker (iteration 2/3) 的反馈,发现以下问题需要修复:

#### Blocker 问题
1. **10-01-GAP01**: `requirement_coverage` - Gap closure 计划未声明 requirements,无法追踪需求覆盖

#### Warning 问题
2. **10-02A**: `dependency_correctness` - Wave 编号为 2,但依赖 Wave 2 的 10-01-GAP01,应为 Wave 3
3. **10-02A**: `key_links_planned` - must_haves 中缺少 key_links 字段
4. **10-03A**: `key_links_planned` - must_haves 中缺少 key_links 字段
5. **10-02A**: `verification_derivation` - truths 中的 'EXIT_CODE_MAPPING 在 conftest.py 中定义' 是实现细节

### 修复方案

#### 1. 修复 10-01-GAP01 requirements 声明

**修改内容:**
```yaml
# 修改前
requirements: []

# 修改后
requirements: [VAL-01]

# 同时更新 truths 和 key_links
truths:
  - 测试文件中的导入语句能够成功加载所需模块
  - 所有 9 个 JSON Schema 测试用例执行并验证通过
  - 父计划 10-01 已实现 JSON Schema 验证功能并通过 VAL-01 验证
key_links:
  - VAL-01 需求在 10-01 计划中实现和验证
  - 本计划仅修复 10-01 执行后发现的导入路径错误,支持父计划完成 VAL-01 验证
```

**理由:**
- Gap closure 计划需要声明它支持的父计划需求
- 明确说明这是支持父计划完成 VAL-01 验证,而不是独立实现 VAL-01

#### 2. 修复 10-02A wave 编号和 key_links

**修改内容:**
```yaml
# 修改前
wave: 2
must_haves:
  exit_code_mapping_established: EXIT_CODE_MAPPING 在 conftest.py 中定义
  # ...

# 修改后
wave: 3
must_haves:
  exit_code_mapping_established: 退出码映射表在测试框架中定义并可访问
  # ...
  key_links:
    - 退出码映射表基于 INTEGRATION.md 和 error_codes.py 定义
    - 验证结果支持 VAL-02 需求(认证相关部分)
```

**理由:**
- Wave 编号应正确反映依赖关系 (10-01-GAP01 在 Wave 2,所以 10-02A 应在 Wave 3)
- truths 应避免实现细节,改为用户可观察的陈述
- 添加 key_links 说明与需求和文档的关系

#### 3. 修复 10-03A key_links

**修改内容:**
```yaml
# 修改前
must_haves:
  basic_integration_tests_implemented: version, status, config 命令可通过 subprocess 调用
  # ...

# 修改后
must_haves:
  basic_integration_tests_implemented: version, status, config 命令可通过 subprocess 调用
  # ...
  key_links:
    - 使用 subprocess 模拟第三方工具调用场景
    - 验证结果支持 VAL-03 需求(基本和下载部分)
```

**理由:**
- 添加 key_links 说明与需求的关系和验证场景

#### 4. 更新 PLANS-SUMMARY.md 反映完整阶段结构

**修改内容:**
- 更新计划总数为 6 (3 主计划 + 3 子计划)
- 添加 10-01-GAP01 gap closure 计划的详细信息
- 明确标注已完成和待执行的计划状态
- 更新 Wave 执行顺序和依赖关系图
- 更新需求覆盖表,反映实际完成状态

### 修复后的完整执行顺序

```
Wave 1:
  10-01 (JSON 输出格式验证) ✅ 已完成
    ↓
Wave 2:
  10-01-GAP01 (修复导入路径) ⏳ 待执行
    ↓
Wave 3:
  10-02A (认证退出码验证) ⏳ 待执行 [依赖 10-01-GAP01]
    ↓
  10-02B (下载/参数退出码验证) ✅ 已完成
    ↓
  10-03A (基本/下载集成测试) ⏳ 待执行 [依赖 10-01-GAP01 + 10-02B]
    ↓
  10-03B (批量/错误恢复集成测试) ✅ 已完成
```

### 问题解决状态

| 问题 | 计划 | 严重性 | 状态 |
|------|------|--------|------|
| requirement_coverage | 10-01-GAP01 | blocker | ✅ 已解决 (添加 requirements: [VAL-01]) |
| dependency_correctness | 10-02A | warning | ✅ 已解决 (更新 wave: 3) |
| key_links_planned | 10-02A | warning | ✅ 已解决 (添加 key_links) |
| key_links_planned | 10-03A | warning | ✅ 已解决 (添加 key_links) |
| verification_derivation | 10-02A | warning | ✅ 已解决 (修改 truths 避免实现细节) |

### 文件变更列表

**修改的文件:**
1. `10-01-GAP01-PLAN.md`
   - 更新 requirements: [VAL-01]
   - 更新 truths 和 key_links 说明
   - 明确说明支持父计划完成 VAL-01 验证

2. `10-02A-API-VALIDATION-PLAN.md`
   - 更新 wave: 3
   - 修改 exit_code_mapping_established 避免实现细节
   - 添加 key_links 字段

3. `10-03A-API-VALIDATION-PLAN.md`
   - 添加 key_links 字段

4. `10-PLANS-SUMMARY.md`
   - 更新计划总数和阶段结构
   - 添加 gap closure 计划信息
   - 更新执行顺序和依赖关系
   - 更新需求覆盖表

### 预期影响

1. **需求追踪**: 10-01-GAP01 现在正确声明支持 VAL-01,便于追踪需求覆盖
2. **Wave 正确**: 10-02A 的 wave 编号正确反映其依赖关系
3. **验证清晰**: 所有计划都有 key_links 字段,说明与需求和文档的关系
4. **避免实现细节**: truths 使用用户可观察的陈述,而非代码实现细节
5. **阶段结构完整**: PLANS-SUMMARY.md 反映完整的 6 计划结构(包括 gap closure)

### 验证清单

- ✅ 10-01-GAP01 声明 requirements: [VAL-01]
- ✅ 10-01-GAP01 的 truths 和 key_links 说明支持父计划
- ✅ 10-02A wave: 3 (正确反映依赖关系)
- ✅ 10-02A 添加 key_links 字段
- ✅ 10-02A truths 避免实现细节
- ✅ 10-03A 添加 key_links 字段
- ✅ PLANS-SUMMARY.md 更新为完整阶段结构
- ✅ 所有 checker 问题已解决

---

**修订完成日期:** 2026-02-27
**修订版本:** v3 (FINAL)
**下一步:** 执行 gap closure (10-01-GAP01)
