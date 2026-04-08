# V2 第一实施子阶段：场景核心闭环 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在不一次性铺开完整 V2 的前提下，先交付“功能测试用例输入 -> 场景草稿对象 -> 审核状态流 -> 服务层最小摘要”的第一实施子阶段闭环。

**Architecture:** 保持 `platform_core` 作为当前阶段核心承载层，不提前引入完整 Django/DRF 工程骨架；先把 V2 的场景模型、功能用例草稿解析器、状态流规则和服务层最小能力做实，再为后续服务化持久化与入口承接提供稳定契约。实现上优先新增聚焦文件承载功能用例驱动逻辑，避免继续把 `parsers.py` 和 `services.py` 做成无边界大文件。

**Tech Stack:** Python、pytest、Pydantic、现有 `platform_core` 测试与服务层

---

### Task 1: 场景核心模型与状态对象

**Files:**
- Modify: `platform_core/models.py`
- Modify: `platform_core/__init__.py`
- Test: `tests/platform_core/test_models.py`

- [x] **Step 1: 写失败测试，锁定 V2 场景模型与状态对象**

```python
from datetime import datetime

from platform_core.models import (
    DependencyLink,
    ReviewRecord,
    ScenarioLifecycleStatus,
    ScenarioServiceSummary,
    ScenarioStep,
    TestScenario,
    VariableBinding,
)


def test_v2_models_capture_scenario_draft_fields():
    scenario = TestScenario(
        scenario_id="scenario-order-create",
        scenario_name="创建订单后查询订单详情",
        scenario_code="order_create_and_query",
        module_id="module-order",
        scenario_desc="功能测试用例驱动生成的场景草稿",
        source_ids=["source-functional-case-001"],
        priority="high",
        review_status="pending",
    )

    step = ScenarioStep(
        step_id="step-create-order",
        scenario_id=scenario.scenario_id,
        step_order=1,
        step_name="创建订单",
        operation_id="operation-create-order",
    )

    binding = VariableBinding(
        binding_id="binding-order-id",
        variable_name="order_id",
        source_operation_id="operation-create-order",
        source_field_path="data.id",
        target_operations=["operation-get-order"],
        target_scope="scenario",
    )

    dependency = DependencyLink(
        dependency_id="dependency-order-query",
        upstream_operation_id="operation-create-order",
        downstream_operation_id="operation-get-order",
        dependency_type="data_flow",
        binding_id=binding.binding_id,
        required=True,
        confidence_score=0.9,
        source="functional_case",
    )

    review = ReviewRecord(
        review_id="review-001",
        target_type="scenario",
        target_id=scenario.scenario_id,
        reviewer="qa-owner",
        review_status="pending",
        reviewed_at=datetime(2026, 4, 8, 20, 0, 0),
    )

    lifecycle = ScenarioLifecycleStatus(
        review_status="pending",
        execution_status="not_started",
        current_stage="draft",
    )

    summary = ScenarioServiceSummary(
        route_code="functional_case",
        service_stage="v2_phase1",
        scenario_id=scenario.scenario_id,
        scenario_code=scenario.scenario_code,
        scenario_name=scenario.scenario_name,
        review_status="pending",
        execution_status="not_started",
        issue_count=0,
    )

    assert step.step_order == 1
    assert binding.target_scope == "scenario"
    assert dependency.required is True
    assert review.review_status == "pending"
    assert lifecycle.current_stage == "draft"
    assert summary.execution_status == "not_started"
```

- [x] **Step 2: 运行定向测试，确认红灯**

Run: `python -m pytest tests/platform_core/test_models.py -k "v2_models or scenario_status or scenario_service" -v --basetemp .pytest_tmp/v2_phase1_models_red`
Expected: FAIL，并提示 `TestScenario`、`ScenarioLifecycleStatus` 或 `ScenarioServiceSummary` 尚未定义

- [x] **Step 3: 实现最小模型**

```python
class TestScenario(PlatformBaseModel):
    """场景资产或场景草稿模型。"""

    scenario_id: str
    scenario_name: str
    scenario_code: str
    module_id: str | None = None
    scenario_desc: str | None = None
    source_ids: list[str] = Field(default_factory=list)
    priority: Literal["high", "medium", "low"] = "medium"
    review_status: Literal["pending", "approved", "rejected", "revised"] = "pending"
    metadata: dict[str, Any] = Field(default_factory=dict)


class ScenarioLifecycleStatus(PlatformBaseModel):
    """场景生命周期状态对象。"""

    review_status: Literal["pending", "approved", "rejected", "revised"]
    execution_status: Literal["not_started", "running", "passed", "failed"] = "not_started"
    current_stage: Literal["draft", "reviewed", "confirmed", "executing", "finished"] = "draft"
```

- [x] **Step 4: 重跑定向测试，确认转绿**

Run: `python -m pytest tests/platform_core/test_models.py -k "v2_models or scenario_status or scenario_service" -v --basetemp .pytest_tmp/v2_phase1_models_green`
Expected: PASS

