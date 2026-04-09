# V2 第三实施子阶段：场景执行闭环与结果回写 Implementation Plan

> **For agentic workers:** 按已确认的 V2 阶段文档继续执行，当前子阶段只补“正式确认 -> 工作区导出 -> pytest 执行 -> 结果回写”的最小闭环。

**Goal:** 让已确认的功能测试用例场景可以导出为本地 pytest 工作区、执行真实场景测试，并把执行结果、报告路径和工作区引用回写到数据库事实源。

**Architecture:** 在 `scenario_service` 继续复用当前草稿导入与审核服务；新增一个面向功能测试用例场景的最小执行流水线，负责：
1. 读取场景与步骤持久化记录；
2. 把步骤转换为可执行的 pytest 场景测试文件；
3. 借助 `platform_core` 现有 `AssetWorkspace` 与 `PytestExecutor` 完成工作区导出、执行和资产清单落盘；
4. 回写 `ScenarioExecutionRecord` 与 `ScenarioRecord` 的执行摘要。

**Tech Stack:** Python、pytest、现有 `platform_core` 工作区与执行器、`scenario_service` 服务层、JSONPlaceholder 公共基线

---

### Task 1: 锁定执行闭环红灯测试

**Files:**
- Create: `service_tests/test_execution_closure.py`
- Modify: `service_tests/test_drf_contract.py`

- [x] **Step 1: 写失败测试，锁定已确认场景的工作区导出与执行回写**

目标：
- 已确认场景执行后会生成工作区、pytest 测试文件、报告文件和资产清单；
- 场景与执行记录会回写 `workspace_root`、`report_path`、`execution_status`、通过数等摘要字段；
- 未绑定受支持公开基线操作的场景会在执行前被结构化阻断。

- [x] **Step 2: 运行定向测试，确认红灯**

Run:
- `.venv_service\Scripts\python.exe -m pytest service_tests/test_execution_closure.py -v --ds=platform_service.test_settings --basetemp .pytest_tmp/v2_phase3_execution_red`
- `.venv_service\Scripts\python.exe -m pytest service_tests/test_drf_contract.py -k "result_summary" -v --ds=platform_service.test_settings --basetemp .pytest_tmp/v2_phase3_drf_red`

Expected:
- FAIL，原因应来自“执行闭环尚未实现”，而不是测试拼写或导入错误。

### Task 2: 实现最小场景执行流水线

**Files:**
- Create: `platform_core/scenario_execution.py`
- Modify: `platform_core/renderers.py`
- Create: `platform_core/templates/tests/test_scenario_module.py.j2`
- Modify: `scenario_service/services.py`

- [x] **Step 1: 实现最小公开基线操作目录与测试模板渲染**

目标：
- 支持最小一批 JSONPlaceholder 场景操作绑定；
- 支持步骤顺序执行、上游变量提取、下游路径注入；
- 生成的 pytest 测试文件可被现有执行器直接收集。

- [x] **Step 2: 接入服务层执行与结果回写**

目标：
- `request_execution()` 不再只创建空记录，而是导出工作区、执行 pytest 并更新记录；
- 结果查询接口返回更新后的状态、报告路径和统计摘要；
- 失败场景返回结构化错误码。

- [x] **Step 3: 重跑定向测试，确认转绿**

Run:
- `.venv_service\Scripts\python.exe -m pytest service_tests/test_execution_closure.py -v --ds=platform_service.test_settings --basetemp .pytest_tmp/v2_phase3_execution_green`
- `.venv_service\Scripts\python.exe -m pytest service_tests/test_drf_contract.py -v --ds=platform_service.test_settings --basetemp .pytest_tmp/v2_phase3_drf_green`

Expected:
- PASS

### Task 3: 文档同步与回归

**Files:**
- Modify: `README.md`
- Modify: `product_document/阶段文档/V2阶段工作计划文档.md`
- Modify: `product_document/测试文档/详细测试用例说明书(V2).md`
- Modify: `task_plan.md`
- Modify: `findings.md`
- Modify: `progress.md`

- [x] **Step 1: 回写第三子阶段能力状态与测试结果**

目标：
- 把 `V2-IMP-002/003/004` 和 `V2-TEST-006/007` 的状态更新到最新；
- 记录场景执行闭环与结果回写已进入首批可运行状态。

- [x] **Step 2: 执行回归**

Run:
- `.venv_service\Scripts\python.exe -m pytest service_tests -v --ds=platform_service.test_settings --basetemp .pytest_tmp/v2_phase3_service_tests`
- `python -m pytest tests/platform_core -v --basetemp .pytest_tmp/v2_phase3_platform_core_regression`
- `python -m pytest tests -v --basetemp .pytest_tmp/v2_phase3_root_regression`
- `python -m pytest api_test/tests -v --basetemp .pytest_tmp/v2_phase3_api_test_regression`

Expected:
- 新增执行闭环测试通过；
- 既有 `platform_core`、根治理测试与 `api_test` 公开基线不回退。
