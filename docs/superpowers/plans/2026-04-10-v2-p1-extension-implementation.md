# V2 P1 Extension Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在 V2 `P0` 主线已完成的基础上，补齐多来源追溯、抓包问题分类、执行历史与差异摘要、AI 建议治理以及入口一致性前置能力。

**Architecture:** 持续沿用现有 `Django + DRF + MySQL + pytest` 的增量式架构，不新增独立前端工程。先扩展 `scenario_service` 的持久化与查询事实层，再增强 `platform_core` 抓包解析和工作台入口，让 Web 与后续 Windows 入口都共用同一套服务契约与流程语言。

**Tech Stack:** Python 3.12、Django、Django REST Framework、MySQL、pytest、requests、Jinja2、现有 V2 工作台模板

---

## Scope Check

本计划覆盖的能力虽然横跨持久化、解析、服务、接口和入口，但都围绕同一条扩展主线：`场景事实层增强 -> 服务契约增强 -> AI 建议治理 -> 入口承接`。这些能力彼此强依赖，适合在同一份实现计划里按顺序完成，而不是拆成多个互不相干的子计划。

## File Structure

- Create: `D:\AI\api-test-platform\service_tests\test_traceability_history_flow.py`
  作用：验证来源追溯、执行历史独立沉淀和结果历史查询。
- Create: `D:\AI\api-test-platform\service_tests\test_scenario_query_contract.py`
  作用：验证列表筛选、详情增强、结果历史与差异摘要的 DRF 契约。
- Create: `D:\AI\api-test-platform\tests\platform_core\test_traffic_capture_traceability.py`
  作用：验证抓包问题分类、低置信标记和来源元数据生成。
- Create: `D:\AI\api-test-platform\scenario_service\suggestion_providers.py`
  作用：封装建议提供者抽象和规则型默认实现。
- Create: `D:\AI\api-test-platform\service_tests\test_scenario_suggestions.py`
  作用：验证建议创建、查询、采纳、阻断与修订关联。
- Create: `D:\AI\api-test-platform\scenario_service\migrations\0003_scenariosourcerecord_scenariosuggestionrecord_and_more.py`
  作用：落库来源追溯、建议记录和执行历史扩展字段。
- Modify: `D:\AI\api-test-platform\scenario_service\models.py`
  作用：扩展场景持久化模型，补来源追溯、建议记录和执行历史关联。
- Modify: `D:\AI\api-test-platform\scenario_service\services.py`
  作用：补来源持久化、筛选查询、历史摘要、差异构造、建议采纳和详情聚合。
- Modify: `D:\AI\api-test-platform\scenario_service\serializers.py`
  作用：增加列表筛选、建议创建与建议采纳的请求校验。
- Modify: `D:\AI\api-test-platform\scenario_service\views.py`
  作用：暴露增强后的列表、详情、结果、建议接口。
- Modify: `D:\AI\api-test-platform\scenario_service\urls.py`
  作用：注册建议相关 API 路由。
- Modify: `D:\AI\api-test-platform\platform_core\traffic_capture.py`
  作用：增强抓包问题分类和来源元数据。
- Modify: `D:\AI\api-test-platform\platform_core\models.py`
  作用：扩展 `ScenarioServiceSummary`，承接来源聚合、问题聚合和最近差异摘要。
- Modify: `D:\AI\api-test-platform\scenario_service\templates\scenario_service\workbench.html`
  作用：增加筛选、历史、差异和建议区域。
- Modify: `D:\AI\api-test-platform\service_tests\test_drf_contract.py`
  作用：保持已有 DRF 契约用例与扩展字段同步。
- Modify: `D:\AI\api-test-platform\service_tests\test_workbench_ui.py`
  作用：覆盖工作台筛选、历史、差异和建议区域。
- Modify: `D:\AI\api-test-platform\product_document\阶段文档\V2阶段工作计划文档.md`
  作用：同步扩展轮开发进度、测试进度和风险状态。
- Modify: `D:\AI\api-test-platform\product_document\测试文档\详细测试用例说明书(V2).md`
  作用：把 `P1` 新增实现与测试落地状态回填到测试文档。
- Modify: `D:\AI\api-test-platform\README.md`
  作用：同步工作台能力与服务契约增强后的当前仓库说明入口。

### Task 1: 来源追溯与执行历史持久化基础

**Files:**
- Create: `D:\AI\api-test-platform\service_tests\test_traceability_history_flow.py`
- Create: `D:\AI\api-test-platform\scenario_service\migrations\0003_scenariosourcerecord_scenariosuggestionrecord_and_more.py`
- Modify: `D:\AI\api-test-platform\scenario_service\models.py`
- Modify: `D:\AI\api-test-platform\scenario_service\services.py`
- Modify: `D:\AI\api-test-platform\platform_core\models.py`

- [x] **Step 1: Write the failing test**

