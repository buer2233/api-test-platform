# V3 P1 G2 抓包正式执行闭环 Implementation Plan

> **For agentic workers:** 本计划承接已获批准的 `V3 P1-G2` 范围，按 TDD 顺序推进“正式确认 -> 绑定确认 -> 正式执行 -> 结果回写”闭环，不与 `G3 / G4` 混做。

**Goal:** 在现有 `scenario_service` 抓包草稿导入能力之上，补齐 V3 `P1-G2` 的正式确认对象、动态变量绑定确认、抓包正式执行门禁、结果回写与审计留痕，并完成对应自动化测试与文档同步。

**Architecture:** 延续当前 `Django + DRF + MySQL + service_tests` 的增量改造路线，不新建独立抓包子系统。抓包仍先导入为 `ScenarioRecord`，再通过单独的“抓包正式执行对象”记录确认态和绑定态；正式执行仍复用现有 `ScenarioExecutionRecord` 与 `ScenarioExecutionPipeline`，避免并行执行体系。

**Tech Stack:** Python 3.12、Django、Django REST Framework、pytest、MySQL、现有 `scenario_service` / `platform_core` 执行底座

---

## Scope Check

`P1-G2` 只覆盖以下主线：
1. 抓包草稿正式确认；
2. 动态变量 / 操作绑定确认；
3. 在项目、环境和权限门禁内触发正式执行；
4. 抓包执行结果回写、查询与审计；
5. 对 `P1-G1` 权限与审计能力的复用验证。

本计划**不包含**：
1. Web 正式入口深化；
2. Windows Demo 套壳与打包；
3. 调度中心、批量执行与重试；
4. 复杂抓包智能映射或 AI 自动修复。

## File Structure

- Create: `D:\AI\api-test-platform\service_tests\test_v3_p1_traffic_capture_execution.py`
  作用：覆盖正式确认、绑定确认、执行阻断、执行成功与审计闭环。
- Create: `D:\AI\api-test-platform\scenario_service\migrations\0007_trafficcaptureformalizationrecord.py`
  作用：落库抓包正式执行对象。
- Modify: `D:\AI\api-test-platform\scenario_service\models.py`
  作用：新增抓包正式执行对象模型。
- Modify: `D:\AI\api-test-platform\scenario_service\services.py`
  作用：新增抓包正式确认、绑定确认、执行前校验、执行后结果回写与摘要构造。
- Modify: `D:\AI\api-test-platform\scenario_service\serializers.py`
  作用：新增抓包正式确认与绑定确认请求校验器。
- Modify: `D:\AI\api-test-platform\scenario_service\views.py`
  作用：新增抓包正式确认与绑定确认接口。
- Modify: `D:\AI\api-test-platform\scenario_service\urls.py`
  作用：注册抓包正式确认与绑定确认路由。
- Modify: `D:\AI\api-test-platform\platform_core\scenario_execution.py`
  作用：必要时补充抓包来源场景执行时的来源类型和最小绑定校验，不新增第二套执行器。
- Modify: `D:\AI\api-test-platform\product_document\阶段文档\V3阶段工作计划文档.md`
  作用：回填 `P1-G2` 开发与测试进度。
- Modify: `D:\AI\api-test-platform\product_document\测试文档\详细测试用例说明书(V3-P1).md`
  作用：回填 `TC-V3-P1-MODEL-003`、`TC-V3-P1-API-003`、`TC-V3-P1-ISO-002`、`TC-V3-P1-EXEC-001`、`TC-V3-P1-INT-001` 的执行结果。
- Modify: `D:\AI\api-test-platform\README.md`
  作用：同步当前阶段已推进到 `V3 P1 G2`。
- Modify: `D:\AI\api-test-platform\task_plan.md`
- Modify: `D:\AI\api-test-platform\findings.md`
- Modify: `D:\AI\api-test-platform\progress.md`

### Task 1: 抓包正式执行对象与红灯测试

**Files:**
- Create: `D:\AI\api-test-platform\service_tests\test_v3_p1_traffic_capture_execution.py`
- Modify: `D:\AI\api-test-platform\scenario_service\models.py`
- Modify: `D:\AI\api-test-platform\scenario_service\services.py`

- [ ] **Step 1: Write the failing test**

