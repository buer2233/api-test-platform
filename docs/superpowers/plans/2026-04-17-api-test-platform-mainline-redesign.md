# API Test Platform Mainline Redesign Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将当前偏治理控制台的工作台，重构为以 `api_test` 为唯一资产落点的接口自动化平台，完成“模块级抓包过滤 -> 数据治理 -> 接口方法识别/复用/新增 -> 测试用例生成 -> pytest 门禁 -> allure 报告与失败重试”的最小闭环。

**Architecture:** 前端继续复用 Django 模板页，但将页面信息架构重构为三段式工作台。服务层新增抓包代理会话、过滤记录、接口方法注册扫描、`api_test` 资产生成与 `pytest/allure` 提交门禁能力。生成资产统一写入 `api_test/core/<project>/<model>/` 与 `api_test/tests/<project>/<model>/`，数据库只保存过程记录和治理记录。

**Tech Stack:** Python、Django、DRF、MySQL、pytest、requests、allure-pytest、Jinja2、Django 模板、PowerShell

---

## 文件结构映射

### 需要新增的文件
- `scenario_service/capture_proxy.py`
  - 负责模块级抓包代理会话启动、停止、前置 URL/IP 过滤和原始请求记录。
- `scenario_service/api_test_registry.py`
  - 负责扫描 `api_test/core/` 中现有接口方法资产，并按“HTTP 方法 + 完整 URL 路径”建立匹配索引。
- `scenario_service/api_test_generator.py`
  - 负责生成 `api_test/core/<project>/<model>/` 与 `api_test/tests/<project>/<model>/` 下的文件，并执行 `pytest` 门禁。
- `scenario_service/migrations/0010_captureproxyrecord_capturehttprecord_generationjobrecord.py`
  - 负责抓包会话、抓包 HTTP 记录、生成任务记录落库。
- `service_tests/test_mainline_workbench_ui.py`
  - 负责三段式工作台、主题切换、子模块默认测试用例列表等 UI/TDD 验证。
- `service_tests/test_capture_proxy_flow.py`
  - 负责代理端口启动/停止、过滤后只记录匹配请求、归属到模块/子模块。
- `service_tests/test_api_test_registry.py`
  - 负责接口方法匹配、复用、新增状态判定。
- `service_tests/test_api_test_generation.py`
  - 负责 `api_test` 目录落盘、allure 规范、pytest 门禁。

### 需要修改的文件
- `scenario_service/models.py`
  - 增加抓包会话、抓包记录、生成任务、主题偏好等结构化对象。
- `scenario_service/serializers.py`
  - 增加抓包会话请求、过滤请求、生成确认请求、主题切换请求序列化。
- `scenario_service/services.py`
  - 新增主工作台查询组装、治理候选生成、生成提交门禁等服务流程，并把大逻辑委托到新增模块。
- `scenario_service/views.py`
  - 暴露主工作台、抓包控制、治理候选、生成确认、执行结果查询接口。
- `scenario_service/urls.py`
  - 增加抓包控制、治理候选、生成确认、主题配置路由。
- `scenario_service/templates/scenario_service/workbench.html`
  - 重构为三段式主界面，简化为“左树 + 中间列表 + 右侧详情/执行”。
- `platform_service/urls.py`
  - 保持 `/ui/v2/workbench/` 与 `/ui/v3/workbench/` 指向新的主工作台模板。
- `api_test/requirements.txt`
  - 固定补入 `allure-pytest`，并遵守 2025 年及以前固定版本规则。
- `tests/test_dependency_governance.py`
  - 增加 `allure-pytest` 固定版本治理。
- `README.md`
  - 同步当前产品主线、目录落点和主工作台说明。
- `product_document/产品需求说明书(全局).md`
  - 回填“主入口是用例展示与执行，抓包为模块级新增入口”的主线说明。
- `product_document/架构设计/UI设计说明文档.md`
  - 更新三段式工作台、主题规则、模块级抓包入口说明。
- `product_document/架构设计/现有接口自动化测试框架改造方案.md`
  - 回填 `api_test/core/<project>/<model>/` 与 `api_test/tests/<project>/<model>/` 新结构。
- `product_document/测试文档/详细测试用例说明书(V1).md`
  - 增加 `allure` 强制规范与 `api_test` 目录映射口径。

### 需要重点参考的现有文件
- `api_test/core/base_api.py`
- `api_test/core/jsonplaceholder_api.py`
- `api_test/run_test.py`
- `api_test/tests/test_jsonplaceholder_api.py`
- `scenario_service/services.py`
- `scenario_service/templates/scenario_service/workbench.html`
- `service_tests/test_workbench_ui.py`

---

### Task 1: 重构主工作台为三段式信息架构

**Files:**
- Create: `service_tests/test_mainline_workbench_ui.py`
- Modify: `scenario_service/templates/scenario_service/workbench.html`
- Modify: `scenario_service/views.py`
- Modify: `scenario_service/services.py`

- [ ] **Step 1: 写出主工作台结构失败测试**

```python
from rest_framework.test import APIClient


def test_mainline_workbench_renders_three_column_layout_and_primary_regions():
    client = APIClient()

    response = client.get("/ui/v3/workbench/")

    assert response.status_code == 200
    content = response.content.decode("utf-8")
    assert 'data-testid="mainline-shell"' in content
    assert 'data-testid="left-tree-panel"' in content
    assert 'data-testid="middle-list-panel"' in content
    assert 'data-testid="right-detail-panel"' in content
    assert 'data-testid="capture-entry-actions"' in content
    assert 'data-testid="testcase-list-panel"' in content
    assert 'data-testid="detail-fixed-summary"' in content
    assert 'data-testid="detail-tab-method-chain"' in content
    assert 'data-testid="detail-tab-execution-history"' in content
    assert 'data-testid="detail-tab-allure-report"' in content
```

- [ ] **Step 2: 运行单测确认红灯**

