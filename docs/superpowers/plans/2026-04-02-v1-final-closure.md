# V1 最终收口 Implementation Plan

## 1. 目标
完成 V1 阶段最后一轮收口，实现以下结果：
1. `business_rule` 支持第二个最小规则代码 `positive_integer`；
2. `run` / `inspect` 服务摘要具备更稳定的资产聚合字段；
3. `api_test/requirements.txt` 满足固定版本和无无用依赖的治理要求；
4. 在完整回归通过后，把 V1 状态切换为已完成，并把后续增强项转入 V2。

## 2. 文件范围

### 新增
- `docs/superpowers/specs/2026-04-02-v1-final-closure-design.md`
- `docs/superpowers/plans/2026-04-02-v1-final-closure.md`
- `tests/test_dependency_governance.py`

### 修改
- `platform_core/models.py`
- `platform_core/renderers.py`
- `platform_core/rules.py`
- `platform_core/services.py`
- `platform_core/assets.py`
- `platform_core/__init__.py`
- `tests/platform_core/test_models.py`
- `tests/platform_core/test_templates_and_rules.py`
- `tests/platform_core/test_services_and_assets.py`
- `api_test/requirements.txt`
- `README.md`
- `product_document/架构设计/中间模型设计说明书.md`
- `product_document/架构设计/模板体系与代码生成规范说明书.md`
- `product_document/阶段文档/V1阶段工作计划文档.md`
- `product_document/阶段文档/V1实施计划与开发任务拆解说明书.md`
- `product_document/阶段文档/V2阶段工作计划文档.md`
- `product_document/测试文档/详细测试用例说明书(V1).md`
- `task_plan.md`
- `findings.md`
- `progress.md`

## 3. 执行步骤

### 任务 A：先写失败测试
1. 在 `tests/platform_core/test_templates_and_rules.py` 中补 `positive_integer` 的模板渲染与假响应失败测试。
2. 在 `tests/platform_core/test_services_and_assets.py` 中补 `positive_integer` 规则通过测试，以及服务摘要新增聚合字段失败测试。
3. 在 `tests/platform_core/test_models.py` 中补摘要模型新增字段失败测试。
4. 新增 `tests/test_dependency_governance.py`，锁定 `api_test/requirements.txt` 的固定版本约束和 `rsa` 删除要求。
5. 运行定向 pytest，确认红灯。

### 任务 B：实现最小代码
1. 扩展 `RuleValidator` 的支持规则集合。
2. 扩展 `TemplateRenderer` 的 `business_rule` 模板渲染和假响应构造。
3. 为模型与服务增加资产聚合摘要结构。
4. 修正 `api_test/requirements.txt` 为固定版本并删除 `rsa`。

### 任务 C：绿灯与回归
1. 重跑定向测试，确认新增场景转绿。
2. 依次执行：
   - `python -m pytest tests/platform_core -v --basetemp .pytest_tmp/platform_core_v1_final_closure_full`
   - `python -m pytest tests -v --basetemp .pytest_tmp/root_v1_final_closure_full`
   - `python -m pytest api_test/tests -v --basetemp .pytest_tmp/api_test_v1_final_closure_full`
   - `python api_test/run_test.py --public-baseline`
   - `cd api_test && python run_test.py --public-baseline`

### 任务 D：文档收口
1. README 补记本轮新增能力、测试结果和阶段结论。
2. V1 阶段文档改为“已完成”，并把更复杂规则、深层结构和依赖编排转入 V2。
3. V2 阶段文档补记从 V1 承接的增强项。
4. 更新本地计划与进展记录。

## 4. 完成判断
满足以下条件即可结束本轮：
1. 所有新增测试已按 TDD 从失败到通过；
2. 全量回归与公开基线均通过；
3. 文档已同步且口径一致；
4. `git status` 仅保留预期修改与 `.idea/` 未跟踪目录。

## 5. 执行结果
截至 2026-04-02，本计划已执行完成，结果如下：
1. 已完成失败测试与红灯确认：
   - `python -m pytest tests/platform_core/test_models.py tests/platform_core/test_templates_and_rules.py tests/platform_core/test_services_and_assets.py tests/test_dependency_governance.py -k "positive_integer or inventory_summary or source_type or execution_id or asset_type_breakdown or dependency_governance" -v --basetemp .pytest_tmp/v1_final_closure_red`
   - 结果：`1 error`
2. 已完成最小实现并转绿：
   - 同口径绿灯验证结果：`6 passed`
3. 已完成全量回归：
   - `tests/platform_core`：`63 passed`
   - 根测试：`70 passed`
   - `api_test/tests`：`39 passed`
   - 公开基线双入口：`12 passed, 27 deselected`
4. 已完成 README、V1/V2 阶段文档、测试说明书和本地记录同步。
