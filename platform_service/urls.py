"""V2 服务层路由入口。"""

from __future__ import annotations

from django.urls import include, path

from scenario_service.workbench_views import WorkbenchFrontendAssetView, WorkbenchFrontendEntryView


urlpatterns = [
    path("api/v2/scenarios/", include("scenario_service.urls")),
    path("api/v2/workbench/", include("scenario_service.workbench_urls")),
    path("ui/assets/<path:asset_path>/", WorkbenchFrontendAssetView.as_view(), name="workbench-frontend-asset"),
    path("ui/v2/workbench/", WorkbenchFrontendEntryView.as_view(), name="scenario-workbench-legacy"),
    path("ui/v3/workbench/", WorkbenchFrontendEntryView.as_view(), name="scenario-workbench"),
]