Run: `.venv_service\Scripts\python.exe -m pytest service_tests/test_mainline_workbench_ui.py::test_mainline_workbench_renders_three_column_layout_and_primary_regions -q --ds=platform_service.test_settings --basetemp=.pytest_tmp/mainline_ui_red`

Expected: FAIL，提示缺少 `data-testid="mainline-shell"` 或仍渲染旧治理控制台区域。

- [ ] **Step 3: 写最小模板结构实现**

```html
<main class="mainline-shell" data-testid="mainline-shell">
  <aside class="left-tree-panel" data-testid="left-tree-panel"></aside>
  <section class="middle-list-panel" data-testid="middle-list-panel">
    <header class="capture-entry-actions" data-testid="capture-entry-actions"></header>
    <div class="testcase-list-panel" data-testid="testcase-list-panel"></div>
  </section>
  <section class="right-detail-panel" data-testid="right-detail-panel">
    <div class="detail-fixed-summary" data-testid="detail-fixed-summary"></div>
    <div class="detail-tabs">
      <button data-testid="detail-tab-method-chain">方法链</button>
      <button data-testid="detail-tab-execution-history">历史执行</button>
      <button data-testid="detail-tab-allure-report">测试报告</button>
    </div>
  </section>
</main>
```

- [ ] **Step 4: 运行单测确认绿灯**

Run: `.venv_service\Scripts\python.exe -m pytest service_tests/test_mainline_workbench_ui.py::test_mainline_workbench_renders_three_column_layout_and_primary_regions -q --ds=platform_service.test_settings --basetemp=.pytest_tmp/mainline_ui_green`

Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add service_tests/test_mainline_workbench_ui.py scenario_service/templates/scenario_service/workbench.html scenario_service/views.py scenario_service/services.py
git commit -m "feat: 重构主工作台为三段式接口自动化布局"
```

---

### Task 2: 固化左树与中间列表的默认交互

**Files:**
- Modify: `service_tests/test_mainline_workbench_ui.py`
- Modify: `scenario_service/templates/scenario_service/workbench.html`
- Modify: `scenario_service/services.py`

- [ ] **Step 1: 写出“子模块默认展示测试用例列表”的失败测试**

```python
from rest_framework.test import APIClient


def test_submodule_defaults_to_testcase_list_not_method_list(service_test_token: str):
    client = APIClient()

    response = client.get("/ui/v3/workbench/")

    assert response.status_code == 200
    content = response.content.decode("utf-8")
    assert 'data-default-view="testcase-list"' in content
    assert 'data-testid="testcase-list-panel"' in content
    assert 'data-testid="method-list-secondary-entry"' in content
```

- [ ] **Step 2: 运行单测确认红灯**

Run: `.venv_service\Scripts\python.exe -m pytest service_tests/test_mainline_workbench_ui.py::test_submodule_defaults_to_testcase_list_not_method_list -q --ds=platform_service.test_settings --basetemp=.pytest_tmp/submodule_default_red`

Expected: FAIL，缺少 `data-default-view="testcase-list"`。

- [ ] **Step 3: 写最小实现**

```html
<section class="middle-list-panel" data-testid="middle-list-panel" data-default-view="testcase-list">
  <div class="panel-toolbar">
    <button data-testid="capture-start-button">开始抓包</button>
    <button data-testid="capture-stop-button">停止抓包</button>
    <button data-testid="capture-import-button">导入抓包</button>
    <button data-testid="method-list-secondary-entry">查看接口方法</button>
    <button data-testid="create-testcase-button">新增测试用例</button>
  </div>
</section>
```

- [ ] **Step 4: 运行单测确认绿灯**

Run: `.venv_service\Scripts\python.exe -m pytest service_tests/test_mainline_workbench_ui.py::test_submodule_defaults_to_testcase_list_not_method_list -q --ds=platform_service.test_settings --basetemp=.pytest_tmp/submodule_default_green`

Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add service_tests/test_mainline_workbench_ui.py scenario_service/templates/scenario_service/workbench.html scenario_service/services.py
git commit -m "feat: 固化子模块默认测试用例列表交互"
```

---

### Task 3: 增加主题切换且仅切样式不切逻辑

**Files:**
- Modify: `service_tests/test_mainline_workbench_ui.py`
- Modify: `scenario_service/templates/scenario_service/workbench.html`
- Modify: `scenario_service/models.py`
- Modify: `scenario_service/serializers.py`
- Modify: `scenario_service/views.py`
- Modify: `scenario_service/urls.py`

- [ ] **Step 1: 写出主题切换失败测试**

```python
from rest_framework.test import APIClient


def test_theme_switcher_exposes_dark_light_gray_without_layout_variation():
    client = APIClient()

    response = client.get("/ui/v3/workbench/")

    assert response.status_code == 200
    content = response.content.decode("utf-8")
    assert 'data-testid="theme-switcher"' in content
    assert 'value="dark"' in content
    assert 'value="light"' in content
    assert 'value="gray"' in content
    assert 'data-layout-locked="true"' in content
```

- [ ] **Step 2: 运行单测确认红灯**

Run: `.venv_service\Scripts\python.exe -m pytest service_tests/test_mainline_workbench_ui.py::test_theme_switcher_exposes_dark_light_gray_without_layout_variation -q --ds=platform_service.test_settings --basetemp=.pytest_tmp/theme_switch_red`

Expected: FAIL

- [ ] **Step 3: 写最小主题切换实现**

```html
<div class="theme-switcher" data-testid="theme-switcher" data-layout-locked="true">
  <button data-theme-value="dark" value="dark">深色</button>
  <button data-theme-value="light" value="light">浅色</button>
  <button data-theme-value="gray" value="gray">灰色</button>
</div>
```

```python
class ThemePreferenceRecord(models.Model):
    """记录当前工作台主题偏好。"""

    theme_code = models.CharField(max_length=32, default="dark")
    created_at = models.DateTimeField(auto_now_add=True)
```

