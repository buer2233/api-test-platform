# api-test-platform

一个正在从“手写接口自动化测试框架”演进为“统一接口测试资产平台”的仓库。

当前主线目标：

> 统一接口测试资产平台 + AI 生成/编排能力 + 规则校验与执行验证闭环

## 当前状态

截至 2026-04-10，在 V1 正式验收完成、V2 P0 主线闭环通过后，仓库当前工作重点已切换到 V2 P1 扩展轮开发，核心方向为：

- 功能测试用例驱动优先；
- 场景模型、变量绑定、依赖编排与审核确认能力；
- Django + DRF + MySQL 服务化正式落地；
- 抓包驱动草稿化接入；
- 可用型 Web / Windows 入口承接；
- 来源追溯、执行历史、差异摘要与 AI 建议治理等 P1 核心事实层增强；
- V2 详细测试用例说明书已建立，当前正在按扩展实施计划继续执行 TDD。

当前已完成的 V2 第一实施子阶段首批落地包括：

- 已补齐 `TestScenario`、`ScenarioStep`、`VariableBinding`、`DependencyLink`、`ReviewRecord`、场景状态对象与场景服务摘要对象；
- 已新增 `platform_core/functional_cases.py`，支持结构化功能测试用例 JSON 输入解析为场景草稿；
- 已开放 `PlatformApplicationService` 的功能测试用例草稿摘要路线，并补齐非法状态流转阻断；
- 已完成首批定向 TDD 验证：
  - `python -m pytest tests/platform_core/test_models.py -k "v2_scenario" -v --basetemp .pytest_tmp/v2_phase1_models_green`
    - `2 passed`
  - `python -m pytest tests/platform_core/test_parser_inputs.py -k "functional_case_parser" -v --basetemp .pytest_tmp/v2_phase1_parser_green`
    - `2 passed`
  - `python -m pytest tests/platform_core/test_services_and_assets.py -k "current_capabilities or functional_case_draft_summary or invalid_scenario_status_transition" -v --basetemp .pytest_tmp/v2_phase1_service_green`
    - `3 passed`
- 已完成首批回归验证：
  - `python -m pytest tests/platform_core -v --basetemp .pytest_tmp/v2_phase1_platform_core_full`
    - `68 passed`
  - `python -m pytest tests -v --basetemp .pytest_tmp/v2_phase1_root_full`
    - `75 passed`
  - `python -m pytest api_test/tests -v --basetemp .pytest_tmp/v2_phase1_api_test_full`
    - `39 passed`

当前已完成的 V2 第二实施子阶段首批落地包括：

- 已新增 `requirements-platform-service.txt` 与 `.venv_service` 独立服务测试环境，并将 Django、DRF、PyMySQL、PyYAML、pytest 及其关键传递依赖固定到 2025 年及以前版本；
- 已新增 `manage.py`、`platform_service/` 与 `scenario_service/`，建立 Django + DRF 最小服务骨架、场景持久化模型和导入/详情/审核/执行/结果查询接口；
- 已新增 `platform_service/migration_settings.py` 与 `scenario_service/migrations/0001_initial.py`，补齐场景服务模型的初始迁移骨架；
- 已补齐 `platform_service/settings.py` 中的 PyMySQL MySQLdb 兼容补丁，避免 Django MySQL 后端在启动阶段因版本门槛直接失败；
- 已补齐 MySQL 8.4 默认认证链路所需的 `cryptography`、`cffi` 与 `pycparser` 固定版本依赖，为真实 MySQL 环境接入建立稳定基础；
- 已完成第二批定向与回归验证：
  - `.venv_service\\Scripts\\python.exe -m pytest service_tests -v --ds=platform_service.test_settings --basetemp .pytest_tmp/v2_phase2_service_tests`
    - `4 passed`
  - `.venv_service\\Scripts\\python.exe manage.py makemigrations scenario_service --check --dry-run --settings=platform_service.migration_settings`
    - `No changes detected`
  - `python -m pytest tests/platform_core -v --basetemp .pytest_tmp/v2_phase2_platform_core_regression`
    - `68 passed`
  - `python -m pytest tests -v --basetemp .pytest_tmp/v2_phase2_root_regression`
    - `76 passed`
  - `python -m pytest api_test/tests -v --basetemp .pytest_tmp/v2_phase2_api_test_regression`
    - `39 passed`

