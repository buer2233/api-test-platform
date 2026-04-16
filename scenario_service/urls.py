"""V2 场景服务路由。"""

from __future__ import annotations

from django.urls import path

from scenario_service.views import (
    BaselineVersionActivateView,
    FunctionalCaseImportView,
    GovernanceContextQueryView,
    GovernanceMigrationStatusView,
    ProjectRoleAssignmentView,
    ScheduleBatchDetailView,
    ScheduleBatchListCreateView,
    ScheduleItemCancelView,
    ScheduleItemRetryView,
    ScenarioListView,
    ScenarioAuditLogListView,
    ScenarioDetailView,
    ScenarioExecuteView,
    ScenarioExportView,
    ScenarioRevisionView,
    ScenarioResultView,
    ScenarioReviewView,
    ScenarioSuggestionApplyView,
    ScenarioSuggestionListView,
    TrafficCaptureBindingConfirmView,
    TrafficCaptureConfirmView,
    TrafficCaptureImportView,
    WindowsDemoManifestView,
)


urlpatterns = [
    path("", ScenarioListView.as_view(), name="scenario-list"),
    path("governance/context/", GovernanceContextQueryView.as_view(), name="governance-context"),
    path("governance/migration-status/", GovernanceMigrationStatusView.as_view(), name="governance-migration-status"),
    path("governance/windows-demo/", WindowsDemoManifestView.as_view(), name="governance-windows-demo"),
    path("governance/access-grants/", ProjectRoleAssignmentView.as_view(), name="governance-access-grants"),
    path("governance/audit-logs/", ScenarioAuditLogListView.as_view(), name="governance-audit-logs"),
    path("governance/schedule-batches/", ScheduleBatchListCreateView.as_view(), name="governance-schedule-batches"),
    path(
        "governance/schedule-batches/<str:schedule_batch_id>/",
        ScheduleBatchDetailView.as_view(),
        name="governance-schedule-batch-detail",
    ),
    path(
        "governance/schedule-batches/<str:schedule_batch_id>/items/<str:schedule_item_id>/retry/",
        ScheduleItemRetryView.as_view(),
        name="governance-schedule-item-retry",
    ),
    path(
        "governance/schedule-batches/<str:schedule_batch_id>/items/<str:schedule_item_id>/cancel/",
        ScheduleItemCancelView.as_view(),
        name="governance-schedule-item-cancel",
    ),
    path(
        "governance/baseline-versions/activate/",
        BaselineVersionActivateView.as_view(),
        name="governance-baseline-version-activate",
    ),
    path("import-functional-case/", FunctionalCaseImportView.as_view(), name="scenario-import-functional-case"),
    path("import-traffic-capture/", TrafficCaptureImportView.as_view(), name="scenario-import-traffic-capture"),
    path(
        "<str:scenario_id>/traffic-capture/confirm/",
        TrafficCaptureConfirmView.as_view(),
        name="scenario-traffic-capture-confirm",
    ),
    path(
        "<str:scenario_id>/traffic-capture/bindings/confirm/",
        TrafficCaptureBindingConfirmView.as_view(),
        name="scenario-traffic-capture-binding-confirm",
    ),
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
