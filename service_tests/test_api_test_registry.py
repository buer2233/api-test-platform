"""`api_test` 接口方法注册扫描测试。"""

from __future__ import annotations

from scenario_service.services import FunctionalCaseScenarioService
from scenario_service.api_test_registry import ApiTestMethodRegistry


def test_registry_matches_existing_method_by_http_method_and_full_path():
    """注册表应能按 HTTP 方法和完整路径命中已有接口方法。"""
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


def test_candidate_is_marked_as_reuse_or_create_by_registry_match():
    """候选接口应根据注册表命中情况标注为复用或新增。"""
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
