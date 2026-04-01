"""中文注释治理测试。"""

from __future__ import annotations

import ast
import io
import json
import re
import subprocess
import tokenize
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PYTHON_TARGETS = ("api_test", "platform_core", "tests")
CHINESE_PATTERN = re.compile(r"[\u4e00-\u9fff]")
JSON_COMMENT_TARGETS = {
    "runtime": ("base_url", "timeout", "verify_ssl", "default_headers"),
    "session": ("pool_connections", "pool_maxsize", "max_retries"),
    "proxy": ("enabled", "url"),
    "execution": ("tests_root", "report_dir", "default_pytest_args", "public_baseline_marker"),
    "logging": (
        "enabled",
        "stack",
        "headers",
        "body",
        "response",
        "trace_id",
        "http_log_info",
        "http_log_conn",
    ),
    "site_profiles": ("jsonplaceholder",),
}


def _contains_chinese(text: str) -> bool:
    """判断文本中是否包含中文字符。"""
    return bool(CHINESE_PATTERN.search(text))


def _tracked_python_files() -> list[Path]:
    """返回当前仓库受版本控制的 Python 文件列表。"""
    result = subprocess.check_output(
        ["git", "ls-files", "*.py"],
        cwd=ROOT,
        text=True,
        encoding="utf-8",
    )
    files = []
    for line in result.splitlines():
        if line.startswith(PYTHON_TARGETS):
            path = ROOT / line
            if path.exists():
                files.append(path)
    return files


def test_tracked_python_files_skip_deleted_worktree_paths(tmp_path, monkeypatch):
    """已从工作树删除但尚未提交的 Python 文件不应继续进入治理扫描。"""
    existing_file = tmp_path / "api_test" / "kept.py"
    existing_file.parent.mkdir(parents=True, exist_ok=True)
    existing_file.write_text('"""中文模块"""', encoding="utf-8")

    monkeypatch.setattr(
        subprocess,
        "check_output",
        lambda *args, **kwargs: "api_test/kept.py\napi_test/removed.py\n",
    )
    monkeypatch.setattr(__import__(__name__), "ROOT", tmp_path)

    files = _tracked_python_files()

    assert files == [existing_file]


def _iter_definitions(tree: ast.AST) -> list[tuple[str, str, int]]:
    """收集模块内需要强制声明中文 docstring 的定义节点。"""
    definitions: list[tuple[str, str, int]] = []
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            definitions.append(("class", node.name, node.lineno))
            for child in node.body:
                if isinstance(child, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    definitions.append(("method", f"{node.name}.{child.name}", child.lineno))
        elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            definitions.append(("function", node.name, node.lineno))
    return definitions


def _read_python_file(path: Path) -> tuple[str, ast.Module]:
    """以兼容 BOM 的方式读取并解析 Python 文件。"""
    source = path.read_text(encoding="utf-8-sig")
    return source, ast.parse(source)


def _iter_comment_tokens(source: str) -> list[str]:
    """提取源码中的行内注释文本。"""
    comments: list[str] = []
    for token in tokenize.generate_tokens(io.StringIO(source).readline):
        if token.type != tokenize.COMMENT:
            continue
        text = token.string.lstrip("#").strip()
        if text and not text.startswith(("!/usr", "-*- coding", "type: ignore", "noqa")):
            comments.append(text)
    return comments


def test_python_modules_classes_and_methods_use_chinese_docstrings():
    """仓库内 Python 模块、类和方法都应带中文 docstring。"""
    missing: list[str] = []
    non_chinese: list[str] = []

    for path in _tracked_python_files():
        source, tree = _read_python_file(path)
        module_docstring = ast.get_docstring(tree)
        rel_path = path.relative_to(ROOT)
        if not module_docstring:
            missing.append(f"模块缺少 docstring: {rel_path}")
        elif not _contains_chinese(module_docstring):
            non_chinese.append(f"模块 docstring 非中文: {rel_path}")

        for kind, name, lineno in _iter_definitions(tree):
            node = None
            for candidate in ast.walk(tree):
                if isinstance(candidate, ast.ClassDef) and kind == "class" and candidate.name == name and candidate.lineno == lineno:
                    node = candidate
                    break
                if isinstance(candidate, (ast.FunctionDef, ast.AsyncFunctionDef)) and kind != "class":
                    qualified = getattr(candidate, "name", "")
                    if qualified == name.split(".")[-1] and candidate.lineno == lineno:
                        node = candidate
                        break
            if node is None:
                continue
            docstring = ast.get_docstring(node)
            if not docstring:
                missing.append(f"{kind} 缺少 docstring: {rel_path}:{lineno} {name}")
            elif not _contains_chinese(docstring):
                non_chinese.append(f"{kind} docstring 非中文: {rel_path}:{lineno} {name}")

        for comment in _iter_comment_tokens(source):
            if not _contains_chinese(comment):
                non_chinese.append(f"行内注释非中文: {rel_path} -> {comment}")

    assert not missing, "\n".join(missing)
    assert not non_chinese, "\n".join(non_chinese)


def test_api_config_json_contains_chinese_comment_fields():
    """唯一配置源中的关键配置项必须带中文说明字段。"""
    config_path = ROOT / "api_test" / "api_config.json"
    payload = json.loads(config_path.read_text(encoding="utf-8"))
    problems: list[str] = []

    if not _contains_chinese(payload.get("_comment", "")):
        problems.append("根节点缺少中文 _comment")

    for section, keys in JSON_COMMENT_TARGETS.items():
        section_payload = payload.get(section)
        if not isinstance(section_payload, dict):
            problems.append(f"{section} 配置段缺失或不是对象")
            continue
        if not _contains_chinese(section_payload.get("_comment", "")):
            problems.append(f"{section} 缺少中文 _comment")
        for key in keys:
            if key not in section_payload:
                problems.append(f"{section}.{key} 缺失")
                continue
            comment_key = f"{key}_comment"
            if not _contains_chinese(str(section_payload.get(comment_key, ""))):
                problems.append(f"{section}.{key} 缺少中文说明字段 {comment_key}")

    assert not problems, "\n".join(problems)