当前已完成的 V2 第三实施子阶段首批落地包括：

- 已新增 `platform_core/scenario_execution.py` 与 `platform_core/templates/tests/test_scenario_module.py.j2`，补齐“已确认场景 -> 工作区导出 -> pytest 执行 -> 结果回写”的最小执行流水线；
- 已扩展 `TemplateRenderer` 的场景级测试模块渲染能力，并在服务层接入最小公开基线操作目录，当前首批支持：
  - `operation-get-user`
  - `operation-list-user-todos`
- 已完成 `scenario_service/services.py` 的执行入口升级：
  - `request_execution()` 支持 `workspace_root`；
  - 执行前阻断未绑定可执行公开基线操作的场景；
  - 执行后回写 `workspace_root`、`report_path`、`execution_status`、`passed_count`、`failed_count`、`skipped_count` 与 `latest_execution_id`；
- 已补充 `service_tests/test_execution_closure.py` 与 DRF 结果摘要契约测试，锁定导出工作区、生成测试文件、结果查询摘要和阻断错误返回；
- 已将 `requests` 及其关键运行依赖固定到 2025 年及以前版本并纳入服务层依赖治理；
- 已完成第三批定向与回归验证：
  - `.venv_service\\Scripts\\python.exe -m pytest service_tests\\test_execution_closure.py -v --ds=platform_service.test_settings --basetemp .pytest_tmp/v2_phase3_execution_green2`
    - `2 passed`
  - `.venv_service\\Scripts\\python.exe -m pytest service_tests\\test_drf_contract.py -v --ds=platform_service.test_settings --basetemp .pytest_tmp/v2_phase3_drf_green2`
    - `3 passed`
  - `.venv_service\\Scripts\\python.exe -m pytest service_tests -v --ds=platform_service.test_settings --basetemp .pytest_tmp/v2_phase3_service_tests`
    - `7 passed`
  - `python -m pytest tests/platform_core -v --basetemp .pytest_tmp/v2_phase3_platform_core_regression`
    - `68 passed`
  - `python -m pytest tests -v --basetemp .pytest_tmp/v2_phase3_root_regression`
    - `76 passed`
  - `python -m pytest api_test/tests -v --basetemp .pytest_tmp/v2_phase3_api_test_regression`
    - `39 passed`

当前已完成的 V2 真实 MySQL 本地基线包括：

- 已确认本机 `MySQL84` 服务处于后台运行状态，且启动类型为 `Automatic`；
- 已初始化本地 `api_test_platform` 数据库，并建立 `platform_service` 专用账号用于服务层接入；
- 已在设置 `PLATFORM_MYSQL_*` 环境变量后完成 `manage.py migrate` 与 `manage.py showmigrations` 验证，确认 `auth/contenttypes/scenario_service/sessions` 迁移全部落库；
- 已完成一轮基于真实 MySQL 的 `FunctionalCaseScenarioService` 冒烟，最小 JSONPlaceholder 场景执行结果为 `passed`，并已验证工作区、报告文件和执行结果回写同时成立；

当前已完成的 V2 第四实施子阶段首批落地包括：

- 已新增 `ScenarioRevisionRecord` 持久化模型，并生成 `scenario_service/migrations/0002_scenariorevisionrecord.py`，补齐结构化修订留痕事实表；
- 已在 `scenario_service/services.py` 中新增 `revise_scenario()`，支持被驳回场景执行结构化修订、写入修订记录，并同步补充 `review_status=revised` 的审核留痕；
- 已新增 `/api/v2/scenarios/<scenario_id>/revise/` 接口，并让场景详情接口返回 `revisions` 修订清单；
- 已打通“驳回 -> 结构化修订 -> 再审核通过 -> 正式执行”的最小生命周期闭环；
- 已完成第四批定向与回归验证：
  - `.venv_service\\Scripts\\python.exe -m pytest service_tests\\test_review_revision_flow.py -v --ds=platform_service.test_settings --basetemp .pytest_tmp/v2_phase4_revision_green1`
    - `3 passed`
  - `.venv_service\\Scripts\\python.exe manage.py makemigrations scenario_service --check --dry-run --settings=platform_service.migration_settings`
    - `No changes detected`
  - `.venv_service\\Scripts\\python.exe -m pytest service_tests -v --ds=platform_service.test_settings --basetemp .pytest_tmp/v2_phase4_service_tests`
    - `10 passed`
  - 本地真实 MySQL 修订链路冒烟
    - `review_status=approved`
    - `execution_status=passed`
    - `revision_count=1`

