# V1 服务摘要契约收口设计说明

## 1. 文档信息
- 日期：2026-04-02
- 主题：继续收口 `platform_core` 应用服务层与 CLI 之间的稳定摘要契约
- 适用范围：`platform_core/`、`tests/platform_core/`、README 与 V1 阶段文档
- 关联目标：
  - 继续推进 V1 剩余的“产品化接口边界收敛”
  - 让 `PlatformApplicationService` 输出更接近后续 Django + DRF 可承接的稳定结构
  - 降低 CLI 自行拼装响应字典带来的边界漂移风险

## 2. 背景与问题
当前 `platform_core` 已具备：
1. 文档驱动最小闭环；
2. 结构化生成记录与执行记录；
3. 工作区检查与资产摘要输出；
4. CLI `run` / `inspect` 两个稳定入口。

但当前服务层边界仍然存在一个明显问题：
1. `PlatformApplicationService.run_document_pipeline()` 直接返回内部 `PipelineResult`；
2. `platform_core/cli.py` 自己再从 `PipelineResult` 中拼装一个 JSON 字典；
3. `supported_routes()` 只返回简单布尔字典，缺少对“为什么支持/为什么阻断”的稳定表达。

这会带来两个问题：
1. CLI 和未来 DRF 接口都需要重复拼装摘要字段；
2. 应用服务层没有真正形成“可直接给外部入口消费”的稳定输出契约。

## 3. 方案比较

### 方案一：新增服务层稳定摘要模型，并由服务层统一产出，推荐
做法：
1. 在 `platform_core/models.py` 中新增服务摘要模型；
2. `PlatformApplicationService` 提供能力快照和运行摘要方法；
3. CLI `run` 改为直接消费服务层摘要模型；
4. 保持 `inspect_workspace()` 继续返回现有 `AssetInspectionResult`。

优点：
1. 改动范围集中；
2. 不引入新命令和新路线；
3. 更接近未来 DRF 直接返回结构化对象的形态。

缺点：
1. 需要同步更新模型、服务层、CLI 和测试；
2. 需要重新梳理摘要字段命名。

### 方案二：只在 CLI 内部提取一个辅助函数
做法：
1. 不改模型；
2. 只把 CLI 的字典拼装提取到私有函数。

优点：
1. 改动最小。

缺点：
1. 仍然没有把摘要能力收口到服务层；
2. 未来 DRF 层仍然需要重复拼装。

### 方案三：引入通用响应信封和新 `status` 命令
做法：
1. 新增统一响应 envelope；
2. CLI 新增状态查询命令；
3. 服务层统一返回 `status/data/errors` 结构。

优点：
1. 产品化味道更强。

缺点：
1. 会把范围扩大到“新增命令与统一协议”；
2. 当前 V1 不需要这么重的抽象。

## 4. 选型结论
本轮采用方案一。

原因：
1. 它直接解决“服务层没有稳定摘要契约”的问题；
2. 它不扩展 CLI 能力线，只收紧边界；
3. 它与当前文档中“应用服务层 / API 层预留”的方向一致。

## 5. 设计目标

### 5.1 主目标
让当前 `PlatformApplicationService` 额外具备两类稳定输出：
1. **能力快照**：说明 V1 当前开放和阻断的输入路线；
2. **运行摘要**：说明一次文档驱动执行的稳定结果，而不是直接暴露内部流水线细节。

### 5.2 必须达成的结果
1. 新增 `RouteCapabilitySummary` / `ServiceCapabilitySnapshot` 模型；
2. 新增 `DocumentPipelineRunSummary` 模型；
3. `PlatformApplicationService` 提供 `describe_capabilities()`；
4. `PlatformApplicationService` 提供 `run_document_pipeline_summary()`；
5. CLI `run` 直接输出服务层摘要模型，而不是自行拼字典；
6. 现有 `inspect` 与最小闭环测试不被破坏。

### 5.3 非目标
1. 不新增 `status` CLI 命令；
2. 不引入 DRF、数据库或 Web 接口实现；
3. 不扩展功能用例驱动与抓包驱动；
4. 不改变 `inspect_workspace()` 现有核心语义。

