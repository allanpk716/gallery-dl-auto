---
phase: '10'
plan: '02A'
type: auto
wave: 3
depends_on:
  - 10-01-GAP01
files_modified:
  - tests/validation/test_exit_codes.py
  - tests/validation/conftest.py
requirements:
  - VAL-02
must_haves:
  exit_code_mapping_established: 退出码映射表在测试框架中定义并可访问
  auth_exit_codes_verified: TestAuthExitCodes 所有测试通过
  all_tests_pass: pytest tests/validation/test_exit_codes.py -v 显示认证相关测试通过
  val02_partial: 认证相关退出码经过验证
  key_links:
    - 退出码映射表基于 INTEGRATION.md 和 error_codes.py 定义
    - 验证结果支持 VAL-02 需求(认证相关部分)
autonomous: true
---

# Plan 10-02A: 退出码验证 (认证相关)

**Goal**: 建立退出码映射表,验证认证错误场景返回正确的退出码

**Context**:
- Phase 7 已实现结构化错误码系统 (src/gallery_dl_auo/utils/error_codes.py)
- Phase 9 已在 INTEGRATION.md 中记录完整的退出码文档
- 当前缺少系统化的退出码验证,无法保证退出码与文档一致
- 需要先建立退出码映射表,然后验证认证相关退出码

**Requirements met**:
- VAL-02 (部分): 认证相关退出码经过验证,与文档说明完全一致

---

## Tasks

<task id="1">
<name>建立退出码映射表</name>
<goal>基于 INTEGRATION.md 和 error_codes.py,创建退出码映射表</goal>
<files>
- C:/WorkSpace/gallery-dl-auto/tests/validation/conftest.py (更新)
</files>
<action>
1. 在 tests/validation/conftest.py 中定义 EXIT_CODE_MAPPING 常量:
   ```python
   # 退出码映射表 (基于 INTEGRATION.md 和 error_codes.py)
   EXIT_CODE_MAPPING = {
       # 成功场景
       "SUCCESS": 0,

       # 认证错误 (stderr 包含错误码)
       "AUTH_TOKEN_NOT_FOUND": 1,
       "AUTH_TOKEN_EXPIRED": 1,
       "AUTH_TOKEN_INVALID": 1,
       "AUTH_REFRESH_FAILED": 1,

       # API 错误
       "API_NETWORK_ERROR": 1,
       "API_RATE_LIMIT": 1,
       "API_SERVER_ERROR": 1,
       "API_INVALID_RESPONSE": 1,

       # 下载错误
       "DOWNLOAD_FAILED": 1,
       "DOWNLOAD_TIMEOUT": 1,
       "DOWNLOAD_PERMISSION_DENIED": 1,

       # 参数错误
       "INVALID_ARGUMENT": 2,
       "INVALID_DATE_FORMAT": 2,

       # 下载结果状态
       "PARTIAL_SUCCESS": 1,  # 部分下载成功
       "COMPLETE_FAILURE": 2,  # 完全失败
   }
   ```

2. 验证映射表与 INTEGRATION.md 一致:
   - 对比 INTEGRATION.md 中 "退出码参考" 章节
   - 确保所有文档中提到的错误码都包含在映射表中
   - 记录映射表中的退出码含义注释

3. 创建退出码验证辅助函数:
   ```python
   def verify_exit_code(result, expected_error_code: str):
       """验证退出码和错误码是否匹配"""
       expected_exit_code = EXIT_CODE_MAPPING[expected_error_code]
       assert result.exit_code == expected_exit_code, \
           f"Expected exit code {expected_exit_code}, got {result.exit_code}"
   ```
</action>
<verify>
```python
# 验证映射表完整性
from tests.validation.conftest import EXIT_CODE_MAPPING

# 检查所有错误码都有映射
assert "AUTH_TOKEN_NOT_FOUND" in EXIT_CODE_MAPPING
assert "SUCCESS" in EXIT_CODE_MAPPING
assert EXIT_CODE_MAPPING["SUCCESS"] == 0
```
</verify>
<done>退出码映射表已建立,所有错误码都有明确定义</done>
</task>

<task id="2">
<name>实现认证相关退出码验证</name>
<goal>验证认证错误场景返回正确的退出码</goal>
<files>
- C:/WorkSpace/gallery-dl-auto/tests/validation/test_exit_codes.py (新建)
- C:/WorkSpace/gallery-dl-auto/tests/validation/conftest.py (更新,添加 Mock fixtures)
</files>
<action>
1. 创建 tests/validation/test_exit_codes.py

2. 实现 TestAuthExitCodes 测试类:
   - test_no_token_exit_code: 验证无 token 时返回退出码 1
   - test_expired_token_exit_code: 验证 token 过期时返回退出码 1
   - test_invalid_token_exit_code: 验证无效 token 时返回退出码 1
   - test_refresh_failed_exit_code: 验证刷新失败时返回退出码 1

3. 使用 Mock fixtures 模拟认证错误:
   ```python
   @pytest.fixture
   def mock_no_token(monkeypatch):
       """Mock 无 token 场景"""
       def mock_load_token():
           raise TokenNotFoundError("No token found")
       monkeypatch.setattr("gallery_dl_auo.auth.token.load_token", mock_load_token)
   ```

4. 验证错误码字符串在输出中:
   ```python
   result = runner.invoke(cli, ["download", "--type", "daily"])
   assert "AUTH_TOKEN_NOT_FOUND" in result.output
   assert result.exit_code == 1
   ```
</action>
<verify>
```bash
# 运行认证退出码测试
pytest tests/validation/test_exit_codes.py::TestAuthExitCodes -v
```
</verify>
<done>认证相关退出码验证测试已实现并全部通过</done>
</task>

---

## Must-haves (Goal-backward verification)

执行此计划后,以下条件必须为 TRUE:

1. ✅ **退出码映射表已建立**: EXIT_CODE_MAPPING 在 conftest.py 中定义
2. ✅ **认证退出码已验证**: TestAuthExitCodes 所有测试通过
3. ✅ **测试通过**: pytest tests/validation/test_exit_codes.py::TestAuthExitCodes -v 显示所有测试通过
4. ✅ **VAL-02 需求部分满足**: 可以展示认证相关退出码经过验证的证据

**验证命令**:
```bash
# 验证所有 must-haves
pytest tests/validation/test_exit_codes.py::TestAuthExitCodes -v && \
echo "✅ 认证相关退出码验证测试通过"
```

---

## Dependencies

**Depends on**:
- 10-01 (JSON 输出格式验证): 需要测试框架和 conftest.py 基础设施

**Blocks**:
- 10-02B (下载和参数退出码验证): 需要本计划建立的退出码映射表

---

## Risk mitigation

**风险 1: 部分认证错误场景难以在测试中模拟**
- 缓解措施: 优先验证高频认证错误场景,低频场景可手动验证
- 回滚策略: 记录未验证的错误场景,在 VALIDATION_RESULTS.md 中标注

**风险 2: Click 框架的默认退出码与预期不一致**
- 缓解措施: 在测试中验证实际退出码,根据实际情况更新映射表
- 回滚策略: 更新 INTEGRATION.md 以反映实际行为

---

## Notes

- 本计划专注于退出码映射表和认证相关退出码验证
- 下载和参数错误退出码验证在 10-02B 中进行
- 测试结果将记录在 tests/validation/VALIDATION_RESULTS.md
- 退出码映射表作为单一事实来源,文档和测试都基于此表
