# 快速入门指南

## 第一步：安装依赖

```bash
pip install -r requirements.txt
```

## 第二步：配置测试环境

编辑 `config.py` 中的 `BASE_URL`，改为你的测试环境地址：

```python
class RunConfig:
    BASE_URL = "your-test-server.com/oa/second"
```

## 第三步：配置测试账号

编辑 `test_data/account.txt`，添加测试账号：

```
测试管理员,admin@test.com,Test123456,管理员,测试团队
测试成员,user@test.com,Test123456,普通成员,测试团队
```

## 第四步：运行测试

### 方式一：使用pytest命令

```bash
# 运行所有测试
pytest

# 运行冒烟测试
pytest -m smoke

# 生成HTML报告
pytest --html=report/report.html --self-contained-html
```

### 方式二：使用运行脚本

```bash
# 运行所有测试
python run_test.py

# 运行冒烟测试
python run_test.py -m smoke

# 生成HTML报告
python run_test.py --html
```

## 编写第一个测试用例

创建 `tests/test_my_first.py`：

```python
import pytest
from core.public_api import PublicAPI


class TestMyFirst:
    """我的第一个测试"""

    @pytest.fixture(scope="class")
    def api(self, admin_account):
        """初始化API"""
        api = PublicAPI()
        api.admin_username = admin_account['username']
        api.admin_password = admin_account['password']
        yield api
        api.session.close()

    @pytest.mark.basic
    def test_example(self, api):
        """示例测试"""
        # 登录获取会话
        eteamsid, userid = api.get_admin_session()

        # 获取团队信息
        team_info = api.get_team_info(eteamsid)

        # 断言验证
        assert 'tenantKey' in team_info
```

运行新测试：

```bash
pytest tests/test_my_first.py
```

## 常用场景示例

### 场景1：测试GET接口

```python
def test_get_api(api):
    eteamsid, _ = api.get_admin_session()

    response = api.get("/api/user/info", eteamsid=eteamsid)

    assert response['code'] == 200
    assert response['data']['name'] == "张三"
```

### 场景2：测试POST接口

```python
def test_post_api(api):
    eteamsid, _ = api.get_admin_session()

    payload = {
        "name": "测试数据",
        "content": "内容"
    }

    response = api.post("/api/data/create", eteamsid=eteamsid, json=payload)

    assert response['code'] == 200
    assert response['data']['id']
```

### 场景3：文件上传

```python
def test_upload_file(api):
    eteamsid, _ = api.get_admin_session()

    result = api.upload_file(
        eteamsid=eteamsid,
        file_path="test_data/test.pdf",
        module="document"
    )

    assert result['id']
    assert result['name'] == "test.pdf"
```

### 场景4：数据提取

```python
def test_extract_data(api):
    # 复杂响应数据
    response = {
        "code": 200,
        "data": {
            "list": [
                {"id": "1", "name": "项目A"},
                {"id": "2", "name": "项目B"}
            ]
        }
    }

    # 使用get_value提取嵌套数据
    project_list = api.get_value(response, ['data', 'list'])
    assert len(project_list) == 2

    # 使用find_dict_in_list查找
    project = api.find_dict_in_list(project_list, 'id', '2')
    assert project['name'] == "项目B"
```

## 测试标记使用

```python
# 基础功能测试
@pytest.mark.basic
def test_basic_function():
    pass

# 冒烟测试
@pytest.mark.smoke
def test_smoke():
    pass

# P0级核心功能
@pytest.mark.P0
def test_core_feature():
    pass

# 组合标记
@pytest.mark.basic
@pytest.mark.smoke
@pytest.mark.P0
def test_important():
    pass
```

## 获取帮助

- 查看详细文档：`README.md`
- 查看演示用例：`tests/test_demo.py`
- 查看核心类：`core/base_api.py`、`core/public_api.py`
