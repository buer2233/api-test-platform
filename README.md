# api-test-platform

一个正在从“手写接口自动化测试框架”演进为“统一接口测试资产平台”的仓库。

当前主线目标：

> 统一接口测试资产平台 + AI 生成/编排能力 + 规则校验与执行验证闭环

## 当前状态

截至 2026-04-02，仓库处于“通用测试框架大重构”执行中，已完成：

- 重构设计说明与实施计划；
- 重构前备份提交并推送：
  - `c102cb4`
  - `备份：测试框架大重构前的备份提交`
- `api_test/` 配置收口的首个 TDD 循环：
  - 新增 `api_test/api_config.json`
  - 新增 `api_test/core/config_loader.py`
  - 新增 `api_test/tests/test_config_loader.py`
- `api_test/` 运行时治理的第二个 TDD 循环：
  - 已将 `api_test/core/session.py` 改为读取 JSON 配置
  - 已将 `api_test/core/base_api.py` 收口为通用 HTTP 客户端
  - 已将 `api_test/core/__init__.py` 去除旧私有站点导出
- 已完成 `api_test/` 公共工具层拆分的第三个 TDD 循环：
  - 新增 `api_test/core/common_tools.py`
  - `BaseAPI` 已移除嵌套取值、时间、加解密与随机数据工具
  - 新增 `api_test/tests/test_common_tools.py` 锁定工具迁移后的行为回归
- 已补充代理配置能力：
  - `api_test/api_config.json` 新增 `proxy.enabled` 和 `proxy.url`
  - `build_retry_session()` 在代理开关开启时自动为 `http/https` 请求挂载代理
  - 后续客户端应直接控制这两个配置项，而不是新增平行配置源
  - 本轮验证曾临时启用 `proxy.enabled=true` 并使用 `http://127.0.0.1:7890` 完成代理连通性验证，仓库默认值已恢复为关闭
- 已完成中文注释治理首轮落地：
  - 新增 `tests/test_comment_governance.py`，对仓库内 Python 模块/类/方法中文 docstring 与 `api_config.json` 中文说明字段做自动校验
  - 已为 `run_test.py`、`config_loader.py`、`base_api.py`、`platform_core` 核心层和现有测试文件补齐中文注释
  - `config_loader.py` 已兼容忽略 `_comment` / `*_comment` 配置说明字段，保证 `api_config.json` 可同时承载配置和中文说明
- 已完成历史专用残留清理：
  - 已删除 `api_test/config.py`
  - 已删除旧目录桥接清单文件
  - 已删除 `api_test/core/legacy_assets.py`
  - 已删除 `platform_core/legacy_assets.py`
  - 已删除 `api_test/test_data/account.txt`
- 已移除 `api_test/tests` 中两个旧私有站点测试入口：
  - `test_demo.py`
  - `test_public_api_governance.py`
- 已完成 `platform_core` 记录与服务摘要增强首轮落地：
  - `GenerationRecord` 新增 `module_code`、`operation_code`、`target_asset_digest`
  - `ExecutionRecord` 新增 `command`、`exit_code`、测试数量统计字段
  - `AssetWorkspace.inspect_manifest()` 新增生成记录摘要与缺失生成记录检查
  - `platform_core.cli run` 新增 `generation_count`、`asset_count`、执行退出码与测试统计输出
- 已完成 `platform_core` 断言模板覆盖增强：
  - 已新增 `schema_match` 断言模板、解析候选生成和规则校验
  - 生成的 pytest 测试骨架会根据断言集合自动构造最小假响应体，不再固定写死对象结构
  - `schema_match` 的 `required_fields` 渲染改为稳定的 JSON 风格字符串，便于模板与测试长期一致
  - 当前轮继续补齐对象数组结构断言，支持数组项对象字段校验和对象数组假响应生成

当前分支最新已验证结果：

