"""V2 服务层迁移专用 Django 设置。"""

from __future__ import annotations

from .test_settings import *  # noqa: F403


# 迁移生成需要启用真实迁移模块，不能沿用测试环境的禁用配置。
MIGRATION_MODULES = {}

