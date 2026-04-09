# 当前发现

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
