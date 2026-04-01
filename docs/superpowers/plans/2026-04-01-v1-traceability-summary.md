# V1 可追溯记录与服务摘要增强 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 增强 `platform_core` 的生成记录、执行记录和工作区检查摘要，让 V1 最小闭环更适合作为后续服务层与客户端的稳定输出。

**Architecture:** 本轮只围绕 `platform_core` 的记录和摘要边界推进，不扩展 V2 路线，也不继续拆旧 `api_test` 工具层。实现采用 TDD：先锁定模型与执行摘要测试，再修改执行器、流水线和资产检查逻辑，最后同步 CLI 输出和阶段文档。

**Tech Stack:** Python 3.12, pytest, pydantic, JUnit XML, Markdown, Git

---

## File Map

### Create
- 无新增代码目录，复用现有 `platform_core` 结构

### Modify
- `platform_core/models.py`
- `platform_core/executors.py`
- `platform_core/assets.py`
- `platform_core/pipeline.py`
- `platform_core/cli.py`
- `tests/platform_core/test_models.py`
- `tests/platform_core/test_pipeline.py`
- `tests/platform_core/test_services_and_assets.py`
- `README.md`
- `product_document/架构设计/中间模型设计说明书.md`
- `product_document/阶段文档/V1阶段工作计划文档.md`
- `product_document/阶段文档/V1实施计划与开发任务拆解说明书.md`
- `product_document/测试文档/详细测试用例说明书(V1).md`

---

### Task 1: 锁定增强后的记录模型测试

**Files:**
- Modify: `tests/platform_core/test_models.py`
- Modify: `platform_core/models.py`

- [ ] **Step 1: 先写失败测试**

```python
def test_generation_record_captures_extended_traceability_fields():
    generated_at = datetime(2026, 4, 1, 15, 0, 0)
    record = GenerationRecord(
        generation_id="gen-extended-001",
        generation_type="test_case",
        source_ids=["src-openapi-001"],
        target_asset_type="test_case",
        target_asset_path="generated/tests/test_get_user_profile.py",
        generator_type="hybrid",
        generated_at=generated_at,
        generated_by="codex",
        generation_version="v1",
        template_reference="templates/tests/test_module.py.j2",
        module_code="user",
        operation_code="get_user_profile",
        target_asset_digest="a" * 64,
        review_status="pending",
        execution_status="not_run",
    )
    assert record.module_code == "user"
    assert record.operation_code == "get_user_profile"
    assert record.target_asset_digest == "a" * 64


def test_execution_record_captures_structured_execution_summary():
    record = ExecutionRecord(
        execution_id="exec-structured-001",
        target_type="test_case",
        target_id="generated-suite",
        execution_level="smoke",
        started_at=datetime(2026, 4, 1, 15, 1, 0),
        ended_at=datetime(2026, 4, 1, 15, 1, 8),
        result_status="passed",
        report_path="generated/reports/generated-suite.xml",
        error_summary="",
        environment="local",
        command="python -m pytest generated/tests -v",
        exit_code=0,
        total_count=2,
        passed_count=2,
        failed_count=0,
        error_count=0,
        skipped_count=0,
    )
    assert record.command.startswith("python -m pytest")
    assert record.exit_code == 0
    assert record.total_count == 2
    assert record.passed_count == 2
```

- [ ] **Step 2: 运行测试确认失败**

Run: `python -m pytest tests/platform_core/test_models.py -v --basetemp .pytest_tmp/platform_core_models_traceability`

Expected: 失败，提示 `GenerationRecord` / `ExecutionRecord` 缺少新增字段。

- [ ] **Step 3: 写最小实现**

```python
class GenerationRecord(PlatformBaseModel):
    generation_id: str
    generation_type: Literal["api_method", "test_case", "assertion", "scenario"]
    source_ids: list[str] = Field(default_factory=list)
    target_asset_type: str
    target_asset_path: str
    generator_type: Literal["rule_based", "ai_assisted", "hybrid"]
    generated_at: datetime
    generated_by: str
    generation_version: str | None = None
    prompt_reference: str | None = None
    template_reference: str | None = None
    module_code: str | None = None
    operation_code: str | None = None
    target_asset_digest: str | None = None
    review_status: Literal["pending", "approved", "rejected", "revised"] = "pending"
    execution_status: Literal["not_run", "passed", "failed"] = "not_run"


class ExecutionRecord(PlatformBaseModel):
    execution_id: str
    target_type: str
    target_id: str
    execution_level: Literal["structure_check", "rule_check", "smoke", "scenario", "regression"]
    started_at: datetime
    ended_at: datetime | None = None
    result_status: Literal["passed", "failed", "error"]
    report_path: str | None = None
    error_summary: str | None = None
    environment: str | None = None
    command: str | None = None
    exit_code: int | None = None
    total_count: int = 0
    passed_count: int = 0
    failed_count: int = 0
    error_count: int = 0
    skipped_count: int = 0
```

- [ ] **Step 4: 运行测试确认通过**

