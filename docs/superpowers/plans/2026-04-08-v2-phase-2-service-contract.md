# V2 第二实施子阶段：服务化契约与持久化骨架 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 交付 V2 第二实施子阶段的最小 Django + DRF 服务化承载层，使功能测试用例草稿可以入库、查询、审核、触发执行请求并通过结果接口统一查询。

**Architecture:** 新增独立的 Django 服务层包，但继续复用 `platform_core` 的解析器、状态校验和场景摘要模型，不把业务规则复制到服务层。数据库运行目标保持 MySQL，自动化测试使用单独的 Django 测试设置切到 SQLite，以便在无外部数据库依赖的情况下验证正式 API 契约。

**Tech Stack:** Python、Django、Django REST Framework、PyMySQL、pytest、pytest-django、现有 `platform_core`

---

### Task 1: 服务层依赖与本地测试环境治理

**Files:**
- Modify: `.gitignore`
- Create: `requirements-platform-service.txt`
- Modify: `tests/test_dependency_governance.py`

- [ ] **Step 1: 写失败测试，锁定服务层依赖文件**

```python
def test_platform_service_requirements_use_fixed_versions_only():
    requirements_path = PROJECT_ROOT / "requirements-platform-service.txt"
    lines = [
        line.strip()
        for line in requirements_path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]

    assert lines == [
        "Django==5.2.9",
        "djangorestframework==3.16.1",
        "PyMySQL==1.0.2",
        "pytest==8.3.4",
        "pytest-django==4.11.1",
    ]
```

- [ ] **Step 2: 运行定向测试，确认红灯**

Run: `python -m pytest tests/test_dependency_governance.py -k "platform_service_requirements" -v --basetemp .pytest_tmp/v2_phase2_dependency_red`
Expected: FAIL，并提示 `requirements-platform-service.txt` 不存在

- [ ] **Step 3: 写最小实现与环境忽略规则**

```text
requirements-platform-service.txt
.venv_service/
```

- [ ] **Step 4: 重跑定向测试，确认转绿**

Run: `python -m pytest tests/test_dependency_governance.py -k "platform_service_requirements" -v --basetemp .pytest_tmp/v2_phase2_dependency_green`
Expected: PASS

- [ ] **Step 5: 创建本地虚拟环境并安装固定版本依赖**

Run:
- `python -m venv .venv_service`
- `.venv_service\Scripts\python.exe -m pip install --upgrade pip`
- `.venv_service\Scripts\python.exe -m pip install -r requirements-platform-service.txt`

Expected:
- 本地虚拟环境创建成功
- 安装版本与 `requirements-platform-service.txt` 一致

### Task 2: Django 服务骨架与持久化模型

**Files:**
- Create: `manage.py`
- Create: `platform_service/__init__.py`
- Create: `platform_service/settings.py`
- Create: `platform_service/test_settings.py`
- Create: `platform_service/urls.py`
- Create: `platform_service/asgi.py`
- Create: `platform_service/wsgi.py`
- Create: `scenario_service/__init__.py`
- Create: `scenario_service/apps.py`
- Create: `scenario_service/models.py`
- Create: `scenario_service/admin.py`
- Create: `scenario_service/migrations/__init__.py`
- Test: `service_tests/test_service_persistence.py`

- [ ] **Step 1: 写失败测试，锁定场景草稿持久化结构**

```python
import pytest

pytestmark = pytest.mark.django_db


def test_scenario_record_persists_functional_case_draft(scenario_import_service):
    payload = {
        "case_id": "fc-order-001",
        "case_code": "create_order_and_query_order_detail",
        "case_name": "创建订单后查询订单详情",
        "steps": [
            {
                "step_name": "创建订单",
                "operation_id": "operation-create-order",
                "expected": {"status_code": 201},
            }
        ],
    }

    scenario = scenario_import_service.import_functional_case(payload)

    assert scenario.scenario_id.startswith("scenario-")
    assert scenario.scenario_code == "create_order_and_query_order_detail"
    assert scenario.review_status == "pending"
    assert scenario.steps.count() == 1
```

- [ ] **Step 2: 运行定向测试，确认红灯**

Run: `.venv_service\Scripts\python.exe -m pytest service_tests/test_service_persistence.py -v --ds=platform_service.test_settings --basetemp .pytest_tmp/v2_phase2_persistence_red`
Expected: FAIL，并提示 Django 服务层文件或模型未定义

- [ ] **Step 3: 实现最小 Django 骨架与持久化模型**

```python
class ScenarioRecord(models.Model):
    """场景草稿与正式场景的持久化记录。"""

    scenario_id = models.CharField(max_length=128, unique=True)
    scenario_code = models.CharField(max_length=128)
    scenario_name = models.CharField(max_length=255)
    review_status = models.CharField(max_length=32, default="pending")
    execution_status = models.CharField(max_length=32, default="not_started")
    current_stage = models.CharField(max_length=32, default="draft")
    source_ids = models.JSONField(default=list)
    issues = models.JSONField(default=list)


class ScenarioStepRecord(models.Model):
    """场景步骤持久化记录。"""

    scenario = models.ForeignKey(ScenarioRecord, related_name="steps", on_delete=models.CASCADE)
    step_id = models.CharField(max_length=128, unique=True)
    step_order = models.PositiveIntegerField()
    step_name = models.CharField(max_length=255)
    operation_id = models.CharField(max_length=128, null=True, blank=True)
```

