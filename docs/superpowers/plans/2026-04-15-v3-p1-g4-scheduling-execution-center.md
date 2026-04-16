# V3 P1 G4 调度与执行中心 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在现有项目治理、权限审计和正式执行底座上，补齐 `P1-G4` 调度与执行中心，形成“授权 -> 批量执行 -> 重试 -> 取消 -> 聚合 -> 审计”的正式闭环。

**Architecture:** 继续沿用 `scenario_service` 作为统一事实源承载层，不新建第二套执行引擎。调度中心通过“批次对象 + 任务项对象”承接队列、重试和结果聚合，并复用现有 `request_execution()` 作为单场景执行入口；所有调度动作继续受项目边界、显式角色权限和审计日志治理约束。

**Tech Stack:** Python 3.12、Django、Django REST Framework、pytest、MySQL、现有 `scenario_service` / `platform_service`

---

## Scope Check

`P1-G4` 本轮只覆盖：
1. 调度批次与调度任务项正式建模；
2. 单项目 / 单环境边界内的批量执行、队列状态、重试与取消；
3. 聚合摘要、治理上下文和审计留痕；
4. Web 正式入口对调度中心信息的承接。

本轮**不覆盖**：
1. 独立异步 worker、消息队列或定时调度器进程；
2. 跨项目批量编排；
3. 复杂 cron 表达式、分布式锁和优先级抢占；
4. 新的桌面端事实缓存或第二套客户端接口。

## File Structure

- Create: `D:\AI\api-test-platform\service_tests\test_v3_p1_scheduling_execution_center.py`
  作用：覆盖 `TC-V3-P1-MODEL-004 / ISO-003 / API-004 / EXEC-003 / INT-003` 红绿闭环。
- Modify: `D:\AI\api-test-platform\scenario_service\models.py`
  作用：新增调度批次和调度任务项模型。
- Modify: `D:\AI\api-test-platform\scenario_service\services.py`
  作用：新增批量创建、批次查询、任务重试、任务取消和聚合摘要服务。
- Modify: `D:\AI\api-test-platform\scenario_service\serializers.py`
  作用：新增调度批次创建、任务重试、任务取消请求校验器。
- Modify: `D:\AI\api-test-platform\scenario_service\views.py`
  作用：新增调度中心 API 视图。
- Modify: `D:\AI\api-test-platform\scenario_service\urls.py`
  作用：注册调度中心 API 路由。
- Modify: `D:\AI\api-test-platform\scenario_service\templates\scenario_service\workbench.html`
  作用：新增调度中心展示与触发区域。
- Modify: `D:\AI\api-test-platform\scenario_service\admin.py`
  作用：注册新的调度模型，便于后台验收查看。
- Create: `D:\AI\api-test-platform\scenario_service\migrations\0008_scenarioschedulebatchrecord_and_more.py`
  作用：把调度事实模型正式落库到 MySQL。
- Modify: `D:\AI\api-test-platform\README.md`
- Modify: `D:\AI\api-test-platform\product_document\阶段文档\V3阶段工作计划文档.md`
- Modify: `D:\AI\api-test-platform\product_document\测试文档\详细测试用例说明书(V3-P1).md`
- Modify: `D:\AI\api-test-platform\product_document\本地MySQL数据库信息.md`
- Modify: `D:\AI\api-test-platform\task_plan.md`
- Modify: `D:\AI\api-test-platform\findings.md`
- Modify: `D:\AI\api-test-platform\progress.md`

### Task 1: 调度模型红灯测试与最小建模

**Files:**
- Create: `D:\AI\api-test-platform\service_tests\test_v3_p1_scheduling_execution_center.py`
- Modify: `D:\AI\api-test-platform\scenario_service\models.py`
- Create: `D:\AI\api-test-platform\scenario_service\migrations\0008_scenarioschedulebatchrecord_and_more.py`

- [ ] **Step 1: Write the failing test**

```python
def test_schedule_models_capture_queue_retry_aggregate_and_governance_context(service_test_token: str):
    """TC-V3-P1-MODEL-004 调度对象应能表达任务、队列、重试和聚合摘要。"""
```