```python
def test_traffic_capture_formalization_tracks_confirmation_binding_and_readiness(service_test_token: str):
    service = FunctionalCaseScenarioService()
    scenario = service.import_traffic_capture(
        capture_name=f"抓包正式执行-{service_test_token}",
        capture_payload=build_traffic_capture_payload(),
        project_code=f"capture-project-{service_test_token}",
        environment_code=f"capture-env-{service_test_token}",
        scenario_set_code=f"capture-set-{service_test_token}",
    )
    service.review_scenario(
        scenario_id=scenario.scenario_id,
        review_status="approved",
        reviewer="qa-owner",
        review_comment="审核通过",
    )

    confirmation = service.confirm_traffic_capture(
        scenario_id=scenario.scenario_id,
        confirmer="qa-owner",
        confirm_comment="允许进入正式绑定阶段",
    )
    binding_summary = service.confirm_traffic_capture_bindings(
        scenario_id=scenario.scenario_id,
        confirmer="qa-owner",
        step_bindings=[
            {
                "step_id": scenario.steps.all().order_by("step_order", "id")[0].step_id,
                "operation_id": "operation-get-user",
                "request": {"path_params": {"user_id": 1}},
                "expected": {"status_code": 200, "extract": {"user_id": "id"}},
                "uses": {},
            },
            {
                "step_id": scenario.steps.all().order_by("step_order", "id")[1].step_id,
                "operation_id": "operation-list-user-todos",
                "request": {},
                "expected": {"status_code": 200},
                "uses": {"user_id": "$scenario.user_id"},
            },
        ],
        confirm_comment="抓包候选绑定已转正式绑定",
    )
    detail = service.get_scenario_detail(scenario_id=scenario.scenario_id)

    assert confirmation["confirmation_status"] == "confirmed"
    assert binding_summary["binding_status"] == "confirmed"
    assert detail["traffic_capture_formalization"]["execution_readiness"] == "ready"
    assert detail["issue_codes"] == []
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.\.venv_service\Scripts\python.exe -m pytest service_tests\test_v3_p1_traffic_capture_execution.py -k "formalization_tracks_confirmation_binding_and_readiness" -q --basetemp=.pytest_tmp\v3_p1_g2_red_1`

Expected: FAIL，原因应为当前不存在抓包正式执行对象、确认接口与绑定确认能力。

- [ ] **Step 3: Write minimal implementation**

```python
class TrafficCaptureFormalizationRecord(models.Model):
    """抓包场景正式执行治理对象。"""

    confirmation_id = models.CharField(max_length=128, unique=True)
    scenario = models.OneToOneField(ScenarioRecord, related_name="traffic_capture_formalization", on_delete=models.CASCADE)
    project = models.ForeignKey(ProjectRecord, related_name="traffic_capture_formalizations", on_delete=models.PROTECT)
    environment = models.ForeignKey(TestEnvironmentRecord, related_name="traffic_capture_formalizations", on_delete=models.PROTECT)
    confirmation_status = models.CharField(max_length=32, default="draft")
    binding_status = models.CharField(max_length=32, default="pending")
    execution_readiness = models.CharField(max_length=32, default="blocked")
    confirmed_by = models.CharField(max_length=128, blank=True, default="")
    bindings_confirmed_by = models.CharField(max_length=128, blank=True, default="")
    last_execution_id = models.CharField(max_length=128, blank=True, default="")
    metadata = models.JSONField(default=dict)
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.\.venv_service\Scripts\python.exe -m pytest service_tests\test_v3_p1_traffic_capture_execution.py -k "formalization_tracks_confirmation_binding_and_readiness" -q --basetemp=.pytest_tmp\v3_p1_g2_green_1`

Expected: PASS

- [ ] **Step 5: Generate migration and verify no drift**

Run: `.\.venv_service\Scripts\python.exe manage.py makemigrations scenario_service --settings=platform_service.test_settings`

Expected: 生成 `0007_trafficcaptureformalizationrecord.py`

Run: `.\.venv_service\Scripts\python.exe manage.py makemigrations scenario_service --check --dry-run --settings=platform_service.test_settings`

Expected: `No changes detected in app 'scenario_service'`

### Task 2: 抓包正式确认 / 绑定确认 API

**Files:**
- Modify: `D:\AI\api-test-platform\service_tests\test_v3_p1_traffic_capture_execution.py`
- Modify: `D:\AI\api-test-platform\scenario_service\serializers.py`
- Modify: `D:\AI\api-test-platform\scenario_service\views.py`
- Modify: `D:\AI\api-test-platform\scenario_service\urls.py`
- Modify: `D:\AI\api-test-platform\scenario_service\services.py`

- [ ] **Step 1: Write the failing test**

