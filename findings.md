# 当前发现

## 2026-04-15 V3 P1 G2 抓包正式执行闭环发现
- 当前 `P1-G2` 的真正缺口不是“抓包导入”，而是导入后的正式治理层缺失：没有正式确认对象、没有绑定确认动作，也没有执行前门禁，因此执行入口会直接落到旧的 `unsupported_public_baseline_operation` 错误。
- 本轮首批实现采用“抓包场景继续复用 `ScenarioRecord`，另增 `TrafficCaptureFormalizationRecord` 承接确认态与绑定态”的方案，避免为抓包路线再造一套平行场景或执行体系。
- 当前抓包正式执行闭环继续复用 `P1-G1` 的显式 actor 门禁与审计日志：
  - `confirm_traffic_capture`
  - `confirm_traffic_capture_bindings`
  - `execute_scenario`
  三类关键动作都继续落在统一的项目边界和审计查询契约内。
- 执行门禁必须前置在执行管线之前；否则抓包场景会先因为候选 `operation_id` 不可执行而失败，掩盖真正应暴露给用户的治理错误语义。
- 当前第一批抓包正式执行范围仍然刻意收敛：
  - 只支持公开基线操作绑定确认；
  - 不做复杂抓包智能映射；
  - 不做 AI 自动修复或自动推断绑定。
- 当前 `P1-G2` 首批结果已成立：
  - `service_tests/test_v3_p1_traffic_capture_execution.py` -> `3 passed`
  - `service_tests` -> `38 passed`
  - `tests/platform_core` -> `71 passed`
  - `tests` -> `79 passed`
  - `api_test/tests` -> `39 passed`

## 2026-04-15 V3 P1 G1 启动发现
- `P1` 当前范围过大，必须继续拆分；其中 `权限体系与审计治理` 是抓包正式执行、入口深化和调度中心的共同前置，不宜继续和其他 `P1` 子项并行混改。
- 当前仓库虽然已引入 `django.contrib.auth`，但服务层并没有任何正式的用户、角色或项目授权事实对象；如果直接把权限判断散落在视图层，会快速破坏 `scenario_service` 现有事实源设计。
- 当前最稳妥的首批实现不是立刻接完整登录，而是先在服务层补“项目角色授权记录 + 审计日志记录 + 显式 actor 门禁”三件套：
  - 角色授权记录承接 `viewer / editor / executor / reviewer / scheduler / project_admin`；
  - 审计日志记录关键动作的成功与阻断；
  - 审核、执行和查看先接入项目级授权校验。
- 由于现有接口普遍已经带有 `reviewer` 等显式操作者字段，`P1-G1` 第一批实现继续采用 `actor / reviewer / operator` 显式传参，比强行接入完整登录态更符合当前阶段的增量式改造原则。
- 用户已明确要求进入 `P1` 正式开发与测试，因此当前不再停留在计划讨论；实施计划已落到 `docs/superpowers/plans/2026-04-15-v3-p1-g1-permission-audit.md`，后续可直接按该文件执行。
- 本轮真实兼容性问题不是权限模型本身，而是历史 V2/P0 测试默认把 `qa-owner / qa-reviewer` 视为内置操作者；如果完全改成“无授权即拒绝”，会直接打回既有审核主链路。
- 当前已采用“历史内置操作者兼容模板 + P1 新角色授权记录并存”的折中方案：
  - `qa-owner` 保持全量治理动作权限；
  - `qa-reviewer` 保持查看/审核权限；
  - 新增 `viewer / editor / executor / reviewer / scheduler / project_admin` 继续走显式项目角色授权记录。
- 审计日志若写在 `@transaction.atomic` 内部，越权异常会导致阻断日志一起回滚；本轮已将授权校验前移到事务外，确保被阻断的动作也能真正留下审计记录。
- 当前 `P1-G1` 首批结果已成立：
  - `service_tests/test_v3_p1_permission_audit.py` -> `3 passed`
  - `service_tests` -> `35 passed`
  - `tests/platform_core` -> `71 passed`
  - `tests` -> `79 passed`
  - `api_test/tests` -> `39 passed`

## 2026-04-15 V3 P0 详细验收与数据保留发现
- `platform_service.test_settings` 虽然已经切到 MySQL，但如果继续沿用 `pytest.mark.django_db + 清库夹具`，测试数据仍不会保留；本轮已确认真正的冲突点在 `service_tests/conftest.py` 和固定业务标识，而不只是数据库引擎本身。
- 当前更稳妥的数据保留方案不是强行让 pytest-django 接管正式库，而是：
  - 取消 `service_tests` 的 `django_db` 标记与清库逻辑；
  - 通过 `django_db_blocker.unblock()` 直接访问正式 MySQL；
  - 为每条服务测试生成运行期唯一 `case_id / case_code / capture_name`。
- `TrafficCaptureImportView` 原先虽然接收 `project_code / environment_code / scenario_set_code`，但后端会直接忽略这些字段并总是落默认项目；本轮已补齐到 `scenario_service.views` 与 `scenario_service.services.import_traffic_capture()`。
- `scenario_service/templates/scenario_service/workbench.html` 原先默认示例 ID 固定，保留测试数据后重复点“导入功能用例”会高频撞重复；当前已改为页面加载和成功导入后都自动换新示例标识。
- 当前正式 MySQL 留存数据快照表明数据保留策略已生效：
  - `project_count=21`
  - `environment_count=21`
  - `scenario_set_count=21`
  - `baseline_version_count=22`
  - `migration_count=4`
  - `scenario_count=40`
  - `execution_count=16`
- 最新一轮正式 MySQL 详细验收结果为：
  - `P0专项=11 passed`
  - `service_tests=32 passed`
  - `tests/platform_core=71 passed`
  - `tests=79 passed`
  - `api_test/tests=39 passed`
  - 浏览器主链路已通过，执行结果为 `passed`

## 2026-04-14 V3 详细测试文档收口发现
- `product_document/测试文档/详细测试用例说明书(V3-总索引).md`、`详细测试用例说明书(V3-P0).md`、`详细测试用例说明书(V3-P1).md`、`详细测试用例说明书(V3-P2).md` 已建立，形成 V3 当前测试文档包。
- 对四份 V3 测试文档执行 `rg -n "TODO|TBD|待补|待定"` 未发现占位词残留。
- 三份阶段详细测试文档共定义 65 个用例：`P0=23`、`P1=25`、`P2=17`。
- 所有用例编号均符合 `TC-V3-Px-LAYER-XXX` 规则，当前未发现重复编号。
- 三份阶段文档中的跨用例引用均已定义，未发现悬空引用。
- `详细测试用例说明书(V3-总索引).md` 原结论段仍停留在“下一步编写 P0 / P1 / P2 文档”，已在本轮同步修正为“文档包已建立，待评审后进入 P0 开发准备”。
- `V3阶段工作计划文档.md` 原 `V3-DOC-005`、`V3-TEST-002`、`V3-TEST-003`、`V3-TEST-004`、`V3-TEST-005` 仍停留在待开始状态，已在本轮同步回填为已完成。
- `README.md` 与 `全阶段工作规划文档.md` 原先仅反映“V3 阶段工作计划已确认”，本轮已补记 V3 详细测试文档包已建立的当前状态。
- 本轮未执行任何 V3 自动化测试；当前阶段仍属于文档与测试设计收口阶段，不应新增实现或验收结果口径。

