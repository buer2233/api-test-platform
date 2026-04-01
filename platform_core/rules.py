"""平台规则校验器。"""

from __future__ import annotations

import re
from pathlib import Path

from platform_core.models import ApiOperation, AssetManifest, AssertionCandidate, GenerationRecord


class RuleValidator:
    """V1 最小规则校验器。"""

    _SNAKE_CASE_PATTERN = re.compile(r"^[a-z][a-z0-9_]*$")
    _LEGACY_PAYLOAD_MODES = {"none", "json", "data"}
    _LEGACY_RESPONSE_MODES = {"json", "raw"}
    _LEGACY_SOURCE_LAYER = "api_test.core.public_api"
    _LEGACY_TAG = "legacy_public_api"
    _PRIVATE_ENV_TAG = "private_env"

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

    def validate_existing_api_module(self, module: ApiModule) -> list[str]:
        """校验旧接口模块目录是否满足既有资产规则。"""
        violations: list[str] = []
        if not module.module_code or not self._SNAKE_CASE_PATTERN.match(module.module_code):
            violations.append(f"existing_api_asset.module_code 必须为 snake_case: {module.module_code}")
        if self._LEGACY_TAG not in module.tags:
            violations.append(f"existing_api_asset.module.tags 必须包含 {self._LEGACY_TAG}: {module.module_code}")
        if not module.source_ids:
            violations.append(f"existing_api_asset.module.source_ids 不能为空: {module.module_code}")
        return violations

    def validate_existing_api_operation(self, operation: ApiOperation) -> list[str]:
        """校验旧接口操作是否满足既有资产规则。"""
        violations = self.validate_operation(operation)
        metadata = operation.metadata or {}

        if self._LEGACY_TAG not in operation.tags:
            violations.append(
                f"existing_api_asset.operation.tags 必须包含 {self._LEGACY_TAG}: {operation.operation_code}"
            )

        required_metadata_keys = {
            "payload_mode",
            "response_mode",
            "requires_private_env",
            "source_layer",
        }
        for key in required_metadata_keys:
            if key not in metadata:
                violations.append(
                    f"existing_api_asset.operation.metadata.{key} 不能为空: {operation.operation_code}"
                )

        payload_mode = metadata.get("payload_mode")
        if payload_mode is not None and payload_mode not in self._LEGACY_PAYLOAD_MODES:
            violations.append(
                f"existing_api_asset.operation.metadata.payload_mode 非法: {operation.operation_code}"
            )

        response_mode = metadata.get("response_mode")
        if response_mode is not None and response_mode not in self._LEGACY_RESPONSE_MODES:
            violations.append(
                f"existing_api_asset.operation.metadata.response_mode 非法: {operation.operation_code}"
            )

        requires_private_env = metadata.get("requires_private_env")
        if "requires_private_env" in metadata and not isinstance(requires_private_env, bool):
            violations.append(
                f"existing_api_asset.operation.metadata.requires_private_env 必须为 bool: {operation.operation_code}"
            )
        if requires_private_env is True and self._PRIVATE_ENV_TAG not in operation.tags:
            violations.append(
                f"existing_api_asset.operation.tags 必须包含 {self._PRIVATE_ENV_TAG}: {operation.operation_code}"
            )
        if requires_private_env is False and self._PRIVATE_ENV_TAG in operation.tags:
            violations.append(
                f"existing_api_asset.operation.tags 不应包含 {self._PRIVATE_ENV_TAG}: {operation.operation_code}"
            )

        source_layer = metadata.get("source_layer")
        if source_layer is not None and source_layer != self._LEGACY_SOURCE_LAYER:
            violations.append(
                f"existing_api_asset.operation.metadata.source_layer 非法: {operation.operation_code}"
            )

        return violations

    def validate_existing_api_inventory(
        self,
        modules: list[ApiModule],
        operations: list[ApiOperation],
    ) -> list[str]:
        """批量校验旧接口模块与操作组成的库存。"""
        violations: list[str] = []
        module_ids = {module.module_id for module in modules}

        for module in modules:
            violations.extend(self.validate_existing_api_module(module))
        for operation in operations:
            violations.extend(self.validate_existing_api_operation(operation))
            if operation.module_id not in module_ids:
                violations.append(
                    f"existing_api_asset.operation.module_id 未关联到合法模块: {operation.operation_code}"
                )
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
