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
            "fake_status_code": self._resolve_fake_status_code(assertions),
            "fake_response_json_literal": self._build_fake_response_json_literal(assertions),
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
            elif assertion.assertion_type == "schema_match":
                template_name = "assertions/schema_match.py.j2"
                expected_value = assertion.expected_value if isinstance(assertion.expected_value, dict) else {}
                context = {
                    "target_path": assertion.target_path,
                    "expected_type": expected_value.get("type", "object"),
                    "python_type_expr": self._build_python_type_expr(expected_value.get("type", "object")),
                    "item_type": expected_value.get("item_type"),
                    "item_python_type_expr": self._build_python_type_expr(expected_value.get("item_type", "object")),
                    "required_fields": expected_value.get("required_fields", []),
                    "required_fields_literal": json.dumps(
                        expected_value.get("required_fields", []),
                        ensure_ascii=False,
                    ),
                }
            elif assertion.assertion_type == "business_rule":
                expected_value = assertion.expected_value if isinstance(assertion.expected_value, dict) else {}
                rule_code = expected_value.get("rule_code")
                if rule_code not in {"non_empty_string", "positive_integer"}:
                    continue
                template_name = "assertions/business_rule.py.j2"
                context = {
                    "target_path": assertion.target_path,
                    "rule_code": rule_code,
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
    def _build_python_type_expr(expected_type: str) -> str:
        """把断言类型映射为 Python `isinstance` 表达式。"""
        mapping = {
            "object": "dict",
            "array": "list",
            "string": "str",
            "integer": "int",
            "number": "(int, float)",
            "boolean": "bool",
        }
        return mapping.get(expected_type, "object")

    @staticmethod
    def _build_path_expression(path: str, path_params: list[Any]) -> str:
        """根据 path 参数情况构建路径表达式。"""
        if not path_params:
            return f'"{path}"'
        return f'f"{path}"'

    def _resolve_fake_status_code(self, assertions: list[AssertionCandidate]) -> int:
        """从断言候选中推导生成测试使用的假响应状态码。"""
        for assertion in assertions:
            if assertion.assertion_type == "status_code" and isinstance(assertion.expected_value, int):
                return assertion.expected_value
        return 200

    def _build_fake_response_json_literal(self, assertions: list[AssertionCandidate]) -> str:
        """构建可在模板中直接反序列化的假响应 JSON 字符串字面量。"""
        fake_body = self._build_fake_response_body(assertions)
        return self._repr_default(json.dumps(fake_body, ensure_ascii=False))

    def _build_fake_response_body(self, assertions: list[AssertionCandidate]) -> dict[str, Any]:
        """根据断言候选构建最小可通过的假响应体。"""
        body: dict[str, Any] = {}

        for assertion in assertions:
            if assertion.assertion_type != "schema_match" or not isinstance(assertion.expected_value, dict):
                continue
            self._apply_schema_match_placeholder(body, assertion.target_path, assertion.expected_value)

        for assertion in assertions:
            if assertion.assertion_type != "json_field_exists":
                continue
            self._ensure_nested_value(
                body,
                assertion.target_path,
                self._build_path_placeholder(assertion.target_path),
            )

        for assertion in assertions:
            if assertion.assertion_type != "business_rule":
                continue
            expected_value = assertion.expected_value if isinstance(assertion.expected_value, dict) else {}
            rule_code = expected_value.get("rule_code")
            if rule_code == "non_empty_string":
                placeholder_value = self._build_path_placeholder(assertion.target_path)
            elif rule_code == "positive_integer":
                placeholder_value = 1
            else:
                continue
            self._ensure_nested_value(
                body,
                assertion.target_path,
                placeholder_value,
            )

        for assertion in assertions:
            if assertion.assertion_type != "json_field_equals":
                continue
            self._set_nested_value(body, assertion.target_path, assertion.expected_value)

        return body

    def _apply_schema_match_placeholder(
        self,
        body: dict[str, Any],
        target_path: str,
        expected_value: dict[str, Any],
    ) -> None:
        """把 schema_match 断言转换为假响应中的最小结构。"""
        expected_type = expected_value.get("type", "object")
        if expected_type == "object":
            current_value = self._get_nested_value(body, target_path)
            if not isinstance(current_value, dict):
                self._set_nested_value(body, target_path, {})
                current_value = self._get_nested_value(body, target_path)
            required_fields = expected_value.get("required_fields", [])
            for field_name in required_fields:
                if isinstance(current_value, dict) and field_name not in current_value:
                    current_value[field_name] = self._build_path_placeholder(f"{target_path}.{field_name}")
            return

        if expected_type == "array":
            item_type = expected_value.get("item_type")
            required_fields = expected_value.get("required_fields", [])
            if item_type == "object":
                item_payload = {
                    field_name: self._build_path_placeholder(f"{target_path}.{field_name}")
                    for field_name in required_fields
                }
                self._set_nested_value(body, target_path, [item_payload or {}])
                return
            if isinstance(item_type, str):
                self._set_nested_value(body, target_path, [self._build_schema_placeholder(item_type)])
                return

        self._set_nested_value(body, target_path, self._build_schema_placeholder(expected_type))

    @staticmethod
    def _build_schema_placeholder(expected_type: str) -> Any:
        """根据 schema 类型生成占位值。"""
        mapping: dict[str, Any] = {
            "array": [],
            "string": "sample-value",
            "integer": 1,
            "number": 1,
            "boolean": True,
        }
        return mapping.get(expected_type, {})

    @staticmethod
    def _build_path_placeholder(target_path: str) -> str:
        """根据字段路径生成更可读的占位字符串。"""
        field_name = target_path.split(".")[-1]
        return f"sample-{field_name}"

    @staticmethod
    def _get_nested_value(data: dict[str, Any], target_path: str) -> Any:
        """读取嵌套字典中的目标路径值。"""
        current: Any = data
        for key in target_path.split("."):
            if not isinstance(current, dict) or key not in current:
                return None
            current = current[key]
        return current

    def _ensure_nested_value(self, data: dict[str, Any], target_path: str, default_value: Any) -> None:
        """仅当目标路径不存在时，补齐默认占位值。"""
        if self._get_nested_value(data, target_path) is None:
            self._set_nested_value(data, target_path, default_value)

    @staticmethod
    def _set_nested_value(data: dict[str, Any], target_path: str, value: Any) -> None:
        """把值写入嵌套字典路径，并在必要时自动补齐父节点。"""
        parts = target_path.split(".")
        current: dict[str, Any] = data
        for key in parts[:-1]:
            next_value = current.get(key)
            if not isinstance(next_value, dict):
                current[key] = {}
            current = current[key]
        current[parts[-1]] = value

    @staticmethod
    def _build_call_kwargs(operation: ApiOperation) -> str:
        """为生成测试代码构建默认调用参数。"""
        call_parts = []
        for param in operation.path_params:
            call_parts.append(f'{param.param_name}="sample-{param.param_name}"')
        return ", ".join(call_parts)
