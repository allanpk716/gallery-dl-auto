# JSONL 输出格式支持设计

**日期**: 2026-03-03
**状态**: 已批准
**目标**: 为 pixiv-downloader 添加 JSONL 输出格式，节省 LLM Agent 调用的 token 消耗

## 背景

当前 pixiv-downloader 只支持 JSON 格式输出，使用 `indent=2` 的人类可读格式。在给 LLM Agent 调用时，缩进和换行符会产生大量不必要的 token 消耗。需要添加更紧凑的 JSONL 格式选项，同时保留现有的 JSON 格式给人类用户使用。

## 需求分析

**用户需求:**
- 给其他大语言模型的 agent 调用，需要节约 tokens
- 原有的 JSON 输出格式要保留，供人类查看
- 支持通过参数切换输出格式

**技术约束:**
- 保持向后兼容性（默认行为不变）
- 实现简单，风险可控
- 不影响底层逻辑和模型

## 设计方案

### 1. 参数设计

添加 `--format` 参数到 CLI：

```python
@click.option(
    "--format",
    type=click.Choice(["json", "jsonl"]),
    default="json",
    help="Output format: json (human-readable with indentation) or jsonl (compact single-line, for LLM agents)",
)
```

**设计要点:**
- 默认值：`json`（保持向后兼容）
- 支持值：`json`（带缩进，人类友好）和 `jsonl`（紧凑单行，节省 tokens）
- 帮助文档明确说明两种格式的用途

### 2. 实现逻辑

**输出格式化方式:**

```python
# JSON 格式（人类可读）
if format == "json":
    print(result.model_dump_json(indent=2, ensure_ascii=False))

# JSONL 格式（紧凑单行）
else:  # jsonl
    print(result.model_dump_json(indent=None, ensure_ascii=False, separators=(',', ':')))
```

**格式差异:**
- JSON：`indent=2`（多行，带缩进，易读）
- JSONL：`indent=None` + `separators=(',', ':')`（单行，去除所有空格）

**separators 参数说明:**
- `(',', ':')` 确保逗号和冒号后没有空格
- 这是 JSON 序列化的最紧凑形式

### 3. 修改范围

**主要修改文件:**
- `src/gallery_dl_auto/cli/download_cmd.py`

**需要修改的函数:**

1. `download()` - 添加 format 参数
   ```python
   def download(..., format: str) -> None:
   ```

2. `_download_with_gallery_dl()` - 添加 format 参数并修改输出逻辑
   - 位置：第 313 行
   - 修改：根据 format 选择输出格式

3. `_download_with_internal()` - 添加 format 参数并修改输出逻辑
   - 位置：第 437 行
   - 修改：根据 format 选择输出格式

4. `handle_interrupt()` - 信号处理器
   - 策略：统一使用 JSONL 格式输出错误信息
   - 理由：中断是异常情况，agent 调用时更需要紧凑输出

5. 所有错误输出位置 - 使用 `StructuredError.model_dump_json()`
   - 根据上下文选择格式（正常错误也使用对应 format）

### 4. 错误输出处理

**策略决策:**
- 正常结果输出：根据 `--format` 参数决定格式
- 中断错误输出：统一使用 JSONL 格式
  - 理由：信号处理器无法访问 format 参数
  - agent 调用时更需要紧凑的错误信息

**错误输出修改:**
```python
# handle_interrupt() 中
print(json.dumps({
    "success": False,
    "error": "USER_INTERRUPT",
    "message": "下载被用户中断,进度已保存",
    "suggestion": "重新运行相同命令将从断点继续下载"
}, ensure_ascii=False, separators=(',', ':')))
```

### 5. 架构设计

```
CLI Layer (download_cmd.py)
  ├─ 添加 --format 参数 (json/jsonl)
  ├─ 传递 format 到下载函数
  └─ 根据 format 选择输出格式
      ├─ json:  indent=2 (人类友好)
      └─ jsonl: indent=None + separators (节省 tokens)

数据流：
  用户命令 → parse --format → 执行下载 → 格式化输出
                                        ├─ json:  多行带缩进
                                        └─ jsonl: 单行紧凑
```

