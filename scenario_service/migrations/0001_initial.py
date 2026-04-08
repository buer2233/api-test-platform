# 由 Django 5.2.9 于 2026-04-08 09:45 生成

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='ScenarioRecord',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('scenario_id', models.CharField(max_length=128, unique=True)),
                ('scenario_code', models.CharField(max_length=128)),
                ('scenario_name', models.CharField(max_length=255)),
                ('module_id', models.CharField(blank=True, max_length=128, null=True)),
                ('scenario_desc', models.TextField(blank=True, null=True)),
                ('source_ids', models.JSONField(default=list)),
                ('priority', models.CharField(default='medium', max_length=32)),
                ('review_status', models.CharField(default='pending', max_length=32)),
                ('execution_status', models.CharField(default='not_started', max_length=32)),
                ('current_stage', models.CharField(default='draft', max_length=32)),
                ('issue_count', models.PositiveIntegerField(default=0)),
                ('step_count', models.PositiveIntegerField(default=0)),
                ('workspace_root', models.CharField(blank=True, max_length=255, null=True)),
                ('report_path', models.CharField(blank=True, max_length=255, null=True)),
                ('latest_execution_id', models.CharField(blank=True, max_length=128, null=True)),
                ('passed_count', models.PositiveIntegerField(default=0)),
                ('failed_count', models.PositiveIntegerField(default=0)),
                ('skipped_count', models.PositiveIntegerField(default=0)),
                ('issues', models.JSONField(default=list)),
                ('metadata', models.JSONField(default=dict)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='ScenarioExecutionRecord',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('execution_id', models.CharField(max_length=128, unique=True)),
                ('execution_status', models.CharField(default='not_started', max_length=32)),
                ('passed_count', models.PositiveIntegerField(default=0)),
                ('failed_count', models.PositiveIntegerField(default=0)),
                ('skipped_count', models.PositiveIntegerField(default=0)),
                ('report_path', models.CharField(blank=True, max_length=255, null=True)),
                ('failure_summary', models.TextField(blank=True, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('scenario', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='executions', to='scenario_service.scenariorecord')),
            ],
            options={
                'ordering': ['-created_at', '-id'],
            },
        ),
        migrations.CreateModel(
            name='ScenarioReviewRecord',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('review_id', models.CharField(max_length=128, unique=True)),
                ('reviewer', models.CharField(max_length=128)),
                ('review_comment', models.TextField(blank=True, null=True)),
                ('review_status', models.CharField(max_length=32)),
                ('reviewed_at', models.DateTimeField()),
                ('metadata', models.JSONField(default=dict)),
                ('scenario', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='reviews', to='scenario_service.scenariorecord')),
            ],
            options={
                'ordering': ['reviewed_at', 'id'],
            },
        ),
        migrations.CreateModel(
            name='ScenarioStepRecord',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('step_id', models.CharField(max_length=128, unique=True)),
                ('step_order', models.PositiveIntegerField()),
                ('step_name', models.CharField(max_length=255)),
                ('operation_id', models.CharField(blank=True, max_length=128, null=True)),
                ('input_bindings', models.JSONField(default=list)),
                ('expected_bindings', models.JSONField(default=list)),
                ('assertion_ids', models.JSONField(default=list)),
                ('retry_policy', models.JSONField(default=dict)),
                ('optional', models.BooleanField(default=False)),
                ('metadata', models.JSONField(default=dict)),
                ('scenario', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='steps', to='scenario_service.scenariorecord')),
            ],
            options={
                'ordering': ['step_order', 'id'],
            },
        ),
    ]