## 2026-04-14 V3 P0 开发准备发现
- 当前 `scenario_service` 已经是 V2 的统一事实源承载层，P0 最合理的落点不是新建平行模块，而是在现有 `ScenarioRecord / ScenarioExecutionRecord` 等模型基础上扩展项目、环境、场景集与基线版本治理。
- 当前 `scenario_service/views.py` 和 `platform_service/urls.py` 已经暴露 `/api/v2/scenarios/*` 与 `/ui/v2/workbench/`，说明 P0 的“最小治理入口”可以在现有工作台基础上迭代，而不是另起一套前端工程。
- 当前 `scenario_service/templates/scenario_service/workbench.html` 明确仍是 V2 口径，页面只支持导入、审核、执行和结果回看；P0 需要把它提升为项目切换、环境切换、场景集筛选和版本查看可见的治理入口。
- 当前 `scenario_service/services.py` 的执行默认工作区由 `_build_default_workspace_root()` 生成，但尚未引入项目级、环境级和场景集级隔离信息；P0 的工作区隔离和执行记录隔离需要首先从这里切入。
- 当前服务测试集中已有 `test_service_persistence.py`、`test_scenario_query_contract.py`、`test_execution_closure.py`、`test_workbench_ui.py` 等稳定切点，适合按 TDD 继续扩展 P0 模型、API、隔离和 UI 用例。
- 当前 `platform_service/urls.py` 仍统一挂载 `/api/v2/scenarios/` 与 `/ui/v2/workbench/`；P0 先在既有入口上做治理增强更稳妥，暂不额外引入 `v3` 路由层分叉。
- 当前服务测试使用 `platform_service.test_settings` 下的 SQLite + `MIGRATION_MODULES = {"scenario_service": None}`，适合快速做 TDD；而正式迁移一致性仍需继续通过 `manage.py makemigrations --check --dry-run --settings=platform_service.migration_settings` 验证。

## 2026-04-14 V3 P0 第一批实现发现
- 第一批红灯 `service_tests/test_v3_p0_governance_flow.py::test_import_functional_case_assigns_default_governance_context` 失败原因为场景详情缺少 `project / environment / scenario_set / baseline_version`，说明 P0 缺口准确落在服务摘要层而不是测试误报。
- 已新增 `scenario_service/governance.py`，开始把默认项目引导、治理上下文解析和基线版本切换从 `scenario_service/services.py` 中拆出，避免继续堆叠单文件逻辑。
- 已在 `scenario_service/models.py` 中补入 `ProjectRecord`、`TestEnvironmentRecord`、`ScenarioSetRecord`、`BaselineVersionRecord`、`GovernanceMigrationRecord` 以及 `ScenarioRecord / ScenarioExecutionRecord` 的治理关联字段。
- 当前选择继续沿用现有 `/api/v2/scenarios/*` 入口，但在返回结构中增加 V3 P0 治理上下文；这是一种“服务事实源升级、入口路径暂不分叉”的兼容策略。
- 第一批隔离红灯暴露了一个真实实现问题：`BaselineVersionRecord` 的默认 `baseline_version_id` 初版写成全局常量，导致跨项目创建场景集时触发唯一键冲突；已修正为按 `项目 + 场景集 + 版本` 生成稳定标识。
- 已把 `request_execution()` 收紧为必须显式接收 `project_code` 和 `environment_code`，并在执行记录中写回 `project / environment / scenario_set / baseline_version / workspace_root`，开始满足 P0 对执行上下文硬绑定的要求。
- 当前第一批已通过的新增测试包括：
  - 默认治理上下文导入
  - 治理上下文查询
  - 基线版本激活
  - 同名场景跨项目导入隔离
  - 缺少项目 / 环境上下文的执行阻断
  - 项目级工作区与结果上下文隔离

## 2026-04-14 V3 P0 首轮验收发现
- 当前 `P0` 选择继续在现有 `/api/v2/scenarios/*` 和 `/ui/v2/workbench/` 上增量升级是正确的，服务回归已恢复为 `30 passed`，说明没有把 V2 事实源升级成一套平行系统。
- `request_execution()` 的显式上下文绑定要求会直接打破旧的无上下文执行测试；本轮已选择“更新旧测试契约显式传 `project_code / environment_code`”而不是回退 P0 约束，这个取舍与 P0 验收标准一致。
- `scenario_service` 已补齐此前缺失的导出边界能力：
  - 新增 `<scenario_id>/export/` 路由；
  - 导出路径按 `项目 / 环境 / 场景集` 归档；
  - 跨项目导出请求会返回 `project_context_mismatch`。
- 默认工作区路径已从旧的“场景编码 + 随机后缀”收口为 `report/scenario_workspaces/<project>/<environment>/<scenario_set>/...`，浏览器端与服务层回写路径现在能直接体现治理归属。
- 浏览器端最小治理入口已完成真实主链路冒烟：导入、审核、执行、结果回看都能直接带出 `project / environment / scenario_set / baseline_version` 上下文，截图证据已保存在 `.pytest_tmp/browser_smoke/v3_p0_workbench_smoke.png`。
- 本地 MySQL 基线已完成 `scenario_service.0005` 落库，新增表包括：
  - `scenario_service_projectrecord`
  - `scenario_service_testenvironmentrecord`
  - `scenario_service_scenariosetrecord`
  - `scenario_service_baselineversionrecord`
  - `scenario_service_governancemigrationrecord`
- 当前残余风险已明显收敛，但仍需在向用户汇报时明确：
  - 当前已补齐 MySQL 浏览器自动化主链路冒烟，SQLite 路径已从 `platform_service.test_settings` 移除；
  - 后续若继续扩展 UI 自动化，应继续复用正式 MySQL 基线，而不是重新引入独立测试库。

