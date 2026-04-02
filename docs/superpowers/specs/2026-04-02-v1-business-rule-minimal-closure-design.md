# V1 `business_rule` 断言最小闭环设计说明

## 1. 文档信息
- 日期：2026-04-02
- 主题：为 `platform_core` 补齐 `business_rule` 断言的最小平台化闭环
- 适用范围：`platform_core/`、`tests/platform_core/`、README 与 V1 阶段文档
- 关联目标：
  - 继续推进 V1 剩余的平台化能力与边界治理
  - 收口 `AssertionCandidate` 中已定义但尚未落地的 `business_rule`
  - 让模板层、规则层和最小执行闭环继续围绕统一中间模型工作

## 2. 背景与问题
当前 `platform_core` 已具备：
1. `status_code`、`json_field_exists`、`json_field_equals`、`schema_match` 断言模板；
2. `schema_match` 的最小规则校验和假响应体构造；
3. 文档驱动最小闭环、服务摘要契约和工作区检查摘要契约。

但当前仍有一个明确缺口：
1. `AssertionCandidate.assertion_type` 已包含 `business_rule`；
2. 中间模型文档和测试文档也已预留 `business_rule`；
3. 模板层、规则层和假响应体构造对 `business_rule` 仍无实际支持；
4. V1 测试文档的 P1 缺口中也明确提到“更复杂的断言模板测试（如 `business_rule`）”。

这意味着当前平台的断言体系仍存在“模型先定义、实现未跟上”的边界裂缝，不利于后续服务层和客户端稳定消费断言资产。

## 3. 方案比较

### 方案一：只把 `business_rule` 当未知断言忽略
做法：
1. 保持 `AssertionCandidate` 枚举不变；
2. 渲染器和规则层继续跳过 `business_rule`；
3. 仅在文档中说明 V1 暂不支持。

优点：
1. 改动最小；
2. 不会扩大实现面。

缺点：
1. 模型与实现持续脱节；
2. 无法满足当前“平台化能力与边界治理”的推进目标；
3. 后续客户端无法判断该断言是否可执行。

### 方案二：一次性实现复杂 DSL 与多类业务规则
做法：
1. 为 `business_rule` 设计通用 DSL；
2. 支持多类比较、布尔组合和跨字段关系；
3. 自动从文档中推断复杂业务规则。

优点：
1. 断言能力看起来更完整。

缺点：
1. 范围明显超出 V1；
2. 规则输入结构、渲染形式和执行语义都会迅速膨胀；
3. 容易把平台底座拖入“半成品规则引擎”。

### 方案三：实现 V1 最小 `business_rule` 闭环，推荐
做法：
1. 仅支持手工构造的 `business_rule` 断言；
2. 仅支持极小范围的规则代码；
3. 先补模板渲染、规则校验与假响应体支撑；
4. 不改解析器自动推导策略。

优点：
1. 直接收口当前模型与实现的边界缺口；
2. 范围足够小，适合一轮 TDD 闭环；
3. 为后续客户端和服务层保留稳定的扩展位。

缺点：
1. 本轮不会让文档驱动自动产出 `business_rule`；
2. 支持的规则语义非常有限。

## 4. 选型结论
本轮采用方案三。

原因：
1. 它优先解决“模型有、实现无”的平台边界问题；
2. 它不把 V1 推向复杂规则引擎；
3. 它符合当前“先稳住底座、再逐步扩展”的改造策略。

## 5. 设计目标

### 5.1 主目标
让 `business_rule` 在 V1 内具备最小可执行闭环：
1. 模板层可渲染；
2. 规则层可校验；
3. pytest 测试骨架可生成满足规则的最小假响应；
4. 文档和测试状态与代码保持一致。

### 5.2 必须达成的结果
1. `TemplateRenderer.render_assertions()` 支持 `business_rule`；
2. `RuleValidator.validate_assertions()` 能识别非法 `business_rule` 配置；
3. 生成测试骨架时，`business_rule` 可参与假响应体构造；
4. `tests/platform_core` 中补齐模板、规则和最小闭环测试；
5. README 和 V1 阶段文档同步更新。

### 5.3 非目标
1. 不新增复杂规则 DSL；
2. 不支持跨字段表达式；
3. 不让 `OpenAPIDocumentParser` 自动生成 `business_rule`；
4. 不在本轮扩展 V2 场景编排或客户端实现。

