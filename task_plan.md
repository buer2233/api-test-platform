# 当前任务计划

## 目标
- 完成 2026-04-03 的 V1 正式验收复验。
- 对 `jsonplaceholder.typicode.com` 相关用例采用“临时开启代理执行，完成后恢复默认关闭”的验证流程。
- 产出正式验收文档并同步 README、阶段文档、测试文档与本地记录。

## 本轮范围
1. 临时开启 `api_test/api_config.json` 中的代理开关，验证代理连通性与 `jsonplaceholder` 相关用例。
2. 如测试失败则定位并修复；如失败仅来自临时配置偏离默认契约，则恢复默认状态并重跑。
3. 完成 V1 正式验收回归和 `V1阶段正式验收报告.md` 输出。

## 阶段状态
| 阶段 | 状态 | 说明 |
| --- | --- | --- |
| 代理开启与公网冒烟 | 已完成 | 已验证 `127.0.0.1:7890` 可连通，代理请求 JSONPlaceholder 返回 `200 / id=1` |
| `jsonplaceholder` 相关回归 | 已完成 | 代理开启下 `jsonplaceholder` 相关用例为 `12 passed, 27 deselected`，公开基线双入口均为 `12 passed, 27 deselected` |
| 默认配置恢复与非公网回归 | 已完成 | 已恢复 `proxy.enabled=false`，非 `jsonplaceholder` 用例为 `27 passed, 12 deselected`，`test_config_loader.py` 为 `6 passed` |
| V1 验收套件复验 | 已完成 | `tests/platform_core` 为 `63 passed`，根测试为 `70 passed` |
| 文档与正式报告同步 | 已完成 | 已新增正式验收报告，并同步 README、V1 阶段文档、V1 测试文档、`api_test` 文档与本地记录 |

## 风险与注意事项
- `jsonplaceholder` 外网直连仍可能存在时延波动；正式回归优先临时开启代理执行公网用例。
- 仓库默认状态必须保持 `proxy.enabled=false`，否则会破坏配置契约测试。
- `.idea/` 继续忽略，不纳入提交。

## 2026-04-07 当前分析任务

### 目标
- 基于当前仓库状态，分析 V1 阶段研发进度和测试进度是否仍与正式验收结论一致。

### 分析范围
1. 核对 `V1阶段工作计划文档.md`、`V1实施计划与开发任务拆解说明书.md`、`详细测试用例说明书(V1).md` 与 `V1阶段正式验收报告.md`。
2. 核对 `README.md`、`platform_core/`、`tests/`、`api_test/tests/`、`api_test/api_config.json` 与 `api_test/requirements.txt`。
3. 核对 `git status` 与最近提交，判断正式验收后是否还有新的 V1 变更。

### 当前阶段状态
| 阶段 | 状态 | 说明 |
| --- | --- | --- |
| 文档口径核对 | 已完成 | V1 主文档、实施计划、测试说明书和正式验收报告均指向“V1 已完成 / 正式验收通过” |
| 代码与测试资产核对 | 已完成 | `platform_core`、`tests/platform_core`、根治理测试与 `api_test/tests` 结构均与 V1 闭环范围匹配 |
| 仓库状态核对 | 已完成 | 最近主线提交停留在 2026-04-03 正式验收文档同步；当前未见新的 V1 代码提交，工作区仅有 `.idea/` 未跟踪 |
| 结论整理 | 已完成 | 本轮分析结论可输出 |

### 本轮结论约束
- 本轮未重新执行回归测试，避免在未同步阶段文档的情况下制造新的测试结果口径。
- 本轮结论基于 2026-04-03 的正式验收记录，以及 2026-04-07 对当前仓库代码、文档和 Git 状态的复核。

## 2026-04-07 V2 计划文档任务

### 目标
- 基于全阶段规划、V1 完成状态与当前代码底座，深度完善 `product_document/阶段文档/V2阶段工作计划文档.md`。
- 采用多轮确认方式推进，在用户最终确认前不进入 V2 开发和测试。

