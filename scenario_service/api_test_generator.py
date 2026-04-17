"""`api_test` 资产生成的最小路径规则。"""

from __future__ import annotations

from pathlib import Path
from textwrap import dedent


def build_asset_paths(*, project_code: str, model_code: str, case_code: str) -> dict[str, Path]:
    """根据项目、模块和用例编码返回 `api_test` 资产落点。"""
    core_dir = Path("api_test") / "core" / project_code / model_code
    test_dir = Path("api_test") / "tests" / project_code / model_code
    return {
        "core_dir": core_dir,
        "test_dir": test_dir,
        "test_file": test_dir / f"test_{case_code}.py",
    }


def build_testcase_steps(selected_candidates: list[dict]) -> list[dict]:
    """根据抓包选择顺序生成测试用例方法链。"""
    ordered = sorted(selected_candidates, key=lambda item: item["selection_order"])
    return [
        {
            "step_index": index + 1,
            "method_name": item["method_name"],
        }
        for index, item in enumerate(ordered)
    ]


def render_testcase_module(
    *,
    project_code: str,
    model_code: str,
    feature_name: str,
    story_name: str,
    class_name: str,
    test_name: str,
    ordered_steps: list[dict],
) -> str:
    """生成包含 Allure 注解与步骤包装的最小测试模块代码。"""
    step_lines = []
    for item in ordered_steps:
        step_lines.extend(
            [
                f'        with allure.step("{item["step_index"]}.调用接口方法 {item["method_name"]}"):',
                f'            api_client.{item["method_name"]}()',
            ]
        )
    step_block = "\n".join(step_lines) or "        pass"
    return dedent(
        f'''
        import allure


        @allure.feature("{feature_name}")
        @allure.story("{story_name}")
        class {class_name}:
            """{project_code}/{model_code} 自动生成测试类。"""

            def {test_name}(self, api_client):
                """执行自动生成的方法链测试。"""
        {step_block}
        '''
    ).strip() + "\n"


def write_generated_assets(
    *,
    workspace_root: str | Path,
    project_code: str,
    model_code: str,
    core_filename: str,
    core_code: str,
    test_case_code: str,
    case_code: str,
) -> dict[str, str]:
    """把生成的接口方法与测试用例代码落盘到目标工作区。"""
    base_path = Path(workspace_root)
    asset_paths = build_asset_paths(project_code=project_code, model_code=model_code, case_code=case_code)
    core_dir = base_path / asset_paths["core_dir"]
    test_dir = base_path / asset_paths["test_dir"]
    core_dir.mkdir(parents=True, exist_ok=True)
    test_dir.mkdir(parents=True, exist_ok=True)

    core_path = core_dir / core_filename
    test_path = base_path / asset_paths["test_file"]
    core_path.write_text(core_code, encoding="utf-8")
    test_path.write_text(test_case_code, encoding="utf-8")

    return {
        "project_code": project_code,
        "model_code": model_code,
        "core_path": str(core_path),
        "test_path": str(test_path),
    }


def evaluate_generation_gate(pytest_summary: dict) -> dict[str, bool | str]:
    """根据 `pytest` 结果判断当前生成资产是否允许继续提交。"""
    if pytest_summary["pytest_exit_code"] != 0:
        return {"submission_allowed": False, "status": "blocked"}
    return {"submission_allowed": True, "status": "ready_for_review"}