Run: `python -m pytest tests/platform_core/test_models.py -v --basetemp .pytest_tmp/platform_core_models_traceability`

Expected: PASS。

- [ ] **Step 5: 提交**

```bash
git add tests/platform_core/test_models.py platform_core/models.py
git commit -m "重构：增强平台生成记录与执行记录模型的结构化摘要字段"
```

### Task 2: 锁定执行器与流水线的统计输出

**Files:**
- Modify: `tests/platform_core/test_pipeline.py`
- Modify: `platform_core/executors.py`
- Modify: `platform_core/pipeline.py`

- [ ] **Step 1: 先写失败测试**

```python
def test_pytest_executor_runs_smoke_test_and_returns_execution_record(tmp_path):
    output_root = tmp_path / "workspace"
    test_dir = output_root / "generated" / "tests"
    report_dir = output_root / "generated" / "reports"
    test_dir.mkdir(parents=True)
    report_dir.mkdir(parents=True)
    test_file = test_dir / "test_generated_smoke.py"
    test_file.write_text("def test_generated_smoke():\n    assert True\n", encoding="utf-8")

    record = PytestExecutor(project_root=Path.cwd()).run(test_file, output_root=output_root, target_id="generated-smoke")

    assert record.command is not None
    assert record.exit_code == 0
    assert record.total_count == 1
    assert record.passed_count == 1
    assert record.failed_count == 0


def test_document_driven_pipeline_generates_traceable_assets_and_executes_pytest(tmp_path):
    ...
    assert any(record.target_asset_digest for record in result.generation_records)
    assert result.execution_record.total_count == 1
    assert result.execution_record.passed_count == 1
```

- [ ] **Step 2: 运行测试确认失败**

Run: `python -m pytest tests/platform_core/test_pipeline.py -v --basetemp .pytest_tmp/platform_core_pipeline_traceability`

Expected: 失败，执行记录缺少统计字段，生成记录缺少摘要字段。

- [ ] **Step 3: 写最小实现**

```python
def run(self, test_path: str | Path, output_root: str | Path, target_id: str | None = None) -> ExecutionRecord:
    command = [
        self.python_executable,
        "-m",
        "pytest",
        str(test_target),
        "-v",
        f"--basetemp={basetemp_path}",
        f"--junitxml={report_path}",
    ]
    result = subprocess.run(command, ...)
    total_count, failed_count, error_count, skipped_count = self._parse_junit_counts(report_path)
    passed_count = max(total_count - failed_count - error_count - skipped_count, 0)
    return ExecutionRecord(
        ...,
        command=" ".join(command),
        exit_code=result.returncode,
        total_count=total_count,
        passed_count=passed_count,
        failed_count=failed_count,
        error_count=error_count,
        skipped_count=skipped_count,
    )
```

```python
api_record = self._write_generation_record(
    ...,
    module_code=module.module_code,
    operation_code=None,
    target_asset_digest=asset_workspace.build_content_digest(api_path),
)
```

- [ ] **Step 4: 运行测试确认通过**

Run: `python -m pytest tests/platform_core/test_pipeline.py -v --basetemp .pytest_tmp/platform_core_pipeline_traceability`

Expected: PASS。

- [ ] **Step 5: 提交**

```bash
git add tests/platform_core/test_pipeline.py platform_core/executors.py platform_core/pipeline.py
git commit -m "重构：补齐平台执行器统计信息和流水线生成摘要"
```

### Task 3: 锁定工作区检查与 CLI 摘要输出

**Files:**
- Modify: `tests/platform_core/test_services_and_assets.py`
- Modify: `platform_core/assets.py`
- Modify: `platform_core/cli.py`

- [ ] **Step 1: 先写失败测试**

```python
def test_platform_application_service_can_inspect_generated_workspace(tmp_path):
    ...
    assert len(inspection.generation_records) == 2
    assert inspection.missing_generation_records == []
    assert any(record.operation_code == "get_user_profile" for record in inspection.generation_records)


def test_platform_application_service_reports_missing_generation_records(tmp_path):
    ...
    record_path = output_root / "generated" / "records" / "gen-xxxx.json"
    record_path.unlink()
    inspection = PlatformApplicationService(project_root=Path.cwd()).inspect_workspace(output_root)
    assert inspection.validation_status == "invalid"
    assert len(inspection.missing_generation_records) == 1


def test_platform_core_cli_runs_document_pipeline(tmp_path):
    ...
    payload = json.loads(result.stdout)
    assert payload["generation_count"] == 2
    assert payload["asset_count"] == 2
    assert payload["execution_exit_code"] == 0
    assert payload["passed_count"] == 1
```

- [ ] **Step 2: 运行测试确认失败**

Run: `python -m pytest tests/platform_core/test_services_and_assets.py tests/platform_core/test_pipeline.py -v --basetemp .pytest_tmp/platform_core_service_traceability`

Expected: 失败，`inspection` 与 CLI 输出缺少新字段。

- [ ] **Step 3: 写最小实现**

