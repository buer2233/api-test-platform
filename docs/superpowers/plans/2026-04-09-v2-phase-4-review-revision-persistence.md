# 2026-04-09 V2 第四实施子阶段：审核修订持久化计划

## 目标
- 补齐 V2 审核、预览、修订与确认链路中的“结构化修订”正式事实层。
- 打通“驳回 -> 结构化修订 -> 再审核 -> 执行”的最小生命周期闭环。
- 保持现有执行闭环、真实 MySQL 基线和 DRF 契约不回退。

## 本轮范围
1. 新增修订记录持久化模型。
2. 新增结构化修订服务方法与 DRF 接口。
3. 让场景详情可查询修订留痕。
4. 补齐迁移文件并应用到真实 MySQL。
5. 完成 SQLite 测试环境与真实 MySQL 环境的双重验证。

## TDD 清单
1. 先写 `service_tests/test_review_revision_flow.py` 红灯测试。
2. 确认缺口为 `revise_scenario()`、`/revise/` 路由和修订事实表不存在。
3. 编写最小实现。
4. 生成迁移文件并执行迁移一致性检查。
5. 跑 `service_tests` 全量回归。
6. 跑真实 MySQL 修订链路冒烟。

## 验证命令
```bash
.venv_service\Scripts\python.exe -m pytest service_tests\test_review_revision_flow.py -v --ds=platform_service.test_settings --basetemp .pytest_tmp/v2_phase4_revision_green1
.venv_service\Scripts\python.exe manage.py makemigrations scenario_service --check --dry-run --settings=platform_service.migration_settings
.venv_service\Scripts\python.exe -m pytest service_tests -v --ds=platform_service.test_settings --basetemp .pytest_tmp/v2_phase4_service_tests
```

## 结果目标
- `service_tests/test_review_revision_flow.py` 通过。
- `service_tests` 全量回归保持通过。
- 新迁移可在真实 MySQL 上落库。
- 真实 MySQL 下修订链路执行结果为 `passed`。
