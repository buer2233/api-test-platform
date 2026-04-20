# Vue3 Workbench Frontend Separation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将当前 Django 模板工作台重构为基于 `DESIGN.md` 的 Vue3 + TypeScript 前后端分离工作台，并删除旧 Jinja2 前端模板代码。

**Architecture:** 后端继续保留 Django + DRF 业务能力，但不再承担工作台业务模板渲染；新增 Vue3 独立前端工程负责三段式工作台、导航树、详情区和执行交互。后端补齐工作台读模型 API 与前端静态入口承接，旧模板页在新前端稳定后删除。

**Tech Stack:** Python、Django、DRF、MySQL、Vue3、TypeScript、Vite、Vue Router、Vitest

---

### Task 1: 文档与规则先收口

**Files:**
- Modify: `AGENTS.md`
- Modify: `CLAUDE.md`
- Modify: `product_document/产品需求说明书(全局).md`
- Modify: `product_document/架构设计/总体架构设计说明书.md`
- Modify: `product_document/架构设计/UI设计说明文档.md`
- Create: `docs/superpowers/specs/2026-04-20-vue3-workbench-frontend-separation-design.md`

- [ ] **Step 1: 写文档治理红灯测试**

```python
def test_docs_require_design_md_and_vue3_frontend():
    assert "DESIGN.md" in agents_content
    assert "Vue3 + TypeScript" in architecture_content
    assert "前后端分离" in ui_content
```

- [ ] **Step 2: 运行红灯测试**

Run: `python -m pytest tests/test_generic_framework_cleanup.py -q --basetemp=.pytest_tmp/doc_red`
Expected: FAIL

- [ ] **Step 3: 写最小文档实现**

```markdown
### 2.0.1 DESIGN.md 前置规则
在编写任何 UI 之前必须读取并参考项目根目录 `DESIGN.md`。

- 前端：当前轮已确认重构为 **Vue3 + TypeScript**
- Web UI 形态：当前轮已确认采用**前后端分离设计**
```

- [ ] **Step 4: 运行治理测试确认通过**

Run: `python -m pytest tests/test_generic_framework_cleanup.py -q --basetemp=.pytest_tmp/doc_green`
Expected: PASS

### Task 2: 后端前端入口与工作台读模型

**Files:**
- Create: `service_tests/test_vue_frontend_entry.py`
- Create: `service_tests/test_workbench_read_models.py`
- Modify: `scenario_service/api_test_registry.py`
- Modify: `scenario_service/services.py`
- Modify: `scenario_service/views.py`
- Modify: `scenario_service/urls.py`
- Modify: `platform_service/urls.py`

- [ ] **Step 1: 写前端入口与读模型红灯测试**

```python
def test_workbench_routes_return_vue_entry_shell():
    response = client.get("/ui/v3/workbench/")
    assert '<div id="app"></div>' in response.content.decode("utf-8")

def test_workbench_navigation_endpoint_returns_tree():
    response = client.get("/api/v2/workbench/navigation/")
    assert response.json()["data"]["projects"][0]["modules"][0]["submodules"]
```

- [ ] **Step 2: 运行红灯测试**

Run: `.venv_service\Scripts\python.exe -m pytest service_tests/test_vue_frontend_entry.py service_tests/test_workbench_read_models.py -q --basetemp=.pytest_tmp_service/workbench_backend_red`
Expected: FAIL

- [ ] **Step 3: 写最小实现**

```python
class WorkbenchFrontendEntryView(View):
    def get(self, request, *args, **kwargs):
        return HttpResponse('<!doctype html><html><body><div id="app"></div></body></html>')
```

```python
class WorkbenchNavigationView(APIView):
    def get(self, request):
        return Response({"success": True, "data": SCENARIO_SERVICE.build_workbench_navigation()})
```

- [ ] **Step 4: 运行后端测试确认通过**

Run: `.venv_service\Scripts\python.exe -m pytest service_tests/test_vue_frontend_entry.py service_tests/test_workbench_read_models.py -q --basetemp=.pytest_tmp_service/workbench_backend_green`
Expected: PASS

### Task 3: 初始化 Vue3 前端工程

**Files:**
- Create: `frontend/package.json`
- Create: `frontend/tsconfig.json`
- Create: `frontend/vite.config.ts`
- Create: `frontend/index.html`
- Create: `frontend/src/main.ts`
- Create: `frontend/src/App.vue`
- Create: `frontend/src/router/index.ts`
- Create: `frontend/src/styles/design-tokens.css`
- Create: `frontend/src/components/WorkbenchShell.vue`
- Create: `frontend/src/views/WorkbenchView.vue`
- Create: `frontend/src/__tests__/workbench-shell.spec.ts`

- [ ] **Step 1: 写前端壳层红灯测试**

