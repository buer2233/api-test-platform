# V3 P2 AI 治理边界实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在现有建议治理底座上补齐 V3 `P2` 的 AI 治理策略、审批门禁、采纳回退、审计责任链和工作台状态承接能力。

**Architecture:** 继续以 `scenario_service` 为统一事实源，不新建平行 AI 子系统。通过新增治理策略对象和责任链对象，把“建议 -> 审批/拒绝 -> 采纳 -> 回退 -> 复验 -> 留痕”收敛到同一服务层与 MySQL 事实层，并让 `/ui/v3/workbench/` 只消费结构化治理摘要。

**Tech Stack:** Python 3、Django、Django REST Framework、pytest、MySQL 8.4、现有 Django 模板工作台

---

### Task 1: P2 模型与迁移骨架

**Files:**
- Modify: `scenario_service/models.py`
- Create: `scenario_service/migrations/0009_aigovernancepolicyrecord_aisuggestiondecisionrecord_and_more.py`
- Test: `service_tests/test_v3_p2_ai_governance.py`

- [ ] **Step 1: 写失败测试，锁定治理策略对象和责任链对象**

```python
def test_ai_governance_models_capture_policy_scope_and_decision_chain(service_test_token):
    service = FunctionalCaseScenarioService()
    project_code = f"p2-model-{service_test_token}"
    environment_code = f"p2-env-{service_test_token}"
    scenario_set_code = f"p2-set-{service_test_token}"
    context = service.governance_service.resolve_context(
        project_code=project_code,
        environment_code=environment_code,
        scenario_set_code=scenario_set_code,
    )

    policy = service.ensure_ai_governance_policy(
        project_code=project_code,
        operator="platform-admin",
        scope_type="project",
        suggestion_types=["assertion_completion", "step_patch"],
        approval_mode="manual_review",
        rollback_mode="snapshot_restore",
    )

    assert policy["project_code"] == project_code
    assert policy["approval_mode"] == "manual_review"
    assert "step_patch" in policy["suggestion_types"]
    assert policy["auto_execution_enabled"] is False
```

- [ ] **Step 2: 运行失败测试，确认缺口落在模型和服务入口**

Run: `.\\.venv_service\\Scripts\\python.exe -m pytest service_tests\\test_v3_p2_ai_governance.py -k "models_capture_policy_scope" -q --basetemp=.pytest_tmp\\v3_p2_model_red`

Expected: FAIL，提示 `ensure_ai_governance_policy` 或治理模型不存在

- [ ] **Step 3: 写最小实现，新增治理策略和责任链模型**

```python
class AiGovernancePolicyRecord(models.Model):
    project = models.ForeignKey(ProjectRecord, related_name="ai_governance_policies", on_delete=models.CASCADE)
    policy_id = models.CharField(max_length=128, unique=True)
    scope_type = models.CharField(max_length=32, default="project")
    scope_ref = models.CharField(max_length=128, blank=True, default="")
    suggestion_types = models.JSONField(default=list)
    approval_mode = models.CharField(max_length=32, default="manual_review")
    rollback_mode = models.CharField(max_length=32, default="snapshot_restore")
    auto_execution_enabled = models.BooleanField(default=False)
    metadata = models.JSONField(default=dict)


class AiSuggestionDecisionRecord(models.Model):
    project = models.ForeignKey(ProjectRecord, related_name="ai_suggestion_decisions", on_delete=models.PROTECT)
    scenario = models.ForeignKey(ScenarioRecord, related_name="ai_suggestion_decisions", on_delete=models.CASCADE)
    suggestion = models.ForeignKey(ScenarioSuggestionRecord, related_name="decision_records", on_delete=models.CASCADE)
    decision_id = models.CharField(max_length=128, unique=True)
    decision_type = models.CharField(max_length=32)
    decision_status = models.CharField(max_length=32, default="completed")
    actor_name = models.CharField(max_length=128)
    decision_comment = models.TextField(blank=True, default="")
    snapshot_before = models.JSONField(default=dict)
    snapshot_after = models.JSONField(default=dict)
    related_revision_id = models.CharField(max_length=128, blank=True, default="")
    related_execution_id = models.CharField(max_length=128, blank=True, default="")
    metadata = models.JSONField(default=dict)
```

- [ ] **Step 4: 运行测试并校验迁移一致性**

Run: `.\\.venv_service\\Scripts\\python.exe -m pytest service_tests\\test_v3_p2_ai_governance.py -k "models_capture_policy_scope" -q --basetemp=.pytest_tmp\\v3_p2_model_green`

Expected: PASS

- [ ] **Step 5: 提交阶段性变更**

```bash
git add scenario_service/models.py scenario_service/migrations/0009_aigovernancepolicyrecord_aisuggestiondecisionrecord_and_more.py service_tests/test_v3_p2_ai_governance.py
git commit -m "V3 P2：新增AI治理策略与责任链模型骨架"
```

### Task 2: P2 服务与接口流转

