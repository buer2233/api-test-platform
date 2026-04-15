# V3 P0 多项目治理 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在现有 V2 `scenario_service` 基础上落地 V3 `P0` 的多项目与环境治理、默认项目迁移、执行隔离和浏览器端最小治理入口，并完成对应自动化测试与文档同步。

**Architecture:** 继续复用 Django + DRF + MySQL 的现有事实源，不新建平行服务。通过在 `scenario_service` 中增补治理对象模型、治理引导服务、治理查询接口和治理入口 UI，把 V2 的单项目场景事实源升级为 V3 `P0` 治理化事实源；执行隔离继续建立在现有 `ScenarioExecutionPipeline` 上，但工作区、结果回写和查询摘要必须显式携带项目 / 环境 / 场景集 / 版本上下文。

**Tech Stack:** Python 3.12、Django、DRF、pytest、pytest-django、SQLite 测试库、MySQL 迁移校验、现有 `scenario_service` 模板页面

---

## 文件结构

### 新建文件
- `service_tests/test_v3_p0_governance_flow.py`
  - 覆盖治理对象、默认项目迁移、治理查询、版本切换和迁移状态查询。
- `service_tests/test_v3_p0_isolation.py`
  - 覆盖项目级工作区隔离、环境绑定执行、导入导出边界和结果上下文隔离。
- `service_tests/test_v3_p0_workbench_ui.py`
  - 覆盖最小治理入口页面的项目切换、环境切换、场景集筛选、归属展示和结果隔离。
- `scenario_service/governance.py`
  - 承载默认项目迁移、治理上下文解析、版本激活和治理摘要构造，避免继续把 `services.py` 膨胀成单文件超大服务。

### 修改文件
- `scenario_service/models.py`
  - 新增项目、环境、场景集、基线版本、迁移记录模型，并给现有场景 / 执行记录补充治理外键和隔离字段。
- `scenario_service/services.py`
  - 接入治理引导、导入上下文解析、执行上下文校验、工作区隔离、导出路径隔离和结果摘要扩展。
- `scenario_service/serializers.py`
  - 新增治理查询、版本切换、迁移状态与执行上下文序列化器，并扩展导入 / 执行请求参数。
- `scenario_service/views.py`
  - 新增治理上下文、迁移状态、版本切换、导出接口，扩展现有导入 / 列表 / 执行视图。
- `scenario_service/urls.py`
  - 挂载治理上下文、迁移状态、版本切换和导出路由。
- `scenario_service/admin.py`
  - 注册新增治理模型，便于本地排障。
- `scenario_service/templates/scenario_service/workbench.html`
  - 从 V2 工作台升级为 P0 最小治理入口，增加项目 / 环境 / 场景集 / 版本区域与隔离展示。
- `platform_service/urls.py`
  - 如治理路由仍归 `scenario_service.urls`，则只需确认现有挂载可覆盖；若拆新前缀，再在此接入。
- `product_document/阶段文档/V3阶段工作计划文档.md`
  - 回填 P0 实现和测试进度。
- `product_document/测试文档/详细测试用例说明书(V3-P0).md`
  - 回填已执行用例和通过情况。
- `README.md`
  - 更新当前状态与验证入口。
- `task_plan.md`
- `findings.md`
- `progress.md`

### 迁移文件
- `scenario_service/migrations/0005_*.py`
  - 承载治理模型和治理字段的 schema 迁移。

---

## Task 1: 治理模型与默认项目迁移骨架

**Files:**
- Create: `service_tests/test_v3_p0_governance_flow.py`
- Create: `scenario_service/governance.py`
- Modify: `scenario_service/models.py`
- Modify: `scenario_service/admin.py`
- Modify: `scenario_service/services.py`

- [ ] **Step 1: 写第一批失败测试，锁定治理模型和默认项目迁移结果**

```python
@pytest.mark.django_db
def test_governance_bootstrap_creates_default_project_environment_set_and_version():
    service = FunctionalCaseScenarioService()

    payload = {
        "case_id": "fc-p0-001",
        "case_code": "query_user_profile",
        "case_name": "P0 默认项目样例",
        "steps": [{"step_name": "查询用户详情", "operation_id": "operation-get-user", "expected": {"status_code": 200}}],
    }
    scenario = service.import_functional_case(payload)

    detail = service.get_scenario_detail(scenario.scenario_id)

    assert detail["project"]["project_code"] == "default-project"
    assert detail["environment"]["environment_code"] == "default-env"
    assert detail["scenario_set"]["scenario_set_code"] == "default-scenario-set"
    assert detail["baseline_version"]["version_code"] == "baseline-v1"
```

