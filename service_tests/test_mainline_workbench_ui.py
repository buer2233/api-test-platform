"""主工作台三段式信息架构测试。"""

from __future__ import annotations

from html.parser import HTMLParser

from rest_framework.test import APIClient


class TestIdStructureParser(HTMLParser):
    """解析页面中的 data-testid 归属关系。"""

    def __init__(self) -> None:
        """初始化测试标识结构解析器。"""
        super().__init__()
        self._stack: list[tuple[str, str | None]] = []
        self.descendants: dict[str, set[str]] = {}
        self.direct_children: dict[str, list[str]] = {}

    def _find_nearest_parent_testid(self) -> str | None:
        """返回当前栈中最近的测试标识父节点。"""
        for _, item in reversed(self._stack):
            if item:
                return item
        return None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        """记录开始标签与其祖先测试标识的从属关系。"""
        attributes = dict(attrs)
        testid = attributes.get("data-testid")
        parent_testid = self._find_nearest_parent_testid()
        for _, ancestor in self._stack:
            if ancestor:
                self.descendants.setdefault(ancestor, set())
                if testid:
                    self.descendants[ancestor].add(testid)
        if testid:
            self.descendants.setdefault(testid, set())
            self.direct_children.setdefault(testid, [])
            if parent_testid:
                self.direct_children.setdefault(parent_testid, []).append(testid)
        self._stack.append((tag, testid))

    def handle_endtag(self, tag: str) -> None:
        """在标签闭合时弹出当前层级。"""
        while self._stack:
            current_tag, _ = self._stack.pop()
            if current_tag == tag:
                break


def test_mainline_workbench_renders_three_column_layout_and_primary_regions():
    """主工作台应在保留既有 V3 面板契约的前提下渲染三段式布局。"""
    client = APIClient()

    response = client.get("/ui/v3/workbench/")

    assert response.status_code == 200
    content = response.content.decode("utf-8")
    parser = TestIdStructureParser()
    parser.feed(content)

    assert "V3 场景工作台" in content
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
    assert "导入功能用例" in content
    assert "导入抓包草稿" in content
    assert 'data-testid="actor-panel"' in content
    assert 'data-testid="access-grant-panel"' in content
    assert 'data-testid="audit-log-panel"' in content
    assert 'data-testid="traffic-capture-formalization-panel"' in content
    assert 'data-testid="schedule-center-panel"' in content
    assert 'data-testid="windows-demo-panel"' in content
    assert parser.direct_children["mainline-shell"] == [
        "left-tree-panel",
        "middle-list-panel",
        "right-detail-panel",
    ]
    assert "testcase-list-panel" in parser.descendants["left-tree-panel"]
    assert "capture-entry-actions" in parser.descendants["middle-list-panel"]
    assert "actor-panel" in parser.descendants["middle-list-panel"]
    assert "access-grant-panel" in parser.descendants["middle-list-panel"]
    assert "audit-log-panel" in parser.descendants["middle-list-panel"]
    assert "detail-fixed-summary" in parser.descendants["right-detail-panel"]
    assert "detail-tab-method-chain" in parser.descendants["right-detail-panel"]
    assert "detail-tab-execution-history" in parser.descendants["right-detail-panel"]
    assert "detail-tab-allure-report" in parser.descendants["right-detail-panel"]
    assert "traffic-capture-formalization-panel" in parser.descendants["right-detail-panel"]
    assert "windows-demo-panel" in parser.descendants["right-detail-panel"]
    assert "schedule-center-panel" in parser.descendants["right-detail-panel"]
