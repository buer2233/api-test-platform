# V1 BaseAPI 职责收口 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 把 `BaseAPI` 中残留的非 HTTP 工具方法迁移到独立公共工具模块，并以 TDD 方式完成代码、测试和文档同步。

**Architecture:** 采用增量式收口方案，不扩展新的功能线。先写治理测试和工具回归测试，确认红灯后再实现 `core.common_tools`，最后同步 V1 文档和公开基线验证结果。

**Tech Stack:** Python 3.12、pytest、requests、pycryptodome、Markdown、Git

---

## File Map

### Create
- `api_test/core/common_tools.py`
- `api_test/tests/test_common_tools.py`
- `docs/superpowers/specs/2026-04-02-v1-base-api-responsibility-split-design.md`
- `docs/superpowers/plans/2026-04-02-v1-base-api-responsibility-split.md`

### Modify
- `api_test/core/base_api.py`
- `api_test/tests/test_base_api_governance.py`
- `README.md`
- `api_test/README.md`
- `product_document/架构设计/现有接口自动化测试框架改造方案.md`
- `product_document/阶段文档/V1阶段工作计划文档.md`
- `product_document/阶段文档/V1实施计划与开发任务拆解说明书.md`
- `product_document/测试文档/详细测试用例说明书(V1).md`
- `AGENTS.md`

---

### Task 1：锁定失败测试

**Files:**
- Modify: `api_test/tests/test_base_api_governance.py`
- Create: `api_test/tests/test_common_tools.py`

- [ ] **Step 1: 写治理失败测试**
  - 新增断言：`BaseAPI` 不再暴露 `get_value`、时间工具、加密工具和随机数据工具。

- [ ] **Step 2: 写工具回归失败测试**
  - 新增 `test_common_tools.py`，覆盖嵌套取值、时间处理、哈希、AES、随机字符串、手机号和邮箱生成。

- [ ] **Step 3: 运行定向测试确认失败**
  - 运行：`python -m pytest api_test/tests/test_base_api_governance.py api_test/tests/test_common_tools.py -v --noconftest --basetemp .pytest_tmp/base_api_split_red`
  - 预期：`BaseAPI` 仍暴露工具方法，且 `core.common_tools` 尚不存在或测试失败。

### Task 2：补最小实现

**Files:**
- Create: `api_test/core/common_tools.py`
- Modify: `api_test/core/base_api.py`

- [ ] **Step 1: 新增工具模块**
  - 以纯函数形式迁移所有非 HTTP 工具方法。

- [ ] **Step 2: 收口 `BaseAPI`**
  - 删除类中的非 HTTP 工具方法，只保留请求相关能力。

- [ ] **Step 3: 运行定向测试确认通过**
  - 运行：`python -m pytest api_test/tests/test_base_api_governance.py api_test/tests/test_common_tools.py -v --noconftest --basetemp .pytest_tmp/base_api_split_green`
  - 预期：全部通过。

### Task 3：同步文档并执行回归

**Files:**
- Modify: `README.md`
- Modify: `api_test/README.md`
- Modify: `product_document/架构设计/现有接口自动化测试框架改造方案.md`
- Modify: `product_document/阶段文档/V1阶段工作计划文档.md`
- Modify: `product_document/阶段文档/V1实施计划与开发任务拆解说明书.md`
- Modify: `product_document/测试文档/详细测试用例说明书(V1).md`
- Modify: `AGENTS.md`

- [ ] **Step 1: 同步文档**
  - 更新 `BaseAPI` 职责状态、本轮测试命令、执行结果和剩余风险描述。

- [ ] **Step 2: 执行回归**
  - 运行：`python -m pytest api_test/tests/test_base_api_governance.py api_test/tests/test_common_tools.py -v --noconftest --basetemp .pytest_tmp/base_api_split_docs`
  - 运行：`python -m pytest api_test/tests -v --basetemp .pytest_tmp/api_test_base_api_split_full`
  - 运行：`python -m pytest tests/platform_core -v --basetemp .pytest_tmp/platform_core_after_base_api_split`
  - 运行：`python -m pytest tests -v --basetemp .pytest_tmp/root_after_base_api_split`
  - 运行：`python api_test/run_test.py --public-baseline`
  - 运行：`cd api_test && python run_test.py --public-baseline`

- [ ] **Step 3: 提交并推送**
  - 提交信息建议：`重构：收口BaseAPI职责并补齐通用工具层与V1文档`
