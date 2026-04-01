"""平台核心模型测试。"""

from datetime import datetime

from platform_core.models import (
    ApiModule,
    ApiOperation,
    ApiParam,
    AssertionCandidate,
    ExecutionRecord,
    GenerationRecord,
    ResponseField,
    SourceDocument,
)


def test_source_document_records_openapi_origin():
    """TC-V1-MODEL-001 SourceDocument 应记录文档来源信息。"""
    imported_at = datetime(2026, 3, 30, 9, 0, 0)

    source = SourceDocument(
        source_id="src-openapi-001",
        source_type="openapi",
        source_name="user-openapi",
        source_path="fixtures/user_openapi.json",
        source_version="1.0.0",
        source_summary="用户接口文档",
        imported_at=imported_at,
        imported_by="codex",
        raw_reference="file://fixtures/user_openapi.json",
    )

    assert source.source_id == "src-openapi-001"
    assert source.source_type == "openapi"
    assert source.source_path.endswith("user_openapi.json")
    assert source.imported_at == imported_at


def test_source_document_records_existing_api_asset_origin():
    """TC-V1-MODEL-001A SourceDocument 应记录既有接口资产来源。"""
    imported_at = datetime(2026, 3, 31, 20, 0, 0)

    source = SourceDocument(
        source_id="src-existing-public-api",
        source_type="existing_api_asset",
        source_name="api_test_public_api",
        source_path="api_test/core/public_api.py",
        source_version="v1-legacy-catalog",
        source_summary="旧接口目录快照",
        imported_at=imported_at,
        imported_by="platform_core",
        raw_reference="api_test.legacy_api_catalog:PUBLIC_API_OPERATION_CATALOG",
    )

    assert source.source_type == "existing_api_asset"
    assert source.source_path.endswith("public_api.py")


def test_api_module_captures_module_ownership():
    """TC-V1-MODEL-002 ApiModule 应表达模块归属。"""
    module = ApiModule(
        module_id="mod-user",
        module_name="user",
        module_code="user",
        module_path_hint="generated/apis/user_api.py",
        module_type="api",
        module_desc="用户模块",
        source_ids=["src-openapi-001"],
        tags=["user"],
    )

    assert module.module_name == "user"
    assert module.module_type == "api"
    assert module.module_path_hint.endswith("user_api.py")


def test_api_operation_captures_core_definition():
    """TC-V1-MODEL-003 ApiOperation 应表达接口核心定义。"""
    operation = ApiOperation(
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
        success_codes=[200],
        source_ids=["src-openapi-001"],
    )

    assert operation.http_method == "GET"
    assert operation.path == "/api/users/{user_id}"
    assert operation.operation_code == "get_user_profile"
    assert operation.success_codes == [200]


def test_api_param_supports_multiple_locations():
    """TC-V1-MODEL-004 ApiParam 应覆盖 header/query/path/body 参数位置。"""
    params = [
        ApiParam(
            param_id="param-header-auth",
            operation_id="op-create-user",
            param_name="Authorization",
            param_in="header",
            data_type="string",
            required=True,
            example_value="Bearer demo",
            source="openapi",
        ),
        ApiParam(
            param_id="param-query-verbose",
            operation_id="op-create-user",
            param_name="verbose",
            param_in="query",
            data_type="boolean",
            required=False,
            default_value=False,
            source="openapi",
        ),
        ApiParam(
            param_id="param-path-user-id",
            operation_id="op-create-user",
            param_name="user_id",
            param_in="path",
            data_type="string",
            required=True,
            source="openapi",
        ),
        ApiParam(
            param_id="param-body-name",
            operation_id="op-create-user",
            param_name="name",
            param_in="body",
            data_type="string",
            required=True,
            example_value="Alice",
            source="openapi",
        ),
    ]

    assert {param.param_in for param in params} == {"header", "query", "path", "body"}
    assert params[0].required is True
    assert params[1].default_value is False


def test_response_field_marks_assertion_candidates():
    """TC-V1-MODEL-005 ResponseField 应表达断言和变量提取来源。"""
    field = ResponseField(
        field_id="field-user-id",
        operation_id="op-get-user",
        status_code=200,
        field_path="data.id",
        field_name="id",
        data_type="string",
        required=True,
        example_value="u-100",
        desc="用户 ID",
        can_extract_as_variable=True,
        can_assert=True,
    )

    assert field.field_path == "data.id"
    assert field.can_extract_as_variable is True
    assert field.can_assert is True


def test_generation_record_captures_minimum_traceability():
    """TC-V1-MODEL-006 GenerationRecord 应记录最小生成元数据。"""
    generated_at = datetime(2026, 3, 30, 10, 30, 0)

    record = GenerationRecord(
        generation_id="gen-001",
        generation_type="api_method",
        source_ids=["src-openapi-001"],
        target_asset_type="api_module",
        target_asset_path="generated/apis/user_api.py",
        generator_type="hybrid",
        generated_at=generated_at,
        generated_by="codex",
        generation_version="v1",
        template_reference="templates/api/api_module.py.j2",
        review_status="pending",
        execution_status="not_run",
    )

    assert record.generated_at == generated_at
    assert record.target_asset_path.endswith("user_api.py")
    assert record.generator_type == "hybrid"


def test_execution_record_captures_minimum_execution_traceability():
    """TC-V1-MODEL-007 ExecutionRecord 应记录最小执行信息。"""
    started_at = datetime(2026, 3, 30, 10, 35, 0)
    ended_at = datetime(2026, 3, 30, 10, 35, 8)

    record = ExecutionRecord(
        execution_id="exec-001",
        target_type="test_case",
        target_id="test-get-user-smoke",
        execution_level="smoke",
        started_at=started_at,
        ended_at=ended_at,
        result_status="passed",
        report_path="generated/reports/junit.xml",
        error_summary="",
        environment="local",
    )

    assert record.execution_level == "smoke"
    assert record.result_status == "passed"
    assert record.report_path.endswith("junit.xml")


def test_assertion_candidate_keeps_expected_target():
    """模板与集成测试会复用 AssertionCandidate。"""
    candidate = AssertionCandidate(
        assertion_id="assert-status-001",
        operation_id="op-get-user",
        assertion_type="status_code",
        target_path="status_code",
        expected_value=200,
        priority="high",
        source="openapi",
        confidence_score=1.0,
        review_status="pending",
    )

    assert candidate.assertion_type == "status_code"
    assert candidate.expected_value == 200
