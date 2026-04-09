# 2026-04-09 V2 第五实施子阶段：抓包驱动草稿化接入计划

## 目标
- 补齐 V2 第二条输入路线：抓包驱动草稿化接入。
- 打通“抓包导入 -> 清洗去重 -> 动态值候选 -> 场景草稿 -> 审核接入”的最小闭环。
- 不把抓包路线扩张为正式执行闭环，仍保持草稿化边界。

## 本轮范围
1. 新增独立抓包解析模块，不回塞到现有文档解析器。
2. 支持最小 HAR JSON 导入、静态噪声过滤和重复请求折叠。
3. 支持参数归一化、动态值候选提取和依赖候选生成。
4. 开放抓包导入服务接口与场景草稿持久化。
5. 同步阶段文档、测试文档、README 与本地记录。

## TDD 清单
1. 先写 `tests/platform_core/test_parser_inputs.py` 的抓包红灯测试。
2. 再写 `tests/platform_core/test_services_and_assets.py` 的服务摘要红灯测试。
3. 再写 `service_tests/test_traffic_capture_flow.py` 的 DRF 红灯测试。
4. 完成最小实现并跑定向绿灯。
5. 跑 `service_tests`、`tests/platform_core`、`tests` 与 `api_test/tests` 回归。

## 验证命令
```bash
.venv_service\Scripts\python.exe -m pytest tests\platform_core\test_parser_inputs.py -k traffic_capture_parser -v --basetemp .pytest_tmp/v2_phase5_parser_green1
.venv_service\Scripts\python.exe -m pytest tests\platform_core\test_services_and_assets.py -k traffic_capture -v --basetemp .pytest_tmp/v2_phase5_service_summary_green1
.venv_service\Scripts\python.exe -m pytest service_tests\test_traffic_capture_flow.py -v --ds=platform_service.test_settings --basetemp .pytest_tmp/v2_phase5_drf_green1
```

## 结果目标
- 抓包导入已可过滤噪声、完成去重归一化并产出场景草稿。
- 抓包草稿默认进入审核链路，保留低置信提示而不是直接执行。
- 服务层和 DRF 契约已开放抓包导入能力。
