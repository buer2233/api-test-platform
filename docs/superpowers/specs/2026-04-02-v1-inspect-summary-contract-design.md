# V1 工作区检查摘要契约收口设计说明

## 1. 文档信息
- 日期：2026-04-02
- 主题：继续收口 `platform_core` 的工作区检查服务边界与 CLI `inspect` 输出契约
- 适用范围：`platform_core/`、`tests/platform_core/`、README 与 V1 阶段文档
- 关联目标：
  - 继续推进 V1 剩余的“资产管理边界与更多服务输出收敛”
  - 让 `PlatformApplicationService.inspect_workspace()` 的对外结果更接近后续 Django + DRF 可承接的稳定结构
  - 降低 CLI `inspect` 直接暴露资产层检查结果带来的边界漂移风险

## 2. 背景与问题
当前 `platform_core` 已具备：
1. 资产清单落盘与工作区检查；
2. 资产摘要、生成记录摘要、缺失记录与 digest 不一致检查；
3. `PlatformApplicationService.inspect_workspace()`；
4. CLI `inspect` 入口。

但当前边界仍有一个明显缺口：
1. `inspect_workspace()` 直接返回资产层的 `AssetInspectionResult`；
2. CLI `inspect` 直接输出该模型，没有服务层稳定摘要过渡层；
3. `run` 已经完成服务摘要收口，`inspect` 仍停留在“直接暴露底层结果”的状态。

这会带来两个问题：
1. 后续若接入 Django + DRF，服务接口仍需要重新组织 `inspect` 输出；
2. 资产层字段扩展会直接影响 CLI 与未来外部入口，边界不够稳定。

## 3. 方案比较

### 方案一：新增工作区检查服务摘要模型，并由服务层统一产出，推荐
做法：
1. 在 `platform_core/models.py` 中新增工作区检查服务摘要模型；
2. `PlatformApplicationService` 提供构建摘要和直接返回摘要的方法；
3. CLI `inspect` 改为直接消费服务层摘要模型；
4. 保留 `inspect_workspace()` 继续返回 `AssetInspectionResult`，避免扩大破坏面。

优点：
1. 与上一轮 `run` 服务摘要收口方式一致；
2. 不需要重写资产层，只新增服务层收口层；
3. 更接近后续 Web / Desktop 统一消费结构化摘要的形态。

缺点：
1. 需要同步更新模型、服务层、CLI、测试和文档；
2. 会与 `AssetInspectionResult` 存在部分字段重复。

### 方案二：继续沿用 `AssetInspectionResult`
做法：
1. 不新增模型；
2. 继续让 CLI `inspect` 直接输出资产层检查结果。

优点：
1. 改动最小。

缺点：
1. 服务层与资产层边界依旧没有收口；
2. 与 `run` 已服务化的方向不一致。

### 方案三：同时引入统一响应信封
做法：
1. 为 `run` 和 `inspect` 一起引入 envelope；
2. 所有 CLI / 服务层输出改为 `status/data/errors`。

优点：
1. 产品化风格更完整。

缺点：
1. 范围明显膨胀；
2. 当前 V1 不需要这么重的抽象。

## 4. 选型结论
本轮采用方案一。

原因：
1. 它直接命中当前“资产管理边界与更多服务输出收敛”的剩余主线；
2. 它延续上一轮 `run` 摘要契约的设计风格，降低体系不一致；
3. 它不扩展新路线、不引入统一信封，范围可控。

## 5. 设计目标

### 5.1 主目标
让当前 `PlatformApplicationService` 额外具备工作区检查的稳定服务摘要输出，而不是直接把资产层结果暴露给 CLI 与未来服务接口。

### 5.2 必须达成的结果
1. 新增 `WorkspaceInspectionSummary` 模型；
2. `PlatformApplicationService` 提供 `build_workspace_inspection_summary()`；
3. `PlatformApplicationService` 提供 `inspect_workspace_summary()`；
4. CLI `inspect` 直接输出服务层摘要模型；
5. 保留 `inspect_workspace()` 原始行为，兼容现有资产层测试；
6. 现有 `run` 摘要契约与公开基线测试不被破坏。

