---
phase: '10'
plan: '02B'
type: auto
wave: 2
depends_on:
  - 10-02A
files_modified:
  - tests/validation/test_exit_codes.py
  - tests/validation/VALIDATION_RESULTS.md
requirements:
  - VAL-02
must_haves:
  download_exit_codes_verified: TestDownloadExitCodes 所有测试通过
  argument_exit_codes_verified: TestArgumentExitCodes 所有测试通过
  all_tests_pass: pytest tests/validation/test_exit_codes.py -v 显示所有测试通过
  val02_satisfied: 可以展示所有退出码经过验证的证据
autonomous: true
---

# Plan 10-02B: 退出码验证 (下载和参数)

**Goal**: 验证下载命令和参数错误场景的退出码,完成所有退出码验证

**Context**:
- 10-02A 已建立退出码映射表
- 10-02A 已验证认证相关退出码
- 当前需要验证下载命令在不同场景下的退出码
- 需要验证参数错误场景的退出码

**Requirements met**:
- VAL-02: 所有退出码经过验证,与文档说明完全一致,第三方工具可依赖退出码判断执行状态

---

## Tasks

<task id="1">
<name>实现下载相关退出码验证</name>
<goal>验证下载命令在不同场景下的退出码</goal>
<files>
- C:/WorkSpace/gallery-dl-auto/tests/validation/test_exit_codes.py (更新)
</files>
<action>
1. 实现 TestDownloadExitCodes 测试类:
   - test_success_exit_code: 验证完全成功时返回退出码 0
   - test_partial_success_exit_code: 验证部分成功时返回退出码 1
   - test_complete_failure_exit_code: 验证完全失败时返回退出码 2

2. 使用 Mock fixtures 模拟不同下载结果:
   ```python
   @pytest.fixture
   def mock_successful_download(monkeypatch):
       """Mock 成功下载场景"""
       result = BatchDownloadResult(
           success=True,
           total=10,
           downloaded=10,
           failed=0,
           skipped=0,
           success_list=[1, 2, 3, 4, 5, 6, 7, 8, 9, 10],
           failed_errors=[],
           output_dir="/tmp/downloads"
       )
       monkeypatch.setattr("gallery_dl_auo.cli.download.download_ranking", lambda *args: result)
   ```

3. 验证退出码逻辑:
   ```python
   def test_partial_success_exit_code(self, runner, mock_partial_download):
       result = runner.invoke(cli, ["download", "--type", "daily"])
       assert result.exit_code == EXIT_CODE_MAPPING["PARTIAL_SUCCESS"]
       assert result.exit_code == 1
   ```
</action>
<verify>
```bash
# 运行下载退出码测试
pytest tests/validation/test_exit_codes.py::TestDownloadExitCodes -v
```
</verify>
<done>下载相关退出码验证测试已实现并全部通过</done>
</task>

<task id="2">
<name>实现参数错误退出码验证</name>
<goal>验证参数错误返回正确的退出码</goal>
<files>
- C:/WorkSpace/gallery-dl-auto/tests/validation/test_exit_codes.py (更新)
</files>
<action>
1. 实现 TestArgumentExitCodes 测试类:
   - test_invalid_ranking_type: 验证无效排行榜类型返回退出码 2
   - test_invalid_date_format: 验证无效日期格式返回退出码 2
   - test_missing_required_argument: 验证缺少必需参数返回退出码 2

2. 测试 Click 框架的参数验证:
   ```python
   def test_invalid_ranking_type(self, runner):
       result = runner.invoke(cli, ["download", "--type", "invalid_type"])
       assert result.exit_code == 2  # Click 参数错误
       assert "Invalid value" in result.output or "Error" in result.output
   ```

3. 测试自定义参数验证:
   ```python
   def test_invalid_date_format(self, runner):
       result = runner.invoke(cli, ["download", "--type", "daily", "--date", "invalid-date"])
       assert result.exit_code == 2
       assert "INVALID_DATE_FORMAT" in result.output
   ```
