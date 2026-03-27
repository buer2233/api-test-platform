"""
演示测试用例 - 展示如何使用接口自动化测试框架
"""
import pytest
from core.base_api import BaseAPI
from core.public_api import PublicAPI


class TestDemoAPI:
    """演示测试类 - API测试基础用法"""

    @pytest.fixture(scope="class")
    def api(self, admin_account):
        """初始化API实例"""
        api = PublicAPI()

        # 设置管理员账号信息
        api.admin_name = admin_account['name']
        api.admin_username = admin_account['username']
        api.admin_password = admin_account['password']

        yield api

        # 测试结束后的清理工作
        api.session.close()

    @pytest.fixture(scope="function")
    def login_session(self, api):
        """获取登录会话"""
        eteamsid, userid = api.get_admin_session()
        return eteamsid, userid

    @pytest.mark.basic
    @pytest.mark.smoke
    @pytest.mark.auth
    def test_user_login(self, api):
        """
        测试用户登录功能
        验证:
            1. 登录接口返回成功
            2. 返回ETEAMSID和employeeid
        """
        # 执行登录
        eteamsid, userid = api.login(
            username=api.admin_username,
            password=api.admin_password
        )

        # 验证返回结果
        assert eteamsid, "登录失败: 未返回ETEAMSID"
        assert userid, "登录失败: 未返回employeeid"
        assert len(eteamsid) > 10, "ETEAMSID格式异常"

    @pytest.mark.basic
    def test_get_team_info(self, api, login_session):
        """
        测试获取团队信息
        验证:
            1. 接口返回成功
            2. 返回团队基本信息
        """
        eteamsid, _ = login_session

        # 获取团队信息
        team_info = api.get_team_info(eteamsid)

        # 验证返回结果
        assert 'tenantKey' in team_info, "团队信息缺少tenantKey"
        assert 'tenantName' in team_info, "团队信息缺少tenantName"
        assert team_info['tenantKey'], "tenantKey不能为空"

    @pytest.mark.basic
    def test_invite_user(self, api, login_session):
        """
        测试邀请用户功能
        验证:
            1. 邀请接口调用成功
            2. 返回初始密码
        """
        eteamsid, _ = login_session

        # 生成测试数据
        invite_name = api.generate_random_string(6)
        invite_account = api.generate_email(invite_name)

        # 邀请用户
        result = api.invite_user(
            eteamsid=eteamsid,
            name=invite_name,
            account=invite_account
        )

        # 验证邀请结果
        assert result['success'], f"邀请用户失败: {result}"
        assert 'password' in result, "邀请结果中缺少初始密码"
        assert result['password'], "初始密码不能为空"

    @pytest.mark.basic
    def test_create_comment(self, api, login_session):
        """
        测试创建评论功能
        验证:
            1. 评论创建成功
            2. 返回评论ID
        """
        eteamsid, _ = login_session

        # 创建评论
        comment_content = f"自动化测试评论 - {api.generate_random_string(8)}"
        comment = api.create_comment(
            eteamsid=eteamsid,
            module='mainline',
            target_id='test_target_id',
            content=comment_content
        )

        # 验证评论结果
        assert 'id' in comment, "评论结果缺少id字段"
        assert comment['content'] == comment_content, "评论内容不匹配"

    @pytest.mark.basic
    def test_time_conversion(self, api):
        """
        测试时间转换工具方法
        验证:
            1. 日期转时间戳正确
            2. 时间戳转日期正确
            3. 获取周信息正确
            4. 获取月信息正确
        """
        # 测试日期转时间戳
        date_str = "2024-01-01 12:00:00"
        timestamp = api.time_to_stamp(date_str)
        assert timestamp, "日期转时间戳失败"

        # 测试时间戳转日期
        converted_date = api.stamp_to_time(int(timestamp))
        assert converted_date[:10] == "2024-01-01", "时间戳转日期失败"

        # 测试获取周信息
        monday, sunday = api.get_week_info("2024-01-03")
        assert monday == "2024-01-01", f"周一计算错误: {monday}"
        assert sunday == "2024-01-07", f"周日计算错误: {sunday}"

        # 测试获取月信息
        first_day, last_day, days = api.get_month_info("2024-01-15")
        assert first_day == "2024-01-01", f"月初计算错误: {first_day}"
        assert last_day == "2024-01-31", f"月末计算错误: {last_day}"
        assert days == 31, f"月天数计算错误: {days}"

    @pytest.mark.basic
    def test_encryption_methods(self, api):
        """
        测试加密解密工具方法
        验证:
            1. MD5加密正确
            2. SHA1加密正确
            3. AES-ECB加密解密正确
            4. AES-CBC加密解密正确
        """
        test_text = "test_password_123"

        # 测试MD5
        md5_result = api.md5_encrypt(test_text)
        assert md5_result, "MD5加密失败"
        assert len(md5_result) == 32, "MD5结果长度异常"

        # 测试SHA1
        sha1_result = api.sha1_encrypt(test_text)
        assert sha1_result, "SHA1加密失败"
        assert len(sha1_result) == 40, "SHA1结果长度异常"

        # 测试AES-ECB
        key = "1234567890123456"  # 16位密钥
        aes_ecb_encrypted = api.aes_ecb_encrypt(test_text, key)
        aes_ecb_decrypted = api.aes_ecb_decrypt(aes_ecb_encrypted, key)
        assert aes_ecb_decrypted == test_text, "AES-ECB解密结果不匹配"

        # 测试AES-CBC
        iv = "1234567890123456"  # 16位IV
        aes_cbc_encrypted = api.aes_cbc_encrypt(test_text, key, iv)
        aes_cbc_decrypted = api.aes_cbc_decrypt(aes_cbc_encrypted, key, iv)
        assert aes_cbc_decrypted == test_text, "AES-CBC解密结果不匹配"

    @pytest.mark.basic
    def test_data_generation(self, api):
        """
        测试数据生成工具方法
        验证:
            1. 随机字符串生成正确
            2. 手机号生成符合规则
            3. 邮箱生成符合规则
        """
        # 测试随机字符串
        random_str = api.generate_random_string(10)
        assert len(random_str) == 10, "随机字符串长度不正确"
        assert random_str.isalnum(), "随机字符串格式异常"

        # 测试手机号生成
        phone = api.generate_phone_number()
        assert phone.startswith('1'), "手机号应以1开头"
        assert len(phone) == 11, "手机号长度应为11位"
        assert phone.isdigit(), "手机号应全为数字"

        # 测试邮箱生成
        email = api.generate_email()
        assert '@' in email, "邮箱应包含@符号"
        assert email.endswith('.com'), "邮箱应以.com结尾"