```python
def test_traffic_capture_confirmation_endpoints_form_project_scoped_contract(service_test_token: str):
    client = APIClient()
    scenario = FunctionalCaseScenarioService().import_traffic_capture(...)
    FunctionalCaseScenarioService().review_scenario(
        scenario_id=scenario.scenario_id,
        review_status="approved",
        reviewer="qa-owner",
        review_comment="审核通过",
    )

    confirm_response = client.post(
        f"/api/v2/scenarios/{scenario.scenario_id}/traffic-capture/confirm/",
        {"confirmer": "qa-owner", "confirm_comment": "进入正式绑定阶段"},
        format="json",
    )
    binding_response = client.post(
        f"/api/v2/scenarios/{scenario.scenario_id}/traffic-capture/bindings/confirm/",
        {
            "confirmer": "qa-owner",
            "confirm_comment": "绑定确认",
            "step_bindings": [...],
        },
        format="json",
    )
    detail_response = client.get(f"/api/v2/scenarios/{scenario.scenario_id}/")

    assert confirm_response.status_code == 200
    assert binding_response.status_code == 200
    assert detail_response.json()["data"]["traffic_capture_formalization"]["execution_readiness"] == "ready"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.\.venv_service\Scripts\python.exe -m pytest service_tests\test_v3_p1_traffic_capture_execution.py -k "confirmation_endpoints_form_project_scoped_contract" -q --basetemp=.pytest_tmp\v3_p1_g2_red_2`

Expected: FAIL，原因应为确认接口、绑定确认接口和序列化器尚未接入。

- [ ] **Step 3: Write minimal implementation**

```python
urlpatterns += [
    path(
        "<str:scenario_id>/traffic-capture/confirm/",
        TrafficCaptureConfirmView.as_view(),
        name="scenario-traffic-capture-confirm",
    ),
    path(
        "<str:scenario_id>/traffic-capture/bindings/confirm/",
        TrafficCaptureBindingConfirmView.as_view(),
        name="scenario-traffic-capture-binding-confirm",
    ),
]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.\.venv_service\Scripts\python.exe -m pytest service_tests\test_v3_p1_traffic_capture_execution.py -k "confirmation_endpoints_form_project_scoped_contract" -q --basetemp=.pytest_tmp\v3_p1_g2_green_2`

Expected: PASS

### Task 3: 抓包正式执行门禁、结果回写与审计

**Files:**
- Modify: `D:\AI\api-test-platform\service_tests\test_v3_p1_traffic_capture_execution.py`
- Modify: `D:\AI\api-test-platform\scenario_service\services.py`
- Modify: `D:\AI\api-test-platform\platform_core\scenario_execution.py`

- [ ] **Step 1: Write the failing test**

```python
def test_traffic_capture_execution_requires_formalization_and_writes_traceable_result(tmp_path, service_test_token: str):
    client = APIClient()
    service = FunctionalCaseScenarioService()
    scenario = service.import_traffic_capture(...)
    service.review_scenario(
        scenario_id=scenario.scenario_id,
        review_status="approved",
        reviewer="qa-owner",
        review_comment="审核通过",
    )

    blocked_response = client.post(
        f"/api/v2/scenarios/{scenario.scenario_id}/execute/",
        {
            "project_code": scenario.project.project_code,
            "environment_code": scenario.environment.environment_code,
            "operator": "qa-owner",
            "workspace_root": str(tmp_path / "capture-blocked"),
        },
        format="json",
    )

    client.post(f"/api/v2/scenarios/{scenario.scenario_id}/traffic-capture/confirm/", {...}, format="json")
    client.post(f"/api/v2/scenarios/{scenario.scenario_id}/traffic-capture/bindings/confirm/", {...}, format="json")
    execute_response = client.post(
        f"/api/v2/scenarios/{scenario.scenario_id}/execute/",
        {
            "project_code": scenario.project.project_code,
            "environment_code": scenario.environment.environment_code,
            "operator": "qa-owner",
            "workspace_root": str(tmp_path / "capture-ready"),
        },
        format="json",
    )
    result_response = client.get(f"/api/v2/scenarios/{scenario.scenario_id}/result/")
    audit_response = client.get(
        "/api/v2/scenarios/governance/audit-logs/",
        {"project_code": scenario.project.project_code, "action_type": "confirm_traffic_capture_bindings"},
    )

    assert blocked_response.status_code == 400
    assert blocked_response.json()["error"]["code"] == "traffic_capture_formalization_required"
    assert execute_response.status_code == 202
    assert result_response.json()["data"]["execution_status"] == "passed"
    assert result_response.json()["data"]["traffic_capture_formalization"]["last_execution_id"]
    assert audit_response.json()["data"][0]["action_result"] == "succeeded"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.\.venv_service\Scripts\python.exe -m pytest service_tests\test_v3_p1_traffic_capture_execution.py -k "execution_requires_formalization_and_writes_traceable_result" -q --basetemp=.pytest_tmp\v3_p1_g2_red_3`

