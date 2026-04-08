"""V2 场景服务应用配置。"""

from __future__ import annotations

from django.apps import AppConfig


class ScenarioServiceConfig(AppConfig):
    """场景服务应用配置。"""

    default_auto_field = "django.db.models.AutoField"
    name = "scenario_service"
