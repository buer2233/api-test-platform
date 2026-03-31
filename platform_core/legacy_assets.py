from __future__ import annotations

from datetime import UTC, datetime
from importlib import import_module

from platform_core.models import ApiModule, ApiOperation, LegacyApiInventoryResult, SourceDocument


class LegacyPublicApiCatalogAdapter:
    """把旧 PublicAPI 操作目录转换为 platform_core 可消费的结构化快照。"""

    def __init__(self, imported_by: str = "platform_core") -> None:
        self.imported_by = imported_by

    @staticmethod
    def _load_catalog():
        module = import_module("api_test.legacy_api_catalog")
        return module.PUBLIC_API_OPERATION_CATALOG

    def inspect(self) -> LegacyApiInventoryResult:
        source_id = "src-existing-public-api"
        source_document = SourceDocument(
            source_id=source_id,
            source_type="existing_api_asset",
            source_name="api_test_public_api",
            source_path="api_test/core/public_api.py",
            source_version="v1-legacy-catalog",
            source_summary="由旧 PublicAPI 目录治理转换的既有接口资产快照",
            imported_at=datetime.now(UTC),
            imported_by=self.imported_by,
            raw_reference="api_test.legacy_api_catalog:PUBLIC_API_OPERATION_CATALOG",
        )

        module_map: dict[str, ApiModule] = {}
        operations: list[ApiOperation] = []
        private_env_operation_count = 0

        for legacy_operation in self._load_catalog().values():
            module = module_map.setdefault(
                legacy_operation.module_code,
                ApiModule(
                    module_id=f"mod-legacy-{legacy_operation.module_code}",
                    module_name=legacy_operation.module_code,
                    module_code=legacy_operation.module_code,
                    module_path_hint=f"api_test/core/public_api.py::{legacy_operation.module_code}",
                    module_type="common",
                    module_desc=f"旧 PublicAPI 模块目录：{legacy_operation.module_code}",
                    source_ids=[source_id],
                    tags=["legacy_public_api"],
                ),
            )

            tags = ["legacy_public_api"]
            if legacy_operation.requires_private_env:
                tags.append("private_env")
                private_env_operation_count += 1

            operations.append(
                ApiOperation(
                    operation_id=f"op-legacy-{legacy_operation.operation_code}",
                    module_id=module.module_id,
                    operation_name=legacy_operation.operation_name,
                    operation_code=legacy_operation.operation_code,
                    http_method=legacy_operation.http_method,
                    path=legacy_operation.path_template,
                    summary=legacy_operation.description,
                    description=f"由旧 PublicAPI 目录治理转换的既有接口资产：{legacy_operation.operation_name}",
                    tags=tags,
                    success_codes=[200] if legacy_operation.response_mode == "json" else [],
                    source_ids=[source_id],
                    metadata={
                        "payload_mode": legacy_operation.payload_mode,
                        "response_mode": legacy_operation.response_mode,
                        "requires_private_env": legacy_operation.requires_private_env,
                        "source_layer": "api_test.core.public_api",
                    },
                )
            )

        modules = sorted(module_map.values(), key=lambda item: item.module_code)
        operations.sort(key=lambda item: item.operation_code)

        return LegacyApiInventoryResult(
            source_document=source_document,
            module_count=len(modules),
            operation_count=len(operations),
            private_env_operation_count=private_env_operation_count,
            modules=modules,
            operations=operations,
        )
