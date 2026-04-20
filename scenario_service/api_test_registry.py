"""`api_test` 接口方法注册扫描能力。"""

from __future__ import annotations

import ast
from pathlib import Path


HTTP_METHOD_MAP = {
    "get": "GET",
    "post": "POST",
    "put": "PUT",
    "patch": "PATCH",
    "delete": "DELETE",
}


class ApiTestMethodRegistry:
    """按 HTTP 方法和完整 URL 路径管理已有接口方法。"""

    def __init__(self) -> None:
        """初始化空注册表。"""
        self._items: dict[tuple[str, str], dict] = {}
        self._items_by_id: dict[str, dict] = {}

    def clear(self) -> None:
        """清空当前注册表。"""
        self._items.clear()
        self._items_by_id.clear()

    def register(self, item: dict) -> None:
        """注册一个已有接口方法定义。"""
        normalized_item = dict(item)
        normalized_item["http_method"] = str(item["http_method"]).upper()
        normalized_item["path_template"] = str(item.get("path_template") or item.get("full_path") or "")
        normalized_item["full_path"] = normalized_item["path_template"]
        normalized_item["interface_id"] = str(
            item.get("interface_id")
            or f"{normalized_item.get('module_path', normalized_item.get('source_file', 'manual'))}::{normalized_item['method_name']}"
        )
        key = (normalized_item["http_method"], normalized_item["full_path"])
        self._items[key] = normalized_item
        self._items_by_id[str(normalized_item["interface_id"])] = normalized_item

    def load_from_core_directory(self, root: str | Path) -> list[dict]:
        """扫描 `api_test/core` 目录并重建接口方法注册表。"""
        self.clear()
        for item in self.scan_core_directory(root):
            self.register(item)
        return self.list_items()

    def scan_core_directory(self, root: str | Path) -> list[dict]:
        """扫描 `api_test/core` 目录下的接口方法定义。"""
        root_path = Path(root)
        items: list[dict] = []
        for file_path in root_path.rglob("*.py"):
            if file_path.name == "__init__.py":
                continue
            source_file = file_path.resolve().as_posix()
            items.extend(self._scan_python_file(file_path=file_path, source_file=source_file))
        return items

    def list_items(self) -> list[dict]:
        """返回当前注册表中的全部接口项。"""
        return sorted(
            self._items_by_id.values(),
            key=lambda item: (
                str(item.get("project_code", "")),
                str(item.get("module_code", "")),
                str(item.get("method_name", "")),
            ),
        )

    def get_by_interface_id(self, interface_id: str) -> dict | None:
        """按接口标识返回已注册项。"""
        return self._items_by_id.get(interface_id)

    def match(self, http_method: str, full_path: str) -> dict | None:
        """按 HTTP 方法和完整路径返回命中的接口方法。"""
        return self._items.get((http_method.upper(), full_path))

    def _scan_python_file(self, *, file_path: Path, source_file: str) -> list[dict]:
        """扫描单个 Python 文件中的 `BaseAPI` 风格接口方法。"""
        try:
            tree = ast.parse(file_path.read_text(encoding="utf-8"))
        except SyntaxError:
            return []
        items: list[dict] = []
        for node in tree.body:
            if not isinstance(node, ast.ClassDef):
                continue
            if not self._looks_like_api_class(node):
                continue
            for child in node.body:
                if not isinstance(child, ast.FunctionDef):
                    continue
                method_call = self._find_http_call(child)
                if method_call is None or not method_call.args:
                    continue
                http_method = HTTP_METHOD_MAP.get(method_call.func.attr, "").upper()
                path_template = self._extract_path_template(method_call.args[0])
                if not http_method or not path_template:
                    continue
                project_code, module_code = self._resolve_asset_scope(file_path)
                interface_id = f"{project_code}__{module_code}__{node.name}__{child.name}"
                items.append(
                    {
                        "interface_id": interface_id,
                        "source_file": source_file,
                        "class_name": node.name,
                        "method_name": child.name,
                        "http_method": http_method,
                        "path_template": path_template,
                        "full_path": path_template,
                        "project_code": project_code,
                        "module_code": module_code,
                        "required_parameters": self._collect_required_parameters(child),
                    }
                )
        return items

    @staticmethod
    def _looks_like_api_class(node: ast.ClassDef) -> bool:
        """判断类是否看起来像 `BaseAPI` 风格的接口封装类。"""
        for base in node.bases:
            if isinstance(base, ast.Name) and base.id.endswith("BaseAPI"):
                return True
        return False

    def _find_http_call(self, node: ast.FunctionDef) -> ast.Call | None:
        """在方法体中定位首个 HTTP 动作调用。"""
        for child in ast.walk(node):
            if not isinstance(child, ast.Call):
                continue
            if not isinstance(child.func, ast.Attribute):
                continue
            if not isinstance(child.func.value, ast.Name) or child.func.value.id != "self":
                continue
            if child.func.attr not in HTTP_METHOD_MAP:
                continue
            return child
        return None

    @staticmethod
    def _extract_path_template(node: ast.AST) -> str:
        """把字符串常量或 f-string 转为路径模板。"""
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            return node.value
        if isinstance(node, ast.JoinedStr):
            parts: list[str] = []
            for child in node.values:
                if isinstance(child, ast.Constant):
                    parts.append(str(child.value))
                elif isinstance(child, ast.FormattedValue):
                    placeholder = "value"
                    if isinstance(child.value, ast.Name):
                        placeholder = child.value.id
                    elif isinstance(child.value, ast.Attribute):
                        placeholder = child.value.attr
                    parts.append(f"{{{placeholder}}}")
            return "".join(parts)
        return ""

    @staticmethod
    def _collect_required_parameters(node: ast.FunctionDef) -> list[str]:
        """提取方法签名中的必填参数列表。"""
        parameters: list[str] = []
        required_end_index = len(node.args.args) - len(node.args.defaults)
        for index, arg in enumerate(node.args.args):
            if arg.arg == "self":
                continue
            if index < required_end_index:
                parameters.append(arg.arg)
        return parameters

    @staticmethod
    def _resolve_asset_scope(file_path: Path) -> tuple[str, str]:
        """根据文件路径推导项目与模块归属。"""
        normalized_parts = file_path.resolve().as_posix().split("/")
        if len(normalized_parts) >= 5:
            for index, part in enumerate(normalized_parts):
                if part == "api_test" and index + 4 < len(normalized_parts) and normalized_parts[index + 1] == "core":
                    return normalized_parts[index + 2], normalized_parts[index + 3]
        return "shared", "common"