## 2026-04-15 MySQL-only 测试切换发现
- `platform_service.test_settings` 原先仍指向 SQLite，并通过 `MIGRATION_MODULES = {"scenario_service": None}` 跳过真实 migration；这与“所有测试和数据必须使用正式 MySQL 数据库”的新要求冲突。
- 本轮已新增 `test_platform_service_test_settings_also_use_formal_mysql_baseline`，并完成红绿验证，确保测试设置固定为：
  - `ENGINE = django.db.backends.mysql`
  - `NAME = api_test_platform`
  - `MIGRATION_MODULES = {}`
- 当前 MySQL-only 切换后的最新验证结果为：
  - `service_tests=31 passed`
  - `tests/platform_core=71 passed`
  - `tests=79 passed`
  - `api_test/tests=39 passed`
  - `makemigrations --check --dry-run` -> `No changes detected in app 'scenario_service'`
- 当前工作台 `/ui/v2/workbench/` 已在 `platform_service.test_settings` 指向正式 MySQL 后，重新完成“导入 -> 审核通过 -> 触发执行 -> 回看结果”主链路浏览器冒烟，截图为 `.pytest_tmp/browser_mysql_smoke/v3_p0_workbench_mysql_smoke.png`。

## 2026-04-03 V1 正式验收复验
- `jsonplaceholder.typicode.com` 相关公网用例在代理开启下稳定通过，`cd api_test && python -m pytest tests -m jsonplaceholder -v --basetemp ..\\.pytest_tmp\\api_test_jsonplaceholder_acceptance` 结果为 `12 passed, 27 deselected`。
- `python api_test/run_test.py --public-baseline` 与 `cd api_test && python run_test.py --public-baseline` 在代理开启下均为 `12 passed, 27 deselected`。
- 直接把仓库默认配置改为 `proxy.enabled=true` 后运行 `api_test/tests` 会触发 `test_load_api_config_reads_default_json_file` 失败；这不是功能缺陷，而是默认配置契约测试在阻止默认值漂移。
- 按“公网用例开启代理 -> 执行完成后恢复默认关闭 -> 再执行非公网配置/治理回归”的流程，可同时满足公网连通性和默认配置契约：
  - `cd api_test && python -m pytest tests -m "not jsonplaceholder" -v --basetemp ..\\.pytest_tmp\\api_test_non_jsonplaceholder_acceptance` -> `27 passed, 12 deselected`
  - `cd api_test && python -m pytest tests/test_config_loader.py -v --noconftest --basetemp ..\\.pytest_tmp\\config_loader_after_proxy_restore_fix` -> `6 passed`
- V1 正式验收复验的综合结果为：
  - `python -m pytest tests/platform_core -v --basetemp .pytest_tmp/platform_core_v1_acceptance_proxy_20260403` -> `63 passed`
  - `python -m pytest tests -v --basetemp .pytest_tmp/root_v1_acceptance_proxy_20260403` -> `70 passed`
- 已新增 `product_document/阶段文档/V1阶段正式验收报告.md` 作为当前轮正式验收输出。

## V1 状态判断
- `product_document/阶段文档/V1阶段工作计划文档.md` 已切换为 V1 验收版，当前阶段判断为“V1 已完成”。
- `product_document/测试文档/详细测试用例说明书(V1).md` 已同步到最终验收状态，P0 全部通过，P1/P2 增强项已转入 V2 承接。

## 代码发现
- `platform_core/renderers.py` 当前已支持 `business_rule(non_empty_string)` 与 `business_rule(positive_integer)`，并会按规则代码自动生成匹配的最小假响应值。
- `platform_core/rules.py` 当前已允许 `business_rule.rule_code` 的两类最小取值：`non_empty_string` 与 `positive_integer`。
- `platform_core/services.py` 的 `run_document_pipeline_summary()` 和 `inspect_workspace_summary()` 已补齐 `source_type`、`execution_id` 和资产聚合字段，当前摘要输出可直接被后续服务接口消费。
- `platform_core/pipeline.py` 当前会在目录级执行结束后回写各生成记录的 `execution_status`。
- `api_test/requirements.txt` 已改为固定版本约束，并已删除未使用的 `rsa` 依赖。

## 本轮设计结论
- 采用最小收口方案，不扩展解析器自动推断，不做 DSL。
- 继续为 `business_rule` 增加 `positive_integer` 规则代码，用于验证“非空字符串之外的第二档规则”。
- 对服务摘要补充更稳定的资产聚合信息，用于把当前 V1 输出进一步收敛到后续 Web / 客户端可直接承接的结构。
- 通过新增治理测试把依赖约束固化下来，避免后续再次回退到宽松版本和无用依赖。

## 已完成验证
- 定向红灯：`python -m pytest tests/platform_core/test_models.py tests/platform_core/test_templates_and_rules.py tests/platform_core/test_services_and_assets.py tests/test_dependency_governance.py -k "positive_integer or inventory_summary or source_type or execution_id or asset_type_breakdown or dependency_governance" -v --basetemp .pytest_tmp/v1_final_closure_red`
  - 结果：`1 error`
  - 含义：`WorkspaceAssetInventorySummary` 尚未实现，确认新增摘要模型确实缺失
- 定向绿灯：同口径 `... --basetemp .pytest_tmp/v1_final_closure_green`
  - 结果：`6 passed`
- 全量回归：
  - `python -m pytest tests/platform_core -v --basetemp .pytest_tmp/platform_core_v1_final_closure_full` -> `63 passed`
  - `python -m pytest tests -v --basetemp .pytest_tmp/root_v1_final_closure_full` -> `70 passed`
  - `python -m pytest api_test/tests -v --basetemp .pytest_tmp/api_test_v1_final_closure_full` -> `39 passed`
- `python api_test/run_test.py --public-baseline` -> `12 passed, 27 deselected`
- `cd api_test && python run_test.py --public-baseline` -> `12 passed, 27 deselected`

## 2026-04-07 V1 进度分析补充发现
- `product_document/阶段文档/V1阶段工作计划文档.md`、`product_document/阶段文档/V1实施计划与开发任务拆解说明书.md`、`product_document/测试文档/详细测试用例说明书(V1).md` 和 `product_document/阶段文档/V1阶段正式验收报告.md` 的当前口径一致，均明确写明截至 2026-04-03 V1 已完成并已正式验收通过。
- `README.md` 的“当前状态”与正式验收报告保持一致，仍以 2026-04-03 作为最新综合验证日期，没有出现后续回退口径。
- 代码目录侧已存在完整的 V1 最小闭环实现与配套测试资产：
  - `platform_core/` 覆盖模型、解析、模板、规则、流水线、执行器、CLI、资产管理和服务层。
  - `tests/platform_core/` 覆盖模型、模板/规则、流水线、服务/资产和解析输入。
  - 根目录存在中文注释治理、依赖治理和通用框架清理治理测试。
  - `api_test/tests/` 覆盖配置加载、HTTP 底座治理、公共工具、公开站点资源和执行入口。
