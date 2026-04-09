# 本地 MySQL 数据库信息

## 1. 文档说明
- 文档名称：本地 MySQL 数据库信息
- 所属项目：接口自动化测试平台
- 生成时间：2026-04-09
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
- `scenario_service_scenarioexecutionrecord`
- `scenario_service_scenariorecord`
- `scenario_service_scenarioreviewrecord`
- `scenario_service_scenariosteprecord`

---
## 5. 说明
- 当前数据库为本地开发与测试使用的 MySQL 实例。
- 当前表结构主要来自 Django 内置认证/会话表，以及 `scenario_service` 场景服务相关业务表。
- 如后续执行新的 Django migration，本文件中的表清单需要同步更新。
