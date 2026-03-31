"""
接口自动化测试框架配置文件
"""
import os


class RunConfig:
    """测试运行配置"""

    # 项目基础路径
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

    # ==================== 环境配置 ====================
    # 测试环境地址 (可根据需要修改)
    BASE_URL = os.getenv("API_TEST_BASE_URL", "10.12.105.158:10600/oa/second")

    # HTTPS开关
    IS_HTTPS = os.getenv("API_TEST_IS_HTTPS", "0") == "1"

    # 超时时间 (秒)
    TIMEOUT = int(os.getenv("API_TEST_TIMEOUT", "30"))

    # 私有环境登录使用的 RSA 公钥
    RSA_PUBLIC_KEY = os.getenv("API_TEST_RSA_PUBLIC_KEY", "")

    # ==================== 测试账号配置 ====================
    # 测试账号文件名
    ACCOUNT_FILE = "account.txt"

    # ==================== Nacos配置 ====================
    # Nacos平台映射关系 (用于服务发现和配置管理)
    NACOS_MAP = {
        "weapp.devdm.cn": {
            "nacosUrl": "http://10.12.107.56",
            "nacosUser": "nacos",
            "nacosPasswd": "nacos"
        },
        "10.12.107.50": {
            "nacosUrl": "http://10.12.107.56",
            "nacosUser": "nacos",
            "nacosPasswd": "nacos"
        }
    }

    # ==================== Zookeeper配置 ====================
    # Zookeeper平台映射关系 (用于服务注册与发现)
    ZOOKEEPER_MAP = {
        "10.12.105.120": {
            "url": "http://10.12.105.50:9090",
            "user": "admin",
            "passwd": "manager"
        }
    }

    # ==================== 日志配置 ====================
    # 是否启用日志
    IS_LOG = False
    IS_STACK = False
    IS_HEADERS = False
    IS_BODY = False
    IS_RESPONSE = False

    # 日志文件路径
    HTTP_LOG_INFO = "logs/http_info.log"
    HTTP_LOG_CONN = "logs/http_conn.log"

    # ==================== 其他配置 ====================
    # 是否打印traceId
    IS_TRACE_ID = True

    # 构建状态
    IS_BUILD_STATUS = False


# 获取环境变量配置
def get_nacos_config(base_url: str) -> dict:
    """根据base_url获取Nacos配置"""
    return RunConfig.NACOS_MAP.get(base_url, {})


def get_zookeeper_config(base_url: str) -> dict:
    """根据base_url获取Zookeeper配置"""
    return RunConfig.ZOOKEEPER_MAP.get(base_url, {})
