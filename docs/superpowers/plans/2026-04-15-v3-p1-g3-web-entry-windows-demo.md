# V3 P1 G3 Web 正式入口深化与 Windows Demo Implementation Plan

> **For agentic workers:** 本计划承接已获批准的 `V3 P1-G3` 范围，按 TDD 顺序推进“Web 正式入口深化 -> Windows Demo 启动链路 -> 浏览器先验 / Windows 复验契约”闭环，不与 `G4` 调度中心混做。

**Goal:** 在已完成 `P1-G1` 权限与审计治理、`P1-G2` 抓包正式执行闭环的基础上，把当前 `V2` 工作台升级为 `V3` 正式入口，并交付一个可在 Windows 上直接启动、直接进入真实测试页面的 Demo 启动方案，同时保持浏览器端为日常高频验证主路径。

**Architecture:** 继续复用当前 `Django + DRF + MySQL + Django Template + service_tests` 的增量改造路线，不新建独立 React/Tauri 工程，也不引入第二套事实缓存。Web 入口与 Windows Demo 继续共同消费 `/api/v2/scenarios/*` 服务契约；Windows Demo 本轮采用“浏览器应用模式启动器 + 同一路由入口”的最小可运行方案，`Tauri` 仍保留为后续阶段性打包复验优先壳方案。

**Tech Stack:** Python 3.12、Django、Django REST Framework、pytest、PowerShell、MySQL、现有 `scenario_service` / `platform_service`

---

## Scope Check

`P1-G3` 只覆盖以下主线：
1. Web 正式入口升级为可承接权限、审计、抓包正式确认与 Windows Demo 信息的统一产品入口；
2. 为浏览器入口补齐显式 `actor / reviewer / operator`、授权查询、审计日志查询和抓包正式确认控件；
3. 交付一个 Windows 可直接启动的 Demo 启动器，且该启动器与浏览器端共用同一入口 URL 与服务契约；
4. 建立“浏览器先验 + Windows Demo 复验”的自动化验证与文档口径。

本计划**不包含**：
1. `G4` 调度中心、批量执行、队列、重试与聚合能力；
2. 新建 React 工程、Electron 工程或真实 Tauri 打包工程；
3. `macOS` 客户端实现；
4. 完整桌面安装包、升级器和分发体系。

## File Structure

- Create: `D:\AI\api-test-platform\service_tests\test_v3_p1_entry_windows_demo.py`
  作用：覆盖 Web 正式入口契约、Windows Demo manifest 契约与启动器 dry-run 行为。
- Create: `D:\AI\api-test-platform\windows_demo\launch_v3_workbench_demo.ps1`
  作用：提供 Windows Demo 启动脚本，支持浏览器应用模式、可选服务启动和 dry-run 验证。
- Modify: `D:\AI\api-test-platform\platform_service\urls.py`
  作用：注册 `V3` 正式入口路由。
- Modify: `D:\AI\api-test-platform\scenario_service\views.py`
  作用：新增 Windows Demo manifest 接口，并为入口模板注入 `V3` 正式入口上下文。
- Modify: `D:\AI\api-test-platform\scenario_service\urls.py`
  作用：注册 Windows Demo manifest 查询路由。
- Modify: `D:\AI\api-test-platform\scenario_service\templates\scenario_service\workbench.html`
  作用：把当前工作台升级为 `V3` 正式入口，接入权限、审计、抓包正式确认和 Windows Demo 区域。
- Modify: `D:\AI\api-test-platform\README.md`
- Modify: `D:\AI\api-test-platform\product_document\阶段文档\V3阶段工作计划文档.md`
- Modify: `D:\AI\api-test-platform\product_document\测试文档\详细测试用例说明书(V3-P1).md`
- Modify: `D:\AI\api-test-platform\task_plan.md`
- Modify: `D:\AI\api-test-platform\findings.md`
- Modify: `D:\AI\api-test-platform\progress.md`

### Task 1: Web 正式入口红灯测试

**Files:**
- Create: `D:\AI\api-test-platform\service_tests\test_v3_p1_entry_windows_demo.py`
- Modify: `D:\AI\api-test-platform\scenario_service\templates\scenario_service\workbench.html`
- Modify: `D:\AI\api-test-platform\platform_service\urls.py`

- [ ] **Step 1: Write the failing test**