- `python -m pytest api_test/tests/test_base_api_governance.py api_test/tests/test_common_tools.py -v --noconftest --basetemp .pytest_tmp/base_api_split_docs`
  - `19 passed`
- `python -m pytest api_test/tests -v --basetemp .pytest_tmp/api_test_base_api_split_full`
  - `39 passed`
- `python -m pytest tests/platform_core -v --basetemp .pytest_tmp/platform_core_after_base_api_split`
  - `48 passed`
- `python -m pytest tests -v --basetemp .pytest_tmp/root_after_doc_sync`
  - `53 passed`
- `python api_test/run_test.py --public-baseline`
  - `12 passed, 27 deselected`
- `cd api_test && python run_test.py --public-baseline`
  - `12 passed, 27 deselected`
- `python -m pytest api_test/tests/test_config_loader.py -v --noconftest --basetemp .pytest_tmp/config_loader`
  - `5 passed`
- `python -m pytest api_test/tests/test_base_api_governance.py -v --noconftest --basetemp .pytest_tmp/base_api`
  - `10 passed`
- 代理有效性验证：
  - `Test-NetConnection 127.0.0.1 -Port 7890` -> `TcpTestSucceeded=True`
  - 基于 `build_retry_session()` 的代理会话请求 `https://jsonplaceholder.typicode.com/posts/1` -> `200 / body_id=1`
- 2026-04-01 代理开启专项复验：
  - `python -m pytest api_test/tests/test_base_api_governance.py -v --noconftest --basetemp .pytest_tmp/base_api_proxy_recheck`
    - `10 passed`
  - `python api_test/run_test.py --public-baseline`
    - `12 passed, 18 deselected`
  - `cd api_test && python run_test.py --public-baseline`
    - `12 passed, 18 deselected`
- `python -m pytest api_test/tests -v --basetemp .pytest_tmp/api_test_full_after_cleanup`
  - `30 passed`
- 2026-04-01 默认关闭代理直连复验：
  - `python -m pytest api_test/tests -v --basetemp .pytest_tmp/api_test_full_default_off_serial`
    - `1 failed, 28 passed`
    - 失败项：`test_patch_updates_partial_fields`
    - 根因：访问 `jsonplaceholder.typicode.com` 时出现 `SSL handshake/read timeout`，属于外网站点时延波动，不是框架断言逻辑错误
- `python api_test/run_test.py --public-baseline`
  - `12 passed, 18 deselected`
- 中文注释治理与兼容性回归：
  - `python -m pytest tests -v --basetemp .pytest_tmp/root_full_after_comment_fix`
    - `41 passed`
  - `python -m pytest api_test/tests/test_config_loader.py api_test/tests/test_base_api_governance.py api_test/tests/test_run_test.py -v --noconftest --basetemp .pytest_tmp/api_test_local_comment_update_fix`
    - `18 passed`
  - `python api_test/run_test.py --public-baseline`
    - `12 passed, 18 deselected`
- `cd api_test && python run_test.py --public-baseline`
  - `12 passed, 18 deselected`
- `python -m pytest tests/platform_core -v --basetemp .pytest_tmp/platform_core_full_after_cleanup`
  - `36 passed`
- `python -m pytest tests/platform_core/test_models.py -v --basetemp .pytest_tmp/platform_core_models_after_impl`
  - `10 passed`
- `python -m pytest tests/platform_core/test_pipeline.py tests/platform_core/test_services_and_assets.py -v --basetemp .pytest_tmp/platform_core_traceability_after_impl`
  - `17 passed`
- `python -m pytest tests/platform_core/test_templates_and_rules.py -k "schema_match or fake_response" -v --basetemp .pytest_tmp/schema_green`
  - `3 passed`
- `python -m pytest tests/platform_core/test_services_and_assets.py tests/platform_core/test_pipeline.py -v --basetemp .pytest_tmp/schema_pipeline_green`
  - `19 passed`
