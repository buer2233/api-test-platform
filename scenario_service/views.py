"""V2 场景服务接口视图。"""

from __future__ import annotations

from django.views.generic import TemplateView
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from scenario_service.serializers import (
    BaselineVersionActivateSerializer,
    FunctionalCaseImportRequestSerializer,
    ProjectRoleAssignmentQuerySerializer,
    ProjectRoleAssignmentRequestSerializer,
    ScheduleBatchCreateRequestSerializer,
    ScheduleBatchDetailQuerySerializer,
    ScheduleBatchListQuerySerializer,
    ScheduleItemCancelRequestSerializer,
    ScheduleItemRetryRequestSerializer,
    ScenarioListQuerySerializer,
    ScenarioAuditLogQuerySerializer,
    ScenarioExportRequestSerializer,
    ScenarioRevisionRequestSerializer,
    ScenarioReviewRequestSerializer,
    ScenarioSuggestionApplyRequestSerializer,
    ScenarioSuggestionRequestSerializer,
    TrafficCaptureBindingConfirmRequestSerializer,
    TrafficCaptureConfirmRequestSerializer,
    TrafficCaptureImportRequestSerializer,
)
from scenario_service.services import FunctionalCaseScenarioService, ScenarioServiceError
from scenario_service.windows_demo import build_windows_demo_manifest


SCENARIO_SERVICE = FunctionalCaseScenarioService()


def build_error_response(error: ScenarioServiceError) -> Response:
    """构造统一结构化错误响应。"""
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


class FunctionalCaseImportView(APIView):
    """导入功能测试用例并创建场景草稿。"""

    def post(self, request):
        """处理导入请求。"""
        serializer = FunctionalCaseImportRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            scenario = SCENARIO_SERVICE.import_functional_case(serializer.validated_data)
        except ScenarioServiceError as error:
            return build_error_response(error)
        return Response(
            {"success": True, "data": SCENARIO_SERVICE.build_scenario_summary(scenario)},
            status=status.HTTP_201_CREATED,
        )


class TrafficCaptureImportView(APIView):
    """导入抓包数据并创建场景草稿。"""

    def post(self, request):
        """处理抓包导入请求。"""
        serializer = TrafficCaptureImportRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            scenario = SCENARIO_SERVICE.import_traffic_capture(
                capture_name=serializer.validated_data["capture_name"],
                capture_payload=serializer.validated_data["capture_payload"],
                project_code=serializer.validated_data.get("project_code"),
                environment_code=serializer.validated_data.get("environment_code"),
                scenario_set_code=serializer.validated_data.get("scenario_set_code"),
            )
        except ScenarioServiceError as error:
            return build_error_response(error)
        return Response(
            {"success": True, "data": SCENARIO_SERVICE.build_scenario_summary(scenario)},
            status=status.HTTP_201_CREATED,
        )


class TrafficCaptureConfirmView(APIView):
    """处理抓包场景正式确认请求。"""

    def post(self, request, scenario_id: str):
        """处理抓包场景正式确认动作。"""
        serializer = TrafficCaptureConfirmRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            data = SCENARIO_SERVICE.confirm_traffic_capture(
                scenario_id=scenario_id,
                confirmer=serializer.validated_data["confirmer"],
                confirm_comment=serializer.validated_data.get("confirm_comment", ""),
            )
        except ScenarioServiceError as error:
            return build_error_response(error)
        return Response({"success": True, "data": data})


class TrafficCaptureBindingConfirmView(APIView):
    """处理抓包步骤绑定确认请求。"""

    def post(self, request, scenario_id: str):
        """处理抓包步骤绑定确认动作。"""
        serializer = TrafficCaptureBindingConfirmRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            data = SCENARIO_SERVICE.confirm_traffic_capture_bindings(
                scenario_id=scenario_id,
                confirmer=serializer.validated_data["confirmer"],
                step_bindings=serializer.validated_data["step_bindings"],
                confirm_comment=serializer.validated_data.get("confirm_comment", ""),
            )
        except ScenarioServiceError as error:
            return build_error_response(error)
        return Response({"success": True, "data": data})


class ScenarioListView(APIView):
    """返回可用型入口消费的场景摘要列表。"""

    def get(self, request):
        """处理场景列表查询。"""
        serializer = ScenarioListQuerySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        try:
            data = SCENARIO_SERVICE.list_scenarios(serializer.validated_data)
        except ScenarioServiceError as error:
            return build_error_response(error)
        return Response({"success": True, "data": data})


class GovernanceContextQueryView(APIView):
    """返回治理入口使用的项目树摘要。"""

    def get(self, request):
        """处理治理上下文查询。"""
        return Response({"success": True, "data": SCENARIO_SERVICE.get_governance_context()})


class GovernanceMigrationStatusView(APIView):
    """返回默认项目迁移状态摘要。"""

    def get(self, request):
        """处理迁移状态查询。"""
        return Response({"success": True, "data": SCENARIO_SERVICE.governance_service.get_migration_status_summary()})