```python
"""V2 P1 来源追溯与执行历史测试。"""

from __future__ import annotations

import pytest

from scenario_service.services import FunctionalCaseScenarioService


pytestmark = pytest.mark.django_db


def test_import_and_repeated_execution_preserve_source_traces_and_history(tmp_path):
    """场景导入和重复执行后应保留来源追溯与独立历史。"""
    service = FunctionalCaseScenarioService()
    scenario = service.import_functional_case(
        {
            "case_id": "fc-history-001",
            "case_code": "history_query_user_profile",
            "case_name": "重复执行历史场景",
            "steps": [
                {
                    "step_name": "查询用户详情",
                    "operation_id": "operation-get-user",
                    "request": {"path_params": {"user_id": 1}},
                    "expected": {"status_code": 200},
                }
            ],
        }
    )

    service.review_scenario(
        scenario_id=scenario.scenario_id,
        review_status="approved",
        reviewer="qa-owner",
        review_comment="通过",
    )
    service.request_execution(scenario.scenario_id, tmp_path / "run-1")
    service.request_execution(scenario.scenario_id, tmp_path / "run-2")

    detail = service.get_scenario_detail(scenario.scenario_id)
    result = service.get_scenario_result(scenario.scenario_id)

    assert detail["source_traces"][0]["source_type"] == "functional_case"
    assert detail["source_traces"][0]["entity_type"] == "scenario"
    assert len(result["execution_history"]) == 2
    assert result["execution_history"][0]["execution_id"] != result["execution_history"][1]["execution_id"]
    assert result["execution_history"][0]["trigger_source"] == "manual"
```

- [x] **Step 2: Run test to verify it fails**

Run: `.venv_service\Scripts\python.exe -m pytest service_tests/test_traceability_history_flow.py::test_import_and_repeated_execution_preserve_source_traces_and_history -q`
Expected: FAIL，报错点应落在 `source_traces`、`execution_history` 或新增字段缺失，证明现有持久化模型还不能承接这组事实。

- [x] **Step 3: Write minimal implementation**

```python
class ScenarioSourceRecord(models.Model):
    """场景来源追溯记录。"""

    scenario = models.ForeignKey(ScenarioRecord, related_name="sources", on_delete=models.CASCADE)
    entity_type = models.CharField(max_length=32, default="scenario")
    entity_id = models.CharField(max_length=128, blank=True, default="")
    source_type = models.CharField(max_length=32)
    source_ref = models.CharField(max_length=255)
    confidence = models.CharField(max_length=16, default="high")
    issue_tags = models.JSONField(default=list)
    metadata = models.JSONField(default=dict)


class ScenarioSuggestionRecord(models.Model):
    """场景建议记录。"""

    scenario = models.ForeignKey(ScenarioRecord, related_name="suggestions", on_delete=models.CASCADE)
    suggestion_id = models.CharField(max_length=128, unique=True)
    suggestion_type = models.CharField(max_length=64)
    target_type = models.CharField(max_length=32)
    target_id = models.CharField(max_length=128, blank=True, default="")
    baseline_revision_id = models.CharField(max_length=128, blank=True, default="")
    patch_payload = models.JSONField(default=dict)
    diff_summary = models.JSONField(default=dict)
    confidence = models.CharField(max_length=16, default="medium")
    apply_status = models.CharField(max_length=32, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class ScenarioExecutionRecord(models.Model):
    """场景执行请求与结果记录。"""

    scenario = models.ForeignKey(ScenarioRecord, related_name="executions", on_delete=models.CASCADE)
    execution_id = models.CharField(max_length=128, unique=True)
    execution_status = models.CharField(max_length=32, default="not_started")
    passed_count = models.PositiveIntegerField(default=0)
    failed_count = models.PositiveIntegerField(default=0)
    skipped_count = models.PositiveIntegerField(default=0)
    report_path = models.CharField(max_length=255, null=True, blank=True)
    failure_summary = models.TextField(null=True, blank=True)
    trigger_source = models.CharField(max_length=32, default="manual")
    based_on_revision_id = models.CharField(max_length=128, null=True, blank=True)
    based_on_suggestion_id = models.CharField(max_length=128, null=True, blank=True)
    change_summary = models.JSONField(default=dict)
    diff_summary = models.JSONField(default=dict)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)


class ScenarioServiceSummary(PlatformBaseModel):
    """场景路线对外暴露的稳定服务摘要。"""

    route_code: Literal["functional_case", "traffic_capture"]
    service_stage: str
    scenario_id: str
    scenario_code: str
    scenario_name: str
    review_status: Literal["pending", "approved", "rejected", "revised"]
    execution_status: Literal["not_started", "running", "passed", "failed"] = "not_started"
    step_count: int = 0
    issue_count: int = 0
    workspace_root: str | None = None
    report_path: str | None = None
    latest_execution_id: str | None = None
    passed_count: int = 0
    failed_count: int = 0
    skipped_count: int = 0
    source_summary: dict[str, int] = Field(default_factory=dict)
    issue_codes: list[str] = Field(default_factory=list)
    latest_diff_summary: dict[str, Any] = Field(default_factory=dict)


def _persist_source_traces(self, scenario: ScenarioRecord, draft: FunctionalCaseDraft) -> None:
    """把草稿来源事实写入来源追溯表。"""
    source_records = [
        ScenarioSourceRecord(
            scenario=scenario,
            entity_type="scenario",
            entity_id=scenario.scenario_id,
            source_type=draft.source_document.source_type,
            source_ref=draft.source_document.source_id,
            confidence="high",
            issue_tags=[issue.issue_code for issue in draft.issues],
            metadata={"source_name": draft.source_document.source_name},
        )
    ]
    for step in draft.steps:
        source_records.append(
            ScenarioSourceRecord(
                scenario=scenario,
                entity_type="step",
                entity_id=step.step_id,
                source_type=draft.source_document.source_type,
                source_ref=draft.source_document.source_id,
                confidence=step.metadata.get("capture_confidence", "high"),
                issue_tags=[],
                metadata=step.metadata,
            )
        )
    ScenarioSourceRecord.objects.bulk_create(source_records)
```

