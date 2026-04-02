"""模板渲染与规则校验测试。"""

import json

from platform_core.models import ApiModule, ApiOperation, ApiParam, AssertionCandidate, GenerationRecord
from platform_core.renderers import TemplateRenderer
from platform_core.rules import RuleValidator


def build_module() -> ApiModule:
    """构造标准模块样例。"""
    return ApiModule(
        module_id="mod-user",
        module_name="user",
        module_code="user",
        module_path_hint="generated/apis/user_api.py",
        module_type="api",
        module_desc="用户模块",
        source_ids=["src-openapi-001"],
        tags=["user"],
    )


def build_operation() -> ApiOperation:
    """构造标准接口操作样例。"""
    return ApiOperation(
        operation_id="op-get-user",
        module_id="mod-user",
        operation_name="获取用户详情",
        operation_code="get_user_profile",
        http_method="GET",
        path="/api/users/{user_id}",
        summary="获取用户详情",
        description="根据用户 ID 查询用户资料",
        tags=["user"],
        auth_type="session",
        path_params=[
            ApiParam(
                param_id="param-path-user-id",
                operation_id="op-get-user",
                param_name="user_id",
                param_in="path",
                data_type="string",
                required=True,
                source="openapi",
            )
        ],
        query_params=[
            ApiParam(
                param_id="param-query-verbose",
                operation_id="op-get-user",
                param_name="verbose",
                param_in="query",
                data_type="boolean",
                required=False,
                default_value=False,
                source="openapi",
            )
        ],
        success_codes=[200],
        source_ids=["src-openapi-001"],
    )


def build_list_operation() -> ApiOperation:
    """构造列表接口操作样例。"""
    return ApiOperation(
        operation_id="op-list-user",
        module_id="mod-user",
        operation_name="获取用户列表",
        operation_code="list_users",
        http_method="GET",
        path="/api/users",
        summary="获取用户列表",
        description="查询用户列表",
        tags=["user"],
        auth_type=None,
        success_codes=[200],
        source_ids=["src-openapi-001"],
    )


def build_assertions() -> list[AssertionCandidate]:
    """构造断言样例集合。"""
    return [
        AssertionCandidate(
            assertion_id="assert-status-001",
            operation_id="op-get-user",
            assertion_type="status_code",
            target_path="status_code",
            expected_value=200,
            priority="high",
            source="openapi",
            confidence_score=1.0,
            review_status="pending",
        ),
        AssertionCandidate(
            assertion_id="assert-json-001",
            operation_id="op-get-user",
            assertion_type="json_field_exists",
            target_path="data.id",
            expected_value=None,
            priority="medium",
            source="openapi",
            confidence_score=0.8,
            review_status="pending",
        ),
    ]


def test_api_template_renders_standard_api_module():
    """TC-V1-TPL-001 接口方法模板应生成统一代码骨架。"""
    renderer = TemplateRenderer()

    rendered = renderer.render_api_module(build_module(), [build_operation()])

    assert "from platform_core.runtime import ApiClient" in rendered
    assert "class UserApi:" in rendered
    assert "def get_user_profile(self, user_id, verbose=False):" in rendered
    assert 'return self.client.request("GET", path, params=query_params)' in rendered


def test_pytest_template_renders_basic_smoke_test():
    """TC-V1-TPL-002 pytest 模板应生成基础测试骨架。"""
    renderer = TemplateRenderer()

    rendered = renderer.render_test_module(build_module(), build_operation(), build_assertions())

    assert "import pytest" in rendered
    assert "from generated.apis.user_api import UserApi" in rendered
    assert "def test_get_user_profile_smoke(api):" in rendered
    assert 'assert response["status_code"] == 200' in rendered
    assert "# TODO: 补充业务断言" in rendered


def test_assertion_template_renders_unified_assertions():
    """TC-V1-TPL-003 断言模板应生成统一断言片段。"""
    renderer = TemplateRenderer()

    rendered = renderer.render_assertions(build_assertions())

    assert 'assert response["status_code"] == 200' in rendered
    assert 'assert _get_nested_value(body, "data.id") is not None' in rendered