### 6. 测试策略

**测试范围:**

1. **单元测试** (`tests/cli/test_download_cmd.py`)
   - 测试 `--format json` 输出带缩进
   - 测试 `--format jsonl` 输出单行
   - 测试默认值（不指定 format）使用 json
   - 验证向后兼容性

2. **集成测试** (`tests/integration/`)
   - 验证 dry-run 模式下两种格式的输出
   - 验证实际下载时两种格式的输出
   - 验证错误情况下的输出格式

3. **验证测试** (`tests/validation/`)
   - 验证 JSONL 输出可以被 `json.loads()` 解析
   - 验证 JSONL 输出比 JSON 输出更小（token 数量更少）
   - 验证 JSONL 输出不包含换行符（除了末尾）

**测试重点:**
- JSONL 格式验证：无内部换行符、无多余空格
- 向后兼容性：不指定参数时行为完全不变
- 功能等价性：两种格式输出相同的数据结构

## 向后兼容性

**兼容性保证:**
- ✅ 默认值 `json`，不指定 `--format` 时行为完全不变
- ✅ 现有的 JSON 输出格式完全保持不变
- ✅ 所有现有测试不需要修改
- ✅ API 接口签名向后兼容（新增可选参数）

**升级路径:**
- 现有用户：无需任何改动，继续使用默认 JSON 格式
- Agent 调用：添加 `--format jsonl` 参数即可获得紧凑输出

## 预期效果

**Token 节省估算:**

典型输出示例（100 个作品的批量下载）：

- **JSON 格式** (indent=2):
  - 大小：~15KB
  - Token 数：~2000 tokens

- **JSONL 格式** (紧凑):
  - 大小：~9KB
  - Token 数：~1200 tokens
  - **节省：约 40%**

**典型输出对比:**

```json
// JSON 格式（人类可读）
{
  "success": true,
  "total": 100,
  "downloaded": 95,
  "failed": 5,
  "skipped": 0,
  "success_list": [
    123456,
    234567,
    345678
  ],
  "output_dir": "./pixiv-downloads"
}
```

```jsonl
// JSONL 格式（紧凑）
{"success":true,"total":100,"downloaded":95,"failed":5,"skipped":0,"success_list":[123456,234567,345678],"output_dir":"./pixiv-downloads"}
```

## 实施计划

### 阶段 1: 参数添加和函数签名修改
1. 添加 `--format` 参数到 `download()` 函数
2. 修改 `_download_with_gallery_dl()` 和 `_download_with_internal()` 签名
3. 传递 format 参数到各个函数

### 阶段 2: 输出逻辑修改
1. 修改 `_download_with_gallery_dl()` 的输出逻辑
2. 修改 `_download_with_internal()` 的输出逻辑
3. 修改错误处理函数的输出格式

### 阶段 3: 测试
1. 添加单元测试
2. 添加集成测试
3. 手动验证两种格式的输出

### 风险评估
- **技术风险**: 低（仅修改输出格式化逻辑）
- **兼容性风险**: 低（默认值保持不变）
- **测试风险**: 低（功能简单，易于验证）

## 备选方案

### 方案 2: 在模型层添加格式化方法
在 `BatchDownloadResult` 中添加 `to_json()` 和 `to_jsonl()` 方法。

**优点**: 格式化逻辑集中
**缺点**: 过度设计，实现复杂

### 方案 3: 使用输出格式化工具类
创建独立的 `OutputFormatter` 类处理不同格式。

**优点**: 职责分离清晰
**缺点**: 增加复杂度，对当前需求过于重量级

**选择理由**: 方案 1 最简单直接，JSONL 和 JSON 的区别只是格式化参数不同，不需要额外的抽象层。

## 总结

本设计通过添加 `--format` 参数，让用户可以在 JSON 和 JSONL 两种输出格式间切换。JSON 格式保持人类可读性，JSONL 格式节省约 40% 的 tokens，非常适合 LLM Agent 调用场景。实现简单，向后兼容，风险可控。