- [ ] **Step 2: 运行失败测试，确认当前缺少治理对象和治理上下文**

Run: `.\.venv_service\Scripts\python.exe -m pytest service_tests\test_v3_p0_governance_flow.py -k "default_project" -q --ds=platform_service.test_settings --basetemp=.pytest_tmp\v3_p0_red_1`

Expected: FAIL，原因应为详情中不存在 `project/environment/scenario_set/baseline_version` 结构或相关模型未定义。

- [ ] **Step 3: 写最小实现，补齐治理模型和治理引导服务**

```python
class ProjectRecord(models.Model):
    project_id = models.CharField(max_length=128, unique=True)
    project_code = models.CharField(max_length=128, unique=True)
    project_name = models.CharField(max_length=255)
    lifecycle_status = models.CharField(max_length=32, default="active")
    is_archived = models.BooleanField(default=False)
    metadata = models.JSONField(default=dict)


class TestEnvironmentRecord(models.Model):
    environment_id = models.CharField(max_length=128, unique=True)
    project = models.ForeignKey(ProjectRecord, related_name="environments", on_delete=models.CASCADE)
    environment_code = models.CharField(max_length=128)
    environment_name = models.CharField(max_length=255)
    base_url = models.CharField(max_length=255, blank=True, default="")
    variable_set = models.JSONField(default=dict)
    isolation_key = models.CharField(max_length=128, blank=True, default="")
    is_default = models.BooleanField(default=False)


class ScenarioSetRecord(models.Model):
    scenario_set_id = models.CharField(max_length=128, unique=True)
    project = models.ForeignKey(ProjectRecord, related_name="scenario_sets", on_delete=models.CASCADE)
    scenario_set_code = models.CharField(max_length=128)
    scenario_set_name = models.CharField(max_length=255)
    tags = models.JSONField(default=list)
    is_archived = models.BooleanField(default=False)


class BaselineVersionRecord(models.Model):
    baseline_version_id = models.CharField(max_length=128, unique=True)
    scenario_set = models.ForeignKey(ScenarioSetRecord, related_name="baseline_versions", on_delete=models.CASCADE)
    version_code = models.CharField(max_length=128)
    version_name = models.CharField(max_length=255)
    is_frozen = models.BooleanField(default=False)
    is_active = models.BooleanField(default=False)
    metadata = models.JSONField(default=dict)
```

```python
class GovernanceBootstrapService:
    DEFAULT_PROJECT_CODE = "default-project"
    DEFAULT_ENVIRONMENT_CODE = "default-env"
    DEFAULT_SCENARIO_SET_CODE = "default-scenario-set"
    DEFAULT_BASELINE_VERSION_CODE = "baseline-v1"

    def ensure_bootstrap(self) -> dict:
        project, _ = ProjectRecord.objects.get_or_create(
            project_code=self.DEFAULT_PROJECT_CODE,
            defaults={"project_id": "project-default", "project_name": "默认项目"},
        )
        environment, _ = TestEnvironmentRecord.objects.get_or_create(
            project=project,
            environment_code=self.DEFAULT_ENVIRONMENT_CODE,
            defaults={"environment_id": "env-default", "environment_name": "默认环境", "is_default": True},
        )
        scenario_set, _ = ScenarioSetRecord.objects.get_or_create(
            project=project,
            scenario_set_code=self.DEFAULT_SCENARIO_SET_CODE,
            defaults={"scenario_set_id": "set-default", "scenario_set_name": "默认场景集"},
        )
        baseline_version, _ = BaselineVersionRecord.objects.get_or_create(
            scenario_set=scenario_set,
            version_code=self.DEFAULT_BASELINE_VERSION_CODE,
            defaults={"baseline_version_id": "baseline-default-v1", "version_name": "默认基线 V1", "is_frozen": True, "is_active": True},
        )
        # 后续继续补回填逻辑
        return {
            "project": project,
            "environment": environment,
            "scenario_set": scenario_set,
            "baseline_version": baseline_version,
        }
```

- [ ] **Step 4: 运行测试确认通过**

Run: `.\.venv_service\Scripts\python.exe -m pytest service_tests\test_v3_p0_governance_flow.py -k "default_project" -q --ds=platform_service.test_settings --basetemp=.pytest_tmp\v3_p0_green_1`

Expected: PASS

- [ ] **Step 5: 生成并检查迁移文件**