- [x] **Step 4: Run test to verify it passes**

Run: `.venv_service\Scripts\python.exe -m pytest service_tests/test_traceability_history_flow.py::test_import_and_repeated_execution_preserve_source_traces_and_history -q`
Expected: PASS，且 `ScenarioSourceRecord`、扩展后的 `ScenarioExecutionRecord` 和服务返回历史结构已经可用。

- [x] **Step 5: Commit**

```bash
git add service_tests/test_traceability_history_flow.py scenario_service/models.py scenario_service/services.py scenario_service/migrations/0003_scenariosourcerecord_scenariosuggestionrecord_and_more.py platform_core/models.py
git commit -m "V2开发：补齐场景来源追溯与执行历史持久化基础"
```

### Task 2: 列表筛选、详情增强与结果差异契约

**Files:**
- Create: `D:\AI\api-test-platform\service_tests\test_scenario_query_contract.py`
- Modify: `D:\AI\api-test-platform\scenario_service\serializers.py`
- Modify: `D:\AI\api-test-platform\scenario_service\services.py`
- Modify: `D:\AI\api-test-platform\scenario_service\views.py`
- Modify: `D:\AI\api-test-platform\service_tests\test_drf_contract.py`

- [x] **Step 1: Write the failing test**

```python
"""V2 P1 查询契约增强测试。"""

from __future__ import annotations

import pytest
from rest_framework.test import APIClient


pytestmark = pytest.mark.django_db


def test_list_and_result_contract_support_filters_history_and_diff(tmp_path):
    """列表和结果接口应支持筛选、历史和差异摘要。"""
    client = APIClient()
    payload = {
        "case_id": "fc-query-001",
        "case_code": "query_contract_user_profile",
        "case_name": "查询契约场景",
        "steps": [
            {
                "step_name": "查询用户详情",
                "operation_id": "operation-get-user",
                "request": {"path_params": {"user_id": 1}},
                "expected": {"status_code": 200},
            }
        ],
    }

    import_response = client.post("/api/v2/scenarios/import-functional-case/", payload, format="json")
    scenario_id = import_response.json()["data"]["scenario_id"]
    client.post(
        f"/api/v2/scenarios/{scenario_id}/review/",
        {"review_status": "approved", "reviewer": "qa-owner", "review_comment": "通过"},
        format="json",
    )
    client.post(f"/api/v2/scenarios/{scenario_id}/execute/", {"workspace_root": str(tmp_path / "run-1")}, format="json")
    client.post(f"/api/v2/scenarios/{scenario_id}/execute/", {"workspace_root": str(tmp_path / "run-2")}, format="json")

    list_response = client.get(
        "/api/v2/scenarios/",
        {"source_type": "functional_case", "review_status": "approved", "ordering": "updated_desc"},
    )
    result_response = client.get(f"/api/v2/scenarios/{scenario_id}/result/")

    assert list_response.status_code == 200
    assert list_response.json()["data"][0]["source_summary"]["functional_case"] == 1
    assert list_response.json()["data"][0]["issue_codes"] == []
    assert result_response.status_code == 200
    assert len(result_response.json()["data"]["execution_history"]) == 2
    assert "latest_diff_summary" in result_response.json()["data"]
    assert "status_changed" in result_response.json()["data"]["latest_diff_summary"]
```

- [x] **Step 2: Run test to verify it fails**

Run: `.venv_service\Scripts\python.exe -m pytest service_tests/test_scenario_query_contract.py::test_list_and_result_contract_support_filters_history_and_diff -q`
Expected: FAIL，报错应集中在列表接口不接受筛选条件，或结果接口尚未返回 `execution_history` / `latest_diff_summary`。

