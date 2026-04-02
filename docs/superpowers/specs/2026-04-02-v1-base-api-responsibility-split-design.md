# V1 BaseAPI 职责收口设计说明

## 1. 文档信息
- 日期：2026-04-02
- 主题：继续拆分 `api_test/core/base_api.py` 的非 HTTP 工具职责
- 适用范围：`api_test/core/`、`api_test/tests/`、README 与 V1 阶段文档
- 关联目标：
  - 让 `BaseAPI` 真正收口为通用 HTTP 客户端
  - 把通用工具能力迁移到独立模块，降低请求层耦合
  - 继续推进 V1 “通用框架底座治理”主线

## 2. 背景与问题
当前仓库的文档和 README 已明确要求：

> `BaseAPI` 只保留通用 HTTP 能力。

但代码现状仍然存在偏差，`api_test/core/base_api.py` 中除了请求方法外，还保留了：
1. 嵌套取值工具；
2. 时间转换工具；
3. 哈希和 AES 加解密工具；
4. 随机字符串、手机号、邮箱生成工具。

这些能力虽然是通用工具，但不应继续挂载在 HTTP 客户端类上，否则会带来以下问题：
1. 请求层边界仍然不清晰；
2. 后续模板生成会误把工具函数视为接口客户端职责；
3. `BaseAPI` 文档与实际实现不一致；
4. 对后续服务层、客户端和平台化接口边界收口不利。

## 3. 方案比较

### 方案一：新增单一工具模块 `common_tools.py`，推荐
做法：
1. 新增 `api_test/core/common_tools.py`；
2. 以纯函数形式承接原 `BaseAPI` 的通用工具方法；
3. `BaseAPI` 仅保留请求和状态码规范化能力；
4. 通过测试锁定“工具功能保留、HTTP 客户端收口”的目标。

优点：
1. 改动面最小，适合 V1 当前增量治理；
2. 工具职责集中，迁移简单；
3. 便于后续继续按类别再细拆，而不是一次性过度设计。

缺点：
1. 工具模块内部仍会同时容纳多类工具；
2. 后续若工具继续增多，仍需二次拆分。

### 方案二：一次性拆成多个工具模块
做法：
1. 新增 `crypto_tools.py`、`time_tools.py`、`data_tools.py` 等多个模块；
2. 按类别彻底拆散原有方法。

优点：
1. 边界最清晰；
2. 长期结构更优雅。

缺点：
1. 当前影响面小，却会引入更多文件和导出边界；
2. 容易把本轮范围从“职责收口”扩大成“工具层重构”。

### 方案三：保留 `BaseAPI` 上的兼容代理方法
做法：
1. 新建工具模块；
2. `BaseAPI` 中保留同名包装方法，内部转调工具函数。

优点：
1. 迁移最平滑。

缺点：
1. `BaseAPI` 边界并未真正收口；
2. 会继续让使用者误以为这些能力属于请求客户端；
3. 与当前文档目标冲突。

## 4. 选型结论
本轮采用方案一。

原因：
1. 它能直接满足 V1 当前“让 `BaseAPI` 变成纯 HTTP 客户端”的要求；
2. 它保持增量改造，不会把本轮任务放大；
3. 它为未来继续细拆工具层保留空间，但不在当前轮过度设计。

## 5. 设计目标

### 5.1 主目标
完成以下状态收敛：
1. `BaseAPI` 只保留：
   - `__init__`
   - `request`
   - `_normalize_expected_status`
   - `get/post/put/patch/delete`
2. 原工具方法迁移到 `core.common_tools`；
3. 工具原有行为通过测试锁定，不因迁移发生语义回归；
4. README、架构文档、V1 阶段文档与测试文档同步为真实状态。

### 5.2 非目标
1. 不新增新的 HTTP 能力；
2. 不改变 `session.py` 的代理或重试逻辑；
3. 不在本轮继续扩展 `platform_core` 断言类型；
4. 不引入新的第三方依赖。

## 6. 最小结构设计

### 6.1 `BaseAPI`
`BaseAPI` 应只承担：
1. 读取唯一配置源中的运行时配置；
2. 构建请求会话；
3. 发送请求并校验状态码；
4. 提供常见 HTTP 方法快捷调用。

### 6.2 `common_tools.py`
新模块采用纯函数方式承接以下能力：
1. `get_value`
2. `time_to_stamp`
3. `stamp_to_time`
4. `get_week_info`
5. `get_month_info`
6. `md5_encrypt`
7. `sha1_encrypt`
8. `aes_ecb_encrypt`
9. `aes_ecb_decrypt`
10. `aes_cbc_encrypt`
11. `aes_cbc_decrypt`
12. `generate_random_string`
13. `generate_phone_number`
14. `generate_email`

说明：
1. 保持原有函数名，降低迁移成本；
2. `generate_email` 内部改为直接调用同模块函数，不再依赖 `BaseAPI`。

## 7. 测试设计

### 7.1 治理测试
在 `api_test/tests/test_base_api_governance.py` 中新增或增强测试，锁定：
1. `BaseAPI` 不再暴露上述工具方法；
2. 仍然保留请求相关能力与现有代理行为。

### 7.2 工具回归测试
新增 `api_test/tests/test_common_tools.py`，至少覆盖：
1. 嵌套路径取值成功与失败；
2. 时间戳转换；
3. 周/月范围计算；
4. MD5、SHA1 与 AES 加解密；
5. 随机字符串长度；
6. 手机号和邮箱格式。

### 7.3 回归范围
本轮至少执行：
1. `api_test/tests/test_base_api_governance.py`
2. `api_test/tests/test_common_tools.py`
3. `api_test/tests` 全量
4. `tests/platform_core` 全量
5. 根 `tests` 全量
6. `api_test/run_test.py --public-baseline`

## 8. 风险与控制

### 风险 1：工具迁移后产生隐藏引用断裂
控制：
1. 先用检索确认当前无外部调用；
2. 通过新增工具测试和 `api_test/tests` 全量回归拦截。

### 风险 2：文档描述继续与代码脱节
控制：
1. 本轮代码改动后立即同步 README、架构文档、阶段文档和测试文档；
2. 在阶段文档中把该项从“剩余风险”转为“已完成的治理项”。

## 9. 验收标准
只有同时满足以下条件，本轮才算完成：
1. 新增治理测试先失败后通过；
2. `BaseAPI` 中不再保留非 HTTP 工具方法；
3. 新工具模块测试通过；
4. `api_test/tests`、`tests/platform_core`、根 `tests` 和公开基线回归通过；
5. 文档与测试结果已同步更新。

## 10. 结论
本轮不是做新的功能扩张，而是继续把通用测试底座的职责边界做实。

通过把非 HTTP 工具从 `BaseAPI` 中移出，当前框架会更符合“通用 HTTP 客户端 + 独立工具层”的平台化底座方向，也更适合作为后续中间模型、模板生成和服务层接口的稳定承接点。