**Files:**
- Modify: `scenario_service/services.py`
- Modify: `scenario_service/serializers.py`
- Modify: `scenario_service/views.py`
- Modify: `scenario_service/urls.py`
- Test: `service_tests/test_v3_p2_ai_governance.py`

- [ ] **Step 1: 写失败测试，锁定建议创建/审批/拒绝/采纳/回退契约**

```python
def test_ai_governance_api_requires_manual_approval_before_adoption(service_test_token):
    client = APIClient()
    scenario_id = build_v3_p2_scenario(client=client, service_test_token=service_test_token)

    create_response = client.post(
        f"/api/v2/scenarios/{scenario_id}/suggestions/",
        {"requester": "qa-owner", "suggestion_type": "assertion_completion"},
        format="json",
    )
    suggestion_id = create_response.json()["data"][0]["suggestion_id"]
    adopt_response = client.post(
        f"/api/v2/scenarios/{scenario_id}/suggestions/{suggestion_id}/adopt/",
        {"actor": "qa-owner", "revision_comment": "直接采纳"},
        format="json",
    )

    assert create_response.status_code == 201
    assert adopt_response.status_code == 400
    assert adopt_response.json()["error"]["code"] == "ai_suggestion_not_approved"
```

- [ ] **Step 2: 运行失败测试，确认缺口落在状态机和接口**

Run: `.\\.venv_service\\Scripts\\python.exe -m pytest service_tests\\test_v3_p2_ai_governance.py -k "manual_approval_before_adoption" -q --basetemp=.pytest_tmp\\v3_p2_api_red`

Expected: FAIL，提示 `/adopt/` 接口或审批状态门禁不存在

- [ ] **Step 3: 写最小实现，接通策略、审批、拒绝、采纳和回退**

```python
def approve_suggestion(self, scenario_id: str, suggestion_id: str, actor: str, decision_comment: str = "") -> dict:
    suggestion = self._get_project_bound_suggestion(scenario_id=scenario_id, suggestion_id=suggestion_id)
    self._authorize_project_action(... required_permission="can_review" ...)
    suggestion.apply_status = "approved"
    suggestion.save(update_fields=["apply_status", "updated_at"])
    self._create_ai_decision_record(...)
    self._create_audit_log(... action_type="approve_ai_suggestion", action_result="succeeded" ...)
    return self._build_ai_suggestion_summary(suggestion)


def reject_suggestion(self, scenario_id: str, suggestion_id: str, actor: str, decision_comment: str = "") -> dict:
    ...


def adopt_suggestion(self, scenario_id: str, suggestion_id: str, actor: str, revision_comment: str = "") -> dict:
    if suggestion.apply_status != "approved":
        raise ScenarioServiceError(code="ai_suggestion_not_approved", message="AI 建议尚未审批通过，禁止采纳。", status_code=400)
    ...


def rollback_suggestion(self, scenario_id: str, suggestion_id: str, actor: str, rollback_comment: str = "") -> dict:
    ...
```

- [ ] **Step 4: 运行接口测试与定向回归**

Run: `.\\.venv_service\\Scripts\\python.exe -m pytest service_tests\\test_v3_p2_ai_governance.py -k "api or approval or rollback" -q --basetemp=.pytest_tmp\\v3_p2_api_green`

Expected: PASS

- [ ] **Step 5: 提交阶段性变更**

```bash
git add scenario_service/services.py scenario_service/serializers.py scenario_service/views.py scenario_service/urls.py service_tests/test_v3_p2_ai_governance.py
git commit -m "V3 P2：补齐AI建议审批拒绝采纳回退接口链路"
```

### Task 3: 未审批执行阻断与入口状态承接

**Files:**
- Modify: `scenario_service/services.py`
- Modify: `scenario_service/templates/scenario_service/workbench.html`
- Test: `service_tests/test_v3_p2_ai_governance.py`

- [ ] **Step 1: 写失败测试，锁定执行阻断和 UI 状态分层**

```python
def test_unapproved_ai_suggestion_cannot_trigger_execution(service_test_token, tmp_path):
    service = FunctionalCaseScenarioService()
    scenario = build_v3_p2_service_scenario(service=service, service_test_token=service_test_token)
    suggestions = service.create_suggestions(
        scenario_id=scenario.scenario_id,
        requester="qa-owner",
        suggestion_type="assertion_completion",
    )

    with pytest.raises(ScenarioServiceError) as error:
        service.request_execution(
            scenario_id=scenario.scenario_id,
            project_code=scenario.project.project_code,
            environment_code=scenario.environment.environment_code,
            workspace_root=tmp_path / "p2-unapproved",
            operator="qa-owner",
            trigger_source="ai_suggestion",
        )

    assert error.value.code == "ai_suggestion_approval_required"
```

- [ ] **Step 2: 运行失败测试，确认当前系统仍未阻断未审批 AI 链路**

Run: `.\\.venv_service\\Scripts\\python.exe -m pytest service_tests\\test_v3_p2_ai_governance.py -k "unapproved_ai_suggestion_cannot_trigger_execution or workbench" -q --basetemp=.pytest_tmp\\v3_p2_exec_ui_red`