- [x] **Step 3: Write minimal implementation**

```python
class ScenarioListQuerySerializer(serializers.Serializer):
    """场景列表筛选查询参数校验器。"""

    source_type = serializers.ChoiceField(
        choices=["functional_case", "traffic_capture", "ai_suggestion"],
        required=False,
    )
    review_status = serializers.ChoiceField(
        choices=["pending", "approved", "rejected", "revised"],
        required=False,
    )
    execution_status = serializers.ChoiceField(
        choices=["not_started", "passed", "failed"],
        required=False,
    )
    issue_code = serializers.CharField(required=False, allow_blank=True)
    ordering = serializers.ChoiceField(
        choices=["updated_desc", "updated_asc"],
        required=False,
        default="updated_desc",
    )


def list_scenarios(self, filters: dict | None = None) -> list[dict]:
    """按筛选条件返回场景摘要列表。"""
    filters = filters or {}
    queryset = ScenarioRecord.objects.all().order_by("-updated_at", "-id")
    if filters.get("source_type"):
        queryset = queryset.filter(sources__source_type=filters["source_type"]).distinct()
    if filters.get("review_status"):
        queryset = queryset.filter(review_status=filters["review_status"])
    if filters.get("execution_status"):
        queryset = queryset.filter(execution_status=filters["execution_status"])
    if filters.get("issue_code"):
        queryset = queryset.filter(issue_codes__contains=[filters["issue_code"]])
    if filters.get("ordering") == "updated_asc":
        queryset = queryset.order_by("updated_at", "id")
    return [self.build_scenario_summary(item) for item in queryset]


def _build_execution_history(self, scenario: ScenarioRecord) -> list[dict]:
    """构造执行历史摘要。"""
    return [
        {
            "execution_id": execution.execution_id,
            "execution_status": execution.execution_status,
            "passed_count": execution.passed_count,
            "failed_count": execution.failed_count,
            "skipped_count": execution.skipped_count,
            "trigger_source": execution.trigger_source,
            "based_on_revision_id": execution.based_on_revision_id,
            "based_on_suggestion_id": execution.based_on_suggestion_id,
            "created_at": execution.created_at.isoformat(),
        }
        for execution in scenario.executions.all().order_by("-created_at", "-id")
    ]


def _build_diff_summary(self, current: ScenarioExecutionRecord, previous: ScenarioExecutionRecord | None) -> dict:
    """构造最近两次执行的轻量差异摘要。"""
    if previous is None:
        return {"status_changed": False, "failed_count_delta": 0, "passed_count_delta": 0}
    return {
        "status_changed": current.execution_status != previous.execution_status,
        "failed_count_delta": current.failed_count - previous.failed_count,
        "passed_count_delta": current.passed_count - previous.passed_count,
        "skipped_count_delta": current.skipped_count - previous.skipped_count,
        "failure_summary_changed": current.failure_summary != previous.failure_summary,
    }


class ScenarioListView(APIView):
    """返回可用型入口消费的场景摘要列表。"""

    def get(self, request):
        """处理场景列表查询。"""
        serializer = ScenarioListQuerySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        return Response({"success": True, "data": SCENARIO_SERVICE.list_scenarios(serializer.validated_data)})
```

- [x] **Step 4: Run test to verify it passes**

Run: `.venv_service\Scripts\python.exe -m pytest service_tests/test_scenario_query_contract.py::test_list_and_result_contract_support_filters_history_and_diff -q`
Expected: PASS，且列表、详情、结果契约已能稳定返回来源聚合、问题列表、执行历史和最近差异摘要。

- [x] **Step 5: Commit**

```bash
git add service_tests/test_scenario_query_contract.py scenario_service/serializers.py scenario_service/services.py scenario_service/views.py service_tests/test_drf_contract.py
git commit -m "V2开发：增强场景列表筛选与执行历史差异查询契约"
```

### Task 3: 抓包低置信问题分类与来源元数据

**Files:**
- Create: `D:\AI\api-test-platform\tests\platform_core\test_traffic_capture_traceability.py`
- Modify: `D:\AI\api-test-platform\platform_core\traffic_capture.py`
- Modify: `D:\AI\api-test-platform\scenario_service\services.py`

- [ ] **Step 1: Write the failing test**

