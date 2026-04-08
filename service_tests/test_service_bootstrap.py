"""V2 服务层启动与运行环境测试。"""

from __future__ import annotations


def test_mysql_backend_compatibility_patch_exposes_supported_mysqldb_version():
    """服务层应为 Django MySQL 后端暴露满足要求的 MySQLdb 版本信息。"""
    import MySQLdb

    assert MySQLdb.version_info >= (1, 4, 3)

