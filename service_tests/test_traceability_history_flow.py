"""V2 P1 来源追溯与执行历史测试。"""

from __future__ import annotations

import pytest

from scenario_service.services import FunctionalCaseScenarioService


pytestmark = pytest.mark.django_db


def test_import_and_repeated_execution_preserve_source_traces_and_history(tmp_path):
    """场景导入和重复执行后应保留来源追溯与独立历史。"""
    service = FunctionalCaseScenarioService()
    scenario = service.import_functional_case(
        {
            "case_id": "fc-history-001",
            "case_code": "history_query_user_profile",
            "case_name": "重复执行历史场景",
            "steps": [
                {
                    "step_name": "查询用户详情",
                    "operation_id": "operation-get-user",
                    "request": {"path_params": {"user_id": 1}},
                    "expected": {"status_code": 200},
                }
            ],
        }
    )

    service.review_scenario(
        scenario_id=scenario.scenario_id,
        review_status="approved",
        reviewer="qa-owner",
        review_comment="通过",
    )
    service.request_execution(scenario.scenario_id, tmp_path / "run-1")
    service.request_execution(scenario.scenario_id, tmp_path / "run-2")

    detail = service.get_scenario_detail(scenario.scenario_id)
    result = service.get_scenario_result(scenario.scenario_id)

    assert detail["source_traces"][0]["source_type"] == "functional_case"
    assert detail["source_traces"][0]["entity_type"] == "scenario"
    assert len(result["execution_history"]) == 2
    assert result["execution_history"][0]["execution_id"] != result["execution_history"][1]["execution_id"]
    assert result["execution_history"][0]["trigger_source"] == "manual"
