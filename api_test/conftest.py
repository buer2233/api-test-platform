"""Shared pytest fixtures and report hooks for the generic api_test suite."""

from __future__ import annotations

from datetime import datetime

import pytest
from py.xml import html

from core.config_loader import get_api_config
from core.jsonplaceholder_api import JsonPlaceholderAPI


@pytest.fixture(scope="function")
def base_url() -> str:
    return get_api_config().runtime.base_url


@pytest.fixture(scope="function")
def jsonplaceholder_api():
    api = JsonPlaceholderAPI()
    yield api
    api.session.close()


@pytest.fixture(autouse=True)
def test_description(request):
    description = getattr(getattr(request.node, "_obj", None), "__doc__", None) or "未提供用例描述"
    request.node._description = description
    yield


@pytest.hookimpl(optionalhook=True)
def pytest_html_results_summary(prefix, summary, postfix):
    prefix.extend([html.p(f"测试环境: {get_api_config().runtime.base_url}")])
    prefix.extend([html.p(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")])


@pytest.hookimpl(optionalhook=True)
def pytest_html_results_table_header(cells):
    cells.insert(1, html.th("描述"))
    cells.insert(2, html.th("用例ID"))
    cells.insert(3, html.th("状态"))


@pytest.hookimpl(optionalhook=True)
def pytest_html_results_table_row(report, cells):
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
    outcome = yield
    report = outcome.get_result()
    report.description = getattr(item, "_description", "未提供用例描述")


@pytest.hookimpl(optionalhook=True)
def pytest_html_results_table_html(report, data):
    if report.passed:
        data[:] = [html.div("测试通过，无详细日志", class_="empty log")]