- `api_test/api_config.json` 当前仍保持 `proxy.enabled=false`，与正式验收报告要求的默认配置契约一致。
- `api_test/requirements.txt` 当前为固定版本约束，符合仓库依赖治理规则，且未见 `rsa` 残留。
- `git log --format='%h %ad %s' --date=short -5` 显示主线最近一次提交为 2026-04-03 的“文档：同步V1正式验收复验结果并新增正式验收报告”，说明当前仓库没有晚于正式验收的 V1 主线推进记录。
- `git status --short` 当前仅显示 `?? .idea/`，未见新的 V1 代码或文档改动，表明仓库现状基本停留在正式验收后的稳定状态。
- 因未在本轮重新执行 pytest，本轮结论应表述为“当前仓库状态与 2026-04-03 正式验收结论一致”，而不是“2026-04-07 已重新完成全量回归”。

## 2026-04-07 V2 计划文档分析发现
- `product_document/阶段文档/V2阶段工作计划文档.md` 当前只有“简版规划（待后续细化）”，仅列出 7 个方向性要点，没有详细范围、详细设计、测试方案、进度记录、风险记录，不满足仓库对阶段工作计划文档的要求。
- `product_document/阶段文档/全阶段工作规划文档.md` 当前仍写着“阶段 1 收尾 + 阶段 2 推进中”，并将 V2 标记为“未开始”，这与 `2026-04-03` 已完成 V1 正式验收的事实不一致，后续完善 V2 文档时应同时规划对该总入口文档的同步修正。
- `product_document/产品需求说明书(全局).md` 已给出较清晰的 V2 承接方向：功能测试用例驱动、抓包驱动、动态变量与依赖编排、Web/Windows 形态增强、审核预览修订确认、执行调度与结果管理。
- 从全局产品说明书和 V1 文档交叉看，V2 不是“继续补 V1 小功能”，而应是从“文档驱动最小闭环”升级到“多输入路线 + 场景编排 + 产品化入口”的阶段。
- 当前 V2 文档最缺的不是一句目标描述，而是完整的：
  - 阶段定位与进入条件
  - 做什么 / 不做什么
  - 能力任务分组与实施顺序
  - 测试策略、验收标准、风险与阻塞记录
  - 与 V1/V3 的边界说明

## 2026-04-07 V2 承接设计补充发现
- `总体架构设计说明书.md` 已经给出 V2 的推荐形态：在 V1 基础上增强 Django + DRF 应用服务层、Web 界面、更完整资产管理、功能测试用例驱动 / 抓包驱动接入、Windows 应用封装增强。这意味着 V2 需要同时覆盖核心引擎扩展和产品入口扩展，不能只写算法侧增强。
- `中间模型设计说明书.md` 明确将 `VariableBinding`、`DependencyLink`、`TestScenario`、`ScenarioStep`、`ReviewRecord` 作为 V1 预留、V2 应重点增强的模型，这些对象应成为 V2 计划文档中的核心任务组，而不是散落在“后续补充方向”里。
- `模板体系与代码生成规范说明书.md` 明确 V1 暂未强制落地的模板包括：场景测试高级模板、动态变量模板、审核记录模板、高级报告模板、抓包驱动专用模板；这些正好构成 V2 模板体系扩展的主任务清单。
- `V1阶段工作计划文档.md` 当前已经把 V2 承接建议压缩为 4 个点：更复杂 `business_rule` DSL、更深层结构断言、变量提取与依赖编排、服务接口产品化边界与 Web / 客户端承接。V2 正式计划文档需要把这 4 个点展开成可执行的任务组、测试组和验收标准。
- `详细测试用例说明书(V1).md` 已将“场景驱动测试、变量绑定测试、依赖编排测试、抓包驱动闭环测试”明确列为 V2 逐步增强项，因此 V2 文档应从一开始就带上测试编号体系和阶段测试策略，不能再等实现后补。
- 当前最合理的 V2 主线顺序不是“先 Web，再能力”，而应更接近：
  1. 场景与依赖中间模型补齐；
  2. 场景生成 / 抓包解析 / 动态变量能力进入闭环；
  3. 审核、预览、修订与确认机制进入资产生命周期；
  4. Django + DRF 服务层与 Web / Windows 交互入口承接这些稳定能力；
  5. 最后补产品化执行调度和结果展示增强。

## 2026-04-07 外部参考发现
- `microsoft/restler-fuzzer` 展现的关键模式是“先从 OpenAPI 编译为可执行语法，再按 `test -> fuzz-lean -> fuzz` 分级执行”，并强调 stateful / producer-consumer 依赖推断。这对我们 V2 的“依赖编排优先于深度 UI”判断有直接参考价值。来源：https://github.com/microsoft/restler-fuzzer
- `alufers/mitmproxy2swagger` 展现的关键模式是“抓包 -> 生成路径模板候选 -> 人工筛选/修正 -> 二次生成 OpenAPI”，说明抓包驱动路线不应直接一步到最终资产，中间必须有清洗、去重和确认层。来源：https://github.com/alufers/mitmproxy2swagger
- `Schemathesis` 强调从 OpenAPI / GraphQL schema 自动生成大量测试用例，并提供 CLI / CI 入口，这说明契约驱动验证能力更适合作为 V2 执行增强和服务入口增强的参考，而不是替代我们现有模板化资产生成主线。来源：https://github.com/schemathesis
- `openapi-python-client` / `OpenAPI Generator` 的价值更多在“模板与生成器解耦、配置驱动生成、tag/module 归组策略”，可作为我们 V2 优化模板体系和模块归组配置的参考，但不适合直接替代平台化资产治理层。来源：https://github.com/openapi-generators/openapi-python-client 、https://github.com/OpenAPITools/openapi-generator

## 2026-04-08 V2 方案已确认项
- V2 同时覆盖核心能力和产品入口，但阶段优化重点放在核心能力。
- Web / Windows 入口目标深度定为“可用型入口”：支持导入、预览、审核确认、执行、结果查看，不追求完整产品化体验。
- V2 第一主线采用“功能测试用例驱动优先”；抓包驱动纳入 V2，但不作为第一主线。
- V2 文档组织方式采用“方案1：核心能力分层推进型”。
- V2 服务化与数据持久化深度采用“方案A：核心数据先服务化落地”，Django + DRF + MySQL 进入阶段必达范围，本地工作区降为导入导出与执行载体。
- V2 审核确认链路采用“方案B：默认可审核、关键节点需确认”。
- V2 修订能力采用“方案B：结构化修订 + AI 辅助改写并存”，但 AI 输出不能直接成为正式事实资产。
- V2 任务组建议已经过用户确认，顺序为：
  1. 场景驱动核心模型扩展
  2. 功能测试用例驱动闭环
  3. 审核、预览、修订与确认链路
  4. 服务化与数据持久化落地
  5. 抓包驱动草稿化接入
  6. 可用型 Web / Windows 入口

