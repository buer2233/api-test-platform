# V1 服务摘要契约收口 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为 `platform_core` 的应用服务层补齐稳定的能力快照和文档驱动运行摘要模型，并让 CLI `run` 直接消费服务层摘要输出。

**Architecture:** 保持 V1 当前只支持文档驱动最小闭环的范围，不新增命令与路线。先通过失败测试锁定服务摘要模型与应用服务行为，再补最小实现，最后同步 CLI 和阶段文档。

**Tech Stack:** Python 3.12、pytest、pydantic、argparse、Markdown、Git

---

## File Map

### Create
- `docs/superpowers/specs/2026-04-02-v1-service-summary-contract-design.md`
- `docs/superpowers/plans/2026-04-02-v1-service-summary-contract.md`

### Modify
- `platform_core/models.py`
- `platform_core/services.py`
- `platform_core/cli.py`
- `tests/platform_core/test_models.py`
- `tests/platform_core/test_services_and_assets.py`
- `tests/platform_core/test_pipeline.py`
- `README.md`
- `product_document/阶段文档/V1阶段工作计划文档.md`
- `product_document/阶段文档/V1实施计划与开发任务拆解说明书.md`
- `product_document/测试文档/详细测试用例说明书(V1).md`

---

### Task 1：锁定服务摘要模型失败测试

**Files:**
- Modify: `tests/platform_core/test_models.py`
- Modify: `platform_core/models.py`

- [ ] **Step 1: 写失败测试**
  - 新增 `RouteCapabilitySummary` 和 `DocumentPipelineRunSummary` 的最小模型测试。

- [ ] **Step 2: 运行测试确认失败**
  - 运行：`python -m pytest tests/platform_core/test_models.py -v --basetemp .pytest_tmp/platform_core_service_contract_models_red`
  - 预期：失败，提示新增模型尚不存在。

- [ ] **Step 3: 写最小实现**
  - 在 `platform_core/models.py` 中补齐服务摘要模型定义。

- [ ] **Step 4: 运行测试确认通过**
  - 运行：`python -m pytest tests/platform_core/test_models.py -v --basetemp .pytest_tmp/platform_core_service_contract_models_green`
  - 预期：通过。

### Task 2：锁定应用服务层能力快照与运行摘要失败测试

**Files:**
- Modify: `tests/platform_core/test_services_and_assets.py`
- Modify: `platform_core/services.py`

- [ ] **Step 1: 写失败测试**
  - 新增 `describe_capabilities()` 测试；
  - 新增 `run_document_pipeline_summary()` 测试；
  - 保留 `supported_routes()` 旧兼容断言。

- [ ] **Step 2: 运行测试确认失败**
  - 运行：`python -m pytest tests/platform_core/test_services_and_assets.py -k \"capabilities or pipeline_summary or supported_routes\" -v --basetemp .pytest_tmp/platform_core_service_contract_red`
  - 预期：失败，提示新方法或字段不存在。

- [ ] **Step 3: 写最小实现**
  - 在 `PlatformApplicationService` 中补齐：
    - `describe_capabilities()`
    - `build_document_pipeline_summary()`
    - `run_document_pipeline_summary()`

- [ ] **Step 4: 运行测试确认通过**
  - 运行：`python -m pytest tests/platform_core/test_services_and_assets.py -k \"capabilities or pipeline_summary or supported_routes\" -v --basetemp .pytest_tmp/platform_core_service_contract_green`
  - 预期：通过。

### Task 3：锁定 CLI `run` 摘要输出失败测试

**Files:**
- Modify: `tests/platform_core/test_pipeline.py`
- Modify: `platform_core/cli.py`

- [ ] **Step 1: 写失败测试**
  - 在 CLI `run` 集成测试中新增断言：
    - `route_code`
    - `service_stage`
    - `workspace_root`

- [ ] **Step 2: 运行测试确认失败**
  - 运行：`python -m pytest tests/platform_core/test_pipeline.py -k \"cli_runs_document_pipeline\" -v --basetemp .pytest_tmp/platform_core_cli_contract_red`
  - 预期：失败，CLI 当前输出缺少新字段。

- [ ] **Step 3: 写最小实现**
  - 让 CLI `run` 直接调用 `run_document_pipeline_summary()` 并输出模型 JSON。

- [ ] **Step 4: 运行测试确认通过**
  - 运行：`python -m pytest tests/platform_core/test_pipeline.py -k \"cli_runs_document_pipeline\" -v --basetemp .pytest_tmp/platform_core_cli_contract_green`
  - 预期：通过。

### Task 4：同步文档并执行回归

**Files:**
- Modify: `README.md`
- Modify: `product_document/阶段文档/V1阶段工作计划文档.md`
- Modify: `product_document/阶段文档/V1实施计划与开发任务拆解说明书.md`
- Modify: `product_document/测试文档/详细测试用例说明书(V1).md`

- [ ] **Step 1: 同步能力说明**
  - 补记服务层稳定摘要模型、应用服务能力快照和 CLI `run` 收口状态。

- [ ] **Step 2: 执行平台核心回归**
  - 运行：`python -m pytest tests/platform_core -v --basetemp .pytest_tmp/platform_core_service_contract_full`
  - 运行：`python -m pytest tests -v --basetemp .pytest_tmp/root_service_contract_full`

- [ ] **Step 3: 执行 `api_test` 回归**
  - 运行：`python -m pytest api_test/tests -v --basetemp .pytest_tmp/api_test_service_contract_full`
  - 运行：`python api_test/run_test.py --public-baseline`
  - 运行：`cd api_test && python run_test.py --public-baseline`

- [ ] **Step 4: 提交并推送**
  - 提交信息建议：`重构：收口平台服务摘要契约并同步V1阶段文档`
