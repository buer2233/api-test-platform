"""Vue 工作台读模型与前端入口相关路由。"""

from __future__ import annotations

from django.urls import path

from scenario_service.workbench_views import (
    TestInterfaceCatalogView,
    TestInterfaceDetailView,
    WorkbenchBootstrapView,
    WorkbenchNavigationView,
)


urlpatterns = [
    path("bootstrap/", WorkbenchBootstrapView.as_view(), name="workbench-bootstrap"),
    path("navigation/", WorkbenchNavigationView.as_view(), name="workbench-navigation"),
    path("test-interfaces/", TestInterfaceCatalogView.as_view(), name="workbench-test-interface-catalog"),
    path(
        "test-interfaces/<str:interface_id>/",
        TestInterfaceDetailView.as_view(),
        name="workbench-test-interface-detail",
    ),
]
