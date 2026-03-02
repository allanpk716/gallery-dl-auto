# Mode 映射修复 - 最终验证命令

**日期**: 2026-03-02
**版本**: v1.3

---

## 快速验证

### 1. 核心功能测试 (R18 排行榜)

**测试目标**: 验证所有 R18 mode 都能正常工作

```bash
# 测试 day_male_r18 (关键修复)
pixiv-downloader download --type day_male_r18 --limit 1 --dry-run

# 测试 day_female_r18
pixiv-downloader download --type day_female_r18 --limit 1 --dry-run

# 测试 day_r18
pixiv-downloader download --type day_r18 --limit 1 --dry-run

# 测试 week_r18
pixiv-downloader download --type week_r18 --limit 1 --dry-run

# 测试 week_r18g
pixiv-downloader download --type week_r18g --limit 1 --dry-run
```

**预期结果**:
- 所有命令成功执行 (exit code 0)
- 输出包含 `"dry_run": true`
- 没有任何 "Invalid mode" 错误

---

### 2. 向后兼容性测试

**测试目标**: 验证旧的 CLI 调用方式仍然有效

```bash
# 使用 CLI 名称
pixiv-downloader download --type daily --limit 1 --dry-run
pixiv-downloader download --type weekly --limit 1 --dry-run
pixiv-downloader download --type monthly --limit 1 --dry-run

# 使用 API 名称
pixiv-downloader download --type day --limit 1 --dry-run
pixiv-downloader download --type week --limit 1 --dry-run
pixiv-downloader download --type month --limit 1 --dry-run

# 使用分类 mode
pixiv-downloader download --type day_male --limit 1 --dry-run
pixiv-downloader download --type day_female --limit 1 --dry-run
pixiv-downloader download --type week_original --limit 1 --dry-run
pixiv-downloader download --type week_rookie --limit 1 --dry-run
```

**预期结果**:
- 所有命令成功执行
- CLI 名称和 API 名称都能正常工作

---

### 3. 错误处理测试

**测试目标**: 验证无效 mode 的错误提示友好

```bash
# 测试无效 mode
pixiv-downloader download --type invalid_mode --limit 1 --dry-run
```

**预期结果**:
- 命令失败 (exit code != 0)
- 错误消息包含 "Invalid ranking type 'invalid_mode'"
- 错误消息列出所有有效的 mode 选项
- 错误消息同时包含 CLI 名称和 API 名称

**示例输出**:
```
Error: Invalid ranking type 'invalid_mode'. Valid types: day, day_female,
day_female_r18, day_male, day_male_r18, day_r18, daily, month, monthly,
week, week_original, week_rookie, week_r18, week_r18g, weekly
```

---

### 4. 单元测试验证

**测试目标**: 验证所有核心单元测试通过

```bash
# 运行 ModeManager 单元测试
pytest tests/core/test_mode_manager.py -v

# 运行 gallery-dl wrapper 集成测试
pytest tests/integration/test_gallery_dl_wrapper.py -v

# 运行所有核心测试
pytest tests/core/ tests/integration/test_gallery_dl_wrapper.py -v
```

**预期结果**:
- 所有测试通过 (27 个测试)
- 没有失败的测试
- 没有错误

---

### 5. 代码覆盖率检查

**测试目标**: 验证核心功能有足够的测试覆盖

```bash
# 运行测试并生成覆盖率报告
pytest tests/core/ tests/integration/test_gallery_dl_wrapper.py \
    --cov=src/gallery_dl_auto/core \
    --cov=src/gallery_dl_auto/integration \
    --cov-report=term-missing
```

**预期结果**:
- mode_manager.py 覆盖率 >= 95%
- mode_errors.py 覆盖率 = 100%
- gallery_dl_wrapper.py 覆盖率 >= 90%

---

## 完整验证脚本

将以下脚本保存为 `verify_fix.sh` (Linux/Mac) 或 `verify_fix.bat` (Windows):

### Linux/Mac (verify_fix.sh)

