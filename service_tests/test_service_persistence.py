"""V2 服务层持久化测试。"""

from __future__ import annotations

import pytest

from scenario_service.services import FunctionalCaseScenarioService


pytestmark = pytest.mark.django_db


def test_scenario_record_persists_functional_case_draft():
    """TC-V2-SVC-001 场景草稿导入服务应能持久化场景与步骤。"""
    service = FunctionalCaseScenarioService()
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

    scenario = service.import_functional_case(payload)

    assert scenario.scenario_id.startswith("scenario-")
    assert scenario.scenario_code == "create_order_and_query_order_detail"
    assert scenario.review_status == "pending"
    assert scenario.steps.count() == 1