- [ ] **Step 4: 运行单测确认绿灯**

Run: `.venv_service\Scripts\python.exe -m pytest service_tests/test_mainline_workbench_ui.py::test_theme_switcher_exposes_dark_light_gray_without_layout_variation -q --ds=platform_service.test_settings --basetemp=.pytest_tmp/theme_switch_green`

Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add service_tests/test_mainline_workbench_ui.py scenario_service/templates/scenario_service/workbench.html scenario_service/models.py scenario_service/serializers.py scenario_service/views.py scenario_service/urls.py
git commit -m "feat: 增加三主题样式切换且锁定布局逻辑"
```

---

### Task 4: 增加模块级抓包代理会话与前置过滤

**Files:**
- Create: `scenario_service/capture_proxy.py`
- Modify: `scenario_service/models.py`
- Modify: `scenario_service/serializers.py`
- Modify: `scenario_service/services.py`
- Modify: `scenario_service/views.py`
- Modify: `scenario_service/urls.py`
- Create: `scenario_service/migrations/0010_captureproxyrecord_capturehttprecord_generationjobrecord.py`
- Create: `service_tests/test_capture_proxy_flow.py`

- [ ] **Step 1: 写出“前置过滤后只记录匹配请求”的失败测试**

```python
from scenario_service.capture_proxy import CaptureProxyFilter


def test_capture_proxy_filter_only_accepts_matching_url_or_ip():
    filter_rule = CaptureProxyFilter(url_prefix="https://weapp.mulinquan.cn", ip_address="")

    assert filter_rule.should_capture("https://weapp.mulinquan.cn/api/user/list", "10.0.0.8") is True
    assert filter_rule.should_capture("https://static.example.com/app.js", "10.0.0.8") is False
```

- [ ] **Step 2: 运行单测确认红灯**

Run: `.venv_service\Scripts\python.exe -m pytest service_tests/test_capture_proxy_flow.py::test_capture_proxy_filter_only_accepts_matching_url_or_ip -q --ds=platform_service.test_settings --basetemp=.pytest_tmp/capture_filter_red`

Expected: FAIL，提示 `scenario_service.capture_proxy` 不存在。

- [ ] **Step 3: 写最小过滤器实现**

```python
from dataclasses import dataclass


@dataclass
class CaptureProxyFilter:
    """根据 URL 前缀或 IP 过滤抓包请求。"""

    url_prefix: str = ""
    ip_address: str = ""

    def should_capture(self, request_url: str, remote_ip: str) -> bool:
        if self.url_prefix and request_url.startswith(self.url_prefix):
            return True
        if self.ip_address and remote_ip == self.ip_address:
            return True
        return False
```

- [ ] **Step 4: 运行单测确认绿灯**

Run: `.venv_service\Scripts\python.exe -m pytest service_tests/test_capture_proxy_flow.py::test_capture_proxy_filter_only_accepts_matching_url_or_ip -q --ds=platform_service.test_settings --basetemp=.pytest_tmp/capture_filter_green`

Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add scenario_service/capture_proxy.py service_tests/test_capture_proxy_flow.py
git commit -m "feat: 增加抓包代理前置过滤基础能力"
```

---

### Task 5: 增加抓包会话与记录落库

**Files:**
- Modify: `scenario_service/models.py`
- Modify: `scenario_service/serializers.py`
- Modify: `scenario_service/services.py`
- Create: `scenario_service/migrations/0010_captureproxyrecord_capturehttprecord_generationjobrecord.py`
- Modify: `service_tests/test_capture_proxy_flow.py`

- [ ] **Step 1: 写出抓包会话落库失败测试**

```python
from scenario_service.services import FunctionalCaseScenarioService


def test_start_capture_session_persists_filter_and_scope():
    service = FunctionalCaseScenarioService()

    summary = service.start_capture_session(
        project_code="ebuilder",
        module_code="app_center",
        submodule_code="eb_app",
        operator="qa-owner",
        filter_rule={"url_prefix": "https://weapp.mulinquan.cn", "ip_address": ""},
        listen_port=8899,
    )

    assert summary["project_code"] == "ebuilder"
    assert summary["module_code"] == "app_center"
    assert summary["submodule_code"] == "eb_app"
    assert summary["filter_rule"]["url_prefix"] == "https://weapp.mulinquan.cn"
```

- [ ] **Step 2: 运行单测确认红灯**

Run: `.venv_service\Scripts\python.exe -m pytest service_tests/test_capture_proxy_flow.py::test_start_capture_session_persists_filter_and_scope -q --ds=platform_service.test_settings --basetemp=.pytest_tmp/capture_session_red`

Expected: FAIL，提示 `start_capture_session` 未实现。

- [ ] **Step 3: 写最小模型与服务实现**

```python
class CaptureProxyRecord(models.Model):
    """记录模块级抓包会话。"""

    capture_session_id = models.CharField(max_length=64, unique=True)
    project_code = models.CharField(max_length=64)
    module_code = models.CharField(max_length=64)
    submodule_code = models.CharField(max_length=64)
    operator = models.CharField(max_length=64)
    listen_port = models.IntegerField()
    filter_url_prefix = models.CharField(max_length=255, blank=True, default="")
    filter_ip_address = models.CharField(max_length=64, blank=True, default="")
    status = models.CharField(max_length=32, default="running")
    started_at = models.DateTimeField(auto_now_add=True)
```

