"""服务层 Django 测试夹具。"""

from __future__ import annotations

import os

import pytest
from django.apps import apps
from django.core.management import call_command


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "platform_service.settings")


def _clear_scenario_service_tables() -> None:
    """按依赖逆序清理场景服务应用中的业务表数据。"""
    app_config = apps.get_app_config("scenario_service")
    for model in reversed(list(app_config.get_models())):
        model.objects.all().delete()


@pytest.fixture(scope="session")
def django_db_setup(django_db_blocker):
    """复用当前本地 MySQL 基线库执行服务层测试前的迁移准备。"""
    with django_db_blocker.unblock():
        call_command("migrate", run_syncdb=True, verbosity=0)
        _clear_scenario_service_tables()


@pytest.fixture(autouse=True)
def isolate_scenario_service_tables(db):
    """在每个服务测试前后清理业务表，避免不同测试之间相互污染。"""
    _clear_scenario_service_tables()
    yield
    _clear_scenario_service_tables()