当前已启动的 V2 P1 扩展轮 Task 1/Task 2/Task 3/Task 4 首批落地包括：

- 已将 `platform_service/settings.py` 的默认 MySQL 连接参数收口为仓库文档中的本地基线：`127.0.0.1:3306 / api_test_platform / platform_service / PlatformService_2025!`；
- 已新增 `service_tests/conftest.py`，让服务测试复用当前本地 MySQL 基线库，并在每个测试前后清理 `scenario_service` 业务表，绕开 `platform_service` 账号无建库权限的问题；
- 已新增 `ScenarioSourceRecord` 来源追溯事实表，并扩展 `ScenarioExecutionRecord` 的触发来源、修订关联、建议关联、变更摘要和差异摘要字段；
- 已在 `FunctionalCaseScenarioService` 中补齐来源追溯持久化、执行历史构造与重复执行唯一 `execution_id` 生成逻辑；
- 已新增场景列表筛选查询契约，当前已支持按 `source_type`、`review_status`、`execution_status`、`issue_code` 和 `ordering` 过滤场景摘要；
- 已让场景摘要/详情返回 `source_summary`、`issue_codes` 与最近执行差异摘要，让结果查询稳定返回 `execution_history` 与 `latest_diff_summary`；
- 已同步增强 DRF 查询契约测试，锁定列表筛选、详情来源聚合、执行历史和轻量差异摘要返回结构，为后续 AI 建议治理打下事实层基础；
- 已增强 `TrafficCaptureDraftParser` 的抓包归一化分类，当前会额外输出 `static_noise_filtered`、`duplicate_request_group` 等问题标签，并在步骤元数据中写入 `source_traces`、`capture_quality` 和低置信来源信息；
- 已让抓包导入后的场景来源追溯保留步骤级 `issue_tags` 与 `confidence=low`，避免抓包草稿在服务层落库后丢失来源质量标签；
- 已新增 `ScenarioSuggestionRecord` 与规则型建议提供者，当前已支持生成 `assertion_completion` 建议、查询建议列表，并在采纳时自动转成标准 `ScenarioRevisionRecord`；
- 已开放 `/api/v2/scenarios/<scenario_id>/suggestions/` 与 `/api/v2/scenarios/<scenario_id>/suggestions/<suggestion_id>/apply/`，让建议治理继续复用现有修订留痕与再审核机制；
- 当前服务测试执行约束：
  - 服务测试统一使用本地 MySQL 基线配置，并需设置 `DJANGO_SETTINGS_MODULE=platform_service.settings`
  - 由于根 `pytest.ini` 的默认 `.pytest_tmp` 下存在历史锁文件，当前服务测试命令统一追加 `--basetemp=.pytest_tmp_service`