```python
def start_capture_session(self, project_code, module_code, submodule_code, operator, filter_rule, listen_port):
    record = CaptureProxyRecord.objects.create(
        capture_session_id=f"capture-{project_code}-{module_code}-{submodule_code}",
        project_code=project_code,
        module_code=module_code,
        submodule_code=submodule_code,
        operator=operator,
        listen_port=listen_port,
        filter_url_prefix=filter_rule.get("url_prefix", ""),
        filter_ip_address=filter_rule.get("ip_address", ""),
    )
    return {
        "capture_session_id": record.capture_session_id,
        "project_code": record.project_code,
        "module_code": record.module_code,
        "submodule_code": record.submodule_code,
        "filter_rule": {
            "url_prefix": record.filter_url_prefix,
            "ip_address": record.filter_ip_address,
        },
    }
```

- [ ] **Step 4: 运行单测确认绿灯**

Run: `.venv_service\Scripts\python.exe -m pytest service_tests/test_capture_proxy_flow.py::test_start_capture_session_persists_filter_and_scope -q --ds=platform_service.test_settings --basetemp=.pytest_tmp/capture_session_green`

Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add scenario_service/models.py scenario_service/serializers.py scenario_service/services.py scenario_service/migrations/0010_captureproxyrecord_capturehttprecord_generationjobrecord.py service_tests/test_capture_proxy_flow.py
git commit -m "feat: 落库抓包会话与过滤范围记录"
```

---

### Task 6: 把抓包记录治理为接口候选列表

**Files:**
- Modify: `scenario_service/capture_proxy.py`
- Modify: `scenario_service/services.py`
- Modify: `scenario_service/views.py`
- Modify: `scenario_service/urls.py`
- Modify: `service_tests/test_capture_proxy_flow.py`

- [ ] **Step 1: 写出治理候选列表失败测试**

```python
from scenario_service.services import FunctionalCaseScenarioService


def test_capture_records_are_grouped_into_candidate_operations():
    service = FunctionalCaseScenarioService()

    candidates = service.build_capture_candidates(
        capture_records=[
            {"method": "POST", "path": "/api/ebuilder/coms/component/enable", "url": "https://weapp.mulinquan.cn/api/ebuilder/coms/component/enable", "status_code": 200},
            {"method": "GET", "path": "/static/app.js", "url": "https://weapp.mulinquan.cn/static/app.js", "status_code": 200},
        ]
    )

    assert len(candidates) == 1
    assert candidates[0]["method"] == "POST"
    assert candidates[0]["path"] == "/api/ebuilder/coms/component/enable"
```

- [ ] **Step 2: 运行单测确认红灯**

Run: `.venv_service\Scripts\python.exe -m pytest service_tests/test_capture_proxy_flow.py::test_capture_records_are_grouped_into_candidate_operations -q --ds=platform_service.test_settings --basetemp=.pytest_tmp/candidate_build_red`

Expected: FAIL

- [ ] **Step 3: 写最小治理实现**

```python
def build_capture_candidates(self, capture_records):
    candidates = []
    for item in capture_records:
        if item["path"].startswith("/static/"):
            continue
        candidates.append(
            {
                "method": item["method"],
                "path": item["path"],
                "url": item["url"],
                "status_code": item["status_code"],
                "selection_state": "unselected",
            }
        )
    return candidates
```

- [ ] **Step 4: 运行单测确认绿灯**

Run: `.venv_service\Scripts\python.exe -m pytest service_tests/test_capture_proxy_flow.py::test_capture_records_are_grouped_into_candidate_operations -q --ds=platform_service.test_settings --basetemp=.pytest_tmp/candidate_build_green`

Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add scenario_service/capture_proxy.py scenario_service/services.py scenario_service/views.py scenario_service/urls.py service_tests/test_capture_proxy_flow.py
git commit -m "feat: 生成抓包治理后的接口候选列表"
```

---

### Task 7: 增加 `api_test` 接口方法注册扫描与匹配

**Files:**
- Create: `scenario_service/api_test_registry.py`
- Create: `service_tests/test_api_test_registry.py`
- Modify: `scenario_service/services.py`

- [ ] **Step 1: 写出“HTTP 方法 + 完整 URL 路径”匹配失败测试**

```python
from scenario_service.api_test_registry import ApiTestMethodRegistry


def test_registry_matches_existing_method_by_http_method_and_full_path():
    registry = ApiTestMethodRegistry()

    registry.register(
        {
            "module_path": "api_test/core/ebuilder/app_center/component_api.py",
            "method_name": "enable_component",
            "http_method": "POST",
            "full_path": "/api/ebuilder/coms/component/enable",
        }
    )

    matched = registry.match("POST", "/api/ebuilder/coms/component/enable")

    assert matched["method_name"] == "enable_component"
```

- [ ] **Step 2: 运行单测确认红灯**

Run: `.venv_service\Scripts\python.exe -m pytest service_tests/test_api_test_registry.py::test_registry_matches_existing_method_by_http_method_and_full_path -q --ds=platform_service.test_settings --basetemp=.pytest_tmp/registry_red`

Expected: FAIL

- [ ] **Step 3: 写最小注册扫描实现**

```python
class ApiTestMethodRegistry:
    """按 HTTP 方法和完整 URL 路径管理已有接口方法。"""

    def __init__(self):
        self._items = {}

    def register(self, item):
        key = (item["http_method"].upper(), item["full_path"])
        self._items[key] = item

    def match(self, http_method, full_path):
        return self._items.get((http_method.upper(), full_path))
```

- [ ] **Step 4: 运行单测确认绿灯**

Run: `.venv_service\Scripts\python.exe -m pytest service_tests/test_api_test_registry.py::test_registry_matches_existing_method_by_http_method_and_full_path -q --ds=platform_service.test_settings --basetemp=.pytest_tmp/registry_green`

Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add scenario_service/api_test_registry.py service_tests/test_api_test_registry.py scenario_service/services.py
git commit -m "feat: 增加api_test接口方法注册匹配能力"
```

---

### Task 8: 输出复用 / 补参 / 新增三种识别状态

**Files:**
- Modify: `service_tests/test_api_test_registry.py`
- Modify: `scenario_service/api_test_registry.py`
- Modify: `scenario_service/services.py`

- [ ] **Step 1: 写出识别状态失败测试**

```python
from scenario_service.services import FunctionalCaseScenarioService