Run: `.\.venv_service\Scripts\python.exe manage.py makemigrations scenario_service --settings=platform_service.migration_settings`

Expected: 生成 `0005_*.py`

Run: `.\.venv_service\Scripts\python.exe manage.py makemigrations scenario_service --check --dry-run --settings=platform_service.migration_settings`

Expected: `No changes detected in app 'scenario_service'`

---

## Task 2: 治理上下文查询、迁移状态和版本切换接口

**Files:**
- Modify: `service_tests/test_v3_p0_governance_flow.py`
- Modify: `scenario_service/serializers.py`
- Modify: `scenario_service/views.py`
- Modify: `scenario_service/urls.py`
- Modify: `scenario_service/governance.py`
- Modify: `scenario_service/services.py`

- [ ] **Step 1: 写失败测试，锁定治理查询契约、迁移状态查询和版本切换**

```python
@pytest.mark.django_db
def test_governance_context_endpoint_returns_project_environment_set_and_active_version():
    client = APIClient()

    response = client.get("/api/v2/scenarios/governance/context/")

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["projects"][0]["project_code"] == "default-project"
    assert data["projects"][0]["environments"][0]["environment_code"] == "default-env"
    assert data["projects"][0]["scenario_sets"][0]["active_version"]["version_code"] == "baseline-v1"
```

```python
@pytest.mark.django_db
def test_baseline_version_activation_updates_active_version_context():
    client = APIClient()

    bootstrap = client.get("/api/v2/scenarios/governance/context/").json()["data"]
    project_code = bootstrap["projects"][0]["project_code"]
    scenario_set_code = bootstrap["projects"][0]["scenario_sets"][0]["scenario_set_code"]

    create_response = client.post(
        "/api/v2/scenarios/governance/baseline-versions/activate/",
        {
            "project_code": project_code,
            "scenario_set_code": scenario_set_code,
            "version_code": "baseline-v2",
            "version_name": "默认基线 V2",
        },
        format="json",
    )

    assert create_response.status_code == 200
    assert create_response.json()["data"]["active_version"]["version_code"] == "baseline-v2"
```

- [ ] **Step 2: 运行失败测试**

Run: `.\.venv_service\Scripts\python.exe -m pytest service_tests\test_v3_p0_governance_flow.py -k "governance_context or baseline_version_activation" -q --ds=platform_service.test_settings --basetemp=.pytest_tmp\v3_p0_red_2`

Expected: FAIL，原因应为接口、序列化器或版本切换逻辑缺失。

- [ ] **Step 3: 写最小实现**

```python
class GovernanceContextQueryView(APIView):
    def get(self, request):
        data = SCENARIO_SERVICE.get_governance_context()
        return Response({"success": True, "data": data})


class BaselineVersionActivateView(APIView):
    def post(self, request):
        serializer = BaselineVersionActivateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = SCENARIO_SERVICE.activate_baseline_version(**serializer.validated_data)
        return Response({"success": True, "data": data})
```

```python
urlpatterns += [
    path("governance/context/", GovernanceContextQueryView.as_view(), name="governance-context"),
    path("governance/migration-status/", GovernanceMigrationStatusView.as_view(), name="governance-migration-status"),
    path("governance/baseline-versions/activate/", BaselineVersionActivateView.as_view(), name="governance-baseline-activate"),
]
```

- [ ] **Step 4: 运行测试确认通过**

Run: `.\.venv_service\Scripts\python.exe -m pytest service_tests\test_v3_p0_governance_flow.py -k "governance_context or baseline_version_activation" -q --ds=platform_service.test_settings --basetemp=.pytest_tmp\v3_p0_green_2`

Expected: PASS

---

## Task 3: 治理感知导入、执行隔离和导出边界

**Files:**
- Create: `service_tests/test_v3_p0_isolation.py`
- Modify: `scenario_service/services.py`
- Modify: `scenario_service/serializers.py`
- Modify: `scenario_service/views.py`
- Modify: `scenario_service/governance.py`

- [ ] **Step 1: 写失败测试，锁定项目级工作区隔离、环境绑定执行和导入导出边界**

