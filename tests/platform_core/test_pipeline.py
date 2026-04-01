"""文档驱动闭环与执行器测试。"""

import json
import subprocess
import sys
from pathlib import Path
from xml.etree import ElementTree

from platform_core.executors import PytestExecutor
from platform_core.pipeline import DocumentDrivenPipeline


def build_openapi_spec() -> dict:
    """构造单接口 OpenAPI 文档样例。"""
    return {
        "openapi": "3.0.0",
        "info": {"title": "User API", "version": "1.0.0"},
        "paths": {
            "/api/users/{user_id}": {
                "get": {
                    "tags": ["user"],
                    "operationId": "getUserProfile",
                    "summary": "获取用户详情",
                    "parameters": [
                        {
                            "name": "user_id",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string"},
                        },
                        {
                            "name": "verbose",
                            "in": "query",
                            "required": False,
                            "schema": {"type": "boolean", "default": False},
                        },
                    ],
                    "responses": {
                        "200": {
                            "description": "success",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "code": {"type": "integer", "example": 0},
                                            "data": {
                                                "type": "object",
                                                "properties": {
                                                    "id": {"type": "string", "example": "u-100"},
                                                    "name": {"type": "string", "example": "Alice"},
                                                },
                                            },
                                        },
                                    }
                                }
                            },
                        }
                    },
                }
            }
        },
    }


def build_multi_operation_openapi_spec() -> dict:
    """构造多接口 OpenAPI 文档样例。"""
    return {
        "openapi": "3.0.0",
        "info": {"title": "User API", "version": "1.0.0"},
        "paths": {
            "/api/users": {
                "get": {
                    "tags": ["user"],
                    "operationId": "listUsers",
                    "summary": "查询用户列表",
                    "responses": {
                        "200": {
                            "description": "success",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "data": {
                                                "type": "array",
                                                "items": {"type": "string"},
                                            }
                                        },
                                    }
                                }
                            },
                        }
                    },
                }
            },
            "/api/users/{user_id}": {
                "get": {
                    "tags": ["user"],
                    "operationId": "getUserProfile",
                    "summary": "获取用户详情",
                    "parameters": [
                        {
                            "name": "user_id",
                            "in": "path",
                            "required": True,
                            "schema": {"type": "string"},
                        }
                    ],
                    "responses": {
                        "200": {
                            "description": "success",
                            "content": {
                                "application/json": {
                                    "schema": {
                                        "type": "object",
                                        "properties": {
                                            "data": {
                                                "type": "object",
                                                "properties": {
                                                    "id": {"type": "string", "example": "u-100"}
                                                },
                                            }
                                        },
                                    }
                                }
                            },
                        }
                    },
                }
            },
        },
    }


def test_pytest_executor_runs_smoke_test_and_returns_execution_record(tmp_path):
    """TC-V1-EXEC-001/002/003 执行器应完成最小 smoke 执行并输出记录。"""
    output_root = tmp_path / "workspace"
    test_dir = output_root / "generated" / "tests"
    report_dir = output_root / "generated" / "reports"
    test_dir.mkdir(parents=True)
    report_dir.mkdir(parents=True)

    test_file = test_dir / "test_generated_smoke.py"
    test_file.write_text(
        "def test_generated_smoke():\n    assert True\n",
        encoding="utf-8",
    )

    executor = PytestExecutor(project_root=Path.cwd())
    record = executor.run(test_file, output_root=output_root, target_id="generated-smoke")

    assert record.execution_level == "smoke"
    assert record.result_status == "passed"
    assert Path(record.report_path).exists()
    assert record.target_id == "generated-smoke"


def test_document_driven_pipeline_generates_traceable_assets_and_executes_pytest(tmp_path):
    """TC-V1-INT-001/002 文档驱动最小闭环应生成资产、记录并可执行。"""
    source_path = tmp_path / "user_openapi.json"
    source_path.write_text(json.dumps(build_openapi_spec(), ensure_ascii=False, indent=2), encoding="utf-8")

    output_root = tmp_path / "workspace"
    pipeline = DocumentDrivenPipeline(project_root=Path.cwd())

    result = pipeline.run(source_path=source_path, output_root=output_root)

    api_file = output_root / "generated" / "apis" / "user_api.py"
    test_file = output_root / "generated" / "tests" / "test_get_user_profile.py"
    records_dir = output_root / "generated" / "records"

    assert result.source_document.source_type == "openapi"
    assert len(result.modules) == 1
    assert len(result.operations) == 1
    assert api_file.exists()
    assert test_file.exists()
    assert any(record.target_asset_path.endswith("user_api.py") for record in result.generation_records)
    assert any(record.target_asset_path.endswith("test_get_user_profile.py") for record in result.generation_records)
    assert result.execution_record.result_status == "passed"
    assert Path(result.execution_record.report_path).exists()
    assert any(record.name.endswith(".json") for record in records_dir.iterdir())


def test_document_driven_pipeline_executes_all_generated_tests_for_multiple_operations(tmp_path):
    """批量接口闭环应执行全部生成测试，而不是只执行第一个。"""
    source_path = tmp_path / "user_openapi.json"
    source_path.write_text(json.dumps(build_multi_operation_openapi_spec(), ensure_ascii=False, indent=2), encoding="utf-8")

    output_root = tmp_path / "workspace"
    pipeline = DocumentDrivenPipeline(project_root=Path.cwd())

    result = pipeline.run(source_path=source_path, output_root=output_root)

    tests_dir = output_root / "generated" / "tests"
    report_xml = ElementTree.parse(result.execution_record.report_path)
    report_root = report_xml.getroot()
    testsuite = report_root.find("testsuite") if report_root.tag == "testsuites" else report_root

    assert (tests_dir / "test_list_users.py").exists()
    assert (tests_dir / "test_get_user_profile.py").exists()
    assert result.execution_record.target_id == "generated-suite"
    assert testsuite is not None
    assert testsuite.attrib["tests"] == "2"


def test_platform_core_cli_runs_document_pipeline(tmp_path):
    """CLI 应支持直接执行文档驱动最小闭环。"""
    source_path = tmp_path / "user_openapi.json"
    source_path.write_text(json.dumps(build_openapi_spec(), ensure_ascii=False, indent=2), encoding="utf-8")
    output_root = tmp_path / "cli-workspace"

    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "platform_core.cli",
            "run",
            "--source",
            str(source_path),
            "--output",
            str(output_root),
        ],
        cwd=Path.cwd(),
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, result.stderr
    assert "generated-suite" in result.stdout
    assert (output_root / "generated" / "apis" / "user_api.py").exists()