def test_candidate_is_marked_as_reuse_or_create_by_registry_match():
    service = FunctionalCaseScenarioService()

    service.api_test_registry.register(
        {
            "module_path": "api_test/core/ebuilder/app_center/component_api.py",
            "method_name": "enable_component",
            "http_method": "POST",
            "full_path": "/api/ebuilder/coms/component/enable",
        }
    )

    matched = service.annotate_candidate_with_method_state(
        {"method": "POST", "path": "/api/ebuilder/coms/component/enable"}
    )
    created = service.annotate_candidate_with_method_state(
        {"method": "POST", "path": "/api/ebuilder/coms/component/archive"}
    )

    assert matched["method_state"] == "reused"
    assert matched["method_name"] == "enable_component"
    assert created["method_state"] == "create_required"
```

- [ ] **Step 2: 运行单测确认红灯**

Run: `.venv_service\Scripts\python.exe -m pytest service_tests/test_api_test_registry.py::test_candidate_is_marked_as_reuse_or_create_by_registry_match -q --ds=platform_service.test_settings --basetemp=.pytest_tmp/registry_state_red`

Expected: FAIL

- [ ] **Step 3: 写最小状态标注实现**

```python
def annotate_candidate_with_method_state(self, candidate):
    matched = self.api_test_registry.match(candidate["method"], candidate["path"])
    if matched:
        candidate["method_state"] = "reused"
        candidate["method_name"] = matched["method_name"]
        candidate["module_path"] = matched["module_path"]
        return candidate
    candidate["method_state"] = "create_required"
    candidate["method_name"] = ""
    candidate["module_path"] = ""
    return candidate
```

- [ ] **Step 4: 运行单测确认绿灯**

Run: `.venv_service\Scripts\python.exe -m pytest service_tests/test_api_test_registry.py::test_candidate_is_marked_as_reuse_or_create_by_registry_match -q --ds=platform_service.test_settings --basetemp=.pytest_tmp/registry_state_green`

Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add service_tests/test_api_test_registry.py scenario_service/api_test_registry.py scenario_service/services.py
git commit -m "feat: 标注接口候选复用或新增状态"
```

---

### Task 9: 增加 `api_test` 项目/模块目录生成规则

**Files:**
- Create: `service_tests/test_api_test_generation.py`
- Create: `scenario_service/api_test_generator.py`
- Modify: `scenario_service/services.py`

- [ ] **Step 1: 写出目录落点失败测试**

```python
from pathlib import Path

from scenario_service.api_test_generator import build_asset_paths


def test_build_asset_paths_targets_project_and_model_directories():
    result = build_asset_paths(project_code="ebuilder", model_code="app_center", case_code="create_app")

    assert result["core_dir"] == Path("api_test/core/ebuilder/app_center")
    assert result["test_dir"] == Path("api_test/tests/ebuilder/app_center")
    assert result["test_file"] == Path("api_test/tests/ebuilder/app_center/test_create_app.py")
```

- [ ] **Step 2: 运行单测确认红灯**

Run: `.venv_service\Scripts\python.exe -m pytest service_tests/test_api_test_generation.py::test_build_asset_paths_targets_project_and_model_directories -q --ds=platform_service.test_settings --basetemp=.pytest_tmp/asset_paths_red`

Expected: FAIL

- [ ] **Step 3: 写最小目录规则实现**

```python
from pathlib import Path


def build_asset_paths(project_code: str, model_code: str, case_code: str) -> dict:
    core_dir = Path("api_test/core") / project_code / model_code
    test_dir = Path("api_test/tests") / project_code / model_code
    return {
        "core_dir": core_dir,
        "test_dir": test_dir,
        "test_file": test_dir / f"test_{case_code}.py",
    }
```

- [ ] **Step 4: 运行单测确认绿灯**

Run: `.venv_service\Scripts\python.exe -m pytest service_tests/test_api_test_generation.py::test_build_asset_paths_targets_project_and_model_directories -q --ds=platform_service.test_settings --basetemp=.pytest_tmp/asset_paths_green`

Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add service_tests/test_api_test_generation.py scenario_service/api_test_generator.py scenario_service/services.py
git commit -m "feat: 固化api_test项目模块目录落点规则"
```

---

### Task 10: 按抓包顺序生成测试用例方法链

**Files:**
- Modify: `service_tests/test_api_test_generation.py`
- Modify: `scenario_service/api_test_generator.py`
- Modify: `scenario_service/services.py`

- [ ] **Step 1: 写出“抓包顺序就是调用顺序”的失败测试**

```python
from scenario_service.api_test_generator import build_testcase_steps


def test_build_testcase_steps_preserves_capture_order():
    steps = build_testcase_steps(
        [
            {"method_name": "login_app", "selection_order": 1},
            {"method_name": "get_app_detail", "selection_order": 2},
        ]
    )

    assert steps[0]["method_name"] == "login_app"
    assert steps[1]["method_name"] == "get_app_detail"
```

- [ ] **Step 2: 运行单测确认红灯**

Run: `.venv_service\Scripts\python.exe -m pytest service_tests/test_api_test_generation.py::test_build_testcase_steps_preserves_capture_order -q --ds=platform_service.test_settings --basetemp=.pytest_tmp/capture_order_red`

Expected: FAIL

- [ ] **Step 3: 写最小顺序实现**

```python
def build_testcase_steps(selected_candidates: list[dict]) -> list[dict]:
    ordered = sorted(selected_candidates, key=lambda item: item["selection_order"])
    return [
        {
            "step_index": index + 1,
            "method_name": item["method_name"],
        }
        for index, item in enumerate(ordered)
    ]