- 已完成当前轮定向与回归验证：
  - `.venv_service\\Scripts\\python.exe -m pytest service_tests\\test_service_bootstrap.py::test_platform_service_defaults_follow_documented_local_mysql_baseline -q`
    - `1 passed`
  - `.venv_service\\Scripts\\python.exe -m pytest --basetemp=.pytest_tmp_service service_tests\\test_traceability_history_flow.py::test_import_and_repeated_execution_preserve_source_traces_and_history -q`
    - `1 passed`
  - `.venv_service\\Scripts\\python.exe -m pytest --basetemp=.pytest_tmp_service service_tests\\test_service_persistence.py service_tests\\test_execution_closure.py service_tests\\test_review_revision_flow.py -q`
    - `6 passed`
  - `.venv_service\\Scripts\\python.exe -m pytest --basetemp=.pytest_tmp_service service_tests\\test_scenario_query_contract.py service_tests\\test_drf_contract.py -q`
    - `4 passed`
  - `python -m pytest tests\\platform_core\\test_parser_inputs.py::test_traffic_capture_parser_filters_noise_and_builds_reviewable_draft tests\\platform_core\\test_services_and_assets.py::test_platform_application_service_supports_traffic_capture_draft_summary tests\\platform_core\\test_traffic_capture_traceability.py -q --basetemp=.pytest_tmp\\v2_p1_task3_regression`
    - `3 passed`
  - `.venv_service\\Scripts\\python.exe -m pytest --basetemp=.pytest_tmp_service service_tests\\test_scenario_suggestions.py::test_suggestion_creation_and_apply_flow_requires_revision_record -q`
    - `1 passed`
  - `$env:DJANGO_SETTINGS_MODULE='platform_service.settings'; .\\.venv_service\\Scripts\\python.exe -m pytest service_tests -q --basetemp=.pytest_tmp_service`
    - `18 passed`
  - `.venv_service\\Scripts\\python.exe manage.py makemigrations scenario_service --check --dry-run --settings=platform_service.migration_settings`
    - `No changes detected`

截至 2026-04-03，V1 阶段目标已完成，当前仓库已完成：

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
  - 2026-04-03 正式验收复验已确认：`jsonplaceholder` 相关公网用例可先开启代理执行，完成后恢复 `proxy.enabled=false`，同时保持默认配置契约测试通过
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
- 已完成 `platform_core` 服务摘要契约收口：
  - 新增服务层能力快照与文档驱动运行摘要模型
  - `PlatformApplicationService` 已可直接返回 `describe_capabilities()` 与 `run_document_pipeline_summary()`
  - `platform_core.cli run` 已改为直接消费服务层摘要模型，不再自行拼装输出字典
- 已完成 `platform_core` 工作区检查摘要契约收口：
  - 新增工作区检查服务摘要模型
  - `PlatformApplicationService` 已可直接返回 `inspect_workspace_summary()`
  - `platform_core.cli inspect` 已改为直接消费服务层摘要模型，并输出问题数量字段
- 已完成 `platform_core` 断言模板覆盖增强：
  - 已新增 `schema_match` 断言模板、解析候选生成和规则校验
  - 已补齐 `business_rule(non_empty_string)` 与 `business_rule(positive_integer)` 的最小闭环，支持模板渲染、规则校验和按断言生成非空字符串 / 正整数假响应
  - 生成的 pytest 测试骨架会根据断言集合自动构造最小假响应体，不再固定写死对象结构
  - `schema_match` 的 `required_fields` 渲染改为稳定的 JSON 风格字符串，便于模板与测试长期一致
  - 当前轮继续补齐对象数组结构断言，支持数组项对象字段校验和对象数组假响应生成
- 已完成 `platform_core` 最终收口增强：
  - `DocumentPipelineRunSummary` 已补齐 `source_type`、`execution_id` 与 `asset_type_breakdown`
  - `WorkspaceInspectionSummary` 已补齐 `source_type`、`execution_id` 与 `inventory_summary`
  - 生成记录在目录级 pytest 执行后会回写 `execution_status`，便于后续服务层和客户端直接消费
- 已完成依赖治理收口：
  - `api_test/requirements.txt` 已改为固定版本约束
  - 已删除仓库中无代码引用的 `rsa` 依赖
  - 已新增 `tests/test_dependency_governance.py` 锁定依赖治理规则

当前分支最新已验证结果：

