"""V2 场景服务后台注册。"""

from __future__ import annotations

from django.contrib import admin

from scenario_service.models import (
    ScenarioExecutionRecord,
    ScenarioRecord,
    ScenarioReviewRecord,
    ScenarioStepRecord,
)


admin.site.register(ScenarioRecord)
admin.site.register(ScenarioStepRecord)
admin.site.register(ScenarioReviewRecord)
admin.site.register(ScenarioExecutionRecord)