class WindowsDemoManifestView(APIView):
    """返回 Windows Demo 启动清单。"""

    def get(self, request):
        """返回浏览器先验与 Windows 启动器共享的 Demo manifest。"""
        base_url = request.query_params.get("base_url") or request.build_absolute_uri("/").rstrip("/")
        return Response({"success": True, "data": build_windows_demo_manifest(base_url=base_url)})


class BaselineVersionActivateView(APIView):
    """处理当前生效版本切换请求。"""

    def post(self, request):
        """激活目标基线版本。"""
        serializer = BaselineVersionActivateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        return Response(
            {
                "success": True,
                "data": SCENARIO_SERVICE.activate_baseline_version(**serializer.validated_data),
            }
        )


class ProjectRoleAssignmentView(APIView):
    """处理项目角色授权的查询与写入请求。"""

    def get(self, request):
        """处理项目成员角色查询。"""
        serializer = ProjectRoleAssignmentQuerySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        return Response({"success": True, "data": SCENARIO_SERVICE.list_project_roles(**serializer.validated_data)})

    def post(self, request):
        """处理项目成员角色写入。"""
        serializer = ProjectRoleAssignmentRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            data = SCENARIO_SERVICE.assign_project_role(**serializer.validated_data)
        except ScenarioServiceError as error:
            return build_error_response(error)
        return Response({"success": True, "data": data}, status=status.HTTP_201_CREATED)


class ScenarioAuditLogListView(APIView):
    """处理项目审计日志查询请求。"""

    def get(self, request):
        """按治理维度返回审计日志列表。"""
        serializer = ScenarioAuditLogQuerySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        return Response({"success": True, "data": SCENARIO_SERVICE.list_audit_logs(**serializer.validated_data)})


class ScheduleBatchListCreateView(APIView):
    """处理调度批次的查询与创建请求。"""

    def get(self, request):
        """按项目边界返回调度批次列表。"""
        serializer = ScheduleBatchListQuerySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        try:
            data = SCENARIO_SERVICE.list_schedule_batches(**serializer.validated_data)
        except ScenarioServiceError as error:
            return build_error_response(error)
        return Response({"success": True, "data": data})

    def post(self, request):
        """创建调度批次并按策略立即执行或排队。"""
        serializer = ScheduleBatchCreateRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            data = SCENARIO_SERVICE.create_schedule_batch(**serializer.validated_data)
        except ScenarioServiceError as error:
            return build_error_response(error)
        return Response({"success": True, "data": data}, status=status.HTTP_201_CREATED)


class ScheduleBatchDetailView(APIView):
    """处理调度批次详情查询请求。"""

    def get(self, request, schedule_batch_id: str):
        """返回指定调度批次详情。"""
        serializer = ScheduleBatchDetailQuerySerializer(data=request.query_params)
        serializer.is_valid(raise_exception=True)
        try:
            data = SCENARIO_SERVICE.get_schedule_batch_detail(
                schedule_batch_id=schedule_batch_id,
                actor=serializer.validated_data.get("actor"),
            )
        except ScenarioServiceError as error:
            return build_error_response(error)
        return Response({"success": True, "data": data})


class ScheduleItemRetryView(APIView):
    """处理调度任务项重试请求。"""

    def post(self, request, schedule_batch_id: str, schedule_item_id: str):
        """触发指定调度任务项重试。"""
        serializer = ScheduleItemRetryRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            data = SCENARIO_SERVICE.retry_schedule_item(
                schedule_batch_id=schedule_batch_id,
                schedule_item_id=schedule_item_id,
                scheduler=serializer.validated_data["scheduler"],
                workspace_root=serializer.validated_data.get("workspace_root", ""),
            )
        except ScenarioServiceError as error:
            return build_error_response(error)
        return Response({"success": True, "data": data})


class ScheduleItemCancelView(APIView):
    """处理调度任务项取消请求。"""

    def post(self, request, schedule_batch_id: str, schedule_item_id: str):
        """取消指定调度任务项。"""
        serializer = ScheduleItemCancelRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            data = SCENARIO_SERVICE.cancel_schedule_item(
                schedule_batch_id=schedule_batch_id,
                schedule_item_id=schedule_item_id,
                scheduler=serializer.validated_data["scheduler"],
                cancel_reason=serializer.validated_data.get("cancel_reason", ""),
            )
        except ScenarioServiceError as error:
            return build_error_response(error)
        return Response({"success": True, "data": data})


class ScenarioDetailView(APIView):
    """返回场景详情。"""

    def get(self, request, scenario_id: str):
        """处理详情查询请求。"""
        try:
            detail = SCENARIO_SERVICE.get_scenario_detail(
                scenario_id=scenario_id,
                actor=request.query_params.get("actor"),
            )
        except ScenarioServiceError as error:
            return build_error_response(error)
        return Response({"success": True, "data": detail})


