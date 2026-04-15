# V3 P1 G1 权限与审计治理 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在现有 `scenario_service` 治理底座上补齐 V3 `P1-G1` 的项目级角色授权、关键动作阻断和审计日志闭环，并完成对应自动化测试与文档同步。

**Architecture:** 继续复用当前 `Django + DRF + MySQL + service_tests` 的增量架构，不引入完整登录体系，也不新建独立 IAM 子系统。第一批实现以“项目成员角色记录 + 审计日志记录 + 服务层显式 actor 门禁”为主，先把审核、执行和查看等关键动作真正受项目边界约束；浏览器入口和后续 Windows Demo 继续消费同一服务契约。

**Tech Stack:** Python 3.12、Django、Django REST Framework、pytest、MySQL、现有 `scenario_service` 模板入口

---

## Scope Check

`P1` 当前包含权限审计、抓包正式执行、入口深化和调度中心四个子系统，不适合塞进一份同步实施计划。本计划只覆盖 `P1-G1 权限体系与审计治理`，其余 `G2 / G3 / G4` 需在本计划稳定后继续拆分独立计划。

## File Structure

- Create: `D:\AI\api-test-platform\service_tests\test_v3_p1_permission_audit.py`
  作用：覆盖项目成员授权、越权阻断、审核/执行留痕和审计查询主线。
- Create: `D:\AI\api-test-platform\scenario_service\migrations\0006_projectroleassignmentrecord_scenarioauditlogrecord.py`
  作用：落库项目角色授权和审计日志模型。
- Modify: `D:\AI\api-test-platform\scenario_service\models.py`
  作用：新增项目角色授权记录和审计日志记录模型。
- Modify: `D:\AI\api-test-platform\scenario_service\services.py`
  作用：增加角色授权查询、权限校验、审核/执行阻断和审计写入。
- Modify: `D:\AI\api-test-platform\scenario_service\serializers.py`
  作用：补充授权写入、授权查询和审计查询请求校验器，并为现有执行/列表查询增加 actor 参数。
- Modify: `D:\AI\api-test-platform\scenario_service\views.py`
  作用：暴露授权管理与审计日志接口，并让详情/列表/执行/审核入口承接 actor。
- Modify: `D:\AI\api-test-platform\scenario_service\urls.py`
  作用：注册授权与审计治理路由。
- Modify: `D:\AI\api-test-platform\scenario_service\governance.py`
  作用：必要时补充项目级授权默认上下文辅助能力，但不引入复杂耦合。
- Modify: `D:\AI\api-test-platform\product_document\阶段文档\V3阶段工作计划文档.md`
  作用：回填 `P1-G1` 开发与测试进度。
- Modify: `D:\AI\api-test-platform\product_document\测试文档\详细测试用例说明书(V3-P1).md`
  作用：回填 `TC-V3-P1-MODEL-001/002`、`API-001/002`、`EXEC-002` 等已执行结论。
- Modify: `D:\AI\api-test-platform\README.md`
  作用：同步当前阶段已进入 `V3 P1 G1` 开发。
- Modify: `D:\AI\api-test-platform\task_plan.md`
- Modify: `D:\AI\api-test-platform\findings.md`
- Modify: `D:\AI\api-test-platform\progress.md`

### Task 1: 权限对象与审计对象建模

**Files:**
- Create: `D:\AI\api-test-platform\service_tests\test_v3_p1_permission_audit.py`
- Modify: `D:\AI\api-test-platform\scenario_service\models.py`
- Modify: `D:\AI\api-test-platform\scenario_service\services.py`

- [ ] **Step 1: Write the failing test**