## 2026-04-08 正式文档落地发现
- `product_document/阶段文档/V2阶段工作计划文档.md` 已由“简版规划（待后续细化）”升级为正式规划版，已补齐：
  - 阶段定位
  - 进入条件与承接关系
  - 总目标与不做项
  - 正式闭环定义
  - 范围拆解
  - 详细设计方案
  - 开发方案
  - 测试方案
  - 开发 / 测试进度记录
  - 风险与阻塞记录
  - V3 承接建议
- `product_document/阶段文档/全阶段工作规划文档.md` 已同步修正为：
  - 阶段 0、阶段 1、阶段 2 均为已完成
  - 阶段 3 为“V2 阶段规划与能力增强阶段（正式规划版已建立，待进入实施）”
  - 阶段 4 为 V3 平台化深化承接方向
- `README.md` 已同步补记：
  - 2026-04-08 当前仓库重点已切换到 V2 正式规划
  - 当前已确认方向新增 V2 主线说明
  - 建议查看顺序新增 `V2阶段工作计划文档.md` 与 V2 设计稿
- 本轮未执行测试；本轮属于文档同步与阶段规划落地，不应新增测试结果口径。

## 2026-04-08 V2 测试文档设计发现
- `详细测试用例说明书(V2).md` 应按 V2 范围重写，而不是在 V1 文档上继续追加；原因是 V2 已从“文档驱动最小闭环”升级为“场景驱动 + 服务化 + 可用型入口承接”。
- V2 测试分层已收敛为 8 层：文档与阶段约束、中间模型、解析与标准化、模板与规则、服务层与持久化、执行与调度、交互入口、主线集成闭环。
- V2 编号体系建议采用：
  - `TC-V2-DOC-*`
  - `TC-V2-MODEL-*`
  - `TC-V2-PARSE-*`
  - `TC-V2-TPL-*`
  - `TC-V2-RULE-*`
  - `TC-V2-SVC-*`
  - `TC-V2-EXEC-*`
  - `TC-V2-UI-*`
  - `TC-V2-INT-*`
- 服务层与持久化测试需要独立成组，不能并入执行层；原因是“数据库事实源 + DRF 契约 + 状态回写”是 V2 的核心边界，不再是 V1 那种附属摘要能力。
- Web / Windows 入口测试在 V2 仍建议统一为“交互入口测试”，暂不拆分双端独立编号；原因是 V2 重点验证流程一致性和服务复用，不是双端产品体验细化。
- 抓包驱动的“动态值候选识别”建议拆成两档：
  - 基础候选识别进入 P0，用于保证抓包草稿化闭环成立；
  - 复杂噪声清洗、低置信度候选筛选进入 P1。
- AI 辅助改写在 V2 测试中重点验证门禁、留痕、规则校验和回退能力，不把“改写质量优劣”作为阶段必达测试目标。
- 数据库事实源与本地工作区执行载体的一致性测试，P0 先覆盖状态、摘要、执行结果和导出路径一致；版本冲突、回滚和跨版本演进建议留到 P1 / V3。
- `product_document/测试文档/详细测试用例说明书(V2).md` 已正式落地，并已同步更新 `product_document/阶段文档/V2阶段工作计划文档.md` 与 `README.md` 的相关口径。

## 2026-04-08 V2 第一实施子阶段开发发现
- 当前 `platform_core/models.py` 仍完全是 V1 模型集合，尚未落地 `TestScenario`、`ScenarioStep`、`VariableBinding`、`DependencyLink`、`ReviewRecord`、状态对象和场景服务摘要对象。
- 当前 `platform_core/services.py` 仍是 V1-only 口径：`supported_routes()` 中 `functional_case=False`，`run_functional_case_pipeline()` 直接抛 `NotImplementedError`。
- 当前 `platform_core/parsers.py` 只有 `OpenAPIDocumentParser`，没有功能测试用例输入到场景草稿的解析器；继续把这部分塞进 `parsers.py` 会让单文件职责继续膨胀，第一实施子阶段更适合新增 `platform_core/functional_cases.py` 聚焦承载。
- `详细测试用例说明书(V2).md` 中最适合作为第一批落地点的 P0 项是：
  - `TC-V2-MODEL-011`
  - `TC-V2-MODEL-012`
  - `TC-V2-RULE-011`
  - 功能测试用例主线对应的 `TC-V2-PARSE-001` 到 `TC-V2-PARSE-008` 的最小子集
- 本轮不建议一开始就直接实现 `TC-V2-SVC-011`、`TC-V2-SVC-012` 所代表的完整 DRF 契约；更稳妥的顺序是先稳定服务对象和状态摘要，再在下一子阶段补正式接口层。
- 已新增实施计划文件 `docs/superpowers/plans/2026-04-08-v2-phase-1-scenario-core.md`，当前执行方式为“同一会话内 inline TDD 实施”，不再额外停下来做执行方式选择。
- 首批红灯验证结果如下：
  - `tests/platform_core/test_models.py -k "v2_scenario"`：`ImportError`，缺少 `DependencyLink` 等 V2 模型
  - `tests/platform_core/test_parser_inputs.py -k "functional_case_parser"`：`ModuleNotFoundError`，缺少 `platform_core.functional_cases`
  - `tests/platform_core/test_services_and_assets.py -k "current_capabilities or functional_case_draft_summary or invalid_scenario_status_transition"`：`ImportError`，缺少 `ScenarioServiceSummary`
- 首批最小实现已落地：
  - `platform_core/models.py`：新增场景核心模型、状态对象、问题对象和服务摘要对象
  - `platform_core/functional_cases.py`：新增结构化功能测试用例草稿解析器
  - `platform_core/rules.py`：新增非法状态流转校验
  - `platform_core/services.py`：开放功能用例草稿摘要路线，并保留抓包路线阻断
