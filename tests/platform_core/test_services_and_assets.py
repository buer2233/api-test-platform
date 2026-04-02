"""资产清单与应用服务测试。"""

import json
import subprocess
import sys
from argparse import ArgumentParser, _SubParsersAction
from datetime import datetime
from pathlib import Path

import pytest

from platform_core.cli import build_parser
from platform_core.models import (
    ApiOperation,
    AssetManifest,
    AssertionCandidate,
    DocumentPipelineRunSummary,
    GenerationRecord,
)
from platform_core.parsers import OpenAPIDocumentParser
from platform_core.pipeline import DocumentDrivenPipeline
from platform_core.renderers import TemplateRenderer
from platform_core.rules import RuleValidator
from platform_core.services import PlatformApplicationService


def build_openapi_spec() -> dict:
    """构造资产与服务测试使用的 OpenAPI 样例。"""
    return {
        "openapi": "3.0.0",
        "info": {"title": "User API", "version": "1.0.0"},
        "paths": {
            "/api/users/{user_id}": {
                "get": {
                    "tags": ["user"],
                    "operationId": "getUserProfile",
                    "summary": "获取用户详情",
                    "parameters": [
                        {
                            "name": "user_id",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string"},
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "success",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "code": {"type": "integer", "example": 0},
                                            "data": {
                                                "type": "object",
                                                "properties": {
                                                    "id": {"type": "string", "example": "u-100"},
                                                    "name": {"type": "string", "example": "Alice"},
                                                },
                                            },
                                        },
                                    }
                                }
                            },
                        }
                    },
                }
            }
        },
    }


def build_array_object_openapi_spec() -> dict:
    """构造对象数组响应结构的 OpenAPI 样例。"""
    return {
        "openapi": "3.0.0",
        "info": {"title": "User API", "version": "1.0.0"},
        "paths": {
            "/api/users": {
                "get": {
                    "tags": ["user"],
                    "operationId": "listUsers",
                    "summary": "获取用户列表",
                    "responses": {
                        "200": {
                            "description": "success",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "data": {
                                                "type": "array",
                                                "items": {
                                                    "type": "object",
                                                    "properties": {
                                                        "id": {"type": "string", "example": "u-100"},
                                                        "name": {"type": "string", "example": "Alice"},
                                                    },
                                                },
                                            }
                                        },
                                    }
                                }
                            },
                        }
                    },
                }
            }
        },
    }


def build_operation() -> ApiOperation:
    """构造规则测试使用的最小接口对象。"""
    return ApiOperation(
        operation_id="op-get-user",
        module_id="mod-user",
        operation_name="获取用户详情",
        operation_code="get_user_profile",
        http_method="GET",
        path="/api/users/{user_id}",
        success_codes=[200],
        source_ids=["src-openapi-001"],
    )


def test_parser_creates_json_field_equals_assertion_from_response_examples(tmp_path):
    """解析器应从响应示例中生成 json_field_equals 断言。"""
    source_path = tmp_path / "user_openapi.json"
    source_path.write_text(json.dumps(build_openapi_spec(), ensure_ascii=False, indent=2), encoding="utf-8")

    parsed = OpenAPIDocumentParser().parse(source_path)

    equals_assertions = [assertion for assertion in parsed.assertions if assertion.assertion_type == "json_field_equals"]
    assert len(equals_assertions) == 1
    assert equals_assertions[0].target_path == "code"
    assert equals_assertions[0].expected_value == 0


def test_parser_creates_schema_match_assertion_from_object_response(tmp_path):
    """解析器应从对象响应结构中生成 schema_match 断言。"""
    source_path = tmp_path / "user_openapi.json"
    source_path.write_text(json.dumps(build_openapi_spec(), ensure_ascii=False, indent=2), encoding="utf-8")

    parsed = OpenAPIDocumentParser().parse(source_path)

    schema_assertions = [assertion for assertion in parsed.assertions if assertion.assertion_type == "schema_match"]
    assert len(schema_assertions) == 1
    assert schema_assertions[0].target_path == "data"
    assert schema_assertions[0].expected_value["type"] == "object"
    assert schema_assertions[0].expected_value["required_fields"] == ["id", "name"]


