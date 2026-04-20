"""依赖治理测试。"""

from __future__ import annotations

import json
from pathlib import Path


PROJECT_ROOT = Path(__file__).resolve().parents[1]


def test_api_test_requirements_use_fixed_versions_only():
    """`api_test/requirements.txt` 应只包含固定版本约束。"""
    requirements_path = PROJECT_ROOT / "api_test" / "requirements.txt"
    lines = [
        line.strip()
        for line in requirements_path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]

    assert lines == [
        "requests==2.28.0",
        "pytest==7.2.0",
        "allure-pytest==2.13.5",
        "pytest-html==3.1.0",
        "pytest-assume==2.4.3",
        "pytest-rerunfailures==11.0",
        "Jinja2==3.1.0",
        "pydantic==2.7.0",
        "PyYAML==6.0.0",
        "pycryptodome==3.15.0",
        "pandas==1.5.0",
        "python-docx==0.8.11",
        "pdfplumber==0.9.0",
        "PyMySQL==1.0.2",
        "Faker==15.0.0",
    ]


def test_api_test_requirements_no_longer_include_unused_rsa_dependency():
    """`api_test/requirements.txt` 不应再包含未使用的 `rsa` 依赖。"""
    requirements_path = PROJECT_ROOT / "api_test" / "requirements.txt"
    content = requirements_path.read_text(encoding="utf-8")

    assert "rsa" not in content.lower()


def test_platform_service_requirements_use_fixed_versions_only():
    """`requirements-platform-service.txt` 应只包含服务层固定版本依赖。"""
    requirements_path = PROJECT_ROOT / "requirements-platform-service.txt"
    lines = [
        line.strip()
        for line in requirements_path.read_text(encoding="utf-8").splitlines()
        if line.strip() and not line.strip().startswith("#")
    ]

    assert lines == [
        "Django==5.2.9",
        "djangorestframework==3.16.1",
        "PyMySQL==1.0.2",
        "cryptography==43.0.3",
        "cffi==1.17.1",
        "pycparser==2.22",
        "Jinja2==3.1.0",
        "MarkupSafe==3.0.3",
        "pydantic==2.7.0",
        "annotated-types==0.7.0",
        "pydantic-core==2.18.1",
        "typing-extensions==4.15.0",
        "PyYAML==6.0.1",
        "requests==2.32.4",
        "urllib3==2.3.0",
        "charset-normalizer==3.4.1",
        "certifi==2025.1.31",
        "idna==3.10",
        "pytest==8.3.4",
        "pytest-django==4.11.1",
        "pytest-asyncio==0.25.3",
        "asgiref==3.8.1",
        "sqlparse==0.5.3",
        "tzdata==2025.2",
        "colorama==0.4.6",
        "iniconfig==2.0.0",
        "packaging==25.0",
        "pluggy==1.5.0",
    ]


def test_frontend_package_json_uses_fixed_versions_only():
    """`frontend/package.json` 应只包含固定版本依赖。"""
    package_json_path = PROJECT_ROOT / "frontend" / "package.json"
    payload = json.loads(package_json_path.read_text(encoding="utf-8"))

    assert payload["dependencies"] == {
        "vue": "3.4.21",
        "vue-router": "4.3.2",
    }
    assert payload["devDependencies"] == {
        "@vitejs/plugin-vue": "5.0.4",
        "@vue/test-utils": "2.4.5",
        "jsdom": "24.0.0",
        "typescript": "5.4.5",
        "vite": "5.2.11",
        "vitest": "1.6.0",
    }
