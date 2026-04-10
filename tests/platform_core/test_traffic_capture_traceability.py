"""V2 P1 抓包问题分类与来源元数据测试。"""

from __future__ import annotations

import json

from platform_core.traffic_capture import TrafficCaptureDraftParser


def test_traffic_capture_parser_emits_quality_issues_and_source_metadata(tmp_path):
    """抓包解析器应输出细粒度问题标签和来源元数据。"""
    source_path = tmp_path / "trace.har.json"
    source_path.write_text(
        json.dumps(
            {
                "log": {
                    "entries": [
                        {
                            "startedDateTime": "2026-04-10T08:00:00.000Z",
                            "request": {"method": "GET", "url": "https://cdn.example.com/app.js"},
                            "response": {"status": 200, "content": {"mimeType": "application/javascript"}},
                        },
                        {
                            "startedDateTime": "2026-04-10T08:00:01.000Z",
                            "request": {"method": "POST", "url": "https://api.example.com/v1/login"},
                            "response": {
                                "status": 200,
                                "content": {"mimeType": "application/json", "text": "{\"token\":\"abc\"}"},
                            },
                        },
                        {
                            "startedDateTime": "2026-04-10T08:00:02.000Z",
                            "request": {"method": "GET", "url": "https://api.example.com/v1/users/1?a=1&b=2"},
                            "response": {
                                "status": 200,
                                "content": {"mimeType": "application/json", "text": "{\"id\":1,\"name\":\"A\"}"},
                            },
                        },
                        {
                            "startedDateTime": "2026-04-10T08:00:03.000Z",
                            "request": {"method": "GET", "url": "https://api.example.com/v1/users/1?b=2&a=1"},
                            "response": {
                                "status": 200,
                                "content": {"mimeType": "application/json", "text": "{\"id\":1,\"name\":\"A\"}"},
                            },
                        },
                    ]
                }
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )

    draft = TrafficCaptureDraftParser().parse(source_path)
    issue_codes = {issue.issue_code for issue in draft.issues}
    step_metadata = draft.steps[0].metadata

    assert "static_noise_filtered" in issue_codes
    assert "duplicate_request_group" in issue_codes
    assert "capture_operation_needs_review" in issue_codes
    assert step_metadata["source_traces"][0]["source_type"] == "traffic_capture"
    assert step_metadata["source_traces"][0]["confidence"] == "low"
    assert "capture_operation_needs_review" in step_metadata["source_traces"][0]["issue_tags"]
