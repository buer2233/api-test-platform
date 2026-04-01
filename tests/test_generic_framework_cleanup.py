"""通用框架去特化治理测试。"""

from __future__ import annotations

from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_private_site_legacy_files_are_removed():
    """历史私有站点专用文件应已从当前仓库移除。"""
    deprecated_paths = [
        PROJECT_ROOT / "api_test" / "config.py",
        PROJECT_ROOT / "api_test" / "legacy_api_catalog.py",
        PROJECT_ROOT / "api_test" / "core" / "legacy_assets.py",
        PROJECT_ROOT / "platform_core" / "legacy_assets.py",
        PROJECT_ROOT / "api_test" / "test_data" / "account.txt",
    ]

    existing = [str(path.relative_to(PROJECT_ROOT)) for path in deprecated_paths if path.exists()]

    assert existing == []


def test_active_docs_no_longer_describe_private_site_bridge_as_current_state():
    """主文档不应再把旧私有站点桥接描述为当前能力。"""
    doc_paths = [
        PROJECT_ROOT / "README.md",
        PROJECT_ROOT / "api_test" / "README.md",
        PROJECT_ROOT / "api_test" / "QUICKSTART.md",
        PROJECT_ROOT / "product_document" / "架构设计" / "现有接口自动化测试框架改造方案.md",
        PROJECT_ROOT / "product_document" / "阶段文档" / "V1阶段工作计划文档.md",
        PROJECT_ROOT / "product_document" / "阶段文档" / "V1实施计划与开发任务拆解说明书.md",
        PROJECT_ROOT / "product_document" / "测试文档" / "详细测试用例说明书(V1).md",
    ]
    forbidden_terms = [
        "inspect-legacy-public-api",
        "snapshot-legacy-public-api",
        "legacy_api_catalog",
        "API_TEST_RSA_PUBLIC_KEY",
        "private_env",
    ]

    violations: list[str] = []
    for doc_path in doc_paths:
        content = doc_path.read_text(encoding="utf-8")
        for term in forbidden_terms:
            if term in content:
                violations.append(f"{doc_path.relative_to(PROJECT_ROOT)} -> {term}")

    assert violations == []
