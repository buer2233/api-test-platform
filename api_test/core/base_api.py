"""
基础API类 - 所有API类的父类
提供HTTP请求、登录认证、加密解密等基础功能
"""
import base64
import hashlib
import os
import random
import string
import time
from collections.abc import Iterable
from datetime import date, datetime, timedelta
from typing import Optional, Tuple, Dict, Any, List

import requests
from Crypto.Cipher import AES
from Crypto.Util.Padding import pad, unpad

from config import RunConfig
from core.private_env import encrypt_password
from core.session import build_retry_session


class BaseAPI:
    """基础API类 - 提供通用功能"""

    def __init__(self):
        """初始化基础API类"""
        self.base_url = self._get_base_url()
        self.timeout = RunConfig.TIMEOUT
        self.is_https = RunConfig.IS_HTTPS

        # 初始化Session
        self.session = self._init_session()

        # 测试账号信息 (从conftest获取)
        self._init_account_info()

    @staticmethod
    def _get_base_url() -> str:
        """获取基础URL"""
        return RunConfig.BASE_URL

    def _init_session(self) -> requests.Session:
        """初始化Session并设置超时"""
        return build_retry_session()

    def _init_account_info(self):
        """初始化账号信息 (由conftest填充)"""
        # 管理员账号
        self.admin_name = None
        self.admin_username = None
        self.admin_password = None
        self.admin_eteamsid = None
        self.admin_userid = None

        # 普通成员账号
        self.employee_name = None
        self.employee_username = None
        self.employee_password = None
        self.employee_eteamsid = None
        self.employee_userid = None

    # ==================== HTTP请求方法 ====================

    def request(
        self,
        method: str,
        url: str,
        eteamsid: Optional[str] = None,
        expected_status: int | Iterable[int] = 200,
        **kwargs
    ) -> Any:
        """
        发送HTTP请求的通用方法

        Args:
            method: 请求方法 (GET, POST, DELETE, PUT等)
            url: 请求路径 (相对路径或完整URL)
            eteamsid: ETEAMSID会话令牌
            **kwargs: 其他requests参数

        Returns:
            响应JSON数据或原始响应对象
        """
        not_json = bool(kwargs.pop("NOTJSON", False))
        allowed_statuses = self._normalize_expected_status(expected_status)

        # 构建完整URL
        if not url.startswith(('http://', 'https://')):
            protocol = 'https://' if self.is_https else 'http://'
            url = f"{protocol}{self.base_url}{url}"

        # 设置请求头
        headers = kwargs.pop('headers', {})
        headers.setdefault('Content-Type', 'application/json')

        # 设置Cookie
        if eteamsid:
            headers.setdefault('Cookie', f'ETEAMSID={eteamsid}')

        # 发送请求
        response = self.session.request(
            method=method.upper(),
            url=url,
            headers=headers,
            timeout=self.timeout,
            **kwargs
        )

        # 检查响应状态
        assert response.status_code in allowed_statuses, (
            f"请求失败: {method} {url}\n"
            f"状态码: {response.status_code}, 期望: {allowed_statuses}\n"
            f"响应: {response.text}"
        )

        if not_json:
            return response
        return response.json()

    @staticmethod
    def _normalize_expected_status(expected_status: int | Iterable[int]) -> tuple[int, ...]:
        if isinstance(expected_status, int):
            return (expected_status,)
        normalized = tuple(expected_status)
        assert normalized, "expected_status 不能为空"
        return normalized

    def get(self, url: str, eteamsid: Optional[str] = None, **kwargs) -> Any:
        """发送GET请求"""
        return self.request('GET', url, eteamsid=eteamsid, **kwargs)

    def post(self, url: str, eteamsid: Optional[str] = None, **kwargs) -> Any:
        """发送POST请求"""
        return self.request('POST', url, eteamsid=eteamsid, **kwargs)

    def put(self, url: str, eteamsid: Optional[str] = None, **kwargs) -> Any:
        """发送PUT请求"""
        return self.request('PUT', url, eteamsid=eteamsid, **kwargs)

    def patch(self, url: str, eteamsid: Optional[str] = None, **kwargs) -> Any:
        """发送PATCH请求"""
        return self.request('PATCH', url, eteamsid=eteamsid, **kwargs)

    def delete(self, url: str, eteamsid: Optional[str] = None, **kwargs) -> Any:
        """发送DELETE请求"""
        return self.request('DELETE', url, eteamsid=eteamsid, **kwargs)

    # ==================== 认证相关 ====================

    @staticmethod
    def password_rsa(password: str) -> str:
        """
        RSA加密密码
        1. 从显式配置中获取公钥
        2. 使用公钥加密密码
        """
        return encrypt_password(password)

    def login(
        self,
        username: str,
        password: str,
        login_type: str = 'app_account'
    ) -> Tuple[str, str]:
        """
        用户登录

        Args:
            username: 用户名/邮箱/手机号
            password: 密码
            login_type: 登录类型

        Returns:
            (ETEAMSID, employeeid)
        """
        # 构建登录URL
        base_url = self.base_url
        if 'weapp' in base_url:
            passport_url = base_url.replace('weapp', 'passport')
        else:
            passport_url = base_url

        protocol = 'https://' if self.is_https else 'http://'
        url = f"{protocol}{passport_url}/papi/passport/appnew/login/appLogin"

        # RSA加密密码
        encrypted_password = self.password_rsa(password)

        # 请求参数
        payload = {
            "username": username,
            "password": encrypted_password,
            "loginType": login_type,
            "checkCodeKey": "code_auto_test",
            "checkCode": "code_auto_test",
            "customPageConfigId": "10000000000000000"
        }

        headers = {'Content-Type': 'application/json;charset=UTF-8'}

        # 发送登录请求
        response = self.session.post(
            url,
            json=payload,
            headers=headers,
            timeout=self.timeout
        )

        assert response.status_code == 200, f"登录接口异常: {response.text}"

        result = response.json()
        assert result.get('status'), f"登录失败: {result}"

        data = result.get('data', {})
        eteamsid = data.get('ETEAMSID')
        employeeid = data.get('employeeid')

        assert eteamsid, "登录响应中缺少ETEAMSID"
        assert employeeid, "登录响应中缺少employeeid"

        return eteamsid, employeeid

    def get_admin_session(self) -> Tuple[str, str]:
        """获取管理员会话"""
        if not self.admin_eteamsid:
            self.admin_eteamsid, self.admin_userid = self.login(
                self.admin_username,
                self.admin_password
            )
        return self.admin_eteamsid, self.admin_userid

    # ==================== 文件操作 ====================

    def upload_file(
        self,
        eteamsid: str,
        file_path: str,
        module: str = 'document',
        ref_id: str = ''
    ) -> dict:
        """
        上传文件

        Args:
            eteamsid: 会话令牌
            file_path: 文件路径
            module: 模块名称
            ref_id: 关联ID

        Returns:
            上传结果
        """
        protocol = 'https://' if self.is_https else 'http://'
        url = f"{protocol}{self.base_url}/api/file/module/upload"

        file_name = os.path.basename(file_path)
        file_size = os.path.getsize(file_path)
        file_time = int(time.time() * 1000)

        # 构建请求数据
        data = {
            'module': module,
            'name': file_name,
            'size': str(file_size),
            'lastModified': str(file_time),
            'lastModifiedDate': str(file_time)
        }

        if ref_id:
            data['refId'] = ref_id

        # 读取文件
        with open(file_path, 'rb') as f:
            files = {'file': (file_name, f, 'application/octet-stream')}
            headers = {'Cookie': f'ETEAMSID={eteamsid}'}

            response = self.session.post(
                url,
                headers=headers,
                data=data,
                files=files,
                timeout=self.timeout
            )

        assert response.status_code == 200, f"文件上传失败: {response.text}"

        result = response.json()
        assert result.get('code') == 200, f"文件上传失败: {result}"

        return result.get('data')

    # ==================== 数据处理工具 ====================

    @staticmethod
    def get_value(data: Any, keys: List[str], msg: str = '') -> Any:
        """
        从嵌套字典/列表中获取值

        Args:
            data: 数据源 (字典或列表)
            keys: 键路径列表
            msg: 错误提示前缀

        Returns:
            获取的值

        Raises:
            AssertionError: 当键不存在时
        """
        if not isinstance(keys, list):
            keys = [keys]

        try:
            for key in keys:
                data = data[key]
            return data
        except (KeyError, IndexError, TypeError):
            error_msg = f"数据中不存在路径 '{keys}'"
            if msg:
                error_msg = f"{msg}: {error_msg}"
            assert False, error_msg

    @staticmethod
    def time_to_stamp(date_str: str, is_all_day: bool = False) -> str:
        """
        日期字符串转时间戳

        Args:
            date_str: 日期字符串 (格式: %Y-%m-%d 或 %Y-%m-%d %H:%M:%S)
            is_all_day: 是否全天

        Returns:
            毫秒时间戳字符串
        """
        fmt = "%Y-%m-%d" if is_all_day else "%Y-%m-%d %H:%M:%S"
        time_array = time.strptime(date_str, fmt)
        timestamp = int(time.mktime(time_array) * 1000)
        return str(timestamp)

    @staticmethod
    def stamp_to_time(timestamp: int) -> str:
        """
        时间戳转日期字符串

        Args:
            timestamp: 时间戳 (秒或毫秒)

        Returns:
            日期字符串 (格式: %Y-%m-%d %H:%M:%S)
        """
        if len(str(timestamp)) == 13:
            timestamp = timestamp / 1000
        time_array = time.localtime(timestamp)
        return time.strftime("%Y-%m-%d %H:%M:%S", time_array)

    @staticmethod
    def get_week_info(day: Optional[date] = None) -> Tuple[str, str]:
        """
        获取指定日期所在周的周一和周日

        Args:
            day: 日期，默认为今天

        Returns:
            (周一日期, 周日日期)
        """
        if not day:
            day = date.today()
        elif isinstance(day, str):
            day = datetime.strptime(day, '%Y-%m-%d').date()

        monday = day - timedelta(days=day.weekday())
        sunday = monday + timedelta(days=6)

        return monday.strftime('%Y-%m-%d'), sunday.strftime('%Y-%m-%d')

    @staticmethod
    def get_month_info(day: Optional[date] = None) -> Tuple[str, str, int]:
        """
        获取指定日期所在月的第一天、最后一天和总天数

        Args:
            day: 日期，默认为今天

        Returns:
            (第一天, 最后一天, 总天数)
        """
        if not day:
            day = date.today()
        elif isinstance(day, str):
            day = datetime.strptime(day, '%Y-%m-%d').date()

        first_day = date(day.year, day.month, 1)
        # 获取下个月第一天，再减一天得到本月最后一天
        if day.month == 12:
            next_month = date(day.year + 1, 1, 1)
        else:
            next_month = date(day.year, day.month + 1, 1)
        last_day = next_month - timedelta(days=1)

        month_days = (last_day - first_day).days + 1

        return (
            first_day.strftime('%Y-%m-%d'),
            last_day.strftime('%Y-%m-%d'),
            month_days
        )

    # ==================== 加密解密工具 ====================

    @staticmethod
    def md5_encrypt(text: str) -> str:
        """MD5加密"""
        md5 = hashlib.md5()
        md5.update(text.encode('utf-8'))
        return md5.hexdigest().lower()

    @staticmethod
    def sha1_encrypt(text: str) -> str:
        """SHA1加密"""
        sha1 = hashlib.sha1()
        sha1.update(text.encode('utf-8'))
        return sha1.hexdigest()

    @staticmethod
    def aes_ecb_encrypt(plain_text: str, key: str) -> str:
        """AES-ECB加密"""
        cipher = AES.new(key.encode('utf-8'), AES.MODE_ECB)
        padded = pad(plain_text.encode('utf-8'), AES.block_size)
        encrypted = cipher.encrypt(padded)
        return base64.b64encode(encrypted).decode('utf-8')

    @staticmethod
    def aes_ecb_decrypt(cipher_text: str, key: str) -> str:
        """AES-ECB解密"""
        cipher = AES.new(key.encode('utf-8'), AES.MODE_ECB)
        encrypted = base64.b64decode(cipher_text)
        decrypted = cipher.decrypt(encrypted)
        unpadded = unpad(decrypted, AES.block_size)
        return unpadded.decode('utf-8')

    @staticmethod
    def aes_cbc_encrypt(plain_text: str, key: str, iv: str) -> str:
        """AES-CBC加密"""
        cipher = AES.new(key.encode('utf-8'), AES.MODE_CBC, iv.encode('utf-8'))
        padded = pad(plain_text.encode('utf-8'), AES.block_size)
        encrypted = cipher.encrypt(padded)
        return base64.b64encode(encrypted).decode('utf-8')

    @staticmethod
    def aes_cbc_decrypt(cipher_text: str, key: str, iv: str) -> str:
        """AES-CBC解密"""
        cipher = AES.new(key.encode('utf-8'), AES.MODE_CBC, iv.encode('utf-8'))
        encrypted = base64.b64decode(cipher_text)
        decrypted = cipher.decrypt(encrypted)
        unpadded = unpad(decrypted, AES.block_size)
        return unpadded.decode('utf-8')

    # ==================== 测试数据生成工具 ====================

    @staticmethod
    def generate_random_string(length: int = 10) -> str:
        """生成随机字符串 (小写字母+数字)"""
        return ''.join(random.sample(string.ascii_lowercase + string.digits, length))

    @staticmethod
    def generate_phone_number() -> str:
        """生成随机手机号"""
        second = random.choice([3, 4, 5, 7, 8])
        third = random.choice([0, 1, 2, 3, 4, 5, 6, 7, 8, 9])
        suffix = random.randint(10000000, 99999999)
        return f"1{second}{third}{suffix}"

    @staticmethod
    def generate_email(prefix: Optional[str] = None) -> str:
        """生成随机邮箱"""
        if not prefix:
            prefix = BaseAPI.generate_random_string(8)
        timestamp = int(time.time() * 1000)
        return f"{prefix}{timestamp}@etest.com"
