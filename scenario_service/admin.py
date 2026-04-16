"""V2 场景服务后台注册。"""

from __future__ import annotations

from django.contrib import admin

from scenario_service.models import (
    BaselineVersionRecord,
    GovernanceMigrationRecord,
    ProjectRecord,
    ScenarioExecutionRecord,
    ScenarioScheduleBatchRecord,
    ScenarioScheduleItemRecord,
    ScenarioRecord,
    ScenarioReviewRecord,
    ScenarioSetRecord,
    ScenarioStepRecord,
    TestEnvironmentRecord,
)


admin.site.register(ProjectRecord)
admin.site.register(TestEnvironmentRecord)
admin.site.register(ScenarioSetRecord)
admin.site.register(BaselineVersionRecord)
admin.site.register(GovernanceMigrationRecord)
admin.site.register(ScenarioRecord)
admin.site.register(ScenarioStepRecord)
admin.site.register(ScenarioReviewRecord)
admin.site.register(ScenarioExecutionRecord)
admin.site.register(ScenarioScheduleBatchRecord)
admin.site.register(ScenarioScheduleItemRecord)
