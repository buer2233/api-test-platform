# V1 断言模板与规则覆盖增强 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 为 `platform_core` 补齐 `schema_match` 断言模板、断言候选生成与规则校验，继续增强 V1 文档驱动最小闭环的断言覆盖。

**Architecture:** 本轮只围绕断言模板与规则覆盖推进，不扩展 V2 路线，也不继续拆 `api_test` 底座。实现顺序采用 TDD：先锁定解析器、模板层、规则层和流水线的失败测试，再补最小实现，最后同步 README 与 V1 阶段文档。

**Tech Stack:** Python 3.12, pytest, pydantic, Jinja2, Markdown, Git

---

## File Map

### Modify
- `platform_core/parsers.py`
- `platform_core/renderers.py`
- `platform_core/rules.py`
- `platform_core/templates/assertions/schema_match.py.j2`
- `tests/platform_core/test_templates_and_rules.py`
- `tests/platform_core/test_services_and_assets.py`
- `tests/platform_core/test_pipeline.py`
- `README.md`
- `product_document/架构设计/模板体系与代码生成规范说明书.md`
- `product_document/阶段文档/V1阶段工作计划文档.md`
- `product_document/阶段文档/V1实施计划与开发任务拆解说明书.md`
- `product_document/测试文档/详细测试用例说明书(V1).md`

### Create
- `platform_core/templates/assertions/schema_match.py.j2`

---

### Task 1: 先锁定 `schema_match` 解析与模板失败测试

**Files:**
- Modify: `tests/platform_core/test_services_and_assets.py`
- Modify: `tests/platform_core/test_templates_and_rules.py`

- [x] **Step 1: 写失败测试**

```python
def test_parser_creates_schema_match_assertion_from_object_response(tmp_path):
    ...
    schema_assertions = [a for a in parsed.assertions if a.assertion_type == "schema_match"]
    assert len(schema_assertions) == 1
    assert schema_assertions[0].target_path == "data"
    assert schema_assertions[0].expected_value["type"] == "object"
    assert schema_assertions[0].expected_value["required_fields"] == ["id", "name"]


def test_assertion_template_renders_schema_match():
    renderer = TemplateRenderer()
    assertions = [
        AssertionCandidate(
            assertion_id="assert-schema-001",
            operation_id="op-get-user",
            assertion_type="schema_match",
            target_path="data",
            expected_value={"type": "object", "required_fields": ["id", "name"]},
            priority="medium",
            source="openapi",
            confidence_score=0.8,
            review_status="pending",
        )
    ]
    rendered = renderer.render_assertions(assertions)
    assert 'assert isinstance(schema_value, dict)' in rendered
    assert 'for required_field in ["id", "name"]' in rendered
```

- [x] **Step 2: 运行测试确认失败**

Run: `python -m pytest tests/platform_core/test_templates_and_rules.py tests/platform_core/test_services_and_assets.py -v --basetemp .pytest_tmp/assertion_template_fail`

Expected: 失败，因为当前解析器与模板层尚未支持 `schema_match`。

- [x] **Step 3: 写最小实现**

```python
# platform_core/parsers.py
if object_field:
    assertions.append(
        AssertionCandidate(
            assertion_id=f"{operation.operation_id}-schema-match",
            operation_id=operation.operation_id,
            assertion_type="schema_match",
            target_path=object_field.field_path,
            expected_value={"type": "object", "required_fields": child_fields},
            ...
        )
    )
```

```python
# platform_core/renderers.py
elif assertion.assertion_type == "schema_match":
    template_name = "assertions/schema_match.py.j2"
    context = {
        "target_path": assertion.target_path,
        "expected_value": assertion.expected_value,
    }
```

- [x] **Step 4: 运行测试确认通过**

Run: `python -m pytest tests/platform_core/test_templates_and_rules.py tests/platform_core/test_services_and_assets.py -v --basetemp .pytest_tmp/assertion_template_pass`

Expected: PASS。

- [ ] **Step 5: 提交**

```bash
git add platform_core/parsers.py platform_core/renderers.py platform_core/templates/assertions/schema_match.py.j2 tests/platform_core/test_templates_and_rules.py tests/platform_core/test_services_and_assets.py
git commit -m "重构：补齐 schema_match 断言模板与断言候选生成"
```

