---
phase: '10'
plan: '03B'
type: auto
wave: 3
depends_on:
  - 10-03A
files_modified:
  - tests/validation/test_integration.py
  - tests/validation/VALIDATION_RESULTS.md
requirements:
  - VAL-03
must_haves:
  batch_download_tests_implemented: 可批量下载多个排行榜类型
  error_recovery_tests_implemented: 超时和中断处理经过验证
  all_tests_pass: pytest tests/validation/test_integration.py -v 显示所有测试通过
  val03_satisfied: 可以展示第三方工具调用场景经过验证的证据
autonomous: true
---

# Plan 10-03B: 集成测试 (批量下载和错误恢复)

**Goal**: 验证批量下载和错误恢复机制,完成所有集成测试

**Context**:
- 10-03A 已实现基本和下载集成测试
- 当前需要验证批量下载多个排行榜的可靠性
- 需要验证错误恢复机制和超时处理

**Requirements met**:
- VAL-03: 第三方工具调用场景经过集成测试验证,真实场景下工作可靠

---

## Tasks

<task id="1">
<name>实现批量下载集成测试</name>
<goal>验证批量下载多个排行榜的可靠性</goal>
<files>
- C:/WorkSpace/gallery-dl-auto/tests/validation/test_integration.py (更新)
</files>
<action>
1. 实现 test_subprocess_batch_download 测试:
   - 下载多个排行榜类型 (daily, weekly)
   - 验证每个命令执行成功
   - 验证输出格式一致

2. 模拟第三方工具批量调用:
   ```python
   def test_subprocess_batch_download(self, tmp_path):
       output_dir = tmp_path / "downloads"
       ranking_types = ["daily", "weekly"]

       results = []
       for ranking_type in ranking_types:
           result = subprocess.run(
               ["pixiv-downloader", "--quiet", "download", "--type", ranking_type, "--output", str(output_dir)],
               capture_output=True,
               text=True,
               encoding='utf-8',
               timeout=60
           )
           results.append({
               "type": ranking_type,
               "returncode": result.returncode,
               "stdout": result.stdout,
               "stderr": result.stderr
           })

       # 验证所有命令执行完成
       for result in results:
           assert result["returncode"] == 0, f"{result['type']} 下载失败"
   ```

3. 验证速率限制保护:
   - 在批量调用之间添加适当延迟
   - 验证不会触发速率限制
</action>
<verify>
```bash
# 运行批量下载测试
pytest tests/validation/test_integration.py::TestThirdPartyIntegration::test_subprocess_batch_download -v
```
</verify>
<done>批量下载测试已实现,可批量下载多个排行榜类型</done>
</task>

<task id="2">
<name>实现错误恢复机制测试</name>
<goal>验证错误恢复机制和超时处理</goal>
<files>
- C:/WorkSpace/gallery-dl-auto/tests/validation/test_integration.py (更新)
</files>
<action>
1. 实现 TestErrorRecovery 测试类:
   - test_timeout_handling: 验证长时间运行命令的超时处理
   - test_interrupt_handling: 验证 Ctrl+C 中断处理 (Windows 上可能需要跳过)

2. 测试超时处理:
   ```python
   def test_timeout_handling(self):
       # 模拟第三方工具设置超时
       with pytest.raises(subprocess.TimeoutExpired):
           subprocess.run(
               ["pixiv-downloader", "download", "--type", "daily"],
               capture_output=True,
               timeout=1  # 1 秒超时 (预期会超时)
           )
   ```

3. 测试中断处理 (可选,Windows 上可能不可用):
   ```python
   @pytest.mark.skipif(sys.platform == "win32", reason="Signal handling differs on Windows")
   def test_interrupt_handling(self):
       process = subprocess.Popen(
           ["pixiv-downloader", "download", "--type", "daily"],
           stdout=subprocess.PIPE,
           stderr=subprocess.PIPE,
           text=True
       )

       # 发送 SIGINT (Ctrl+C)
       process.send_signal(subprocess.signal.SIGINT)

       stdout, stderr = process.communicate(timeout=5)

       # 验证退出码 130 (128 + SIGINT)
       assert process.returncode == 130
   ```