def test_assertion_template_renders_schema_match():
    """TC-V1-TPL-003A 断言模板应生成 schema_match 断言片段。"""
    renderer = TemplateRenderer()
    assertions = [
        AssertionCandidate(
            assertion_id="assert-schema-001",
            operation_id="op-get-user",
            assertion_type="schema_match",
            target_path="data",
            expected_value={"type": "object", "required_fields": ["id", "name"]},
            priority="medium",
            source="openapi",
            confidence_score=0.8,
            review_status="pending",
        )
    ]

    rendered = renderer.render_assertions(assertions)

    assert 'schema_value = _get_nested_value(body, "data")' in rendered
    assert 'assert isinstance(schema_value, dict)' in rendered
    assert 'for required_field in ["id", "name"]:' in rendered


def test_assertion_template_renders_array_object_schema_match():
    """TC-V1-TPL-003B 断言模板应生成对象数组结构断言片段。"""
    renderer = TemplateRenderer()
    assertions = [
        AssertionCandidate(
            assertion_id="assert-schema-001",
            operation_id="op-list-user",
            assertion_type="schema_match",
            target_path="data",
            expected_value={"type": "array", "item_type": "object", "required_fields": ["id", "name"]},
            priority="medium",
            source="openapi",
            confidence_score=0.8,
            review_status="pending",
        )
    ]

    rendered = renderer.render_assertions(assertions)

    assert 'for schema_item in schema_value:' in rendered
    assert 'assert isinstance(schema_item, dict)' in rendered
    assert 'for required_field in ["id", "name"]:' in rendered


def test_assertion_template_renders_business_rule():
    """TC-V1-TPL-003C 断言模板应生成 business_rule 最小断言片段。"""
    renderer = TemplateRenderer()
    assertions = [
        AssertionCandidate(
            assertion_id="assert-business-001",
            operation_id="op-get-user",
            assertion_type="business_rule",
            target_path="data.name",
            expected_value={"rule_code": "non_empty_string"},
            priority="medium",
            source="manual",
            confidence_score=0.8,
            review_status="pending",
        )
    ]

    rendered = renderer.render_assertions(assertions)

    assert 'business_value = _get_nested_value(body, "data.name")' in rendered
    assert 'assert isinstance(business_value, str)' in rendered
    assert 'assert business_value.strip()' in rendered
    assert "non_empty_string" in rendered


def test_pytest_template_builds_fake_response_for_object_schema_assertions():
    """TC-V1-TPL-002A pytest 模板应生成满足对象断言的假响应。"""
    renderer = TemplateRenderer()
    assertions = build_assertions() + [
        AssertionCandidate(
            assertion_id="assert-schema-001",
            operation_id="op-get-user",
            assertion_type="schema_match",
            target_path="data",
            expected_value={"type": "object", "required_fields": ["id", "name"]},
            priority="medium",
            source="openapi",
            confidence_score=0.8,
            review_status="pending",
        )
    ]

    rendered = renderer.render_test_module(build_module(), build_operation(), assertions)

    assert '"name": "sample-name"' in rendered


def test_pytest_template_builds_fake_response_for_array_schema_assertions():
    """TC-V1-TPL-002B pytest 模板应生成满足数组断言的假响应。"""
    renderer = TemplateRenderer()
    assertions = [
        AssertionCandidate(
            assertion_id="assert-status-001",
            operation_id="op-list-user",
            assertion_type="status_code",
            target_path="status_code",
            expected_value=200,
            priority="high",
            source="openapi",
            confidence_score=1.0,
            review_status="pending",
        ),
        AssertionCandidate(
            assertion_id="assert-exists-001",
            operation_id="op-list-user",
            assertion_type="json_field_exists",
            target_path="data",
            expected_value=None,
            priority="medium",
            source="openapi",
            confidence_score=0.8,
            review_status="pending",
        ),
        AssertionCandidate(
            assertion_id="assert-schema-001",
            operation_id="op-list-user",
            assertion_type="schema_match",
            target_path="data",
            expected_value={"type": "array"},
            priority="medium",
            source="openapi",
            confidence_score=0.8,
            review_status="pending",
        ),
    ]

    rendered = renderer.render_test_module(build_module(), build_list_operation(), assertions)

    assert '"data": []' in rendered


