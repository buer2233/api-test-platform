"""主工作台三段式信息架构测试。"""

from __future__ import annotations

from contextlib import nullcontext
import importlib
import os
import sys
import types

import django
import pymysql
import pytest
from rest_framework.test import APIClient


def _build_local_test_settings_module() -> str:
    """构造当前测试文件专用的 Django 设置模块，避免改动全局配置。"""
    module_name = "service_tests._mainline_workbench_settings"
    if module_name in sys.modules:
        return module_name
    base_settings = importlib.import_module("platform_service.test_settings")
    settings_module = types.ModuleType(module_name)
    for attribute in dir(base_settings):
        if attribute.isupper():
            setattr(settings_module, attribute, getattr(base_settings, attribute))
    sys.modules[module_name] = settings_module
    return module_name


# Django 5 对 mysqlclient 版本门槛更高，这里仅为当前测试文件补齐兼容信息。
pymysql.version_info = (2, 2, 1, "final", 0)
pymysql.__version__ = "2.2.1"
pymysql.install_as_MySQLdb()
os.environ.setdefault("DJANGO_SETTINGS_MODULE", _build_local_test_settings_module())
django.setup()


class _LocalDjangoDbBlocker:
    """提供最小数据库解锁上下文，兼容当前仓库的服务测试夹具。"""

    def unblock(self):
        """返回空上下文，允许现有夹具继续执行迁移。"""
        return nullcontext()


@pytest.fixture(scope="session")
def django_db_blocker():
    """为当前测试文件补齐 pytest-django 缺失时的兼容夹具。"""
    return _LocalDjangoDbBlocker()


def test_mainline_workbench_renders_three_column_layout_and_primary_regions():
    """主工作台应渲染三段式布局和核心区域。"""
    client = APIClient()

    response = client.get("/ui/v3/workbench/")

    assert response.status_code == 200
    content = response.content.decode("utf-8")
    assert 'data-testid="mainline-shell"' in content
    assert 'data-testid="left-tree-panel"' in content
    assert 'data-testid="middle-list-panel"' in content
    assert 'data-testid="right-detail-panel"' in content
    assert 'data-testid="capture-entry-actions"' in content
    assert 'data-testid="testcase-list-panel"' in content
    assert 'data-testid="detail-fixed-summary"' in content
    assert 'data-testid="detail-tab-method-chain"' in content
    assert 'data-testid="detail-tab-execution-history"' in content
    assert 'data-testid="detail-tab-allure-report"' in content