def test_parser_creates_schema_match_assertion_from_array_object_response(tmp_path):
    """解析器应从对象数组响应结构中生成增强版 schema_match 断言。"""
    source_path = tmp_path / "user_array_openapi.json"
    source_path.write_text(json.dumps(build_array_object_openapi_spec(), ensure_ascii=False, indent=2), encoding="utf-8")

    parsed = OpenAPIDocumentParser().parse(source_path)

    schema_assertions = [assertion for assertion in parsed.assertions if assertion.assertion_type == "schema_match"]
    assert len(schema_assertions) == 1
    assert schema_assertions[0].target_path == "data"
    assert schema_assertions[0].expected_value["type"] == "array"
    assert schema_assertions[0].expected_value["item_type"] == "object"
    assert schema_assertions[0].expected_value["required_fields"] == ["id", "name"]


def test_assertion_template_renders_json_field_equals():
    """断言模板应正确渲染 json_field_equals 断言。"""
    renderer = TemplateRenderer()
    assertions = [
        AssertionCandidate(
            assertion_id="assert-json-equals-001",
            operation_id="op-get-user",
            assertion_type="json_field_equals",
            target_path="code",
            expected_value=0,
            priority="medium",
            source="openapi",
            confidence_score=0.9,
            review_status="pending",
        )
    ]

    rendered = renderer.render_assertions(assertions)

    assert 'assert _get_nested_value(body, "code") == 0' in rendered


def test_rule_validator_rejects_ai_generation_without_prompt_reference():
    """AI 辅助生成记录缺少 prompt_reference 时应被拦截。"""
    validator = RuleValidator()
    record = GenerationRecord(
        generation_id="gen-ai-001",
        generation_type="test_case",
        source_ids=["src-openapi-001"],
        target_asset_type="test_case",
        target_asset_path="generated/tests/test_get_user_profile.py",
        generator_type="ai_assisted",
        generated_at=datetime(2026, 3, 31, 11, 30, 0),
        generated_by="codex",
        generation_version="v1",
        template_reference="templates/tests/test_module.py.j2",
        review_status="pending",
        execution_status="not_run",
    )

    violations = validator.validate_generation_record(record)

    assert any("prompt_reference" in violation for violation in violations)


def test_rule_validator_requires_status_code_assertion_for_executable_operation():
    """可执行接口缺少状态码断言时应被拦截。"""
    validator = RuleValidator()
    assertions = [
        AssertionCandidate(
            assertion_id="assert-json-exists-001",
            operation_id="op-get-user",
            assertion_type="json_field_exists",
            target_path="data.id",
            expected_value=None,
            priority="medium",
            source="openapi",
            confidence_score=0.8,
            review_status="pending",
        )
    ]

    violations = validator.validate_assertions(build_operation(), assertions)

    assert any("status_code" in violation for violation in violations)


def test_rule_validator_rejects_invalid_schema_match_assertion():
    """非法 schema_match 断言结构应被拦截。"""
    validator = RuleValidator()
    assertions = [
        AssertionCandidate(
            assertion_id="assert-schema-001",
            operation_id="op-get-user",
            assertion_type="schema_match",
            target_path="data",
            expected_value={"required_fields": ["id"]},
            priority="medium",
            source="openapi",
            confidence_score=0.7,
            review_status="pending",
        ),
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
    ]

    violations = validator.validate_assertions(build_operation(), assertions)

    assert any("schema_match" in violation for violation in violations)


def test_rule_validator_rejects_invalid_array_object_schema_match_assertion():
    """对象数组 schema_match 的非法 item_type 应被拦截。"""
    validator = RuleValidator()
    assertions = [
        AssertionCandidate(
            assertion_id="assert-schema-001",
            operation_id="op-get-user",
            assertion_type="schema_match",
            target_path="data",
            expected_value={"type": "array", "item_type": "unsupported", "required_fields": ["id"]},
            priority="medium",
            source="openapi",
            confidence_score=0.7,
            review_status="pending",
        ),
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
    ]

    violations = validator.validate_assertions(build_operation(), assertions)

    assert any("schema_match.item_type" in violation for violation in violations)


def test_rule_validator_rejects_asset_manifest_without_assets_and_generation_links():
    """资产清单缺少关键字段时应被拦截。"""
    validator = RuleValidator()
    manifest = AssetManifest(
        manifest_id="manifest-001",
        source_id="src-openapi-001",
        source_type="openapi",
        source_digest="a" * 64,
        generated_at=datetime(2026, 3, 31, 12, 0, 0),
        workspace_root="D:/AI/api-test-platform/workspace",
        assets=[],
        generation_ids=[],
        execution_id=None,
        report_path=None,
    )

    violations = validator.validate_asset_manifest(manifest)

    assert any("assets" in violation for violation in violations)
    assert any("generation_ids" in violation for violation in violations)
    assert any("execution_id" in violation for violation in violations)


