#!/usr/bin/env python3
"""Evaluate LLM answers on multi-step reasoning questions across MCD and folder modes."""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
PLAIN_EVAL_DIR = REPO_ROOT / "tests" / "llm_plain_eval"
MCD_EVAL_DIR = REPO_ROOT / "tests" / "llm_mcd"
FOLDER_EVAL_DIR = REPO_ROOT / "tests" / "llm_unpacked_vs_disconnected"
for import_dir in (PLAIN_EVAL_DIR, MCD_EVAL_DIR, FOLDER_EVAL_DIR):
    sys.path.insert(0, str(import_dir))

import run_plain_eval as plain_eval  # noqa: E402
import run_mcd_eval as mcd_eval  # noqa: E402
import run_unpacked_vs_disconnected as folder_eval  # noqa: E402
from benchmark_validation import score_answer_tolerant  # noqa: E402


DEFAULT_MCD_PATH = Path("datasets/auto-manufacturer-tech-spec/auto-manufacturer-tech-spec.mcd")
DEFAULT_CONNECTED_DIR = Path("datasets/auto-manufacturer-tech-spec/unpacked")
DEFAULT_DISCONNECTED_DIR = Path("datasets/auto-manufacturer-tech-spec/disconnected")
DEFAULT_QUESTIONS_PATH = Path("datasets/auto-manufacturer-tech-spec/qa_reasoning_questions_20.jsonl")
DEFAULT_RESULTS_ROOT = Path("results/reasoning_questions")
DEFAULT_OPENAI_MODEL = "gpt-5.4"
DEFAULT_ANTHROPIC_MODEL = "claude-opus-4-5"
DEFAULT_XAI_MODEL = "grok-4.3"
DEFAULT_MAX_OUTPUT_TOKENS = 12000
DEFAULT_JUDGE_MAX_OUTPUT_TOKENS = 2000
PROVIDERS = ["openai", "anthropic", "xai"]
MODES = ["mcd", "connected", "disconnected"]

REASONING_GUIDANCE = (
    "Reasoning-question instructions: These prompts may require multiple table lookups, formula application, "
    "unit conversion, derived values, or conditional conclusions. Use tools to gather the source rows first. "
    "For numeric reasoning, build an answer contract before answering: source IDs, field names, source input values, "
    "question-stated constants, invariant values that stay unchanged, baseline values, derived new values, units, "
    "and every delta/change from baseline. Treat the answer contract as a final-answer checklist: every named ID, "
    "field name, observed source value, derived value, unit, and conclusion requested or implied by the question must "
    "appear in the final answer. "
    "For scenario questions that change a value, always report both the new value and the absolute change from the "
    "original value, with direction and units, even if the question asks mainly for the new value. When the changed "
    "quantity or a derived quantity has a nonzero baseline, also report the percent change using "
    "`100 * delta / baseline`, rounded sensibly. Echo percentage constants in percent form as well as decimal form, "
    "for example 93% and 0.93. "
    "When a question says a value stays unchanged or fixed, retrieve and state that invariant baseline value in the "
    "final answer, not just the changed output. "
    "For engineering calculations, use available math helpers when they match the task. In folder modes, after "
    "retrieving source row values, call the `engineering_math` tool for operations such as `brake_energy_payload_delta_mj`, "
    "`added_drag_force_n`, `road_load_power_kw`, `cda_m2`, `percent_change_from_delta`, "
    "`battery_window_range_delta`, `gcwr_reserve_kg`, `max_payload_for_gcwr_reserve`, `threshold_margin`, "
    "`scaled_pair_by_percent`, `final_drive_tractive_effort_delta`, `rpm_from_power_torque`, and "
    "`power_delta_at_same_rpm`. In MCD mode, retrieve `content/engineering_math.md` when useful or encode the same "
    "helper formula explicitly in `mcd_query` SQL. For folder modes, prefer `sql_query` or `engineering_math` over "
    "plain `table_select` when the question asks for a scenario calculation, because the successful observation "
    "should contain the baseline row values, invariant values, computed new values, and deltas together. "
    "When arithmetic uses powers, unit conversion, or more than two numeric inputs, compute the derived values in "
    "SQL/table tools or the engineering math helper where possible and return the source inputs plus computed outputs "
    "in one observation; do not rely on mental arithmetic in prose. "
    "For unit-sensitive calculations, inspect `content/engineering_math.md` when available, use the "
    "`engineering_math` tool in folder modes when helpful, or encode the same conversion explicitly in SQL. "
    "Convert km/h to m/s as `speed_kmh / 3.6` before applying kinetic-energy or drag formulas; never treat "
    "100 km/h as 100 m/s. "
    "For narrative or explanatory questions containing terms such as basis, rule, review, certification, validation, "
    "release gate, why, or effect, inspect the relevant dossier text or BM25/search result before finalizing. In MCD "
    "mode, prefer `mcd_search` or `mcd_markdown` for that context, then use `mcd_query` for source rows and computed "
    "values. "
    "For schema-adjacent concepts, query and report closely related fields when they exist, especially when one field "
    "is a domain synonym or stricter version of another. Examples include tow rating versus braked trailer rating, "
    "release status versus containment status, and calibration evidence versus certification evidence. "
    "Separate explicit data filters from explanatory context. If a query with inferred narrative/context filters "
    "returns zero rows, retry once with the minimal literal predicate from the question before concluding there is no "
    "matching data. "
    "Use successful tool observations as the only source of exact row values. Do not rely on values from unexecuted "
    "response objects, provisional answers, ignored JSON objects, or your own draft text unless the same values are "
    "present in a successful tool observation. If the exact prompt-named source ID has not been observed with the "
    "fields needed by the answer contract, call a table or SQL tool before finalizing. "
    "For explanatory questions that name both a narrative basis and exact table fields or IDs, retrieve the exact "
    "row values with table or SQL tools; dossier prose alone is not enough when the final answer needs source-row "
    "values. Use text tools for the rule or basis, and table or SQL tools for the exact data. "
    "For tradeoff and review questions, explicitly address each concern term named in the question, such as "
    "certification, calibration, drivability, validation, warranty, or thermal impact, when those terms are part of "
    "the requested conclusion. "
    "Before finalizing, check that delta = new - baseline and, where applicable, recompute a simple independent "
    "identity such as delta_E = 0.5 * payload_delta * v^2. Also verify that every field returned for the answer "
    "contract and every prompt-named identifier appears in the final answer; do not drop observed evidence values in "
    "the prose. "
    "In the final answer, include the source IDs, field names, input values, invariant values, formula/result summary, "
    "absolute and percent changes where applicable, units, and the engineering conclusion. Do not add caveats about "
    "referenced IDs or data sources unless a successful tool observation supports them, and do not rely on unstated "
    "assumptions when the dataset or prompt gives the needed value."
)