- [ ] **Step 4: 重跑定向测试，确认转绿**

Run: `.venv_service\Scripts\python.exe -m pytest service_tests/test_service_persistence.py -v --ds=platform_service.test_settings --basetemp .pytest_tmp/v2_phase2_persistence_green`
Expected: PASS

### Task 3: 复用 `platform_core` 的导入服务与 DRF 契约

**Files:**
- Modify: `platform_core/functional_cases.py`
- Create: `scenario_service/services.py`
- Create: `scenario_service/serializers.py`
- Create: `scenario_service/views.py`
- Create: `scenario_service/urls.py`
- Modify: `platform_service/urls.py`
- Test: `service_tests/test_drf_contract.py`

- [ ] **Step 1: 写失败测试，锁定导入、详情、审核、执行与结果查询接口**

```python
import pytest
from rest_framework.test import APIClient

pytestmark = pytest.mark.django_db


def test_drf_contract_covers_import_detail_review_execute_and_result():
    client = APIClient()
    payload = {
        "case_id": "fc-user-001",
        "case_code": "query_user_profile",
        "case_name": "查询用户详情",
        "steps": [
            {
                "step_name": "查询用户详情",
                "operation_id": "operation-get-user",
                "expected": {"status_code": 200},
            }
        ],
    }

    import_response = client.post("/api/v2/scenarios/import-functional-case/", payload, format="json")
    scenario_id = import_response.json()["data"]["scenario_id"]

    detail_response = client.get(f"/api/v2/scenarios/{scenario_id}/")
    review_response = client.post(
        f"/api/v2/scenarios/{scenario_id}/review/",
        {"review_status": "approved", "reviewer": "qa-owner", "review_comment": "通过"},
        format="json",
    )
    execute_response = client.post(f"/api/v2/scenarios/{scenario_id}/execute/", {}, format="json")
    result_response = client.get(f"/api/v2/scenarios/{scenario_id}/result/")

    assert import_response.status_code == 201
    assert detail_response.status_code == 200
    assert review_response.status_code == 200
    assert execute_response.status_code == 202
    assert result_response.status_code == 200
    assert result_response.json()["data"]["review_status"] == "approved"
```

- [ ] **Step 2: 运行定向测试，确认红灯**

Run: `.venv_service\Scripts\python.exe -m pytest service_tests/test_drf_contract.py -v --ds=platform_service.test_settings --basetemp .pytest_tmp/v2_phase2_drf_red`
Expected: FAIL，并提示接口路由或视图未定义

- [ ] **Step 3: 实现最小 API 契约**

```python
class FunctionalCaseImportView(APIView):
    """导入功能测试用例并创建场景草稿。"""

    def post(self, request):
        summary = scenario_draft_service.import_functional_case(request.data)
        return Response({"success": True, "data": summary}, status=status.HTTP_201_CREATED)


class ScenarioResultView(APIView):
    """返回统一的场景结果摘要。"""

    def get(self, request, scenario_id: str):
        result = scenario_draft_service.get_scenario_result(scenario_id=scenario_id)
        return Response({"success": True, "data": result})
```

- [ ] **Step 4: 重跑定向测试，确认转绿**

Run: `.venv_service\Scripts\python.exe -m pytest service_tests/test_drf_contract.py -v --ds=platform_service.test_settings --basetemp .pytest_tmp/v2_phase2_drf_green`
Expected: PASS

### Task 4: 阶段文档、测试记录与回归

**Files:**
- Modify: `README.md`
- Modify: `product_document/阶段文档/V2阶段工作计划文档.md`
- Modify: `product_document/测试文档/详细测试用例说明书(V2).md`
- Modify: `task_plan.md`
- Modify: `findings.md`
- Modify: `progress.md`

- [ ] **Step 1: 同步第二子阶段状态与测试命令**

```markdown
- README 记录 Django/DRF 服务层最小骨架已建立，以及单独虚拟环境测试命令。
- V2 阶段文档把 `V2-IMP-004`、`V2-TEST-006` 更新为“进行中/已完成第一批”。
- V2 测试文档记录 `TC-V2-SVC-001/002/003/004/005/009/011/012` 的首批实现状态。
```

- [ ] **Step 2: 执行第二子阶段回归**

Run:
- `.venv_service\Scripts\python.exe -m pytest service_tests -v --ds=platform_service.test_settings --basetemp .pytest_tmp/v2_phase2_service_tests`
- `python -m pytest tests/platform_core -v --basetemp .pytest_tmp/v2_phase2_platform_core_regression`
- `python -m pytest tests/test_dependency_governance.py -v --basetemp .pytest_tmp/v2_phase2_dependency_regression`

Expected:
- 新增服务层测试通过
- 既有 `platform_core` 和依赖治理测试不回退

- [ ] **Step 3: 提交本子阶段**

```bash
git add .gitignore requirements-platform-service.txt manage.py platform_service scenario_service service_tests README.md product_document/阶段文档/V2阶段工作计划文档.md product_document/测试文档/详细测试用例说明书(V2).md task_plan.md findings.md progress.md tests/test_dependency_governance.py
git commit -m "V2阶段：建立服务化契约与场景持久化骨架"
```