```python
def test_project_role_assignment_can_be_created_and_queried_via_service(service_test_token: str):
    service = FunctionalCaseScenarioService()
    project_code = f"project-p1-auth-{service_test_token}"
    service.governance_service.resolve_context(project_code=project_code)

    assignment = service.assign_project_role(
        project_code=project_code,
        operator="platform-admin",
        subject_name=f"qa_viewer_{service_test_token}",
        role_code="viewer",
    )
    assignments = service.list_project_roles(project_code=project_code)

    assert assignment["project_code"] == project_code
    assert assignment["subject_name"] == f"qa_viewer_{service_test_token}"
    assert assignment["role_code"] == "viewer"
    assert assignment["permissions"]["can_view"] is True
    assert assignments[0]["subject_name"] == f"qa_viewer_{service_test_token}"
```

```python
def test_blocked_review_attempt_writes_audit_log(service_test_token: str):
    service = FunctionalCaseScenarioService()
    scenario = service.import_functional_case(...)
    service.assign_project_role(
        project_code=scenario.project.project_code,
        operator="platform-admin",
        subject_name=f"qa_viewer_{service_test_token}",
        role_code="viewer",
    )

    with pytest.raises(ScenarioServiceError) as error_info:
        service.review_scenario(
            scenario_id=scenario.scenario_id,
            review_status="approved",
            reviewer=f"qa_viewer_{service_test_token}",
            review_comment="越权尝试",
        )

    audit_logs = service.list_audit_logs(project_code=scenario.project.project_code, action_type="review_scenario")
    assert error_info.value.code == "project_action_forbidden"
    assert audit_logs[0]["action_result"] == "blocked"
    assert audit_logs[0]["actor_name"] == f"qa_viewer_{service_test_token}"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.\.venv_service\Scripts\python.exe -m pytest service_tests\test_v3_p1_permission_audit.py -k "role_assignment or blocked_review_attempt" -q --basetemp=.pytest_tmp\v3_p1_g1_red_1`

Expected: FAIL，原因应为当前服务层不存在授权对象、授权查询和审计日志能力。

- [ ] **Step 3: Write minimal implementation**

```python
class ProjectRoleAssignmentRecord(models.Model):
    """项目成员角色授权记录。"""

    assignment_id = models.CharField(max_length=128, unique=True)
    project = models.ForeignKey(ProjectRecord, related_name="role_assignments", on_delete=models.CASCADE)
    subject_name = models.CharField(max_length=128)
    role_code = models.CharField(max_length=32)
    can_view = models.BooleanField(default=False)
    can_edit = models.BooleanField(default=False)
    can_execute = models.BooleanField(default=False)
    can_review = models.BooleanField(default=False)
    can_schedule = models.BooleanField(default=False)
    can_grant = models.BooleanField(default=False)
    granted_by = models.CharField(max_length=128, default="system")
    is_active = models.BooleanField(default=True)
    metadata = models.JSONField(default=dict)
```

```python
class ScenarioAuditLogRecord(models.Model):
    """关键治理动作审计日志记录。"""

    audit_id = models.CharField(max_length=128, unique=True)
    project = models.ForeignKey(ProjectRecord, related_name="audit_logs", on_delete=models.PROTECT, null=True, blank=True)
    scenario = models.ForeignKey(ScenarioRecord, related_name="audit_logs", on_delete=models.SET_NULL, null=True, blank=True)
    execution = models.ForeignKey(ScenarioExecutionRecord, related_name="audit_logs", on_delete=models.SET_NULL, null=True, blank=True)
    actor_name = models.CharField(max_length=128)
    action_type = models.CharField(max_length=64)
    action_result = models.CharField(max_length=32)
    target_type = models.CharField(max_length=32, default="scenario")
    target_id = models.CharField(max_length=128, blank=True, default="")
    detail_message = models.TextField(blank=True, default="")
    metadata = models.JSONField(default=dict)
```

