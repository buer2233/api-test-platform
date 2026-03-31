# 当前任务计划

## 目标
- 继续推进 `api_test` 底座治理的未完成内容，保持 V1 范围收敛。
- 收口旧 `PublicAPI`、公开基线执行入口、资产检查输出和 pytest 配置相关风险。
- 完成文档一致性检查，并输出当前已实现功能和测试覆盖说明。

## 阶段状态
| 阶段 | 状态 | 说明 |
| --- | --- | --- |
| 规划记录初始化 | 已完成 | 已创建 `task_plan.md`、`findings.md`、`progress.md` |
| 测试先行与增量实现 | 已完成 | 已补齐 `PublicAPI` 目录治理、公开基线入口、CLI inspect 资产摘要与 pytest 配置收敛 |
| 全量回归验证 | 已完成 | `platform_core` 为 `37 passed`；`api_test` 为 `30 passed, 4 skipped`；公开基线为 `30 passed, 4 deselected` |
| 文档与记录同步 | 已完成 | README、阶段文档、测试文档、计划记录已同步本轮结果 |
| 汇总报告输出 | 进行中 | 输出实现功能、测试覆盖与剩余风险说明 |

## 本轮边界
- 仅继续 `api_test` 底座改造，不扩展到 V2/Web/服务层大范围实现。
- 公共接口测试基线继续以 `https://jsonplaceholder.typicode.com/` 为准。
- 保持 TDD 增量策略，不做一次性推翻式重构。

## 风险与注意事项
- 需确保文档中的测试基线统一为 `api_test: 30 passed, 4 skipped`、`api_test public baseline: 30 passed, 4 deselected`、`platform_core: 37 passed`。
- 私有环境用例仍保留跳过状态，不能误报为完成。
- 旧 `PublicAPI` 虽已有最小操作目录，但仍未完全纳入统一平台中间模型。