```python
def test_v3_workbench_renders_permission_audit_formalization_and_windows_demo_regions():
    client = APIClient()

    response = client.get("/ui/v3/workbench/")

    assert response.status_code == 200
    content = response.content.decode("utf-8")
    assert "V3 场景工作台" in content
    assert 'data-testid="actor-panel"' in content
    assert 'data-testid="access-grant-panel"' in content
    assert 'data-testid="audit-log-panel"' in content
    assert 'data-testid="traffic-capture-formalization-panel"' in content
    assert 'data-testid="windows-demo-panel"' in content
    assert "/api/v2/scenarios/governance/access-grants/" in content
    assert "/api/v2/scenarios/governance/audit-logs/" in content
    assert "/api/v2/scenarios/governance/windows-demo/" in content
    assert "traffic_capture_formalization" in content
```

- [ ] **Step 2: Run test to verify it fails**

Run: `.\.venv_service\Scripts\python.exe -m pytest service_tests\test_v3_p1_entry_windows_demo.py -k "renders_permission_audit_formalization_and_windows_demo_regions" -q --basetemp=.pytest_tmp\v3_p1_g3_red_1`

Expected: FAIL，原因应为当前没有 `/ui/v3/workbench/` 路由，且模板未承接 `P1-G1 / G2` 与 Windows Demo 区域。

- [ ] **Step 3: Write minimal implementation**

要求：
1. 新增 `/ui/v3/workbench/` 正式入口路由；
2. 保留 `/ui/v2/workbench/` 兼容访问；
3. 模板显式承接 `actor / reviewer / operator`、权限授权、审计日志、抓包正式确认/绑定确认和 Windows Demo 信息；
4. 页面继续只消费统一服务层接口，不新增第二套事实源。

- [ ] **Step 4: Run test to verify it passes**

Run: `.\.venv_service\Scripts\python.exe -m pytest service_tests\test_v3_p1_entry_windows_demo.py -k "renders_permission_audit_formalization_and_windows_demo_regions" -q --basetemp=.pytest_tmp\v3_p1_g3_green_1`

Expected: PASS

### Task 2: Windows Demo manifest 与启动器红灯测试

**Files:**
- Modify: `D:\AI\api-test-platform\service_tests\test_v3_p1_entry_windows_demo.py`
- Modify: `D:\AI\api-test-platform\scenario_service\views.py`
- Modify: `D:\AI\api-test-platform\scenario_service\urls.py`
- Create: `D:\AI\api-test-platform\windows_demo\launch_v3_workbench_demo.ps1`

- [ ] **Step 1: Write the failing tests**