- [ ] **Step 5: 提交本任务**

```bash
git add platform_core/models.py platform_core/__init__.py tests/platform_core/test_models.py
git commit -m "V2阶段：补齐场景核心模型与状态摘要对象"
```

### Task 2: 功能测试用例草稿解析器

**Files:**
- Create: `platform_core/functional_cases.py`
- Modify: `platform_core/__init__.py`
- Test: `tests/platform_core/test_parser_inputs.py`

- [x] **Step 1: 写失败测试，锁定“功能用例 -> 场景草稿”解析行为**

```python
from platform_core.functional_cases import FunctionalCaseDraftParser


def test_functional_case_parser_builds_scenario_draft_from_json(tmp_path):
    source_path = tmp_path / "functional_case.json"
    source_path.write_text(
        """
        {
          "case_id": "fc-order-001",
          "case_name": "创建订单后查询订单详情",
          "priority": "high",
          "preconditions": ["已完成登录"],
          "steps": [
            {
              "step_name": "创建订单",
              "operation_id": "operation-create-order",
              "expected": {"status_code": 201, "extract": {"order_id": "data.id"}}
            },
            {
              "step_name": "查询订单详情",
              "operation_id": "operation-get-order",
              "uses": {"order_id": "$scenario.order_id"},
              "expected": {"status_code": 200}
            }
          ]
        }
        """.strip(),
        encoding="utf-8",
    )

    result = FunctionalCaseDraftParser().parse(source_path)

    assert result.scenario.scenario_code == "create_order_and_query_order_detail"
    assert [step.step_order for step in result.steps] == [1, 2]
    assert result.bindings[0].variable_name == "order_id"
    assert result.dependencies[0].upstream_operation_id == "operation-create-order"
    assert result.lifecycle.review_status == "pending"
    assert result.issues == []
```

- [x] **Step 2: 运行定向测试，确认红灯**

Run: `python -m pytest tests/platform_core/test_parser_inputs.py -k "functional_case_parser" -v --basetemp .pytest_tmp/v2_phase1_parser_red`
Expected: FAIL，并提示 `FunctionalCaseDraftParser` 或返回对象尚未定义

- [x] **Step 3: 实现最小解析器**

```python
class FunctionalCaseDraftParser:
    """把功能测试用例输入解析为 V2 场景草稿对象。"""

    def parse(self, source_path: str | Path) -> FunctionalCaseDraft:
        raw = json.loads(Path(source_path).read_text(encoding="utf-8"))
        scenario = TestScenario(...)
        steps = [ScenarioStep(...)]
        bindings = [VariableBinding(...)]
        dependencies = [DependencyLink(...)]
        lifecycle = ScenarioLifecycleStatus(
            review_status="pending",
            execution_status="not_started",
            current_stage="draft",
        )
        return FunctionalCaseDraft(
            scenario=scenario,
            steps=steps,
            bindings=bindings,
            dependencies=dependencies,
            review_records=[],
            lifecycle=lifecycle,
            issues=[],
        )
```

- [x] **Step 4: 重跑定向测试，确认转绿**

Run: `python -m pytest tests/platform_core/test_parser_inputs.py -k "functional_case_parser" -v --basetemp .pytest_tmp/v2_phase1_parser_green`
Expected: PASS

- [ ] **Step 5: 提交本任务**

```bash
git add platform_core/functional_cases.py platform_core/__init__.py tests/platform_core/test_parser_inputs.py
git commit -m "V2阶段：补齐功能测试用例到场景草稿的解析闭环"
```

### Task 3: 非法状态流转与服务层最小功能路线

**Files:**
- Modify: `platform_core/rules.py`
- Modify: `platform_core/services.py`
- Test: `tests/platform_core/test_services_and_assets.py`

- [x] **Step 1: 写失败测试，锁定状态门禁和服务层功能用例路线**

```python
import pytest

from platform_core.services import PlatformApplicationService


def test_platform_application_service_exposes_v2_phase1_functional_case_route(tmp_path):
    source_path = tmp_path / "functional_case.json"
    source_path.write_text(
        '{"case_id":"fc-001","case_name":"用户查询","steps":[{"step_name":"查询用户","operation_id":"operation-get-user","expected":{"status_code":200}}]}',
        encoding="utf-8",
    )

    service = PlatformApplicationService(project_root=tmp_path)

    routes = service.supported_routes()
    snapshot = service.describe_capabilities()
    draft = service.run_functional_case_pipeline(source_path=source_path, output_root=tmp_path / "workspace")

    assert routes["functional_case"] is True
    assert any(route.route_code == "functional_case" and route.enabled for route in snapshot.routes)
    assert draft.route_code == "functional_case"
    assert draft.review_status == "pending"
    assert draft.execution_status == "not_started"


def test_platform_application_service_blocks_invalid_scenario_status_transition():
    service = PlatformApplicationService()

    with pytest.raises(ValueError, match="非法状态流转"):
        service.validate_scenario_transition(
            current_review_status="rejected",
            target_review_status="approved",
            current_execution_status="not_started",
            target_execution_status="not_started",
        )
```