- 2026-04-10 V2 P1 扩展轮 Task 1/Task 2/Task 3/Task 4：
  - `.venv_service\\Scripts\\python.exe -m pytest service_tests\\test_service_bootstrap.py::test_platform_service_defaults_follow_documented_local_mysql_baseline -q`
    - `1 passed`
  - `$env:DJANGO_SETTINGS_MODULE='platform_service.settings'; .\\.venv_service\\Scripts\\python.exe -m pytest --basetemp=.pytest_tmp_service service_tests\\test_traceability_history_flow.py::test_import_and_repeated_execution_preserve_source_traces_and_history -q`
    - `1 passed`
  - `$env:DJANGO_SETTINGS_MODULE='platform_service.settings'; .\\.venv_service\\Scripts\\python.exe -m pytest --basetemp=.pytest_tmp_service service_tests\\test_service_persistence.py service_tests\\test_execution_closure.py service_tests\\test_review_revision_flow.py -q`
    - `6 passed`
  - `$env:DJANGO_SETTINGS_MODULE='platform_service.settings'; .\\.venv_service\\Scripts\\python.exe -m pytest --basetemp=.pytest_tmp_service service_tests\\test_scenario_query_contract.py service_tests\\test_drf_contract.py -q`
    - `4 passed`
  - `python -m pytest tests\\platform_core\\test_parser_inputs.py::test_traffic_capture_parser_filters_noise_and_builds_reviewable_draft tests\\platform_core\\test_services_and_assets.py::test_platform_application_service_supports_traffic_capture_draft_summary tests\\platform_core\\test_traffic_capture_traceability.py -q --basetemp=.pytest_tmp\\v2_p1_task3_regression`
    - `3 passed`
  - `$env:DJANGO_SETTINGS_MODULE='platform_service.settings'; .\\.venv_service\\Scripts\\python.exe -m pytest --basetemp=.pytest_tmp_service service_tests\\test_scenario_suggestions.py::test_suggestion_creation_and_apply_flow_requires_revision_record -q`
    - `1 passed`
  - `$env:DJANGO_SETTINGS_MODULE='platform_service.settings'; .\\.venv_service\\Scripts\\python.exe -m pytest service_tests -q --basetemp=.pytest_tmp_service`
    - `18 passed`
  - `.venv_service\\Scripts\\python.exe manage.py makemigrations scenario_service --check --dry-run --settings=platform_service.migration_settings`
    - `No changes detected`
- 2026-04-03 V1 正式验收复验：
  - `cd api_test && python -m pytest tests -m jsonplaceholder -v --basetemp ..\.pytest_tmp\api_test_jsonplaceholder_acceptance`
    - `12 passed, 27 deselected`
  - `python api_test/run_test.py --public-baseline`
    - `12 passed, 27 deselected`
  - `cd api_test && python run_test.py --public-baseline`
    - `12 passed, 27 deselected`
  - `cd api_test && python -m pytest tests -m "not jsonplaceholder" -v --basetemp ..\.pytest_tmp\api_test_non_jsonplaceholder_acceptance`
    - `27 passed, 12 deselected`
  - `cd api_test && python -m pytest tests/test_config_loader.py -v --noconftest --basetemp ..\.pytest_tmp\config_loader_after_proxy_restore_fix`
    - `6 passed`
  - `python -m pytest tests/platform_core -v --basetemp .pytest_tmp/platform_core_v1_acceptance_proxy_20260403`
    - `63 passed`
  - `python -m pytest tests -v --basetemp .pytest_tmp/root_v1_acceptance_proxy_20260403`
    - `70 passed`
  - `python -m pytest tests -v --basetemp .pytest_tmp/root_v1_acceptance_doc_sync_20260403`
    - `70 passed`
- `python -m pytest tests/platform_core/test_models.py tests/platform_core/test_templates_and_rules.py tests/platform_core/test_services_and_assets.py tests/test_dependency_governance.py -k "positive_integer or inventory_summary or source_type or execution_id or asset_type_breakdown or dependency_governance" -v --basetemp .pytest_tmp/v1_final_closure_green`
  - `6 passed`
- `python -m pytest tests/platform_core -v --basetemp .pytest_tmp/platform_core_v1_final_closure_full`
  - `63 passed`
- `python -m pytest tests -v --basetemp .pytest_tmp/root_v1_final_closure_full`
  - `70 passed`
- `python -m pytest api_test/tests -v --basetemp .pytest_tmp/api_test_v1_final_closure_full`
  - `39 passed`
- `python api_test/run_test.py --public-baseline`
  - `12 passed, 27 deselected`
- `cd api_test && python run_test.py --public-baseline`
  - `12 passed, 27 deselected`

当前已补充的 UI 原型资产：

- `docs/ui-prototypes/mobile-onboarding-illustrated.html`
  - 移动端 App 引导页静态原型，采用插图风格与三步引导流程，可直接浏览器预览
