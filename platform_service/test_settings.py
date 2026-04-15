"""服务层测试专用 Django 设置。"""

from __future__ import annotations

from .settings import *  # noqa: F403

# 测试阶段与正式开发统一复用本地 MySQL 基线，禁止回退到 SQLite。
MIGRATION_MODULES = {}
