# 2026-04-09 V2 第六实施子阶段：可用型入口工作台计划

## 目标
- 落地 V2 可用型 Web 入口工作台，承接导入、预览、审核确认、执行和结果查看。
- 保持入口页只消费服务层，不把核心逻辑回塞前端。
- 通过真实浏览器冒烟确认页面不是静态壳。

## 本轮范围
1. 新增场景列表接口，供入口页消费统一摘要。
2. 新增 `/ui/v2/workbench/` 页面路由与工作台模板。
3. 页面支持功能用例导入、抓包导入、场景切换、审核动作、执行触发和结果刷新。
4. 同步入口页视觉样式与当前深色平台化方向。
5. 执行页面契约测试、服务回归和浏览器冒烟。

## TDD 清单
1. 先写 `service_tests/test_workbench_ui.py` 红灯测试，锁定列表接口与页面骨架。
2. 完成最小页面和路由实现。
3. 跑入口页契约绿灯。
4. 跑服务层、平台核心和底座回归。
5. 启动本地 Django 服务，用浏览器验证功能用例导入、审核、执行和抓包导入。

## 验证命令
```bash
.venv_service\Scripts\python.exe -m pytest service_tests\test_workbench_ui.py -v --ds=platform_service.test_settings --basetemp .pytest_tmp/v2_phase6_ui_green1
.venv_service\Scripts\python.exe -m pytest service_tests -v --ds=platform_service.test_settings --basetemp .pytest_tmp/v2_phase5_6_service_tests
.venv_service\Scripts\python.exe -m pytest tests\platform_core -v --basetemp .pytest_tmp/v2_phase5_6_platform_core
.venv_service\Scripts\python.exe -m pytest tests -v --basetemp .pytest_tmp/v2_phase5_6_root
python -m pytest api_test\tests -v --basetemp .pytest_tmp/v2_phase5_6_api_test_fix
```

## 结果目标
- `/ui/v2/workbench/` 已具备可用型入口五段式流程。
- Web 入口与服务层状态展示保持一致。
- V2 规划内的 P0 主线闭环全部成立。
