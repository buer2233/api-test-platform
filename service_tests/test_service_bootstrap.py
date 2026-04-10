"""V2 服务层启动与运行环境测试。"""

from __future__ import annotations

import importlib


def test_mysql_backend_compatibility_patch_exposes_supported_mysqldb_version():
    """服务层应为 Django MySQL 后端暴露满足要求的 MySQLdb 版本信息。"""
    import MySQLdb

    assert MySQLdb.version_info >= (1, 4, 3)


def test_platform_service_defaults_follow_documented_local_mysql_baseline(monkeypatch):
    """服务层默认数据库连接参数应与仓库文档中的本地 MySQL 基线一致。"""
    monkeypatch.delenv("PLATFORM_MYSQL_DB", raising=False)
    monkeypatch.delenv("PLATFORM_MYSQL_USER", raising=False)
    monkeypatch.delenv("PLATFORM_MYSQL_PASSWORD", raising=False)
    monkeypatch.delenv("PLATFORM_MYSQL_HOST", raising=False)
    monkeypatch.delenv("PLATFORM_MYSQL_PORT", raising=False)

    import platform_service.settings as settings_module

    settings_module = importlib.reload(settings_module)

    assert settings_module.DATABASES["default"]["NAME"] == "api_test_platform"
    assert settings_module.DATABASES["default"]["USER"] == "platform_service"
    assert settings_module.DATABASES["default"]["PASSWORD"] == "PlatformService_2025!"
    assert settings_module.DATABASES["default"]["HOST"] == "127.0.0.1"
    assert settings_module.DATABASES["default"]["PORT"] == "3306"