class TestDemoAdvanced:
    """演示测试类 - 高级用法"""

    @pytest.fixture(scope="class")
    def api(self, admin_account):
        """初始化API实例"""
        api = PublicAPI()
        api.admin_username = admin_account['username']
        api.admin_password = admin_account['password']
        yield api
        api.session.close()

    @pytest.mark.P0
    @pytest.mark.regression
    def test_data_extraction(self, api):
        """
        测试数据提取功能
        演示如何从复杂的响应中提取数据
        """
        # 模拟复杂响应数据
        mock_response = {
            "code": 200,
            "data": {
                "data": {
                    "id": "12345",
                    "name": "测试项目"
                }
            }
        }

        # 使用get_value方法提取嵌套数据
        project_id = api.get_value(mock_response, ['data', 'data', 'id'])
        assert project_id == "12345", "数据提取失败"

        # 测试错误情况
        with pytest.raises(AssertionError):
            api.get_value(mock_response, ['data', 'nonexistent'])

    @pytest.mark.P0
    def test_list_search(self, api):
        """
        测试列表搜索功能
        演示如何在列表中查找特定数据
        """
        # 模拟列表数据
        mock_list = [
            {"id": "1", "name": "项目A", "status": "active"},
            {"id": "2", "name": "项目B", "status": "inactive"},
            {"id": "3", "name": "项目C", "status": "active"}
        ]

        # 查找特定项目
        result = api.find_dict_in_list(mock_list, 'id', '2')
        assert result is not None, "未找到目标数据"
        assert result['name'] == "项目B", "查找结果不正确"

        # 测试递归搜索
        results = api.search_dict_recursive(mock_list, 'status', 'active')
        assert len(results) == 2, "递归搜索结果数量不正确"
