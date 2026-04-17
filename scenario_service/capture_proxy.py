"""抓包代理的最小过滤能力。"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(slots=True)
class CaptureProxyFilter:
    """根据 URL 前缀或 IP 过滤抓包请求。"""

    url_prefix: str = ""
    ip_address: str = ""

    def should_capture(self, request_url: str, remote_ip: str) -> bool:
        """判断当前请求是否应进入抓包记录。"""
        if self.url_prefix and request_url.startswith(self.url_prefix):
            return True
        if self.ip_address and remote_ip == self.ip_address:
            return True
        return False


class CaptureCandidateBuilder:
    """把抓包记录整理为接口候选列表。"""

    def build(self, capture_records: list[dict]) -> list[dict]:
        """过滤静态资源并输出最小候选结构。"""
        candidates: list[dict] = []
        for item in capture_records:
            path = str(item.get("path", ""))
            if path.startswith("/static/"):
                continue
            candidates.append(
                {
                    "method": str(item.get("method", "")).upper(),
                    "path": path,
                    "url": str(item.get("url", "")),
                    "status_code": item.get("status_code"),
                    "selection_state": "unselected",
                }
            )
        return candidates
