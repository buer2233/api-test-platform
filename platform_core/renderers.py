"""模板渲染器。"""

from __future__ import annotations

import json
import textwrap
from pathlib import Path
from typing import Any

from jinja2 import Environment, FileSystemLoader

from platform_core.models import ApiModule, ApiOperation, AssertionCandidate, GenerationRecord


class TemplateRenderer:
    """V1 模板渲染器。"""

    def __init__(self) -> None:
        """初始化 Jinja2 模板环境。"""
        template_dir = Path(__file__).resolve().parent / "templates"
        self.env = Environment(
            loader=FileSystemLoader(template_dir),
            trim_blocks=True,
            lstrip_blocks=True,
            keep_trailing_newline=True,
        )

    def render_api_module(self, module: ApiModule, operations: list[ApiOperation]) -> str:
        """渲染 API 模块代码。"""
        template = self.env.get_template("api/api_module.py.j2")
        payload = {
            "class_name": f"{self._snake_to_pascal(module.module_code)}Api",
            "operations": [self._build_operation_context(operation) for operation in operations],
        }
        return template.render(**payload).removeprefix("\ufeff")

    def render_test_module(
        self,
        module: ApiModule,
        operation: ApiOperation,
        assertions: list[AssertionCandidate],
    ) -> str:
        """渲染单个接口对应的 pytest 测试模块。"""
        template = self.env.get_template("tests/test_module.py.j2")
        operation_context = self._build_operation_context(operation)
        payload = {
            "module_import": f"generated.apis.{module.module_code}_api",
            "class_name": f"{self._snake_to_pascal(module.module_code)}Api",
            "operation": operation_context,
            "call_kwargs": self._build_call_kwargs(operation),
            "assertions": textwrap.indent(self.render_assertions(assertions).rstrip(), "    "),
        }
        return template.render(**payload).removeprefix("\ufeff")

    def render_assertions(self, assertions: list[AssertionCandidate]) -> str:
        """把断言候选列表渲染为测试断言代码。"""
        rendered: list[str] = []
        for assertion in assertions:
            if assertion.assertion_type == "status_code":
                template_name = "assertions/status_code.py.j2"
                context = {"expected_value": assertion.expected_value}
            elif assertion.assertion_type == "json_field_exists":
                template_name = "assertions/json_field_exists.py.j2"
                context = {"target_path": assertion.target_path}
            elif assertion.assertion_type == "json_field_equals":
                template_name = "assertions/json_field_equals.py.j2"
                context = {
                    "target_path": assertion.target_path,
                    "expected_value": self._repr_default(assertion.expected_value),
                }
            else:
                continue
            rendered.append(
                self.env.get_template(template_name).render(**context).removeprefix("\ufeff").rstrip()
            )
        return "\n".join(rendered) + ("\n" if rendered else "")

    def render_generation_record(self, record: GenerationRecord) -> str:
        """渲染生成记录 JSON 文本。"""
        template = self.env.get_template("records/generation_record.json.j2")
        payload = json.dumps(record.model_dump(mode="json"), ensure_ascii=False, indent=2)
        return template.render(payload=payload).removeprefix("\ufeff")

    @staticmethod
    def _snake_to_pascal(value: str) -> str:
        """把 snake_case 转为 PascalCase。"""
        return "".join(part.capitalize() for part in value.split("_") if part)

    def _build_operation_context(self, operation: ApiOperation) -> dict[str, Any]:
        """构建模板渲染所需的接口上下文字典。"""
        signature_parts = [param.param_name for param in operation.path_params]
        for param in operation.query_params:
            signature_parts.append(f"{param.param_name}={self._repr_default(param.default_value)}")
        for param in operation.body_params:
            signature_parts.append(param.param_name)

        query_lines = [
            f'if {param.param_name} is not None:\n            query_params["{param.param_name}"] = {param.param_name}'
            for param in operation.query_params
        ]

        return {
            "operation_code": operation.operation_code,
            "http_method": operation.http_method.upper(),
            "signature": ", ".join(signature_parts),
            "path_expression": self._build_path_expression(operation.path, operation.path_params),
            "query_lines": query_lines,
            "has_query_params": bool(operation.query_params),
        }

    @staticmethod
    def _repr_default(value: Any) -> str:
        """把默认值转换为可直接嵌入模板的 Python 表达式。"""
        if value is None:
            return "None"
        return repr(value)

    @staticmethod
    def _build_path_expression(path: str, path_params: list[Any]) -> str:
        """根据 path 参数情况构建路径表达式。"""
        if not path_params:
            return f'"{path}"'
        return f'f"{path}"'

    @staticmethod
    def _build_call_kwargs(operation: ApiOperation) -> str:
        """为生成测试代码构建默认调用参数。"""
        call_parts = []
        for param in operation.path_params:
            call_parts.append(f'{param.param_name}="sample-{param.param_name}"')
        return ", ".join(call_parts)