```python
"""V2 P1 抓包问题分类与来源元数据测试。"""

from __future__ import annotations

import json

from platform_core.traffic_capture import TrafficCaptureDraftParser


def test_traffic_capture_parser_emits_quality_issues_and_source_metadata(tmp_path):
    """抓包解析器应输出细粒度问题标签和来源元数据。"""
    source_path = tmp_path / "trace.har.json"
    source_path.write_text(
        json.dumps(
            {
                "log": {
                    "entries": [
                        {
                            "startedDateTime": "2026-04-10T08:00:00.000Z",
                            "request": {"method": "GET", "url": "https://cdn.example.com/app.js"},
                            "response": {"status": 200, "content": {"mimeType": "application/javascript"}},
                        },
                        {
                            "startedDateTime": "2026-04-10T08:00:01.000Z",
                            "request": {"method": "POST", "url": "https://api.example.com/v1/login"},
                            "response": {
                                "status": 200,
                                "content": {"mimeType": "application/json", "text": "{\"token\":\"abc\"}"},
                            },
                        },
                        {
                            "startedDateTime": "2026-04-10T08:00:02.000Z",
                            "request": {"method": "GET", "url": "https://api.example.com/v1/users/1?a=1&b=2"},
                            "response": {
                                "status": 200,
                                "content": {"mimeType": "application/json", "text": "{\"id\":1,\"name\":\"A\"}"},
                            },
                        },
                        {
                            "startedDateTime": "2026-04-10T08:00:03.000Z",
                            "request": {"method": "GET", "url": "https://api.example.com/v1/users/1?b=2&a=1"},
                            "response": {
                                "status": 200,
                                "content": {"mimeType": "application/json", "text": "{\"id\":1,\"name\":\"A\"}"},
                            },
                        },
                    ]
                }
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    draft = TrafficCaptureDraftParser().parse(source_path)
    issue_codes = {issue.issue_code for issue in draft.issues}
    step_metadata = draft.steps[0].metadata

    assert "static_noise_filtered" in issue_codes
    assert "duplicate_request_group" in issue_codes
    assert "capture_operation_needs_review" in issue_codes
    assert step_metadata["source_traces"][0]["source_type"] == "traffic_capture"
    assert step_metadata["source_traces"][0]["confidence"] == "low"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv_service\Scripts\python.exe -m pytest tests/platform_core/test_traffic_capture_traceability.py::test_traffic_capture_parser_emits_quality_issues_and_source_metadata -q`
Expected: FAIL，报错应集中在 `static_noise_filtered`、`duplicate_request_group`、`source_traces` 等新标签和元数据尚未生成。

- [ ] **Step 3: Write minimal implementation**

```python
def parse_payload(
    self,
    raw_capture: dict[str, Any],
    source_name: str | None = None,
    source_path: Path | None = None,
) -> FunctionalCaseDraft:
    """直接把抓包请求体解析为场景草稿聚合对象。"""
    resolved_source_name = source_name or "traffic_capture"
    source = source_path or Path(f"{self._normalize_identifier(resolved_source_name)}.har.json")
    normalization = self._normalize_entries(raw_capture=raw_capture)
    normalized_entries = normalization["entries"]
    normalization_issues = normalization["issues"]
    source_document = self._build_source_document(
        source=source,
        source_name=resolved_source_name,
        normalized_entries=normalized_entries,
    )
    scenario = self._build_scenario(
        source_document=source_document,
        source_name=resolved_source_name,
        normalized_entries=normalized_entries,
    )

    issues = list(normalization_issues)
    for step_order, entry in enumerate(normalized_entries, start=1):
        source_trace = {
            "entity_type": "step",
            "source_type": "traffic_capture",
            "source_ref": entry["url"],
            "confidence": "low",
            "issue_tags": ["capture_operation_needs_review"],
        }
        raw_step = {
            "step_name": f'{entry["method"]} {entry["path_template"]}',
            "operation_id": self._build_operation_id(entry["method"], entry["path_template"]),
            "request": {
                "path_template": entry["path_template"],
                "path_params": dict(entry["path_params"]),
                "query_params": dict(entry["query_params"]),
                "headers": dict(entry["headers"]),
                "json": entry["json_body"],
            },
            "expected": {"status_code": entry["response_status"]},
            "uses": {},
            "capture_source": entry["url"],
            "capture_confidence": "low",
        }
        step = ScenarioStep(
            step_id=f"{scenario.scenario_id}-step-{step_order}",
            scenario_id=scenario.scenario_id,
            step_order=step_order,
            step_name=raw_step["step_name"],
            operation_id=raw_step["operation_id"],
            input_bindings=[],
            expected_bindings=list(raw_step["expected"].keys()),
            assertion_ids=[],
            retry_policy={},
            optional=False,
            metadata={
                "raw_step": raw_step,
                "capture_confidence": "low",
                "capture_quality": entry["quality_tags"],
                "source_traces": [source_trace],
            },
        )
        issues.append(
            FunctionalCaseIssue(
                issue_code="capture_operation_needs_review",
                issue_message=f"抓包步骤暂以候选操作标识接入，需人工确认接口绑定: {step.step_name}",
                severity="warning",
                step_id=step.step_id,
                step_order=step.step_order,
                metadata={"operation_id": step.operation_id, "quality_tags": entry["quality_tags"]},
            )
        )


def _normalize_entries(self, raw_capture: dict[str, Any]) -> dict[str, Any]:
    """过滤噪声、去重并生成稳定的请求序列。"""
    normalized_entries: list[dict[str, Any]] = []
    issues: list[FunctionalCaseIssue] = []
    seen_keys: set[str] = set()
    for entry in sorted(raw_capture.get("log", {}).get("entries") or [], key=lambda item: item.get("startedDateTime") or ""):
        normalized_entry = self._normalize_entry(entry)
        if not normalized_entry:
            continue
        if self._is_noise_entry(normalized_entry):
            issues.append(
                FunctionalCaseIssue(
                    issue_code="static_noise_filtered",
                    issue_message=f'已过滤噪声请求: {normalized_entry["method"]} {normalized_entry["url"]}',
                    severity="warning",
                    metadata={"source_url": normalized_entry["url"]},
                )
            )
            continue
        dedupe_key = json.dumps(
            {
                "method": normalized_entry["method"],
                "path_template": normalized_entry["path_template"],
                "query_params": normalized_entry["query_params"],
                "json_body": normalized_entry["json_body"],
            },
            ensure_ascii=False,
            sort_keys=True,
        )
        if dedupe_key in seen_keys:
            issues.append(
                FunctionalCaseIssue(
                    issue_code="duplicate_request_group",
                    issue_message=f'已折叠重复请求: {normalized_entry["method"]} {normalized_entry["path_template"]}',
                    severity="warning",
                    metadata={"source_url": normalized_entry["url"]},
                )
            )
            continue
        seen_keys.add(dedupe_key)
        normalized_entry["quality_tags"] = ["capture_operation_needs_review"]
        normalized_entries.append(normalized_entry)
    return {"entries": normalized_entries, "issues": issues}
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv_service\Scripts\python.exe -m pytest tests/platform_core/test_traffic_capture_traceability.py::test_traffic_capture_parser_emits_quality_issues_and_source_metadata -q`
Expected: PASS，且抓包解析结果已经能输出来源元数据、低置信标签和重复/噪声问题分类。