- `docs/superpowers/specs/2026-04-08-mobile-onboarding-design.md`
  - 对应原型设计说明，记录结构拆分、视觉方向与后续 React 组件拆分建议

以下保留当前阶段的历史专项与阶段性验证记录，用于追踪演进过程，不代表当前最新综合计数：

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
- 2026-04-03 正式验收复验已采用“`jsonplaceholder` 相关用例先开启代理、完成后恢复默认关闭并执行非公网配置/治理回归”的分段流程，相关结果已写入 [V1阶段正式验收报告.md](/D:/AI/api-test-platform/product_document/%E9%98%B6%E6%AE%B5%E6%96%87%E6%A1%A3/V1%E9%98%B6%E6%AE%B5%E6%AD%A3%E5%BC%8F%E9%AA%8C%E6%94%B6%E6%8A%A5%E5%91%8A.md)；
- 2026-04-03 文档同步后已再次执行根测试 `python -m pytest tests -v --basetemp .pytest_tmp/root_v1_acceptance_doc_sync_20260403`，结果仍为 `70 passed`；
- 仓库默认保持 `proxy.enabled=false`，但默认直连外网站点仍存在时延波动，当前公开站点回归建议优先开启代理；
- `platform_core` 的生成记录、执行记录、工作区检查、服务能力快照、运行摘要、检查摘要和 `schema_match` 断言闭环已经完成 V1 范围内收口；
- `business_rule` 当前已支持 `non_empty_string` 和 `positive_integer` 两个最小规则代码，但仍只支持手工构造断言，不由解析器自动生成；
- 生成测试骨架时，伪客户端返回值已从固定示例改为随断言上下文生成，当前对象、数组、对象数组、非空字符串和正整数业务规则场景都不会再因假响应结构失真而误报失败；
- `run` / `inspect` 摘要已补齐 `source_type`、`execution_id` 和资产聚合字段，工作区检查结果可直接被后续 Django + DRF / 客户端消费；
- 生成记录在目录级执行完成后会回写 `execution_status`，当前工作区检查摘要已能聚合展示执行状态分布；
- `api_test/requirements.txt` 已改为固定版本，并通过自动化治理测试锁定，避免再次引入宽松约束和无用依赖；
- `platform_core`、根治理测试与执行入口回归当前轮均保持通过；
- 2026-04-02 当前轮完整回归中，`tests/platform_core` 为 `63 passed`、根测试为 `70 passed`、`api_test/tests` 为 `39 passed`，公开基线双入口均为 `12 passed, 27 deselected`；
- 当前 V1 阶段目标已经完成；更复杂的 `business_rule` DSL、更深层结构断言、动态变量与依赖编排能力已转入 V2 阶段规划。

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
- V2 当前优先围绕功能测试用例驱动、场景编排、审核确认、服务化落地和可用型入口承接推进
- `api_test/` 的目标是“通用 HTTP 测试底座 + JSON 配置驱动 + 公开示例适配”
- 所有全局配置最终统一收口到 `api_test/api_config.json`
- 可用型入口的页面探索当前已补充移动端引导页原型，后续 Web / Windows 正式实现可据此继续拆分组件与交互

## 当前建议查看顺序

开始任何需求、设计或开发前，优先查看：

- [AGENTS.md](/D:/AI/api-test-platform/AGENTS.md)
- [V2阶段工作计划文档.md](/D:/AI/api-test-platform/product_document/阶段文档/V2阶段工作计划文档.md)
- [详细测试用例说明书(V2).md](/D:/AI/api-test-platform/product_document/测试文档/详细测试用例说明书(V2).md)
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
- [v1-service-summary-contract-design.md](/D:/AI/api-test-platform/docs/superpowers/specs/2026-04-02-v1-service-summary-contract-design.md)
- [v1-service-summary-contract.md](/D:/AI/api-test-platform/docs/superpowers/plans/2026-04-02-v1-service-summary-contract.md)
- [v1-inspect-summary-contract-design.md](/D:/AI/api-test-platform/docs/superpowers/specs/2026-04-02-v1-inspect-summary-contract-design.md)
- [v1-inspect-summary-contract.md](/D:/AI/api-test-platform/docs/superpowers/plans/2026-04-02-v1-inspect-summary-contract.md)
- [v1-business-rule-minimal-closure-design.md](/D:/AI/api-test-platform/docs/superpowers/specs/2026-04-02-v1-business-rule-minimal-closure-design.md)
- [v1-business-rule-minimal-closure.md](/D:/AI/api-test-platform/docs/superpowers/plans/2026-04-02-v1-business-rule-minimal-closure.md)
- [v1-final-closure-design.md](/D:/AI/api-test-platform/docs/superpowers/specs/2026-04-02-v1-final-closure-design.md)
- [v1-final-closure.md](/D:/AI/api-test-platform/docs/superpowers/plans/2026-04-02-v1-final-closure.md)
- [2026-04-08-v2-stage-plan-design.md](/D:/AI/api-test-platform/docs/superpowers/specs/2026-04-08-v2-stage-plan-design.md)

