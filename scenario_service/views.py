"""V2 场景服务接口视图。"""

from __future__ import annotations

from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from scenario_service.serializers import (
    FunctionalCaseImportRequestSerializer,
    ScenarioReviewRequestSerializer,
)
from scenario_service.services import FunctionalCaseScenarioService, ScenarioServiceError


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
        scenario = SCENARIO_SERVICE.import_functional_case(serializer.validated_data)
        return Response(
            {"success": True, "data": SCENARIO_SERVICE.build_scenario_summary(scenario)},
            status=status.HTTP_201_CREATED,
        )


class ScenarioDetailView(APIView):
    """返回场景详情。"""

    def get(self, request, scenario_id: str):
        """处理详情查询请求。"""
        try:
            detail = SCENARIO_SERVICE.get_scenario_detail(scenario_id=scenario_id)
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


class ScenarioExecuteView(APIView):
    """处理场景执行触发请求。"""

    def post(self, request, scenario_id: str):
        """处理执行触发动作。"""
        try:
            workspace_root = None
            if isinstance(request.data, dict):
                workspace_root = request.data.get("workspace_root")
            execution = SCENARIO_SERVICE.request_execution(
                scenario_id=scenario_id,
                workspace_root=workspace_root,
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


class ScenarioResultView(APIView):
    """返回统一结果摘要。"""

    def get(self, request, scenario_id: str):
        """处理结果查询请求。"""
        try:
            result = SCENARIO_SERVICE.get_scenario_result(scenario_id=scenario_id)
        except ScenarioServiceError as error:
            return build_error_response(error)
        return Response({"success": True, "data": result})
