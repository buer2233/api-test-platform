"""
接口自动化测试框架配置文件
"""
import os


class RunConfig:
    """测试运行配置"""

    # 项目基础路径
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))

    # ==================== 环境配置 ====================
    # 当前公开基线默认站点，私有环境用例需要通过环境变量覆盖
    DEFAULT_PUBLIC_BASE_URL = "jsonplaceholder.typicode.com"

    # 测试环境地址 (可根据需要修改)
    BASE_URL = os.getenv("API_TEST_BASE_URL", DEFAULT_PUBLIC_BASE_URL)

    # HTTPS开关
    IS_HTTPS = os.getenv("API_TEST_IS_HTTPS", "1") == "1"

    # 超时时间 (秒)
    TIMEOUT = int(os.getenv("API_TEST_TIMEOUT", "30"))

    # 私有环境登录使用的 RSA 公钥
    RSA_PUBLIC_KEY = os.getenv("API_TEST_RSA_PUBLIC_KEY", "")

    # ==================== 测试账号配置 ====================
    # 测试账号文件名
    ACCOUNT_FILE = "account.txt"

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