```python
@pytest.mark.django_db
def test_execution_workspace_and_report_paths_are_isolated_by_project_and_environment(tmp_path):
    service = FunctionalCaseScenarioService()

    scenario_a = service.import_functional_case({
        "project_code": "project-a",
        "environment_code": "env-a",
        "scenario_set_code": "set-a",
        "case_id": "fc-p0-iso-001",
        "case_code": "query_user_profile",
        "case_name": "项目 A 查询用户",
        "steps": [{"step_name": "查询用户详情", "operation_id": "operation-get-user", "request": {"path_params": {"user_id": 1}}, "expected": {"status_code": 200}}],
    })
    scenario_b = service.import_functional_case({
        "project_code": "project-b",
        "environment_code": "env-b",
        "scenario_set_code": "set-b",
        "case_id": "fc-p0-iso-001",
        "case_code": "query_user_profile",
        "case_name": "项目 B 查询用户",
        "steps": [{"step_name": "查询用户详情", "operation_id": "operation-get-user", "request": {"path_params": {"user_id": 1}}, "expected": {"status_code": 200}}],
    })

    service.review_scenario(scenario_a.scenario_id, "approved", "qa-owner", "通过")
    service.review_scenario(scenario_b.scenario_id, "approved", "qa-owner", "通过")

    execution_a = service.request_execution(scenario_a.scenario_id, project_code="project-a", environment_code="env-a")
    execution_b = service.request_execution(scenario_b.scenario_id, project_code="project-b", environment_code="env-b")

    assert execution_a.workspace_root != execution_b.workspace_root
    assert execution_a.project.project_code == "project-a"
    assert execution_b.project.project_code == "project-b"
```

```python
@pytest.mark.django_db
def test_export_bundle_path_is_scoped_by_project():
    client = APIClient()
    # 省略导入
    response = client.post(f"/api/v2/scenarios/{scenario_id}/export/", {"project_code": "project-a"}, format="json")
    assert response.status_code == 200
    assert "project-a" in response.json()["data"]["export_path"]
```

- [ ] **Step 2: 运行失败测试**

Run: `.\.venv_service\Scripts\python.exe -m pytest service_tests\test_v3_p0_isolation.py -q --ds=platform_service.test_settings --basetemp=.pytest_tmp\v3_p0_red_3`

Expected: FAIL，原因应为导入 / 执行请求不支持治理上下文、执行记录不带上下文或导出接口缺失。

- [ ] **Step 3: 写最小实现**

```python
def request_execution(self, scenario_id: str, project_code: str | None = None, environment_code: str | None = None, workspace_root: str | Path | None = None) -> ScenarioExecutionRecord:
    scenario = self._get_scenario(scenario_id=scenario_id)
    if not project_code or not environment_code:
        raise ScenarioServiceError(code="governance_context_required", message="执行必须显式指定项目和环境。", status_code=400)
    governance_context = self.governance_service.resolve_execution_context(
        scenario=scenario,
        project_code=project_code,
        environment_code=environment_code,
    )
    output_root = Path(workspace_root) if workspace_root else self.governance_service.build_workspace_root(governance_context, scenario)
    ...
```

```python
def export_scenario_bundle(self, scenario_id: str, project_code: str) -> dict:
    scenario = self._get_scenario(scenario_id)
    context = self.governance_service.resolve_project_context(scenario=scenario, project_code=project_code)
    export_path = self.governance_service.build_export_path(context, scenario)
    export_path.write_text(json.dumps(self.get_scenario_detail(scenario_id), ensure_ascii=False, indent=2), encoding="utf-8")
    return {"scenario_id": scenario.scenario_id, "project_code": context.project.project_code, "export_path": str(export_path)}
```

- [ ] **Step 4: 运行测试确认通过**

Run: `.\.venv_service\Scripts\python.exe -m pytest service_tests\test_v3_p0_isolation.py -q --ds=platform_service.test_settings --basetemp=.pytest_tmp\v3_p0_green_3`

Expected: PASS

---

## Task 4: 最小治理入口 UI

**Files:**
- Create: `service_tests/test_v3_p0_workbench_ui.py`
- Modify: `scenario_service/templates/scenario_service/workbench.html`
- Modify: `scenario_service/views.py`

- [ ] **Step 1: 写失败测试，锁定项目切换、环境切换、场景集筛选和归属展示**

```python
@pytest.mark.django_db
def test_p0_workbench_renders_governance_switchers_and_context_summary():
    client = APIClient()

    response = client.get("/ui/v2/workbench/")

    assert response.status_code == 200
    content = response.content.decode("utf-8")
    assert 'data-testid="project-switcher"' in content
    assert 'data-testid="environment-switcher"' in content
    assert 'data-testid="scenario-set-switcher"' in content
    assert 'data-testid="baseline-version-panel"' in content
    assert 'data-testid="governance-summary"' in content
```