```python
class GenerationInspectionEntry(PlatformBaseModel):
    generation_id: str
    generation_type: str
    target_asset_type: str
    target_asset_path: str
    module_code: str | None = None
    operation_code: str | None = None
    template_reference: str | None = None
    review_status: str
    execution_status: str
```

```python
def inspect_manifest(self, validator: RuleValidator | None = None) -> AssetInspectionResult:
    ...
    generation_records = self._load_generation_records(manifest.generation_ids)
    missing_generation_records = [...]
    if missing_generation_records:
        validation_status = "invalid"
    return AssetInspectionResult(
        ...,
        generation_records=generation_records,
        missing_generation_records=missing_generation_records,
    )
```

```python
if args.command == "run":
    print(json.dumps({
        "source": result.source_document.source_name,
        "modules": len(result.modules),
        "operations": len(result.operations),
        "generation_count": len(result.generation_records),
        "asset_count": len(result.asset_manifest.assets),
        "execution_target": result.execution_record.target_id,
        "execution_status": result.execution_record.result_status,
        "execution_exit_code": result.execution_record.exit_code,
        "total_count": result.execution_record.total_count,
        "passed_count": result.execution_record.passed_count,
        "failed_count": result.execution_record.failed_count,
        "error_count": result.execution_record.error_count,
        "skipped_count": result.execution_record.skipped_count,
        "report_path": result.execution_record.report_path,
        "asset_manifest_path": result.asset_manifest_path,
    }, ensure_ascii=False))
```

- [ ] **Step 4: 运行测试确认通过**

Run: `python -m pytest tests/platform_core/test_services_and_assets.py tests/platform_core/test_pipeline.py -v --basetemp .pytest_tmp/platform_core_service_traceability`

Expected: PASS。

- [ ] **Step 5: 提交**

```bash
git add tests/platform_core/test_services_and_assets.py platform_core/assets.py platform_core/cli.py
git commit -m "重构：增强工作区检查结果与 CLI 执行摘要输出"
```

### Task 4: 同步 README 与 V1 阶段文档

**Files:**
- Modify: `README.md`
- Modify: `product_document/架构设计/中间模型设计说明书.md`
- Modify: `product_document/阶段文档/V1阶段工作计划文档.md`
- Modify: `product_document/阶段文档/V1实施计划与开发任务拆解说明书.md`
- Modify: `product_document/测试文档/详细测试用例说明书(V1).md`

- [ ] **Step 1: 更新文档中的能力描述**

```markdown
- 在 README 中补记当前轮“生成记录/执行记录/工作区检查摘要增强”状态和最新验证命令。
- 在《中间模型设计说明书》中补记 `GenerationRecord` / `ExecutionRecord` 的摘要增强字段。
- 在《V1阶段工作计划文档》中补记当前轮开发进度、测试结果和风险收敛状态。
- 在《V1实施计划与开发任务拆解说明书》中把下一轮重点从“记录增强待做”更新为“当前轮已完成”。
- 在《详细测试用例说明书(V1)》中把 P1 的生成记录、执行记录增强转为已落地测试项。
```

- [ ] **Step 2: 运行文档治理与平台核心回归**

Run:
- `python -m pytest tests -v --basetemp .pytest_tmp/root_after_traceability_docs`
- `python -m pytest tests/platform_core -v --basetemp .pytest_tmp/platform_core_after_traceability`

Expected: PASS。

- [ ] **Step 3: 运行 `api_test` 回归确认未受影响**

Run:
- `python -m pytest api_test/tests -v --basetemp .pytest_tmp/api_test_after_traceability`
- `python api_test/run_test.py --public-baseline`

Expected: 通过；如直连外网波动，则记录为站点超时风险，不误判为本轮逻辑失败。

- [ ] **Step 4: 提交**

```bash
git add README.md product_document/架构设计/中间模型设计说明书.md product_document/阶段文档/V1阶段工作计划文档.md product_document/阶段文档/V1实施计划与开发任务拆解说明书.md product_document/测试文档/详细测试用例说明书(V1).md
git commit -m "文档：同步 V1 记录增强与服务摘要收口进展"
```

### Task 5: 完成整仓验证并推送

**Files:**
- Modify: 本轮全部改动文件

- [ ] **Step 1: 执行整仓验证**

Run:
- `python -m pytest tests -v --basetemp .pytest_tmp/root_full_traceability`
- `python -m pytest tests/platform_core -v --basetemp .pytest_tmp/platform_core_full_traceability`
- `python -m pytest api_test/tests -v --basetemp .pytest_tmp/api_test_full_traceability`
- `python api_test/run_test.py --public-baseline`
- `cd api_test && python run_test.py --public-baseline`

Expected: `platform_core` 与根治理测试全部通过；`api_test` 若因外网站点直连波动失败，需要切代理复验并在文档中准确记录。

- [ ] **Step 2: 提交最终状态**

```bash
git add -A
git commit -m "重构：增强 V1 闭环记录追溯能力并收口服务摘要输出"
```

- [ ] **Step 3: 推送远端**

```bash
git push origin main
```