- `TestScenario` 作为模型名称会触发 pytest 对“Test*”类的默认收集告警，已通过 `__test__ = False` 显式关闭该类的测试收集，避免后续回归噪声。
- 首批验证与回归结果：
  - `python -m pytest tests/platform_core/test_models.py -k "v2_scenario" -v --basetemp .pytest_tmp/v2_phase1_models_green` -> `2 passed`
  - `python -m pytest tests/platform_core/test_parser_inputs.py -k "functional_case_parser" -v --basetemp .pytest_tmp/v2_phase1_parser_green` -> `2 passed`
  - `python -m pytest tests/platform_core/test_services_and_assets.py -k "current_capabilities or functional_case_draft_summary or invalid_scenario_status_transition" -v --basetemp .pytest_tmp/v2_phase1_service_green` -> `3 passed`
  - `python -m pytest tests/platform_core -v --basetemp .pytest_tmp/v2_phase1_platform_core_full` -> `68 passed`
  - `python -m pytest tests -v --basetemp .pytest_tmp/v2_phase1_root_full` -> `75 passed`
  - `python -m pytest api_test/tests -v --basetemp .pytest_tmp/v2_phase1_api_test_full` -> `39 passed`
- 本轮仍保留的已知空白：
  - 还没有正式的 Django + DRF + MySQL 承载层
  - 还没有 `TC-V2-SVC-011`、`TC-V2-SVC-012` 对应的正式 API 契约实现
  - 还没有结构化修订持久化、抓包草稿化接入和可用型入口实现

## 2026-04-08 V2 第二实施子阶段开发发现
- 当前全局 Python 环境中安装的 `Django 6.0.1` 发布于 2026-01-06，按仓库依赖安全规则属于禁止直接使用的版本；第二子阶段必须改为仓库内独立虚拟环境，并固定到 2025 年及以前的版本。
- 当前仓库没有任何 Django 项目骨架、`manage.py`、`settings.py`、`urls.py` 或 DRF 路由定义，说明 `TC-V2-SVC-011`、`TC-V2-SVC-012` 目前仍是纯文档状态。
- 当前仓库也没有根级依赖文件来承载服务层依赖，只有 `api_test/requirements.txt`；第二子阶段需要新增独立的服务层依赖文件，并把版本治理纳入自动化测试。
- 为避免影响现有根测试和 V1 底座回归，第二子阶段的 Django/DRF 接口测试更适合放在单独的 `service_tests/` 路径下，并使用独立虚拟环境执行。
- 已新增第二子阶段实施计划文件 `docs/superpowers/plans/2026-04-08-v2-phase-2-service-contract.md`，当前计划范围聚焦：
  - 服务层依赖与环境治理
  - Django/DRF 最小骨架
  - 场景草稿持久化
  - 导入、详情、审核、执行请求与结果查询接口

## 2026-04-08 V2 第二实施子阶段补充发现
- `requirements-platform-service.txt` 仅锁定 Django/pytest 直系依赖还不够；`MarkupSafe`、`annotated-types`、`pydantic-core`、`typing-extensions` 和 `pytest-asyncio` 也需要显式固定版本，才能满足仓库的依赖安全规则并消除测试环境告警。
- `PyYAML==6.0.0` 在当前 Python 3.12 Windows 服务环境下会退回源码构建并失败；服务层依赖已调整为 `PyYAML==6.0.1`，并通过依赖治理测试锁定。
- `platform_service/settings.py` 中单纯调用 `pymysql.install_as_MySQLdb()` 仍不足以通过 Django 5.2.9 的 MySQL 后端版本门槛；需要进一步补齐 `version_info` / `__version__` 兼容补丁。
- 当前第二子阶段的首批可运行范围已经成立：
  - `service_tests/test_service_persistence.py` 覆盖场景草稿持久化；
  - `service_tests/test_drf_contract.py` 覆盖导入、详情、审核、执行请求与结果查询接口；
  - `service_tests/test_service_bootstrap.py` 覆盖 MySQL 启动兼容补丁。
- 已新增 `platform_service/migration_settings.py` 并生成 `scenario_service/migrations/0001_initial.py`，当前可通过 `manage.py makemigrations --check --dry-run --settings=platform_service.migration_settings` 验证迁移文件与模型保持一致。
- 已完成回归结果：
  - `.venv_service\\Scripts\\python.exe -m pytest service_tests -v --ds=platform_service.test_settings --basetemp .pytest_tmp/v2_phase2_service_tests` -> `4 passed`
  - `python -m pytest tests/platform_core -v --basetemp .pytest_tmp/v2_phase2_platform_core_regression` -> `68 passed`
  - `python -m pytest tests -v --basetemp .pytest_tmp/v2_phase2_root_regression` -> `76 passed`
  - `python -m pytest api_test/tests -v --basetemp .pytest_tmp/v2_phase2_api_test_regression` -> `39 passed`
- 当前仍需记录的后续问题：
  - 默认 MySQL 认证链路在本地环境下仍未完成正式验收；
  - 真实 MySQL 结果回写、审核修订持久化、抓包草稿化接入和可用型入口仍待下一子阶段继续实现。

## 2026-04-09 V2 第三实施子阶段启动发现
- 当前第三子阶段的目标已经在 `docs/superpowers/plans/2026-04-08-v2-phase-3-execution-closure.md` 中收敛为最小执行闭环，不包含抓包驱动和正式前端实现。
- `scenario_service/services.py` 中的 `request_execution()` 现状仍只是创建一条 `ScenarioExecutionRecord`，并把场景状态更新为 `not_started`；尚未接入工作区导出、pytest 执行和结果回写。
- 工作区中已存在 `service_tests/test_execution_closure.py` 红灯测试草稿，覆盖：
  - 已确认场景执行后导出工作区、生成测试文件、产出 `asset_manifest.json`、执行通过并回写 `report_path`；
  - 不受支持的公开基线操作绑定在执行前被阻断。
- 当前第三子阶段最适合复用的底座能力是：
  - `platform_core/assets.py` 中的工作区与资产清单能力；
  - `platform_core/executors.py` 中的 pytest 执行与 JUnit 统计能力；
  - `platform_core/runtime/client.py` 中的最小 HTTP 客户端。
- 当前未落地但必须补齐的能力包括：
  - 面向场景步骤的最小测试模板；
  - 场景步骤到 JSONPlaceholder 公开基线操作的绑定目录；
  - 场景变量提取与下游路径/查询参数注入；
  - 服务层对执行结果的数据库回写。
- 第三子阶段首轮红灯测试已经确认失败原因准确：
  - `service_tests/test_execution_closure.py` 失败于 `FunctionalCaseScenarioService.request_execution()` 还不接受 `workspace_root` 参数；
  - `service_tests/test_drf_contract.py -k result_summary` 失败于结果接口仍返回 `execution_status=not_started`，说明执行闭环和结果回写尚未实现。
- 这组红灯表明当前最小实现应优先补齐：
  - 服务层执行请求签名扩展；
  - 场景测试文件导出；
  - pytest 执行；
  - 结果统计与 `report_path` 回写；
  - DRF 执行入口透传 `workspace_root`。