```

- [ ] **Step 4: 运行单测确认绿灯**

Run: `.venv_service\Scripts\python.exe -m pytest service_tests/test_api_test_generation.py::test_build_testcase_steps_preserves_capture_order -q --ds=platform_service.test_settings --basetemp=.pytest_tmp/capture_order_green`

Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add service_tests/test_api_test_generation.py scenario_service/api_test_generator.py scenario_service/services.py
git commit -m "feat: 生成测试用例时保持抓包接口顺序"
```

---

### Task 11: 生成符合 Allure 规范的测试用例代码

**Files:**
- Modify: `service_tests/test_api_test_generation.py`
- Modify: `scenario_service/api_test_generator.py`
- Modify: `api_test/requirements.txt`
- Modify: `tests/test_dependency_governance.py`

- [ ] **Step 1: 写出 Allure 规范失败测试**

```python
from scenario_service.api_test_generator import render_testcase_module


def test_render_testcase_module_contains_allure_feature_story_and_steps():
    code = render_testcase_module(
        project_code="ebuilder",
        model_code="app_center",
        feature_name="ebuilder-应用中心",
        story_name="应用中心-EB应用-新建应用",
        class_name="TestAppCenter",
        test_name="test_create_eb_app",
        ordered_steps=[{"step_index": 1, "method_name": "create_app"}],
    )

    assert '@allure.feature("ebuilder-应用中心")' in code
    assert '@allure.story("应用中心-EB应用-新建应用")' in code
    assert 'with allure.step("1.调用接口方法 create_app"):' in code
```

- [ ] **Step 2: 运行单测确认红灯**

Run: `.venv_service\Scripts\python.exe -m pytest service_tests/test_api_test_generation.py::test_render_testcase_module_contains_allure_feature_story_and_steps -q --ds=platform_service.test_settings --basetemp=.pytest_tmp/allure_code_red`

Expected: FAIL

- [ ] **Step 3: 写最小 Allure 代码生成实现**

```python
def render_testcase_module(project_code, model_code, feature_name, story_name, class_name, test_name, ordered_steps):
    step_blocks = []
    for item in ordered_steps:
        step_blocks.append(
            f'        with allure.step("{item["step_index"]}.调用接口方法 {item["method_name"]}"):\\n'
            f'            response_{item["step_index"]} = {item["method_name"]}()\\n'
            f'            assert response_{item["step_index"]} is not None\\n'
        )
    joined_steps = "".join(step_blocks)
    return (
        "import allure\\n\\n"
        f"@allure.feature(\\"{feature_name}\\")\\n"
        f"class {class_name}:\\n"
        f"    @allure.story(\\"{story_name}\\")\\n"
        f"    def {test_name}(self):\\n"
        f"{joined_steps}"
    )
```

- [ ] **Step 4: 运行单测确认绿灯**

Run: `.venv_service\Scripts\python.exe -m pytest service_tests/test_api_test_generation.py::test_render_testcase_module_contains_allure_feature_story_and_steps -q --ds=platform_service.test_settings --basetemp=.pytest_tmp/allure_code_green`

Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add service_tests/test_api_test_generation.py scenario_service/api_test_generator.py api_test/requirements.txt tests/test_dependency_governance.py
git commit -m "feat: 生成符合allure规范的接口自动化测试用例"
```

---

### Task 12: 落盘接口方法与测试用例文件

**Files:**
- Modify: `service_tests/test_api_test_generation.py`
- Modify: `scenario_service/api_test_generator.py`
- Modify: `scenario_service/services.py`

- [ ] **Step 1: 写出落盘失败测试**

```python
from pathlib import Path

from scenario_service.api_test_generator import write_generated_assets


def test_write_generated_assets_creates_core_and_test_files(tmp_path: Path):
    result = write_generated_assets(
        workspace_root=tmp_path,
        project_code="ebuilder",
        model_code="app_center",
        core_filename="component_api.py",
        core_code="def enable_component():\\n    return {}\\n",
        test_case_code="class TestAppCenter:\\n    pass\\n",
        case_code="create_app",
    )

    assert (tmp_path / "api_test/core/ebuilder/app_center/component_api.py").exists()
    assert (tmp_path / "api_test/tests/ebuilder/app_center/test_create_app.py").exists()
    assert result["project_code"] == "ebuilder"
```

- [ ] **Step 2: 运行单测确认红灯**

Run: `.venv_service\Scripts\python.exe -m pytest service_tests/test_api_test_generation.py::test_write_generated_assets_creates_core_and_test_files -q --ds=platform_service.test_settings --basetemp=.pytest_tmp/write_assets_red`

Expected: FAIL

- [ ] **Step 3: 写最小落盘实现**

```python
def write_generated_assets(workspace_root, project_code, model_code, core_filename, core_code, test_case_code, case_code):
    base = Path(workspace_root)
    paths = build_asset_paths(project_code=project_code, model_code=model_code, case_code=case_code)
    core_dir = base / paths["core_dir"]
    test_dir = base / paths["test_dir"]
    core_dir.mkdir(parents=True, exist_ok=True)
    test_dir.mkdir(parents=True, exist_ok=True)
    core_path = core_dir / core_filename
    test_path = base / paths["test_file"]
    core_path.write_text(core_code, encoding="utf-8")
    test_path.write_text(test_case_code, encoding="utf-8")
    return {"project_code": project_code, "model_code": model_code, "core_path": str(core_path), "test_path": str(test_path)}
```

- [ ] **Step 4: 运行单测确认绿灯**

Run: `.venv_service\Scripts\python.exe -m pytest service_tests/test_api_test_generation.py::test_write_generated_assets_creates_core_and_test_files -q --ds=platform_service.test_settings --basetemp=.pytest_tmp/write_assets_green`

Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add service_tests/test_api_test_generation.py scenario_service/api_test_generator.py scenario_service/services.py
git commit -m "feat: 生成并落盘api_test核心资产文件"
```

---

### Task 13: 增加 pytest 门禁与生成任务记录

