# 当前发现

## 代码发现
- `api_test/core/base_api.py` 已支持 `expected_status`、`put()`、`patch()`，请求底座更完整。
- `api_test/core/jsonplaceholder_api.py` 已封装 `posts/users/todos` 的基础查询与伪写操作。
- `api_test/conftest.py` 已提供 `jsonplaceholder_api` fixture，便于公共站点测试复用。
- `api_test/core/public_api.py` 已补充最小旧接口操作目录，`PublicAPI.describe_operations()` 可输出治理后的旧接口元信息。
- `api_test/legacy_api_catalog.py` 已把旧目录提升为跨模块可导入的 catalog，供 `api_test` 与 `platform_core` 共同消费。
- `api_test/run_test.py` 已新增 `--public-baseline` 模式，可稳定排除 `private_env` 用例。
- `platform_core` 的 CLI `inspect` 现可返回资产摘要列表，不再只有数量级统计。
- `platform_core/legacy_assets.py` 已可把旧 `PublicAPI` 目录转换为 `existing_api_asset` 类型的结构化快照。
- `platform_core/legacy_assets.py` 现在还可把旧接口快照导出到工作区，生成模块级 JSON 资产、执行报告和 `asset_manifest.json`。
- `platform_core/rules.py` 已新增 `existing_api_asset` 专项规则，可校验旧接口模块命名、`legacy_public_api` / `private_env` 标记以及 `payload_mode` / `response_mode` / `requires_private_env` / `source_layer` 元数据。

## 测试发现
- `api_test/tests/test_base_api_governance.py` 覆盖底座请求治理、RSA 公钥显式依赖、重试 Session 配置。
- `api_test/tests/test_jsonplaceholder_api.py` 覆盖 JSONPlaceholder 基础 CRUD 与嵌套路由。
- `api_test/tests/test_jsonplaceholder_resources.py` 覆盖 `users`、`todos` 和公共 fixture 基线。
- `api_test/tests/test_public_api_governance.py` 覆盖旧 `PublicAPI` 操作目录和 raw response 调用约束。
- `api_test/tests/test_run_test.py` 覆盖公开基线执行命令构建逻辑。
- `tests/platform_core/test_services_and_assets.py` 已覆盖旧接口结构化快照的服务层与 CLI 检查入口。
- `tests/platform_core/test_services_and_assets.py` 已覆盖旧接口快照落盘、工作区检查和 CLI `snapshot-legacy-public-api` 入口。
- `tests/platform_core/test_templates_and_rules.py` 与 `tests/platform_core/test_services_and_assets.py` 现已覆盖旧接口专项规则、校验状态输出和无效快照阻断。
- 当前验证基线为：
  - `cd api_test && python -m pytest -v` => `30 passed, 4 skipped`
  - `cd api_test && python run_test.py --public-baseline` => `30 passed, 4 deselected`
  - `python -m pytest tests/platform_core -v` => `40 passed`

## 文档发现
- README、`api_test/README.md`、V1 阶段计划、实施拆解、测试说明等文件已同步更新旧接口目录治理、公开基线入口、资产摘要输出与最新测试基线。
- 已完成旧基线扫描，未发现 `18 passed, 4 skipped`、`15 passed, 4 skipped` 或 `25 passed, 4 skipped` 等过期结果残留。

## 新风险发现
- 旧 `PublicAPI` 虽已补齐最小治理目录和专项规则，但私有业务接口仍未完全接入统一平台中间模型。
- 私有环境链路仍依赖真实账号、私有环境和 RSA 公钥，当前仅通过 `private_env` 标记和公开基线入口隔离。