测试应断言：
1. 批次对象可记录 `project / environment / scenario_set / baseline_version / dispatch_strategy / queue_status / aggregate_summary`；
2. 任务项对象可记录 `scenario / item_status / retry_policy / retry_count / max_retry_count / failure_reason / execution`；
3. 模型可结构化表达成功、失败、取消和重试统计。

- [ ] **Step 2: Run test to verify it fails**

Run:
```powershell
$env:DJANGO_SETTINGS_MODULE='platform_service.test_settings'; .\.venv_service\Scripts\python.exe -m pytest service_tests\test_v3_p1_scheduling_execution_center.py -k "schedule_models_capture_queue_retry_aggregate_and_governance_context" -q --basetemp=.pytest_tmp\v3_p1_g4_red_1
```

Expected: FAIL，原因应为当前缺少调度模型。

- [ ] **Step 3: Write minimal implementation**

新增两个正式模型：
```python
class ScenarioScheduleBatchRecord(models.Model):
    schedule_batch_id = models.CharField(max_length=128, unique=True)
    project = models.ForeignKey(ProjectRecord, ...)
    environment = models.ForeignKey(TestEnvironmentRecord, ...)
    scenario_set = models.ForeignKey(ScenarioSetRecord, ...)
    baseline_version = models.ForeignKey(BaselineVersionRecord, ...)
    queue_status = models.CharField(max_length=32, default="queued")
    dispatch_strategy = models.CharField(max_length=32, default="immediate")
    trigger_source = models.CharField(max_length=32, default="schedule_batch")
    aggregate_summary = models.JSONField(default=dict)
```

```python
class ScenarioScheduleItemRecord(models.Model):
    schedule_item_id = models.CharField(max_length=128, unique=True)
    schedule_batch = models.ForeignKey(ScenarioScheduleBatchRecord, related_name="items", ...)
    scenario = models.ForeignKey(ScenarioRecord, related_name="schedule_items", ...)
    execution = models.ForeignKey(ScenarioExecutionRecord, null=True, blank=True, ...)
    item_status = models.CharField(max_length=32, default="queued")
    retry_policy = models.JSONField(default=dict)
    retry_count = models.PositiveIntegerField(default=0)
    max_retry_count = models.PositiveIntegerField(default=0)
    failure_reason = models.TextField(blank=True, default="")
```

- [ ] **Step 4: Run test to verify it passes**

Run:
```powershell
$env:DJANGO_SETTINGS_MODULE='platform_service.test_settings'; .\.venv_service\Scripts\python.exe -m pytest service_tests\test_v3_p1_scheduling_execution_center.py -k "schedule_models_capture_queue_retry_aggregate_and_governance_context" -q --basetemp=.pytest_tmp\v3_p1_g4_green_1
```

Expected: PASS

### Task 2: 服务层红灯测试与项目边界收口

**Files:**
- Modify: `D:\AI\api-test-platform\service_tests\test_v3_p1_scheduling_execution_center.py`
- Modify: `D:\AI\api-test-platform\scenario_service\services.py`

- [ ] **Step 1: Write the failing tests**

```python
def test_schedule_center_blocks_cross_project_batch_and_keeps_retry_scoped(service_test_token: str):
    """TC-V3-P1-ISO-003 调度中心的批量执行与重试不得跨项目串扰。"""
```

```python
def test_schedule_execution_aggregates_success_failure_retry_and_cancel(service_test_token: str, tmp_path):
    """TC-V3-P1-EXEC-003 批量执行、重试和结果聚合应在项目边界内稳定工作。"""
```

测试应覆盖：
1. 同一批次内混入跨项目场景时直接阻断；
2. 立即执行批次能同步产出成功项、失败项和聚合摘要；
3. 失败项重试只影响目标任务项；
4. 队列项取消后聚合摘要更新为 `canceled`。

- [ ] **Step 2: Run tests to verify they fail**

