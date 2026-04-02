"""OpenAPI / Swagger 文档解析器。"""

from __future__ import annotations

import json
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

import yaml

from platform_core.models import (
    ApiModule,
    ApiOperation,
    ApiParam,
    AssertionCandidate,
    ParsedDocument,
    ResponseField,
    SourceDocument,
)


class OpenAPIDocumentParser:
    """OpenAPI/Swagger 文档 -> V1 中间模型解析器。"""

    SUPPORTED_METHODS = {"get", "post", "put", "delete", "patch"}
    YAML_SUFFIXES = {".yaml", ".yml"}

    def parse(self, source_path: str | Path) -> ParsedDocument:
        """解析源文档并输出中间模型。"""
        source = Path(source_path)
        spec = self._load_spec(source)
        info = spec.get("info", {})
        is_openapi = bool(spec.get("openapi"))
        source_document = SourceDocument(
            source_id=f"source-{self._normalize_identifier(source.stem)}",
            source_type="openapi" if is_openapi else "swagger",
            source_name=source.stem,
            source_path=str(source),
            source_version=info.get("version"),
            source_summary=info.get("title"),
            imported_at=datetime.now(UTC),
            imported_by="codex",
            raw_reference=str(source.resolve()),
        )

        modules: dict[str, ApiModule] = {}
        operations: list[ApiOperation] = []
        assertions: list[AssertionCandidate] = []

        for path, path_item in spec.get("paths", {}).items():
            for method, operation_spec in path_item.items():
                if method.lower() not in self.SUPPORTED_METHODS:
                    continue
                module = self._build_module(path, operation_spec, source_document)
                modules[module.module_id] = module

                operation = self._build_operation(
                    path=path,
                    method=method,
                    operation_spec=operation_spec,
                    module=module,
                    source_document=source_document,
                    is_openapi=is_openapi,
                )
                operations.append(operation)
                assertions.extend(self._build_assertions(operation))

        return ParsedDocument(
            source_document=source_document,
            modules=list(modules.values()),
            operations=operations,
            assertions=assertions,
        )

    def _load_spec(self, source: Path) -> dict[str, Any]:
        """读取 JSON 或 YAML 格式的接口文档。"""
        raw = source.read_text(encoding="utf-8-sig")
        if source.suffix.lower() in self.YAML_SUFFIXES:
            return yaml.safe_load(raw)
        return json.loads(raw)

    def _build_module(
        self,
        path: str,
        operation_spec: dict[str, Any],
        source_document: SourceDocument,
    ) -> ApiModule:
        """根据路径和标签生成模块模型。"""
        raw_module_name = (operation_spec.get("tags") or [self._module_name_from_path(path)])[0]
        module_code = self._normalize_identifier(raw_module_name)
        return ApiModule(
            module_id=f"module-{module_code}",
            module_name=raw_module_name,
            module_code=module_code,
            module_path_hint=f"generated/apis/{module_code}_api.py",
            module_type="api",
            module_desc=operation_spec.get("summary") or raw_module_name,
            source_ids=[source_document.source_id],
            tags=operation_spec.get("tags") or [raw_module_name],
        )

    def _build_operation(
        self,
        path: str,
        method: str,
        operation_spec: dict[str, Any],
        module: ApiModule,
        source_document: SourceDocument,
        is_openapi: bool,
    ) -> ApiOperation:
        """根据单个路径方法定义生成接口操作模型。"""
        operation_code = self._normalize_identifier(
            operation_spec.get("operationId") or f"{method}_{path}"
        )
        parameters = operation_spec.get("parameters") or []
        path_params: list[ApiParam] = []
        query_params: list[ApiParam] = []
        header_params: list[ApiParam] = []
        body_params: list[ApiParam] = []

        for index, parameter in enumerate(parameters, start=1):
            param = self._build_param(parameter, operation_code, index)
            if param is None:
                continue
            if param.param_in == "path":
                path_params.append(param)
            elif param.param_in == "query":
                query_params.append(param)
            elif param.param_in == "header":
                header_params.append(param)
            elif param.param_in == "body":
                body_params.append(param)

        if is_openapi:
            body_params.extend(self._build_openapi_body_params(operation_code, operation_spec))

        success_code, response_fields, response_schema = self._build_response_fields(
            operation_code,
            operation_spec,
            is_openapi,
        )

        return ApiOperation(
            operation_id=f"operation-{operation_code}",
            module_id=module.module_id,
            operation_name=operation_spec.get("summary") or operation_code,
            operation_code=operation_code,
            http_method=method.upper(),
            path=path,
            summary=operation_spec.get("summary"),
            description=operation_spec.get("description"),
            tags=operation_spec.get("tags") or module.tags,
            auth_type="session" if operation_spec.get("security") else None,
            request_headers=header_params,
            path_params=path_params,
            query_params=query_params,
            body_params=body_params,
            response_fields=response_fields,
            success_codes=[success_code] if success_code is not None else [],
            source_ids=[source_document.source_id],
            metadata={"primary_success_response_schema": response_schema},
        )

    def _build_param(
        self,
        parameter: dict[str, Any],
        operation_code: str,
        index: int,
    ) -> ApiParam | None:
        """把单个参数定义转换为统一参数模型。"""
        schema = parameter.get("schema") or {}
        param_in = parameter.get("in")
        if param_in not in {"header", "path", "query", "body", "cookie"}:
            return None

        if param_in == "body":
            return self._build_body_root_param(parameter, operation_code, index)

        return ApiParam(
            param_id=f"{operation_code}-param-{index}",
            operation_id=f"operation-{operation_code}",
            param_name=parameter["name"],
            param_in=param_in,
            data_type=schema.get("type", "string"),
            required=parameter.get("required", False),
            default_value=schema.get("default"),
            example_value=schema.get("example"),
            desc=parameter.get("description"),
            source="openapi",
        )

    def _build_body_root_param(
        self,
        parameter: dict[str, Any],
        operation_code: str,
        index: int,
    ) -> ApiParam:
        """为 Swagger body 参数生成根参数模型。"""
        schema = parameter.get("schema") or {}
        return ApiParam(
            param_id=f"{operation_code}-body-{index}",
            operation_id=f"operation-{operation_code}",
            param_name=parameter.get("name", "body"),
            param_in="body",
            data_type=schema.get("type", "object"),
            required=parameter.get("required", False),
            default_value=schema.get("default"),
            example_value=schema.get("example"),
            desc=parameter.get("description"),
            source="swagger",
        )

    def _build_openapi_body_params(self, operation_code: str, operation_spec: dict[str, Any]) -> list[ApiParam]:
        """解析 OpenAPI requestBody 中的 body 字段定义。"""
        request_body = operation_spec.get("requestBody") or {}
        content = request_body.get("content") or {}
        schema = (content.get("application/json") or {}).get("schema") or {}
        body_params: list[ApiParam] = []
        for index, (name, prop) in enumerate((schema.get("properties") or {}).items(), start=1):
            body_params.append(
                ApiParam(
                    param_id=f"{operation_code}-body-{index}",
                    operation_id=f"operation-{operation_code}",
                    param_name=name,
                    param_in="body",
                    data_type=prop.get("type", "string"),
                    required=name in (schema.get("required") or []),
                    default_value=prop.get("default"),
                    example_value=prop.get("example"),
                    desc=prop.get("description"),
                    source="openapi",
                )
            )
        return body_params

    def _build_response_fields(
        self,
        operation_code: str,
        operation_spec: dict[str, Any],
        is_openapi: bool,
    ) -> tuple[int | None, list[ResponseField], dict[str, Any]]:
        """提取成功响应码及其响应字段。"""
        responses = operation_spec.get("responses") or {}
        success_codes = sorted([int(code) for code in responses if code.isdigit() and code.startswith("2")])
        if not success_codes:
            return None, [], {}

        success_code = success_codes[0]
        response_payload = responses.get(str(success_code)) or {}
        if is_openapi:
            schema = ((((response_payload.get("content") or {}).get("application/json") or {}).get("schema")) or {})
        else:
            schema = response_payload.get("schema") or {}
        fields = self._extract_response_fields(
            operation_id=f"operation-{operation_code}",
            status_code=success_code,
            schema=schema,
        )
        return success_code, fields, schema

    def _extract_response_fields(
        self,
        operation_id: str,
        status_code: int,
        schema: dict[str, Any],
        prefix: str = "",
    ) -> list[ResponseField]:
        """递归展开响应 schema 中的字段定义。"""
        properties = schema.get("properties") or {}
        required_fields = schema.get("required") or []
        collected: list[ResponseField] = []
        for name, prop in properties.items():
            field_path = f"{prefix}.{name}" if prefix else name
            field_type = prop.get("type", "string")
            collected.append(
                ResponseField(
                    field_id=f"{operation_id}-{self._normalize_identifier(field_path)}",
                    operation_id=operation_id,
                    status_code=status_code,
                    field_path=field_path,
                    field_name=name,
                    data_type=field_type,
                    required=name in required_fields,
                    example_value=prop.get("example"),
                    desc=prop.get("description"),
                    can_extract_as_variable=field_type != "object" and name.lower().endswith("id"),
                    can_assert=True,
                )
            )
            if field_type == "object":
                collected.extend(
                    self._extract_response_fields(
                        operation_id=operation_id,
                        status_code=status_code,
                        schema=prop,
                        prefix=field_path,
                    )
                )
        return collected

    def _build_assertions(self, operation: ApiOperation) -> list[AssertionCandidate]:
        """根据操作定义自动生成最小断言集合。"""
        assertions = [
            AssertionCandidate(
                assertion_id=f"{operation.operation_id}-status-code",
                operation_id=operation.operation_id,
                assertion_type="status_code",
                target_path="status_code",
                expected_value=operation.success_codes[0] if operation.success_codes else 200,
                priority="high",
                source="openapi",
                confidence_score=1.0,
                review_status="pending",
            )
        ]

        first_response_field = next((field for field in operation.response_fields if field.can_assert), None)
        if first_response_field:
            assertions.append(
                AssertionCandidate(
                    assertion_id=f"{operation.operation_id}-field-exists",
                    operation_id=operation.operation_id,
                    assertion_type="json_field_exists",
                    target_path=first_response_field.field_path,
                    expected_value=None,
                    priority="medium",
                    source="openapi",
                    confidence_score=0.8,
                    review_status="pending",
                )
            )
        schema_assertion = self._build_schema_match_assertion(operation)
        if schema_assertion:
            assertions.append(schema_assertion)
        comparable_field = next(
            (
                field
                for field in operation.response_fields
                if field.can_assert and field.example_value is not None and field.data_type not in {"object", "array"}
            ),
            None,
        )
        if comparable_field:
            assertions.append(
                AssertionCandidate(
                    assertion_id=f"{operation.operation_id}-field-equals",
                    operation_id=operation.operation_id,
                    assertion_type="json_field_equals",
                    target_path=comparable_field.field_path,
                    expected_value=comparable_field.example_value,
                    priority="medium",
                    source="openapi",
                    confidence_score=0.7,
                    review_status="pending",
                )
            )
        return assertions

    def _build_schema_match_assertion(self, operation: ApiOperation) -> AssertionCandidate | None:
        """根据响应字段推导最小 schema_match 断言。"""
        response_schema = operation.metadata.get("primary_success_response_schema", {})
        if isinstance(response_schema, dict):
            schema_assertion = self._build_schema_match_from_schema(operation, response_schema)
            if schema_assertion is not None:
                return schema_assertion

        object_field = next(
            (field for field in operation.response_fields if field.can_assert and field.data_type == "object"),
            None,
        )
        if object_field:
            return AssertionCandidate(
                assertion_id=f"{operation.operation_id}-schema-match",
                operation_id=operation.operation_id,
                assertion_type="schema_match",
                target_path=object_field.field_path,
                expected_value={
                    "type": "object",
                    "required_fields": self._collect_direct_child_fields(operation, object_field.field_path),
                },
                priority="medium",
                source="openapi",
                confidence_score=0.7,
                review_status="pending",
            )

        array_field = next(
            (field for field in operation.response_fields if field.can_assert and field.data_type == "array"),
            None,
        )
        if array_field:
            return AssertionCandidate(
                assertion_id=f"{operation.operation_id}-schema-match",
                operation_id=operation.operation_id,
                assertion_type="schema_match",
                target_path=array_field.field_path,
                expected_value={"type": "array"},
                priority="medium",
                source="openapi",
                confidence_score=0.7,
                review_status="pending",
            )
        return None

    def _build_schema_match_from_schema(
        self,
        operation: ApiOperation,
        response_schema: dict[str, Any],
    ) -> AssertionCandidate | None:
        """根据原始成功响应 schema 推导更精确的 schema_match 断言。"""
        properties = response_schema.get("properties") or {}
        for field_name, field_schema in properties.items():
            field_type = field_schema.get("type")
            if field_type == "object":
                expected_value: dict[str, Any] = {"type": "object"}
                required_fields = list((field_schema.get("properties") or {}).keys())
                if required_fields:
                    expected_value["required_fields"] = required_fields
                return AssertionCandidate(
                    assertion_id=f"{operation.operation_id}-schema-match",
                    operation_id=operation.operation_id,
                    assertion_type="schema_match",
                    target_path=field_name,
                    expected_value=expected_value,
                    priority="medium",
                    source="openapi",
                    confidence_score=0.7,
                    review_status="pending",
                )
            if field_type == "array":
                expected_value = {"type": "array"}
                item_schema = field_schema.get("items") or {}
                if item_schema.get("type") == "object":
                    expected_value["item_type"] = "object"
                    required_fields = list((item_schema.get("properties") or {}).keys())
                    if required_fields:
                        expected_value["required_fields"] = required_fields
                return AssertionCandidate(
                    assertion_id=f"{operation.operation_id}-schema-match",
                    operation_id=operation.operation_id,
                    assertion_type="schema_match",
                    target_path=field_name,
                    expected_value=expected_value,
                    priority="medium",
                    source="openapi",
                    confidence_score=0.7,
                    review_status="pending",
                )
        return None

    @staticmethod
    def _collect_direct_child_fields(operation: ApiOperation, parent_path: str) -> list[str]:
        """收集指定对象节点下一层直接字段名。"""
        prefix = f"{parent_path}."
        child_fields: list[str] = []
        for field in operation.response_fields:
            if not field.field_path.startswith(prefix):
                continue
            suffix = field.field_path.removeprefix(prefix)
            if "." in suffix:
                continue
            child_fields.append(field.field_name)
        return child_fields

    @staticmethod
    def _module_name_from_path(path: str) -> str:
        """根据 URL 路径推导默认模块名。"""
        parts = [part for part in path.split("/") if part and not part.startswith("{")]
        return parts[1] if len(parts) > 1 else (parts[0] if parts else "default")

    @staticmethod
    def _normalize_identifier(value: str) -> str:
        """把任意标识符规范化为 snake_case。"""
        spaced = re.sub(r"([a-z0-9])([A-Z])", r"\1 \2", value)
        spaced = re.sub(r"[^a-zA-Z0-9]+", " ", spaced)
        return "_".join(part.lower() for part in spaced.split() if part)