## 6. 结构设计

### 6.1 路线能力摘要模型
新增 `RouteCapabilitySummary`：
- `route_code`
- `enabled`
- `stage`
- `detail`

新增 `ServiceCapabilitySnapshot`：
- `service_stage`
- `local_mode_only`
- `available_commands`
- `routes`

设计意图：
1. 让外部入口不只知道布尔值，还知道当前阶段为何阻断；
2. 后续 DRF / 客户端可直接消费，不需要再次写映射表。

### 6.2 文档驱动运行摘要模型
新增 `DocumentPipelineRunSummary`：
- `route_code`
- `service_stage`
- `source`
- `source_id`
- `workspace_root`
- `modules`
- `operations`
- `generation_count`
- `asset_count`
- `execution_target`
- `execution_status`
- `execution_exit_code`
- `total_count`
- `passed_count`
- `failed_count`
- `error_count`
- `skipped_count`
- `report_path`
- `asset_manifest_path`

设计意图：
1. 对外暴露“这次运行的稳定结果”；
2. 不把 CLI 绑定到 `PipelineResult` 的内部结构上。

### 6.3 服务层职责调整
`PlatformApplicationService` 调整为：
1. `run_document_pipeline()`：保留，继续返回底层 `PipelineResult`，供内部调用和已有测试使用；
2. `build_document_pipeline_summary()`：把 `PipelineResult` 转成 `DocumentPipelineRunSummary`；
3. `run_document_pipeline_summary()`：执行闭环并直接返回摘要模型；
4. `describe_capabilities()`：返回 `ServiceCapabilitySnapshot`。

说明：
1. 保留原方法是为了避免扩大破坏面；
2. 新摘要方法面向未来服务接口边界。

### 6.4 CLI 边界
CLI `run` 调整为：
1. 调用 `run_document_pipeline_summary()`；
2. 直接输出摘要模型的 `model_dump(mode="json")`；
3. 返回码仍依据 `execution_status` 保持原语义。

CLI `inspect` 保持现状：
1. 继续输出 `AssetInspectionResult`；
2. 暂不再引入新的包装层。

## 7. 测试设计

### 7.1 模型层
新增测试验证：
1. `RouteCapabilitySummary` 能表达阻断原因；
2. `DocumentPipelineRunSummary` 能表达运行摘要字段。

### 7.2 服务层
新增测试验证：
1. `describe_capabilities()` 返回完整能力快照；
2. `run_document_pipeline_summary()` 返回稳定摘要；
3. `supported_routes()` 旧行为仍兼容。

### 7.3 CLI 层
新增或增强测试验证：
1. CLI `run` 输出包含 `route_code`、`service_stage`、`workspace_root`；
2. CLI `run` 输出仍保留原有计数字段；
3. CLI 返回码语义保持不变。

## 8. 风险与控制

### 风险 1：服务层与 CLI 字段名漂移
控制：
1. 摘要模型集中定义字段；
2. CLI 只做 `model_dump`，不再手写字典。

### 风险 2：现有测试或调用方被破坏
控制：
1. 保留 `run_document_pipeline()` 的原始返回值语义；
2. 新增摘要方法而不是直接替换底层接口。

## 9. 验收标准
只有同时满足以下条件，本轮才算完成：
1. 新增服务摘要模型测试先失败后通过；
2. `PlatformApplicationService` 能返回稳定能力快照和运行摘要；
3. CLI `run` 已不再手工拼接摘要字典；
4. `tests/platform_core`、根测试、`api_test/tests` 和公开基线回归继续通过；
5. README 与 V1 阶段文档已同步更新。

## 10. 结论
本轮不是做新能力，而是继续把 `platform_core` 的服务边界做实。

通过把“能力快照”和“运行摘要”正式收口到应用服务层，当前 V1 会更接近后续 Django + DRF 可直接承接的接口形态，同时也能减少 CLI 和未来其他入口重复拼装响应的成本。
