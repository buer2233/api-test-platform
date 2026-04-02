# V1 断言模板与规则覆盖增强设计说明

## 1. 文档信息
- 日期：2026-04-02
- 主题：增强 `platform_core` 的断言模板与断言规则覆盖
- 适用范围：`platform_core/`、`tests/platform_core/`、仓库 README 与 V1 阶段文档
- 关联目标：
  - 补齐 V1 断言模板覆盖缺口
  - 将《模板体系与代码生成规范说明书》中定义但尚未真正落地的 `schema_match` 断言纳入最小闭环
  - 继续降低 AI 辅助生成和文档驱动生成的不稳定性

## 2. 背景与问题
当前 `platform_core` 已经具备：
- `status_code` 断言模板；
- `json_field_exists` 断言模板；
- `json_field_equals` 断言模板；
- 可执行接口的 `status_code` 前置规则。

但文档与实现之间仍存在一个明显缺口：
- 《模板体系与代码生成规范说明书》在 V1 推荐断言模板类型中已经包含 `schema_match`；
- 《中间模型设计说明书》的 `AssertionCandidate` 也已定义 `schema_match`；
- 当前解析器、模板渲染器、规则和测试中却还没有真正落地该断言能力；
- V1 测试说明里仍明确写着“更丰富的断言模板测试（除已落地 `json_field_equals` 外）”。

这意味着当前平台虽然能生成部分断言，但仍未完成“断言模板最小闭环”的文档承诺，也不利于后续把响应结构校验稳定沉淀为平台资产。

## 3. 方案比较

### 方案一：补齐 `schema_match` 最小断言闭环，推荐
做法：
- 在解析器中根据响应结构生成 `schema_match` 断言候选；
- 在模板层新增 `schema_match` 断言模板；
- 在规则层校验 `schema_match` 断言的最小结构；
- 在测试与文档中补齐对应编号和回归结果。

优点：
- 直接补齐当前文档承诺与实现之间的缺口；
- 范围清晰，能在一轮 TDD 中闭环；
- 比继续抽象更复杂的业务断言更稳妥。

缺点：
- 需要为 V1 定义一个“足够简单但可执行”的 schema 断言格式；
- 需要同步更新多处文档和测试。

### 方案二：先继续拆 `api_test/core/base_api.py`
做法：
- 把时间工具、加密工具、随机数据工具继续拆出 `BaseAPI`。

优点：
- 能继续降低旧底座耦合。

缺点：
- 对 V1 主闭环帮助不如断言模板直接；
- 当前文档中关于模板/规则覆盖的缺口依旧存在。

### 方案三：直接引入更复杂的业务规则断言
做法：
- 一次性实现 `business_rule` 断言模板和更复杂的语义校验。

优点：
- 能让断言能力看上去更丰富。

缺点：
- V1 范围容易膨胀；
- 业务规则断言缺乏稳定的结构化输入，不适合作为当前轮最小实现。

## 4. 选型结论
本轮采用**方案一**。

原因：
1. 它直接对应 V1 文档里还未补齐的“断言模板扩展”缺口；
2. 它不需要引入新路线，也不需要扩张到 V2 场景编排；
3. 它能继续增强规则层和模板层的一致性。

## 5. 设计目标

### 5.1 主目标
把当前断言模板能力从：

> `status_code` + `json_field_exists` + `json_field_equals`

增强为：

> `status_code` + `json_field_exists` + `json_field_equals` + `schema_match`

### 5.2 必须达成的结果
1. 解析器能在存在结构化响应对象时生成 `schema_match` 候选；
2. 模板层能渲染 `schema_match` 断言代码；
3. 规则层能识别不合法的 `schema_match` 配置；
4. 最小闭环、模板测试、规则测试和集成测试继续通过。

### 5.3 非目标
1. 不实现复杂 JSON Schema 全量校验器；
2. 不实现 `business_rule` 断言；
3. 不做场景驱动级联断言；
4. 不在本轮继续拆 `BaseAPI`。

