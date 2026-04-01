"""旧 PublicAPI 的最小标准化目录。"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Literal


PayloadMode = Literal["none", "json", "data"]


@dataclass(frozen=True, slots=True)
class LegacyApiOperation:
    """为旧 PublicAPI 提供统一操作目录，便于后续向平台模型收口。"""

    operation_name: str
    operation_code: str
    module_code: str
    path_template: str
    http_method: Literal["GET", "POST", "PUT", "PATCH", "DELETE"]
    payload_mode: PayloadMode = "none"
    requires_private_env: bool = True
    response_mode: Literal["json", "raw"] = "json"
    description: str | None = None
    metadata: dict[str, Any] | None = None

    def render_path(self, **path_params: Any) -> str:
        """使用路径参数渲染旧接口路径模板。"""
        return self.path_template.format(**path_params)


PUBLIC_API_OPERATION_CATALOG: dict[str, LegacyApiOperation] = {
    "invite_user": LegacyApiOperation(
        operation_name="邀请用户",
        operation_code="invite_user",
        module_code="user_management",
        path_template="/api/basicserver/saves",
        http_method="POST",
        payload_mode="json",
        description="邀请成员进入团队。",
    ),
    "change_password": LegacyApiOperation(
        operation_name="修改密码",
        operation_code="change_password",
        module_code="user_management",
        path_template="/api/basicserver/changePassword",
        http_method="POST",
        payload_mode="data",
        description="通过旧登录链路修改成员密码。",
    ),
    "get_team_info": LegacyApiOperation(
        operation_name="获取团队信息",
        operation_code="get_team_info",
        module_code="team_management",
        path_template="/api/basicserver/info",
        http_method="GET",
        description="获取当前租户团队信息。",
    ),
    "create_comment": LegacyApiOperation(
        operation_name="创建评论",
        operation_code="create_comment",
        module_code="comment",
        path_template="/api/{module_name}/common/comment/createComment",
        http_method="POST",
        payload_mode="json",
        description="创建业务评论。",
    ),
    "add_watch": LegacyApiOperation(
        operation_name="添加关注",
        operation_code="add_watch",
        module_code="watch",
        path_template="/api/my/watch/batchAdd",
        http_method="POST",
        payload_mode="json",
        description="添加关注关系。",
    ),
    "remove_watch": LegacyApiOperation(
        operation_name="取消关注",
        operation_code="remove_watch",
        module_code="watch",
        path_template="/api/my/watch/batchDelete",
        http_method="POST",
        payload_mode="json",
        description="删除关注关系。",
    ),
    "send_remind": LegacyApiOperation(
        operation_name="发送提醒",
        operation_code="send_remind",
        module_code="remind",
        path_template="/api/bcw/remind/send",
        http_method="POST",
        payload_mode="json",
        response_mode="raw",
        description="发送提醒或催办。",
    ),
    "save_normal_config": LegacyApiOperation(
        operation_name="保存普通配置",
        operation_code="save_normal_config",
        module_code="configuration",
        path_template="/api/bcw/base/configuration/saveNormalConfig",
        http_method="POST",
        payload_mode="json",
        description="保存普通配置项。",
    ),
}