- `python -m pytest tests/platform_core/test_templates_and_rules.py tests/platform_core/test_services_and_assets.py tests/platform_core/test_pipeline.py -k "array_object or schema_match" -v --basetemp .pytest_tmp/array_schema_green`
  - `8 passed`
- `python -m pytest tests/platform_core -v --basetemp .pytest_tmp/platform_core_array_schema_full`
  - `48 passed`
- `python -m pytest tests -v --basetemp .pytest_tmp/root_array_schema_full`
  - `53 passed`
- `python -m pytest api_test/tests -v --basetemp .pytest_tmp/api_test_array_schema_full`
  - `30 passed`
- `python api_test/run_test.py --public-baseline`
  - `12 passed, 18 deselected`
- `cd api_test && python run_test.py --public-baseline`
  - `12 passed, 18 deselected`
- `python -m pytest tests/platform_core -v --basetemp .pytest_tmp/platform_core_assertion_full`
  - `43 passed`
- `python -m pytest tests -v --basetemp .pytest_tmp/root_assertion_full`
  - `48 passed`
- `python -m pytest api_test/tests -v --basetemp .pytest_tmp/api_test_assertion_full`
  - `30 passed`
- `python api_test/run_test.py --public-baseline`
  - `12 passed, 18 deselected`
- `cd api_test && python run_test.py --public-baseline`
  - `12 passed, 18 deselected`
- `python -m pytest tests -v --basetemp .pytest_tmp/root_full_traceability`
  - `43 passed`
- `python -m pytest tests/platform_core -v --basetemp .pytest_tmp/platform_core_full_traceability`
  - `38 passed`
- `python -m pytest api_test/tests -v --basetemp .pytest_tmp/api_test_full_traceability`
  - `30 passed`
- `python api_test/run_test.py --public-baseline`
  - `12 passed, 18 deselected`
- `cd api_test && python run_test.py --public-baseline`
  - `12 passed, 18 deselected`

说明：

- 当前 `api_test` 的通用配置、通用运行时、公开基线入口和公开示例测试已经完成当前轮闭环验证；
- 代理开启时，当前公开基线与运行入口复验稳定通过；
- 仓库默认保持 `proxy.enabled=false`，但默认直连外网站点仍存在时延波动，当前公开站点回归建议优先开启代理；
- `platform_core` 的生成记录、执行记录、工作区检查、CLI 运行摘要和 `schema_match` 断言闭环已经开始向后续服务接口形态收口；
- 生成测试骨架时，伪客户端返回值已从固定示例改为随断言上下文生成，当前对象、数组和对象数组场景都不会再因假响应结构失真而误报失败；
- `platform_core`、根治理测试与执行入口回归当前轮均保持通过；
- 2026-04-02 当前轮完整回归中，`tests/platform_core` 为 `48 passed`、根测试为 `53 passed`、`api_test/tests` 为 `39 passed`，公开基线双入口均为 `12 passed, 27 deselected`；
- `BaseAPI` 与 `common_tools` 的首轮职责收口已完成；后续主要剩余工作转为模板/规则更深覆盖，以及服务接口产品化边界继续收敛。

## 当前仓库结构

```text
api-test-platform/
├─ api_test/
│  ├─ api_config.json       # 唯一配置源
│  ├─ core/                 # 通用运行时与历史底座代码
│  │  ├─ common_tools.py    # 通用工具函数
│  ├─ tests/                # api_test 自动化测试
│  │  ├─ test_common_tools.py
│  ├─ conftest.py           # 公开基线 fixture / 报告 hook
│  ├─ pytest.ini            # api_test pytest 配置
│  ├─ run_test.py           # 公开基线执行入口
│  ├─ README.md
│  └─ QUICKSTART.md
├─ platform_core/           # V1 平台核心最小闭环
├─ tests/platform_core/     # platform_core 自动化测试
├─ product_document/        # 产品、架构、阶段、测试文档
├─ docs/superpowers/        # 当前轮设计说明与实施计划
├─ AGENTS.md
└─ README.md
```