```ts
it('渲染三段式工作台壳层并显示设计标题', () => {
  const wrapper = mount(WorkbenchShell, { props: { title: '抓包与接口自动化工作台' } })
  expect(wrapper.find('[data-testid="left-tree-panel"]').exists()).toBe(true)
  expect(wrapper.find('[data-testid="middle-list-panel"]').exists()).toBe(true)
  expect(wrapper.find('[data-testid="right-detail-panel"]').exists()).toBe(true)
})
```

- [ ] **Step 2: 运行前端红灯测试**

Run: `npm --prefix frontend run test -- --runInBand`
Expected: FAIL

- [ ] **Step 3: 写最小前端实现**

```ts
import { createApp } from 'vue'
import App from './App.vue'
import router from './router'
import './styles/design-tokens.css'

createApp(App).use(router).mount('#app')
```

```vue
<template>
  <main class="workbench-shell">
    <section data-testid="left-tree-panel"></section>
    <section data-testid="middle-list-panel"></section>
    <section data-testid="right-detail-panel"></section>
  </main>
</template>
```

- [ ] **Step 4: 运行前端测试确认通过**

Run: `npm --prefix frontend run test -- --runInBand`
Expected: PASS

### Task 4: 接通导航树、详情区、测试接口目录与执行动作

**Files:**
- Create: `frontend/src/services/api.ts`
- Create: `frontend/src/services/types.ts`
- Create: `frontend/src/components/NavigationTree.vue`
- Create: `frontend/src/components/WorkbenchListPanel.vue`
- Create: `frontend/src/components/WorkbenchDetailPanel.vue`
- Create: `frontend/src/__tests__/workbench-navigation.spec.ts`
- Create: `frontend/src/__tests__/workbench-actions.spec.ts`
- Modify: `frontend/src/views/WorkbenchView.vue`

- [ ] **Step 1: 写交互红灯测试**

```ts
it('渲染项目-模块-子模块-测试用例-测试接口树', async () => {
  expect(wrapper.text()).toContain('项目')
  expect(wrapper.text()).toContain('模块')
  expect(wrapper.text()).toContain('子模块')
  expect(wrapper.text()).toContain('测试接口')
})

it('点击执行与重试会调用后端接口', async () => {
  await wrapper.get('[data-testid="execute-testcase-button"]').trigger('click')
  expect(executeMock).toHaveBeenCalled()
})
```

- [ ] **Step 2: 运行红灯测试**

Run: `npm --prefix frontend run test -- --runInBand`
Expected: FAIL

- [ ] **Step 3: 写最小实现**

```ts
export async function fetchWorkbenchNavigation() {
  return get('/api/v2/workbench/navigation/')
}

export async function executeScenario(scenarioId: string, payload: ExecutePayload) {
  return post(`/api/v2/scenarios/${scenarioId}/execute/`, payload)
}
```

```vue
<template>
  <NavigationTree :projects="navigation.projects" @select-testcase="handleTestcaseSelect" />
  <WorkbenchDetailPanel :detail="selectedDetail" :result="selectedResult" @execute="handleExecute" @retry="handleRetry" />
</template>
```

- [ ] **Step 4: 运行前端测试确认通过**

Run: `npm --prefix frontend run test -- --runInBand`
Expected: PASS

### Task 5: 切换正式入口并删除旧模板

**Files:**
- Modify: `scenario_service/views.py`
- Delete: `scenario_service/templates/scenario_service/workbench.html`
- Modify: `README.md`
- Modify: `product_document/架构设计/现有接口自动化测试框架改造方案.md`

- [ ] **Step 1: 写旧模板清理红灯测试**

```python
def test_legacy_workbench_template_is_removed():
    assert not Path("scenario_service/templates/scenario_service/workbench.html").exists()
```

- [ ] **Step 2: 运行红灯测试**

Run: `python -m pytest tests/test_generic_framework_cleanup.py -q --basetemp=.pytest_tmp/legacy_template_red`
Expected: FAIL

- [ ] **Step 3: 写最小清理实现**

```python
class ScenarioWorkbenchView(View):
    def get(self, request, *args, **kwargs):
        return self.frontend_entry_response()
```

```bash
git rm scenario_service/templates/scenario_service/workbench.html
```

- [ ] **Step 4: 运行全量验证**

Run: `.venv_service\Scripts\python.exe -m pytest service_tests -q --basetemp=.pytest_tmp_service/vue_workbench_full`
Expected: PASS

Run: `python -m pytest tests -q --basetemp=.pytest_tmp/vue_root_full`
Expected: PASS

Run: `python -m pytest tests/platform_core -q --basetemp=.pytest_tmp/vue_platform_core_full`
Expected: PASS

Run: `python -m pytest api_test/tests -q --basetemp=.pytest_tmp/vue_api_test_full`
Expected: PASS

Run: `npm --prefix frontend run test`
Expected: PASS

Run: `npm --prefix frontend run build`
Expected: PASS

- [ ] **Step 5: 提交并推送**

```bash
git add -A
git commit -m "重构：完成Vue3前后端分离工作台重构并清理旧Jinja2前端模板"
git push origin main
```