Expected: FAIL，原因应为当前抓包场景在审核通过后仍可直接走通或执行失败缺少正式确认门禁。

- [ ] **Step 3: Write minimal implementation**

```python
def _ensure_traffic_capture_execution_ready(self, scenario: ScenarioRecord) -> TrafficCaptureFormalizationRecord:
    """校验抓包场景是否已具备正式执行条件。"""
```

要求：
1. 仅对 `source_type == "traffic_capture"` 的场景生效；
2. 未正式确认或未完成绑定确认时返回结构化错误；
3. 执行成功后回写 `last_execution_id`、`execution_readiness` 和审计日志；
4. 结果查询与详情摘要返回 `traffic_capture_formalization`。

- [ ] **Step 4: Run test to verify it passes**

Run: `.\.venv_service\Scripts\python.exe -m pytest service_tests\test_v3_p1_traffic_capture_execution.py -k "execution_requires_formalization_and_writes_traceable_result" -q --basetemp=.pytest_tmp\v3_p1_g2_green_3`

Expected: PASS

### Task 4: P1-G2 回归、文档同步与阶段记录

**Files:**
- Modify: `D:\AI\api-test-platform\product_document\阶段文档\V3阶段工作计划文档.md`
- Modify: `D:\AI\api-test-platform\product_document\测试文档\详细测试用例说明书(V3-P1).md`
- Modify: `D:\AI\api-test-platform\README.md`
- Modify: `D:\AI\api-test-platform\task_plan.md`
- Modify: `D:\AI\api-test-platform\findings.md`
- Modify: `D:\AI\api-test-platform\progress.md`

- [ ] **Step 1: Run targeted G2 tests**

Run: `.\.venv_service\Scripts\python.exe -m pytest service_tests\test_v3_p1_traffic_capture_execution.py -q --basetemp=.pytest_tmp\v3_p1_g2_targeted`

Expected: PASS

- [ ] **Step 2: Run service regression**

Run: `.\.venv_service\Scripts\python.exe -m pytest service_tests -q --basetemp=.pytest_tmp\v3_p1_g2_service`

Expected: PASS

- [ ] **Step 3: Run non-service regression**

Run: `python -m pytest tests/platform_core -q --basetemp=.pytest_tmp\v3_p1_g2_platform_core`

Expected: PASS

Run: `python -m pytest tests -q --basetemp=.pytest_tmp\v3_p1_g2_root`

Expected: PASS

Run: `python -m pytest api_test/tests -q --basetemp=.pytest_tmp\v3_p1_g2_api_test`

Expected: PASS

- [ ] **Step 4: Sync docs**

```markdown
- 在 `V3阶段工作计划文档.md` 中把 `V3-IMP-003` 的说明更新为 `G1 已完成，G2 已启动/已完成`
- 在 `详细测试用例说明书(V3-P1).md` 中回填 `MODEL-003 / API-003 / ISO-002 / EXEC-001 / INT-001` 的执行结果
- 在 `README.md` 中把当前阶段更新到 “V3 P1 G2 开发中/已完成”
```

- [ ] **Step 5: Record risks and follow-up**

```markdown
- 记录当前抓包正式执行仍以公开基线操作绑定为第一批范围
- 记录 G3 入口深化需消费 `traffic_capture_formalization` 摘要
- 记录 G4 调度中心需复用抓包正式执行门禁，不能绕过确认态与绑定态
```

## Coverage Check

- `TC-V3-P1-MODEL-003` -> Task 1
- `TC-V3-P1-API-003` -> Task 2
- `TC-V3-P1-ISO-002` -> Task 3
- `TC-V3-P1-EXEC-001` -> Task 3
- `TC-V3-P1-INT-001` -> Task 3 / Task 4

## Notes

- 抓包正式执行仍必须复用 `P1-G1` 的 actor 权限与审计门禁，不新增并行鉴权逻辑。
- 所有新增方法、测试和配置说明继续使用中文注释。
- 当前第一批抓包正式执行只承接公开基线操作绑定，不在本轮扩展复杂自动映射策略。