## 6. `business_rule` 的最小设计

### 6.1 断言语义
本轮只支持一种规则代码：
- `non_empty_string`

目标语义：
- 读取 `target_path` 对应字段值；
- 校验该值是字符串；
- 校验去除首尾空白后不为空。

### 6.2 `expected_value` 结构
本轮统一使用如下最小结构：

```json
{
  "rule_code": "non_empty_string"
}
```

约束：
1. `expected_value` 必须为字典；
2. `rule_code` 为必填；
3. 当前只允许 `non_empty_string`。

说明：
1. 字段路径继续复用 `AssertionCandidate.target_path`；
2. 不新增重复的 `field` 参数，避免结构冗余。

### 6.3 渲染后的断言行为
以 `target_path="data.name"` 为例，渲染出的断言逻辑至少包括：
1. `business_value = _get_nested_value(body, "data.name")`
2. `assert isinstance(business_value, str)`
3. `assert business_value.strip()`

断言消息需明确包含：
1. `business_rule`
2. 规则代码
3. 目标路径

### 6.4 假响应体构造策略
当断言集合包含 `business_rule(non_empty_string)` 时：
1. 若目标路径不存在，则自动补齐一个非空字符串占位值；
2. 占位值格式继续采用现有可读风格，如 `sample-name`；
3. 若同一路径已被 `json_field_equals` 或 `schema_match` 生成更具体值，则不覆盖已有值。

### 6.5 规则校验策略
新增最小校验：
1. `business_rule.expected_value` 必须为字典；
2. `business_rule.rule_code` 必须存在；
3. `business_rule.rule_code` 必须在允许集合中；
4. `business_rule.target_path` 不能为空。

## 7. 结构设计

### 7.1 模板层
新增模板文件：
- `platform_core/templates/assertions/business_rule.py.j2`

`render_assertions()` 增加 `business_rule` 分支，并传入：
1. `target_path`
2. `rule_code`

### 7.2 假响应体构造
在 `TemplateRenderer._build_fake_response_body()` 中追加 `business_rule` 处理分支：
1. 仅对 `non_empty_string` 生效；
2. 使用 `_ensure_nested_value()` 生成占位值；
3. 保持与已有断言生成顺序兼容。

### 7.3 规则层
在 `RuleValidator.validate_assertions()` 中追加 `business_rule` 校验分支，避免非法断言被静默跳过。

## 8. 测试设计

### 8.1 模板层
新增测试验证：
1. `business_rule` 可渲染出稳定断言片段；
2. pytest 测试骨架可生成满足 `non_empty_string` 的假响应。

### 8.2 规则层
新增测试验证：
1. 非法 `expected_value` 会被拦截；
2. 非法 `rule_code` 会被拦截；
3. 违规信息明确指出 `business_rule`。

### 8.3 最小闭环层
新增测试验证：
1. 同一组断言经过模板渲染后可被规则层接受；
2. 生成的测试骨架中同时包含 `business_rule` 断言与匹配的假响应体。

## 9. 风险与控制

### 风险 1：`business_rule` 范围继续膨胀
控制：
1. 本轮仅允许 `non_empty_string`；
2. 不引入 DSL 和跨字段规则。

### 风险 2：假响应体与断言语义不一致
控制：
1. 先写失败测试锁定假响应输出；
2. 生成顺序保持“更具体断言优先”。

### 风险 3：文档再次落后于实现
控制：
1. 代码、测试、README、阶段文档同步更新；
2. 把当前轮验证命令与结果直接回填到 V1 文档。

## 10. 验收标准
只有同时满足以下条件，本轮才算完成：
1. `business_rule` 的模板、规则和最小闭环测试先失败后通过；
2. `tests/platform_core`、根测试、`api_test/tests` 和公开基线回归继续通过；
3. README 与 V1 阶段文档已同步到真实状态；
4. 未引入新的专用站点逻辑或 V2 范围实现。

## 11. 结论
本轮不是扩展高级断言能力，而是继续把 V1 断言边界做实。

通过给 `business_rule` 补齐最小可执行闭环，平台会进一步减少“模型定义先行、实现缺失”的裂缝，也为后续客户端和服务接口保留了稳定、可扩展的断言入口。
