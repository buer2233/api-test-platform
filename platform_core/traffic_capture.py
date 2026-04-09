"""抓包驱动的场景草稿解析能力。"""

from __future__ import annotations

import json
import re
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from urllib.parse import parse_qsl, urlparse

from platform_core.models import (
    AssertionCandidate,
    DependencyLink,
    FunctionalCaseDraft,
    FunctionalCaseIssue,
    ScenarioLifecycleStatus,
    ScenarioStep,
    SourceDocument,
    TestScenario,
    VariableBinding,
)


class TrafficCaptureDraftParser:
    """把 HAR 抓包输入清洗为可审核的场景草稿。"""

    _STATIC_EXTENSIONS = {
        ".js",
        ".css",
        ".png",
        ".jpg",
        ".jpeg",
        ".gif",
        ".svg",
        ".ico",
        ".woff",
        ".woff2",
        ".ttf",
        ".map",
    }
    _IGNORED_METHODS = {"OPTIONS"}
    _IGNORED_HEADERS = {
        "accept",
        "accept-encoding",
        "accept-language",
        "cache-control",
        "connection",
        "content-length",
        "cookie",
        "host",
        "origin",
        "pragma",
        "referer",
        "sec-ch-ua",
        "sec-ch-ua-mobile",
        "sec-ch-ua-platform",
        "sec-fetch-dest",
        "sec-fetch-mode",
        "sec-fetch-site",
        "user-agent",
    }

    def parse(self, source_path: str | Path) -> FunctionalCaseDraft:
        """从 HAR 文件读取抓包内容并生成场景草稿。"""
        source = Path(source_path)
        raw_capture = json.loads(source.read_text(encoding="utf-8-sig"))
        return self.parse_payload(raw_capture=raw_capture, source_name=source.stem, source_path=source)

    def parse_payload(
        self,
        raw_capture: dict[str, Any],
        source_name: str | None = None,
        source_path: Path | None = None,
    ) -> FunctionalCaseDraft:
        """直接把抓包请求体解析为场景草稿聚合对象。"""
        resolved_source_name = source_name or "traffic_capture"
        source = source_path or Path(f"{self._normalize_identifier(resolved_source_name)}.har.json")
        normalized_entries = self._normalize_entries(raw_capture=raw_capture)
        source_document = self._build_source_document(
            source=source,
            source_name=resolved_source_name,
            normalized_entries=normalized_entries,
        )
        scenario = self._build_scenario(
            source_document=source_document,
            source_name=resolved_source_name,
            normalized_entries=normalized_entries,
        )

        steps: list[ScenarioStep] = []
        assertions: list[AssertionCandidate] = []
        issues: list[FunctionalCaseIssue] = []
        binding_index: dict[str, VariableBinding] = {}
        value_index: dict[str, list[VariableBinding]] = {}
        dependencies: list[DependencyLink] = []

        for step_order, entry in enumerate(normalized_entries, start=1):
            step_name = f'{entry["method"]} {entry["path_template"]}'
            operation_id = self._build_operation_id(entry["method"], entry["path_template"])
            request_payload = {
                "path_template": entry["path_template"],
                "path_params": dict(entry["path_params"]),
                "query_params": dict(entry["query_params"]),
                "headers": dict(entry["headers"]),
                "json": entry["json_body"],
            }
            request_payload, step_uses, step_dependencies = self._resolve_request_bindings(
                request_payload=request_payload,
                current_operation_id=operation_id,
                step_order=step_order,
                binding_index=binding_index,
                value_index=value_index,
            )
            raw_step = {
                "step_name": step_name,
                "operation_id": operation_id,
                "request": request_payload,
                "expected": {
                    "status_code": entry["response_status"],
                },
                "uses": step_uses,
                "capture_source": entry["url"],
                "capture_confidence": "low",
            }
            step_id = f"{scenario.scenario_id}-step-{step_order}"
            step = ScenarioStep(
                step_id=step_id,
                scenario_id=scenario.scenario_id,
                step_order=step_order,
                step_name=step_name,
                operation_id=operation_id,
                input_bindings=list(step_uses.keys()),
                expected_bindings=list(raw_step["expected"].keys()),
                assertion_ids=[],
                retry_policy={},
                optional=False,
                metadata={"raw_step": raw_step, "capture_confidence": "low"},
            )
            steps.append(step)
            assertions.append(self._build_status_assertion(step=step, response_status=entry["response_status"]))
            issues.append(
                FunctionalCaseIssue(
                    issue_code="capture_operation_needs_review",
                    issue_message=f"抓包步骤暂以候选操作标识接入，需人工确认接口绑定: {step_name}",
                    severity="warning",
                    step_id=step.step_id,
                    step_order=step.step_order,
                    metadata={"operation_id": operation_id},
                )
            )
            dependencies.extend(step_dependencies)
            self._collect_response_bindings(
                entry=entry,
                step=step,
                binding_index=binding_index,
                value_index=value_index,
            )

        lifecycle = ScenarioLifecycleStatus(
            review_status=scenario.review_status,
            execution_status="not_started",
            current_stage="draft",
        )
        return FunctionalCaseDraft(
            source_document=source_document,
            scenario=scenario,
            steps=steps,
            bindings=list(binding_index.values()),
            dependencies=dependencies,
            assertions=assertions,
            review_records=[],
            lifecycle=lifecycle,
            issues=issues,
        )

    def _normalize_entries(self, raw_capture: dict[str, Any]) -> list[dict[str, Any]]:
        """过滤噪声、去重并生成稳定的请求序列。"""
        entries = sorted(
            raw_capture.get("log", {}).get("entries") or [],
            key=lambda item: item.get("startedDateTime") or "",
        )
        normalized_entries: list[dict[str, Any]] = []
        seen_keys: set[str] = set()
        for entry in entries:
            normalized_entry = self._normalize_entry(entry)
            if not normalized_entry or self._is_noise_entry(normalized_entry):
                continue
            dedupe_key = json.dumps(
                {
                    "method": normalized_entry["method"],
                    "path_template": normalized_entry["path_template"],
                    "path_params": normalized_entry["path_params"],
                    "query_params": normalized_entry["query_params"],
                    "headers": normalized_entry["headers"],
                    "json_body": normalized_entry["json_body"],
                },
                ensure_ascii=False,
                sort_keys=True,
            )
            if dedupe_key in seen_keys:
                continue
            seen_keys.add(dedupe_key)
            normalized_entries.append(normalized_entry)
        return normalized_entries

    def _normalize_entry(self, entry: dict[str, Any]) -> dict[str, Any] | None:
        """把单条 HAR entry 归一化为便于场景草稿消费的结构。"""
        request = entry.get("request") or {}
        response = entry.get("response") or {}
        method = str(request.get("method") or "").upper()
        url = request.get("url")
        if not method or not url:
            return None

        parsed_url = urlparse(url)
        query_pairs = request.get("queryString") or [
            {"name": name, "value": value}
            for name, value in parse_qsl(parsed_url.query, keep_blank_values=True)
        ]
        query_params = {
            item.get("name"): item.get("value", "")
            for item in sorted(query_pairs, key=lambda pair: pair.get("name") or "")
            if item.get("name")
        }
        path_template, path_params = self._normalize_path(parsed_url.path)
        headers = self._normalize_headers(request.get("headers") or [])
        json_body = self._load_json_text((request.get("postData") or {}).get("text"))
        response_json = self._load_json_text((response.get("content") or {}).get("text"))
        return {
            "started_at": entry.get("startedDateTime") or "",
            "method": method,
            "url": url,
            "host": parsed_url.netloc,
            "path": parsed_url.path,
            "path_template": path_template,
            "path_params": path_params,
            "query_params": query_params,
            "headers": headers,
            "json_body": json_body,
            "response_status": int(response.get("status") or 0),
            "response_json": response_json,
        }

    def _is_noise_entry(self, entry: dict[str, Any]) -> bool:
        """判断当前请求是否属于静态资源或浏览器噪声。"""
        if entry["method"] in self._IGNORED_METHODS:
            return True
        suffix = Path(entry["path"]).suffix.lower()
        return suffix in self._STATIC_EXTENSIONS

    def _build_source_document(
        self,
        source: Path,
        source_name: str,
        normalized_entries: list[dict[str, Any]],
    ) -> SourceDocument:
        """构造抓包来源对象。"""
        raw_reference = str(source.resolve()) if source.exists() else str(source)
        source_key = f"traffic_capture_{self._normalize_identifier(source_name)}"
        return SourceDocument(
            source_id=f"source-{source_key}",
            source_type="traffic_capture",
            source_name=source_name,
            source_path=str(source),
            source_version="v2_har_draft",
            source_summary=f"共保留 {len(normalized_entries)} 条可审核抓包请求",
            imported_at=datetime.now(UTC),
            imported_by="codex",
            raw_reference=raw_reference,
        )

    def _build_scenario(
        self,
        source_document: SourceDocument,
        source_name: str,
        normalized_entries: list[dict[str, Any]],
    ) -> TestScenario:
        """构造抓包场景草稿对象。"""
        scenario_code = f"capture_{self._normalize_identifier(source_name)}"
        scenario_name = source_name or "抓包场景草稿"
        return TestScenario(
            scenario_id=f"scenario-{scenario_code}",
            scenario_name=scenario_name,
            scenario_code=scenario_code,
            module_id="traffic_capture",
            scenario_desc=f"抓包导入草稿，共保留 {len(normalized_entries)} 个候选步骤",
            source_ids=[source_document.source_id],
            priority="medium",
            review_status="pending",
            preconditions=[],
            postconditions=[],
            cleanup_required=False,
            metadata={"input_type": "traffic_capture_har"},
        )

    def _resolve_request_bindings(
        self,
        request_payload: dict[str, Any],
        current_operation_id: str,
        step_order: int,
        binding_index: dict[str, VariableBinding],
        value_index: dict[str, list[VariableBinding]],
    ) -> tuple[dict[str, Any], dict[str, str], list[DependencyLink]]:
        """在当前请求中识别并替换已知的动态值候选。"""
        step_uses: dict[str, str] = {}
        dependencies: list[DependencyLink] = []
        seen_dependency_keys: set[tuple[str, str]] = set()

        def replace_value(value: Any) -> Any:
            binding = self._match_binding(value=value, value_index=value_index)
            if binding is None:
                return value
            step_uses[binding.variable_name] = f"$scenario.{binding.variable_name}"
            if current_operation_id not in binding.target_operations:
                binding.target_operations.append(current_operation_id)
            dependency_key = (binding.binding_id, current_operation_id)
            if dependency_key not in seen_dependency_keys:
                seen_dependency_keys.add(dependency_key)
                dependencies.append(
                    DependencyLink(
                        dependency_id=(
                            f"capture-step-{step_order}-dependency-{self._normalize_identifier(binding.variable_name)}"
                        ),
                        upstream_operation_id=binding.source_operation_id,
                        downstream_operation_id=current_operation_id,
                        dependency_type="data_flow",
                        binding_id=binding.binding_id,
                        required=True,
                        confidence_score=0.8,
                        source="traffic_capture",
                        metadata={"capture_confidence": "low"},
                    )
                )
            raw_sample = binding.metadata.get("value_sample")
            if isinstance(value, str) and isinstance(raw_sample, str) and raw_sample in value and value != raw_sample:
                return value.replace(raw_sample, f"$scenario.{binding.variable_name}")
            return f"$scenario.{binding.variable_name}"

        transformed_payload = self._walk_payload(request_payload, replace_value)
        return transformed_payload, step_uses, dependencies

    def _collect_response_bindings(
        self,
        entry: dict[str, Any],
        step: ScenarioStep,
        binding_index: dict[str, VariableBinding],
        value_index: dict[str, list[VariableBinding]],
    ) -> None:
        """从响应体中提取后续可复用的动态值候选。"""
        for field_path, raw_value in self._flatten_json(entry["response_json"]):
            variable_name = self._build_variable_name(field_path)
            if variable_name not in binding_index:
                binding_index[variable_name] = VariableBinding(
                    binding_id=f"{step.step_id}-binding-{self._normalize_identifier(variable_name)}",
                    variable_name=variable_name,
                    source_operation_id=step.operation_id,
                    source_field_path=field_path,
                    extract_expression=self._build_extract_expression(field_path),
                    target_operations=[],
                    target_scope="scenario",
                    fallback_value=None,
                    required=False,
                    metadata={
                        "source_step_id": step.step_id,
                        "capture_confidence": "low",
                        "value_sample": raw_value,
                    },
                )
            value_index.setdefault(str(raw_value), []).append(binding_index[variable_name])

    def _build_status_assertion(self, step: ScenarioStep, response_status: int) -> AssertionCandidate:
        """为抓包步骤生成最小状态码断言候选。"""
        assertion_id = f"{step.step_id}-status-code"
        step.assertion_ids.append(assertion_id)
        return AssertionCandidate(
            assertion_id=assertion_id,
            operation_id=step.operation_id,
            scenario_step_id=step.step_id,
            assertion_type="status_code",
            target_path="status_code",
            expected_value=response_status,
            priority="high",
            source="traffic_capture",
            confidence_score=0.8,
            review_status="pending",
        )

    @staticmethod
    def _normalize_headers(headers: list[dict[str, Any]]) -> dict[str, Any]:
        """过滤浏览器噪声请求头，仅保留和场景语义相关的头信息。"""
        normalized_headers: dict[str, Any] = {}
        for item in headers:
            header_name = str(item.get("name") or "").strip()
            if not header_name:
                continue
            normalized_key = header_name.lower()
            if normalized_key in TrafficCaptureDraftParser._IGNORED_HEADERS:
                continue
            normalized_headers[header_name] = item.get("value", "")
        return normalized_headers

    def _normalize_path(self, path: str) -> tuple[str, dict[str, Any]]:
        """把路径中的动态段抽取为模板和路径参数。"""
        segments = [segment for segment in str(path or "").split("/") if segment]
        normalized_segments: list[str] = []
        path_params: dict[str, Any] = {}
        for index, segment in enumerate(segments):
            if self._is_dynamic_segment(segment):
                previous_segment = segments[index - 1] if index > 0 else "value"
                param_name = self._build_path_param_name(previous_segment)
                normalized_segments.append(f"{{{param_name}}}")
                path_params[param_name] = self._coerce_scalar(segment)
                continue
            normalized_segments.append(segment)
        return "/" + "/".join(normalized_segments), path_params

    @staticmethod
    def _build_path_param_name(previous_segment: str) -> str:
        """基于前一个静态路径段推导路径参数名。"""
        candidate = re.sub(r"[^a-z0-9]+", "_", previous_segment.lower()).strip("_") or "value"
        if candidate.endswith("ies"):
            candidate = f"{candidate[:-3]}y"
        elif candidate.endswith("s") and len(candidate) > 1:
            candidate = candidate[:-1]
        return f"{candidate}_id"

    @staticmethod
    def _is_dynamic_segment(segment: str) -> bool:
        """判断路径段是否像资源 ID 或 UUID。"""
        return bool(re.fullmatch(r"\d+", segment) or re.fullmatch(r"[0-9a-fA-F-]{8,}", segment))

    @staticmethod
    def _coerce_scalar(value: str) -> Any:
        """把字符串值尽量转换为更稳定的标量类型。"""
        if re.fullmatch(r"\d+", value):
            return int(value)
        return value

    def _build_operation_id(self, method: str, path_template: str) -> str:
        """根据方法和规范化路径构造候选操作标识。"""
        return f'capture-{self._normalize_identifier(f"{method}_{path_template}")}'

    def _build_variable_name(self, field_path: str) -> str:
        """根据响应字段路径生成稳定的变量名。"""
        tail = field_path.split(".")[-1]
        return self._normalize_identifier(tail)

    @staticmethod
    def _build_extract_expression(field_path: str) -> str:
        """把响应字段路径转换为统一的 JSONPath 表达式。"""
        return f'$.{field_path.lstrip("$.")}'

    @staticmethod
    def _flatten_json(payload: Any, prefix: str = "") -> list[tuple[str, Any]]:
        """递归提取响应体中的原子字段。"""
        flattened: list[tuple[str, Any]] = []
        if isinstance(payload, dict):
            for key, value in payload.items():
                next_prefix = f"{prefix}.{key}" if prefix else str(key)
                flattened.extend(TrafficCaptureDraftParser._flatten_json(value, next_prefix))
            return flattened
        if isinstance(payload, list):
            for index, value in enumerate(payload):
                next_prefix = f"{prefix}[{index}]"
                flattened.extend(TrafficCaptureDraftParser._flatten_json(value, next_prefix))
            return flattened
        if prefix and payload is not None:
            flattened.append((prefix, payload))
        return flattened

    def _match_binding(
        self,
        value: Any,
        value_index: dict[str, list[VariableBinding]],
    ) -> VariableBinding | None:
        """根据请求值匹配已知的动态变量候选。"""
        raw_value = str(value)
        direct_candidates = value_index.get(raw_value) or []
        if direct_candidates:
            return direct_candidates[0]
        if not isinstance(value, str):
            return None
        for candidate_value in sorted(value_index.keys(), key=len, reverse=True):
            if candidate_value and candidate_value in value:
                return value_index[candidate_value][0]
        return None

    def _walk_payload(self, payload: Any, replacer) -> Any:
        """递归遍历请求载荷并替换已识别的动态值。"""
        if isinstance(payload, dict):
            return {key: self._walk_payload(value, replacer) for key, value in payload.items()}
        if isinstance(payload, list):
            return [self._walk_payload(item, replacer) for item in payload]
        return replacer(payload)

    @staticmethod
    def _load_json_text(raw_text: str | None) -> Any:
        """尽量把字符串内容解析为 JSON；解析失败时保留原文本。"""
        if raw_text is None or raw_text == "":
            return None
        try:
            return json.loads(raw_text)
        except json.JSONDecodeError:
            return raw_text

    @staticmethod
    def _normalize_identifier(value: Any) -> str:
        """把输入值转换为可复用的 snake_case 标识。"""
        raw_value = str(value or "").strip().lower()
        normalized = re.sub(r"[^a-z0-9]+", "_", raw_value)
        return normalized.strip("_") or "item"


__all__ = ["TrafficCaptureDraftParser"]
