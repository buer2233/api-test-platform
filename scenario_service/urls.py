"""V2 场景服务路由。"""

from __future__ import annotations

from django.urls import path

from scenario_service.views import (
    FunctionalCaseImportView,
    ScenarioListView,
    ScenarioDetailView,
    ScenarioExecuteView,
    ScenarioRevisionView,
    ScenarioResultView,
    ScenarioReviewView,
    TrafficCaptureImportView,
)


urlpatterns = [
    path("", ScenarioListView.as_view(), name="scenario-list"),
    path("import-functional-case/", FunctionalCaseImportView.as_view(), name="scenario-import-functional-case"),
    path("import-traffic-capture/", TrafficCaptureImportView.as_view(), name="scenario-import-traffic-capture"),
    path("<str:scenario_id>/", ScenarioDetailView.as_view(), name="scenario-detail"),
    path("<str:scenario_id>/review/", ScenarioReviewView.as_view(), name="scenario-review"),
    path("<str:scenario_id>/revise/", ScenarioRevisionView.as_view(), name="scenario-revise"),
    path("<str:scenario_id>/execute/", ScenarioExecuteView.as_view(), name="scenario-execute"),
    path("<str:scenario_id>/result/", ScenarioResultView.as_view(), name="scenario-result"),
]