def test_document_pipeline_persists_asset_manifest_with_hashes(tmp_path):
    """流水线应落盘带摘要的资产清单。"""
    source_path = tmp_path / "user_openapi.json"
    source_path.write_text(json.dumps(build_openapi_spec(), ensure_ascii=False, indent=2), encoding="utf-8")

    output_root = tmp_path / "workspace"
    pipeline = DocumentDrivenPipeline(project_root=Path.cwd())

    result = pipeline.run(source_path=source_path, output_root=output_root)

    manifest_path = output_root / "generated" / "records" / "asset_manifest.json"
    assert manifest_path.exists()
    assert result.asset_manifest_path == str(manifest_path)
    assert result.asset_manifest.source_id == result.source_document.source_id
    assert len(result.asset_manifest.source_digest) == 64
    assert {asset.asset_type for asset in result.asset_manifest.assets} == {"api_module", "test_case"}
    assert any(asset.operation_code == "get_user_profile" for asset in result.asset_manifest.assets)
    assert all(len(asset.content_digest) == 64 for asset in result.asset_manifest.assets)
    assert result.asset_manifest.execution_id == result.execution_record.execution_id


def test_platform_application_service_can_inspect_generated_workspace(tmp_path):
    """应用服务应能检查已生成工作区。"""
    source_path = tmp_path / "user_openapi.json"
    source_path.write_text(json.dumps(build_openapi_spec(), ensure_ascii=False, indent=2), encoding="utf-8")
    output_root = tmp_path / "workspace"

    pipeline = DocumentDrivenPipeline(project_root=Path.cwd())
    pipeline.run(source_path=source_path, output_root=output_root)

    service = PlatformApplicationService(project_root=Path.cwd())
    inspection = service.inspect_workspace(output_root)

    assert inspection.validation_status == "valid"
    assert inspection.asset_count == 2
    assert inspection.generation_count == 2
    assert len(inspection.assets) == 2
    assert len(inspection.generation_records) == 2
    assert any(asset.operation_code == "get_user_profile" for asset in inspection.assets)
    assert any(record.operation_code == "get_user_profile" for record in inspection.generation_records)
    assert inspection.missing_assets == []
    assert inspection.missing_generation_records == []
    assert inspection.digest_mismatches == []
    assert inspection.report_exists is True


def test_platform_application_service_describes_v1_capabilities():
    """应用服务应输出可直接消费的能力快照。"""
    service = PlatformApplicationService(project_root=Path.cwd())

    snapshot = service.describe_capabilities()
    routes = {route.route_code: route for route in snapshot.routes}

    assert snapshot.service_stage == "v1"
    assert snapshot.local_mode_only is True
    assert snapshot.available_commands == ["run", "inspect"]
    assert routes["document"].enabled is True
    assert routes["document"].stage == "v1_active"
    assert routes["functional_case"].enabled is False
    assert routes["traffic_capture"].enabled is False
    assert "V1" in routes["functional_case"].detail


def test_platform_application_service_returns_document_pipeline_summary(tmp_path):
    """应用服务应直接返回稳定的文档驱动运行摘要。"""
    source_path = tmp_path / "user_openapi.json"
    source_path.write_text(json.dumps(build_openapi_spec(), ensure_ascii=False, indent=2), encoding="utf-8")
    output_root = tmp_path / "workspace"

    service = PlatformApplicationService(project_root=Path.cwd())
    summary = service.run_document_pipeline_summary(source_path=source_path, output_root=output_root)

    assert isinstance(summary, DocumentPipelineRunSummary)
    assert summary.route_code == "document"
    assert summary.service_stage == "v1"
    assert summary.workspace_root == str(output_root)
    assert summary.modules == 1
    assert summary.operations == 1
    assert summary.generation_count == 2
    assert summary.asset_count == 2
    assert summary.execution_target == "generated-suite"
    assert summary.execution_status == "passed"
    assert summary.execution_exit_code == 0
    assert summary.total_count == 1
    assert summary.passed_count == 1