MCD_REASONING_GUIDANCE = (
    "MCD reasoning-question instructions: Use MCD MCP observations, not the dataset index alone, as the source of "
    "truth for final answers. Build an answer contract before answering: prompt-named IDs, exact field names, source "
    "input values, question-stated constants, invariant values, baseline values, derived new values, units, every "
    "delta/change, and the final engineering or gate conclusion. Select or compute those contract fields in successful "
    "MCD observations before finalizing. "
    "For table-only numeric questions, a single well-formed `mcd_query` CTE is acceptable when it returns all source "
    "inputs, computed outputs, units or unit-conversion values, deltas, and conclusion-supporting fields together. "
    "When arithmetic uses powers, unit conversion, or more than two numeric inputs, encode the calculation directly in "
    "`mcd_query` SQL. Convert km/h to m/s as `speed_kmh / 3.6`; never treat 100 km/h as 100 m/s. "
    "For narrative or explanatory questions containing terms such as basis, rule, review, certification, validation, "
    "release gate, why, or effect, inspect package prose first with `mcd_search` or `mcd_markdown`; then use "
    "`mcd_query` for exact row values and computed values. Do not answer those questions from the dataset index alone. "
    "For towing questions, retrieve and final-answer both `tow_rating_kg` and `braked_trailer_rating_kg` whenever "
    "either exists; in this dataset `tow_rating_kg` is the published braked rating and is mirrored by "
    "`braked_trailer_rating_kg`. "
    "For release-gate scenario questions, report baseline status fields separately from scenario fields. If changed "
    "scenario values make the gate pass, explicitly state `scenario_release_status=released` or `would be released`; "
    "do not leave the conclusion only as `would_meet_release_gates=yes`, and do not let the baseline "
    "`release_status=containment` contradict the scenario outcome. "
    "For lower coolant-flow or thermal-validation acceptance questions, treat the proposed coolant-flow target as the "
    "changed control variable, not as the validation evidence by itself. Check and final-answer validation evidence "
    "fields such as `thermal_derate_start_c`, `continuous_charge_kw`, `peak_discharge_kw`, and "
    "`battery_heat_rejection_kw` when present, and explicitly use the term `validation`. "
    "For schema-adjacent concepts, query and report closely related fields when they exist, especially domain "
    "synonyms or stricter versions of a field: tow rating versus braked trailer rating, release status versus "
    "containment status, and calibration evidence versus certification evidence. "
    "Before finalizing, verify every field returned for the answer contract and every prompt-named identifier appears "
    "in the final answer. Include source IDs, field names, input values, invariant values, formula/result summary, "
    "absolute and percent changes where applicable, units, and the engineering conclusion."
)


