"""JSONPlaceholder 资源级测试。"""


def test_jsonplaceholder_fixture_uses_public_base_url(jsonplaceholder_api):
    """公共 fixture 应绑定 JSONPlaceholder 默认基线地址。"""
    assert jsonplaceholder_api.base_url == "jsonplaceholder.typicode.com"
    assert jsonplaceholder_api.is_https is True


def test_get_user_resource_contract(jsonplaceholder_api):
    """用户资源应返回基础身份、地址和公司字段。"""
    user = jsonplaceholder_api.get_user(1)

    assert user["id"] == 1
    assert user["username"] == "Bret"
    assert "address" in user
    assert "company" in user
    assert "city" in user["address"]
    assert "name" in user["company"]


def test_list_users_returns_stable_collection_shape(jsonplaceholder_api):
    """用户列表应返回稳定的集合结构。"""
    users = jsonplaceholder_api.list_users()

    assert len(users) >= 10
    assert all("id" in user and "email" in user for user in users)


def test_list_todos_by_user_id_filters_collection(jsonplaceholder_api):
    """待办过滤应只返回指定用户的任务。"""
    todos = jsonplaceholder_api.list_todos(userId=1)

    assert len(todos) > 0
    assert all(todo["userId"] == 1 for todo in todos)
    assert all("completed" in todo for todo in todos)


def test_list_user_todos_supports_nested_route(jsonplaceholder_api):
    """嵌套路由 users/{id}/todos 应返回该用户待办。"""
    todos = jsonplaceholder_api.list_user_todos(1)

    assert len(todos) > 0
    assert all(todo["userId"] == 1 for todo in todos)
