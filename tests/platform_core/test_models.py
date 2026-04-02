"""平台核心模型测试。"""

from datetime import datetime

from platform_core.models import (
    ApiModule,
    ApiOperation,
    ApiParam,
    AssertionCandidate,
    DocumentPipelineRunSummary,
    ExecutionRecord,
    GenerationRecord,
    ResponseField,
    RouteCapabilitySummary,
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
    """TC-V1-MODEL-001A SourceDocument 应记录通用既有资产来源。"""
    imported_at = datetime(2026, 3, 31, 20, 0, 0)

    source = SourceDocument(
        source_id="src-existing-api-module",
        source_type="existing_api_asset",
        source_name="existing-user-api-module",
        source_path="workspace/existing_assets/user_api_module.json",
        source_version="v1-existing-asset",
        source_summary="由既有接口资产导入的模块快照",
        imported_at=imported_at,
        imported_by="platform_core",
        raw_reference="workspace://existing-assets/user_api_module.json",
    )

    assert source.source_type == "existing_api_asset"
    assert source.source_path.endswith("user_api_module.json")


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


def test_generation_record_captures_extended_traceability_fields():
    """TC-V1-MODEL-006A GenerationRecord 应记录资产归属与内容摘要。"""
    generated_at = datetime(2026, 4, 1, 15, 0, 0)

    record = GenerationRecord(
        generation_id="gen-extended-001",
        generation_type="test_case",
        source_ids=["src-openapi-001"],
        target_asset_type="test_case",
        target_asset_path="generated/tests/test_get_user_profile.py",
        generator_type="hybrid",
        generated_at=generated_at,
        generated_by="codex",
        generation_version="v1",
        template_reference="templates/tests/test_module.py.j2",
        module_code="user",
        operation_code="get_user_profile",
        target_asset_digest="a" * 64,
        review_status="pending",
        execution_status="not_run",
    )

    assert record.module_code == "user"
    assert record.operation_code == "get_user_profile"
    assert record.target_asset_digest == "a" * 64


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
        command="python -m pytest generated/tests -v",
        exit_code=0,
        total_count=1,
        passed_count=1,
        failed_count=0,
        error_count=0,
        skipped_count=0,
    )

    assert record.execution_level == "smoke"
    assert record.result_status == "passed"
    assert record.report_path.endswith("junit.xml")
    assert record.command.startswith("python -m pytest")
    assert record.exit_code == 0
    assert record.total_count == 1
    assert record.passed_count == 1


def test_route_capability_summary_describes_v1_route_boundaries():
    """TC-V1-MODEL-008 RouteCapabilitySummary 应记录路线状态和阻断原因。"""
    capability = RouteCapabilitySummary(
        route_code="functional_case",
        enabled=False,
        stage="v1_blocked",
        detail="V1 仅支持文档驱动最小闭环，功能测试用例驱动留待后续阶段开放",
    )

    assert capability.route_code == "functional_case"
    assert capability.enabled is False
    assert capability.stage == "v1_blocked"
    assert "V1" in capability.detail


def test_document_pipeline_run_summary_captures_service_contract():
    """TC-V1-MODEL-009 DocumentPipelineRunSummary 应表达服务层稳定运行摘要。"""
    summary = DocumentPipelineRunSummary(
        route_code="document",
        service_stage="v1",
        source="user-openapi",
        source_id="src-openapi-001",
        workspace_root="D:/AI/api-test-platform/workspace",
        modules=1,
        operations=1,
        generation_count=2,
        asset_count=2,
        execution_target="generated-suite",
        execution_status="passed",
        execution_exit_code=0,
        total_count=1,
        passed_count=1,
        failed_count=0,
        error_count=0,
        skipped_count=0,
        report_path="generated/reports/generated-suite.xml",
        asset_manifest_path="generated/records/asset_manifest.json",
    )

    assert summary.route_code == "document"
    assert summary.service_stage == "v1"
    assert summary.workspace_root.endswith("workspace")
    assert summary.execution_target == "generated-suite"
    assert summary.execution_exit_code == 0


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