def test_pytest_template_builds_fake_response_for_array_object_schema_assertions():
    """TC-V1-TPL-002C pytest 模板应生成满足对象数组断言的假响应。"""
    renderer = TemplateRenderer()
    assertions = [
        AssertionCandidate(
            assertion_id="assert-status-001",
            operation_id="op-list-user",
            assertion_type="status_code",
            target_path="status_code",
            expected_value=200,
            priority="high",
            source="openapi",
            confidence_score=1.0,
            review_status="pending",
        ),
        AssertionCandidate(
            assertion_id="assert-schema-001",
            operation_id="op-list-user",
            assertion_type="schema_match",
            target_path="data",
            expected_value={"type": "array", "item_type": "object", "required_fields": ["id", "name"]},
            priority="medium",
            source="openapi",
            confidence_score=0.8,
            review_status="pending",
        ),
    ]

    rendered = renderer.render_test_module(build_module(), build_list_operation(), assertions)

    assert '"data": [{"id": "sample-id", "name": "sample-name"}]' in rendered


def test_pytest_template_builds_fake_response_for_business_rule_assertions():
    """TC-V1-TPL-002D pytest 模板应生成满足 business_rule 的假响应。"""
    renderer = TemplateRenderer()
    assertions = [
        AssertionCandidate(
            assertion_id="assert-status-001",
            operation_id="op-get-user",
            assertion_type="status_code",
            target_path="status_code",
            expected_value=200,
            priority="high",
            source="manual",
            confidence_score=1.0,
            review_status="pending",
        ),
        AssertionCandidate(
            assertion_id="assert-business-001",
            operation_id="op-get-user",
            assertion_type="business_rule",
            target_path="data.name",
            expected_value={"rule_code": "non_empty_string"},
            priority="medium",
            source="manual",
            confidence_score=0.8,
            review_status="pending",
        ),
    ]

    rendered = renderer.render_test_module(build_module(), build_operation(), assertions)

    assert '"name": "sample-name"' in rendered


def test_generation_record_template_renders_traceable_json():
    """TC-V1-TPL-004 生成记录模板应生成最小记录结构。"""
    renderer = TemplateRenderer()
    record = GenerationRecord(
        generation_id="gen-001",
        generation_type="api_method",
        source_ids=["src-openapi-001"],
        target_asset_type="api_module",
        target_asset_path="generated/apis/user_api.py",
        generator_type="hybrid",
        generated_at="2026-03-30T10:30:00",
        generated_by="codex",
        generation_version="v1",
        template_reference="templates/api/api_module.py.j2",
        review_status="pending",
        execution_status="not_run",
    )

    rendered = renderer.render_generation_record(record)
    payload = json.loads(rendered)

    assert payload["source_ids"] == ["src-openapi-001"]
    assert payload["target_asset_path"].endswith("user_api.py")
    assert payload["review_status"] == "pending"


def test_rule_validator_rejects_invalid_operation_name():
    """TC-V1-RULE-001 接口方法命名不符合规范时应被识别。"""
    validator = RuleValidator()
    invalid_operation = build_operation().model_copy(update={"operation_code": "GetUserProfile"})

    violations = validator.validate_operation(invalid_operation)

    assert any("operation_code" in violation for violation in violations)


def test_rule_validator_rejects_invalid_test_file_name():
    """TC-V1-RULE-002 测试文件命名不符合规范时应被识别。"""
    validator = RuleValidator()

    violations = validator.validate_test_file_name("user_profile.py")

    assert violations
    assert "test_*.py" in violations[0]


def test_rule_validator_rejects_missing_module_assignment():
    """TC-V1-RULE-003 模块归类缺失时应被识别。"""
    validator = RuleValidator()
    invalid_operation = build_operation().model_copy(update={"module_id": ""})

    violations = validator.validate_operation(invalid_operation)

    assert any("module_id" in violation for violation in violations)


def test_rule_validator_rejects_missing_required_fields():
    """TC-V1-RULE-004 接口核心字段缺失时应被识别。"""
    validator = RuleValidator()
    invalid_operation = build_operation().model_copy(update={"http_method": "", "path": ""})

    violations = validator.validate_operation(invalid_operation)

    assert any("http_method" in violation for violation in violations)
    assert any("path" in violation for violation in violations)


def test_rule_validator_no_longer_exposes_private_site_specific_rules():
    """规则校验器不应再暴露旧私有站点专用规则入口。"""
    validator = RuleValidator()

    assert not hasattr(validator, "validate_existing_api_module")
    assert not hasattr(validator, "validate_existing_api_operation")
    assert not hasattr(validator, "validate_existing_api_inventory")