```python
ROLE_PERMISSION_TEMPLATES = {
    "viewer": {"can_view": True},
    "editor": {"can_view": True, "can_edit": True},
    "executor": {"can_view": True, "can_execute": True},
    "reviewer": {"can_view": True, "can_review": True},
    "scheduler": {"can_view": True, "can_execute": True, "can_schedule": True},
    "project_admin": {
        "can_view": True,
        "can_edit": True,
        "can_execute": True,
        "can_review": True,
        "can_schedule": True,
        "can_grant": True,
    },
}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.\.venv_service\Scripts\python.exe -m pytest service_tests\test_v3_p1_permission_audit.py -k "role_assignment or blocked_review_attempt" -q --basetemp=.pytest_tmp\v3_p1_g1_green_1`

Expected: PASS

- [ ] **Step 5: Generate migration and verify no drift**

Run: `.\.venv_service\Scripts\python.exe manage.py makemigrations scenario_service --settings=platform_service.test_settings`

Expected: 生成 `0006_projectroleassignmentrecord_scenarioauditlogrecord.py`

Run: `.\.venv_service\Scripts\python.exe manage.py makemigrations scenario_service --check --dry-run --settings=platform_service.test_settings`

Expected: `No changes detected in app 'scenario_service'`

### Task 2: 授权管理接口与审计查询接口

**Files:**
- Modify: `D:\AI\api-test-platform\service_tests\test_v3_p1_permission_audit.py`
- Modify: `D:\AI\api-test-platform\scenario_service\serializers.py`
- Modify: `D:\AI\api-test-platform\scenario_service\views.py`
- Modify: `D:\AI\api-test-platform\scenario_service\urls.py`
- Modify: `D:\AI\api-test-platform\scenario_service\services.py`

- [ ] **Step 1: Write the failing test**

```python
def test_access_grant_and_audit_log_endpoints_return_project_scoped_contract(service_test_token: str):
    client = APIClient()
    project_code = f"project-p1-api-{service_test_token}"
    FunctionalCaseScenarioService().governance_service.resolve_context(project_code=project_code)

    grant_response = client.post(
        "/api/v2/scenarios/governance/access-grants/",
        {
            "project_code": project_code,
            "operator": "platform-admin",
            "subject_name": f"qa_executor_{service_test_token}",
            "role_code": "executor",
        },
        format="json",
    )
    list_response = client.get("/api/v2/scenarios/governance/access-grants/", {"project_code": project_code})
    audit_response = client.get("/api/v2/scenarios/governance/audit-logs/", {"project_code": project_code})

    assert grant_response.status_code == 201
    assert list_response.status_code == 200
    assert list_response.json()["data"][0]["role_code"] == "executor"
    assert audit_response.status_code == 200
    assert audit_response.json()["data"][0]["action_type"] == "assign_project_role"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.\.venv_service\Scripts\python.exe -m pytest service_tests\test_v3_p1_permission_audit.py -k "access_grant_and_audit_log_endpoints" -q --basetemp=.pytest_tmp\v3_p1_g1_red_2`

Expected: FAIL，原因应为授权与审计路由、序列化器和视图尚未接入。

- [ ] **Step 3: Write minimal implementation**

```python
class ProjectRoleAssignmentRequestSerializer(serializers.Serializer):
    project_code = serializers.CharField()
    operator = serializers.CharField()
    subject_name = serializers.CharField()
    role_code = serializers.ChoiceField(
        choices=["viewer", "editor", "executor", "reviewer", "scheduler", "project_admin"]
    )
```

```python
class ProjectRoleAssignmentView(APIView):
    def get(self, request):
        serializer = ProjectRoleAssignmentQuerySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        return Response({"success": True, "data": SCENARIO_SERVICE.list_project_roles(**serializer.validated_data)})

    def post(self, request):
        serializer = ProjectRoleAssignmentRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = SCENARIO_SERVICE.assign_project_role(**serializer.validated_data)
        return Response({"success": True, "data": data}, status=status.HTTP_201_CREATED)
```