- 第三子阶段实现过程中暴露出新的服务运行时依赖缺口：
  - 生成测试在 `.venv_service` 子进程中导入 `platform_core.runtime.client.ApiClient` 时失败；
  - 根因不是业务逻辑，而是 `.venv_service` 尚未安装 `requests` 及其运行依赖；
  - 该问题已通过为 `requirements-platform-service.txt` 补齐固定版本的 `requests/urllib3/charset-normalizer/certifi/idna` 并重建环境口径解决。
- 当前第三子阶段首批执行闭环已经成立：
  - 已确认场景可导出为本地 pytest 工作区；
  - 生成测试文件位于 `generated/tests/test_<scenario_code>.py`；
  - 执行后会生成 `asset_manifest.json`、JUnit 报告和 `execution_record.json`；
  - `ScenarioRecord` / `ScenarioExecutionRecord` 会回写 `workspace_root`、`report_path`、`execution_status`、`passed_count`、`failed_count`、`skipped_count` 与 `latest_execution_id`。
- 当前最小公开基线操作目录已支持：
  - `operation-get-user`
  - `operation-list-user-todos`
- 仍待后续子阶段继续补齐的执行侧能力包括：
  - 更多公开基线操作目录；
  - 更复杂的变量注入与依赖编排；
  - 可选步骤、重试策略和执行历史增强；
  - 数据库与真实 MySQL 环境的一致性正式验收。

## 2026-04-09 本地 MySQL 初始化与正式验收发现
- 本机 `MySQL84` 服务已存在且处于 `Running / Automatic` 状态，说明当前环境不需要重新安装 MySQL，只需完成服务化基线初始化。
- `platform_service` 账号在 MySQL 8.4 中默认使用 `caching_sha2_password`，`.venv_service` 中的 `PyMySQL==1.0.2` 在缺少 `cryptography` 时无法完成该认证链路。
- 直接切换到 `mysql_native_password` 不可作为当前环境的最小解，因为本机 MySQL 8.4 实例中该插件状态为 `DISABLED`，且当前用户态无法改写服务配置文件启用插件。
- 更稳妥的收口方案是补齐 `cryptography==43.0.3`、`cffi==1.17.1`、`pycparser==2.22`，并把它们纳入 `requirements-platform-service.txt` 与依赖治理测试。
- 本机 `pip` 默认配置指向清华镜像且超时为 `6000` 秒，会导致安装命令长时间挂起；改为一次性指定 `https://pypi.org/simple` 和较短超时后，依赖安装可稳定完成。
- 真实 MySQL 验收已经成立：
  - `platform_service@127.0.0.1` 可连接 `api_test_platform`
  - `manage.py migrate --settings=platform_service.settings` 全部成功
  - `manage.py showmigrations --settings=platform_service.settings` 全部为 `[X]`
  - 基于真实 MySQL 的 `FunctionalCaseScenarioService` 冒烟结果为 `execution_status=passed`
- `V2-RISK-007` 不再是“本地真实 MySQL 完全未验收”的状态，当前应下调为“已缓解但仍需继续覆盖更复杂历史执行治理”。

## 2026-04-09 审核修订持久化深化发现
- 当前审核链路原先只有 `ScenarioReviewRecord`，虽然可以表达 `review_status=revised`，但没有独立的结构化修订事实记录，无法追溯修订内容本身。
- 当前执行流水线读取的是 `ScenarioStepRecord.metadata.raw_step`，因此结构化修订如果只改顶层字段、不改 `raw_step`，执行链路仍会消费旧配置；修订实现必须同步更新步骤持久化字段和 `raw_step`。
- 本轮最小闭环采用“修订事实表 + 修订接口 + 修订后补一条 `review_status=revised` 审核记录”的组合方式：
  - `ScenarioRevisionRecord` 负责记录修订内容；
  - `ScenarioReviewRecord` 继续表达状态流；
  - 两者一起构成“修订事实 + 生命周期状态”。
- 最小结构化修订当前支持：
  - 场景级字段：`scenario_name`、`scenario_desc`、`priority`、`module_id`
  - 步骤级字段：`step_name`、`operation_id`、`optional`、`retry_policy`、`request`、`expected`、`uses`
- 当前修订门禁收口为：只有 `rejected` 或 `revised` 状态的场景允许继续进入结构化修订；未驳回场景直接修订会被阻断。
- 这一轮能力已完成双环境验证：
  - SQLite 测试环境：`service_tests=10 passed`
  - 真实 MySQL 环境：`0002_scenariorevisionrecord` 已落库，修订链路冒烟 `passed`

## 2026-04-09 抓包草稿化接入与工作台入口收口发现
- `platform_core/traffic_capture.py` 已独立承载抓包解析，不再把 HAR 处理硬塞回既有文档解析器；当前已支持：
  - 静态资源与 `OPTIONS` 噪声过滤
  - 重复请求折叠
  - 查询参数归一化
  - 响应字段动态值候选提取
  - 基于已识别变量的依赖候选生成
- `scenario_service/services.py` 已把“功能测试用例草稿”和“抓包草稿”统一收口到 `_persist_scenario_draft()`，说明两条输入路线当前已共享同一事实落点和摘要契约。
- 抓包导入服务接口已经成立：
  - `POST /api/v2/scenarios/import-traffic-capture/`
  - 导入结果默认进入 `pending / not_started`，保持“只做草稿接入、不直接执行”的阶段边界。
- V2 可用型入口当前采用 Django 模板工作台页而非新建 React 工程，这是符合阶段约束的更稳妥选择：
  - 已新增 `GET /api/v2/scenarios/` 列表接口
  - 已新增 `GET /ui/v2/workbench/` 工作台页
  - 页面仅消费服务层 API，没有把核心逻辑前移到前端
- 工作台浏览器冒烟已验证以下真实链路：
  - 功能测试用例导入成功
  - 审核通过成功
  - 执行成功且结果区显示 `passed`
  - 列表状态在执行后可同步刷新为 `passed`
  - 抓包导入成功并在列表中展示 `pending / not_started / steps 2 / issues 2`
- 当前 V2 文档需要同步修正的关键口径有两个：
  - 抓包驱动草稿化接入与工作台入口不再是“待开始”，而是已完成
  - AI 辅助改写虽然在早期设计中被保留，但当前应明确降为 P1/V3，不能继续写成 V2 完成阻断项
- 当前 V2 的非阻断剩余项已收敛为：
  - AI 辅助改写与多轮确认
  - Windows 独立壳分发与完整客户端体验
  - 更复杂执行历史治理、更多公开基线操作目录和复杂变量编排
