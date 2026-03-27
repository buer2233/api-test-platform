# 接口自动化测试框架

基于 Python + pytest 的企业级接口自动化测试框架，提供完善的测试基础设施和丰富的工具方法。

## 框架特点

- **易于使用**: 简洁的API设计，快速上手
- **功能完善**: 涵盖认证、加密、数据处理等常用功能
- **可扩展性强**: 模块化设计，易于扩展和定制
- **pytest集成**: 充分利用pytest的fixture和标记功能
- **报告美观**: 支持HTML测试报告，包含详细的测试信息
- **开箱即用**: 包含百度公开接口测试示例，无需配置即可运行

## 目录

- [项目结构](#项目结构)
- [快速开始](#快速开始)
- [核心类说明](#核心类说明)
- [测试用例编写](#测试用例编写)
- [百度接口测试示例](#百度接口测试示例)
- [pytest标记说明](#pytest标记说明)
- [常用命令](#常用命令)
- [配置说明](#配置说明)
- [最佳实践](#最佳实践)
- [常见问题](#常见问题)

## 项目结构

```
api_test/
├── config.py              # 全局配置文件
├── conftest.py            # pytest配置和fixture
├── pytest.ini             # pytest配置文件
├── requirements.txt       # 依赖包列表
├── run_test.py            # 测试运行脚本
├── .gitignore             # Git忽略文件
├── README.md              # 项目文档
├── QUICKSTART.md          # 快速入门指南
├── core/                  # 核心类目录
│   ├── __init__.py
│   ├── base_api.py        # 基础API类
│   └── public_api.py      # 公共API类
├── tests/                 # 测试用例目录
│   ├── __init__.py
│   ├── test_demo.py       # 框架演示测试用例
│   └── test_baidu_sug.py  # 百度搜索建议接口测试
├── test_data/             # 测试数据目录
│   └── account.txt        # 测试账号文件
└── report/                # 测试报告目录 (自动创建)
```

## 快速开始

### 1. 安装依赖

```bash
# 进入项目目录
cd test_framework/api_test

# 安装依赖
pip install -r requirements.txt
```

### 2. 运行示例测试

框架已包含百度搜索建议接口的测试用例，无需配置即可运行：

```bash
# 运行百度接口测试
pytest tests/test_baidu_sug.py -v

# 生成HTML报告
pytest tests/test_baidu_sug.py --html=report/baidu_test.html --self-contained-html
```

### 3. 查看测试结果

测试运行后会显示详细结果：
```
tests/test_baidu_sug.py::TestBaiduSuggestionAPI::test_baidu_suggestion_basic PASSED
tests/test_baidu_sug.py::TestBaidu_sugAPI::test_baidu_suggestion_response_time PASSED
...
========================= 6 passed in 2.15s =========================
```

## 核心类说明

### BaseAPI 基础API类

所有API类的父类，提供HTTP请求、数据转换、加密解密等基础功能。

#### HTTP请求方法

```python
from core.base_api import BaseAPI

api = BaseAPI()

# GET请求
response = api.get("/api/user/info", eteamsid="xxx")

# POST请求 (JSON)
response = api.post("/api/user/create", eteamsid="xxx", json={"name": "张三"})

# POST请求 (表单)
response = api.post("/api/form/submit", eteamsid="xxx", data={"key": "value"})

# DELETE请求
response = api.delete("/api/user/1", eteamsid="xxx")
```

#### 用户认证

```python
# 用户登录
eteamsid, userid = api.login("username", "password")

# 获取管理员会话 (自动登录)
eteamsid, userid = api.get_admin_session()
```

#### 时间处理

```python
# 日期转时间戳 (毫秒)
timestamp = api.time_to_stamp("2024-01-01 12:00:00")
# 返回: "1704105600000"

# 时间戳转日期
date_str = api.stamp_to_time(1704105600000)
# 返回: "2024-01-01 12:00:00"

# 获取周信息 (周一、周日)
monday, sunday = api.get_week_info("2024-01-03")
# 返回: ("2024-01-01", "2024-01-07")

# 获取月信息 (月初、月末、天数)
first_day, last_day, days = api.get_month_info("2024-01-15")
# 返回: ("2024-01-01", "2024-01-31", 31)
```

#### 加密解密

```python
# MD5加密
md5_hash = api.md5_encrypt("password123")

# SHA1加密
sha1_hash = api.sha1_encrypt("password123")

# AES-ECB加密解密
key = "1234567890123456"  # 16位密钥
encrypted = api.aes_ecb_encrypt("plaintext", key)
decrypted = api.aes_ecb_decrypt(encrypted, key)

# AES-CBC加密解密
iv = "1234567890123456"  # 16位IV
encrypted = api.aes_cbc_encrypt("plaintext", key, iv)
decrypted = api.aes_cbc_decrypt(encrypted, key, iv)
```

#### 数据生成

```python
# 生成随机字符串 (小写字母+数字)
random_str = api.generate_random_string(10)
# 返回: "a3b7c9d2e1"

# 生成手机号
phone = api.generate_phone_number()
# 返回: "13812345678"

# 生成邮箱
email = api.generate_email()
# 返回: "x7k3m9q2170412345678@test.com"
```

#### 数据提取

```python
# 从嵌套字典中提取数据
response = {
    "code": 200,
    "data": {
        "user": {
            "id": "123",
            "name": "张三"
        }
    }
}

# 提取嵌套数据
user_name = api.get_value(response, ['data', 'user', 'name'])
# 返回: "张三"

# 如果路径不存在会抛出断言错误
```

### PublicAPI 公共API类

继承自BaseAPI，提供业务相关的通用方法。

```python
from core.public_api import PublicAPI

api = PublicAPI()

# 邀请用户
result = api.invite_user(eteamsid, "张三", "zhangsan@test.com")
# 返回: {'success': True, 'password': '初始密码', 'data': {...}}

# 创建评论
comment = api.create_comment(
    eteamsid,
    module="mainline",
    target_id="123",
    content="这是一条评论"
)

# 获取团队信息
team_info = api.get_team_info(eteamsid)
# 返回: {'tenantKey': 'xxx', 'tenantName': '测试团队', ...}

# 添加关注
api.add_watch(eteamsid, module="mainline", entity_id="123")

# 取消关注
api.remove_watch(eteamsid, module="mainline", entity_id="123")

# 发送提醒
api.send_remind(eteamsid, target_id="123", content="请及时处理")

# 保存配置
api.save_normal_config(eteamsid, "config_key", "config_value")
```

## 测试用例编写

### 基础结构

```python
import pytest
from core.base_api import BaseAPI

class TestMyAPI:
    """测试类命名规范：以Test开头"""

    @pytest.fixture(scope="class")
    def api(self):
        """Fixture：初始化API实例"""
        api = BaseAPI()
        yield api
        api.session.close()  # 清理资源

    @pytest.mark.basic
    @pytest.mark.smoke
    def test_example(self, api):
        """
        测试方法命名规范：以test开头
        文档字符串会显示在测试报告中
        """
        # 准备测试数据
        test_data = {"key": "value"}

        # 执行测试操作
        response = api.post("/api/test", json=test_data)

        # 验证结果
        assert response["code"] == 200
        assert "data" in response
```

### 使用Fixture

```python
class TestWithFixture:
    """使用Fixture的示例"""

    @pytest.fixture(scope="function")
    def login_session(self, api):
        """返回登录会话"""
        eteamsid, userid = api.get_admin_session()
        return eteamsid, userid

    def test_with_session(self, api, login_session):
        """使用会话进行测试"""
        eteamsid, userid = login_session
        response = api.get("/api/user/info", eteamsid=eteamsid)
        assert response["code"] == 200
```

### 参数化测试

```python
@pytest.mark.parametrize("keyword,expected_count", [
    ("测试", 10),
    ("Python", 10),
    ("AI", 10),
])
def test_search_suggestion(api, keyword, expected_count):
    """参数化测试示例"""
    params = {"wd": keyword}
    response = api.get("/sugrec", params=params)
    assert len(response.get("g", [])) >= expected_count
```

### 跳过和预期失败

```python
@pytest.mark.skip(reason="功能未实现")
def test_not_implemented():
    """跳过此测试"""
    pass

@pytest.mark.skipif(condition, reason="条件满足时跳过")
def test_conditional_skip():
    """条件跳过"""
    pass

@pytest.mark.xfail(reason="已知问题")
def test_known_issue():
    """预期失败"""
    assert False
```

## 百度接口测试示例

框架已包含百度搜索建议接口的完整测试用例，展示如何测试公开的HTTP接口。

### 接口信息

- **接口名称**: 百度搜索建议API
- **接口地址**: https://www.baidu.com/sugrec
- **请求方法**: GET
- **请求参数**:
  | 参数 | 说明 | 示例 |
  |------|------|------|
  | wd | 搜索关键词 | 测试 |
  | json | 返回JSON格式 | 1 |
  | prod | 产品类型 | pc |
  | from | 来源 | pc_web |

- **响应格式**:
```json
{
  "q": "测试",
  "g": [
    {"q": "测试infp人格", "sa": "s_1"},
    {"q": "测试MBTI人格免费", "sa": "s_2"}
  ]
}
```

### 测试用例

```python
@pytest.mark.basic
@pytest.mark.smoke
def test_baidu_suggestion_basic(self, api):
    """测试百度搜索建议接口 - 基础功能"""
    # 构建请求参数
    params = {
        "wd": "测试",
        "json": "1",
        "prod": "pc"
    }

    # 发送请求
    response = api.session.get(
        "https://www.baidu.com/sugrec",
        params=params
    )

    # 验证状态码
    assert response.status_code == 200

    # 验证JSON格式
    data = response.json()
    assert "q" in data
    assert "g" in data

    # 验证建议列表
    suggestions = data["g"]
    assert len(suggestions) > 0
```

### 运行百度测试

```bash
# 运行所有百度测试
pytest tests/test_baidu_sug.py -v

# 运行基础测试
pytest tests/test_baidu_sug.py::TestBaiduSuggestionAPI -v

# 运行单个测试
pytest tests/test_baidu_sug.py::TestBaiduSuggestionAPI::test_baidu_suggestion_basic -v

# 生成报告
pytest tests/test_baidu_sug.py --html=report/baidu_report.html
```

## pytest标记说明

框架预定义了以下标记用于测试分类：

### 功能模块标记

| 标记 | 说明 |
|------|------|
| `@pytest.mark.basic` | 基础功能测试 |
| `@pytest.mark.smoke` | 冒烟测试 |
| `@pytest.mark.auth` | 认证授权模块 |
| `@pytest.mark.user` | 用户管理模块 |
| `@pytest.mark.workflow` | 工作流模块 |
| `@pytest.mark.document` | 文档管理模块 |
| `@pytest.mark.attend` | 考勤模块 |
| `@pytest.mark.calendar` | 日程模块 |
| `@pytest.mark.crm` | 客户关系管理模块 |

### 优先级标记

| 标记 | 说明 |
|------|------|
| `@pytest.mark.P0` | P0级用例(核心功能) |
| `@pytest.mark.P1` | P1级用例(重要功能) |
| `@pytest.mark.P2` | P2级用例(一般功能) |
| `@pytest.mark.P3` | P3级用例(边缘功能) |

### 测试类型标记

| 标记 | 说明 |
|------|------|
| `@pytest.mark.integration` | 集成测试 |
| `@pytest.mark.unit` | 单元测试 |
| `@pytest.mark.regression` | 回归测试 |

## 常用命令

### 基础命令

```bash
# 运行所有测试
pytest

# 运行指定目录
pytest tests/

# 运行指定文件
pytest tests/test_demo.py

# 运行指定类
pytest tests/test_demo.py::TestDemoAPI

# 运行指定方法
pytest tests/test_demo.py::TestDemoAPI::test_example
```

### 标记筛选

```bash
# 运行冒烟测试
pytest -m smoke

# 运行P0级用例
pytest -m P0

# 运行基础功能测试
pytest -m basic

# 组合标记 (或关系)
pytest -m "smoke or P0"

# 组合标记 (与关系)
pytest -m "smoke and P0"

# 排除标记
pytest -m "not smoke"
```

### 输出控制

```bash
# 详细输出
pytest -v

# 更详细输出
pytest -vv

# 显示打印信息
pytest -s

# 显示最长10个失败信息
pytest --tb=long

# 只显示一行失败信息
pytest --tb=line

# 不显示traceback
pytest --tb=no
```

### 测试执行

```bash
# 失败重跑2次
pytest --reruns 2

# 失败后立即停止
pytest -x

# 达到2个失败后停止
pytest --maxfail=2

# 并发执行 (需要pytest-xdist)
pytest -n auto

# 顺序执行 (需要pytest-order)
pytest --order-dependencies
```

### 报告生成

```bash
# 生成HTML报告
pytest --html=report/report.html --self-contained-html

# 生成Allure报告 (需要allure-pytest)
pytest --alluredir=allure-results
allure serve allure-results

# 生成覆盖率报告 (需要pytest-cov)
pytest --cov=core --cov-report=html
```

### 组合使用

```bash
# 完整测试命令示例
pytest -m smoke -v --reruns 2 --html=report/smoke_report.html
```

## 配置说明

### config.py 配置项

```python
class RunConfig:
    """测试运行配置"""

    # ==================== 环境配置 ====================
    BASE_URL = "your-server.com"    # 测试环境地址
    IS_HTTPS = True                 # HTTPS开关
    TIMEOUT = 30                    # 超时时间(秒)

    # ==================== 账号配置 ====================
    ACCOUNT_FILE = "account.txt"    # 测试账号文件

    # ==================== 日志配置 ====================
    IS_LOG = False                  # 是否启用日志
    IS_TRACE_ID = True             # 是否打印traceId

    # ==================== Nacos配置 ====================
    NACOS_MAP = {                   # Nacos平台映射
        "server.com": {
            "nacosUrl": "http://nacos-server",
            "nacosUser": "nacos",
            "nacosPasswd": "nacos"
        }
    }

    # ==================== Zookeeper配置 ====================
    ZOOKEEPER_MAP = {              # Zookeeper平台映射
        "server.com": {
            "url": "http://zk-server",
            "user": "admin",
            "passwd": "manager"
        }
    }
```

### pytest.ini 配置项

```ini
[pytest]
# 测试标记
markers =
    basic: 基础功能测试
    smoke: 冒烟测试
    P0: P0级用例

# 测试路径
testpaths = tests

# 文件匹配模式
python_files = test_*.py
python_classes = Test*
python_functions = test_*

# 输出选项
addopts =
    -v
    --strict-markers
    --tb=short

# 最小Python版本
minversion = 3.7
```

## 最佳实践

### 1. 测试用例组织

```
tests/
├── test_basic/              # 基础功能测试
│   ├── test_auth.py
│   └── test_user.py
├── test_business/           # 业务功能测试
│   ├── test_workflow.py
│   └── test_document.py
└── test_integration/        # 集成测试
    └── test_e2e.py
```

### 2. 测试数据管理

```python
# 使用fixture管理测试数据
@pytest.fixture
def test_user():
    return {
        "name": "测试用户",
        "email": "test@example.com",
        "phone": "13800138000"
    }

# 使用外部文件
@pytest.fixture
def config_data():
    with open("test_data/config.json") as f:
        return json.load(f)
```

### 3. 断言最佳实践

```python
# 好的断言
assert response["code"] == 200, f"期望200，实际{response['code']}"
assert "data" in response, "响应中缺少data字段"
assert len(response["data"]) > 0, "数据列表不应为空"

# 使用get_value安全提取
user_id = api.get_value(response, ['data', 'user', 'id'])
```

### 4. 错误处理

```python
def test_with_proper_error_handling(api):
    try:
        response = api.get("/api/endpoint")
        assert response["code"] == 200
    except AssertionError as e:
        # 记录详细错误信息
        print(f"请求失败: {e}")
        print(f"响应内容: {response}")
        raise
```

### 5. 测试独立性

```python
# 每个测试独立运行，不依赖其他测试
@pytest.fixture(autouse=True)
def setup_test():
    # 测试前准备
    print("测试开始")
    yield
    # 测试后清理
    print("测试结束")
```

## 常见问题

### Q: 如何处理HTTPS证书问题？

A: 在发送请求时禁用SSL验证：
```python
response = api.session.get(url, verify=False)
```

### Q: 如何添加请求头？

A: 在请求时传入headers参数：
```python
headers = {"Content-Type": "application/json", "Authorization": "Bearer token"}
response = api.post(url, headers=headers, json=data)
```

### Q: 如何处理文件上传？

A: 使用upload_file方法或自定义请求：
```python
# 方法1：使用框架方法
result = api.upload_file(eteamsid, "/path/to/file.pdf")

# 方法2：自定义请求
with open("file.pdf", "rb") as f:
    files = {"file": f}
    response = api.post(url, files=files)
```

### Q: 如何调试测试用例？

A: 使用pytest的调试功能：
```bash
# 使用pdb调试
pytest --pdb

# 在测试失败时进入pdb
pytest --pdb --pdb-trace

# 使用print调试
pytest -s
```

### Q: 如何生成测试报告？

A: 使用HTML报告插件：
```bash
pytest --html=report/report.html --self-contained-html
```

## 扩展开发

### 添加新的API封装类

1. 在core目录下创建新的API类
2. 继承BaseAPI或PublicAPI
3. 实现具体的业务方法

```python
# core/my_api.py
from core.base_api import BaseAPI

class MyAPI(BaseAPI):
    """自定义API类"""

    def get_user_list(self, eteamsid, page=1, size=20):
        """获取用户列表"""
        params = {"page": page, "size": size}
        return self.get("/api/user/list", eteamsid=eteamsid, params=params)

    def create_user(self, eteamsid, user_data):
        """创建用户"""
        return self.post("/api/user/create", eteamsid=eteamsid, json=user_data)
```

### 添加自定义Fixture

```python
# conftest.py
@pytest.fixture(scope="session")
def custom_resource():
    """自定义资源fixture"""
    resource = create_resource()
    yield resource
    cleanup_resource(resource)
```

## 贡献指南

欢迎提交Issue和Pull Request！

## 许可证

本项目仅供学习和参考使用。

## 联系方式

如有问题或建议，请联系测试团队。