@dataclass(frozen=True)
class ProviderConfig:
    name: str
    model: str
    api_key_env: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mcd-path", type=Path, default=DEFAULT_MCD_PATH)
    parser.add_argument("--connected-dir", type=Path, default=DEFAULT_CONNECTED_DIR)
    parser.add_argument("--disconnected-dir", type=Path, default=DEFAULT_DISCONNECTED_DIR)
    parser.add_argument("--question-file", type=Path, default=DEFAULT_QUESTIONS_PATH)
    parser.add_argument(
        "--questions",
        type=int,
        default=None,
        help="Run only the first N reasoning questions. Defaults to all questions in --question-file.",
    )
    parser.add_argument("--results-root", type=Path, default=DEFAULT_RESULTS_ROOT)
    parser.add_argument(
        "--modes",
        default="all",
        help=(
            "Comma-separated modes: all, mcd, connected, disconnected, mcd,connected, "
            "mcd,disconnected, or connected,disconnected."
        ),
    )
    parser.add_argument("--providers", nargs="+", choices=PROVIDERS, default=["openai"])
    parser.add_argument("--openai-model", default=os.getenv("OPENAI_MODEL", DEFAULT_OPENAI_MODEL))
    parser.add_argument("--anthropic-model", default=os.getenv("ANTHROPIC_MODEL", DEFAULT_ANTHROPIC_MODEL))
    parser.add_argument("--xai-model", default=os.getenv("XAI_MODEL", DEFAULT_XAI_MODEL))
    parser.add_argument("--max-tool-steps", type=int, default=20)
    parser.add_argument("--mcd-mcp", default=os.getenv("MCD_MCP", mcd_eval.DEFAULT_MCD_MCP))
    parser.add_argument("--mcd-cli", default=os.getenv("MCD_CLI", "mcd"))
    parser.add_argument("--mcp-timeout-seconds", type=int, default=30)
    parser.add_argument("--cli-timeout-seconds", type=int, default=30)
    parser.add_argument("--python-timeout-seconds", type=int, default=30)
    parser.add_argument("--max-observation-chars", type=int, default=20000)
    parser.add_argument("--max-output-tokens", type=int, default=DEFAULT_MAX_OUTPUT_TOKENS)
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--timeout-seconds", type=int, default=120)
    parser.add_argument("--retries", type=int, default=2)
    parser.add_argument(
        "--scoring-mode",
        choices=["programmatic", "llm_judge"],
        default="llm_judge",
        help="Default is llm_judge because reasoning answers may be valid with varied phrasing.",
    )
    parser.add_argument(
        "--judge-provider",
        choices=["same", "openai", "anthropic", "xai"],
        default=os.getenv("JUDGE_PROVIDER", "same"),
    )
    parser.add_argument("--judge-model", default=os.getenv("JUDGE_MODEL"))
    parser.add_argument("--judge-max-output-tokens", type=int, default=DEFAULT_JUDGE_MAX_OUTPUT_TOKENS)
    parser.add_argument("--judge-temperature", type=float, default=0.0)
    parser.add_argument("--judge-timeout-seconds", type=int, default=120)
    parser.add_argument("--judge-retries", type=int, default=2)
    parser.add_argument(
        "--openai-stateful-responses",
        action="store_true",
        help="Use OpenAI previous_response_id chaining for MCD follow-up tool steps.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Write output structure without calling provider APIs or running tools.",
    )
    return parser.parse_args()


def parse_modes(value: str) -> list[str]:
    requested = [item.strip().casefold() for item in value.split(",") if item.strip()]
    if not requested or requested == ["all"]:
        return list(MODES)
    if "all" in requested:
        raise ValueError("--modes may be 'all' or a comma-separated subset, not both.")

    invalid = [item for item in requested if item not in MODES]
    if invalid:
        raise ValueError(f"Unknown mode(s): {', '.join(invalid)}. Valid modes: all, {', '.join(MODES)}.")

    ordered = []
    for mode in MODES:
        if mode in requested and mode not in ordered:
            ordered.append(mode)
    return ordered


