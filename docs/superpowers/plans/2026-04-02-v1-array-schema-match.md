# V1 数组对象结构断言增强 Implementation Plan

**Goal:** 为 `platform_core` 的 `schema_match` 补齐对象数组结构表达、模板渲染、规则校验和假响应生成能力。

**Architecture:** 继续围绕文档驱动最小闭环推进，不新增输入路线。实现顺序采用 TDD：先锁定解析层、模板层、规则层和流水线层失败测试，再补最小实现，最后同步 README 与阶段文档。

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
- `docs/superpowers/specs/2026-04-02-v1-array-schema-match-design.md`
- `docs/superpowers/plans/2026-04-02-v1-array-schema-match.md`

---

## Task 1：锁定数组对象结构断言失败测试

**Files:**
- Modify: `tests/platform_core/test_services_and_assets.py`
- Modify: `tests/platform_core/test_templates_and_rules.py`
- Modify: `tests/platform_core/test_pipeline.py`

- [x] Step 1：新增失败测试
  - 解析器能从对象数组响应中生成 `schema_match(type=array,item_type=object,required_fields=...)`
  - 模板层能渲染数组项对象断言
  - pytest 模板能生成对象数组假响应
  - 流水线生成的测试骨架包含数组项结构断言

- [x] Step 2：运行定向测试确认失败
  - `python -m pytest tests/platform_core/test_templates_and_rules.py tests/platform_core/test_services_and_assets.py tests/platform_core/test_pipeline.py -k "array_object or schema_match" -v --basetemp .pytest_tmp/array_schema_red`

## Task 2：补最小实现

**Files:**
- Modify: `platform_core/parsers.py`
- Modify: `platform_core/renderers.py`
- Modify: `platform_core/rules.py`
- Modify: `platform_core/templates/assertions/schema_match.py.j2`

- [x] Step 1：在解析器中识别对象数组并生成增强版 `schema_match`
- [x] Step 2：在模板层渲染数组项对象断言
- [x] Step 3：在假响应生成器中生成最小对象数组
- [x] Step 4：在规则层校验 `item_type` 和 `required_fields`

- [x] Step 5：运行定向测试确认通过
  - `python -m pytest tests/platform_core/test_templates_and_rules.py tests/platform_core/test_services_and_assets.py tests/platform_core/test_pipeline.py -k "array_object or schema_match" -v --basetemp .pytest_tmp/array_schema_green`

## Task 3：同步文档并执行回归

**Files:**
- Modify: `README.md`
- Modify: `product_document/架构设计/模板体系与代码生成规范说明书.md`
- Modify: `product_document/阶段文档/V1阶段工作计划文档.md`
- Modify: `product_document/阶段文档/V1实施计划与开发任务拆解说明书.md`
- Modify: `product_document/测试文档/详细测试用例说明书(V1).md`

- [x] Step 1：同步能力说明、测试编号和本轮进度
- [x] Step 2：执行回归
  - `python -m pytest tests/platform_core -v --basetemp .pytest_tmp/platform_core_array_schema_full`
  - `python -m pytest tests -v --basetemp .pytest_tmp/root_array_schema_full`
  - `python -m pytest api_test/tests -v --basetemp .pytest_tmp/api_test_array_schema_full`
  - `python api_test/run_test.py --public-baseline`
  - `cd api_test && python run_test.py --public-baseline`

- [ ] Step 3：提交并推送
