"""V2 服务层路由入口。"""

from __future__ import annotations

from django.urls import include, path


urlpatterns = [
    path("api/v2/scenarios/", include("scenario_service.urls")),
]
