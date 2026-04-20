"""Vue 工作台入口与读模型接口视图。"""

from __future__ import annotations

import json
import mimetypes
from pathlib import Path

from django.http import FileResponse, Http404, HttpResponse
from django.views import View
from rest_framework.response import Response
from rest_framework.views import APIView

from scenario_service.services import FunctionalCaseScenarioService, ScenarioServiceError


WORKBENCH_SERVICE = FunctionalCaseScenarioService()
PROJECT_ROOT = Path(__file__).resolve().parents[1]
FRONTEND_DIST_ROOT = PROJECT_ROOT / "frontend" / "dist"
FRONTEND_INDEX_PATH = FRONTEND_DIST_ROOT / "index.html"


def build_frontend_fallback_html(*, entry_path: str) -> str:
    """构造前端构建产物缺失时的最小 Vue 入口壳层。"""
    bootstrap_payload = {
        "page_title": "抓包与接口自动化工作台",
        "entry_path": entry_path,
        "frontend_framework": "vue3",
        "design_source": "DESIGN.md",
        "api_root": "/api/v2",
    }
    bootstrap_json = json.dumps(bootstrap_payload, ensure_ascii=False)
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link rel="icon" href="data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 64 64'%3E%3Crect width='64' height='64' rx='16' fill='%23fffefb'/%3E%3Cpath d='M18 18h28v8H18zm0 12h18v8H18zm0 12h28v8H18z' fill='%23ff4f00'/%3E%3C/svg%3E">
    <title>抓包与接口自动化工作台</title>
</head>
<body>
    <div id="app"></div>
    <script id="workbench-bootstrap" type="application/json">{bootstrap_json}</script>
</body>
</html>
"""


class WorkbenchFrontendEntryView(View):
    """返回 Vue 工作台前端入口。"""

    entry_path = "/ui/v3/workbench/"

    def get(self, request, *args, **kwargs):
        """优先返回构建后的前端入口，缺失时返回最小兜底壳层。"""
        if FRONTEND_INDEX_PATH.exists():
            return HttpResponse(
                FRONTEND_INDEX_PATH.read_text(encoding="utf-8"),
                content_type="text/html; charset=utf-8",
            )
        return HttpResponse(
            build_frontend_fallback_html(entry_path=self.entry_path),
            content_type="text/html; charset=utf-8",
        )


class WorkbenchFrontendAssetView(View):
    """承接前端构建产物静态资源访问。"""

    def get(self, request, asset_path: str, *args, **kwargs):
        """返回构建后的静态资源文件。"""
        target_path = (FRONTEND_DIST_ROOT / asset_path).resolve()
        if not str(target_path).startswith(str(FRONTEND_DIST_ROOT.resolve())) or not target_path.exists():
            raise Http404("workbench_frontend_asset_not_found")
        content_type, _ = mimetypes.guess_type(target_path.name)
        return FileResponse(target_path.open("rb"), content_type=content_type or "application/octet-stream")


class WorkbenchBootstrapView(APIView):
    """返回 Vue 工作台启动摘要。"""

    def get(self, request):
        """返回前端初始化所需的最小元数据。"""
        return Response({"success": True, "data": WORKBENCH_SERVICE.build_workbench_bootstrap()})


class WorkbenchNavigationView(APIView):
    """返回项目/模块/子模块/测试用例导航树。"""

    def get(self, request):
        """返回 Vue 工作台消费的导航树读模型。"""
        return Response({"success": True, "data": WORKBENCH_SERVICE.build_workbench_navigation()})


class TestInterfaceCatalogView(APIView):
    """返回工作台测试接口目录。"""

    def get(self, request):
        """返回 `api_test` 接口目录扫描摘要。"""
        return Response({"success": True, "data": WORKBENCH_SERVICE.build_test_interface_catalog()})


class TestInterfaceDetailView(APIView):
    """返回单个测试接口详情。"""

    def get(self, request, interface_id: str):
        """返回指定测试接口的详细摘要。"""
        try:
            data = WORKBENCH_SERVICE.get_test_interface_detail(interface_id)
        except ScenarioServiceError as error:
            return Response(
                {
                    "success": False,
                    "error": {
                        "code": error.code,
                        "message": error.message,
                    },
                },
                status=error.status_code,
            )
        return Response({"success": True, "data": data})