```python
def test_windows_demo_manifest_endpoint_returns_browser_first_shared_contract():
    client = APIClient()

    response = client.get("/api/v2/scenarios/governance/windows-demo/")

    assert response.status_code == 200
    data = response.json()["data"]
    assert data["entry_path"] == "/ui/v3/workbench/"
    assert data["preferred_shell"] == "browser_app"
    assert data["tauri_priority"] is True
    assert data["packaging_strategy"] == "browser_first_stage_packaging_recheck"
    assert "/api/v2/scenarios/" in data["shared_contract_endpoints"]
    assert "/api/v2/scenarios/governance/access-grants/" in data["shared_contract_endpoints"]


def test_windows_demo_launcher_dry_run_outputs_v3_entry_url():
    script_path = Path(__file__).resolve().parents[1] / "windows_demo" / "launch_v3_workbench_demo.ps1"
    result = subprocess.run(
        [
            "powershell",
            "-NoProfile",
            "-ExecutionPolicy",
            "Bypass",
            "-File",
            str(script_path),
            "-BaseUrl",
            "http://127.0.0.1:18080",
            "-SkipServiceStartup",
            "-DryRun",
        ],
        check=True,
        capture_output=True,
        text=True,
    )
    payload = json.loads(result.stdout)

    assert payload["entry_url"] == "http://127.0.0.1:18080/ui/v3/workbench/"
    assert payload["launch_mode"] == "browser_first"
    assert payload["browser_mode"] == "app"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `.\.venv_service\Scripts\python.exe -m pytest service_tests\test_v3_p1_entry_windows_demo.py -k "windows_demo_manifest_endpoint or windows_demo_launcher_dry_run_outputs_v3_entry_url" -q --basetemp=.pytest_tmp\v3_p1_g3_red_2`

Expected: FAIL，原因应为当前没有 Windows Demo manifest 接口，也没有启动器脚本。

- [ ] **Step 3: Write minimal implementation**

要求：
1. 暴露 `/api/v2/scenarios/governance/windows-demo/` manifest 接口；
2. manifest 明确 `browser_first + tauri_priority + shared_contract_endpoints`；
3. 提供 Windows PowerShell 启动器脚本，支持 `-DryRun`、`-BaseUrl`、`-SkipServiceStartup`；
4. 启动器默认入口必须是 `/ui/v3/workbench/`。

- [ ] **Step 4: Run tests to verify they pass**

Run: `.\.venv_service\Scripts\python.exe -m pytest service_tests\test_v3_p1_entry_windows_demo.py -k "windows_demo_manifest_endpoint or windows_demo_launcher_dry_run_outputs_v3_entry_url" -q --basetemp=.pytest_tmp\v3_p1_g3_green_2`

Expected: PASS

### Task 3: G3 回归、文档同步与阶段记录

**Files:**
- Modify: `D:\AI\api-test-platform\README.md`
- Modify: `D:\AI\api-test-platform\product_document\阶段文档\V3阶段工作计划文档.md`
- Modify: `D:\AI\api-test-platform\product_document\测试文档\详细测试用例说明书(V3-P1).md`
- Modify: `D:\AI\api-test-platform\task_plan.md`
- Modify: `D:\AI\api-test-platform\findings.md`
- Modify: `D:\AI\api-test-platform\progress.md`

- [ ] **Step 1: Run targeted G3 tests**

Run: `.\.venv_service\Scripts\python.exe -m pytest service_tests\test_v3_p1_entry_windows_demo.py -q --basetemp=.pytest_tmp\v3_p1_g3_targeted`

Expected: PASS

- [ ] **Step 2: Run service regression**

Run: `.\.venv_service\Scripts\python.exe -m pytest service_tests -q --basetemp=.pytest_tmp\v3_p1_g3_service`

Expected: PASS

- [ ] **Step 3: Run non-service regression**

Run: `python -m pytest tests/platform_core -q --basetemp=.pytest_tmp\v3_p1_g3_platform_core`

Expected: PASS

Run: `python -m pytest tests -q --basetemp=.pytest_tmp\v3_p1_g3_root`

Expected: PASS

Run: `python -m pytest api_test/tests -q --basetemp=.pytest_tmp\v3_p1_g3_api_test`

Expected: PASS

- [ ] **Step 4: Sync docs**

```markdown
- 在 `V3阶段工作计划文档.md` 中把 `V3-IMP-003` 的说明更新为 `G1 / G2 已完成，G3 已启动/已完成`
- 在 `详细测试用例说明书(V3-P1).md` 中回填 `TC-V3-P1-MIG-002`、`TC-V3-P1-UI-001`、`TC-V3-P1-UI-002`、`TC-V3-P1-UI-003`、`TC-V3-P1-INT-002` 的执行结果
- 在 `README.md` 中把当前阶段更新到 “V3 P1 G3 开发中/已完成”
```

- [ ] **Step 5: Record risks and follow-up**

```markdown
- 记录当前 Windows Demo 以浏览器应用模式启动器承接“可实际测试”的最小能力
- 记录 Tauri 仍保留为后续阶段性打包复验优先壳方案，待 Rust 工具链就绪后接入
- 记录 G4 调度中心需要继续复用当前 Web 入口和 Windows Demo 的统一契约，不再新增第二套入口
```

## Coverage Check

- `TC-V3-P1-MIG-002` -> Task 2 / Task 3
- `TC-V3-P1-UI-001` -> Task 1
- `TC-V3-P1-UI-002` -> Task 2
- `TC-V3-P1-UI-003` -> Task 2 / Task 3
- `TC-V3-P1-INT-002` -> Task 2 / Task 3

## Notes

- 本轮为了满足“浏览器先验 + Windows 可真实测试”的阶段目标，优先交付浏览器应用模式启动器，不强行引入当前机器尚未具备工具链的 Tauri 工程。
- 文档与 manifest 必须显式说明：当前方案并未否定 `Tauri 优先`，而是把它保留为后续阶段性打包复验路径。
- 所有新增方法、脚本和测试说明继续使用中文注释。