- [x] **Step 2: 运行定向测试，确认红灯**

Run: `python -m pytest tests/platform_core/test_services_and_assets.py -k "v2_phase1_functional_case_route or invalid_scenario_status_transition" -v --basetemp .pytest_tmp/v2_phase1_service_red`
Expected: FAIL，并提示 `functional_case` 仍为 `False` 或 `validate_scenario_transition` 未定义

- [x] **Step 3: 实现最小服务层与状态校验**

```python
class PlatformApplicationService:
    """V1/V2 过渡期应用服务层。"""

    def __init__(..., functional_case_parser: FunctionalCaseDraftParser | None = None, ...):
        self.functional_case_parser = functional_case_parser or FunctionalCaseDraftParser()

    @staticmethod
    def supported_routes() -> dict[str, bool]:
        return {
            "document": True,
            "functional_case": True,
            "traffic_capture": False,
        }

    def run_functional_case_pipeline(self, source_path: str | Path, output_root: str | Path) -> ScenarioServiceSummary:
        draft = self.functional_case_parser.parse(source_path=source_path)
        return ScenarioServiceSummary(
            route_code="functional_case",
            service_stage="v2_phase1",
            scenario_id=draft.scenario.scenario_id,
            scenario_code=draft.scenario.scenario_code,
            scenario_name=draft.scenario.scenario_name,
            review_status=draft.lifecycle.review_status,
            execution_status=draft.lifecycle.execution_status,
            issue_count=len(draft.issues),
        )

    @staticmethod
    def validate_scenario_transition(...):
        if current_review_status == "rejected" and target_review_status == "approved":
            raise ValueError("非法状态流转")
```

- [x] **Step 4: 重跑定向测试，确认转绿**

Run: `python -m pytest tests/platform_core/test_services_and_assets.py -k "v2_phase1_functional_case_route or invalid_scenario_status_transition" -v --basetemp .pytest_tmp/v2_phase1_service_green`
Expected: PASS

- [ ] **Step 5: 提交本任务**

```bash
git add platform_core/rules.py platform_core/services.py tests/platform_core/test_services_and_assets.py
git commit -m "V2阶段：开放功能用例路线并补齐状态流转门禁"
```

### Task 4: 文档与记录同步

**Files:**
- Modify: `README.md`
- Modify: `product_document/阶段文档/V2阶段工作计划文档.md`
- Modify: `task_plan.md`
- Modify: `findings.md`
- Modify: `progress.md`

- [x] **Step 1: 同步阶段文档与 README**

```markdown
- README 增加“V2 第一实施子阶段已开始”的说明，并记录当前已落地的功能用例草稿闭环范围。
- `V2阶段工作计划文档.md` 把 `V2-IMP-001`、`V2-IMP-002`、`V2-TEST-003`、`V2-TEST-004` 更新为“进行中”或“已完成（第一子阶段）”。
- 在“风险与阻塞记录”中补充第一子阶段暴露出的实现空白和后续建议。
```

- [x] **Step 2: 记录本轮发现与测试结果**

Run:
- `python -m pytest tests/platform_core/test_models.py tests/platform_core/test_parser_inputs.py tests/platform_core/test_services_and_assets.py -k "v2_phase1 or functional_case_parser or scenario" -v --basetemp .pytest_tmp/v2_phase1_targeted`
- `python -m pytest tests/platform_core -v --basetemp .pytest_tmp/v2_phase1_platform_core_full`

Expected:
- 定向 V2 新增测试全部通过
- `tests/platform_core` 现有测试不回退

- [ ] **Step 3: 提交本任务**

```bash
git add README.md product_document/阶段文档/V2阶段工作计划文档.md task_plan.md findings.md progress.md
git commit -m "V2阶段：同步第一实施子阶段进度与测试记录"
```

### Task 5: 阶段总结与后续接口规划

**Files:**
- Modify: `findings.md`
- Modify: `progress.md`

- [x] **Step 1: 记录尚未实现的下一批 V2 能力**

```markdown
1. 审核记录持久化与结构化修订接口仍未落地。
2. DRF 接口契约、结果查询契约与数据库事实源尚未进入本子阶段实现。
3. 抓包驱动草稿化接入与可用型入口仍待下一实施子阶段。
```

- [x] **Step 2: 汇总阶段阻塞与下一步建议**

```markdown
1. 下一子阶段优先把 `ScenarioServiceSummary` 扩成可持久化事实摘要，并补 `TC-V2-SVC-011`、`TC-V2-SVC-012` 的服务接口契约测试。
2. 再下一子阶段补审核修订链路和模板导出，避免服务对象与交互入口再次各自拼状态。
```

- [ ] **Step 3: 保持工作区可汇报**

Run: `git status --short`
Expected: 只包含本轮预期改动和本地未跟踪目录 `.idea/`、`.bytro`
