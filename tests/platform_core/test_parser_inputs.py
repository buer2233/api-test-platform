"""解析器输入格式测试。"""

import json
from pathlib import Path

from platform_core.functional_cases import FunctionalCaseDraftParser
from platform_core.parsers import OpenAPIDocumentParser
from platform_core.traffic_capture import TrafficCaptureDraftParser


def test_parser_supports_yaml_openapi_documents(tmp_path):
    """解析器应支持 YAML 格式的 OpenAPI 文档。"""
    source_path = tmp_path / "user_openapi.yaml"
    source_path.write_text(
        """
openapi: 3.0.0
info:
  title: User API
  version: 1.0.0
paths:
  /api/users/{user_id}:
    get:
      tags: [user]
      operationId: getUserProfile
      summary: 获取用户详情
      parameters:
        - name: user_id
          in: path
          required: true
          schema:
            type: string
      responses:
        '200':
          description: success
          content:
            application/json:
              schema:
                type: object
                properties:
                  data:
                    type: object
                    properties:
                      id:
                        type: string
                        example: u-100
""".strip(),
        encoding="utf-8",
    )

    parsed = OpenAPIDocumentParser().parse(source_path)

    assert parsed.source_document.source_type == "openapi"
    assert len(parsed.operations) == 1
    assert parsed.operations[0].operation_code == "get_user_profile"


def test_parser_supports_yaml_swagger_documents_with_multiple_operations(tmp_path):
    """解析器应支持 Swagger YAML 并解析多个接口。"""
    source_path = tmp_path / "user_swagger.yml"
    source_path.write_text(
        """
swagger: '2.0'
info:
  title: User API
  version: 1.0.0
paths:
  /api/users:
    get:
      tags: [user]
      operationId: listUsers
      summary: 查询用户列表
      responses:
        '200':
          description: success
          schema:
            type: object
            properties:
              data:
                type: array
    post:
      tags: [user]
      operationId: createUser
      summary: 创建用户
      parameters:
        - name: body
          in: body
          required: true
          schema:
            type: object
            required: [name]
            properties:
              name:
                type: string
      responses:
        '201':
          description: created
          schema:
            type: object
            properties:
              data:
                type: object
                properties:
                  id:
                    type: string
""".strip(),
        encoding="utf-8",
    )

    parsed = OpenAPIDocumentParser().parse(source_path)

    assert parsed.source_document.source_type == "swagger"
    assert {operation.operation_code for operation in parsed.operations} == {"list_users", "create_user"}
    assert any(operation.http_method == "POST" for operation in parsed.operations)


def test_functional_case_parser_builds_scenario_draft_from_json(tmp_path):
    """TC-V2-PARSE-001/002/005/006 功能测试用例输入应能生成场景草稿。"""
    source_path = tmp_path / "functional_case.json"
    source_path.write_text(
        json.dumps(
            {
                "case_id": "fc-order-001",
                "case_code": "create_order_and_query_order_detail",
                "case_name": "创建订单后查询订单详情",
                "priority": "high",
                "preconditions": ["已完成登录"],
                "steps": [
                    {
                        "step_name": "创建订单",
                        "operation_id": "operation-create-order",
                        "expected": {
                            "status_code": 201,
                            "extract": {"order_id": "data.id"},
                        },
                    },
                    {
                        "step_name": "查询订单详情",
                        "operation_id": "operation-get-order",
                        "uses": {"order_id": "$scenario.order_id"},
                        "expected": {"status_code": 200},
                    },
                ],
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    draft = FunctionalCaseDraftParser().parse(source_path)

    assert draft.source_document.source_type == "functional_case"
    assert draft.scenario.scenario_code == "create_order_and_query_order_detail"
    assert [step.step_order for step in draft.steps] == [1, 2]
    assert draft.bindings[0].variable_name == "order_id"
    assert draft.bindings[0].target_operations == ["operation-get-order"]
    assert draft.dependencies[0].upstream_operation_id == "operation-create-order"
    assert draft.dependencies[0].downstream_operation_id == "operation-get-order"
    assert draft.lifecycle.review_status == "pending"
    assert draft.issues == []


def test_functional_case_parser_records_structured_issue_for_unresolved_step(tmp_path):
    """TC-V2-PARSE-004/008 歧义步骤应保留问题清单而不是直接确认为正式资产。"""
    source_path = tmp_path / "functional_case_invalid.json"
    source_path.write_text(
        json.dumps(
            {
                "case_id": "fc-order-002",
                "case_code": "query_order_without_operation",
                "case_name": "缺少操作绑定的场景",
                "steps": [
                    {
                        "step_name": "查询订单详情",
                        "expected": {"status_code": 200},
                    }
                ],
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    draft = FunctionalCaseDraftParser().parse(source_path)

    assert draft.scenario.review_status == "pending"
    assert len(draft.issues) == 1
    assert draft.issues[0].issue_code == "missing_operation_id"
    assert draft.issues[0].issue_message


def test_traffic_capture_parser_filters_noise_and_builds_reviewable_draft(tmp_path):
    """TC-V2-PARSE-009/010/011 抓包导入应完成清洗、去重和动态值候选提取。"""
    source_path = tmp_path / "traffic_capture.har.json"
    source_path.write_text(
        json.dumps(
            {
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
                            "startedDateTime": "2026-04-09T10:00:01.000Z",
                            "request": {
                                "method": "OPTIONS",
                                "url": "https://api.example.com/v1/users/7?b=2&a=1",
                                "queryString": [
                                    {"name": "b", "value": "2"},
                                    {"name": "a", "value": "1"},
                                ],
                            },
                            "response": {
                                "status": 204,
                                "content": {"mimeType": "text/plain"},
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
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    draft = TrafficCaptureDraftParser().parse(source_path)

    assert draft.source_document.source_type == "traffic_capture"
    assert draft.scenario.review_status == "pending"
    assert len(draft.steps) == 2
    assert [step.step_order for step in draft.steps] == [1, 2]
    assert draft.steps[1].metadata["raw_step"]["request"]["path_template"] == "/v1/users/{user_id}"
    assert draft.steps[1].metadata["raw_step"]["request"]["query_params"] == {"a": "1", "b": "2"}
    assert {binding.variable_name for binding in draft.bindings} >= {"token", "user_id"}
    assert any(
        dependency.upstream_operation_id == draft.steps[0].operation_id
        and dependency.downstream_operation_id == draft.steps[1].operation_id
        for dependency in draft.dependencies
    )
    assert {issue.issue_code for issue in draft.issues} >= {"capture_operation_needs_review"}
