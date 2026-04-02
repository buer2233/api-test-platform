"""平台规则校验器。"""

from __future__ import annotations

import re
from pathlib import Path

from platform_core.models import ApiOperation, AssetManifest, AssertionCandidate, GenerationRecord


class RuleValidator:
    """V1 最小规则校验器。"""

    _SNAKE_CASE_PATTERN = re.compile(r"^[a-z][a-z0-9_]*$")
    _SUPPORTED_SCHEMA_TYPES = {"object", "array", "string", "integer", "number", "boolean"}

    def validate_operation(self, operation: ApiOperation) -> list[str]:
        """校验通用接口操作是否满足最小命名和字段约束。"""
        violations: list[str] = []
        if not operation.operation_code or not self._SNAKE_CASE_PATTERN.match(operation.operation_code):
            violations.append("operation_code 必须为 snake_case")
        if not operation.module_id:
            violations.append("module_id 不能为空")
        if not operation.http_method:
            violations.append("http_method 不能为空")
        if not operation.path:
            violations.append("path 不能为空")
        if not operation.source_ids:
            violations.append("source_ids 不能为空")
        return violations

    @staticmethod
    def validate_test_file_name(file_name: str) -> list[str]:
        """校验测试文件名是否符合 `test_*.py` 规范。"""
        normalized = Path(file_name).name
        if not normalized.startswith("test_") or not normalized.endswith(".py"):
            return ["测试文件名必须符合 test_*.py 规范"]
        return []

    @staticmethod
    def validate_generation_record(record: GenerationRecord) -> list[str]:
        """校验生成记录是否具备最小追溯字段。"""
        violations: list[str] = []
        if not record.source_ids:
            violations.append("generation_record.source_ids 不能为空")
        if not record.target_asset_path:
            violations.append("generation_record.target_asset_path 不能为空")
        if not record.template_reference:
            violations.append("generation_record.template_reference 不能为空")
        if not record.generation_version:
            violations.append("generation_record.generation_version 不能为空")
        if record.generator_type == "ai_assisted" and not record.prompt_reference:
            violations.append("ai_assisted 生成记录必须提供 prompt_reference")
        return violations

    @staticmethod
    def validate_assertions(
        operation: ApiOperation,
        assertions: list[AssertionCandidate],
    ) -> list[str]:
        """校验接口断言集合是否满足执行前置要求。"""
        violations: list[str] = []
        if operation.success_codes and not any(
            assertion.assertion_type == "status_code" for assertion in assertions
        ):
            violations.append("可执行接口至少需要一个 status_code 断言")
        for assertion in assertions:
            if assertion.assertion_type != "schema_match":
                continue
            if not isinstance(assertion.expected_value, dict):
                violations.append("schema_match.expected_value 必须为字典")
                continue
            expected_type = assertion.expected_value.get("type")
            if expected_type not in RuleValidator._SUPPORTED_SCHEMA_TYPES:
                violations.append("schema_match.type 非法或缺失")
            required_fields = assertion.expected_value.get("required_fields", [])
            if "required_fields" in assertion.expected_value and (
                not isinstance(required_fields, list)
                or any(not isinstance(field, str) or not field for field in required_fields)
            ):
                violations.append("schema_match.required_fields 必须为非空字符串列表")
        return violations

    @staticmethod
    def validate_asset_manifest(manifest: AssetManifest) -> list[str]:
        """校验资产清单是否包含执行闭环所需的关键字段。"""
        violations: list[str] = []
        if not manifest.assets:
            violations.append("asset_manifest.assets 不能为空")
        if not manifest.generation_ids:
            violations.append("asset_manifest.generation_ids 不能为空")
        if not manifest.execution_id:
            violations.append("asset_manifest.execution_id 不能为空")
        if not manifest.report_path:
            violations.append("asset_manifest.report_path 不能为空")
        for asset in manifest.assets:
            if not asset.source_ids:
                violations.append(f"asset_record.source_ids 不能为空: {asset.asset_id}")
            if not asset.content_digest:
                violations.append(f"asset_record.content_digest 不能为空: {asset.asset_id}")
        return violations


__all__ = ["RuleValidator"]