### 5.3 非目标
1. 不新增新的 CLI 命令；
2. 不引入统一 envelope；
3. 不扩展功能用例驱动与抓包驱动；
4. 不重写 `AssetWorkspace.inspect_manifest()` 核心逻辑。

## 6. 结构设计

### 6.1 工作区检查服务摘要模型
新增 `WorkspaceInspectionSummary`：
- `command_code`
- `service_stage`
- `workspace_root`
- `manifest_path`
- `source_id`
- `validation_status`
- `asset_count`
- `generation_count`
- `report_path`
- `report_exists`
- `missing_asset_count`
- `missing_generation_record_count`
- `digest_mismatch_count`
- `validation_error_count`
- `assets`
- `generation_records`
- `missing_assets`
- `missing_generation_records`
- `digest_mismatches`
- `validation_errors`

设计意图：
1. 让外部入口获得稳定的服务层输出；
2. 保留资产与生成记录摘要列表，便于后续 Web / Desktop 直接展示；
3. 新增问题数量字段，方便前端或服务接口直接做概览展示，而不是自己再统计。

### 6.2 服务层职责调整
`PlatformApplicationService` 调整为：
1. `inspect_workspace()`：保留，继续返回底层 `AssetInspectionResult`；
2. `build_workspace_inspection_summary()`：把 `AssetInspectionResult` 转成 `WorkspaceInspectionSummary`；
3. `inspect_workspace_summary()`：直接执行检查并返回服务层摘要模型。

说明：
1. 保留原方法是为了兼容既有测试与内部调用；
2. 新摘要方法面向未来服务接口边界。

### 6.3 CLI 边界
CLI `inspect` 调整为：
1. 调用 `inspect_workspace_summary()`；
2. 直接输出摘要模型的 `model_dump(mode="json")`；
3. 返回码仍依据 `validation_status` 保持原语义。

## 7. 测试设计

### 7.1 模型层
新增测试验证：
1. `WorkspaceInspectionSummary` 能表达服务阶段、问题数量与摘要列表。

### 7.2 服务层
新增测试验证：
1. `inspect_workspace_summary()` 返回稳定摘要；
2. 服务摘要中的问题数量与底层检查结果一致；
3. `inspect_workspace()` 原始行为仍兼容。

### 7.3 CLI 层
新增或增强测试验证：
1. CLI `inspect` 输出包含 `command_code`、`service_stage`；
2. CLI `inspect` 输出包含问题数量字段；
3. CLI 返回码语义保持不变。

## 8. 风险与控制

### 风险 1：服务摘要与资产层结果字段不一致
控制：
1. 由服务层统一构建摘要；
2. 摘要中的统计字段全部基于 `AssetInspectionResult` 计算，不在 CLI 重复统计。

### 风险 2：CLI `inspect` 现有测试被破坏
控制：
1. 先写失败测试锁定新增字段；
2. 保留现有 `assets` / `generation_records` 等核心输出，避免无意义破坏。

## 9. 验收标准
只有同时满足以下条件，本轮才算完成：
1. 新增工作区检查摘要模型测试先失败后通过；
2. `PlatformApplicationService` 能返回稳定的工作区检查摘要；
3. CLI `inspect` 已改为直接消费服务层摘要；
4. `tests/platform_core`、根测试、`api_test/tests` 和公开基线回归继续通过；
5. README 与 V1 阶段文档已同步更新。

## 10. 结论
本轮仍然不是做新路线，而是继续把 V1 当前已有能力的服务边界做实。

通过把工作区检查结果正式收口到服务层稳定摘要，`platform_core` 会从“当前能检查、能输出”的状态，进一步收口为“后续 Django + DRF / 客户端可直接消费的资产管理接口形态”。
