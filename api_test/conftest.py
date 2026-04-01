"""`api_test` 公共 pytest fixture 与报告钩子。"""

from __future__ import annotations

from datetime import datetime

import pytest
from py.xml import html

from core.config_loader import get_api_config
from core.jsonplaceholder_api import JsonPlaceholderAPI


@pytest.fixture(scope="function")
def base_url() -> str:
    """返回当前公开基线使用的基础地址。"""
    return get_api_config().runtime.base_url


@pytest.fixture(scope="function")
def jsonplaceholder_api():
    """提供 JSONPlaceholder API 封装实例，并在用例结束后关闭会话。"""
    api = JsonPlaceholderAPI()
    yield api
    api.session.close()


@pytest.fixture(autouse=True)
def test_description(request):
    """把测试函数的 docstring 同步到 HTML 报告描述列。"""
    description = getattr(getattr(request.node, "_obj", None), "__doc__", None) or "未提供用例描述"
    request.node._description = description
    yield


@pytest.hookimpl(optionalhook=True)
def pytest_html_results_summary(prefix, summary, postfix):
    """在 HTML 报告头部追加测试环境和执行时间。"""
    prefix.extend([html.p(f"测试环境: {get_api_config().runtime.base_url}")])
    prefix.extend([html.p(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")])


@pytest.hookimpl(optionalhook=True)
def pytest_html_results_table_header(cells):
    """自定义 HTML 报告表头列。"""
    cells.insert(1, html.th("描述"))
    cells.insert(2, html.th("用例ID"))
    cells.insert(3, html.th("状态"))


@pytest.hookimpl(optionalhook=True)
def pytest_html_results_table_row(report, cells):
    """把中文描述和状态信息写入 HTML 报告每一行。"""
    description = getattr(report, "description", "") or str(report.nodeid)
    cells.insert(1, html.td(description))
    cells.insert(2, html.td(report.nodeid))
    if report.passed:
        status = '<span style="color:green">通过</span>'
    elif report.failed:
        status = '<span style="color:red">失败</span>'
    else:
        status = '<span style="color:orange">跳过</span>'
    cells.insert(3, html.td(status))


@pytest.hookimpl(hookwrapper=True, tryfirst=True)
def pytest_runtest_makereport(item, call):
    """在 pytest 生成报告对象时挂载中文描述字段。"""
    outcome = yield
    report = outcome.get_result()
    report.description = getattr(item, "_description", "未提供用例描述")


@pytest.hookimpl(optionalhook=True)
def pytest_html_results_table_html(report, data):
    """在通过用例时输出精简的通过信息。"""
    if report.passed:
        data[:] = [html.div("测试通过，无详细日志", class_="empty log")]