## 当前已确认方向

- 公开接口测试基线统一使用 `https://jsonplaceholder.typicode.com/`
- V1 当前只开放文档驱动最小闭环
- `api_test/` 的目标是“通用 HTTP 测试底座 + JSON 配置驱动 + 公开示例适配”
- 所有全局配置最终统一收口到 `api_test/api_config.json`

## 当前建议查看顺序

开始任何需求、设计或开发前，优先查看：

- [AGENTS.md](/D:/AI/api-test-platform/AGENTS.md)
- [产品需求说明书(全局).md](/D:/AI/api-test-platform/product_document/产品需求说明书(全局).md)
- [总体架构设计说明书.md](/D:/AI/api-test-platform/product_document/架构设计/总体架构设计说明书.md)
- [中间模型设计说明书.md](/D:/AI/api-test-platform/product_document/架构设计/中间模型设计说明书.md)
- [现有接口自动化测试框架改造方案.md](/D:/AI/api-test-platform/product_document/架构设计/现有接口自动化测试框架改造方案.md)
- [详细测试用例说明书(V1).md](/D:/AI/api-test-platform/product_document/测试文档/详细测试用例说明书(V1).md)
- [generic-test-framework-refactor-design.md](/D:/AI/api-test-platform/docs/superpowers/specs/2026-04-01-generic-test-framework-refactor-design.md)
- [generic-test-framework-refactor.md](/D:/AI/api-test-platform/docs/superpowers/plans/2026-04-01-generic-test-framework-refactor.md)
- [v1-traceability-summary-design.md](/D:/AI/api-test-platform/docs/superpowers/specs/2026-04-01-v1-traceability-summary-design.md)
- [v1-traceability-summary.md](/D:/AI/api-test-platform/docs/superpowers/plans/2026-04-01-v1-traceability-summary.md)
- [v1-assertion-template-coverage-design.md](/D:/AI/api-test-platform/docs/superpowers/specs/2026-04-02-v1-assertion-template-coverage-design.md)
- [v1-assertion-template-coverage.md](/D:/AI/api-test-platform/docs/superpowers/plans/2026-04-02-v1-assertion-template-coverage.md)
- [v1-array-schema-match-design.md](/D:/AI/api-test-platform/docs/superpowers/specs/2026-04-02-v1-array-schema-match-design.md)
- [v1-array-schema-match.md](/D:/AI/api-test-platform/docs/superpowers/plans/2026-04-02-v1-array-schema-match.md)
- [v1-base-api-responsibility-split-design.md](/D:/AI/api-test-platform/docs/superpowers/specs/2026-04-02-v1-base-api-responsibility-split-design.md)
- [v1-base-api-responsibility-split.md](/D:/AI/api-test-platform/docs/superpowers/plans/2026-04-02-v1-base-api-responsibility-split.md)

## 当前验证入口

平台核心历史基线：

```bash
python -m pytest tests/platform_core -v
```

当前轮配置收口验证：

```bash
python -m pytest api_test/tests/test_config_loader.py -v --noconftest --basetemp .pytest_tmp/config_loader
python -m pytest api_test/tests/test_base_api_governance.py api_test/tests/test_common_tools.py -v --noconftest --basetemp .pytest_tmp/base_api_split_docs
python -m pytest api_test/tests -v --basetemp .pytest_tmp/api_test_base_api_split_full
python -m pytest tests/platform_core -v --basetemp .pytest_tmp/platform_core_after_base_api_split
python -m pytest tests -v --basetemp .pytest_tmp/root_after_doc_sync
python api_test/run_test.py --public-baseline
cd api_test && python run_test.py --public-baseline
```

## 备注

- 当前 README 已切换为“重构进行中”视角，只记录本分支已验证事实。
- `api_test` 和 `platform_core` 的更大范围回归，将在本轮去特化和文档同步完成后再次统一复验并回填文档。
