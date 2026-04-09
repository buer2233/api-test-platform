"""V2 服务层路由入口。"""

from __future__ import annotations

from django.urls import include, path

from scenario_service.views import ScenarioWorkbenchView


urlpatterns = [
    path("api/v2/scenarios/", include("scenario_service.urls")),
    path("ui/v2/workbench/", ScenarioWorkbenchView.as_view(), name="scenario-workbench"),
]
