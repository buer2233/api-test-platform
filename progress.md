# 会话进展

## 2026-03-31

### 已完成
- 基于 TDD 为 `BaseAPI` 补充 `put()` 与 `patch()` 包装方法。
- 为 `JsonPlaceholderAPI` 补充 `list_users()`、`get_user()`、`list_todos()`、`list_user_todos()`。
- 在 `api_test/conftest.py` 中新增 `jsonplaceholder_api` fixture。
- 新增/扩展测试：
  - `api_test/tests/test_base_api_governance.py`
  - `api_test/tests/test_jsonplaceholder_resources.py`
- 为 `PublicAPI` 补充最小旧接口操作目录，并新增 `api_test/core/legacy_assets.py`。
- 将旧接口目录提升为 `api_test/legacy_api_catalog.py`，供 `api_test` 与 `platform_core` 共同消费。
- 为 `api_test/run_test.py` 新增 `--public-baseline` 模式，并补充命令构建测试。
- 为 `platform_core` 的工作区检查结果补充资产摘要输出，CLI `inspect` 同步输出完整结构化结果。
- 为 `platform_core` 新增旧接口结构化适配层、服务检查入口和 CLI `inspect-legacy-public-api` 命令。
- 为根目录和 `api_test` 的 pytest 配置显式补齐 `asyncio_default_fixture_loop_scope=function`，并修复 `api_test/conftest.py` 的旧式 optionalhook 写法。
- 已同步更新 README 与 V1 阶段/测试文档。

### 已验证
- `cd api_test && python -m pytest tests/test_base_api_governance.py tests/test_jsonplaceholder_resources.py -v`
  - 结果：`13 passed`
- `python -m pytest api_test/tests/test_public_api_governance.py api_test/tests/test_run_test.py -v`
  - 结果：`5 passed`
- `python -m pytest tests/platform_core/test_services_and_assets.py -k "inspect" -v`
  - 结果：`2 passed`
- `python -m pytest tests/platform_core/test_models.py tests/platform_core/test_services_and_assets.py -k "existing_api_asset or legacy_public_api" -v`
  - 结果：`3 passed`
- `cd api_test && python -m pytest -v`
  - 结果：`30 passed, 4 skipped`
- `python -m pytest tests/platform_core -v`
  - 结果：`35 passed`
- `cd api_test && python run_test.py --public-baseline`
  - 结果：`30 passed, 4 deselected`

### 待完成
- 输出当前实现功能与测试覆盖说明。
