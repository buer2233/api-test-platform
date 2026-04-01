# V1 可追溯记录与服务摘要增强设计说明

## 1. 文档信息
- 日期：2026-04-01
- 主题：增强 `platform_core` 的生成记录、执行记录和工作区检查摘要
- 适用范围：`platform_core/`、`tests/platform_core/`、仓库 README 与 V1 阶段文档
- 关联目标：
  - 补齐 V1 P1 阶段“更细的生成记录测试”和“更细的执行记录测试”
  - 让应用服务层和 CLI 输出更接近后续 Django + DRF 可承接的结构化接口形态
  - 保持当前文档驱动最小闭环、资产清单和公开基线回归稳定

## 2. 背景与问题
当前 `platform_core` 已经完成 V1 最小闭环的首批实现，能够完成：
- OpenAPI / Swagger 文档解析；
- 中间模型构建；
- 模板渲染；
- 规则校验；
- pytest 执行；
- 资产清单落盘；
- 工作区检查。

但当前记录与服务边界仍然偏“能运行、能落盘”，还不够适合作为后续产品化接口的稳定输出：
- `GenerationRecord` 只记录最小生成元数据，缺少与最终资产内容直接关联的摘要字段；
- `ExecutionRecord` 只能表达通过/失败，不包含退出码、执行命令和测试数量摘要；
- `AssetWorkspace.inspect_manifest()` 只能返回资产摘要，不能直接返回生成记录检查摘要；
- CLI `run` 输出仍然偏流水线内部结构，缺少稳定的执行统计字段；
- 当前测试说明书中已明确 P1 需要“更细的生成记录测试”和“更细的执行记录测试”，但仓库中尚未真正落地。

如果继续只做“能跑”的记录文件，后续服务化时会出现两类问题：
1. 客户端 / Web / DRF 接口需要重新拼装摘要，造成重复逻辑；
2. 执行回放、资产核查和问题定位只能依赖文件内容人工排查，不利于平台化验收。

## 3. 方案比较

### 方案一：增强记录模型并把摘要能力直接收口到服务层与 CLI
做法：
- 扩展 `GenerationRecord` 和 `ExecutionRecord` 的结构化字段；
- 在执行器中生成更细的执行统计；
- 在工作区检查中输出生成记录摘要；
- CLI `run` 和 `inspect` 输出稳定摘要结构。

优点：
- 最符合 V1 当前“闭环记录 + 服务边界预留”的目标；
- 可直接复用于后续 Django + DRF 响应模型；
- 测试编号和现有未完成项可以清晰回填。

缺点：
- 需要同时调整模型、执行器、资产检查、CLI 和多处测试；
- 本轮工作量大于仅修局部工具层。

### 方案二：只增加测试和规则，不改记录模型
做法：
- 保持现有模型结构；
- 仅在测试和校验层补更多断言。

优点：
- 改动小、风险低。

缺点：
- 不能解决服务输出过于粗糙的问题；
- 无法真正让后续客户端或 DRF 直接消费执行摘要；
- 很可能下一轮还要重做一次。

### 方案三：优先继续拆 `api_test/core/base_api.py`
做法：
- 把时间工具、加密工具、HTTP 客户端继续拆分为更细模块。

优点：
- 能继续降低旧底座耦合。

缺点：
- 与 V1 当前最直接的未完成项并不完全一致；
- 对平台主闭环和资产追溯增强帮助较小；
- 更像底座治理，不是本轮最优先。

## 4. 选型结论
本轮采用**方案一**。

原因：
1. 它直接对应 V1 文档中尚未完成的 P1 测试项；
2. 它能够在不扩张范围的前提下，把 `platform_core` 从“能跑”推进到“可被服务层稳定消费”；
3. 相比继续拆 `BaseAPI`，它更接近平台化主线和 Django + DRF 可承接的接口边界。

## 5. 设计目标

### 5.1 主目标
把当前 `platform_core` 的执行与记录闭环增强为：

> 有结构化生成记录、有结构化执行统计、有可直接输出给服务层/CLI 的稳定摘要

### 5.2 必须达成的结果
1. `GenerationRecord` 能直接表达目标资产摘要和资产归属；
2. `ExecutionRecord` 能表达退出码、执行命令和测试数量统计；
3. `AssetWorkspace.inspect_manifest()` 能返回生成记录检查摘要和缺失情况；
4. CLI `run` 输出包含稳定的执行与生成摘要字段；
5. 当前最小闭环、资产清单与现有回归全部继续通过。

### 5.3 非目标
1. 不新增 Django / DRF 正式接口层；
2. 不引入数据库持久化；
3. 不扩展 V2 的场景编排、变量绑定或抓包驱动实现；
4. 不在本轮继续大拆 `api_test/core/base_api.py`。

## 6. 结构设计

### 6.1 GenerationRecord 增强字段
在保留现有字段的前提下，新增以下字段：
- `module_code`：该生成结果归属的模块编码，便于服务层直接按模块展示；
- `operation_code`：若资产与单接口绑定，则记录接口编码；
- `target_asset_digest`：目标资产文件的内容摘要，避免只在 `asset_manifest` 中出现摘要。