- [ ] **Step 5: Commit**

```bash
git add tests/platform_core/test_traffic_capture_traceability.py platform_core/traffic_capture.py scenario_service/services.py
git commit -m "V2开发：增强抓包低置信问题分类与来源元数据"
```

### Task 4: AI 建议对象与采纳治理链路

**Files:**
- Create: `D:\AI\api-test-platform\scenario_service\suggestion_providers.py`
- Create: `D:\AI\api-test-platform\service_tests\test_scenario_suggestions.py`
- Modify: `D:\AI\api-test-platform\scenario_service\models.py`
- Modify: `D:\AI\api-test-platform\scenario_service\serializers.py`
- Modify: `D:\AI\api-test-platform\scenario_service\services.py`
- Modify: `D:\AI\api-test-platform\scenario_service\views.py`
- Modify: `D:\AI\api-test-platform\scenario_service\urls.py`

- [ ] **Step 1: Write the failing test**

```python
"""V2 P1 场景建议治理测试。"""

from __future__ import annotations

import pytest
from rest_framework.test import APIClient

from scenario_service.models import ScenarioRevisionRecord


pytestmark = pytest.mark.django_db


def test_suggestion_creation_and_apply_flow_requires_revision_record():
    """AI 建议采纳后必须转成标准修订记录。"""
    client = APIClient()
    import_response = client.post(
        "/api/v2/scenarios/import-functional-case/",
        {
            "case_id": "fc-ai-001",
            "case_code": "ai_suggestion_user_profile",
            "case_name": "AI 建议场景",
            "steps": [
                {
                    "step_name": "查询用户详情",
                    "operation_id": "operation-get-user",
                    "expected": {"status_code": 200},
                }
            ],
        },
        format="json",
    )
    scenario_id = import_response.json()["data"]["scenario_id"]

    create_response = client.post(
        f"/api/v2/scenarios/{scenario_id}/suggestions/",
        {"requester": "qa-owner", "suggestion_type": "assertion_completion"},
        format="json",
    )
    suggestion_id = create_response.json()["data"][0]["suggestion_id"]

    apply_response = client.post(
        f"/api/v2/scenarios/{scenario_id}/suggestions/{suggestion_id}/apply/",
        {"reviser": "qa-owner", "revision_comment": "采纳建议"},
        format="json",
    )

    assert create_response.status_code == 201
    assert apply_response.status_code == 200
    assert apply_response.json()["data"]["apply_status"] == "applied"
    assert ScenarioRevisionRecord.objects.filter(scenario__scenario_id=scenario_id).count() == 1
    assert apply_response.json()["data"]["revision_id"].startswith("revision-")
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv_service\Scripts\python.exe -m pytest service_tests/test_scenario_suggestions.py::test_suggestion_creation_and_apply_flow_requires_revision_record -q`
Expected: FAIL，报错应集中在建议接口不存在、建议模型缺失，或采纳建议后没有生成 `ScenarioRevisionRecord`。

