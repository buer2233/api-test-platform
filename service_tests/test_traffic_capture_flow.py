"""V2 抓包草稿化导入链路测试。"""

from __future__ import annotations

import pytest
from rest_framework.test import APIClient


pytestmark = pytest.mark.django_db


def build_traffic_capture_payload() -> dict:
    """构造服务层抓包导入测试使用的最小 HAR 样例。"""
    return {
        "log": {
            "entries": [
                {
                    "startedDateTime": "2026-04-09T10:00:00.000Z",
                    "request": {
                        "method": "GET",
                        "url": "https://cdn.example.com/assets/app.js",
                    },
                    "response": {
                        "status": 200,
                        "content": {"mimeType": "application/javascript"},
                    },
                },
                {
                    "startedDateTime": "2026-04-09T10:00:02.000Z",
                    "request": {
                        "method": "POST",
                        "url": "https://api.example.com/v1/login",
                        "headers": [
                            {"name": "Content-Type", "value": "application/json"},
                        ],
                        "postData": {
                            "mimeType": "application/json",
                            "text": "{\"username\": \"demo\", \"password\": \"demo\"}",
                        },
                    },
                    "response": {
                        "status": 200,
                        "content": {
                            "mimeType": "application/json",
                            "text": "{\"token\": \"token-001\", \"user_id\": 7}",
                        },
                    },
                },
                {
                    "startedDateTime": "2026-04-09T10:00:03.000Z",
                    "request": {
                        "method": "GET",
                        "url": "https://api.example.com/v1/users/7?b=2&a=1",
                        "headers": [
                            {"name": "Authorization", "value": "Bearer token-001"},
                        ],
                        "queryString": [
                            {"name": "b", "value": "2"},
                            {"name": "a", "value": "1"},
                        ],
                    },
                    "response": {
                        "status": 200,
                        "content": {
                            "mimeType": "application/json",
                            "text": "{\"id\": 7, \"name\": \"Alice\"}",
                        },
                    },
                },
                {
                    "startedDateTime": "2026-04-09T10:00:04.000Z",
                    "request": {
                        "method": "GET",
                        "url": "https://api.example.com/v1/users/7?a=1&b=2",
                        "headers": [
                            {"name": "Authorization", "value": "Bearer token-001"},
                        ],
                        "queryString": [
                            {"name": "a", "value": "1"},
                            {"name": "b", "value": "2"},
                        ],
                    },
                    "response": {
                        "status": 200,
                        "content": {
                            "mimeType": "application/json",
                            "text": "{\"id\": 7, \"name\": \"Alice\"}",
                        },
                    },
                },
            ]
        }
    }


def test_drf_contract_imports_traffic_capture_into_reviewable_scenario_draft():
    """TC-V2-SVC-009/011 抓包导入接口应创建可审核场景草稿。"""
    client = APIClient()
    payload = {
        "capture_name": "登录后查询用户详情",
        "capture_payload": build_traffic_capture_payload(),
    }

    import_response = client.post("/api/v2/scenarios/import-traffic-capture/", payload, format="json")

    assert import_response.status_code == 201
    data = import_response.json()["data"]
    assert data["review_status"] == "pending"
    assert data["execution_status"] == "not_started"
    assert data["step_count"] == 2
    assert data["issue_count"] >= 1

    scenario_id = data["scenario_id"]
    detail_response = client.get(f"/api/v2/scenarios/{scenario_id}/")

    assert detail_response.status_code == 200
    detail = detail_response.json()["data"]
    assert len(detail["steps"]) == 2
    assert any(issue["issue_code"] == "capture_operation_needs_review" for issue in detail["issues"])

    review_response = client.post(
        f"/api/v2/scenarios/{scenario_id}/review/",
        {"review_status": "approved", "reviewer": "qa-owner", "review_comment": "进入人工确认"},
        format="json",
    )

    assert review_response.status_code == 200
    assert review_response.json()["data"]["review_status"] == "approved"
