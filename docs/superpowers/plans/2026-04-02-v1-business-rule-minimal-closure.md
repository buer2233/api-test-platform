# V1 `business_rule` 断言最小闭环 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为 `platform_core` 补齐 `business_rule(non_empty_string)` 的模板渲染、规则校验和最小假响应支撑，继续收口 V1 断言平台化边界。

**Architecture:** 本轮只实现手工构造断言可执行的最小闭环，不改解析器自动推导，不做复杂规则 DSL。按 TDD 顺序先补失败测试，再补最小实现，最后同步 README、阶段文档和测试文档。

**Tech Stack:** Python 3.12、pytest、pydantic、Jinja2、Markdown、Git

---

## File Map

### Create
- `docs/superpowers/specs/2026-04-02-v1-business-rule-minimal-closure-design.md`
- `docs/superpowers/plans/2026-04-02-v1-business-rule-minimal-closure.md`
- `platform_core/templates/assertions/business_rule.py.j2`

### Modify
- `platform_core/renderers.py`
- `platform_core/rules.py`
- `tests/platform_core/test_templates_and_rules.py`
- `tests/platform_core/test_services_and_assets.py`
- `README.md`
- `product_document/架构设计/中间模型设计说明书.md`
- `product_document/架构设计/模板体系与代码生成规范说明书.md`
- `product_document/阶段文档/V1阶段工作计划文档.md`
- `product_document/阶段文档/V1实施计划与开发任务拆解说明书.md`
- `product_document/测试文档/详细测试用例说明书(V1).md`

---

### Task 1：锁定 `business_rule` 模板失败测试

**Files:**
- Modify: `tests/platform_core/test_templates_and_rules.py`
- Create: `platform_core/templates/assertions/business_rule.py.j2`
- Modify: `platform_core/renderers.py`

- [ ] **Step 1: 写失败测试**

```python
def test_assertion_template_renders_business_rule():
    renderer = TemplateRenderer()
    assertions = [
        AssertionCandidate(
            assertion_id="assert-business-001",
            operation_id="op-get-user",
            assertion_type="business_rule",
            target_path="data.name",
            expected_value={"rule_code": "non_empty_string"},
            priority="medium",
            source="manual",
            confidence_score=0.8,
            review_status="pending",
        )
    ]

    rendered = renderer.render_assertions(assertions)

    assert 'business_value = _get_nested_value(body, "data.name")' in rendered
    assert 'assert isinstance(business_value, str)' in rendered
    assert 'assert business_value.strip()' in rendered
```

- [ ] **Step 2: 运行测试确认失败**

Run: `python -m pytest tests/platform_core/test_templates_and_rules.py -k "business_rule" -v --basetemp .pytest_tmp/business_rule_template_red`

Expected: FAIL，提示 `business_rule` 尚未渲染。

- [ ] **Step 3: 写最小实现**

```python
# platform_core/renderers.py
elif assertion.assertion_type == "business_rule":
    expected_value = assertion.expected_value if isinstance(assertion.expected_value, dict) else {}
    template_name = "assertions/business_rule.py.j2"
    context = {
        "target_path": assertion.target_path,
        "rule_code": expected_value.get("rule_code", ""),
    }
```

```python
# platform_core/templates/assertions/business_rule.py.j2
business_value = _get_nested_value(body, "{{ target_path }}")
assert isinstance(business_value, str), (
    "business_rule 断言失败: 规则 {{ rule_code }} 要求路径 {{ target_path }} 的值必须为字符串"
)
assert business_value.strip(), (
    "business_rule 断言失败: 规则 {{ rule_code }} 要求路径 {{ target_path }} 的值不能为空字符串"
)
```

- [ ] **Step 4: 运行测试确认通过**

Run: `python -m pytest tests/platform_core/test_templates_and_rules.py -k "business_rule" -v --basetemp .pytest_tmp/business_rule_template_green`

Expected: PASS。

### Task 2：锁定 `business_rule` 规则与假响应失败测试

**Files:**
- Modify: `tests/platform_core/test_templates_and_rules.py`
- Modify: `tests/platform_core/test_services_and_assets.py`
- Modify: `platform_core/rules.py`
- Modify: `platform_core/renderers.py`

- [ ] **Step 1: 写失败测试**

```python
def test_pytest_template_builds_fake_response_for_business_rule_assertions():
    renderer = TemplateRenderer()
    assertions = [
        AssertionCandidate(
            assertion_id="assert-status-001",
            operation_id="op-get-user",
            assertion_type="status_code",
            target_path="status_code",
            expected_value=200,
            priority="high",
            source="manual",
            confidence_score=1.0,
            review_status="pending",
        ),
        AssertionCandidate(
            assertion_id="assert-business-001",
            operation_id="op-get-user",
            assertion_type="business_rule",
            target_path="data.name",
            expected_value={"rule_code": "non_empty_string"},
            priority="medium",
            source="manual",
            confidence_score=0.8,
            review_status="pending",
        ),
    ]

    rendered = renderer.render_test_module(build_module(), build_operation(), assertions)

    assert '"name": "sample-name"' in rendered


def test_rule_validator_rejects_invalid_business_rule_assertion():
    validator = RuleValidator()
    assertions = [
        AssertionCandidate(
            assertion_id="assert-business-001",
            operation_id="op-get-user",
            assertion_type="business_rule",
            target_path="data.name",
            expected_value={"rule_code": "unsupported"},
            priority="medium",
            source="manual",
            confidence_score=0.8,
            review_status="pending",
        ),
        AssertionCandidate(
            assertion_id="assert-status-001",
            operation_id="op-get-user",
            assertion_type="status_code",
            target_path="status_code",
            expected_value=200,
            priority="high",
            source="manual",
            confidence_score=1.0,
            review_status="pending",
        ),
    ]

    violations = validator.validate_assertions(build_operation(), assertions)

    assert any("business_rule" in violation for violation in violations)
```