Run:
```powershell
$env:DJANGO_SETTINGS_MODULE='platform_service.test_settings'; .\.venv_service\Scripts\python.exe -m pytest service_tests\test_v3_p1_scheduling_execution_center.py -k "schedule_center_blocks_cross_project_batch_and_keeps_retry_scoped or schedule_execution_aggregates_success_failure_retry_and_cancel" -q --basetemp=.pytest_tmp\v3_p1_g4_red_2
```

Expected: FAIL，原因应为当前缺少批量调度服务和重试/取消逻辑。

- [ ] **Step 3: Write minimal implementation**

新增服务方法：
```python
def create_schedule_batch(...): ...
def get_schedule_batch_detail(...): ...
def retry_schedule_item(...): ...
def cancel_schedule_item(...): ...
```

关键约束：
1. 先校验 `can_schedule` 权限；
2. 所有场景必须属于同一 `project / environment`；
3. 默认 `dispatch_strategy="immediate"` 时同步执行并写回 `queued -> running -> succeeded/failed`；
4. `dispatch_strategy="manual_queue"` 时保留 `queued`，供取消演示；
5. 聚合摘要必须返回成功、失败、重试、取消和总数统计。

- [ ] **Step 4: Run tests to verify they pass**

Run:
```powershell
$env:DJANGO_SETTINGS_MODULE='platform_service.test_settings'; .\.venv_service\Scripts\python.exe -m pytest service_tests\test_v3_p1_scheduling_execution_center.py -k "schedule_center_blocks_cross_project_batch_and_keeps_retry_scoped or schedule_execution_aggregates_success_failure_retry_and_cancel" -q --basetemp=.pytest_tmp\v3_p1_g4_green_2
```

Expected: PASS

### Task 3: 接口红灯测试、入口承接与审计闭环

**Files:**
- Modify: `D:\AI\api-test-platform\service_tests\test_v3_p1_scheduling_execution_center.py`
- Modify: `D:\AI\api-test-platform\scenario_service\serializers.py`
- Modify: `D:\AI\api-test-platform\scenario_service\views.py`
- Modify: `D:\AI\api-test-platform\scenario_service\urls.py`
- Modify: `D:\AI\api-test-platform\scenario_service\templates\scenario_service\workbench.html`

- [ ] **Step 1: Write the failing tests**

```python
def test_schedule_batch_api_supports_create_retry_cancel_and_aggregate_query(service_test_token: str, tmp_path):
    """TC-V3-P1-API-004 调度中心接口应支持批量任务创建、重试、取消和结果聚合查询。"""
```

```python
def test_schedule_center_forms_authorize_execute_retry_aggregate_audit_closure(service_test_token: str, tmp_path):
    """TC-V3-P1-INT-003 调度中心独立验收链路应形成完整闭环。"""
```

```python
def test_v3_workbench_renders_schedule_center_region():
    """TC-V3-P1-UI-001 补充：Web 正式入口应能承接调度中心区域。"""
```

接口建议：
1. `POST /api/v2/scenarios/governance/schedule-batches/`
2. `GET /api/v2/scenarios/governance/schedule-batches/`
3. `GET /api/v2/scenarios/governance/schedule-batches/<batch_id>/`
4. `POST /api/v2/scenarios/governance/schedule-batches/<batch_id>/items/<item_id>/retry/`
5. `POST /api/v2/scenarios/governance/schedule-batches/<batch_id>/items/<item_id>/cancel/`

- [ ] **Step 2: Run tests to verify they fail**

Run:
```powershell
$env:DJANGO_SETTINGS_MODULE='platform_service.test_settings'; .\.venv_service\Scripts\python.exe -m pytest service_tests\test_v3_p1_scheduling_execution_center.py -k "schedule_batch_api_supports_create_retry_cancel_and_aggregate_query or schedule_center_forms_authorize_execute_retry_aggregate_audit_closure or renders_schedule_center_region" -q --basetemp=.pytest_tmp\v3_p1_g4_red_3
```

Expected: FAIL，原因应为当前没有调度 API 和入口区域。

- [ ] **Step 3: Write minimal implementation**