**Files:**
- Modify: `scenario_service/models.py`
- Modify: `scenario_service/services.py`
- Modify: `scenario_service/api_test_generator.py`
- Modify: `service_tests/test_api_test_generation.py`

- [ ] **Step 1: 写出 pytest 门禁失败测试**

```python
from scenario_service.api_test_generator import evaluate_generation_gate


def test_generation_gate_blocks_submission_when_pytest_fails():
    result = evaluate_generation_gate({"pytest_exit_code": 1, "pytest_status": "failed"})

    assert result["submission_allowed"] is False
    assert result["status"] == "blocked"
```

- [ ] **Step 2: 运行单测确认红灯**

Run: `.venv_service\Scripts\python.exe -m pytest service_tests/test_api_test_generation.py::test_generation_gate_blocks_submission_when_pytest_fails -q --ds=platform_service.test_settings --basetemp=.pytest_tmp/pytest_gate_red`

Expected: FAIL

- [ ] **Step 3: 写最小门禁实现**

```python
def evaluate_generation_gate(pytest_summary: dict) -> dict:
    if pytest_summary["pytest_exit_code"] != 0:
        return {"submission_allowed": False, "status": "blocked"}
    return {"submission_allowed": True, "status": "ready_for_review"}
```

```python
class GenerationJobRecord(models.Model):
    """记录接口方法和测试用例生成任务。"""

    generation_job_id = models.CharField(max_length=64, unique=True)
    project_code = models.CharField(max_length=64)
    model_code = models.CharField(max_length=64)
    case_code = models.CharField(max_length=128)
    pytest_exit_code = models.IntegerField(default=-1)
    pytest_status = models.CharField(max_length=32, default="pending")
    submission_status = models.CharField(max_length=32, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)
```

- [ ] **Step 4: 运行单测确认绿灯**

Run: `.venv_service\Scripts\python.exe -m pytest service_tests/test_api_test_generation.py::test_generation_gate_blocks_submission_when_pytest_fails -q --ds=platform_service.test_settings --basetemp=.pytest_tmp/pytest_gate_green`

Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add scenario_service/models.py scenario_service/services.py scenario_service/api_test_generator.py service_tests/test_api_test_generation.py
git commit -m "feat: 增加pytest门禁和生成任务状态记录"
```

---

### Task 14: 接通工作台的生成确认与提交接口

**Files:**
- Modify: `scenario_service/serializers.py`
- Modify: `scenario_service/views.py`
- Modify: `scenario_service/urls.py`
- Modify: `scenario_service/services.py`
- Modify: `scenario_service/templates/scenario_service/workbench.html`
- Modify: `service_tests/test_mainline_workbench_ui.py`
- Modify: `service_tests/test_api_test_generation.py`

- [ ] **Step 1: 写出生成确认接口失败测试**

```python
from rest_framework.test import APIClient


