"""V2 场景服务路由。"""

from __future__ import annotations

from django.urls import path

from scenario_service.views import (
    BaselineVersionActivateView,
    FunctionalCaseImportView,
    GovernanceContextQueryView,
    GovernanceMigrationStatusView,
    ScenarioListView,
    ScenarioDetailView,
    ScenarioExecuteView,
    ScenarioExportView,
    ScenarioRevisionView,
    ScenarioResultView,
    ScenarioReviewView,
    ScenarioSuggestionApplyView,
    ScenarioSuggestionListView,
    TrafficCaptureImportView,
)


urlpatterns = [
    path("", ScenarioListView.as_view(), name="scenario-list"),
    path("governance/context/", GovernanceContextQueryView.as_view(), name="governance-context"),
    path("governance/migration-status/", GovernanceMigrationStatusView.as_view(), name="governance-migration-status"),
    path(
        "governance/baseline-versions/activate/",
        BaselineVersionActivateView.as_view(),
        name="governance-baseline-version-activate",
    ),
    path("import-functional-case/", FunctionalCaseImportView.as_view(), name="scenario-import-functional-case"),
    path("import-traffic-capture/", TrafficCaptureImportView.as_view(), name="scenario-import-traffic-capture"),
    path("<str:scenario_id>/", ScenarioDetailView.as_view(), name="scenario-detail"),
    path("<str:scenario_id>/review/", ScenarioReviewView.as_view(), name="scenario-review"),
    path("<str:scenario_id>/revise/", ScenarioRevisionView.as_view(), name="scenario-revise"),
    path("<str:scenario_id>/execute/", ScenarioExecuteView.as_view(), name="scenario-execute"),
    path("<str:scenario_id>/export/", ScenarioExportView.as_view(), name="scenario-export"),
    path("<str:scenario_id>/result/", ScenarioResultView.as_view(), name="scenario-result"),
    path("<str:scenario_id>/suggestions/", ScenarioSuggestionListView.as_view(), name="scenario-suggestion-list"),
    path(
        "<str:scenario_id>/suggestions/<str:suggestion_id>/apply/",
        ScenarioSuggestionApplyView.as_view(),
        name="scenario-suggestion-apply",
    ),
]
