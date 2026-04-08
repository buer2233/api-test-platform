"""V2 服务层测试专用 Django 设置。"""

from __future__ import annotations

from pathlib import Path

from .settings import *  # noqa: F403


TEST_DB_DIR = Path(BASE_DIR) / ".pytest_tmp"  # type: ignore[name-defined]
TEST_DB_DIR.mkdir(exist_ok=True)

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": str(TEST_DB_DIR / "service_test.sqlite3"),
    }
}

MIGRATION_MODULES = {
    "scenario_service": None,
}
