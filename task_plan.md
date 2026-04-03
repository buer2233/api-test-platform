# 当前任务计划

## 目标
- 完成 2026-04-03 的 V1 正式验收复验。
- 对 `jsonplaceholder.typicode.com` 相关用例采用“临时开启代理执行，完成后恢复默认关闭”的验证流程。
- 产出正式验收文档并同步 README、阶段文档、测试文档与本地记录。

## 本轮范围
1. 临时开启 `api_test/api_config.json` 中的代理开关，验证代理连通性与 `jsonplaceholder` 相关用例。
2. 如测试失败则定位并修复；如失败仅来自临时配置偏离默认契约，则恢复默认状态并重跑。
3. 完成 V1 正式验收回归和 `V1阶段正式验收报告.md` 输出。

## 阶段状态
| 阶段 | 状态 | 说明 |
| --- | --- | --- |
| 代理开启与公网冒烟 | 已完成 | 已验证 `127.0.0.1:7890` 可连通，代理请求 JSONPlaceholder 返回 `200 / id=1` |
| `jsonplaceholder` 相关回归 | 已完成 | 代理开启下 `jsonplaceholder` 相关用例为 `12 passed, 27 deselected`，公开基线双入口均为 `12 passed, 27 deselected` |
| 默认配置恢复与非公网回归 | 已完成 | 已恢复 `proxy.enabled=false`，非 `jsonplaceholder` 用例为 `27 passed, 12 deselected`，`test_config_loader.py` 为 `6 passed` |
| V1 验收套件复验 | 已完成 | `tests/platform_core` 为 `63 passed`，根测试为 `70 passed` |
| 文档与正式报告同步 | 已完成 | 已新增正式验收报告，并同步 README、V1 阶段文档、V1 测试文档、`api_test` 文档与本地记录 |

## 风险与注意事项
- `jsonplaceholder` 外网直连仍可能存在时延波动；正式回归优先临时开启代理执行公网用例。
- 仓库默认状态必须保持 `proxy.enabled=false`，否则会破坏配置契约测试。
- `.idea/` 继续忽略，不纳入提交。