def test_platform_application_service_reports_missing_assets_in_workspace(tmp_path):
    """应用服务应能识别工作区中缺失的生成文件。"""
    source_path = tmp_path / "user_openapi.json"
    source_path.write_text(json.dumps(build_openapi_spec(), ensure_ascii=False, indent=2), encoding="utf-8")
    output_root = tmp_path / "workspace"

    pipeline = DocumentDrivenPipeline(project_root=Path.cwd())
    result = pipeline.run(source_path=source_path, output_root=output_root)
    Path(result.generated_paths["test::get_user_profile"]).unlink()

    service = PlatformApplicationService(project_root=Path.cwd())
    inspection = service.inspect_workspace(output_root)

    assert inspection.validation_status == "invalid"
    assert len(inspection.missing_assets) == 1
    assert inspection.missing_assets[0].endswith("test_get_user_profile.py")


def test_platform_application_service_reports_missing_generation_records(tmp_path):
    """应用服务应能识别工作区中缺失的生成记录文件。"""
    source_path = tmp_path / "user_openapi.json"
    source_path.write_text(json.dumps(build_openapi_spec(), ensure_ascii=False, indent=2), encoding="utf-8")
    output_root = tmp_path / "workspace"

    pipeline = DocumentDrivenPipeline(project_root=Path.cwd())
    pipeline.run(source_path=source_path, output_root=output_root)
    generation_record_path = next((output_root / "generated" / "records").glob("gen-*.json"))
    generation_record_path.unlink()

    service = PlatformApplicationService(project_root=Path.cwd())
    inspection = service.inspect_workspace(output_root)

    assert inspection.validation_status == "invalid"
    assert len(inspection.missing_generation_records) == 1
    assert inspection.missing_generation_records[0].endswith(".json")


def test_platform_core_cli_can_inspect_workspace_manifest(tmp_path):
    """CLI 应支持检查工作区资产清单。"""
    source_path = tmp_path / "user_openapi.json"
    source_path.write_text(json.dumps(build_openapi_spec(), ensure_ascii=False, indent=2), encoding="utf-8")
    output_root = tmp_path / "workspace"

    pipeline = DocumentDrivenPipeline(project_root=Path.cwd())
    pipeline.run(source_path=source_path, output_root=output_root)

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "platform_core.cli",
            "inspect",
            "--workspace",
            str(output_root),
        ],
        cwd=Path.cwd(),
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["validation_status"] == "valid"
    assert payload["asset_count"] == 2
    assert payload["generation_count"] == 2
    assert len(payload["assets"]) == 2
    assert len(payload["generation_records"]) == 2
    assert any(asset["operation_code"] == "get_user_profile" for asset in payload["assets"])
    assert any(record["operation_code"] == "get_user_profile" for record in payload["generation_records"])
    assert payload["missing_generation_records"] == []
    assert payload["report_exists"] is True


def test_platform_application_service_blocks_future_routes_in_v1(tmp_path):
    """应用服务应显式阻断 V1 尚未开放的路线。"""
    service = PlatformApplicationService(project_root=Path.cwd())

    assert service.supported_routes()["document"] is True
    assert service.supported_routes()["functional_case"] is False
    assert service.supported_routes()["traffic_capture"] is False

    with pytest.raises(NotImplementedError, match="V1 仅支持文档驱动最小闭环"):
        service.run_functional_case_pipeline(source_path=tmp_path / "cases.md", output_root=tmp_path / "out")

    with pytest.raises(NotImplementedError, match="V1 仅支持文档驱动最小闭环"):
        service.run_traffic_capture_pipeline(source_path=tmp_path / "capture.har", output_root=tmp_path / "out")


def test_platform_application_service_no_longer_exposes_legacy_catalog_methods():
    """应用服务不应再暴露旧 PublicAPI 目录桥接方法。"""
    service = PlatformApplicationService(project_root=Path.cwd())

    assert not hasattr(service, "inspect_legacy_public_api_catalog")
    assert not hasattr(service, "snapshot_legacy_public_api_catalog")


def test_platform_core_cli_no_longer_registers_legacy_catalog_commands():
    """CLI 不应再注册旧目录检查和快照命令。"""
    parser = build_parser()
    subparsers = [action for action in parser._actions if isinstance(action, _SubParsersAction)]

    assert len(subparsers) == 1
    commands = set(subparsers[0].choices)
    assert "inspect-legacy-public-api" not in commands
    assert "snapshot-legacy-public-api" not in commands

    with pytest.raises(SystemExit):
        parser.parse_args(["inspect-legacy-public-api"])

    with pytest.raises(SystemExit):
        parser.parse_args(["snapshot-legacy-public-api", "--output", "workspace"])
