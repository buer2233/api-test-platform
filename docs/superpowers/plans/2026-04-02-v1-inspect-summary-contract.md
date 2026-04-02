# V1 工作区检查摘要契约收口 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为 `platform_core` 的应用服务层补齐工作区检查稳定摘要模型，并让 CLI `inspect` 直接消费服务层摘要输出。

**Architecture:** 保持 V1 当前只支持文档驱动与工作区检查的范围，不新增命令与路线。先通过失败测试锁定工作区检查摘要模型与应用服务行为，再补最小实现，最后同步 CLI 和阶段文档。

**Tech Stack:** Python 3.12、pytest、pydantic、argparse、Markdown、Git

---

## File Map

### Create
- `docs/superpowers/specs/2026-04-02-v1-inspect-summary-contract-design.md`
- `docs/superpowers/plans/2026-04-02-v1-inspect-summary-contract.md`

### Modify
- `platform_core/models.py`
- `platform_core/services.py`
- `platform_core/cli.py`
- `platform_core/__init__.py`
- `tests/platform_core/test_models.py`
- `tests/platform_core/test_services_and_assets.py`
- `README.md`
- `product_document/架构设计/中间模型设计说明书.md`
- `product_document/阶段文档/V1阶段工作计划文档.md`
- `product_document/阶段文档/V1实施计划与开发任务拆解说明书.md`
- `product_document/测试文档/详细测试用例说明书(V1).md`

---

### Task 1：锁定工作区检查摘要模型失败测试

**Files:**
- Modify: `tests/platform_core/test_models.py`
- Modify: `platform_core/models.py`

- [ ] **Step 1: 写失败测试**
  - 新增 `WorkspaceInspectionSummary` 的最小模型测试。

- [ ] **Step 2: 运行测试确认失败**
  - 运行：`python -m pytest tests/platform_core/test_models.py -k "workspace_inspection_summary" -v --basetemp .pytest_tmp/platform_core_inspect_summary_models_red`
  - 预期：失败，提示新增模型尚不存在。

- [ ] **Step 3: 写最小实现**
  - 在 `platform_core/models.py` 中补齐工作区检查服务摘要模型定义，并导出到 `platform_core/__init__.py`。

- [ ] **Step 4: 运行测试确认通过**
  - 运行：`python -m pytest tests/platform_core/test_models.py -k "workspace_inspection_summary" -v --basetemp .pytest_tmp/platform_core_inspect_summary_models_green`
  - 预期：通过。

### Task 2：锁定应用服务层工作区检查摘要失败测试

**Files:**
- Modify: `tests/platform_core/test_services_and_assets.py`
- Modify: `platform_core/services.py`

- [ ] **Step 1: 写失败测试**
  - 新增 `inspect_workspace_summary()` 测试；
  - 断言摘要包含 `command_code`、`service_stage`、数量字段和摘要列表；
  - 保留 `inspect_workspace()` 原始兼容断言。

- [ ] **Step 2: 运行测试确认失败**
  - 运行：`python -m pytest tests/platform_core/test_services_and_assets.py -k "inspect_workspace_summary" -v --basetemp .pytest_tmp/platform_core_inspect_summary_service_red`
  - 预期：失败，提示新方法或字段不存在。

- [ ] **Step 3: 写最小实现**
  - 在 `PlatformApplicationService` 中补齐：
    - `build_workspace_inspection_summary()`
    - `inspect_workspace_summary()`

- [ ] **Step 4: 运行测试确认通过**
  - 运行：`python -m pytest tests/platform_core/test_services_and_assets.py -k "inspect_workspace_summary" -v --basetemp .pytest_tmp/platform_core_inspect_summary_service_green`
  - 预期：通过。

### Task 3：锁定 CLI `inspect` 摘要输出失败测试

**Files:**
- Modify: `tests/platform_core/test_services_and_assets.py`
- Modify: `platform_core/cli.py`

- [ ] **Step 1: 写失败测试**
  - 在 CLI `inspect` 集成测试中新增断言：
    - `command_code`
    - `service_stage`
    - `missing_asset_count`
    - `missing_generation_record_count`
    - `digest_mismatch_count`
    - `validation_error_count`

- [ ] **Step 2: 运行测试确认失败**
  - 运行：`python -m pytest tests/platform_core/test_services_and_assets.py -k "cli_can_inspect_workspace_manifest" -v --basetemp .pytest_tmp/platform_core_inspect_cli_red`
  - 预期：失败，CLI 当前输出缺少新字段。

- [ ] **Step 3: 写最小实现**
  - 让 CLI `inspect` 直接调用 `inspect_workspace_summary()` 并输出模型 JSON。

- [ ] **Step 4: 运行测试确认通过**
  - 运行：`python -m pytest tests/platform_core/test_services_and_assets.py -k "inspect_workspace_summary or cli_can_inspect_workspace_manifest" -v --basetemp .pytest_tmp/platform_core_inspect_cli_green`
  - 预期：通过。

### Task 4：同步文档并执行回归

**Files:**
- Modify: `README.md`
- Modify: `product_document/架构设计/中间模型设计说明书.md`
- Modify: `product_document/阶段文档/V1阶段工作计划文档.md`
- Modify: `product_document/阶段文档/V1实施计划与开发任务拆解说明书.md`
- Modify: `product_document/测试文档/详细测试用例说明书(V1).md`

- [ ] **Step 1: 同步能力说明**
  - 补记工作区检查服务摘要模型、应用服务层 `inspect` 收口状态和 CLI `inspect` 服务化输出。

- [ ] **Step 2: 执行平台核心回归**
  - 运行：`python -m pytest tests/platform_core -v --basetemp .pytest_tmp/platform_core_inspect_summary_full`
  - 运行：`python -m pytest tests -v --basetemp .pytest_tmp/root_inspect_summary_full`

- [ ] **Step 3: 执行 `api_test` 回归**
  - 运行：`python -m pytest api_test/tests -v --basetemp .pytest_tmp/api_test_inspect_summary_full`
  - 运行：`python api_test/run_test.py --public-baseline`
  - 运行：`cd api_test && python run_test.py --public-baseline`

- [ ] **Step 4: 提交并推送**
  - 提交信息建议：`重构：收口工作区检查摘要契约并同步V1阶段文档`