def test_generation_confirmation_endpoint_returns_pytest_gate_summary():
    client = APIClient()

    response = client.post(
        "/api/v2/scenarios/generation/confirm/",
        {
            "project_code": "ebuilder",
            "model_code": "app_center",
            "case_code": "create_app",
            "selected_candidate_ids": ["candidate-1"],
        },
        format="json",
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    assert "submission_allowed" in payload["data"]
    assert "pytest_status" in payload["data"]
```

- [ ] **Step 2: 运行单测确认红灯**

Run: `.venv_service\Scripts\python.exe -m pytest service_tests/test_api_test_generation.py::test_generation_confirmation_endpoint_returns_pytest_gate_summary -q --ds=platform_service.test_settings --basetemp=.pytest_tmp/generation_confirm_red`

Expected: FAIL，提示路由不存在。

- [ ] **Step 3: 写最小接口实现**

```python
class GenerationConfirmRequestSerializer(serializers.Serializer):
    project_code = serializers.CharField()
    model_code = serializers.CharField()
    case_code = serializers.CharField()
    selected_candidate_ids = serializers.ListField(child=serializers.CharField(), min_length=1)
```

```python
class ScenarioGenerationConfirmView(APIView):
    def post(self, request):
        serializer = GenerationConfirmRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = SCENARIO_SERVICE.confirm_generation_job(**serializer.validated_data)
        return Response({"success": True, "data": data})
```

```python
path("generation/confirm/", ScenarioGenerationConfirmView.as_view(), name="scenario-generation-confirm"),
```

- [ ] **Step 4: 运行单测确认绿灯**

Run: `.venv_service\Scripts\python.exe -m pytest service_tests/test_api_test_generation.py::test_generation_confirmation_endpoint_returns_pytest_gate_summary -q --ds=platform_service.test_settings --basetemp=.pytest_tmp/generation_confirm_green`

Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add scenario_service/serializers.py scenario_service/views.py scenario_service/urls.py scenario_service/services.py scenario_service/templates/scenario_service/workbench.html service_tests/test_mainline_workbench_ui.py service_tests/test_api_test_generation.py
git commit -m "feat: 接通生成确认与提交门禁接口"
```

---

### Task 15: 增加 Allure 报告入口与失败重试链路

**Files:**
- Modify: `scenario_service/services.py`
- Modify: `scenario_service/views.py`
- Modify: `scenario_service/templates/scenario_service/workbench.html`
- Modify: `service_tests/test_mainline_workbench_ui.py`
- Modify: `service_tests/test_execution_closure.py`

- [ ] **Step 1: 写出报告入口与失败重试失败测试**

```python
from rest_framework.test import APIClient


def test_workbench_exposes_allure_report_entry_and_retry_action():
    client = APIClient()

    response = client.get("/ui/v3/workbench/")

    assert response.status_code == 200
    content = response.content.decode("utf-8")
    assert 'data-testid="latest-allure-report-entry"' in content
    assert 'data-testid="retry-failed-testcase-button"' in content
```

- [ ] **Step 2: 运行单测确认红灯**

Run: `.venv_service\Scripts\python.exe -m pytest service_tests/test_mainline_workbench_ui.py::test_workbench_exposes_allure_report_entry_and_retry_action -q --ds=platform_service.test_settings --basetemp=.pytest_tmp/report_retry_red`

Expected: FAIL

- [ ] **Step 3: 写最小报告与重试实现**

```html
<div class="latest-report-actions">
  <a data-testid="latest-allure-report-entry" href="#" target="_blank" rel="noopener">查看 Allure 报告</a>
  <button data-testid="retry-failed-testcase-button">失败重试</button>
</div>
```

```python
def build_latest_execution_summary(self, scenario_id: str) -> dict:
    result = self.get_scenario_result(scenario_id)
    result["latest_allure_report_path"] = result.get("report_path", "")
    result["retry_available"] = result.get("execution_status") == "failed"
    return result
```

- [ ] **Step 4: 运行单测确认绿灯**

Run: `.venv_service\Scripts\python.exe -m pytest service_tests/test_mainline_workbench_ui.py::test_workbench_exposes_allure_report_entry_and_retry_action -q --ds=platform_service.test_settings --basetemp=.pytest_tmp/report_retry_green`

Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add scenario_service/services.py scenario_service/views.py scenario_service/templates/scenario_service/workbench.html service_tests/test_mainline_workbench_ui.py service_tests/test_execution_closure.py
git commit -m "feat: 增加allure报告入口和失败重试工作台动作"
```

---

### Task 16: 文档同步与全量回归

**Files:**
- Modify: `README.md`
- Modify: `product_document/产品需求说明书(全局).md`
- Modify: `product_document/架构设计/UI设计说明文档.md`
- Modify: `product_document/架构设计/现有接口自动化测试框架改造方案.md`
- Modify: `product_document/测试文档/详细测试用例说明书(V1).md`
- Modify: `task_plan.md`
- Modify: `findings.md`
- Modify: `progress.md`

- [ ] **Step 1: 写出文档治理失败测试**

```python
from pathlib import Path


def test_readme_mentions_api_test_project_model_asset_layout():
    content = Path("README.md").read_text(encoding="utf-8")

    assert "api_test/core/<project>/<model>/" in content
    assert "api_test/tests/<project>/<model>/" in content
    assert "抓包前置过滤" in content
    assert "allure" in content
```

- [ ] **Step 2: 运行单测确认红灯**

Run: `D:\Python3.12\python.exe -m pytest tests/test_generic_framework_cleanup.py::test_readme_mentions_api_test_project_model_asset_layout -q --basetemp=.pytest_tmp/doc_sync_red`

Expected: FAIL，提示 README 尚未同步新主线口径。

- [ ] **Step 3: 同步文档与记录**

```markdown
- 主入口更新为“用例展示与执行”
- 抓包入口下沉到模块 / 子模块级
- 抓包支持 URL / IP 前置过滤，且过滤后只记录匹配数据
- 核心资产固定落到 `api_test/core/<project>/<model>/` 与 `api_test/tests/<project>/<model>/`
- 所有生成用例统一遵守 `allure.feature / allure.story / allure.step` 规范
```

- [ ] **Step 4: 执行全量回归**

Run: `.venv_service\Scripts\python.exe -m pytest service_tests -q --ds=platform_service.test_settings --basetemp=.pytest_tmp/mainline_full_service`

Expected: PASS，所有服务层测试通过。

Run: `D:\Python3.12\python.exe -m pytest tests/platform_core -q --basetemp=.pytest_tmp/mainline_full_platform_core`

Expected: PASS

Run: `D:\Python3.12\python.exe -m pytest tests -q --basetemp=.pytest_tmp/mainline_full_root`

Expected: PASS

Run: `D:\Python3.12\python.exe -m pytest api_test/tests -q --basetemp=.pytest_tmp/mainline_full_api_test`

Expected: PASS

- [ ] **Step 5: 提交**

```bash
git add README.md product_document/产品需求说明书(全局).md product_document/架构设计/UI设计说明文档.md product_document/架构设计/现有接口自动化测试框架改造方案.md product_document/测试文档/详细测试用例说明书(V1).md task_plan.md findings.md progress.md
git commit -m "docs: 同步主线改造设计口径与全量回归结果"
```

---

## 计划自检

### 1. 规格覆盖检查
- 主界面三段式、左树、中间列、右侧混合式详情：由 Task 1、Task 2、Task 3 覆盖。
- 模块级抓包、前置 URL/IP 过滤、只记录匹配数据：由 Task 4、Task 5、Task 6 覆盖。
- `HTTP 方法 + 完整 URL 路径` 接口匹配：由 Task 7、Task 8 覆盖。
- 资产目录落到 `api_test/core/<project>/<model>/` 与 `api_test/tests/<project>/<model>/`：由 Task 9、Task 12 覆盖。
- 抓包顺序就是用例调用顺序：由 Task 10 覆盖。
- `allure.feature / story / step` 强制规范：由 Task 11 覆盖。
- AI 生成后必须通过 `pytest` 才允许提交：由 Task 13、Task 14 覆盖。
- `allure` 报告与失败重试：由 Task 15 覆盖。
- 文档同步与全量回归：由 Task 16 覆盖。

### 2. 占位词检查
- 计划中未使用 `TODO / TBD / 待补 / 待定 / implement later` 等占位词。
- 每个任务均提供了明确文件路径、测试代码、命令和最小实现代码片段。

### 3. 类型与命名一致性检查
- 抓包过滤统一使用 `CaptureProxyFilter`、抓包会话统一使用 `CaptureProxyRecord`。
- 方法注册统一使用 `ApiTestMethodRegistry`。
- 生成门禁统一使用 `GenerationJobRecord` 和 `evaluate_generation_gate()`。
- 资产目录命名统一使用 `project_code / model_code / case_code`。