- 浏览器冒烟期间还额外发现了一个入口可用性问题：工作台默认功能用例示例在数据库中已存在时，重复导入会把 `ScenarioRecord.scenario_id` 唯一键冲突直接抛成 `500`。
- 根因已确认在服务层：`_persist_scenario_draft()` 直接写库，没有在业务层把重复场景标识转换成结构化错误；当前已补齐重复导入检查，并通过 `service_tests/test_workbench_ui.py` 新增用例锁定为 `400 + scenario_already_exists`。

## 2026-04-10 V2 全量验收发现
- 当前仓库中尚不存在 `product_document/阶段文档/V2阶段正式验收报告.md`，说明虽然 V2 阶段文档与测试文档已写明“P0 主线与本轮 P1 扩展均已完成”，但仍缺少正式收口文档。
- `git status --short --untracked-files=all` 当前仅显示 `?? .bytro` 与 `?? .idea/*`，未见新的代码脏改动，适合直接做正式验收归档。
- 最近 5 条主线提交均为 2026-04-10 的 V2 P1 扩展提交，表明当前验收对象应包含 P0 主线和本轮 P1 扩展，而不是仅按 2026-04-09 的 P0 状态验收。
- 本轮验收级自动化回归结果已复核：
  - `python -m pytest tests/platform_core -q --basetemp=.pytest_tmp/v2_acceptance_platform_core` -> `71 passed`
  - `python -m pytest tests -q --basetemp=.pytest_tmp/v2_acceptance_root` -> `79 passed`
  - `python -m pytest api_test/tests -q --basetemp=.pytest_tmp/v2_acceptance_api_test` -> `39 passed`
  - `$env:DJANGO_SETTINGS_MODULE='platform_service.settings'; .\.venv_service\Scripts\python.exe -m pytest service_tests -q --basetemp=.pytest_tmp/v2_acceptance_service_fixed` -> `19 passed`
  - `$env:DJANGO_SETTINGS_MODULE='platform_service.settings'; .\.venv_service\Scripts\python.exe manage.py makemigrations scenario_service --check --dry-run --settings=platform_service.migration_settings` -> `No changes detected in app 'scenario_service'`
- `service_tests` 首次使用 `--basetemp=.pytest_tmp_service/v2_acceptance_service` 执行时出现 `FileNotFoundError`，原因是 pytest 不会自动创建缺失的父目录；该问题属于验收命令参数问题，不属于服务层功能缺陷。
- 本轮真实浏览器冒烟已新增一轮 2026-04-10 证据：
  - `http://127.0.0.1:18080/ui/v2/workbench/` 可正常加载，页面标题为 `V2 场景工作台`
  - 工作台可从默认功能用例文本框导入 `ui_console_query_user_profile`
  - 场景可通过页面按钮完成“审核通过 -> 触发执行”
  - 页面结果区显示 `review_status=approved`、`execution_status=passed`、`passed_count=1`、`failed_count=0`、`skipped_count=0`
  - 页面可展示 `latest_execution_id`、`report_path`、`execution_history` 和 `latest_diff_summary`
- 基于本轮复核，V2 当前更适合形成“正式验收通过”结论，而不是继续停留在“待用户验收/汇总推送”的阶段性表述。

## 2026-04-14 V3 阶段计划正式化发现
- `全阶段工作规划文档.md`、`V2阶段工作计划文档.md` 与 `V2阶段正式验收报告.md` 当前共同指向同一个事实：V2 已完成正式验收，V3 不应再写成“待启动占位”，而应进入正式规划状态。
- 本轮用户已明确确认 V3 的第一主轴为“平台治理优先”，而不是执行中台优先或产品入口优先。
- 本轮已确认 V3 采用 `P0 / P1 / P2` 分层推进，且 **P0、P1、P2 都必须各自形成独立验收**，不再只依赖最终总体验收。
- `P0` 已确认聚焦“多项目与环境治理”，并明确做到“执行隔离级”；其入口形态不是完整控制台，而是浏览器端最小治理入口。
- 环境管理深度已确认到“测试环境层”，场景集与版本治理深度已确认到“基线版本级”。
- V2 历史资产承接策略已确认采用“默认项目迁移”，要求场景、修订、建议和执行记录统一迁入默认项目 / 默认环境 / 默认场景集，并保持可追溯。
- `P1` 已确认承接权限体系、抓包正式执行闭环、产品入口深化和调度与执行中心，但它们都必须建立在 `P0` 稳定验收之后。
- Windows 路线已确认采用“先 Web 稳定，再轻量套壳到 Windows”；默认壳方案写为“`Tauri` 优先，浏览器先验，阶段性打包复验”，以满足后续真实测试和反复修改验证的便捷性要求。
- `macOS` 已明确调整为“保留为后续要做，但当前阶段暂不做正式实现”，因此它应写入后续承接建议，而不是当前轮必达范围。
- 当前 V3 文档中最需要提前写死的风险边界包括：范围膨胀、跨项目串扰、历史数据迁移一致性、入口反向耦合、AI 越权、调度先于治理，以及 Windows Demo 反向牵引治理主线的风险。

## 2026-04-14 V3 详细测试文档包设计发现
- `V3` 测试文档不再适合沿用 V1 / V2 的单文件模式，因为当前阶段已明确 `P0 / P1 / P2` 都需要独立验收。
- 本轮已确认 `V3` 测试文档采用 **1 个总索引 + 3 个分文档** 的结构，其中：
  - 总索引只写规则、矩阵、映射和验收原则；
  - `P0 / P1 / P2` 三份分文档分别承载详细测试用例。
- 本轮已确认 `P0 / P1 / P2` 三份分文档都需要写得很详细，而不是只细写 `P0`。
- 本轮已确认每份分文档内部按测试层分章，而不是按任务组分章。
- 本轮已确认统一编号体系采用 `TC-V3-Px-LAYER-XXX`，例如 `TC-V3-P0-DOC-001`、`TC-V3-P1-API-012`、`TC-V3-P2-INT-003`。
- 本轮已确认单条用例使用超详细执行模板，至少包含：编号、名称、目标、背景、前置条件、输入、执行步骤、检查点、失败判定、优先级、预期结果、归属阶段验收、后续联动测试。
- `P0` 的测试重点是：历史资产迁移、执行隔离、最小治理入口和独立验收闭环。
- `P1` 的测试重点是：权限体系、抓包正式执行、Web 正式入口深化、Windows Demo 和调度中心。
- `P2` 的测试重点是：AI 建议边界、审批门禁、回退、留痕以及“AI 不能越权成为事实源”的治理闭环。