```bash
#!/bin/bash

echo "=== Mode 映射修复验证脚本 ==="
echo ""

# 1. 单元测试
echo "1. 运行单元测试..."
pytest tests/core/ tests/integration/test_gallery_dl_wrapper.py -v
if [ $? -ne 0 ]; then
    echo "❌ 单元测试失败"
    exit 1
fi
echo "✅ 单元测试通过"
echo ""

# 2. R18 mode 测试
echo "2. 测试 R18 排行榜..."
for mode in day_r18 day_male_r18 day_female_r18 week_r18 week_r18g; do
    echo "  Testing $mode..."
    pixiv-downloader download --type $mode --limit 1 --dry-run > /dev/null 2>&1
    if [ $? -ne 0 ]; then
        echo "  ❌ $mode 测试失败"
        exit 1
    fi
    echo "  ✅ $mode 测试通过"
done
echo ""

# 3. 向后兼容性测试
echo "3. 测试向后兼容性..."
for mode in daily weekly monthly; do
    echo "  Testing $mode..."
    pixiv-downloader download --type $mode --limit 1 --dry-run > /dev/null 2>&1
    if [ $? -ne 0 ]; then
        echo "  ❌ $mode 测试失败"
        exit 1
    fi
    echo "  ✅ $mode 测试通过"
done
echo ""

echo "=== 所有验证通过 ✅ ==="
```

### Windows (verify_fix.bat)

```batch
@echo off
echo === Mode 映射修复验证脚本 ===
echo.

echo 1. 运行单元测试...
pytest tests/core/ tests/integration/test_gallery_dl_wrapper.py -v
if errorlevel 1 (
    echo ❌ 单元测试失败
    exit /b 1
)
echo ✅ 单元测试通过
echo.

echo 2. 测试 R18 排行榜...
for %%m in (day_r18 day_male_r18 day_female_r18 week_r18 week_r18g) do (
    echo   Testing %%m...
    pixiv-downloader download --type %%m --limit 1 --dry-run > nul 2>&1
    if errorlevel 1 (
        echo   ❌ %%m 测试失败
        exit /b 1
    )
    echo   ✅ %%m 测试通过
)
echo.

echo 3. 测试向后兼容性...
for %%m in (daily weekly monthly) do (
    echo   Testing %%m...
    pixiv-downloader download --type %%m --limit 1 --dry-run > nul 2>&1
    if errorlevel 1 (
        echo   ❌ %%m 测试失败
        exit /b 1
    )
    echo   ✅ %%m 测试通过
)
echo.

echo === 所有验证通过 ✅ ===
```

---

## 验证清单

完成以下所有检查项即可确认修复成功:

- [ ] **单元测试**: 所有 27 个核心测试通过
- [ ] **R18 mode**: 5 种 R18 排行榜都能正常下载
- [ ] **向后兼容**: CLI 名称 (daily) 和 API 名称 (day) 都能工作
- [ ] **错误提示**: 无效 mode 显示友好的错误消息
- [ ] **代码覆盖**: 核心模块覆盖率 >= 95%
- [ ] **文档更新**: CLI 帮助文本已更新

---

## 预期时间

- **快速验证**: 5-10 分钟 (仅核心功能)
- **完整验证**: 15-20 分钟 (包含所有测试)

---

## 故障排除

### 问题 1: 单元测试失败

**可能原因**:
- 依赖未安装
- 代码未正确部署

**解决方案**:
```bash
pip install -e .
pytest tests/core/ -v
```

### 问题 2: R18 mode 仍然失败

**可能原因**:
- gallery-dl 版本过低
- ModeManager 未正确集成

**解决方案**:
```bash
pip install --upgrade gallery-dl>=1.28.0
python -c "from gallery_dl_auto.core import ModeManager; print(ModeManager.api_to_gallery_dl('day_male_r18'))"
```

### 问题 3: Token 无效

**可能原因**:
- Token 过期
- 未登录

**解决方案**:
```bash
pixiv-downloader login
```

---

## 成功标志

当您看到以下输出时,表示修复成功:

```
$ pixiv-downloader download --type day_male_r18 --limit 1 --dry-run

{
  "dry_run": true,
  "mode": "day_male_r18",
  "date": null,
  "limit": 1,
  "offset": 0,
  "total_works": 1,
  "works": [
    {
      "rank": 1,
      "illust_id": 12345678,
      "title": "作品标题",
      "author": "作者名"
    }
  ]
}
```

**关键指标**:
- ✅ 没有任何 "Invalid mode" 错误
- ✅ 成功返回排行榜数据
- ✅ JSON 输出格式正确

---

**文档生成时间**: 2026-03-02
