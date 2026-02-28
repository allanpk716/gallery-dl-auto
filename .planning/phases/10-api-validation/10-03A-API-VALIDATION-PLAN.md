---
phase: '10'
plan: '03A'
type: auto
wave: 3
depends_on:
  - 10-01-GAP01
  - 10-02B
files_modified:
  - tests/validation/test_integration.py
  - tests/validation/conftest.py
requirements:
  - VAL-03
must_haves:
  basic_integration_tests_implemented: version, status, config 命令可通过 subprocess 调用
  download_integration_tests_implemented: download 命令在成功和错误场景下工作正常
  all_tests_pass: pytest tests/validation/test_integration.py -v 显示基本和下载测试通过
  val03_partial: 基本和下载集成测试经过验证
  key_links:
    - 使用 subprocess 模拟第三方工具调用场景
    - 验证结果支持 VAL-03 需求(基本和下载部分)
autonomous: true
---

# Plan 10-03A: 集成测试 (基本和下载)

**Goal**: 使用 subprocess 模拟第三方工具调用,验证基本命令和下载命令的集成

**Context**:
- 10-01 已验证 JSON 输出格式符合规范
- 10-02B 已验证退出码与文档一致
- 当前缺少真实场景的集成测试,无法保证第三方工具调用的可靠性
- 需要使用 subprocess 模拟第三方工具调用,验证端到端集成

**Requirements met**:
- VAL-03 (部分): 基本命令和下载命令的第三方工具调用场景经过集成测试验证

---

## Tasks

<task id="1">
<name>实现基本 subprocess 集成测试</name>
<goal>使用 subprocess 模拟第三方工具调用,验证基本功能</goal>
<files>
- C:/WorkSpace/gallery-dl-auto/tests/validation/test_integration.py (新建)
</files>
<action>
1. 创建 tests/validation/test_integration.py

2. 实现 TestThirdPartyIntegration 测试类:
   - test_subprocess_version_command: 验证 version 命令
   - test_subprocess_status_command: 验证 status 命令
   - test_subprocess_config_command: 验证 config 命令

3. 使用 subprocess.run 调用 CLI:
   ```python
   def test_subprocess_version_command(self):
       result = subprocess.run(
           ["pixiv-downloader", "--json-output", "version"],
           capture_output=True,
           text=True,
           encoding='utf-8',  # Windows 必需
           timeout=10
       )

       assert result.returncode == 0

       # 验证 stdout 是有效 JSON
       output = json.loads(result.stdout)
       assert "version" in output
   ```

4. 处理 Windows 编码问题:
   - 显式指定 encoding='utf-8'
   - 验证输出不包含乱码
</action>
<verify>
```bash
# 运行基本集成测试
pytest tests/validation/test_integration.py::TestThirdPartyIntegration::test_subprocess_version_command -v
```
</verify>
<done>基本集成测试已实现,version/status/config 命令可通过 subprocess 调用</done>
</task>

<task id="2">
<name>实现下载命令集成测试</name>
<goal>验证下载命令在第三方工具调用场景下的行为</goal>
<files>
- C:/WorkSpace/gallery-dl-auto/tests/validation/test_integration.py (更新)
</files>
<action>
1. 在 TestThirdPartyIntegration 中添加下载测试:
   - test_subprocess_download_success: 验证成功下载场景
   - test_subprocess_no_token_error: 验证认证错误处理
   - test_subprocess_invalid_argument: 验证参数错误处理

2. 使用 tmp_path fixture 隔离文件系统:
   ```python
   def test_subprocess_download_success(self, tmp_path):
       output_dir = tmp_path / "downloads"

       result = subprocess.run(
           ["pixiv-downloader", "--json-output", "download", "--type", "daily", "--output", str(output_dir)],
           capture_output=True,
           text=True,
           encoding='utf-8',
           timeout=60
       )

       assert result.returncode == 0

       output = json.loads(result.stdout)
       assert "success" in output
       assert "total" in output
   ```

3. 验证错误场景:
   ```python
   def test_subprocess_no_token_error(self):
       result = subprocess.run(
           ["pixiv-downloader", "--json-output", "download", "--type", "daily"],
           capture_output=True,
           text=True,
           encoding='utf-8',
           timeout=10
       )

       assert result.returncode != 0

       # 验证错误输出是有效 JSON
       output_text = result.stdout if result.stdout else result.stderr
       error = json.loads(output_text)

       assert "error_code" in error
       assert error["error_code"] == "AUTH_TOKEN_NOT_FOUND"
   ```
</action>
<verify>
```bash
# 运行下载集成测试
pytest tests/validation/test_integration.py::TestThirdPartyIntegration::test_subprocess_download_success -v
```
</verify>
<done>下载集成测试已实现,download 命令在成功和错误场景下工作正常</done>
</task>

---

## Must-haves (Goal-backward verification)

执行此计划后,以下条件必须为 TRUE:

1. ✅ **基本集成测试已实现**: version, status, config 命令可通过 subprocess 调用
2. ✅ **下载集成测试已实现**: download 命令在成功和错误场景下工作正常
3. ✅ **测试通过**: pytest tests/validation/test_integration.py -v 显示基本和下载测试通过
4. ✅ **VAL-03 需求部分满足**: 可以展示基本和下载集成测试经过验证的证据

**验证命令**:
```bash
# 验证所有 must-haves
pytest tests/validation/test_integration.py::TestThirdPartyIntegration -v && \
echo "✅ 基本和下载集成测试通过"
```

---

## Dependencies

**Depends on**:
- 10-01 (JSON 输出格式验证): 需要 JSON Schema 和测试框架
- 10-02B (退出码验证): 需要退出码映射表

**Blocks**:
- 10-03B (批量下载和错误恢复测试): 需要本计划建立的基础设施

---

## Risk mitigation

**风险 1: subprocess 调用在 Windows 上失败**
- 缓解措施: 显式指定 encoding='utf-8',使用绝对路径
- 回滚策略: 标记 Windows 特定测试为 @pytest.mark.skipif

**风险 2: 集成测试依赖真实环境和 token**
- 缓解措施: 使用 tmp_path 隔离文件系统,Mock API 调用
- 回滚策略: 标记依赖真实环境的测试为 @pytest.mark.integration

---

## Notes

- 本计划专注于基本命令和下载命令的 subprocess 集成测试
- 批量下载和错误恢复测试在 10-03B 中进行
- 测试结果将记录在 tests/validation/VALIDATION_RESULTS.md
