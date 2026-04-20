"""Vue 工作台读模型接口测试。"""

from __future__ import annotations

from rest_framework.test import APIClient


def build_workbench_case_payload(
    *,
    case_id: str,
    case_code: str,
    project_code: str,
    environment_code: str,
    scenario_set_code: str,
    module_id: str,
) -> dict:
    """构造工作台导航树测试使用的功能用例载荷。"""
    return {
        "project_code": project_code,
        "environment_code": environment_code,
        "scenario_set_code": scenario_set_code,
        "case_id": case_id,
        "case_code": case_code,
        "case_name": "工作台导航树场景",
        "module_id": module_id,
        "steps": [
            {
                "step_name": "查询用户详情",
                "operation_id": "operation-get-user",
                "request": {"path_params": {"user_id": 1}},
                "expected": {"status_code": 200},
            }
        ],
    }


def test_workbench_bootstrap_endpoint_exposes_vue_frontend_metadata():
    """工作台启动接口应返回 Vue 前端启动所需元数据。"""
    client = APIClient()

    response = client.get("/api/v2/workbench/bootstrap/")

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    data = payload["data"]
    assert data["page_title"] == "抓包与接口自动化工作台"
    assert data["frontend_framework"] == "vue3"
    assert data["frontend_entry"] == "/ui/v3/workbench/"
    assert data["design_source"] == "DESIGN.md"


def test_workbench_navigation_endpoint_returns_project_module_submodule_tree(service_test_token: str):
    """工作台导航树接口应返回项目/模块/子模块/测试用例结构。"""
    client = APIClient()
    project_code = f"vue-project-{service_test_token}"
    environment_code = f"module-env-{service_test_token}"
    scenario_set_code = f"submodule-set-{service_test_token}"
    module_id = f"account_center_{service_test_token}"
    case_code = f"workbench_tree_case_{service_test_token}"
    payload = build_workbench_case_payload(
        case_id=f"fc-workbench-tree-{service_test_token}",
        case_code=case_code,
        project_code=project_code,
        environment_code=environment_code,
        scenario_set_code=scenario_set_code,
        module_id=module_id,
    )

    import_response = client.post("/api/v2/scenarios/import-functional-case/", payload, format="json")
    response = client.get("/api/v2/workbench/navigation/")

    assert import_response.status_code == 201
    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    projects = payload["data"]["projects"]
    project = next(item for item in projects if item["project_code"] == project_code)
    module = next(item for item in project["modules"] if item["module_code"] == module_id)
    submodule = next(item for item in module["submodules"] if item["submodule_code"] == scenario_set_code)

    assert submodule["testcases"][0]["scenario_code"] == case_code
    assert submodule["testcases"][0]["execution_status"] == "not_started"


def test_workbench_test_interface_catalog_endpoint_lists_api_test_methods():
    """测试接口目录接口应能返回 `api_test` 目录扫描结果。"""
    client = APIClient()

    response = client.get("/api/v2/workbench/test-interfaces/")

    assert response.status_code == 200
    payload = response.json()
    assert payload["success"] is True
    interfaces = payload["data"]["interfaces"]
    target = next(item for item in interfaces if item["method_name"] == "get_user")

    assert target["http_method"] == "GET"
    assert target["path_template"] == "/users/{user_id}"
    assert target["source_file"].endswith("api_test/core/jsonplaceholder_api.py")


def test_workbench_test_interface_detail_endpoint_returns_method_summary():
    """测试接口详情接口应返回单个接口方法的详细摘要。"""
    client = APIClient()
    list_response = client.get("/api/v2/workbench/test-interfaces/")

    assert list_response.status_code == 200
    interfaces = list_response.json()["data"]["interfaces"]
    target = next(item for item in interfaces if item["method_name"] == "list_posts")

    detail_response = client.get(f"/api/v2/workbench/test-interfaces/{target['interface_id']}/")

    assert detail_response.status_code == 200
    payload = detail_response.json()
    assert payload["success"] is True
    assert payload["data"]["method_name"] == "list_posts"
    assert payload["data"]["http_method"] == "GET"
    assert payload["data"]["path_template"] == "/posts"