- [ ] **Step 3: Write minimal implementation**

```python
class BaseSuggestionProvider:
    """建议提供者抽象基类。"""

    def generate(self, scenario: ScenarioRecord, suggestion_type: str) -> list[dict]:
        """生成建议补丁。"""
        raise NotImplementedError


class RuleBasedSuggestionProvider(BaseSuggestionProvider):
    """规则型默认建议提供者。"""

    def generate(self, scenario: ScenarioRecord, suggestion_type: str) -> list[dict]:
        """基于当前问题和步骤结构生成建议。"""
        if suggestion_type == "assertion_completion":
            return [
                {
                    "target_type": "step",
                    "target_id": step.step_id,
                    "patch_payload": {"expected": {"status_code": 200}},
                    "diff_summary": {"added_expected_keys": ["status_code"]},
                }
                for step in scenario.steps.all()
                if "status_code" not in step.expected_bindings
            ]
        return []


class ScenarioSuggestionRequestSerializer(serializers.Serializer):
    """建议创建请求校验器。"""

    requester = serializers.CharField()
    suggestion_type = serializers.ChoiceField(
        choices=["assertion_completion", "low_confidence_repair", "step_patch"],
    )


class ScenarioSuggestionApplyRequestSerializer(serializers.Serializer):
    """建议采纳请求校验器。"""

    reviser = serializers.CharField()
    revision_comment = serializers.CharField(required=False, allow_blank=True)


@transaction.atomic
def create_suggestions(self, scenario_id: str, requester: str, suggestion_type: str) -> list[ScenarioSuggestionRecord]:
    """生成场景建议记录。"""
    scenario = self._get_scenario(scenario_id)
    payloads = self.suggestion_provider.generate(scenario, suggestion_type)
    records = [
        ScenarioSuggestionRecord.objects.create(
            scenario=scenario,
            suggestion_id=f"suggestion-{uuid4().hex[:12]}",
            suggestion_type=suggestion_type,
            target_type=payload["target_type"],
            target_id=payload["target_id"],
            baseline_revision_id=scenario.revisions.last().revision_id if scenario.revisions.exists() else "",
            patch_payload=payload["patch_payload"],
            diff_summary=payload["diff_summary"],
            confidence="medium",
            apply_status="pending",
        )
        for payload in payloads
    ]
    return records


@transaction.atomic
def apply_suggestion(
    self,
    scenario_id: str,
    suggestion_id: str,
    reviser: str,
    revision_comment: str | None = None,
) -> dict:
    """采纳建议并生成标准修订记录。"""
    scenario = self._get_scenario(scenario_id)
    suggestion = scenario.suggestions.get(suggestion_id=suggestion_id)
    if suggestion.apply_status == "applied":
        raise ScenarioServiceError("scenario_suggestion_already_applied", "该建议已采纳。", 400)
    patched = self.revise_scenario(
        scenario_id=scenario_id,
        reviser=reviser,
        revision_comment=revision_comment or "采纳建议",
        scenario_patch=suggestion.patch_payload,
    )
    latest_revision = patched.revisions.last()
    suggestion.apply_status = "applied"
    suggestion.save(update_fields=["apply_status", "updated_at"])
    return {
        "suggestion_id": suggestion.suggestion_id,
        "apply_status": suggestion.apply_status,
        "revision_id": latest_revision.revision_id,
    }
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv_service\Scripts\python.exe -m pytest service_tests/test_scenario_suggestions.py::test_suggestion_creation_and_apply_flow_requires_revision_record -q`
Expected: PASS，且建议创建、查询、采纳、转修订的治理链路已经建立。

- [ ] **Step 5: Commit**

```bash
git add scenario_service/suggestion_providers.py service_tests/test_scenario_suggestions.py scenario_service/models.py scenario_service/serializers.py scenario_service/services.py scenario_service/views.py scenario_service/urls.py
git commit -m "V2开发：接入场景建议对象与采纳转修订治理链路"
```

### Task 5: 工作台承接、文档同步与回归

**Files:**
- Modify: `D:\AI\api-test-platform\scenario_service\templates\scenario_service\workbench.html`
- Modify: `D:\AI\api-test-platform\service_tests\test_workbench_ui.py`
- Modify: `D:\AI\api-test-platform\product_document\阶段文档\V2阶段工作计划文档.md`
- Modify: `D:\AI\api-test-platform\product_document\测试文档\详细测试用例说明书(V2).md`
- Modify: `D:\AI\api-test-platform\README.md`

- [ ] **Step 1: Write the failing test**

