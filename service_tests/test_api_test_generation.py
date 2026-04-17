"""`api_test` 资产生成路径测试。"""

from __future__ import annotations

from pathlib import Path

from rest_framework.test import APIClient

from scenario_service.api_test_generator import (
    build_asset_paths,
    build_testcase_steps,
    evaluate_generation_gate,
    render_testcase_module,
    write_generated_assets,
)


def test_build_asset_paths_targets_project_and_model_directories():
    """生成路径应稳定落到 `api_test` 的项目目录和模块目录。"""
    result = build_asset_paths(project_code="ebuilder", model_code="app_center", case_code="create_app")

    assert result["core_dir"] == Path("api_test/core/ebuilder/app_center")
    assert result["test_dir"] == Path("api_test/tests/ebuilder/app_center")
    assert result["test_file"] == Path("api_test/tests/ebuilder/app_center/test_create_app.py")


def test_build_testcase_steps_preserves_capture_order():
    """生成测试步骤时应保持抓包选择顺序。"""
    steps = build_testcase_steps(
        [
            {"method_name": "login_app", "selection_order": 1},
            {"method_name": "get_app_detail", "selection_order": 2},
        ]
    )

    assert steps[0]["method_name"] == "login_app"
    assert steps[1]["method_name"] == "get_app_detail"


def test_render_testcase_module_contains_allure_feature_story_and_steps():
    """生成的测试代码应包含 Allure 规范与步骤包装。"""
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


def test_write_generated_assets_creates_core_and_test_files(tmp_path: Path):
    """生成资产时应同时落盘核心方法文件和测试文件。"""
    result = write_generated_assets(
        workspace_root=tmp_path,
        project_code="ebuilder",
        model_code="app_center",
        core_filename="component_api.py",
        core_code="def enable_component():\n    return {}\n",
        test_case_code="class TestAppCenter:\n    pass\n",
        case_code="create_app",
    )

    assert (tmp_path / "api_test/core/ebuilder/app_center/component_api.py").exists()
    assert (tmp_path / "api_test/tests/ebuilder/app_center/test_create_app.py").exists()
    assert result["project_code"] == "ebuilder"


def test_generation_gate_blocks_submission_when_pytest_fails():
    """`pytest` 失败时应阻断生成结果提交。"""
    result = evaluate_generation_gate({"pytest_exit_code": 1, "pytest_status": "failed"})

    assert result["submission_allowed"] is False
    assert result["status"] == "blocked"


def test_generation_confirmation_endpoint_returns_pytest_gate_summary():
    """生成确认接口应返回 `pytest` 门禁摘要。"""
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
