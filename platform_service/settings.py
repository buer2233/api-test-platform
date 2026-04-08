"""V2 服务层 Django 设置。"""

from __future__ import annotations

import os
from pathlib import Path

import pymysql


def configure_pymysql_mysqlclient_compatibility() -> None:
    """配置 PyMySQL 兼容 Django 对 mysqlclient 版本门槛的检查。"""
    pymysql.version_info = (1, 4, 6, "final", 0)
    pymysql.__version__ = "1.4.6"
    pymysql.install_as_MySQLdb()


configure_pymysql_mysqlclient_compatibility()

BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = "v2-platform-service-fixed-secret"
DEBUG = True
ALLOWED_HOSTS = ["*"]

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "rest_framework",
    "scenario_service",
]

MIDDLEWARE = [
    "django.middleware.common.CommonMiddleware",
]

ROOT_URLCONF = "platform_service.urls"
TEMPLATES: list[dict] = []
WSGI_APPLICATION = "platform_service.wsgi.application"
ASGI_APPLICATION = "platform_service.asgi.application"

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.mysql",
        "NAME": os.getenv("PLATFORM_MYSQL_DB", "api_test_platform"),
        "USER": os.getenv("PLATFORM_MYSQL_USER", "root"),
        "PASSWORD": os.getenv("PLATFORM_MYSQL_PASSWORD", "root"),
        "HOST": os.getenv("PLATFORM_MYSQL_HOST", "127.0.0.1"),
        "PORT": os.getenv("PLATFORM_MYSQL_PORT", "3306"),
        "OPTIONS": {
            "charset": "utf8mb4",
        },
    }
}

LANGUAGE_CODE = "zh-hans"
TIME_ZONE = "Asia/Shanghai"
USE_I18N = True
USE_TZ = True
DEFAULT_AUTO_FIELD = "django.db.models.AutoField"

REST_FRAMEWORK = {
    "UNAUTHENTICATED_USER": None,
}
