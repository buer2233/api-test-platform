"""V2 服务层持久化测试。"""

from __future__ import annotations

from scenario_service.services import FunctionalCaseScenarioService


def test_scenario_record_persists_functional_case_draft(service_test_token: str):
    """TC-V2-SVC-001 场景草稿导入服务应能持久化场景与步骤。"""
    service = FunctionalCaseScenarioService()
    case_id = f"fc-order-001-{service_test_token}"
    case_code = f"create_order_and_query_order_detail_{service_test_token}"
    payload = {
        "case_id": case_id,
        "case_code": case_code,
        "case_name": "创建订单后查询订单详情",
        "steps": [
            {
                "step_name": "创建订单",
                "operation_id": "operation-create-order",
                "expected": {"status_code": 201},
            }
        ],
    }

    scenario = service.import_functional_case(payload)

    assert scenario.scenario_id.startswith("scenario-")
    assert scenario.scenario_code == case_code
    assert scenario.review_status == "pending"
    assert scenario.steps.count() == 1
