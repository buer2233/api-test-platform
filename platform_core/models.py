from __future__ import annotations

from datetime import datetime
from typing import Any, Literal

from pydantic import BaseModel, ConfigDict, Field


class PlatformBaseModel(BaseModel):
    """平台模型基类，允许在 V1 逐步扩展 metadata。"""

    model_config = ConfigDict(extra="allow", populate_by_name=True)


class SourceDocument(PlatformBaseModel):
    source_id: str
    source_type: Literal[
        "openapi",
        "swagger",
        "markdown_doc",
        "functional_case",
        "traffic_capture",
        "manual_input",
    ]
    source_name: str
    source_path: str | None = None
    source_version: str | None = None
    source_summary: str | None = None
    imported_at: datetime
    imported_by: str | None = None
    raw_reference: str | None = None


class ApiParam(PlatformBaseModel):
    param_id: str
    operation_id: str
    param_name: str
    param_in: Literal["header", "path", "query", "body", "cookie"]
    data_type: str
    required: bool
    default_value: Any | None = None
    example_value: Any | None = None
    enum_values: list[Any] = Field(default_factory=list)
    desc: str | None = None
    source: str | None = None
    metadata: dict[str, Any] = Field(default_factory=dict)


class ResponseField(PlatformBaseModel):
    field_id: str
    operation_id: str
    status_code: int
    field_path: str
    field_name: str
    data_type: str
    required: bool
    example_value: Any | None = None
    desc: str | None = None
    can_extract_as_variable: bool = False
    can_assert: bool = False


class ApiModule(PlatformBaseModel):
    module_id: str
    module_name: str
    module_code: str
    module_path_hint: str | None = None
    module_type: Literal["api", "bs", "app", "common"] = "api"
    module_desc: str | None = None
    source_ids: list[str] = Field(default_factory=list)
    tags: list[str] = Field(default_factory=list)


class ApiOperation(PlatformBaseModel):
    operation_id: str
    module_id: str
    operation_name: str
    operation_code: str
    http_method: str
    path: str
    summary: str | None = None
    description: str | None = None
    tags: list[str] = Field(default_factory=list)
    auth_type: str | None = None
    request_headers: list[ApiParam] = Field(default_factory=list)
    path_params: list[ApiParam] = Field(default_factory=list)
    query_params: list[ApiParam] = Field(default_factory=list)
    body_params: list[ApiParam] = Field(default_factory=list)
    response_fields: list[ResponseField] = Field(default_factory=list)
    success_codes: list[int] = Field(default_factory=list)
    error_codes: list[int] = Field(default_factory=list)
    source_ids: list[str] = Field(default_factory=list)
    confidence_score: float = 1.0
    metadata: dict[str, Any] = Field(default_factory=dict)


class AssertionCandidate(PlatformBaseModel):
    assertion_id: str
    operation_id: str | None = None
    scenario_step_id: str | None = None
    assertion_type: Literal[
        "status_code",
        "json_field_equals",
        "json_field_exists",
        "schema_match",
        "business_rule",
    ]
    target_path: str
    expected_value: Any | None = None
    priority: Literal["high", "medium", "low"] = "medium"
    source: str | None = None
    confidence_score: float = 1.0
    review_status: Literal["pending", "approved", "rejected", "revised"] = "pending"


class GenerationRecord(PlatformBaseModel):
    generation_id: str
    generation_type: Literal["api_method", "test_case", "assertion", "scenario"]
    source_ids: list[str] = Field(default_factory=list)
    target_asset_type: str
    target_asset_path: str
    generator_type: Literal["rule_based", "ai_assisted", "hybrid"]
    generated_at: datetime
    generated_by: str
    generation_version: str | None = None
    prompt_reference: str | None = None
    template_reference: str | None = None
    review_status: Literal["pending", "approved", "rejected", "revised"] = "pending"
    execution_status: Literal["not_run", "passed", "failed"] = "not_run"


class AssetRecord(PlatformBaseModel):
    asset_id: str
    asset_type: Literal["api_module", "test_case"]
    asset_path: str
    generation_id: str
    module_code: str | None = None
    operation_code: str | None = None
    source_ids: list[str] = Field(default_factory=list)
    content_digest: str
    review_status: Literal["pending", "approved", "rejected", "revised"] = "pending"


class AssetInspectionEntry(PlatformBaseModel):
    asset_id: str
    asset_type: Literal["api_module", "test_case"]
    asset_path: str
    generation_id: str
    module_code: str | None = None
    operation_code: str | None = None
    source_ids: list[str] = Field(default_factory=list)
    review_status: Literal["pending", "approved", "rejected", "revised"] = "pending"


class AssetManifest(PlatformBaseModel):
    manifest_id: str
    source_id: str
    source_type: str
    source_digest: str
    generated_at: datetime
    workspace_root: str
    assets: list[AssetRecord] = Field(default_factory=list)
    generation_ids: list[str] = Field(default_factory=list)
    execution_id: str | None = None
    report_path: str | None = None


class AssetInspectionResult(PlatformBaseModel):
    manifest_path: str
    workspace_root: str
    source_id: str
    asset_count: int
    generation_count: int
    assets: list[AssetInspectionEntry] = Field(default_factory=list)
    execution_id: str | None = None
    report_path: str | None = None
    report_exists: bool = False
    missing_assets: list[str] = Field(default_factory=list)
    digest_mismatches: list[str] = Field(default_factory=list)
    validation_errors: list[str] = Field(default_factory=list)
    validation_status: Literal["valid", "invalid"]


class ExecutionRecord(PlatformBaseModel):
    execution_id: str
    target_type: str
    target_id: str
    execution_level: Literal["structure_check", "rule_check", "smoke", "scenario", "regression"]
    started_at: datetime
    ended_at: datetime | None = None
    result_status: Literal["passed", "failed", "error"]
    report_path: str | None = None
    error_summary: str | None = None
    environment: str | None = None


class ParsedDocument(PlatformBaseModel):
    source_document: SourceDocument
    modules: list[ApiModule]
    operations: list[ApiOperation]
    assertions: list[AssertionCandidate]


class PipelineResult(PlatformBaseModel):
    source_document: SourceDocument
    modules: list[ApiModule]
    operations: list[ApiOperation]
    assertions: list[AssertionCandidate]
    generation_records: list[GenerationRecord]
    execution_record: ExecutionRecord
    asset_manifest: AssetManifest
    asset_manifest_path: str
    generated_paths: dict[str, str] = Field(default_factory=dict)
