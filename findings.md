# 当前发现

## V1 状态判断
- `product_document/阶段文档/V1阶段工作计划文档.md` 已切换为 V1 验收版，当前阶段判断为“V1 已完成”。
- `product_document/测试文档/详细测试用例说明书(V1).md` 已同步到最终验收状态，P0 全部通过，P1/P2 增强项已转入 V2 承接。

## 代码发现
- `platform_core/renderers.py` 当前已支持 `business_rule(non_empty_string)` 与 `business_rule(positive_integer)`，并会按规则代码自动生成匹配的最小假响应值。
- `platform_core/rules.py` 当前已允许 `business_rule.rule_code` 的两类最小取值：`non_empty_string` 与 `positive_integer`。
- `platform_core/services.py` 的 `run_document_pipeline_summary()` 和 `inspect_workspace_summary()` 已补齐 `source_type`、`execution_id` 和资产聚合字段，当前摘要输出可直接被后续服务接口消费。
- `platform_core/pipeline.py` 当前会在目录级执行结束后回写各生成记录的 `execution_status`。
- `api_test/requirements.txt` 已改为固定版本约束，并已删除未使用的 `rsa` 依赖。

## 本轮设计结论
- 采用最小收口方案，不扩展解析器自动推断，不做 DSL。
- 继续为 `business_rule` 增加 `positive_integer` 规则代码，用于验证“非空字符串之外的第二档规则”。
- 对服务摘要补充更稳定的资产聚合信息，用于把当前 V1 输出进一步收敛到后续 Web / 客户端可直接承接的结构。
- 通过新增治理测试把依赖约束固化下来，避免后续再次回退到宽松版本和无用依赖。

## 已完成验证
- 定向红灯：`python -m pytest tests/platform_core/test_models.py tests/platform_core/test_templates_and_rules.py tests/platform_core/test_services_and_assets.py tests/test_dependency_governance.py -k "positive_integer or inventory_summary or source_type or execution_id or asset_type_breakdown or dependency_governance" -v --basetemp .pytest_tmp/v1_final_closure_red`
  - 结果：`1 error`
  - 含义：`WorkspaceAssetInventorySummary` 尚未实现，确认新增摘要模型确实缺失
- 定向绿灯：同口径 `... --basetemp .pytest_tmp/v1_final_closure_green`
  - 结果：`6 passed`
- 全量回归：
  - `python -m pytest tests/platform_core -v --basetemp .pytest_tmp/platform_core_v1_final_closure_full` -> `63 passed`
  - `python -m pytest tests -v --basetemp .pytest_tmp/root_v1_final_closure_full` -> `70 passed`
  - `python -m pytest api_test/tests -v --basetemp .pytest_tmp/api_test_v1_final_closure_full` -> `39 passed`
  - `python api_test/run_test.py --public-baseline` -> `12 passed, 27 deselected`
  - `cd api_test && python run_test.py --public-baseline` -> `12 passed, 27 deselected`
