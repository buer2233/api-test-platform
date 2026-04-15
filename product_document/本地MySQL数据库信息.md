# 本地 MySQL 数据库信息

## 1. 文档说明
- 文档名称：本地 MySQL 数据库信息
- 所属项目：接口自动化测试平台
- 生成时间：2026-04-14
- 适用范围：当前本地开发与测试环境

---
## 2. MySQL 服务信息
- 服务名称：`MySQL84`
- 服务状态：`Running`
- 启动方式：`Automatic`
- MySQL 版本：`8.4.6`
- 服务程序路径：`C:\Program Files\MySQL\MySQL Server 8.4\bin\mysqld.exe`

---
## 3. 当前项目连接信息
- 连接 IP：`127.0.0.1`
- 连接端口：`3306`
- 数据库名：`api_test_platform`
- 用户名：`platform_service`
- 密码：`PlatformService_2025!`

---
## 4. 当前数据库包含的表
- `auth_group`
- `auth_group_permissions`
- `auth_permission`
- `auth_user`
- `auth_user_groups`
- `auth_user_user_permissions`
- `django_content_type`
- `django_migrations`
- `django_session`
- `scenario_service_baselineversionrecord`
- `scenario_service_governancemigrationrecord`
- `scenario_service_projectrecord`
- `scenario_service_scenarioexecutionrecord`
- `scenario_service_scenariorecord`
- `scenario_service_scenarioreviewrecord`
- `scenario_service_scenariorevisionrecord`
- `scenario_service_scenariosetrecord`
- `scenario_service_scenariosourcerecord`
- `scenario_service_scenariosuggestionrecord`
- `scenario_service_scenariosteprecord`
- `scenario_service_testenvironmentrecord`

---
## 5. 说明
- 当前数据库为本地开发与测试使用的 MySQL 实例。
- 当前表结构主要来自 Django 内置认证/会话表，以及 `scenario_service` 场景服务相关业务表。
- 2026-04-10 已新增 `scenario_service_scenariosourcerecord`，用于承接场景与步骤的来源追溯事实。
- 2026-04-10 已新增 `scenario_service_scenariosuggestionrecord`，用于承接 AI/规则建议记录与采纳治理留痕。
- 2026-04-14 已应用 `scenario_service.0005_baselineversionrecord_governancemigrationrecord_and_more`，新增项目、测试环境、场景集、基线版本和治理迁移记录相关表。
- 2026-04-14 已基于本地 MySQL 完成一轮 V3 P0 服务层真实冒烟，执行结果为 `passed`，治理上下文为 `mysql-p0-project / mysql-p0-env / mysql-p0-set / baseline-v1`。
- 2026-04-15 起 `platform_service.test_settings` 已切换为正式 MySQL 基线配置，后续服务测试与浏览器冒烟不再允许回退到 SQLite。
- 2026-04-15 已验证服务测试运行期数据库连接直接指向 `api_test_platform`，`SELECT DATABASE()` 返回 `api_test_platform`。
- 2026-04-15 起 `service_tests` 已取消自动清库策略，测试数据、浏览器点测数据和数据库事实数据默认保留。
- 2026-04-15 最近一次留存数据快照：
  - `project_count=21`
  - `environment_count=21`
  - `scenario_set_count=21`
  - `baseline_version_count=22`
  - `migration_count=4`
  - `scenario_count=40`
  - `execution_count=16`
- 如后续执行新的 Django migration，本文件中的表清单需要同步更新。