```python
"""V2 P1 工作台增强测试。"""

from __future__ import annotations

import pytest
from rest_framework.test import APIClient


pytestmark = pytest.mark.django_db


def test_workbench_renders_filter_history_diff_and_suggestion_regions():
    """工作台应展示筛选、历史、差异和建议区域。"""
    client = APIClient()

    response = client.get("/ui/v2/workbench/")

    assert response.status_code == 200
    content = response.content.decode("utf-8")
    assert 'data-testid="scenario-filter-panel"' in content
    assert 'data-testid="execution-history-panel"' in content
    assert 'data-testid="diff-summary-panel"' in content
    assert 'data-testid="suggestion-panel"' in content
    assert "source_type" in content
    assert "issue_code" in content
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.venv_service\Scripts\python.exe -m pytest service_tests/test_workbench_ui.py::test_workbench_renders_filter_history_diff_and_suggestion_regions -q`
Expected: FAIL，因为当前工作台还没有筛选、历史、差异和建议区域。

- [ ] **Step 3: Write minimal implementation**

```html
<section class="result-box" data-testid="scenario-filter-panel">
    <span class="field-label">场景筛选</span>
    <div class="summary-grid">
        <div class="summary-cell">
            <span class="summary-key">来源类型</span>
            <input id="filter-source-type" name="source_type" placeholder="functional_case / traffic_capture">
        </div>
        <div class="summary-cell">
            <span class="summary-key">问题标签</span>
            <input id="filter-issue-code" name="issue_code" placeholder="capture_operation_needs_review">
        </div>
    </div>
</section>

<section class="result-box" data-testid="execution-history-panel">
    <span class="field-label">执行历史</span>
    <div id="execution-history-list"><div class="empty">等待加载历史记录。</div></div>
</section>

<section class="result-box" data-testid="diff-summary-panel">
    <span class="field-label">最近差异</span>
    <div id="diff-summary"><div class="empty">等待加载差异摘要。</div></div>
</section>

<section class="result-box" data-testid="suggestion-panel">
    <span class="field-label">建议与修订</span>
    <div class="button-row">
        <button class="button secondary" id="load-suggestions-button">查看 AI 建议</button>
    </div>
    <div id="suggestion-list"><div class="empty">等待加载建议记录。</div></div>
</section>
```

```markdown
| V2-IMP-007 | V2 P1 核心事实层与查询增强 | 已完成 | 已补齐来源追溯、执行历史、筛选查询、结果差异和建议治理的服务契约 | 2026-04-10 |
| V2-TEST-011 | V2 P1 扩展回归验证 | 已完成 | 已完成来源追溯、抓包问题分类、建议采纳链路、工作台增强与主线回归 | 2026-04-10 |

- AI 改写建议对比、修订留痕与重复执行历史沉淀：已完成并纳入本轮实现；
- 场景结果摘要模板、场景列表筛选和差异检查服务增强验证：已完成并通过自动化回归。
```

- [ ] **Step 4: Run test to verify it passes**

Run: `.venv_service\Scripts\python.exe -m pytest service_tests/test_workbench_ui.py -q && .venv_service\Scripts\python.exe -m pytest service_tests/test_drf_contract.py service_tests/test_scenario_query_contract.py service_tests/test_scenario_suggestions.py service_tests/test_traceability_history_flow.py tests/platform_core/test_traffic_capture_traceability.py -q`
Expected: PASS，且工作台结构、DRF 契约、建议治理、来源追溯和抓包质量分类均通过回归。

- [ ] **Step 5: Commit**

```bash
git add scenario_service/templates/scenario_service/workbench.html service_tests/test_workbench_ui.py product_document/阶段文档/V2阶段工作计划文档.md product_document/测试文档/详细测试用例说明书(V2).md README.md
git commit -m "V2开发：完成P1扩展入口承接并同步阶段文档与测试文档"
```

## Coverage Check

- `多来源追溯事实` -> Task 1
- `执行历史事实` -> Task 1、Task 2
- `列表筛选、结果摘要、历史查询、轻量差异检查` -> Task 2、Task 5
- `抓包低置信问题标记、复杂噪声分类和一致性检查` -> Task 3
- `AI 建议对象和建议采纳治理链路` -> Task 4
- `修订记录、执行记录与建议记录之间的关联追溯` -> Task 1、Task 4
- `Web / Windows 共用流程语言、服务契约和入口职责边界` -> Task 2、Task 5
- `文档同步与阶段记录回填` -> Task 5

## Notes

- 本计划默认继续遵循 `AGENTS.md`：所有新增方法补中文注释、所有代码变更用 `apply_patch`、所有实现与测试后同步更新相关文档。
- 本计划默认按小步 TDD 执行，每个任务完成后先跑定向测试，再跑受影响回归，再提交中文 commit。
- 本计划不包含 `git push`，推送应在整轮 P1 扩展开发与测试通过、文档同步完成、可向用户汇报阶段结果时执行。