## 6. `schema_match` 的最小设计

### 6.1 断言语义
V1 中的 `schema_match` 不追求完整 JSON Schema 兼容，只做最小结构校验：
- 校验目标路径存在；
- 校验目标值的数据类型；
- 若目标值为对象，则校验要求的关键字段是否存在。

### 6.2 `AssertionCandidate.expected_value` 结构
本轮统一使用如下最小结构：

```json
{
  "type": "object",
  "required_fields": ["id", "name"]
}
```

或：

```json
{
  "type": "array"
}
```

约束：
- `type` 为必填；
- `required_fields` 为可选，仅在 `type=object` 时有效；
- 当前只支持 `object` / `array` / `string` / `integer` / `number` / `boolean`。

### 6.3 渲染后的断言行为
以 `target_path="data"` 为例，渲染出的断言逻辑应至少包括：
1. `schema_value = _get_nested_value(body, "data")`
2. 校验 `schema_value` 不为空；
3. 校验 `schema_value` 的 Python 类型符合 `expected_value["type"]`；
4. 若有 `required_fields`，逐个校验字段存在。

### 6.4 解析器生成策略
解析器在以下情况下生成 `schema_match` 候选：
- 若响应字段中存在可断言的对象字段，则优先为第一个对象字段生成 `schema_match`；
- 若响应字段中没有对象字段但存在数组字段，则为第一个数组字段生成 `schema_match`。

对象断言的 `required_fields`：
- 取该对象节点下一层直接子字段名；
- 不递归展开多层 schema；
- 若没有直接子字段，则只保留 `type`。

## 7. 规则设计

### 7.1 新增规则
对 `schema_match` 断言增加最小结构校验：
- `expected_value` 必须是字典；
- 必须存在 `type`；
- `type` 必须在允许集合内；
- 若存在 `required_fields`，必须是字符串列表。

### 7.2 与现有规则的关系
- 现有“可执行接口至少需要一个 `status_code` 断言”规则继续保留；
- `schema_match` 作为补强断言，不替代 `status_code` 的前置要求。

## 8. 测试设计

### 8.1 模板层
新增测试验证：
1. `schema_match` 模板可正确渲染对象结构断言；
2. 能校验 `required_fields`；
3. 生成结果可直接嵌入 pytest 测试骨架。

### 8.2 解析层
新增测试验证：
1. 解析器能从响应对象结构中生成 `schema_match` 候选；
2. `expected_value["type"]` 和 `required_fields` 正确。

### 8.3 规则层
新增测试验证：
1. `schema_match` 缺少 `type` 会被拦截；
2. 非法 `type` 会被拦截；
3. 非法 `required_fields` 会被拦截。

### 8.4 集成层
在现有流水线测试中新增断言：
1. 生成的测试骨架中包含 `schema_match` 断言片段；
2. 文档驱动闭环仍能执行通过。

## 9. 风险与控制

### 风险 1：把 `schema_match` 做成完整 JSON Schema 校验导致范围失控
控制：
- V1 只实现最小类型和关键字段检查；
- 不引入外部复杂 schema 校验库。

### 风险 2：解析器自动生成的 `required_fields` 过深或不稳定
控制：
- 只取对象节点下一层直接字段名；
- 不递归做多层 required 推断。

### 风险 3：文档与实现再次脱节
控制：
- 在本轮代码、测试更新后，立即同步 README、V1 阶段文档与测试说明书。

## 10. 验收标准
只有同时满足以下条件，本轮才算完成：
1. `schema_match` 解析、模板、规则和集成测试全部通过；
2. `tests/platform_core` 全量回归继续通过；
3. `api_test` 全量与公开基线入口未被本轮破坏；
4. README 与 V1 阶段文档已同步到真实状态。

## 11. 结论
本轮是 V1 断言模板体系的补强，而不是新增大功能。

通过把 `schema_match` 纳入最小闭环，平台的模板层、规则层和执行层会更一致，也更符合当前产品和架构文档中已经确认的方向。