## 当前验证入口

平台核心历史基线：

```bash
python -m pytest tests/platform_core -v
```

V1 验收回归验证：

```bash
python -m pytest tests/platform_core -v --basetemp .pytest_tmp/platform_core_v1_final_closure_full
python -m pytest tests -v --basetemp .pytest_tmp/root_v1_final_closure_full
python -m pytest api_test/tests -v --basetemp .pytest_tmp/api_test_v1_final_closure_full
python api_test/run_test.py --public-baseline
cd api_test && python run_test.py --public-baseline
```

V2 第二实施子阶段服务回归验证：

```bash
.venv_service\Scripts\python.exe -m pytest service_tests -v --ds=platform_service.test_settings --basetemp .pytest_tmp/v2_phase2_service_tests
.venv_service\Scripts\python.exe manage.py makemigrations scenario_service --check --dry-run --settings=platform_service.migration_settings
python -m pytest tests/platform_core -v --basetemp .pytest_tmp/v2_phase2_platform_core_regression
python -m pytest tests -v --basetemp .pytest_tmp/v2_phase2_root_regression
python -m pytest api_test/tests -v --basetemp .pytest_tmp/v2_phase2_api_test_regression
```

V2 第三实施子阶段执行闭环回归验证：

```bash
.venv_service\Scripts\python.exe -m pytest service_tests\test_execution_closure.py -v --ds=platform_service.test_settings --basetemp .pytest_tmp/v2_phase3_execution_green2
.venv_service\Scripts\python.exe -m pytest service_tests\test_drf_contract.py -v --ds=platform_service.test_settings --basetemp .pytest_tmp/v2_phase3_drf_green2
.venv_service\Scripts\python.exe -m pytest service_tests -v --ds=platform_service.test_settings --basetemp .pytest_tmp/v2_phase3_service_tests
python -m pytest tests/platform_core -v --basetemp .pytest_tmp/v2_phase3_platform_core_regression
python -m pytest tests -v --basetemp .pytest_tmp/v2_phase3_root_regression
python -m pytest api_test/tests -v --basetemp .pytest_tmp/v2_phase3_api_test_regression
```

V2 本地真实 MySQL 基线验证：

```bash
python -m pytest tests/test_dependency_governance.py -v --basetemp .pytest_tmp/mysql_dependency_regression
.venv_service\Scripts\python.exe -m pytest service_tests -v --ds=platform_service.test_settings --basetemp .pytest_tmp/mysql_service_regression
```

V2 第四实施子阶段审核修订回归验证：

```bash
.venv_service\Scripts\python.exe -m pytest service_tests\test_review_revision_flow.py -v --ds=platform_service.test_settings --basetemp .pytest_tmp/v2_phase4_revision_green1
.venv_service\Scripts\python.exe manage.py makemigrations scenario_service --check --dry-run --settings=platform_service.migration_settings
.venv_service\Scripts\python.exe -m pytest service_tests -v --ds=platform_service.test_settings --basetemp .pytest_tmp/v2_phase4_service_tests
```

## 备注

- 当前 README 以 V1 验收事实为基础，并已同步补记 V2 第一、第二、第三、第四实施子阶段以及本地真实 MySQL 基线的实际进展。
- 当前已进入 V2 阶段正式实现与测试执行，后续新增能力应优先进入 V2 阶段文档和对应测试文档，再按新的 TDD 轮次推进实现与回归。