class ScenarioReviewView(APIView):
    """处理场景审核请求。"""

    def post(self, request, scenario_id: str):
        """处理审核动作。"""
        serializer = ScenarioReviewRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            scenario = SCENARIO_SERVICE.review_scenario(
                scenario_id=scenario_id,
                review_status=serializer.validated_data["review_status"],
                reviewer=serializer.validated_data["reviewer"],
                review_comment=serializer.validated_data.get("review_comment", ""),
            )
        except ScenarioServiceError as error:
            return build_error_response(error)
        except ValueError as error:
            return build_error_response(
                ScenarioServiceError(code="invalid_transition", message=str(error), status_code=400)
            )
        return Response({"success": True, "data": SCENARIO_SERVICE.build_scenario_summary(scenario)})


class ScenarioRevisionView(APIView):
    """处理场景结构化修订请求。"""

    def post(self, request, scenario_id: str):
        """处理结构化修订动作。"""
        serializer = ScenarioRevisionRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        scenario_patch = {
            key: value
            for key, value in serializer.validated_data.items()
            if key not in {"reviser", "revision_comment"}
        }
        try:
            scenario = SCENARIO_SERVICE.revise_scenario(
                scenario_id=scenario_id,
                reviser=serializer.validated_data["reviser"],
                revision_comment=serializer.validated_data.get("revision_comment", ""),
                scenario_patch=scenario_patch,
            )
        except ScenarioServiceError as error:
            return build_error_response(error)
        return Response({"success": True, "data": SCENARIO_SERVICE.build_scenario_summary(scenario)})


class ScenarioExecuteView(APIView):
    """处理场景执行触发请求。"""

    def post(self, request, scenario_id: str):
        """处理执行触发动作。"""
        try:
            workspace_root = None
            project_code = None
            environment_code = None
            operator = None
            if isinstance(request.data, dict):
                workspace_root = request.data.get("workspace_root")
                project_code = request.data.get("project_code")
                environment_code = request.data.get("environment_code")
                operator = request.data.get("operator")
            execution = SCENARIO_SERVICE.request_execution(
                scenario_id=scenario_id,
                project_code=project_code,
                environment_code=environment_code,
                workspace_root=workspace_root,
                operator=operator,
            )
        except ScenarioServiceError as error:
            return build_error_response(error)
        return Response(
            {
                "success": True,
                "data": {
                    "scenario_id": scenario_id,
                    "execution_id": execution.execution_id,
                    "execution_status": execution.execution_status,
                },
            },
            status=status.HTTP_202_ACCEPTED,
        )


class ScenarioExportView(APIView):
    """处理场景导出请求。"""

    def post(self, request, scenario_id: str):
        """按项目归属导出场景详情快照。"""
        serializer = ScenarioExportRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            export_result = SCENARIO_SERVICE.export_scenario_bundle(
                scenario_id=scenario_id,
                project_code=serializer.validated_data["project_code"],
                export_root=serializer.validated_data.get("export_root", ""),
            )
        except ScenarioServiceError as error:
            return build_error_response(error)
        return Response({"success": True, "data": export_result})


class ScenarioResultView(APIView):
    """返回统一结果摘要。"""

    def get(self, request, scenario_id: str):
        """处理结果查询请求。"""
        try:
            result = SCENARIO_SERVICE.get_scenario_result(
                scenario_id=scenario_id,
                actor=request.query_params.get("actor"),
            )
        except ScenarioServiceError as error:
            return build_error_response(error)
        return Response({"success": True, "data": result})


class ScenarioSuggestionListView(APIView):
    """处理场景建议的查询与创建请求。"""

    def get(self, request, scenario_id: str):
        """返回指定场景的建议列表。"""
        try:
            suggestions = SCENARIO_SERVICE.list_suggestions(scenario_id=scenario_id)
        except ScenarioServiceError as error:
            return build_error_response(error)
        return Response({"success": True, "data": suggestions})

    def post(self, request, scenario_id: str):
        """生成指定场景的建议记录。"""
        serializer = ScenarioSuggestionRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            suggestions = SCENARIO_SERVICE.create_suggestions(
                scenario_id=scenario_id,
                requester=serializer.validated_data["requester"],
                suggestion_type=serializer.validated_data["suggestion_type"],
            )
        except ScenarioServiceError as error:
            return build_error_response(error)
        return Response({"success": True, "data": suggestions}, status=status.HTTP_201_CREATED)


class ScenarioSuggestionApplyView(APIView):
    """处理场景建议采纳请求。"""

    def post(self, request, scenario_id: str, suggestion_id: str):
        """采纳建议并生成标准修订记录。"""
        serializer = ScenarioSuggestionApplyRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            result = SCENARIO_SERVICE.apply_suggestion(
                scenario_id=scenario_id,
                suggestion_id=suggestion_id,
                reviser=serializer.validated_data["reviser"],
                revision_comment=serializer.validated_data.get("revision_comment", ""),
            )
        except ScenarioServiceError as error:
            return build_error_response(error)
        return Response({"success": True, "data": result})


class ScenarioWorkbenchView(TemplateView):
    """返回 V3 正式入口工作台页面。"""

    template_name = "scenario_service/workbench.html"
