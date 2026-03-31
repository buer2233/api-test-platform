"""旧底座接口资产的最小标准化描述。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal


PayloadMode = Literal["none", "json", "data"]


@dataclass(frozen=True, slots=True)
class LegacyApiOperation:
    """为旧 PublicAPI 提供统一操作目录，便于后续向平台模型收口。"""

    operation_name: str
    operation_code: str
    module_code: str
    path_template: str
    http_method: Literal["GET", "POST", "PUT", "PATCH", "DELETE"]
    payload_mode: PayloadMode = "none"
    requires_private_env: bool = True
    response_mode: Literal["json", "raw"] = "json"
    description: str | None = None
    metadata: dict[str, Any] | None = None

    def render_path(self, **path_params: Any) -> str:
        return self.path_template.format(**path_params)