- [ ] **Step 2: 运行测试确认失败**

Run: `python -m pytest tests/platform_core/test_templates_and_rules.py tests/platform_core/test_services_and_assets.py -k "business_rule" -v --basetemp .pytest_tmp/business_rule_rule_red`

Expected: FAIL，提示规则或假响应尚未支持。

- [ ] **Step 3: 写最小实现**

```python
# platform_core/renderers.py
for assertion in assertions:
    if assertion.assertion_type != "business_rule":
        continue
    expected_value = assertion.expected_value if isinstance(assertion.expected_value, dict) else {}
    if expected_value.get("rule_code") == "non_empty_string":
        self._ensure_nested_value(
            body,
            assertion.target_path,
            self._build_path_placeholder(assertion.target_path),
        )
```

```python
# platform_core/rules.py
if assertion.assertion_type == "business_rule":
    if not isinstance(assertion.expected_value, dict):
        violations.append("business_rule.expected_value 必须为字典")
        continue
    rule_code = assertion.expected_value.get("rule_code")
    if not isinstance(rule_code, str) or not rule_code:
        violations.append("business_rule.rule_code 不能为空")
    elif rule_code not in {"non_empty_string"}:
        violations.append("business_rule.rule_code 非法或暂不支持")
```

- [ ] **Step 4: 运行测试确认通过**

Run: `python -m pytest tests/platform_core/test_templates_and_rules.py tests/platform_core/test_services_and_assets.py -k "business_rule" -v --basetemp .pytest_tmp/business_rule_rule_green`

Expected: PASS。

### Task 3：执行 `platform_core` 回归并同步文档

**Files:**
- Modify: `README.md`
- Modify: `product_document/架构设计/中间模型设计说明书.md`
- Modify: `product_document/架构设计/模板体系与代码生成规范说明书.md`
- Modify: `product_document/阶段文档/V1阶段工作计划文档.md`
- Modify: `product_document/阶段文档/V1实施计划与开发任务拆解说明书.md`
- Modify: `product_document/测试文档/详细测试用例说明书(V1).md`

- [ ] **Step 1: 执行平台核心回归**

Run:
- `python -m pytest tests/platform_core -v --basetemp .pytest_tmp/platform_core_business_rule_full`
- `python -m pytest tests -v --basetemp .pytest_tmp/root_business_rule_full`

Expected: PASS。

- [ ] **Step 2: 同步 README 与阶段文档**

```markdown
- README：补记 `business_rule(non_empty_string)` 已完成最小闭环和当前轮验证结果。
- 中间模型设计说明书：把 `business_rule` 从“仅枚举预留”更新为“V1 当前已落地最小语义”。
- 模板体系与代码生成规范说明书：补充 `business_rule` 的最小输入结构与模板约束。
- V1 阶段工作计划文档 / 实施计划文档：回填本轮 TDD 编号、验证命令和通过结果。
- 详细测试用例说明书（V1）：补充 `business_rule` 模板测试、规则测试和 P1 缺口状态。
```

- [ ] **Step 3: 执行 `api_test` 与公开基线回归**

Run:
- `python -m pytest api_test/tests -v --basetemp .pytest_tmp/api_test_business_rule_full`
- `python api_test/run_test.py --public-baseline`
- `cd api_test && python run_test.py --public-baseline`

Expected: PASS；若出现外网时延波动，按既有规则记录为站点风险，不误判为本轮逻辑错误。

- [ ] **Step 4: 提交并推送**

```bash
git add platform_core/renderers.py platform_core/rules.py platform_core/templates/assertions/business_rule.py.j2 tests/platform_core/test_templates_and_rules.py tests/platform_core/test_services_and_assets.py README.md product_document/架构设计/中间模型设计说明书.md product_document/架构设计/模板体系与代码生成规范说明书.md product_document/阶段文档/V1阶段工作计划文档.md product_document/阶段文档/V1实施计划与开发任务拆解说明书.md product_document/测试文档/详细测试用例说明书(V1).md docs/superpowers/specs/2026-04-02-v1-business-rule-minimal-closure-design.md docs/superpowers/plans/2026-04-02-v1-business-rule-minimal-closure.md
git commit -m "重构：补齐business_rule断言最小闭环并同步V1文档"
git push origin main
```