</action>
<verify>
```bash
# 运行错误恢复测试
pytest tests/validation/test_integration.py::TestErrorRecovery -v
```
</verify>
<done>错误恢复测试已实现,超时和中断处理经过验证</done>
</task>

<task id="3">
<name>运行完整集成测试并记录结果</name>
<goal>运行所有集成测试,记录结果和发现的问题</goal>
<files>
- C:/WorkSpace/gallery-dl-auto/src/gallery_dl_auo/cli/*.py (修复问题)
- C:/WorkSpace/gallery-dl-auto/tests/validation/VALIDATION_RESULTS.md (最终更新)
</files>
<action>
1. 运行完整的集成测试套件:
   ```bash
   pytest tests/validation/test_integration.py -v --tb=short
   ```

2. 分析测试失败原因:
   - subprocess 调用失败: 命令未找到、权限问题、路径问题
   - JSON 解析失败: 输出包含非 JSON 内容
   - 超时或中断处理失败: Windows 特定行为

3. 修复发现的问题:
   - 更新 CLI 命令实现
   - 调整超时时间
   - 标记平台特定测试

4. 更新 tests/validation/VALIDATION_RESULTS.md:
   - 记录每个集成场景的验证状态
   - 记录发现的问题和修复措施
   - 记录平台差异 (Windows vs Unix)

5. 生成最终验证报告:
   ```markdown
   # Phase 10 API 验证报告

   ## VAL-01: JSON 输出格式验证
   - 状态: ✅ 通过
   - 测试覆盖: X 个命令
   - 发现问题: Y 个 (已修复)

   ## VAL-02: 退出码验证
   - 状态: ✅ 通过
   - 测试覆盖: X 个错误场景
   - 发现问题: Y 个 (已修复)

   ## VAL-03: 集成测试
   - 状态: ✅ 通过
   - 测试覆盖: X 个集成场景
   - 发现问题: Y 个 (已修复)
   ```

6. 重新运行所有验证测试,确保通过:
   ```bash
   pytest tests/validation/ -v --cov=gallery_dl_auo.cli
   ```
</action>
<verify>
```bash
# 所有验证测试通过
pytest tests/validation/ -v
# 应看到: X passed, Y warnings

# 手动验证集成场景
pixiv-downloader --json-output version | jq .
pixiv-downloader --json-output download --type daily
echo $?  # 检查退出码
```
</verify>
<done>所有集成测试通过,VAL-03 需求完全满足,Phase 10 所有验证需求全部满足</done>
</task>

---

## Must-haves (Goal-backward verification)

执行此计划后,以下条件必须为 TRUE:

1. ✅ **批量下载测试已实现**: 可批量下载多个排行榜类型
2. ✅ **错误恢复测试已实现**: 超时和中断处理经过验证
3. ✅ **所有测试通过**: pytest tests/validation/test_integration.py -v 显示所有测试通过
4. ✅ **VAL-03 需求满足**: 可以展示第三方工具调用场景经过验证的证据

**验证命令**:
```bash
# 验证所有 must-haves
pytest tests/validation/ -v && \
echo "✅ 所有 API 验证测试通过 (VAL-01, VAL-02, VAL-03)"
```

---

## Dependencies

**Depends on**:
- 10-03A (基本和下载集成测试): 需要本计划建立的基础设施

**Blocks**: 无 (Wave 3,最后一个计划)

---

## Risk mitigation

**风险 1: 批量测试触发速率限制**
- 缓解措施: 在测试中添加适当延迟 (time.sleep)
- 回滚策略: 标记速率限制测试为手动测试

**风险 2: 超时和中断测试不稳定**
- 缓解措施: 设置合理的超时时间,捕获异常
- 回滚策略: 跳过不稳定测试,在 VALIDATION_RESULTS.md 中说明

**风险 3: subprocess 调用在 Windows 上失败**
- 缓解措施: 显式指定 encoding='utf-8',使用绝对路径
- 回滚策略: 标记 Windows 特定测试为 @pytest.mark.skipif

---

## Notes

- 本计划专注于批量下载和错误恢复测试
- 依赖 10-03A 建立的基础设施
- 测试结果将记录在 tests/validation/VALIDATION_RESULTS.md
- 完成本计划后,Phase 10 所有验证需求 (VAL-01, VAL-02, VAL-03) 将全部满足
