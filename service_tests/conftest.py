"""服务层 MySQL 验收测试夹具。"""

from __future__ import annotations

import hashlib
import os
from datetime import datetime
from uuid import uuid4

import pytest
from django.core.management import call_command


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "platform_service.settings")


@pytest.fixture(scope="session", autouse=True)
def prepare_service_mysql_baseline(django_db_blocker):
    """在正式 MySQL 基线库上执行迁移准备，不创建独立测试库也不清空历史数据。"""
    with django_db_blocker.unblock():
        call_command("migrate", run_syncdb=True, verbosity=0)


@pytest.fixture(autouse=True)
def service_db_access(django_db_blocker):
    """为服务层测试直接打开正式 MySQL 访问权限，避免 pytest-django 事务回滚清空数据。"""
    with django_db_blocker.unblock():
        yield


@pytest.fixture(scope="session")
def service_test_run_token() -> str:
    """生成当前服务层回归批次的唯一标识，用于避免保留历史数据时发生业务编码冲突。"""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    return f"{timestamp}_{uuid4().hex[:6]}"


@pytest.fixture
def service_test_token(service_test_run_token: str, request: pytest.FixtureRequest) -> str:
    """生成当前测试用例的唯一标识片段，供 case_id、case_code 与 capture_name 拼接使用。"""
    node_digest = hashlib.sha1(request.node.nodeid.encode("utf-8")).hexdigest()[:6]
    return f"{service_test_run_token}_{node_digest}"
