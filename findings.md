# 当前发现

## 代码发现
- `api_test/core/base_api.py` 已支持 `expected_status`、`put()`、`patch()`，请求底座更完整。
- `api_test/core/jsonplaceholder_api.py` 已封装 `posts/users/todos` 的基础查询与伪写操作。
- `api_test/conftest.py` 已提供 `jsonplaceholder_api` fixture，便于公共站点测试复用。

## 测试发现
- `api_test/tests/test_base_api_governance.py` 覆盖底座请求治理、RSA 公钥显式依赖、重试 Session 配置。
- `api_test/tests/test_jsonplaceholder_api.py` 覆盖 JSONPlaceholder 基础 CRUD 与嵌套路由。
- `api_test/tests/test_jsonplaceholder_resources.py` 覆盖 `users`、`todos` 和公共 fixture 基线。
- 当前验证基线为：
  - `cd api_test && python -m pytest -v` => `25 passed, 4 skipped`
  - `python -m pytest tests/platform_core -v` => `32 passed`

## 文档发现
- README、`api_test/README.md`、V1 阶段计划、实施拆解、测试说明等文件已同步更新 JSONPlaceholder 规则与最新测试基线。
- 已完成旧基线扫描，未发现 `18 passed, 4 skipped` 或 `15 passed, 4 skipped` 等过期结果残留。

## 新风险发现
- `platform_core` 与 `api_test` 回归均出现 `pytest-asyncio` 的 `asyncio_default_fixture_loop_scope` 弃用告警，当前不阻断，但应作为后续测试基座治理项收敛。