Expected: FAIL，提示执行阻断码或工作台 AI 状态区域不存在

- [ ] **Step 3: 写最小实现，补齐执行阻断和工作台状态区**

```python
def _ensure_ai_suggestion_execution_ready(self, scenario: ScenarioRecord, trigger_source: str, actor_name: str | None) -> None:
    if trigger_source != "ai_suggestion":
        return
    pending_ai_suggestion = scenario.suggestions.filter(apply_status__in=["pending_approval", "approved"]).order_by("-updated_at", "-id").first()
    if pending_ai_suggestion is None:
        return
    if pending_ai_suggestion.apply_status != "adopted":
        ...
        raise ScenarioServiceError(
            code="ai_suggestion_approval_required",
            message="AI 建议未完成审批与采纳，禁止直接触发正式执行。",
            status_code=400,
        )
```

```html
<section class="result-box" data-testid="ai-governance-panel">
    <span class="field-label">AI 治理状态</span>
    <div id="ai-governance-summary"><div class="empty">等待加载 AI 治理摘要。</div></div>
</section>
```

- [ ] **Step 4: 运行 UI/执行定向测试**

Run: `.\\.venv_service\\Scripts\\python.exe -m pytest service_tests\\test_v3_p2_ai_governance.py -k "unapproved_ai_suggestion_cannot_trigger_execution or workbench_renders_ai_governance" -q --basetemp=.pytest_tmp\\v3_p2_exec_ui_green`

Expected: PASS

- [ ] **Step 5: 提交阶段性变更**

```bash
git add scenario_service/services.py scenario_service/templates/scenario_service/workbench.html service_tests/test_v3_p2_ai_governance.py
git commit -m "V3 P2：增加AI执行阻断与工作台治理状态承接"
```

### Task 4: P2 文档、验收与全量回归

**Files:**
- Modify: `README.md`
- Modify: `product_document/阶段文档/V3阶段工作计划文档.md`
- Modify: `product_document/测试文档/详细测试用例说明书(V3-P2).md`
- Modify: `product_document/测试文档/详细测试用例说明书(V3-总索引).md`
- Modify: `product_document/本地MySQL数据库信息.md`
- Modify: `task_plan.md`
- Modify: `findings.md`
- Modify: `progress.md`
- Create: `product_document/阶段文档/V3阶段P2独立验收报告.md`
- Test: `service_tests/test_v3_p2_ai_governance.py`

- [ ] **Step 1: 写或补齐验收级测试**

```python
def test_v3_p2_acceptance_closure_separates_delivered_governance_from_future_autonomy(...):
    ...
```

- [ ] **Step 2: 运行 P2 定向套件、全量回归和迁移检查**

Run: `.\\.venv_service\\Scripts\\python.exe -m pytest service_tests\\test_v3_p2_ai_governance.py -q --basetemp=.pytest_tmp\\v3_p2_targeted`
Expected: PASS

Run: `.\\.venv_service\\Scripts\\python.exe -m pytest service_tests -q --basetemp=.pytest_tmp\\v3_p2_service`
Expected: PASS

Run: `python -m pytest tests/platform_core -q --basetemp=.pytest_tmp\\v3_p2_platform_core`
Expected: PASS

Run: `python -m pytest tests -q --basetemp=.pytest_tmp\\v3_p2_root`
Expected: PASS

Run: `python -m pytest api_test/tests -q --basetemp=.pytest_tmp\\v3_p2_api_test`
Expected: PASS

Run: `.\\.venv_service\\Scripts\\python.exe manage.py makemigrations scenario_service --check --dry-run --settings=platform_service.test_settings`
Expected: `No changes detected in app 'scenario_service'`

- [ ] **Step 3: 同步阶段文档、测试文档、MySQL 文档和验收报告**

```markdown
- `P2` 已实现：治理策略对象、审批门禁、采纳/拒绝/回退责任链、未审批执行阻断、入口状态提示。
- `P2` 未实现：自动自愈、无人审批执行、自动修复自治编排。
```

- [ ] **Step 4: 复核 README 与本地记录一致性**

Run: `rg -n "P2|AI 治理|自动自愈|无人审批|回退" README.md product_document/阶段文档/V3阶段工作计划文档.md product_document/阶段文档/V3阶段P2独立验收报告.md product_document/测试文档/详细测试用例说明书(V3-P2).md`

Expected: 口径一致，明确区分已实现治理能力和保留自治能力

- [ ] **Step 5: 提交阶段性变更**

```bash
git add README.md product_document/阶段文档/V3阶段工作计划文档.md product_document/测试文档/详细测试用例说明书(V3-P2).md product_document/测试文档/详细测试用例说明书(V3-总索引).md product_document/本地MySQL数据库信息.md product_document/阶段文档/V3阶段P2独立验收报告.md task_plan.md findings.md progress.md
git commit -m "V3 P2：完成AI治理边界开发测试与独立验收归档"
```
