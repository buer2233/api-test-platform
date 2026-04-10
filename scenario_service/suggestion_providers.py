"""V2 场景建议提供者。"""

from __future__ import annotations

from scenario_service.models import ScenarioRecord


class BaseSuggestionProvider:
    """建议提供者抽象基类。"""

    def generate(self, scenario: ScenarioRecord, suggestion_type: str) -> list[dict]:
        """根据场景和建议类型生成结构化建议补丁。"""
        raise NotImplementedError


class RuleBasedSuggestionProvider(BaseSuggestionProvider):
    """规则型默认建议提供者。"""

    def generate(self, scenario: ScenarioRecord, suggestion_type: str) -> list[dict]:
        """基于当前场景结构生成最小可治理建议。"""
        if suggestion_type == "assertion_completion":
            return self._build_assertion_completion_suggestions(scenario)
        return []

    @staticmethod
    def _build_assertion_completion_suggestions(scenario: ScenarioRecord) -> list[dict]:
        """为缺少提取断言的步骤生成最小补丁建议。"""
        suggestions: list[dict] = []
        for step in scenario.steps.all().order_by("step_order", "id"):
            raw_step = dict((step.metadata or {}).get("raw_step") or {})
            expected = dict(raw_step.get("expected") or {})
            if "extract" in expected:
                continue
            patch_expected = {
                **expected,
                "extract": {
                    "result_id": "id",
                },
            }
            suggestions.append(
                {
                    "target_type": "step",
                    "target_id": step.step_id,
                    "patch_payload": {
                        "steps": [
                            {
                                "step_id": step.step_id,
                                "expected": patch_expected,
                            }
                        ]
                    },
                    "diff_summary": {
                        "added_expected_keys": ["extract"],
                        "target_step_id": step.step_id,
                    },
                    "confidence": "medium",
                }
            )
        return suggestions
