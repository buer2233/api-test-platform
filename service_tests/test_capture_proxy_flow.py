"""模块级抓包代理会话测试。"""

from __future__ import annotations

from scenario_service.capture_proxy import CaptureProxyFilter
from scenario_service.services import FunctionalCaseScenarioService


def test_capture_proxy_filter_only_accepts_matching_url_or_ip():
    """抓包前置过滤应只接受命中 URL 前缀或 IP 的请求。"""
    filter_rule = CaptureProxyFilter(url_prefix="https://weapp.mulinquan.cn", ip_address="")

    assert filter_rule.should_capture("https://weapp.mulinquan.cn/api/user/list", "10.0.0.8") is True
    assert filter_rule.should_capture("https://static.example.com/app.js", "10.0.0.8") is False


def test_start_capture_session_persists_filter_and_scope(service_test_token: str):
    """启动抓包会话时应落库记录模块归属与过滤条件。"""
    service = FunctionalCaseScenarioService()

    summary = service.start_capture_session(
        project_code=f"ebuilder-{service_test_token}",
        module_code="app_center",
        submodule_code="eb_app",
        operator="qa-owner",
        filter_rule={"url_prefix": "https://weapp.mulinquan.cn", "ip_address": ""},
        listen_port=8899,
    )

    assert summary["project_code"] == f"ebuilder-{service_test_token}"
    assert summary["module_code"] == "app_center"
    assert summary["submodule_code"] == "eb_app"
    assert summary["filter_rule"]["url_prefix"] == "https://weapp.mulinquan.cn"


def test_capture_records_are_grouped_into_candidate_operations():
    """抓包治理应过滤静态资源，只保留业务接口候选。"""
    service = FunctionalCaseScenarioService()

    candidates = service.build_capture_candidates(
        capture_records=[
            {
                "method": "POST",
                "path": "/api/ebuilder/coms/component/enable",
                "url": "https://weapp.mulinquan.cn/api/ebuilder/coms/component/enable",
                "status_code": 200,
            },
            {
                "method": "GET",
                "path": "/static/app.js",
                "url": "https://weapp.mulinquan.cn/static/app.js",
                "status_code": 200,
            },
        ]
    )

    assert len(candidates) == 1
    assert candidates[0]["method"] == "POST"
    assert candidates[0]["path"] == "/api/ebuilder/coms/component/enable"