def provider_configs(args: argparse.Namespace) -> list[ProviderConfig]:
    configs = {
        "openai": ProviderConfig("openai", args.openai_model, "OPENAI_API_KEY"),
        "anthropic": ProviderConfig("anthropic", args.anthropic_model, "ANTHROPIC_API_KEY"),
        "xai": ProviderConfig("xai", args.xai_model, "XAI_API_KEY"),
    }
    return [configs[name] for name in args.providers]


def judge_provider_config(args: argparse.Namespace, answer_config: ProviderConfig) -> ProviderConfig:
    if args.judge_provider == "same":
        return ProviderConfig(answer_config.name, args.judge_model or answer_config.model, answer_config.api_key_env)

    configs = {
        "openai": ProviderConfig("openai", args.judge_model or args.openai_model, "OPENAI_API_KEY"),
        "anthropic": ProviderConfig("anthropic", args.judge_model or args.anthropic_model, "ANTHROPIC_API_KEY"),
        "xai": ProviderConfig("xai", args.judge_model or args.xai_model, "XAI_API_KEY"),
    }
    return configs[args.judge_provider]


def to_mcd_config(config: ProviderConfig) -> mcd_eval.ProviderConfig:
    return mcd_eval.ProviderConfig(config.name, config.model, config.api_key_env)


def to_folder_config(config: ProviderConfig) -> folder_eval.ProviderConfig:
    return folder_eval.ProviderConfig(config.name, config.model, config.api_key_env)


def validate_reasoning_questions(questions: list[dict[str, Any]], path: Path) -> None:
    seen_ids: set[str] = set()
    errors: list[str] = []
    for index, question in enumerate(questions, start=1):
        location = f"{path}:{index}"
        for field in ("id", "family_id", "prompt", "reference_answer"):
            value = question.get(field)
            if not isinstance(value, str) or not value.strip():
                errors.append(f"{location} requires non-empty string field {field!r}.")

        question_id = question.get("id")
        if isinstance(question_id, str):
            if question_id in seen_ids:
                errors.append(f"{location} duplicates question id {question_id!r}.")
            seen_ids.add(question_id)

        expected_contains = question.get("expected_contains")
        if not isinstance(expected_contains, list) or not expected_contains:
            errors.append(f"{location} requires a non-empty expected_contains array.")
            continue
        for expected_index, expected in enumerate(expected_contains, start=1):
            if not isinstance(expected, str) or not expected.strip():
                errors.append(f"{location} expected_contains[{expected_index}] must be a non-empty string.")

        if isinstance(question.get("reference_answer"), str):
            reference_score = score_answer_tolerant(question["reference_answer"], expected_contains)
            if not reference_score["passed"]:
                missing = [
                    check["expected"]
                    for check in reference_score["checks"]
                    if not check["found"]
                ]
                question["_reference_missing_expected_contains"] = missing

    if errors:
        raise ValueError("Invalid reasoning questions:\n" + "\n".join(f"- {error}" for error in errors))


def install_reasoning_prompt_patches() -> None:
    original_mcd_agent_prompt = mcd_eval.make_mcd_agent_prompt
    original_mcd_compact_prompt = mcd_eval.make_mcd_agent_compact_prompt
    original_mcd_followup_prompt = mcd_eval.make_mcd_agent_followup_prompt
    original_kb_agent_prompt = folder_eval.make_kb_agent_prompt
    original_kb_compact_prompt = folder_eval.make_kb_agent_compact_prompt

    def inject_guidance_before_context(prompt: str, guidance: str) -> str:
        for marker in ("\n\nQuestion:\n", "\n\nTool observation for the previous action:\n"):
            if marker in prompt:
                before, after = prompt.split(marker, 1)
                return f"{before}\n\n{guidance}{marker}{after}"
        return f"{prompt}\n\n{guidance}"

    def make_mcd_reasoning_prompt(**kwargs: Any) -> str:
        return inject_guidance_before_context(original_mcd_agent_prompt(**kwargs), MCD_REASONING_GUIDANCE)

    def make_mcd_reasoning_compact_prompt(*args: Any, **kwargs: Any) -> str:
        return inject_guidance_before_context(
            original_mcd_compact_prompt(*args, **kwargs),
            MCD_REASONING_GUIDANCE,
        )

    def make_mcd_reasoning_followup_prompt(*args: Any, **kwargs: Any) -> str:
        return inject_guidance_before_context(
            original_mcd_followup_prompt(*args, **kwargs),
            MCD_REASONING_GUIDANCE,
        )

    def make_kb_prompt_with_guidance(prompt: str) -> str:
        prompt = inject_guidance_before_context(prompt, REASONING_GUIDANCE)
        return (
            f"{prompt}\n\n"
            "Action-selection reminder: when the question names an exact source ID, table field, or calculation over "
            "table fields, the next action must retrieve those exact row fields with one table or SQL tool before any "
            "final answer. Do not start with read_text or engineering_math when source-row values are still missing; "
            "text and math references can follow after the source row if they are still needed. If current state has "
            "only prose observations plus ignored or provisional row values, call a table or SQL tool now. "
            "Response-format reminder: return exactly one JSON object and no prose. If you need data, return only "
            '{"tool":"tool_name","args":{...}}. If you know the answer from successful observations, return only '
            '{"answer":"..."}. Do not include a draft answer with a tool call.'
        )

    def make_kb_reasoning_prompt(*args: Any, **kwargs: Any) -> str:
        return make_kb_prompt_with_guidance(original_kb_agent_prompt(*args, **kwargs))

    def make_kb_reasoning_compact_prompt(*args: Any, **kwargs: Any) -> str:
        return make_kb_prompt_with_guidance(original_kb_compact_prompt(*args, **kwargs))

    mcd_eval.make_mcd_agent_prompt = make_mcd_reasoning_prompt
    mcd_eval.make_mcd_agent_compact_prompt = make_mcd_reasoning_compact_prompt
    mcd_eval.make_mcd_agent_followup_prompt = make_mcd_reasoning_followup_prompt
    folder_eval.make_kb_agent_prompt = make_kb_reasoning_prompt
    folder_eval.make_kb_agent_compact_prompt = make_kb_reasoning_compact_prompt