</action>
<verify>
```bash
# 运行参数错误退出码测试
pytest tests/validation/test_exit_codes.py::TestArgumentExitCodes -v
```
</verify>
<done>参数错误退出码验证测试已实现并全部通过</done>
</task>

<task id="3">
<name>验证所有退出码并记录结果</name>
<goal>运行完整的退出码验证测试,记录结果</goal>
<files>
- C:/WorkSpace/gallery-dl-auto/src/gallery_dl_auo/cli/*.py (修复问题)
- C:/WorkSpace/gallery-dl-auto/tests/validation/VALIDATION_RESULTS.md (更新)
</files>
<action>
1. 运行完整的退出码验证测试:
   ```bash
   pytest tests/validation/test_exit_codes.py -v --tb=short
   ```

2. 分析测试失败原因:
   - 退出码与映射表不一致: 更新代码或更新映射表
   - 错误码字符串不在输出中: 更新错误处理逻辑
   - Click 框架返回不同退出码: 确认是 Click 行为还是自定义行为

3. 修复发现的问题:
   - 统一使用 ctx.exit(code) 或 sys.exit(code)
   - 确保错误处理中包含错误码字符串
   - 更新 INTEGRATION.md 如果发现文档与实际不一致

4. 更新 tests/validation/VALIDATION_RESULTS.md:
   - 记录每个错误场景的验证状态
   - 记录发现的问题和修复措施
   - 标注未验证的错误场景 (低频错误)

5. 重新运行测试,确保所有测试通过:
   ```bash
   pytest tests/validation/test_exit_codes.py -v
   ```
</action>
<verify>
```bash
# 所有测试通过
pytest tests/validation/test_exit_codes.py -v
# 应看到: X passed, Y warnings

# 手动验证退出码
pixiv-downloader download --type invalid_type
echo $?  # 应输出: 2
```
</verify>
<done>所有退出码验证测试通过,VAL-02 需求完全满足</done>
</task>

---

## Must-haves (Goal-backward verification)

执行此计划后,以下条件必须为 TRUE:

1. ✅ **下载退出码已验证**: TestDownloadExitCodes 所有测试通过
2. ✅ **参数错误退出码已验证**: TestArgumentExitCodes 所有测试通过
3. ✅ **所有测试通过**: pytest tests/validation/test_exit_codes.py -v 显示所有测试通过
4. ✅ **VAL-02 需求满足**: 可以展示所有退出码经过验证的证据

**验证命令**:
```bash
# 验证所有 must-haves
pytest tests/validation/test_exit_codes.py -v && \
echo "✅ 所有退出码验证测试通过"
```

---

## Dependencies

**Depends on**:
- 10-02A (退出码映射表和认证验证): 需要本计划建立的退出码映射表

**Blocks**:
- 10-03 (集成测试): 需要本计划验证的退出码映射表

---

## Risk mitigation

**风险 1: 部分下载场景难以在测试中模拟**
- 缓解措施: 优先验证高频下载场景,低频场景可手动验证或标记为 @pytest.mark.skip
- 回滚策略: 记录未验证的场景,在 VALIDATION_RESULTS.md 中标注

**风险 2: Click 框架的默认退出码与预期不一致**
- 缓解措施: 在测试中验证实际退出码,根据实际情况更新映射表
- 回滚策略: 更新 INTEGRATION.md 以反映实际行为

**风险 3: Windows 和 Unix 系统退出码行为不同**
- 缓解措施: 在 Windows 上运行测试,确保一致性
- 回滚策略: 记录平台差异,在文档中说明

---

## Notes

- 本计划专注于下载和参数错误退出码验证
- 依赖 10-02A 建立的退出码映射表
- 测试结果将记录在 tests/validation/VALIDATION_RESULTS.md
- 完成本计划后,VAL-02 需求将完全满足