要求：
1. 新增调度 API 序列化和视图；
2. 返回结构需区分批次级、任务项级和聚合级状态；
3. 调度创建、重试、取消必须写入审计日志；
4. Web 工作台新增 `data-testid="schedule-center-panel"` 区域，消费上述 API。

- [ ] **Step 4: Run tests to verify they pass**

Run:
```powershell
$env:DJANGO_SETTINGS_MODULE='platform_service.test_settings'; .\.venv_service\Scripts\python.exe -m pytest service_tests\test_v3_p1_scheduling_execution_center.py -k "schedule_batch_api_supports_create_retry_cancel_and_aggregate_query or schedule_center_forms_authorize_execute_retry_aggregate_audit_closure or renders_schedule_center_region" -q --basetemp=.pytest_tmp\v3_p1_g4_green_3
```

Expected: PASS

### Task 4: G4 全量回归与文档同步

**Files:**
- Modify: `D:\AI\api-test-platform\README.md`
- Modify: `D:\AI\api-test-platform\product_document\阶段文档\V3阶段工作计划文档.md`
- Modify: `D:\AI\api-test-platform\product_document\测试文档\详细测试用例说明书(V3-P1).md`
- Modify: `D:\AI\api-test-platform\product_document\本地MySQL数据库信息.md`
- Modify: `D:\AI\api-test-platform\task_plan.md`
- Modify: `D:\AI\api-test-platform\findings.md`
- Modify: `D:\AI\api-test-platform\progress.md`

- [ ] **Step 1: Run targeted G4 tests**

Run:
```powershell
$env:DJANGO_SETTINGS_MODULE='platform_service.test_settings'; .\.venv_service\Scripts\python.exe -m pytest service_tests\test_v3_p1_scheduling_execution_center.py -q --basetemp=.pytest_tmp\v3_p1_g4_targeted
```

Expected: PASS

- [ ] **Step 2: Run full regression**

Run:
```powershell
$env:DJANGO_SETTINGS_MODULE='platform_service.test_settings'; .\.venv_service\Scripts\python.exe -m pytest service_tests -q --basetemp=.pytest_tmp\v3_p1_g4_service
python -m pytest tests/platform_core -q --basetemp=.pytest_tmp\v3_p1_g4_platform_core
python -m pytest tests -q --basetemp=.pytest_tmp\v3_p1_g4_root
python -m pytest api_test/tests -q --basetemp=.pytest_tmp\v3_p1_g4_api_test
$env:DJANGO_SETTINGS_MODULE='platform_service.test_settings'; .\.venv_service\Scripts\python.exe manage.py makemigrations scenario_service --check --dry-run --settings=platform_service.test_settings
```

Expected:
1. 全部 PASS；
2. 迁移检查为 `No changes detected in app 'scenario_service'`。

- [ ] **Step 3: Sync docs**

文档至少回填：
1. `README.md` 当前状态更新为 `P1-G4` 已完成；
2. `V3阶段工作计划文档.md` 把 `V3-IMP-003` 说明更新为 `G1/G2/G3/G4` 完成；
3. `详细测试用例说明书(V3-P1).md` 回填 `MODEL-004 / ISO-003 / API-004 / EXEC-003 / INT-003` 执行结果；
4. `本地MySQL数据库信息.md` 补记新增调度表清单。

## Coverage Check

- `TC-V3-P1-MODEL-004` -> Task 1
- `TC-V3-P1-ISO-003` -> Task 2
- `TC-V3-P1-API-004` -> Task 3
- `TC-V3-P1-EXEC-003` -> Task 2 / Task 3
- `TC-V3-P1-INT-003` -> Task 3

## Notes

- 本轮不引入独立异步 worker，调度执行采用同步编排 + 正式状态记录，优先满足当前阶段的可验收性和项目边界稳定性。
- 失败场景优先通过不受支持的公开基线操作构造，确保在 MySQL 和现有执行底座上可稳定复现。
- 所有新增方法、模型和模板逻辑继续补齐中文注释，并同步更新阶段文档与测试文档。
