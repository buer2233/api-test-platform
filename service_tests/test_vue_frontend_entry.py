"""Vue 前端入口承接测试。"""

from __future__ import annotations

from rest_framework.test import APIClient


def test_v2_workbench_route_returns_vue_entry_shell():
    """`/ui/v2/workbench/` 应返回 Vue 前端入口而不是旧模板结构。"""
    client = APIClient()

    response = client.get("/ui/v2/workbench/")

    assert response.status_code == 200
    content = response.content.decode("utf-8")
    assert '<div id="app"></div>' in content
    assert "V3 Governance Console" not in content
    assert 'data-testid="workbench-root"' not in content


def test_v3_workbench_route_returns_vue_entry_shell():
    """`/ui/v3/workbench/` 应返回 Vue 前端入口而不是旧模板结构。"""
    client = APIClient()

    response = client.get("/ui/v3/workbench/")

    assert response.status_code == 200
    content = response.content.decode("utf-8")
    assert '<div id="app"></div>' in content
    assert "V3 Governance Console" not in content
    assert 'data-testid="workbench-root"' not in content
