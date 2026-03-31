import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

import pytest

from api_test.legacy_api_catalog import LegacyApiOperation
from platform_core.legacy_assets import LegacyPublicApiCatalogAdapter
from platform_core.models import ApiOperation, AssetManifest, AssertionCandidate, GenerationRecord
from platform_core.parsers import OpenAPIDocumentParser
from platform_core.pipeline import DocumentDrivenPipeline
from platform_core.renderers import TemplateRenderer
from platform_core.rules import RuleValidator
from platform_core.services import PlatformApplicationService


def build_openapi_spec() -> dict:
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


def build_operation() -> ApiOperation:
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


class InvalidLegacyPublicApiCatalogAdapter(LegacyPublicApiCatalogAdapter):
    @staticmethod
    def _load_catalog():
        return {
            "invalid_legacy_operation": LegacyApiOperation(
                operation_name="非法旧接口",
                operation_code="invalid_legacy_operation",
                module_code="UserManagement",
                path_template="/api/legacy/invalid",
                http_method="POST",
                payload_mode="json",
                requires_private_env=True,
                response_mode="binary",
                description="故意构造的非法旧接口目录，用于校验规则层。",
            )
        }


def test_parser_creates_json_field_equals_assertion_from_response_examples(tmp_path):
    source_path = tmp_path / "user_openapi.json"
    source_path.write_text(json.dumps(build_openapi_spec(), ensure_ascii=False, indent=2), encoding="utf-8")

    parsed = OpenAPIDocumentParser().parse(source_path)

    equals_assertions = [assertion for assertion in parsed.assertions if assertion.assertion_type == "json_field_equals"]
    assert len(equals_assertions) == 1
    assert equals_assertions[0].target_path == "code"
    assert equals_assertions[0].expected_value == 0


def test_assertion_template_renders_json_field_equals():
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


def test_rule_validator_rejects_asset_manifest_without_assets_and_generation_links():
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
    assert any(asset.operation_code == "get_user_profile" for asset in inspection.assets)
    assert inspection.missing_assets == []
    assert inspection.digest_mismatches == []
    assert inspection.report_exists is True


def test_platform_application_service_reports_missing_assets_in_workspace(tmp_path):
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


def test_platform_core_cli_can_inspect_workspace_manifest(tmp_path):
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
    assert any(asset["operation_code"] == "get_user_profile" for asset in payload["assets"])
    assert payload["report_exists"] is True


def test_platform_application_service_blocks_future_routes_in_v1(tmp_path):
    service = PlatformApplicationService(project_root=Path.cwd())

    assert service.supported_routes()["document"] is True
    assert service.supported_routes()["functional_case"] is False
    assert service.supported_routes()["traffic_capture"] is False

    with pytest.raises(NotImplementedError, match="V1 仅支持文档驱动最小闭环"):
        service.run_functional_case_pipeline(source_path=tmp_path / "cases.md", output_root=tmp_path / "out")

    with pytest.raises(NotImplementedError, match="V1 仅支持文档驱动最小闭环"):
        service.run_traffic_capture_pipeline(source_path=tmp_path / "capture.har", output_root=tmp_path / "out")


def test_platform_application_service_can_inspect_legacy_public_api_catalog():
    service = PlatformApplicationService(project_root=Path.cwd())

    inventory = service.inspect_legacy_public_api_catalog()

    assert inventory.source_document.source_type == "existing_api_asset"
    assert inventory.validation_status == "valid"
    assert inventory.validation_errors == []
    assert inventory.module_count >= 4
    assert inventory.operation_count >= 8
    assert inventory.private_env_operation_count == inventory.operation_count
    assert any(module.module_code == "user_management" for module in inventory.modules)
    invite_operation = next(operation for operation in inventory.operations if operation.operation_code == "invite_user")
    assert invite_operation.http_method == "POST"
    assert invite_operation.metadata["requires_private_env"] is True


def test_platform_core_cli_can_inspect_legacy_public_api_catalog():
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "platform_core.cli",
            "inspect-legacy-public-api",
        ],
        cwd=Path.cwd(),
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["source_document"]["source_type"] == "existing_api_asset"
    assert payload["validation_status"] == "valid"
    assert payload["validation_errors"] == []
    assert payload["module_count"] >= 4
    assert payload["operation_count"] >= 8
    assert any(operation["operation_code"] == "invite_user" for operation in payload["operations"])


def test_platform_application_service_can_snapshot_legacy_public_api_catalog(tmp_path):
    output_root = tmp_path / "legacy-workspace"
    service = PlatformApplicationService(project_root=Path.cwd())

    result = service.snapshot_legacy_public_api_catalog(output_root=output_root)
    inspection = service.inspect_workspace(output_root)

    assert result.source_document.source_type == "existing_api_asset"
    assert result.execution_record.execution_level == "structure_check"
    assert result.execution_record.result_status == "passed"
    assert Path(result.execution_record.report_path).exists()
    assert Path(result.asset_manifest_path).exists()
    assert len(result.modules) >= 4
    assert len(result.operations) >= 8
    assert len(result.asset_manifest.assets) == len(result.modules)
    assert all(asset.asset_type == "api_module" for asset in result.asset_manifest.assets)
    assert any(key.startswith("api::legacy::") for key in result.generated_paths)
    assert inspection.validation_status == "valid"
    assert inspection.asset_count == len(result.modules)
    report_payload = json.loads(Path(result.execution_record.report_path).read_text(encoding="utf-8"))
    assert report_payload["validation_status"] == "valid"
    assert report_payload["validation_errors"] == []


def test_platform_core_cli_can_snapshot_legacy_public_api_catalog(tmp_path):
    output_root = tmp_path / "legacy-cli-workspace"

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "platform_core.cli",
            "snapshot-legacy-public-api",
            "--output",
            str(output_root),
        ],
        cwd=Path.cwd(),
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    payload = json.loads(result.stdout)
    assert payload["source_type"] == "existing_api_asset"
    assert payload["execution_status"] == "passed"
    assert payload["module_count"] >= 4
    assert payload["operation_count"] >= 8
    assert Path(payload["asset_manifest_path"]).exists()


def test_platform_application_service_rejects_invalid_legacy_public_api_catalog_snapshot(tmp_path):
    service = PlatformApplicationService(
        project_root=Path.cwd(),
        legacy_catalog_adapter=InvalidLegacyPublicApiCatalogAdapter(),
    )

    inventory = service.inspect_legacy_public_api_catalog()

    assert inventory.validation_status == "invalid"
    assert any("module_code" in violation for violation in inventory.validation_errors)
    assert any("response_mode" in violation for violation in inventory.validation_errors)

    with pytest.raises(ValueError, match="module_code|response_mode"):
        service.snapshot_legacy_public_api_catalog(output_root=tmp_path / "invalid-legacy-workspace")