- [ ] **Step 2: 运行失败测试**

Run: `.\.venv_service\Scripts\python.exe -m pytest service_tests\test_v3_p0_workbench_ui.py -q --ds=platform_service.test_settings --basetemp=.pytest_tmp\v3_p0_red_4`

Expected: FAIL，原因应为模板中不存在治理入口区域。

- [ ] **Step 3: 写最小实现**

```html
<section class="result-box" data-testid="governance-summary">
    <div data-testid="project-switcher"></div>
    <div data-testid="environment-switcher"></div>
    <div data-testid="scenario-set-switcher"></div>
    <div data-testid="baseline-version-panel"></div>
</section>
```

```javascript
const governance = await request("/api/v2/scenarios/governance/context/");
state.projects = governance.projects || [];
```

- [ ] **Step 4: 运行测试确认通过**

Run: `.\.venv_service\Scripts\python.exe -m pytest service_tests\test_v3_p0_workbench_ui.py -q --ds=platform_service.test_settings --basetemp=.pytest_tmp\v3_p0_green_4`

Expected: PASS

---

## Task 5: P0 验收回归、文档同步与最终验证

**Files:**
- Modify: `product_document/阶段文档/V3阶段工作计划文档.md`
- Modify: `product_document/测试文档/详细测试用例说明书(V3-P0).md`
- Modify: `README.md`
- Modify: `task_plan.md`
- Modify: `findings.md`
- Modify: `progress.md`

- [ ] **Step 1: 执行 P0 定向服务测试**

Run: `.\.venv_service\Scripts\python.exe -m pytest service_tests\test_v3_p0_governance_flow.py service_tests\test_v3_p0_isolation.py service_tests\test_v3_p0_workbench_ui.py -q --ds=platform_service.test_settings --basetemp=.pytest_tmp\v3_p0_acceptance_targeted`

Expected: PASS

- [ ] **Step 2: 执行服务层全量回归**

Run: `.\.venv_service\Scripts\python.exe -m pytest service_tests -q --ds=platform_service.test_settings --basetemp=.pytest_tmp\v3_p0_acceptance_service`

Expected: PASS

- [ ] **Step 3: 执行平台核心与旧底座回归**

Run: `python -m pytest tests/platform_core -q --basetemp=.pytest_tmp\v3_p0_platform_core`

Expected: PASS

Run: `python -m pytest tests -q --basetemp=.pytest_tmp\v3_p0_root`

Expected: PASS

Run: `python -m pytest api_test/tests -q --basetemp=.pytest_tmp\v3_p0_api_test`

Expected: PASS

- [ ] **Step 4: 执行迁移一致性检查**

Run: `.\.venv_service\Scripts\python.exe manage.py makemigrations scenario_service --check --dry-run --settings=platform_service.migration_settings`

Expected: `No changes detected in app 'scenario_service'`

- [ ] **Step 5: 同步文档和本地记录**

```markdown
- 在 `V3阶段工作计划文档.md` 中回填 `V3-IMP-001/002` 与 `V3-TEST-002` 的实际结果
- 在 `详细测试用例说明书(V3-P0).md` 中回填已执行用例和通过结论
- 在 `README.md` 中把当前状态切换为 “V3 P0 开发 / 测试已完成，待汇报”
```

- [ ] **Step 6: 汇总问题清单和后续修复项**

```markdown
- 记录实现过程中出现的设计折中、兼容性风险和暂未覆盖项
- 形成向用户汇报时要重点说明的“已完成 / 问题 / 下一步修正建议”
```

---

## 自检结论

### Spec 覆盖
- `P0-G1/G2`：由 Task 1 和 Task 2 覆盖治理对象、场景集、版本和查询契约。
- `P0-G3`：由 Task 3 覆盖项目级工作区隔离、环境绑定执行和导入导出边界。
- `P0-G4`：由 Task 1 和 Task 2 覆盖默认项目迁移、迁移状态查询和幂等性。
- `P0-G5`：由 Task 4 覆盖浏览器端最小治理入口。
- `P0` 验收：由 Task 5 覆盖定向回归、全量回归、迁移检查和文档同步。

### Placeholder 扫描
- 无 `TODO / TBD / implement later / fill in details` 占位内容。

### 类型一致性
- 治理对象统一使用 `ProjectRecord / TestEnvironmentRecord / ScenarioSetRecord / BaselineVersionRecord / GovernanceBootstrapService` 命名。
- 执行上下文统一使用 `project_code / environment_code / scenario_set_code / version_code`。