```python
urlpatterns += [
    path("governance/access-grants/", ProjectRoleAssignmentView.as_view(), name="governance-access-grants"),
    path("governance/audit-logs/", ScenarioAuditLogListView.as_view(), name="governance-audit-logs"),
]
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.\.venv_service\Scripts\python.exe -m pytest service_tests\test_v3_p1_permission_audit.py -k "access_grant_and_audit_log_endpoints" -q --basetemp=.pytest_tmp\v3_p1_g1_green_2`

Expected: PASS

### Task 3: 审核、执行和查看门禁接入

**Files:**
- Modify: `D:\AI\api-test-platform\service_tests\test_v3_p1_permission_audit.py`
- Modify: `D:\AI\api-test-platform\scenario_service\services.py`
- Modify: `D:\AI\api-test-platform\scenario_service\serializers.py`
- Modify: `D:\AI\api-test-platform\scenario_service\views.py`

- [ ] **Step 1: Write the failing test**

```python
def test_review_and_execute_require_project_roles_and_write_success_audits(tmp_path, service_test_token: str):
    client = APIClient()
    service = FunctionalCaseScenarioService()
    scenario = service.import_functional_case(...)

    client.post(
        "/api/v2/scenarios/governance/access-grants/",
        {
            "project_code": scenario.project.project_code,
            "operator": "platform-admin",
            "subject_name": f"qa_reviewer_{service_test_token}",
            "role_code": "reviewer",
        },
        format="json",
    )
    client.post(
        "/api/v2/scenarios/governance/access-grants/",
        {
            "project_code": scenario.project.project_code,
            "operator": "platform-admin",
            "subject_name": f"qa_executor_{service_test_token}",
            "role_code": "executor",
        },
        format="json",
    )

    review_response = client.post(
        f"/api/v2/scenarios/{scenario.scenario_id}/review/",
        {"review_status": "approved", "reviewer": f"qa_reviewer_{service_test_token}", "review_comment": "通过"},
        format="json",
    )
    execute_response = client.post(
        f"/api/v2/scenarios/{scenario.scenario_id}/execute/",
        {
            "project_code": scenario.project.project_code,
            "environment_code": scenario.environment.environment_code,
            "operator": f"qa_executor_{service_test_token}",
            "workspace_root": str(tmp_path / "run-ok"),
        },
        format="json",
    )
    blocked_detail_response = client.get(
        f"/api/v2/scenarios/{scenario.scenario_id}/",
        {"actor": f"qa_other_{service_test_token}"},
    )
    audit_response = client.get(
        "/api/v2/scenarios/governance/audit-logs/",
        {"project_code": scenario.project.project_code, "actor_name": f"qa_executor_{service_test_token}"},
    )

    assert review_response.status_code == 200
    assert execute_response.status_code == 202
    assert blocked_detail_response.status_code == 403
    assert any(item["action_type"] == "execute_scenario" and item["action_result"] == "succeeded" for item in audit_response.json()["data"])
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.\.venv_service\Scripts\python.exe -m pytest service_tests\test_v3_p1_permission_audit.py -k "review_and_execute_require_project_roles" -q --basetemp=.pytest_tmp\v3_p1_g1_red_3`

Expected: FAIL，原因应为现有审核、执行和详情接口尚未承接 actor 权限校验。

- [ ] **Step 3: Write minimal implementation**

```python
def review_scenario(self, scenario_id: str, review_status: str, reviewer: str, review_comment: str = "") -> ScenarioRecord:
    scenario = self._get_scenario(scenario_id=scenario_id)
    self._authorize_project_action(
        project=scenario.project,
        actor_name=reviewer,
        action_type="review_scenario",
        required_permission="can_review",
        scenario=scenario,
    )
    ...
```