### 当前阶段状态
| 阶段 | 状态 | 说明 |
| --- | --- | --- |
| V2 现有文档审计 | 已完成 | 当前 V2 文档仅为简版占位，缺少范围、设计、测试、进度和风险体系 |
| 上位文档承接关系核对 | 已完成 | 全阶段规划、全局产品说明书已给出 V2 方向，但全阶段规划文档仍停留在 V1 进行中口径，需要后续同步 |
| V2 方案结构设计 | 进行中 | 正在提炼 V2 的阶段定位、能力拆解、实施顺序和验收原则 |
| 用户逐轮确认 | 待开始 | 需先给出候选组织方式和推荐方案 |
| 文档正式修订 | 待开始 | 在用户确认结构和重点后再改写正式文档 |

### 本轮约束
- 先做设计与计划，不写 V2 实现代码，不启动 V2 测试执行。
- 如引用外部开源项目，只作为设计参考，不直接迁移其实现或口径。

### 2026-04-08 正式文档落地状态
| 阶段 | 状态 | 说明 |
| --- | --- | --- |
| V2 阶段工作计划文档正式化 | 已完成 | 已将占位稿升级为正式规划版，并补充范围、设计、测试、进度、风险与 V3 承接建议 |
| 全阶段工作规划文档同步 | 已完成 | 已同步修正 V1 完成、V2 规划中、V3 承接方向等阶段口径 |
| README 阶段状态同步 | 已完成 | 已补记当前仓库重点已切换到 V2 正式规划，并更新建议查看顺序与当前方向 |
| 自检与汇总 | 进行中 | 正在整理本轮文档改写结果并准备向用户汇报 |

## 2026-04-08 V2 测试文档任务

### 目标
- 基于已确认的 `V2阶段工作计划文档.md`，独立完成 `product_document/测试文档/详细测试用例说明书(V2).md`。
- 编写过程中不反复向用户提问；问题和可选项先记录，最终统一汇报。

### 当前阶段状态
| 阶段 | 状态 | 说明 |
| --- | --- | --- |
| 上位文档复核 | 已完成 | 已复核 V2 计划、V1 测试说明书、中间模型、模板规范、UI 设计和全局产品说明 |
| V2 测试分层与编号收敛 | 已完成 | 已确定 8 层测试分层和 `TC-V2-DOC/MODEL/PARSE/TPL/RULE/SVC/EXEC/UI/INT` 编号体系 |
| V2 测试文档正式编写 | 已完成 | 已完成 `product_document/测试文档/详细测试用例说明书(V2).md`，覆盖八层测试分层、详细编号、优先级与通过标准 |
| 阶段文档与本地记录同步 | 已完成 | 已同步更新 `V2阶段工作计划文档.md`、README 和本地记录文件中的测试设计进度 |

### 本轮约束
- 仅编写测试说明书与进度记录，不进入 V2 实现代码开发。
- 文档必须明确 V2 做什么、不做什么，以及 P0 / P1 / P2 的分层优先级。
- 抓包驱动在 V2 仅按“草稿化接入”写测试，不扩写为完整执行闭环。

## 2026-04-08 V2 第一实施子阶段开发

### 目标
- 基于 `V2阶段工作计划文档.md` 与 `详细测试用例说明书(V2).md`，启动 V2 正式开发。
- 本轮只落地第一实施子阶段：场景核心模型、功能测试用例草稿解析、状态流门禁与服务层最小功能路线。
- 严格按 TDD 推进，并持续同步 README、阶段文档和本地记录。