设计约束：
- 这三个字段都允许为空，但一旦存在目标资产文件，就应尽量写实值；
- `target_asset_digest` 采用 SHA256，与 `AssetRecord.content_digest` 保持一致算法。

### 6.2 ExecutionRecord 增强字段
新增以下字段：
- `command`：本次执行的完整 pytest 命令；
- `exit_code`：进程退出码；
- `total_count`：总测试数；
- `passed_count`：通过数；
- `failed_count`：失败数；
- `error_count`：错误数；
- `skipped_count`：跳过数。

设计约束：
- 测试数量优先从 JUnit XML 报告解析，不依赖 stdout 文本；
- 若无法解析报告，则数量字段使用 `0`，但不影响 `result_status` 的原有语义。

### 6.3 生成记录检查摘要
新增 `GenerationInspectionEntry` 模型，用于 `inspect_manifest()` 输出：
- `generation_id`
- `generation_type`
- `target_asset_type`
- `target_asset_path`
- `module_code`
- `operation_code`
- `template_reference`
- `review_status`
- `execution_status`

`AssetInspectionResult` 同步新增：
- `generation_records`
- `missing_generation_records`

这样工作区检查结果不仅能表达“资产是否存在”，还可表达“生成记录是否齐全、指向是否正确”。

### 6.4 服务层与 CLI 输出收口
CLI `run` 输出新增并稳定以下字段：
- `generation_count`
- `asset_count`
- `execution_exit_code`
- `total_count`
- `passed_count`
- `failed_count`
- `error_count`
- `skipped_count`

CLI `inspect` 则继续输出 `AssetInspectionResult`，但现在会包含：
- 资产摘要；
- 生成记录摘要；
- 缺失生成记录列表；
- 现有校验错误与缺失资产信息。

## 7. 实现边界

### 7.1 需要修改的代码
- `platform_core/models.py`
- `platform_core/executors.py`
- `platform_core/assets.py`
- `platform_core/pipeline.py`
- `platform_core/cli.py`

### 7.2 需要补强的测试
- `tests/platform_core/test_models.py`
- `tests/platform_core/test_pipeline.py`
- `tests/platform_core/test_services_and_assets.py`
- 必要时补充 `tests/platform_core/test_templates_and_rules.py`

### 7.3 需要同步更新的文档
- `README.md`
- `product_document/阶段文档/V1阶段工作计划文档.md`
- `product_document/阶段文档/V1实施计划与开发任务拆解说明书.md`
- `product_document/测试文档/详细测试用例说明书(V1).md`
- 如涉及模型说明，再更新 `product_document/架构设计/中间模型设计说明书.md`

## 8. TDD 测试设计

### 8.1 模型层
新增或增强测试，验证：
1. `GenerationRecord` 能保存 `module_code`、`operation_code` 和 `target_asset_digest`；
2. `ExecutionRecord` 能保存 `command`、`exit_code` 和测试数量统计。

### 8.2 执行层
新增测试，验证：
1. `PytestExecutor.run()` 能把执行命令写入记录；
2. 能从 JUnit XML 中得到总数与通过/失败/错误/跳过数；
3. CLI `run` 能输出这些统计字段。

### 8.3 资产检查层
新增测试，验证：
1. `inspect_manifest()` 可返回生成记录摘要；
2. 缺失生成记录文件时会返回 `missing_generation_records`；
3. 原有 `validation_status`、`missing_assets` 和 `digest_mismatches` 语义不被破坏。

## 9. 风险与控制

### 风险 1：记录模型变更导致旧测试或序列化兼容性回归
控制：
- 新字段全部采用向后兼容的可选字段或稳定默认值；
- 先写测试锁定新行为，再补实现。

### 风险 2：执行统计依赖 JUnit XML 结构，解析可能不稳定
控制：
- 以 pytest 自带 `--junitxml` 输出为唯一解析来源；
- 支持 `testsuite` 和 `testsuites` 两种根节点；
- 解析失败时回退为 0，不抛出额外异常。

### 风险 3：服务层输出字段扩展后文档不同步
控制：
- 本轮按 AGENTS 要求，在测试调整、代码调整和验证完成后立即回填 README、V1 阶段文档和测试说明书。

## 10. 验收标准
只有同时满足以下条件，本轮才算完成：
1. `tests/platform_core` 中新增的记录与摘要测试通过；
2. `platform_core` 全量回归通过；
3. `api_test` 全量与公开基线入口回归不被本轮改动破坏；
4. README、V1 阶段文档和测试说明书已同步到本轮真实状态；
5. 当前仓库仍然不能被误判为“V1 全量完成”。

## 11. 结论
本轮不是扩功能，而是继续把 V1 的最小闭环做扎实。

通过增强生成记录、执行记录和工作区检查摘要，`platform_core` 可以从“当前能跑的流水线”进一步收口为“后续服务层可直接复用的稳定输出边界”，这比继续在旧底座工具层做局部整理更符合当前 V1 主线。
