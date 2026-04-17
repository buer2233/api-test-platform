"""主工作台三段式信息架构测试。"""

from __future__ import annotations

from rest_framework.test import APIClient


def test_mainline_workbench_renders_three_column_layout_and_primary_regions():
    """主工作台应渲染三段式布局和核心区域。"""
    client = APIClient()

    response = client.get("/ui/v3/workbench/")

    assert response.status_code == 200
    content = response.content.decode("utf-8")
    assert 'data-testid="mainline-shell"' in content
    assert 'data-testid="left-tree-panel"' in content
    assert 'data-testid="middle-list-panel"' in content
    assert 'data-testid="right-detail-panel"' in content
    assert 'data-testid="capture-entry-actions"' in content
    assert 'data-testid="testcase-list-panel"' in content
    assert 'data-testid="detail-fixed-summary"' in content
    assert 'data-testid="detail-tab-method-chain"' in content
    assert 'data-testid="detail-tab-execution-history"' in content
    assert 'data-testid="detail-tab-allure-report"' in content