### Task 2: 锁定 `schema_match` 规则与闭环失败测试

**Files:**
- Modify: `platform_core/rules.py`
- Modify: `tests/platform_core/test_services_and_assets.py`
- Modify: `tests/platform_core/test_pipeline.py`

- [x] **Step 1: 写失败测试**

```python
def test_rule_validator_rejects_invalid_schema_match_assertion():
    validator = RuleValidator()
    operation = build_operation()
    assertions = [
        AssertionCandidate(
            assertion_id="assert-schema-001",
            operation_id="op-get-user",
            assertion_type="schema_match",
            target_path="data",
            expected_value={"required_fields": ["id"]},
            priority="medium",
            source="openapi",
            confidence_score=0.7,
            review_status="pending",
        )
    ]
    violations = validator.validate_assertions(operation, assertions)
    assert any("schema_match" in violation for violation in violations)


def test_document_driven_pipeline_renders_schema_match_assertion_into_generated_test(tmp_path):
    ...
    generated_test = (output_root / "generated" / "tests" / "test_get_user_profile.py").read_text(encoding="utf-8")
    assert "schema_value = _get_nested_value(body, \"data\")" in generated_test
```

- [x] **Step 2: 运行测试确认失败**

Run: `python -m pytest tests/platform_core/test_services_and_assets.py tests/platform_core/test_pipeline.py -v --basetemp .pytest_tmp/schema_rule_fail`

Expected: 失败，因为规则层尚未校验 `schema_match` 结构。

- [x] **Step 3: 写最小实现**

```python
if assertion.assertion_type == "schema_match":
    if not isinstance(assertion.expected_value, dict):
        violations.append("schema_match.expected_value 必须为字典")
    elif assertion.expected_value.get("type") not in {"object", "array", "string", "integer", "number", "boolean"}:
        violations.append("schema_match.type 非法")
```

- [x] **Step 4: 运行测试确认通过**

Run: `python -m pytest tests/platform_core/test_services_and_assets.py tests/platform_core/test_pipeline.py -v --basetemp .pytest_tmp/schema_rule_pass`

Expected: PASS。

- [ ] **Step 5: 提交**

```bash
git add platform_core/rules.py tests/platform_core/test_services_and_assets.py tests/platform_core/test_pipeline.py
git commit -m "重构：增强 schema_match 断言规则校验与闭环验证"
```

### Task 3: 同步文档并执行回归

**Files:**
- Modify: `README.md`
- Modify: `product_document/架构设计/模板体系与代码生成规范说明书.md`
- Modify: `product_document/阶段文档/V1阶段工作计划文档.md`
- Modify: `product_document/阶段文档/V1实施计划与开发任务拆解说明书.md`
- Modify: `product_document/测试文档/详细测试用例说明书(V1).md`

- [x] **Step 1: 同步文档**

```markdown
- 在 README 中补记 `schema_match` 已落地的当前状态和验证结果。
- 在《模板体系与代码生成规范说明书》中把 `schema_match` 从“V1 推荐类型”更新为“当前已落地最小实现”。
- 在《V1阶段工作计划文档》中回填模板/规则覆盖增强的新一轮结果。
- 在《V1实施计划与开发任务拆解说明书》中回填本轮验证命令和结果。
- 在《详细测试用例说明书(V1)》中补充 `schema_match` 模板和规则测试说明。
```

- [x] **Step 2: 执行回归**

Run:
- `python -m pytest tests/platform_core -v --basetemp .pytest_tmp/platform_core_assertion_full`
- `python -m pytest tests -v --basetemp .pytest_tmp/root_assertion_full`
- `python -m pytest api_test/tests -v --basetemp .pytest_tmp/api_test_assertion_full`
- `python api_test/run_test.py --public-baseline`

Expected: PASS；若外网站点直连波动，则按既有规则记录为外网风险，不误判为本轮逻辑失败。

- [ ] **Step 3: 提交并推送**

```bash
git add README.md product_document/架构设计/模板体系与代码生成规范说明书.md product_document/阶段文档/V1阶段工作计划文档.md product_document/阶段文档/V1实施计划与开发任务拆解说明书.md product_document/测试文档/详细测试用例说明书(V1).md
git commit -m "文档：同步 V1 断言模板覆盖增强进展与测试结果"
git push origin main
```