```python
def request_execution(self, scenario_id: str, project_code: str | None = None, environment_code: str | None = None, workspace_root: str | Path | None = None, operator: str | None = None) -> ScenarioExecutionRecord:
    scenario = self._get_scenario(scenario_id=scenario_id)
    if operator:
        self._authorize_project_action(
            project=scenario.project,
            actor_name=operator,
            action_type="execute_scenario",
            required_permission="can_execute",
            scenario=scenario,
        )
    ...
```

```python
def get_scenario_detail(self, scenario_id: str, actor: str | None = None) -> dict:
    scenario = self._get_scenario(scenario_id=scenario_id)
    if actor:
        self._authorize_project_action(
            project=scenario.project,
            actor_name=actor,
            action_type="view_scenario",
            required_permission="can_view",
            scenario=scenario,
        )
    ...
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.\.venv_service\Scripts\python.exe -m pytest service_tests\test_v3_p1_permission_audit.py -k "review_and_execute_require_project_roles" -q --basetemp=.pytest_tmp\v3_p1_g1_green_3`

Expected: PASS

### Task 4: P1-G1 回归、文档同步与阶段记录

**Files:**
- Modify: `D:\AI\api-test-platform\product_document\阶段文档\V3阶段工作计划文档.md`
- Modify: `D:\AI\api-test-platform\product_document\测试文档\详细测试用例说明书(V3-P1).md`
- Modify: `D:\AI\api-test-platform\README.md`
- Modify: `D:\AI\api-test-platform\task_plan.md`
- Modify: `D:\AI\api-test-platform\findings.md`
- Modify: `D:\AI\api-test-platform\progress.md`

- [ ] **Step 1: Run targeted P1 G1 service tests**

Run: `.\.venv_service\Scripts\python.exe -m pytest service_tests\test_v3_p1_permission_audit.py -q --basetemp=.pytest_tmp\v3_p1_g1_targeted`

Expected: PASS

- [ ] **Step 2: Run service regression**

Run: `.\.venv_service\Scripts\python.exe -m pytest service_tests -q --basetemp=.pytest_tmp\v3_p1_g1_service`

Expected: PASS

- [ ] **Step 3: Run non-service regression**

Run: `python -m pytest tests/platform_core -q --basetemp=.pytest_tmp\v3_p1_g1_platform_core`

Expected: PASS

Run: `python -m pytest tests -q --basetemp=.pytest_tmp\v3_p1_g1_root`

Expected: PASS

Run: `python -m pytest api_test/tests -q --basetemp=.pytest_tmp\v3_p1_g1_api_test`

Expected: PASS

- [ ] **Step 4: Sync docs**

```markdown
- 在 `V3阶段工作计划文档.md` 中把 `V3-IMP-003` 拆分为 `P1-G1 已启动 / 已完成首批权限审计治理`
- 在 `详细测试用例说明书(V3-P1).md` 中回填模型、API、ISO、EXEC 用例的首批执行结果
- 在 `README.md` 中把当前阶段切换到 “V3 P1 G1 开发中”
```

- [ ] **Step 5: Record risks and follow-up**

```markdown
- 明确当前仅完成“显式 actor + 项目角色 + 审计日志”第一批能力
- 记录后续 `P1-G2` 需把抓包正式执行接入同一权限与审计门禁
- 记录后续 `P1-G3/G4` 需继续复用同一授权查询与审计查询契约
```

## Coverage Check

- `TC-V3-P1-MODEL-001` -> Task 1
- `TC-V3-P1-MODEL-002` -> Task 1
- `TC-V3-P1-API-001` -> Task 2
- `TC-V3-P1-API-002` -> Task 2
- `TC-V3-P1-ISO-001` -> Task 3
- `TC-V3-P1-EXEC-002` -> Task 3

## Notes

- 当前计划不引入完整登录态，只使用显式 `actor / reviewer / operator` 承接第一批项目级角色门禁。
- 所有新增方法、测试和配置说明继续使用中文注释。
- 推送动作不包含在本计划内；应在本轮实现、验证和文档同步完成后再单独提交与推送。