### 当前阶段状态
| 阶段 | 状态 | 说明 |
| --- | --- | --- |
| 第一实施子阶段计划编写 | 已完成 | 已新增 `docs/superpowers/plans/2026-04-08-v2-phase-1-scenario-core.md`，明确模型、解析器、服务层和文档同步任务 |
| V2 第一批失败测试设计收敛 | 已完成 | 已确认优先覆盖 `TC-V2-MODEL-011/012`、`TC-V2-RULE-011` 以及功能用例主线最小闭环 |
| V2 第一批失败测试编写 | 已完成 | 已在 `test_models.py`、`test_parser_inputs.py`、`test_services_and_assets.py` 完成首批红灯测试，并确认失败原因来自 V2 能力缺失 |
| V2 第一批最小实现 | 已完成 | 已修改 `platform_core/models.py`、新增 `platform_core/functional_cases.py`、调整 `services.py` 与 `rules.py`，完成首批最小实现 |
| 文档与记录同步 | 已完成（本轮） | 已同步 README、V2 阶段文档、V2 测试文档和本地记录，并回写首批测试结果 |
| 首批回归验证 | 已完成 | 已完成定向新测、`tests/platform_core` 全量、根治理测试与 `api_test/tests` 回归验证 |

### 本轮约束
- 不一次性铺开完整 Django/DRF/MySQL、抓包驱动和 UI 入口。
- 先把“功能测试用例输入 -> 场景草稿对象 -> 服务层最小摘要”做成稳定闭环。
- 所有新增方法、注释和测试说明继续使用中文。

## 2026-04-08 V2 第二实施子阶段开发

### 目标
- 在第一实施子阶段完成后，继续落地第二实施子阶段：服务化契约与持久化骨架。
- 重点实现 Django + DRF 最小骨架、场景草稿持久化、审核/执行请求接口与结果查询接口。
- 保持 MySQL 作为正式运行目标，测试环境采用独立虚拟环境和 Django 测试设置。

### 当前阶段状态
| 阶段 | 状态 | 说明 |
| --- | --- | --- |
| 第二实施子阶段计划编写 | 已完成 | 已新增 `docs/superpowers/plans/2026-04-08-v2-phase-2-service-contract.md` |
| 服务层依赖与环境治理设计 | 已完成 | 已建立 `.venv_service`，并将 Django/DRF、PyYAML、pytest 及关键传递依赖固定到 2025 年及以前版本 |
| 第二批失败测试编写 | 已完成 | 已补齐服务依赖治理、MySQL 启动兼容补丁、Django 持久化骨架与 DRF API 契约的失败测试，并确认红灯原因准确 |
| 第二批最小实现 | 已完成（第一批） | 已新增 Django 项目骨架、服务 app、持久化模型、初始迁移文件、DRF 视图与 PyMySQL MySQLdb 兼容补丁 |
| 文档与记录同步 | 已完成（本轮） | 已同步 README、V2 阶段文档、V2 测试文档与本地记录，并回写第二子阶段测试结果 |

### 本轮约束
- 不使用 2026 年及以后发布的 Django 版本；全程固定到 2025 年及以前版本。
- 不直接依赖全局 Python 环境中的 `Django 6.0.1`。
- 第二子阶段只做服务化契约与持久化骨架，不把真实场景执行器、抓包驱动和 UI 一起摊开。

### 当前结果
- 已完成 `requirements-platform-service.txt` 与 `tests/test_dependency_governance.py` 的红绿治理，并用 `.venv_service` 重建独立服务环境。
- 已新增 `service_tests/test_service_persistence.py`、`service_tests/test_drf_contract.py`、`service_tests/test_service_bootstrap.py`，覆盖场景持久化、DRF 契约和 MySQL 启动兼容补丁。
- 已新增 `platform_service/migration_settings.py` 并生成 `scenario_service/migrations/0001_initial.py`，可在 SQLite 迁移设置下执行迁移一致性检查。
- 已完成本轮验证：
  - `.venv_service\\Scripts\\python.exe -m pytest service_tests -v --ds=platform_service.test_settings --basetemp .pytest_tmp/v2_phase2_service_tests` -> `4 passed`
  - `python -m pytest tests/platform_core -v --basetemp .pytest_tmp/v2_phase2_platform_core_regression` -> `68 passed`
  - `python -m pytest tests -v --basetemp .pytest_tmp/v2_phase2_root_regression` -> `76 passed`
  - `python -m pytest api_test/tests -v --basetemp .pytest_tmp/v2_phase2_api_test_regression` -> `39 passed`

### 下一步
- 继续扩展真实 MySQL 验收、审核修订持久化、抓包草稿化接入和可用型入口测试。
