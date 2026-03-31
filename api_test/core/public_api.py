"""
公共API类 - 封装常用的API操作
继承自BaseAPI，提供业务相关的通用方法
"""
from typing import Optional, Dict, Any, List

from core.base_api import BaseAPI
from legacy_api_catalog import LegacyApiOperation, PUBLIC_API_OPERATION_CATALOG


class PublicAPI(BaseAPI):
    """公共API类 - 提供业务相关的通用方法"""

    OPERATION_CATALOG = PUBLIC_API_OPERATION_CATALOG

    def __init__(self):
        """初始化公共API类"""
        super().__init__()

    @classmethod
    def describe_operations(cls) -> dict[str, LegacyApiOperation]:
        """返回旧接口目录，供测试治理和后续平台接入复用。"""
        return dict(cls.OPERATION_CATALOG)

    @classmethod
    def get_operation(cls, operation_code: str) -> LegacyApiOperation:
        return cls.OPERATION_CATALOG[operation_code]

    def _call_operation(
        self,
        operation_code: str,
        eteamsid: str,
        payload: Optional[Dict[str, Any]] = None,
        *,
        path_params: Optional[Dict[str, Any]] = None,
        path_override: Optional[str] = None,
    ) -> Any:
        operation = self.get_operation(operation_code)
        url = path_override or operation.render_path(**(path_params or {}))
        kwargs: Dict[str, Any] = {}
        if payload and operation.payload_mode != "none":
            kwargs[operation.payload_mode] = payload
        if operation.response_mode == "raw":
            kwargs["NOTJSON"] = True
        return self.request(operation.http_method, url, eteamsid=eteamsid, **kwargs)

    # ==================== 用户管理 ====================

    def invite_user(
        self,
        eteamsid: str,
        name: str,
        account: str
    ) -> Dict[str, Any]:
        """
        邀请用户

        Args:
            eteamsid: 会话令牌
            name: 用户姓名
            account: 用户账号(邮箱/手机号)

        Returns:
            邀请结果
        """
        payload = {
            "inviteInfos": [{
                "invitee": name,
                "contact": account,
                "inviteNo": 1,
                "accountType": "3",
                "personalStatus": "3"
            }]
        }

        response = self._call_operation("invite_user", eteamsid=eteamsid, payload=payload)

        # 检查响应
        invite_info = response.get('inviteInfos', [{}])[0]

        if 'initPassword' in invite_info:
            return {
                'success': True,
                'password': invite_info['initPassword'],
                'data': invite_info
            }

        return {
            'success': False,
            'data': invite_info
        }

    def change_password(
        self,
        eteamsid: str,
        employee_id: str,
        old_password: str,
        new_password: str
    ) -> Dict[str, Any]:
        """
        修改密码

        Args:
            eteamsid: 会话令牌
            employee_id: 员工ID
            old_password: 旧密码
            new_password: 新密码

        Returns:
            修改结果
        """
        payload = {
            'oldPassword': old_password,
            'newPassword': new_password,
            'employee.id': employee_id
        }

        return self._call_operation("change_password", eteamsid=eteamsid, payload=payload)

    # ==================== 团队管理 ====================

    def get_team_info(self, eteamsid: str) -> Dict[str, Any]:
        """
        获取团队信息

        Args:
            eteamsid: 会话令牌

        Returns:
            团队信息
        """
        response = self._call_operation("get_team_info", eteamsid=eteamsid)

        return self.get_value(response, ['data', 'tenant'], msg='获取团队信息失败')

    # ==================== 评论相关 ====================

    def create_comment(
        self,
        eteamsid: str,
        module: str,
        target_id: str,
        content: str,
        attachments: Optional[List[Dict]] = None,
        client: str = 'pc',
        module_name: str = ''
    ) -> Dict[str, Any]:
        """
        创建评论

        Args:
            eteamsid: 会话令牌
            module: 模块名称
            target_id: 目标ID
            content: 评论内容
            attachments: 附件列表
            client: 客户端类型 (pc/h5/app)
            module_name: 模块路径名称

        Returns:
            评论结果
        """
        payload = {
            "attachments": attachments or [],
            "comment": {
                "targetId": target_id,
                "module": module,
                "disableMessage": False,
                "address": "",
                "longitude": "",
                "latitude": "",
                "imAtContent": content,
                "atLinkList": [],
                "content": content,
                "relevanceList": []
            },
            "client": client
        }

        response = self._call_operation(
            "create_comment",
            eteamsid=eteamsid,
            payload=payload,
            path_params={"module_name": module_name},
        )

        return self.get_value(response, ['data'], msg='创建评论失败')

    # ==================== 关注/提醒 ====================

    def add_watch(
        self,
        eteamsid: str,
        module: str,
        entity_id: str,
        is_h5: bool = False
    ) -> Dict[str, Any]:
        """
        添加关注

        Args:
            eteamsid: 会话令牌
            module: 模块名称
            entity_id: 实体ID
            is_h5: 是否H5端

        Returns:
            关注结果
        """
        payload = {
            "module": module,
            "entityIds": [entity_id]
        }

        path_override = "/api/app/my/watch/batchAdd" if is_h5 else None
        return self._call_operation("add_watch", eteamsid=eteamsid, payload=payload, path_override=path_override)

    def remove_watch(
        self,
        eteamsid: str,
        module: str,
        entity_id: str,
        is_h5: bool = False
    ) -> Dict[str, Any]:
        """
        取消关注

        Args:
            eteamsid: 会话令牌
            module: 模块名称
            entity_id: 实体ID
            is_h5: 是否H5端

        Returns:
            取消关注结果
        """
        payload = {
            "module": module,
            "entityId": entity_id
        }

        path_override = "/api/app/my/watch/batchDelete" if is_h5 else None
        return self._call_operation(
            "remove_watch",
            eteamsid=eteamsid,
            payload=payload,
            path_override=path_override,
        )

    def send_remind(
        self,
        eteamsid: str,
        target_id: str,
        type_: str = "mainline",
        content: str = "",
        check_str: str = "",
        ids: str = "",
        is_h5: bool = False
    ) -> int:
        """
        发送提醒/催办

        Args:
            eteamsid: 会话令牌
            target_id: 目标ID
            type_: 类型
            content: 提醒内容
            check_str: 提醒人类型
            ids: 指定人员ID
            is_h5: 是否H5端

        Returns:
            状态码
        """
        payload = {
            "targetId": target_id,
            "type": type_,
            "content": content,
            "checkStr": check_str,
            "ids": ids
        }

        path_override = "/api/app/bcw/remind/send" if is_h5 else None
        response = self._call_operation(
            "send_remind",
            eteamsid=eteamsid,
            payload=payload,
            path_override=path_override,
        )

        return response.status_code

    # ==================== 配置管理 ====================

    def save_normal_config(
        self,
        eteamsid: str,
        config_key: str,
        config_value: str = "1"
    ) -> Dict[str, Any]:
        """
        保存普通配置

        Args:
            eteamsid: 会话令牌
            config_key: 配置键
            config_value: 配置值

        Returns:
            保存结果
        """
        payload = {
            "config": {
                "configKey": config_key,
                "configValue": config_value
            }
        }

        return self._call_operation("save_normal_config", eteamsid=eteamsid, payload=payload)

    # ==================== 数据工具 ====================

    def find_dict_in_list(
        self,
        data_list: List[Dict],
        key: str,
        value: Any
    ) -> Optional[Dict]:
        """
        在字典列表中查找指定条件的字典

        Args:
            data_list: 字典列表
            key: 查找的键
            value: 查找的值

        Returns:
            找到的字典，未找到返回None
        """
        for item in data_list:
            if item.get(key) == value:
                return item
        return None

    def search_dict_recursive(
        self,
        data: Any,
        key: str,
        value: Any
    ) -> List[Dict]:
        """
        递归搜索嵌套字典/列表中符合条件的数据

        Args:
            data: 数据源 (字典或列表)
            key: 查找的键
            value: 查找的值

        Returns:
            匹配的字典列表
        """
        matches = []

        if isinstance(data, dict):
            for k, v in data.items():
                if k == key and v == value:
                    matches.append(data)
                else:
                    matches.extend(self.search_dict_recursive(v, key, value))

        elif isinstance(data, list):
            for item in data:
                matches.extend(self.search_dict_recursive(item, key, value))

        return matches

    def get_dataframe_column(
        self,
        dataframe,
        column: str,
        value: Any = None,
        field: str = None
    ) -> Any:
        """
        获取DataFrame中某列的值或某列某行的字段值

        Args:
            dataframe: DataFrame数据
            column: 列名
            value: 列的值 (与field一起使用)
            field: 字段名 (与value一起使用)

        Returns:
            列数据或字段值

        Note:
            此方法需要pandas库支持
        """
        try:
            import pandas as pd
        except ImportError:
            raise ImportError("使用此方法需要安装pandas库: pip install pandas")

        if not isinstance(dataframe, pd.DataFrame):
            dataframe = pd.DataFrame(dataframe)

        if value is None:
            # 获取整列数据
            try:
                return dataframe.loc[:, column].tolist()
            except KeyError:
                assert False, f"DataFrame中没有列名为'{column}'的列"

        elif value and field:
            # 获取某列某行的字段值
            try:
                return dataframe.loc[dataframe[column] == value, [field]].values[0][0]
            except (KeyError, IndexError):
                assert False, f"无法从列'{column}'中值'{value}'获取字段'{field}'"