def make_output_dir(results_root: Path) -> Path:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    for suffix in ["", *[f"_{index:02d}" for index in range(1, 100)]]:
        output_dir = results_root / f"run_{timestamp}{suffix}"
        try:
            output_dir.mkdir(parents=True, exist_ok=False)
            return output_dir
        except FileExistsError:
            continue
    raise RuntimeError(f"Could not create a unique output directory under {results_root}")


def run_mcd_mode(
    *,
    mcd_path: Path,
    mcd_summary_text: str,
    questions: list[dict[str, Any]],
    config: ProviderConfig,
    args: argparse.Namespace,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    mcd_config = to_mcd_config(config)
    for index, question in enumerate(questions, start=1):
        started = time.perf_counter()
        answer, metadata, trace, error = mcd_eval.run_mcd_agent_question(
            mcd_path=mcd_path,
            mcd_summary_text=mcd_summary_text,
            provider=config.name,
            model=config.model,
            question=question,
            args=args,
        )
        row = {
            "mode": "mcd",
            "dataset": "mcd",
            "mcd_path": str(mcd_path),
            "provider": config.name,
            "model": config.model,
            "question_index": index,
            "question_id": question["id"],
            "family_id": question.get("family_id"),
            "question": question["prompt"],
            "expected_contains": question["expected_contains"],
            "reference_answer": question.get("reference_answer"),
            "reference_missing_expected_contains": question.get("_reference_missing_expected_contains"),
            "answer": answer,
            "score": None,
            "error": error,
            "metadata": metadata,
            "trace": trace,
            "tool_calls": mcd_eval.tool_calls_from_trace(trace),
            "elapsed_seconds": round(time.perf_counter() - started, 3),
        }
        row["score"] = mcd_eval.score_or_none(answer, question, error, args.dry_run, args, mcd_config)
        rows.append(row)
        print(f"{config.name} mcd {index}/{len(questions)} {question['id']}: {mcd_eval.status_label(row)}", flush=True)
    return rows


def run_folder_mode(
    *,
    mode: str,
    questions: list[dict[str, Any]],
    config: ProviderConfig,
    args: argparse.Namespace,
) -> list[dict[str, Any]]:
    if mode == "connected":
        target = folder_eval.DatasetTarget("connected", args.connected_dir, use_manifest=True)
    elif mode == "disconnected":
        target = folder_eval.DatasetTarget("disconnected", args.disconnected_dir, use_manifest=False)
    else:
        raise ValueError(f"Unsupported folder mode: {mode}")

    rows = folder_eval.run_dataset(
        target=target,
        questions=questions,
        config=to_folder_config(config),
        args=args,
    )
    for row in rows:
        row["mode"] = mode
        row["reference_missing_expected_contains"] = next(
            (
                question.get("_reference_missing_expected_contains")
                for question in questions
                if question["id"] == row["question_id"]
            ),
            None,
        )
    return rows


def passed(row: dict[str, Any] | None) -> bool:
    return bool(row and row.get("score") and row["score"].get("passed"))


def status_label(row: dict[str, Any] | None) -> str:
    if not row:
        return "n/a"
    if row.get("error"):
        return "ERROR"
    if row.get("score") is None:
        return "DRY" if row.get("metadata", {}).get("dry_run") else "UNSCORED"
    return "PASS" if passed(row) else "FAIL"


def symbol(row: dict[str, Any] | None) -> str:
    if not row:
        return "n/a"
    if row.get("error"):
        return "ERR"
    if row.get("score") is None:
        return "DRY" if row.get("metadata", {}).get("dry_run") else "UNS"
    return "PASS" if passed(row) else "FAIL"


def extract_json_objects(text: str) -> list[dict[str, Any]]:
    decoder = json.JSONDecoder()
    objects: list[dict[str, Any]] = []
    index = 0
    while index < len(text):
        start = text.find("{", index)
        if start == -1:
            break
        try:
            value, end = decoder.raw_decode(text[start:])
        except json.JSONDecodeError:
            index = start + 1
            continue
        if isinstance(value, dict):
            objects.append(value)
        index = start + max(end, 1)
    return objects


def trace_response_diagnostics(trace: list[dict[str, Any]]) -> dict[str, int]:
    multi_object_steps = 0
    ignored_response_objects = 0
    ignored_answer_objects = 0
    for item in trace:
        objects = extract_json_objects(str(item.get("raw") or ""))
        if len(objects) <= 1:
            continue
        multi_object_steps += 1
        ignored_objects = objects[1:]
        ignored_response_objects += len(ignored_objects)
        ignored_answer_objects += sum(1 for value in ignored_objects if "answer" in value)
    return {
        "multi_object_steps": multi_object_steps,
        "ignored_response_objects": ignored_response_objects,
        "ignored_answer_objects": ignored_answer_objects,
    }


def rows_response_diagnostics(rows: list[dict[str, Any]]) -> dict[str, int]:
    totals = {
        "rows_with_multi_object_steps": 0,
        "multi_object_steps": 0,
        "ignored_response_objects": 0,
        "ignored_answer_objects": 0,
    }
    for row in rows:
        diagnostics = trace_response_diagnostics(row.get("trace") or [])
        if diagnostics["multi_object_steps"]:
            totals["rows_with_multi_object_steps"] += 1
        for key in ("multi_object_steps", "ignored_response_objects", "ignored_answer_objects"):
            totals[key] += diagnostics[key]
    return totals


def tool_call_distribution(rows: list[dict[str, Any]]) -> dict[str, int]:
    distribution: dict[str, int] = {}
    for row in rows:
        calls = str(int(row.get("tool_calls") or 0))
        distribution[calls] = distribution.get(calls, 0) + 1
    return dict(sorted(distribution.items(), key=lambda item: int(item[0])))


def format_tool_call_distribution(distribution: dict[str, int]) -> str:
    if not distribution:
        return "n/a"
    return ", ".join(f"{calls}: {count}" for calls, count in distribution.items())


def mode_summary(rows: list[dict[str, Any]], provider: str, mode: str, model: str) -> dict[str, Any]:
    scored = sum(1 for row in rows if row.get("score") is not None)
    passed_count = sum(1 for row in rows if passed(row))
    elapsed = sum(float(row.get("elapsed_seconds") or 0.0) for row in rows)
    tool_calls = mcd_eval.tool_calls_from_rows(rows)
    tokens = mcd_eval.token_usage_from_rows(rows)
    response_diagnostics = rows_response_diagnostics(rows)
    return {
        "provider": provider,
        "model": model,
        "mode": mode,
        "total": len(rows),
        "scored": scored,
        "passed": passed_count,
        "failed": scored - passed_count,
        "errors": sum(1 for row in rows if row.get("error")),
        "pass_rate": passed_count / scored if scored else 0.0,
        "elapsed_seconds": round(elapsed, 3),
        "avg_elapsed_seconds": round(elapsed / len(rows), 3) if rows else 0.0,
        "tool_calls": tool_calls,
        "avg_tool_calls": round(tool_calls / len(rows), 2) if rows else 0.0,
        "tool_call_distribution": tool_call_distribution(rows),
        "response_diagnostics": response_diagnostics,
        "token_usage": tokens,
    }


def write_run_config(
    *,
    path: Path,
    args: argparse.Namespace,
    modes: list[str],
    configs: list[ProviderConfig],
    question_count: int,
    created_at: str,
) -> None:
    plain_eval.write_json(
        path,
        {
            "created_at": created_at,
            "providers": [config.__dict__ for config in configs],
            "modes": modes,
            "mcd_path": str(args.mcd_path),
            "connected_dir": str(args.connected_dir),
            "disconnected_dir": str(args.disconnected_dir),
            "question_file": str(args.question_file),
            "questions": args.questions,
            "question_count": question_count,
            "scoring_mode": args.scoring_mode,
            "judge_provider": (
                [judge_provider_config(args, config).__dict__ for config in configs]
                if args.scoring_mode == "llm_judge"
                else None
            ),
            "judge_max_output_tokens": args.judge_max_output_tokens,
            "judge_temperature": args.judge_temperature,
            "judge_timeout_seconds": args.judge_timeout_seconds,
            "judge_retries": args.judge_retries,
            "max_tool_steps": args.max_tool_steps,
            "mcd_mcp": args.mcd_mcp,
            "mcd_mcp_status": mcd_eval.mcd_mcp_status(args.mcd_mcp),
            "mcd_cli": args.mcd_cli,
            "mcd_cli_status": mcd_eval.mcd_cli_status(args.mcd_cli),
            "mcp_timeout_seconds": args.mcp_timeout_seconds,
            "cli_timeout_seconds": args.cli_timeout_seconds,
            "python_timeout_seconds": args.python_timeout_seconds,
            "max_observation_chars": args.max_observation_chars,
            "max_output_tokens": args.max_output_tokens,
            "temperature": args.temperature,
            "timeout_seconds": args.timeout_seconds,
            "retries": args.retries,
            "openai_stateful_responses": args.openai_stateful_responses,
            "dry_run": args.dry_run,
            "tokenizer": {"summary": plain_eval.TOKENIZER_SUMMARY, **plain_eval.TOKENIZER_INFO},
            "prompt_profile": "reasoning_questions",
        },
    )


def write_summary_markdown(
    *,
    path: Path,
    created_at: str,
    args: argparse.Namespace,
    modes: list[str],
    questions: list[dict[str, Any]],
    summaries: list[dict[str, Any]],
    rows_by_key: dict[tuple[str, str], list[dict[str, Any]]],
) -> None:
    lines = [
        "# Reasoning Questions Evaluation",
        "",
        f"- Created at: `{created_at}`",
        f"- Question file: `{args.question_file}`",
        f"- Question count: `{len(questions)}`",
        f"- Modes: `{', '.join(modes)}`",
        f"- Scoring mode: `{args.scoring_mode}`",
        f"- Judge provider: `{args.judge_provider if args.scoring_mode == 'llm_judge' else 'n/a'}`",
        f"- Judge model override: `{args.judge_model or 'n/a'}`",
        f"- Token usage includes judge calls: `{args.scoring_mode == 'llm_judge'}`",
        "- Timing rows exclude judge latency; judge latency is stored in `score.judge_elapsed_seconds`.",
        "",
        "| Provider | Mode | Model | Passed | Failed | Scored | Total | Pass rate | Errors |",
        "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for item in summaries:
        lines.append(
            f"| {item['provider']} | {item['mode']} | `{item['model']}` | {item['passed']} | "
            f"{item['failed']} | {item['scored']} | {item['total']} | {item['pass_rate']:.1%} | {item['errors']} |"
        )

    lines.extend(
        [
            "",
            "| Provider | Mode | Input tokens | Output tokens | Total tokens | Tool calls | Avg calls | Total seconds |",
            "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for item in summaries:
        tokens = item["token_usage"]
        lines.append(
            f"| {item['provider']} | {item['mode']} | {tokens['input_tokens']:,} | "
            f"{tokens['output_tokens']:,} | {tokens['total_tokens']:,} | {item['tool_calls']} | "
            f"{item['avg_tool_calls']:.2f} | {item['elapsed_seconds']:.1f} sec |"
        )

    lines.extend(
        [
            "",
            "## Tool Call Diagnostics",
            "",
            "Tool distribution is `tool calls per question: question count`. Ignored response objects are extra JSON "
            "objects emitted after the first executable object in the same model response; only the first object is "
            "executed by the harness.",
            "",
            "| Provider | Mode | Tool distribution | Rows with extra JSON | Extra JSON objects | Ignored answer objects |",
            "| --- | --- | --- | ---: | ---: | ---: |",
        ]
    )
    for item in summaries:
        diagnostics = item["response_diagnostics"]
        lines.append(
            f"| {item['provider']} | {item['mode']} | "
            f"`{format_tool_call_distribution(item['tool_call_distribution'])}` | "
            f"{diagnostics['rows_with_multi_object_steps']} | "
            f"{diagnostics['ignored_response_objects']} | "
            f"{diagnostics['ignored_answer_objects']} |"
        )

    for provider in sorted({key[0] for key in rows_by_key}):
        lines.extend(
            [
                "",
                f"## {provider} Question Matrix",
                "",
                "| # | Question ID | " + " | ".join(modes) + " |",
                "| ---: | --- | " + " | ".join("---" for _ in modes) + " |",
            ]
        )
        for index, question in enumerate(questions, start=1):
            cells = []
            for mode in modes:
                rows = rows_by_key.get((provider, mode), [])
                row = next((item for item in rows if item["question_id"] == question["id"]), None)
                cells.append(symbol(row))
            lines.append(f"| {index} | `{question['id']}` | " + " | ".join(cells) + " |")

    reference_warnings = [
        (question["id"], question.get("_reference_missing_expected_contains"))
        for question in questions
        if question.get("_reference_missing_expected_contains")
    ]
    if reference_warnings:
        lines.extend(
            [
                "",
                "## Reference Notes",
                "",
                "Some reference answers do not literally contain every `expected_contains` string. "
                "This is allowed for reasoning questions because the LLM judge compares both fields semantically.",
                "",
            ]
        )
        for question_id, missing in reference_warnings:
            lines.append(f"- `{question_id}`: missing literal expected strings in reference: `{missing}`")

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    plain_eval.load_dotenv()
    install_reasoning_prompt_patches()
    args = parse_args()
    modes = parse_modes(args.modes)
    configs = provider_configs(args)

    # The imported folder runner expects these attributes when run_dataset is called.
    args.eval_mode = "kb_agent"
    args.batch_size = 1

    if not args.dry_run:
        env_configs = [plain_eval.ProviderConfig(config.name, config.model, config.api_key_env) for config in configs]
        if args.scoring_mode == "llm_judge":
            env_configs.extend(
                plain_eval.ProviderConfig(judge.name, judge.model, judge.api_key_env)
                for judge in (judge_provider_config(args, config) for config in configs)
            )
        plain_eval.validate_provider_env(
            list({
                (item.name, item.model, item.api_key_env): item
                for item in env_configs
            }.values())
        )

    args.mcd_path = args.mcd_path.resolve()
    args.connected_dir = args.connected_dir.resolve()
    args.disconnected_dir = args.disconnected_dir.resolve()
    args.question_file = args.question_file.resolve()
    args.results_root = args.results_root.resolve()

    if "mcd" in modes and not args.mcd_path.exists():
        raise FileNotFoundError(f"MCD package not found: {args.mcd_path}")
    if "connected" in modes and not args.connected_dir.exists():
        raise FileNotFoundError(f"Connected dataset directory not found: {args.connected_dir}")
    if "disconnected" in modes and not args.disconnected_dir.exists():
        raise FileNotFoundError(f"Disconnected dataset directory not found: {args.disconnected_dir}")

    questions = plain_eval.read_jsonl(args.question_file)
    validate_reasoning_questions(questions, args.question_file)
    if args.questions is not None:
        if args.questions < 1:
            raise ValueError("--questions must be a positive integer.")
        questions = questions[: args.questions]

    output_dir = make_output_dir(args.results_root)
    created_at = datetime.now().isoformat(timespec="seconds")
    write_run_config(
        path=output_dir / "run_config.json",
        args=args,
        modes=modes,
        configs=configs,
        question_count=len(questions),
        created_at=created_at,
    )

    mcd_summary_text = mcd_eval.build_mcd_summary(args.mcd_path) if "mcd" in modes else ""
    all_rows: list[dict[str, Any]] = []
    rows_by_key: dict[tuple[str, str], list[dict[str, Any]]] = {}
    summaries: list[dict[str, Any]] = []

    for config in configs:
        for mode in modes:
            if mode == "mcd":
                rows = run_mcd_mode(
                    mcd_path=args.mcd_path,
                    mcd_summary_text=mcd_summary_text,
                    questions=questions,
                    config=config,
                    args=args,
                )
            else:
                rows = run_folder_mode(mode=mode, questions=questions, config=config, args=args)

            rows_by_key[(config.name, mode)] = rows
            all_rows.extend(rows)
            summaries.append(mode_summary(rows, config.name, mode, config.model))
            plain_eval.write_jsonl(output_dir / f"{config.name}_{mode}_results.jsonl", rows)

    plain_eval.write_jsonl(output_dir / "all_results.jsonl", all_rows)
    plain_eval.write_json(output_dir / "summary.json", {"modes": summaries})
    write_summary_markdown(
        path=output_dir / "comparison.md",
        created_at=created_at,
        args=args,
        modes=modes,
        questions=questions,
        summaries=summaries,
        rows_by_key=rows_by_key,
    )

    print(f"Results written to {output_dir}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
