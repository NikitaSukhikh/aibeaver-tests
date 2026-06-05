#!/usr/bin/env python3
"""Compare MultiHiertt mini answers using packed MCD tools and original source tools."""

from __future__ import annotations

import argparse
import copy
import csv
import html
import hashlib
import json
import math
import os
import re
import string
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from html.parser import HTMLParser
from pathlib import Path
from typing import Any
from urllib.parse import urlsplit, urlunsplit


REPO_ROOT = Path(__file__).resolve().parents[2]
PLAIN_EVAL_DIR = REPO_ROOT / "tests" / "llm_plain_eval"
MCD_EVAL_DIR = REPO_ROOT / "tests" / "llm_mcd"
for import_dir in (PLAIN_EVAL_DIR, MCD_EVAL_DIR):
    sys.path.insert(0, str(import_dir))

import run_mcd_eval as mcd_eval  # noqa: E402
import run_plain_eval as plain_eval  # noqa: E402
from benchmark_validation import score_answer_llm_judge, score_answer_tolerant  # noqa: E402


DEFAULT_MCD_PATH = Path("datasets/multihiertt-mini/multihiertt-mini.mcd")
DEFAULT_ORIGINAL_DIR = Path("datasets/multihiertt-mini/original_disconnected")
DEFAULT_QUESTIONS_PATH = Path("datasets/multihiertt-mini/qa_questions_50.jsonl")
DEFAULT_ANSWERS_PATH = Path("datasets/multihiertt-mini/answers.json")
DEFAULT_RESULTS_ROOT = Path("results/multihiertt_mini_new")
DEFAULT_OPENAI_MODEL = "gpt-5.4"
DEFAULT_ANTHROPIC_MODEL = "claude-opus-4-5"
DEFAULT_XAI_MODEL = "grok-4.3"
DEFAULT_MAX_OUTPUT_TOKENS = 12000
DEFAULT_JUDGE_MAX_OUTPUT_TOKENS = 2000
PROVIDERS = ["openai", "anthropic", "xai"]
MODES = ["mcd_cli_tools", "original_tools"]
SKIPPED_MODES = {"mcd_tools": "native remote MCP mode is skipped for now; substituting mcd_cli_tools"}
MCD_MATRIX_COLUMNS = [f"c{index}" for index in range(12)]
MULTIHIERTT_PROGRAM_OPS = {"add", "subtract", "multiply", "divide", "exp"}


@dataclass(frozen=True)
class TableParse:
    rows: list[list[str]]


class SimpleTableParser(HTMLParser):
    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.rows: list[list[str]] = []
        self._current_row: list[str] | None = None
        self._current_cell: list[str] | None = None

    def handle_starttag(self, tag: str, attrs: list[tuple[str, str | None]]) -> None:
        if tag == "tr":
            self._current_row = []
        elif tag in {"td", "th"} and self._current_row is not None:
            self._current_cell = []
        elif tag == "br" and self._current_cell is not None:
            self._current_cell.append(" ")

    def handle_endtag(self, tag: str) -> None:
        if tag in {"td", "th"} and self._current_row is not None and self._current_cell is not None:
            text = " ".join("".join(self._current_cell).split())
            self._current_row.append(html.unescape(text))
            self._current_cell = None
        elif tag == "tr" and self._current_row is not None:
            if any(cell for cell in self._current_row):
                self.rows.append(self._current_row)
            self._current_row = None

    def handle_data(self, data: str) -> None:
        if self._current_cell is not None:
            self._current_cell.append(data)


def parse_html_table(markup: str) -> TableParse:
    parser = SimpleTableParser()
    parser.feed(markup)
    parser.close()
    return TableParse(rows=parser.rows)


def multihiertt_str_to_num(text: Any) -> float | str:
    """Mirror upstream MultiHiertt's permissive program numeric parser."""
    value = str(text).replace("$", "").replace(",", "").replace("-", "").replace("%", "")
    try:
        return float(value)
    except ValueError:
        if "const_" in value:
            value = value.replace("const_", "")
            if value == "m1":
                value = "-1"
            try:
                return float(value)
            except ValueError:
                return "n/a"
        return "n/a"


def multihiertt_program_tokenization(original_program: str) -> list[str]:
    program: list[str] = []
    for token in original_program.split(","):
        token = token.strip()
        current = ""
        for char in token:
            if char == ")" and current:
                program.append(current)
                current = ""
            current += char
            if char in {"(", ")"}:
                program.append(current)
                current = ""
        if current:
            program.append(current)
    program.append("EOF")
    return program


def normalize_predicted_program(value: Any) -> list[str]:
    if value in (None, "", []):
        return []
    if isinstance(value, str):
        tokens = multihiertt_program_tokenization(value)
    elif isinstance(value, list):
        tokens = [str(item) for item in value if str(item).strip()]
        if tokens and tokens[-1] != "EOF":
            tokens.append("EOF")
    else:
        return []
    return tokens


def eval_multihiertt_program(program: list[str]) -> tuple[int, float | str]:
    invalid_flag = 0
    result: float | str = "n/a"
    try:
        program = program[:-1]
        for index, token in enumerate(program):
            if index % 4 == 0 and token.strip("(") not in MULTIHIERTT_PROGRAM_OPS:
                return 1, "n/a"
            if (index + 1) % 4 == 0 and token != ")":
                return 1, "n/a"

        steps = "|".join(program).split(")")[:-1]
        results: dict[int, float] = {}
        for index, step in enumerate(steps):
            step = step.strip()
            if len(step.split("(")) > 2:
                invalid_flag = 1
                break
            operation = step.split("(")[0].strip("|").strip()
            raw_args = step.split("(")[1].strip("|").strip().split("|")
            if len(raw_args) < 2:
                invalid_flag = 1
                break

            parsed_args: list[float] = []
            for raw_arg in raw_args[:2]:
                arg = raw_arg.strip()
                if "#" in arg:
                    parsed_args.append(results[int(arg.replace("#", ""))])
                    continue
                parsed = multihiertt_str_to_num(arg)
                if parsed == "n/a":
                    invalid_flag = 1
                    break
                parsed_args.append(float(parsed))
            if invalid_flag:
                break

            left, right = parsed_args
            if operation == "add":
                result = left + right
            elif operation == "subtract":
                result = left - right
            elif operation == "multiply":
                result = left * right
            elif operation == "divide":
                result = left / right
            elif operation == "exp":
                result = left**right
            results[index] = float(result)

        if result != "n/a":
            result = round(float(result), 5)
    except Exception:  # noqa: BLE001 - upstream marks any execution issue invalid.
        invalid_flag = 1
    return invalid_flag, result


def multihiertt_remove_articles(text: str) -> str:
    return re.sub(r"\b(a|an|the)\b", " ", text, flags=re.UNICODE)


def multihiertt_white_space_fix(text: str) -> str:
    return " ".join(text.split())


def multihiertt_is_number(text: str) -> bool:
    try:
        float(text)
        return True
    except ValueError:
        return False


def multihiertt_remove_punc(text: str) -> str:
    if multihiertt_is_number(text):
        return text
    return "".join(char for char in text if char not in string.punctuation)


def multihiertt_normalize_number(text: str) -> str:
    if multihiertt_is_number(text):
        return str(float(text))
    return text


def multihiertt_normalize_answer(text: Any) -> str:
    parts = [
        multihiertt_white_space_fix(
            multihiertt_remove_articles(
                multihiertt_normalize_number(multihiertt_remove_punc(token.lower()))
            )
        )
        for token in re.split(" |-", str(text))
    ]
    return " ".join(part for part in parts if part.strip()).strip()


def multihiertt_answer_to_bags(answer: Any) -> tuple[list[str], list[set[str]]]:
    raw_spans = answer if isinstance(answer, (list, tuple)) else [answer]
    normalized_spans = [multihiertt_normalize_answer(span) for span in raw_spans]
    return normalized_spans, [set(span.split()) for span in normalized_spans]


def multihiertt_match_numbers_if_present(gold_bag: set[str], predicted_bag: set[str]) -> bool:
    gold_numbers = {word for word in gold_bag if multihiertt_is_number(word)}
    predicted_numbers = {word for word in predicted_bag if multihiertt_is_number(word)}
    return not gold_numbers or bool(gold_numbers.intersection(predicted_numbers))


def multihiertt_compute_f1(predicted_bag: set[str], gold_bag: set[str]) -> float:
    intersection = len(gold_bag.intersection(predicted_bag))
    precision = 1.0 if not predicted_bag else intersection / float(len(predicted_bag))
    recall = 1.0 if not gold_bag else intersection / float(len(gold_bag))
    if precision == 0.0 and recall == 0.0:
        return 0.0
    return (2 * precision * recall) / (precision + recall)


def multihiertt_align_bags(predicted: list[set[str]], gold: list[set[str]]) -> list[float]:
    scores = [
        [
            multihiertt_compute_f1(predicted_item, gold_item)
            if multihiertt_match_numbers_if_present(gold_item, predicted_item)
            else 0.0
            for predicted_item in predicted
        ]
        for gold_item in gold
    ]
    if not scores:
        return [0.0] * len(predicted)

    memo: dict[tuple[int, int], tuple[float, tuple[float, ...]]] = {}

    def best_assignment(gold_index: int, used_mask: int) -> tuple[float, tuple[float, ...]]:
        key = (gold_index, used_mask)
        if key in memo:
            return memo[key]
        if gold_index >= len(gold):
            result = (0.0, ())
            memo[key] = result
            return result

        best_total = -1.0
        best_values: tuple[float, ...] = ()
        for predicted_index in range(len(predicted)):
            if used_mask & (1 << predicted_index):
                continue
            suffix_total, suffix_values = best_assignment(gold_index + 1, used_mask | (1 << predicted_index))
            total = scores[gold_index][predicted_index] + suffix_total
            if total > best_total:
                best_total = total
                best_values = (scores[gold_index][predicted_index], *suffix_values)
        if not predicted or best_total < 0:
            suffix_total, suffix_values = best_assignment(gold_index + 1, used_mask)
            best_total = suffix_total
            best_values = (0.0, *suffix_values)
        result = (best_total, best_values)
        memo[key] = result
        return result

    _total, aligned_values = best_assignment(0, 0)
    max_scores = [0.0] * max(len(gold), len(predicted))
    for gold_index, value in enumerate(aligned_values):
        max_scores[gold_index] = value
    return max_scores


def multihiertt_span_selection_metrics(predicted: Any, gold: Any) -> tuple[float, float]:
    predicted_bags = multihiertt_answer_to_bags(predicted)
    gold_bags = multihiertt_answer_to_bags(gold)
    exact_match = 1.0 if set(predicted_bags[0]) == set(gold_bags[0]) and len(predicted_bags[0]) == len(gold_bags[0]) else 0.0
    f1_per_bag = multihiertt_align_bags(predicted_bags[1], gold_bags[1])
    f1 = round(sum(f1_per_bag) / len(f1_per_bag), 2) if f1_per_bag else 0.0
    return exact_match, f1


def multihiertt_evaluate_span_program_result(span_answer: Any, program_answer: Any) -> tuple[float, float]:
    span_answer = str(span_answer)
    parsed_span_answer = multihiertt_str_to_num(span_answer)
    if parsed_span_answer != "n/a":
        try:
            program_number = float(program_answer)
            span_number = float(parsed_span_answer)
        except (TypeError, ValueError):
            return 0.0, 0.0
        tolerance = min(abs(min(program_number, span_number) / 1000), 0.1)
        return (1.0, 1.0) if math.isclose(program_number, span_number, abs_tol=tolerance) else (0.0, 0.0)
    return multihiertt_span_selection_metrics(span_answer, str(program_answer))


def multihiertt_official_score(
    *,
    predicted_answer: str,
    predicted_program: Any,
    gold_answer: Any,
    gold_program: str,
) -> dict[str, Any]:
    pred_program = normalize_predicted_program(predicted_program)
    if pred_program and gold_program:
        _predicted_invalid_flag, predicted_result = eval_multihiertt_program(pred_program)
        _gold_invalid_flag, gold_result = eval_multihiertt_program(multihiertt_program_tokenization(gold_program))
        exact_match = 1.0 if predicted_result == gold_result else 0.0
        f1 = exact_match
        branch = "pred_program_gold_program"
    elif not pred_program and not gold_program:
        exact_match, f1 = multihiertt_span_selection_metrics(predicted_answer, gold_answer)
        branch = "pred_span_gold_span"
    elif not pred_program and gold_program:
        exact_match, f1 = multihiertt_evaluate_span_program_result(predicted_answer, gold_answer)
        branch = "pred_span_gold_program"
    else:
        exact_match, f1 = multihiertt_evaluate_span_program_result(gold_answer, predicted_answer)
        branch = "pred_program_gold_span"

    return {
        "passed": exact_match == 1.0,
        "exact_match": exact_match,
        "f1": f1,
        "scoring": "multihiertt_official_eval_py_compatible",
        "branch": branch,
        "predicted_program": pred_program,
        "gold_program": gold_program,
        "gold_answer": str(gold_answer),
    }


def parse_prediction_payload(parsed: dict[str, Any]) -> tuple[str, list[str]]:
    answer_value = parsed.get("predicted_ans", parsed.get("answer", ""))
    predicted_program = normalize_predicted_program(parsed.get("predicted_program", []))
    return str(answer_value).strip(), predicted_program


def multihiertt_common_reasoning_rules() -> str:
    return (
        "Use only the supplied MultiHiertt source data. The benchmark question names one example_id; keep that "
        "example id in the final answer. For financial table arithmetic, identify the relevant table section, "
        "header row, year columns, row labels, and measure columns before computing. Use source paragraphs when "
        "the required fact is stated in prose rather than in a table cell. Clean numeric text by removing `$`, "
        "`%`, commas, spaces, and parentheses before arithmetic; treat dash placeholders such as `-`, `—`, and "
        "blank cells as missing unless the table context defines them as zero. For projection/current-rate "
        "questions, compute from the visible source numbers rather than rounding to a nearby whole value. For "
        "ratio or percentage questions, include the decimal ratio and, when useful, the percent expression, for "
        "example `0.18136 (18.136%)`, so scale is unambiguous. Preserve enough decimal places for arithmetic "
        "answers instead of coarse rounding unless the question explicitly asks for rounding. For yes/no questions, "
        "answer yes or no and include the compared source values. In benchmark JSON, put the example id in "
        "`example_id` and put only the requested answer value in `predicted_ans`."
    )


@dataclass(frozen=True)
class ProviderConfig:
    name: str
    model: str
    api_key_env: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mcd-path", type=Path, default=DEFAULT_MCD_PATH)
    parser.add_argument("--original-dir", type=Path, default=DEFAULT_ORIGINAL_DIR)
    parser.add_argument(
        "--original-json",
        type=Path,
        default=None,
        help="Optional override for the original MultiHierTT JSON file. Defaults to --original-dir/dev_50.json.",
    )
    parser.add_argument("--questions-path", type=Path, default=DEFAULT_QUESTIONS_PATH)
    parser.add_argument("--answers-path", type=Path, default=DEFAULT_ANSWERS_PATH)
    parser.add_argument("--results-root", type=Path, default=DEFAULT_RESULTS_ROOT)
    parser.add_argument(
        "--modes",
        default="all",
        help=(
            "Comma-separated modes: all, mcd_cli_tools, original_tools, or any subset. "
            "mcd_cli_tools materializes packed .mcd source data with local mcd query-batch. "
            "mcd_tools/native remote MCP is skipped for now."
        ),
    )
    parser.add_argument("--providers", nargs="+", choices=PROVIDERS, default=["openai"])
    parser.add_argument("--openai-model", default=os.getenv("OPENAI_MODEL", DEFAULT_OPENAI_MODEL))
    parser.add_argument("--anthropic-model", default=os.getenv("ANTHROPIC_MODEL", DEFAULT_ANTHROPIC_MODEL))
    parser.add_argument("--xai-model", default=os.getenv("XAI_MODEL", DEFAULT_XAI_MODEL))
    parser.add_argument("--questions", type=int, default=None, help="Run only the first N questions.")
    parser.add_argument("--max-tool-steps", type=int, default=20)
    parser.add_argument(
        "--mcd-remote-mcp-url",
        default=os.getenv("MCD_REMOTE_MCP_URL"),
        help="Public HTTPS URL for the fixed-package MCD Streamable HTTP endpoint, usually ending in /mcp.",
    )
    parser.add_argument("--mcd-remote-mcp-label", default=os.getenv("MCD_REMOTE_MCP_LABEL", "multihiertt_mcd"))
    parser.add_argument("--mcd-mcp", default=os.getenv("MCD_MCP", mcd_eval.DEFAULT_MCD_MCP))
    parser.add_argument("--mcd-cli", default=os.getenv("MCD_CLI", "mcd"))
    parser.add_argument("--mcp-timeout-seconds", type=int, default=30)
    parser.add_argument("--cli-timeout-seconds", type=int, default=30)
    parser.add_argument("--python-timeout-seconds", type=int, default=30)
    parser.add_argument("--max-observation-chars", type=int, default=200000)
    parser.add_argument("--max-output-tokens", type=int, default=DEFAULT_MAX_OUTPUT_TOKENS)
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--timeout-seconds", type=int, default=120)
    parser.add_argument("--retries", type=int, default=2)
    parser.add_argument(
        "--scoring-mode",
        choices=["multihiertt", "programmatic", "llm_judge"],
        default="llm_judge",
        help=(
            "llm_judge is the default semantic evaluator; multihiertt mirrors upstream evaluate.py "
            "EM/F1 over qa.answer/qa.program; programmatic uses expected_contains."
        ),
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
    parser.add_argument("--openai-stateful-responses", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def normalize_remote_mcp_url(url: str | None) -> str | None:
    if not url:
        return None
    parsed = urlsplit(url.strip())
    path = parsed.path or "/"
    if path == "/":
        path = "/mcp"
    else:
        path = path.rstrip("/")
    return urlunsplit((parsed.scheme, parsed.netloc, path, parsed.query, parsed.fragment))


def parse_modes(value: str) -> list[str]:
    requested = [item.strip().casefold() for item in value.split(",") if item.strip()]
    if not requested or requested == ["all"]:
        return list(MODES)
    if "all" in requested:
        raise ValueError("--modes may be 'all' or a comma-separated subset, not both.")
    skipped = [item for item in requested if item in SKIPPED_MODES]
    for item in skipped:
        print(f"WARNING: skipping mode {item!r}: {SKIPPED_MODES[item]}", file=sys.stderr)
    replacements = ["mcd_cli_tools" for item in skipped if item == "mcd_tools"]
    requested = [item for item in requested if item not in SKIPPED_MODES]
    requested.extend(replacement for replacement in replacements if replacement not in requested)
    invalid = [item for item in requested if item not in MODES]
    if invalid:
        valid = ", ".join([*MODES, *SKIPPED_MODES])
        raise ValueError(f"Unknown mode(s): {', '.join(invalid)}. Valid modes: all, {valid}.")
    modes = [mode for mode in MODES if mode in requested]
    if not modes:
        raise ValueError("No active modes remain after skipping native remote MCP mode.")
    return modes


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


def load_questions(questions_path: Path, answers_path: Path) -> list[dict[str, Any]]:
    questions: list[dict[str, Any]] = []
    with questions_path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                question = json.loads(stripped)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSON on {questions_path}:{line_number}: {exc}") from exc
            for field in ("id", "family_id", "example_id", "source_uid", "prompt"):
                if not isinstance(question.get(field), str) or not question[field].strip():
                    raise ValueError(f"{questions_path}:{line_number} requires non-empty string field {field!r}.")
            questions.append(question)
    answers_payload = json.loads(answers_path.read_text(encoding="utf-8"))
    answers = {
        str(item["id"]): item
        for item in answers_payload.get("answers", [])
        if isinstance(item, dict) and item.get("id")
    }
    merged: list[dict[str, Any]] = []
    errors: list[str] = []
    seen_ids: set[str] = set()
    for index, question in enumerate(questions, start=1):
        question_id = str(question.get("id") or "")
        if not question_id:
            errors.append(f"{questions_path}:{index} missing id.")
            continue
        if question_id in seen_ids:
            errors.append(f"{questions_path}:{index} duplicate id {question_id!r}.")
        seen_ids.add(question_id)
        answer = answers.get(question_id)
        if not answer:
            errors.append(f"{questions_path}:{index} has no evaluator label in {answers_path}.")
            continue
        expected_contains = answer.get("expected_contains")
        reference_answer = answer.get("reference_answer")
        if not isinstance(expected_contains, list) or not expected_contains:
            errors.append(f"{answers_path} answer {question_id!r} requires expected_contains.")
        if not isinstance(reference_answer, str) or not reference_answer.strip():
            errors.append(f"{answers_path} answer {question_id!r} requires reference_answer.")
        gold_answer = answer.get("answer")
        gold_program = answer.get("program", "")
        if gold_answer is None:
            errors.append(f"{answers_path} answer {question_id!r} requires answer.")
        if not isinstance(gold_program, str):
            errors.append(f"{answers_path} answer {question_id!r} program must be a string when present.")
        merged.append(
            {
                **question,
                "expected_contains": expected_contains,
                "reference_answer": reference_answer,
                "gold_answer": gold_answer,
                "gold_program": gold_program,
                "question_type": str(answer.get("question_type", "")),
                "answer_label": answer,
                "evaluation_question": make_evaluation_question(question, answer),
            }
        )
    if errors:
        raise ValueError("Invalid MultiHiertt questions/answers:\n" + "\n".join(f"- {error}" for error in errors))
    return merged


def canonical_json(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def evaluation_hash(evaluation_question: dict[str, Any]) -> str:
    return hashlib.sha256(canonical_json(evaluation_question).encode("utf-8")).hexdigest()


def make_evaluation_question(question: dict[str, Any], answer: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": str(question["id"]),
        "family_id": str(question.get("family_id") or answer.get("family_id") or ""),
        "example_id": str(question["example_id"]),
        "source_uid": str(question["source_uid"]),
        "prompt": str(question["prompt"]),
        "expected_contains": [str(item) for item in answer.get("expected_contains", [])],
        "reference_answer": str(answer.get("reference_answer", "")),
        "answer": answer.get("answer"),
        "program": str(answer.get("program", "")),
        "question_type": str(answer.get("question_type", "")),
    }


def sanitize_original_record(record: dict[str, Any]) -> dict[str, Any]:
    sanitized = copy.deepcopy(record)
    sanitized.pop("qa", None)
    return sanitized


def load_original_records(original_dir: Path, original_json: Path, questions: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    if original_json.resolve().parent != original_dir.resolve():
        raise ValueError(f"Original JSON must be inside the original package directory: {original_dir}")

    records = json.loads(original_json.read_text(encoding="utf-8"))
    if not isinstance(records, list):
        raise ValueError(f"Expected {original_json} to contain a JSON array.")
    if len(records) < len(questions):
        raise ValueError(f"{original_json} has {len(records)} records, fewer than {len(questions)} questions.")

    selection_map_path = original_dir / "selection_map.csv"
    if not selection_map_path.exists():
        raise FileNotFoundError(selection_map_path)

    selection_rows: dict[str, dict[str, str]] = {}
    with selection_map_path.open("r", encoding="utf-8", newline="") as handle:
        for row in csv.DictReader(handle):
            example_id = str(row.get("example_id") or "")
            if example_id:
                selection_rows[example_id] = row

    by_example_id: dict[str, dict[str, Any]] = {}
    for example_id, selection in selection_rows.items():
        try:
            record_index = int(str(selection.get("source_record_index") or ""))
        except ValueError as exc:
            raise ValueError(f"Invalid source_record_index for {example_id} in {selection_map_path}.") from exc
        if record_index < 0 or record_index >= len(records):
            raise ValueError(f"source_record_index for {example_id} is outside {original_json}.")
        record = records[record_index]
        by_example_id[example_id] = sanitize_original_record(record)

    missing = [question["example_id"] for question in questions if question["example_id"] not in by_example_id]
    if missing:
        raise ValueError(f"Missing example IDs in {selection_map_path}: {missing}")
    return by_example_id


def make_source_prompt(question: dict[str, Any], source_payload: dict[str, Any], source_access_note: str) -> str:
    prompt_source_payload = {
        key: value
        for key, value in source_payload.items()
        if not str(key).startswith("_")
    }
    payload = {
        "example_id": question["example_id"],
        "question": question["prompt"],
        "source_record": prompt_source_payload,
    }
    return (
        "You are answering one MultiHiertt mini benchmark question in a one-shot source-tool-pack setting.\n\n"
        "Shared task rules:\n"
        f"{multihiertt_common_reasoning_rules()}\n\n"
        "Source access:\n"
        f"{source_access_note}\n\n"
        "Important orchestration rule:\n"
        "This benchmark permits exactly one model turn for this answer. You cannot actually call tools after this "
        "message. Treat the tool contracts below as a guide to how the source payload is organized, and treat the "
        "source payload as the already-materialized output of those tools.\n\n"
        "Return exactly one JSON object with this shape:\n"
        '{"example_id":"the provided example id","predicted_ans":"requested answer value only","predicted_program":[]}\n\n'
        "`predicted_program` may be a MultiHiertt program token list only if you are certain it exactly represents "
        "the computation; otherwise return an empty list and put the answer value in `predicted_ans`.\n\n"
        "Source payload:\n"
        f"{json.dumps(payload, ensure_ascii=False, indent=2)}"
    )


def original_source_note() -> str:
    return (
        "Original JSON source-tool pack. The model-visible tools are conceptual, but their data is already included "
        "below:\n"
        "- overview(): source counts and table inventory.\n"
        "- paragraphs(indexes|query|limit): paragraph records from `paragraphs`.\n"
        "- table(table_index,start_row,limit): parsed original HTML table rows from `tables`.\n"
        "- search(query,scope,limit): search across paragraphs, table cells, and descriptions.\n"
        "- cell_descriptions(cell_refs|query|limit): entries from `table_description`.\n"
        "Use only the supplied parsed original JSON source record. Do not use hidden `qa` evaluator labels or "
        "outside knowledge."
    )


def build_original_source_record(source_record: dict[str, Any], question: dict[str, Any]) -> dict[str, Any]:
    parsed_tables = []
    for table_index, markup in enumerate(source_record.get("tables", [])):
        parsed = parse_html_table(str(markup))
        parsed_tables.append(
            {
                "table_index": table_index,
                "row_count": len(parsed.rows),
                "max_column_count": max((len(row) for row in parsed.rows), default=0),
                "rows": [
                    {"row_index": row_index, "cells": row}
                    for row_index, row in enumerate(parsed.rows)
                ],
            }
        )
    return {
        "example_id": question["example_id"],
        "source_uid": question["source_uid"],
        "question": question["prompt"],
        "paragraphs": list(source_record.get("paragraphs", [])),
        "tables": parsed_tables,
        "table_description": dict(source_record.get("table_description", {})),
    }


def load_original_source_records(
    records_by_example_id: dict[str, dict[str, Any]],
    questions: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    return {
        question["example_id"]: build_original_source_record(records_by_example_id[question["example_id"]], question)
        for question in questions
    }


def sql_literal(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def compact_mcd_row_cells(row: dict[str, Any]) -> list[Any]:
    cells = [row.get(column) for column in MCD_MATRIX_COLUMNS]
    while cells and cells[-1] in (None, ""):
        cells.pop()
    return cells


def run_mcd_cli_query_batch(
    *,
    mcd_cli: str,
    mcd_path: Path,
    queries: list[str],
    timeout_seconds: int,
) -> dict[str, Any]:
    command = [mcd_cli, "query-batch"]
    for query in queries:
        command.extend(["--sql", query])
    command.append(str(mcd_path))
    started = time.perf_counter()
    completed = subprocess.run(
        command,
        cwd=str(REPO_ROOT),
        env={**os.environ, "MCD_PATH": str(mcd_path), "MCD_CLI": mcd_cli, "PYTHONIOENCODING": "utf-8"},
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout_seconds,
        check=False,
    )
    elapsed_seconds = round(time.perf_counter() - started, 3)
    if completed.returncode != 0:
        raise RuntimeError(
            f"mcd query-batch failed with exit code {completed.returncode}: {completed.stderr.strip()}"
        )
    try:
        payload = json.loads(completed.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"mcd query-batch returned non-JSON output: {completed.stdout[:500]}") from exc
    return {
        "command": command,
        "elapsed_seconds": elapsed_seconds,
        "stdout_bytes": len(completed.stdout),
        "stderr": completed.stderr,
        "payload": payload,
    }


def cli_batch_rows(batch_payload: dict[str, Any], index: int) -> list[dict[str, Any]]:
    queries = batch_payload.get("queries", [])
    if not isinstance(queries, list) or index >= len(queries):
        return []
    result = queries[index].get("result", {}) if isinstance(queries[index], dict) else {}
    rows = result.get("rows", []) if isinstance(result, dict) else []
    return [dict(row) for row in rows if isinstance(row, dict)]


def build_mcd_cli_source_record(question: dict[str, Any], batch: dict[str, Any]) -> dict[str, Any]:
    payload = batch["payload"]
    example_rows = cli_batch_rows(payload, 0)
    table_inventory_rows = cli_batch_rows(payload, 1)
    matrix_rows = cli_batch_rows(payload, 2)
    paragraph_rows = cli_batch_rows(payload, 3)
    cell_rows = cli_batch_rows(payload, 4)
    if not example_rows:
        raise ValueError(f"MCD CLI materialization returned no example row for {question['example_id']}.")

    rows_by_table: dict[int, list[dict[str, Any]]] = {}
    for row in matrix_rows:
        table_index = int(row["table_index"])
        rows_by_table.setdefault(table_index, []).append(
            {
                "row_id": row.get("row_id"),
                "row_index": row.get("row_index"),
                "cells": compact_mcd_row_cells(row),
            }
        )

    tables: list[dict[str, Any]] = []
    for table in table_inventory_rows:
        table_index = int(table["table_index"])
        tables.append(
            {
                "source_table_id": table.get("source_table_id"),
                "table_index": table_index,
                "row_count": table.get("row_count"),
                "max_column_count": table.get("max_column_count"),
                "rows": rows_by_table.get(table_index, []),
            }
        )

    cell_descriptions = [
        {
            "cell_ref": row.get("cell_ref"),
            "table_index": row.get("table_index"),
            "row_index": row.get("row_index"),
            "col_index": row.get("col_index"),
            "cell_text": row.get("cell_text"),
            "cell_description": row.get("cell_description"),
        }
        for row in cell_rows
    ]
    return {
        "source_format": "mcd_cli_query_batch",
        "example_id": question["example_id"],
        "source_uid": example_rows[0].get("source_uid") or question.get("source_uid"),
        "question": question["prompt"],
        "paragraphs": [
            {
                "paragraph_index": row.get("paragraph_index"),
                "paragraph_text": row.get("paragraph_text"),
            }
            for row in paragraph_rows
        ],
        "tables": tables,
        "cell_descriptions": cell_descriptions,
        "table_description": {
            str(row["cell_ref"]): row.get("cell_description")
            for row in cell_descriptions
            if row.get("cell_ref") and row.get("cell_description")
        },
        "_source_materialization": {
            "tool_type": "cli",
            "tool": "mcd query-batch",
            "elapsed_seconds": batch["elapsed_seconds"],
            "stdout_bytes": batch["stdout_bytes"],
            "query_count": len(batch["payload"].get("queries", [])),
        },
        "_tool_calls": 1,
    }


def mcd_cli_source_queries(example_id: str) -> list[str]:
    example = sql_literal(example_id)
    columns = ", ".join(MCD_MATRIX_COLUMNS)
    return [
        (
            "select example_id, source_uid, source_split, question "
            "from multihiertt_examples "
            f"where example_id = {example}"
        ),
        (
            "select source_table_id, table_index, row_count, max_column_count "
            "from multihiertt_source_tables "
            f"where example_id = {example} "
            "order by table_index"
        ),
        (
            f"select row_id, source_table_id, table_index, row_index, {columns} "
            "from multihiertt_table_rows "
            f"where example_id = {example} "
            "order by table_index, row_index"
        ),
        (
            "select paragraph_index, paragraph_text "
            "from multihiertt_paragraphs "
            f"where example_id = {example} "
            "order by paragraph_index"
        ),
        (
            "select cell_ref, table_index, row_index, col_index, cell_text, cell_description "
            "from multihiertt_cells "
            f"where example_id = {example} "
            "and cell_description is not null "
            "and cell_description <> '' "
            "order by table_index, row_index, col_index"
        ),
    ]


def load_mcd_cli_source_records(
    *,
    mcd_path: Path,
    questions: list[dict[str, Any]],
    args: argparse.Namespace,
) -> dict[str, dict[str, Any]]:
    records: dict[str, dict[str, Any]] = {}
    for question in questions:
        batch = run_mcd_cli_query_batch(
            mcd_cli=args.mcd_cli,
            mcd_path=mcd_path,
            queries=mcd_cli_source_queries(question["example_id"]),
            timeout_seconds=args.cli_timeout_seconds,
        )
        records[question["example_id"]] = build_mcd_cli_source_record(question, batch)
    return records


def mcd_cli_source_note() -> str:
    return (
        "MCD CLI source-tool pack. The model-visible tools are conceptual, but their data is already included "
        "below as materialized output from local `mcd query-batch`:\n"
        "- mcd query-batch: source table inventory, table rows, paragraphs, and cell descriptions for this example.\n"
        "- mcd query: exact SQL over `multihiertt_examples`, `multihiertt_source_tables`, "
        "`multihiertt_table_rows`, `multihiertt_paragraphs`, and `multihiertt_cells`.\n"
        "Use only the supplied MCD CLI source record. Reconstruct table headers from nearby rows before arithmetic; "
        "cell descriptions are hints, not hidden evaluator labels."
    )


def make_mcd_native_prompt(*, mcd_summary_text: str, question: dict[str, Any]) -> str:
    payload = {
        "id": question["id"],
        "example_id": question["example_id"],
        "source_uid": question.get("source_uid"),
        "question": question["prompt"],
    }
    return (
        "You are answering one MultiHiertt mini benchmark question using the provided native MCD MCP tools.\n\n"
        "Shared task rules:\n"
        f"{multihiertt_common_reasoning_rules()}\n\n"
        "Native tool usage:\n"
        "Use the provided MCP tools directly inside this single provider request. Use `mcd_search` for BM25 text "
        "retrieval and `mcd_query` for exact row-level values, counts, joins, and arithmetic inputs. Use "
        "`mcd_query_batch` when you need multiple SQL lookups, such as table discovery plus row retrieval plus "
        "a computed arithmetic check. Prefer `output: \"compact\"` for row-heavy SQL results. Do not emit "
        "textual tool-call JSON such as `mcp_tool`; call the native tool instead.\n\n"
        "Remote-call budget:\n"
        "Plan one broad first tool call before using tools. For most questions, make that first call a single "
        "`mcd_query_batch` containing table inventory, relevant rows, targeted paragraphs/cells, and any computed "
        "arithmetic check you can express in SQL. Use one extra targeted call only when the first compact batch "
        "does not contain enough evidence or exposes an ambiguity.\n\n"
        "MCD source-access rules:\n"
        "Always filter source queries by the provided example_id. Use `multihiertt_source_tables` to identify "
        "candidate tables, `multihiertt_table_rows` to inspect row shape and headers, `multihiertt_cells` for exact "
        "cell refs/descriptions, and `multihiertt_paragraphs` for prose facts. Use `mcd_search` when you need "
        "direct BM25 retrieval over package text, schema terms, annotations, provenance, or markdown context before "
        "choosing exact SQL filters. BM25 search is for locating relevant text; use `mcd_query` or "
        "`mcd_query_batch` for exact row-level values, counts, joins, and arithmetic inputs. If a computed SQL "
        "result is NULL, empty, failed, or "
        "contradicted by prior rows, do not answer from an earlier guess; issue a corrected query. Do arithmetic "
        "only after confirming row labels, header columns, units, signs, and missing-value conventions.\n\n"
        "Preferred first call:\n"
        "- `mcd_query_batch` with `output` set to `compact` and SQL shaped like:\n"
        "  1. select source_table_id, table_index, row_count, max_column_count from multihiertt_source_tables "
        "where example_id='<example_id>' order by table_index\n"
        "  2. select row_id, table_index, row_index, c0, c1, c2, c3, c4, c5, c6, c7, c8, c9, c10, c11 from "
        "multihiertt_table_rows where example_id='<example_id>' order by table_index, row_index\n"
        "  3. select paragraph_index, paragraph_text from multihiertt_paragraphs where example_id='<example_id>' "
        "and (lower(paragraph_text) like lower('%key term%') or lower(paragraph_text) like lower('%second term%'))\n"
        "  4. select cell_ref, table_index, row_index, col_index, cell_text, cell_description from multihiertt_cells "
        "where example_id='<example_id>' and (lower(cell_text) like lower('%key term%') or lower(cell_description) "
        "like lower('%key term%'))\n"
        "- Batch SQL call shape: {\"mcp_tool\":\"mcd_query_batch\",\"arguments\":{\"sql\":[\"select ...\", "
        "\"select ...\"],\"output\":\"compact\"}}\n"
        "- BM25 text search: {\"mcp_tool\":\"mcd_search\",\"arguments\":{\"query\":\"<example_id> <term>\","
        "\"kind\":\"markdown\",\"limit\":5}}\n"
        "The BM25 line shows intended search arguments only; use the native tool, not literal JSON.\n\n"
        "Dataset index:\n"
        f"{mcd_summary_text}\n\n"
        "Question:\n"
        f"{json.dumps(payload, ensure_ascii=False, indent=2)}\n\n"
        "Final answer format:\n"
        "Return exactly one JSON object and no prose: "
        '{"example_id":"the provided example id","predicted_ans":"requested answer value only","predicted_program":[]}'
    )


def model_question(question: dict[str, Any]) -> dict[str, str]:
    """Return only the fields needed by model-facing prompts."""
    return {
        "id": str(question["id"]),
        "family_id": str(question.get("family_id") or ""),
        "example_id": str(question["example_id"]),
        "source_uid": str(question["source_uid"]),
        "prompt": str(question["prompt"]),
    }


def score_or_none(
    answer: str,
    predicted_program: Any,
    question: dict[str, Any],
    error: str | None,
    dry_run: bool,
    args: argparse.Namespace,
    config: ProviderConfig,
) -> dict[str, Any] | None:
    if dry_run or error:
        return None
    return evaluate_answer(
        answer=answer,
        predicted_program=predicted_program,
        evaluation_question=question["evaluation_question"],
        args=args,
        config=config,
    )


def evaluate_answer(
    *,
    answer: str,
    predicted_program: Any,
    evaluation_question: dict[str, Any],
    args: argparse.Namespace,
    config: ProviderConfig,
) -> dict[str, Any]:
    if args.scoring_mode == "multihiertt":
        return multihiertt_official_score(
            predicted_answer=answer,
            predicted_program=predicted_program,
            gold_answer=evaluation_question["answer"],
            gold_program=str(evaluation_question.get("program") or ""),
        )
    if args.scoring_mode == "llm_judge":
        judge_config = judge_provider_config(args, config)
        return score_answer_llm_judge(
            answer=f"{evaluation_question['example_id']} {answer}",
            question=evaluation_question,
            provider=judge_config.name,
            model=judge_config.model,
            max_output_tokens=args.judge_max_output_tokens,
            temperature=args.judge_temperature,
            timeout_seconds=args.judge_timeout_seconds,
            retries=args.judge_retries,
        )
    programmatic_answer = f"{evaluation_question['example_id']} {answer}"
    return score_answer_tolerant(programmatic_answer, evaluation_question["expected_contains"])


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


def status_label(row: dict[str, Any]) -> str:
    if row.get("error"):
        return "ERROR"
    if row.get("score") is None:
        return "DRY" if row.get("metadata", {}).get("dry_run") else "UNSCORED"
    return "PASS" if row["score"].get("passed") else "FAIL"


MCD_REMOTE_ALLOWED_TOOLS = [
    "mcd_agent_context",
    "mcd_markdown",
    "mcd_query",
    "mcd_query_batch",
    "mcd_search",
    "mcd_table",
    "mcd_relationships",
    "mcd_annotations",
    "mcd_provenance",
    "mcd_validate",
]


def openai_remote_mcp_tool_calls(response: dict[str, Any]) -> int:
    return sum(1 for item in response.get("output", []) if item.get("type") == "mcp_call")


def compact_openai_output_items(response: dict[str, Any]) -> list[dict[str, Any]]:
    compact: list[dict[str, Any]] = []
    for item in response.get("output", []):
        item_type = item.get("type")
        if item_type == "mcp_call":
            compact.append(
                {
                    "type": item_type,
                    "name": item.get("name"),
                    "server_label": item.get("server_label"),
                    "status": item.get("status"),
                    "error": item.get("error"),
                    "arguments": item.get("arguments"),
                }
            )
        elif item_type == "message":
            compact.append({"type": item_type, "content": item.get("content")})
        elif item_type:
            compact.append({"type": item_type, "status": item.get("status")})
    return compact


def call_openai_native_mcd(
    *,
    prompt: str,
    model: str,
    remote_mcp_url: str,
    remote_mcp_label: str,
    max_output_tokens: int,
    temperature: float,
    timeout_seconds: int,
) -> tuple[str, dict[str, Any], dict[str, Any]]:
    api_key = plain_eval.require_env("OPENAI_API_KEY")
    payload = {
        "model": model,
        "input": prompt,
        "max_output_tokens": max_output_tokens,
        "temperature": temperature,
        "tools": [
            {
                "type": "mcp",
                "server_label": remote_mcp_label,
                "server_description": "Read-only tools for one fixed MultiHiertt MCD package.",
                "server_url": remote_mcp_url,
                "require_approval": "never",
                "allowed_tools": {"tool_names": MCD_REMOTE_ALLOWED_TOOLS},
            }
        ],
    }
    response, headers = plain_eval.http_json(
        "https://api.openai.com/v1/responses",
        {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        payload,
        timeout_seconds,
    )
    metadata = {
        "id": response.get("id"),
        "usage": response.get("usage"),
        "request_id": headers.get("x-request-id"),
        "remote_mcp_url": remote_mcp_url,
        "remote_mcp_label": remote_mcp_label,
        "native_remote_mcp": True,
    }
    return plain_eval.extract_openai_text(response), metadata, response


def call_openai_native_mcd_with_retries(
    *,
    prompt: str,
    model: str,
    remote_mcp_url: str,
    remote_mcp_label: str,
    max_output_tokens: int,
    temperature: float,
    timeout_seconds: int,
    retries: int,
) -> tuple[str, dict[str, Any], dict[str, Any]]:
    last_error: Exception | None = None
    for attempt in range(retries + 1):
        try:
            return call_openai_native_mcd(
                prompt=prompt,
                model=model,
                remote_mcp_url=remote_mcp_url,
                remote_mcp_label=remote_mcp_label,
                max_output_tokens=max_output_tokens,
                temperature=temperature,
                timeout_seconds=timeout_seconds,
            )
        except Exception as exc:  # noqa: BLE001
            last_error = exc
            if attempt < retries:
                time.sleep(2**attempt)
    assert last_error is not None
    raise last_error


def symbol(row: dict[str, Any] | None) -> str:
    if not row:
        return "n/a"
    if row.get("error"):
        return "ERR"
    if row.get("score") is None:
        return "DRY" if row.get("metadata", {}).get("dry_run") else "UNS"
    return "PASS" if row["score"].get("passed") else "FAIL"


def run_source_mode(
    *,
    mode: str,
    source_records_by_example_id: dict[str, dict[str, Any]],
    source_access_note: str,
    questions: list[dict[str, Any]],
    config: ProviderConfig,
    args: argparse.Namespace,
) -> list[dict[str, Any]]:
    rows = []
    for index, question in enumerate(questions, start=1):
        started = time.perf_counter()
        source_record = source_records_by_example_id[question["example_id"]]
        prompt = make_source_prompt(model_question(question), source_record, source_access_note)
        trace: list[dict[str, Any]] = []
        metadata: dict[str, Any] = {}
        answer = ""
        error = None
        if args.dry_run:
            metadata = {
                "dry_run": True,
                "token_usage": {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0},
            }
        else:
            try:
                raw, metadata = plain_eval.call_with_retries(
                    config.name,
                    prompt,
                    config.model,
                    args.max_output_tokens,
                    args.temperature,
                    args.timeout_seconds,
                    args.retries,
                )
                metadata = {**metadata, "token_usage": mcd_eval.token_usage_from_metadata(metadata)}
                parsed = plain_eval.extract_json_object(raw)
                answer, predicted_program = parse_prediction_payload(parsed)
                if not answer:
                    error = "Provider response JSON did not include a non-empty predicted_ans/answer."
                trace = [{"step": 1, "raw": raw, "parsed": parsed, "predicted_program": predicted_program}]
            except Exception as exc:  # noqa: BLE001
                error = str(exc)
        row = {
            "mode": mode,
            "provider": config.name,
            "model": config.model,
            "question_index": index,
            "question_id": question["id"],
            "example_id": question["example_id"],
            "family_id": question.get("family_id"),
            "question": question["prompt"],
            "expected_contains": question["expected_contains"],
            "reference_answer": question["reference_answer"],
            "evaluation_question": question["evaluation_question"],
            "evaluation_hash": evaluation_hash(question["evaluation_question"]),
            "answer": answer,
            "predicted_program": trace[0].get("predicted_program", []) if trace else [],
            "score": None,
            "error": error,
            "metadata": {
                **metadata,
                "source_materialization": source_record.get("_source_materialization"),
            },
            "trace": trace,
            "tool_calls": int(source_record.get("_tool_calls") or 0),
            "one_shot_tool_pack": True,
            "elapsed_seconds": round(time.perf_counter() - started, 3),
        }
        row["score"] = score_or_none(
            answer,
            row.get("predicted_program", []),
            question,
            error,
            args.dry_run,
            args,
            config,
        )
        rows.append(row)
        print(f"{config.name} {mode} {index}/{len(questions)} {question['id']}: {status_label(row)}", flush=True)
    return rows


def run_mcd_native_mode(
    *,
    mcd_summary_text: str,
    questions: list[dict[str, Any]],
    config: ProviderConfig,
    args: argparse.Namespace,
) -> list[dict[str, Any]]:
    if config.name != "openai":
        raise ValueError("mcd_tools native remote MCP mode is OpenAI-only. Use --providers openai.")
    if not args.dry_run and not args.mcd_remote_mcp_url:
        raise ValueError(
            "mcd_tools requires --mcd-remote-mcp-url for native one-shot MCP. "
            "Start tests\\multihiertt_mini\\mcd_fixed_http_server.py and expose its /mcp endpoint via HTTPS."
        )
    rows = []
    for index, question in enumerate(questions, start=1):
        started = time.perf_counter()
        prompt = make_mcd_native_prompt(mcd_summary_text=mcd_summary_text, question=model_question(question))
        metadata: dict[str, Any] = {}
        trace: list[dict[str, Any]] = []
        answer = ""
        predicted_program: list[str] = []
        tool_calls = 0
        error = None
        if args.dry_run:
            metadata = {
                "dry_run": True,
                "remote_mcp_url": args.mcd_remote_mcp_url,
                "remote_mcp_label": args.mcd_remote_mcp_label,
                "native_remote_mcp": True,
                "token_usage": {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0},
            }
        else:
            try:
                raw, metadata, response = call_openai_native_mcd_with_retries(
                    prompt=prompt,
                    model=config.model,
                    remote_mcp_url=args.mcd_remote_mcp_url,
                    remote_mcp_label=args.mcd_remote_mcp_label,
                    max_output_tokens=args.max_output_tokens,
                    temperature=args.temperature,
                    timeout_seconds=args.timeout_seconds,
                    retries=args.retries,
                )
                metadata = {**metadata, "token_usage": mcd_eval.token_usage_from_metadata(metadata)}
                parsed = plain_eval.extract_json_object(raw)
                answer, predicted_program = parse_prediction_payload(parsed)
                tool_calls = openai_remote_mcp_tool_calls(response)
                trace = [
                    {
                        "step": 1,
                        "raw": raw,
                        "parsed": parsed,
                        "predicted_program": predicted_program,
                        "openai_output": compact_openai_output_items(response),
                    }
                ]
                if not answer:
                    error = "Provider response JSON did not include a non-empty predicted_ans/answer."
            except Exception as exc:  # noqa: BLE001
                error = str(exc)
        row = {
            "mode": "mcd_tools",
            "provider": config.name,
            "model": config.model,
            "question_index": index,
            "question_id": question["id"],
            "example_id": question["example_id"],
            "family_id": question.get("family_id"),
            "question": question["prompt"],
            "expected_contains": question["expected_contains"],
            "reference_answer": question["reference_answer"],
            "evaluation_question": question["evaluation_question"],
            "evaluation_hash": evaluation_hash(question["evaluation_question"]),
            "answer": answer,
            "predicted_program": predicted_program,
            "score": None,
            "error": error,
            "metadata": metadata,
            "trace": trace,
            "tool_calls": tool_calls,
            "one_shot_native_mcp": True,
            "elapsed_seconds": round(time.perf_counter() - started, 3),
        }
        row["score"] = score_or_none(answer, predicted_program, question, error, args.dry_run, args, config)
        rows.append(row)
        print(f"{config.name} mcd_tools {index}/{len(questions)} {question['id']}: {status_label(row)}", flush=True)
    return rows


def mode_summary(rows: list[dict[str, Any]], provider: str, mode: str, model: str) -> dict[str, Any]:
    scored = sum(1 for row in rows if row.get("score") is not None)
    passed = sum(
        1
        for row in rows
        if isinstance(row.get("score"), dict) and row["score"].get("passed")
    )
    exact_match_total = sum(
        float(row["score"].get("exact_match", 1.0 if row["score"].get("passed") else 0.0))
        for row in rows
        if isinstance(row.get("score"), dict)
    )
    f1_total = sum(
        float(row["score"].get("f1", 1.0 if row["score"].get("passed") else 0.0))
        for row in rows
        if isinstance(row.get("score"), dict)
    )
    elapsed = sum(float(row.get("elapsed_seconds") or 0.0) for row in rows)
    return {
        "provider": provider,
        "mode": mode,
        "model": model,
        "total": len(rows),
        "scored": scored,
        "passed": passed,
        "failed": scored - passed,
        "errors": sum(1 for row in rows if row.get("error")),
        "pass_rate": passed / scored if scored else 0.0,
        "exact_match": exact_match_total / scored if scored else 0.0,
        "f1": f1_total / scored if scored else 0.0,
        "elapsed_seconds": round(elapsed, 3),
        "avg_elapsed_seconds": round(elapsed / len(rows), 3) if rows else 0.0,
        "tool_calls": mcd_eval.tool_calls_from_rows(rows),
        "token_usage": mcd_eval.token_usage_from_rows(rows),
    }


def write_summary(
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
        "# MultiHiertt Mini MCD CLI Tools vs Original Source Tools",
        "",
        f"- Created at: `{created_at}`",
        f"- MCD package: `{args.mcd_path}`",
        f"- Original package: `{args.original_dir}`",
        f"- Original JSON: `{args.original_json}`",
        f"- Questions: `{len(questions)}` from `{args.questions_path}`",
        f"- Evaluator labels: `{args.answers_path}`",
        "- Evaluator: shared per-question payload from `answers.json`; both modes use the same evaluator hash.",
        "- `mcd_cli_tools` materializes source data from the packed MCD file with local `mcd query-batch`, then gives the model one source-pack call.",
        "- Native remote MCP mode (`mcd_tools`) is skipped for now.",
        f"- MCD CLI: `{args.mcd_cli}`",
        f"- MCD CLI available: `{mcd_eval.mcd_cli_status(args.mcd_cli)['available_on_path_or_filesystem']}`",
        "- `original_tools` gives the model original JSON/table conceptual tool contracts plus pre-materialized parsed source data.",
        "- `Tool calls` counts local MCD CLI query-batch materialization calls for `mcd_cli_tools`; `original_tools` is one-shot and should remain zero by design.",
        f"- Modes: `{', '.join(modes)}`",
        f"- Scoring mode: `{args.scoring_mode}`",
        "",
        "| Provider | Mode | Model | EM | F1 | Passed | Failed | Scored | Total | Pass rate | Errors | Tool calls |",
        "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for item in summaries:
        lines.append(
            f"| {item['provider']} | {item['mode']} | `{item['model']}` | {item['exact_match']:.3f} | "
            f"{item['f1']:.3f} | {item['passed']} | {item['failed']} | {item['scored']} | {item['total']} | "
            f"{item['pass_rate']:.1%} | {item['errors']} | {item['tool_calls']} |"
        )
    lines.extend(
        [
            "",
            "| Provider | Mode | Input tokens | Output tokens | Total tokens | Total seconds | Avg seconds |",
            "| --- | --- | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for item in summaries:
        tokens = item["token_usage"]
        lines.append(
            f"| {item['provider']} | {item['mode']} | {tokens['input_tokens']:,} | "
            f"{tokens['output_tokens']:,} | {tokens['total_tokens']:,} | "
            f"{item['elapsed_seconds']:.1f} | {item['avg_elapsed_seconds']:.1f} |"
        )
    for provider in sorted({key[0] for key in rows_by_key}):
        lines.extend(["", f"## {provider} Matrix", "", "| # | Question ID | " + " | ".join(modes) + " |"])
        lines.append("| ---: | --- | " + " | ".join("---" for _ in modes) + " |")
        for index, question in enumerate(questions, start=1):
            cells = []
            for mode in modes:
                rows = rows_by_key.get((provider, mode), [])
                row = next((item for item in rows if item["question_id"] == question["id"]), None)
                cells.append(symbol(row))
            lines.append(f"| {index} | `{question['id']}` | " + " | ".join(cells) + " |")
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    plain_eval.load_dotenv()
    args = parse_args()
    args.mcd_remote_mcp_url = normalize_remote_mcp_url(args.mcd_remote_mcp_url)
    modes = parse_modes(args.modes)
    configs = provider_configs(args)

    if not args.dry_run:
        env_configs = [plain_eval.ProviderConfig(config.name, config.model, config.api_key_env) for config in configs]
        if args.scoring_mode == "llm_judge":
            env_configs.extend(
                plain_eval.ProviderConfig(judge.name, judge.model, judge.api_key_env)
                for judge in (judge_provider_config(args, config) for config in configs)
            )
        plain_eval.validate_provider_env(
            list({(item.name, item.model, item.api_key_env): item for item in env_configs}.values())
        )

    args.mcd_path = args.mcd_path.resolve()
    args.original_dir = args.original_dir.resolve()
    args.original_json = (args.original_json or (args.original_dir / "dev_50.json")).resolve()
    args.questions_path = args.questions_path.resolve()
    args.answers_path = args.answers_path.resolve()
    args.results_root = args.results_root.resolve()
    for path in (args.questions_path, args.answers_path):
        if not path.exists():
            raise FileNotFoundError(path)
    if "mcd_cli_tools" in modes and not args.mcd_path.exists():
        raise FileNotFoundError(args.mcd_path)
    if "mcd_cli_tools" in modes and not mcd_eval.mcd_cli_status(args.mcd_cli)["available_on_path_or_filesystem"]:
        raise FileNotFoundError(f"MCD CLI not found: {args.mcd_cli}")
    if "original_tools" in modes:
        if not args.original_dir.exists():
            raise FileNotFoundError(args.original_dir)
        if not args.original_json.exists():
            raise FileNotFoundError(args.original_json)

    questions = load_questions(args.questions_path, args.answers_path)
    if args.questions is not None:
        if args.questions < 1:
            raise ValueError("--questions must be a positive integer.")
        questions = questions[: args.questions]

    mcd_cli_source_records_by_example_id = (
        load_mcd_cli_source_records(mcd_path=args.mcd_path, questions=questions, args=args)
        if "mcd_cli_tools" in modes
        else {}
    )
    original_records_by_example_id = (
        load_original_records(args.original_dir, args.original_json, questions)
        if "original_tools" in modes
        else {}
    )
    original_source_records_by_example_id = (
        load_original_source_records(original_records_by_example_id, questions)
        if "original_tools" in modes
        else {}
    )
    output_dir = make_output_dir(args.results_root)
    created_at = datetime.now().isoformat(timespec="seconds")
    plain_eval.write_json(
        output_dir / "run_config.json",
        {
            "created_at": created_at,
            "providers": [config.__dict__ for config in configs],
            "modes": modes,
            "skipped_modes": SKIPPED_MODES,
            "mcd_path": str(args.mcd_path),
            "original_dir": str(args.original_dir),
            "original_json": str(args.original_json),
            "questions_path": str(args.questions_path),
            "answers_path": str(args.answers_path),
            "question_count": len(questions),
            "shared_evaluator": {
                "scoring_mode": args.scoring_mode,
                "answers_path": str(args.answers_path),
                "evaluation_hashes": {
                    question["id"]: evaluation_hash(question["evaluation_question"])
                    for question in questions
                },
                "note": "Both mcd and original modes call the same evaluator with the same per-question payload.",
            },
            "scoring_mode": args.scoring_mode,
            "multihiertt_official_scoring": {
                "upstream_repo": "https://github.com/psunlpgroup/MultiHiertt",
                "upstream_commit": "45bd9ccdf3142ea059bd5e69c0afb83437fa539c",
                "logic": "Compatible with evaluate.py: program execution EM/F1 for predicted_program, DROP-style span EM/F1 for span answers, and span-vs-program numeric bridge.",
            },
            "judge_provider": args.judge_provider,
            "judge_model": args.judge_model,
            "mode_profiles": {
                "mcd_cli_tools": (
                    "single model call with MCD source data pre-materialized by local `mcd query-batch`; "
                    "native remote MCP mode is skipped"
                ),
                "original_tools": (
                    "single model call with original JSON conceptual tools and pre-materialized parsed "
                    "paragraph/table/cell-description payload"
                ),
            },
            "max_tool_steps": args.max_tool_steps,
            "mcd_remote_mcp_url": args.mcd_remote_mcp_url,
            "mcd_remote_mcp_label": args.mcd_remote_mcp_label,
            "mcd_mcp": args.mcd_mcp,
            "mcd_mcp_status": mcd_eval.mcd_mcp_status(args.mcd_mcp),
            "mcd_cli": args.mcd_cli,
            "mcd_cli_status": mcd_eval.mcd_cli_status(args.mcd_cli),
            "max_observation_chars": args.max_observation_chars,
            "max_output_tokens": args.max_output_tokens,
            "temperature": args.temperature,
            "dry_run": args.dry_run,
            "prompt_profile": "multihiertt_mcd_cli_source_tools_vs_original_source_tools",
        },
    )

    all_rows: list[dict[str, Any]] = []
    summaries: list[dict[str, Any]] = []
    rows_by_key: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for config in configs:
        for mode in modes:
            if mode == "mcd_cli_tools":
                rows = run_source_mode(
                    mode="mcd_cli_tools",
                    source_records_by_example_id=mcd_cli_source_records_by_example_id,
                    source_access_note=mcd_cli_source_note(),
                    questions=questions,
                    config=config,
                    args=args,
                )
            else:
                rows = run_source_mode(
                    mode="original_tools",
                    source_records_by_example_id=original_source_records_by_example_id,
                    source_access_note=original_source_note(),
                    questions=questions,
                    config=config,
                    args=args,
                )
            rows_by_key[(config.name, mode)] = rows
            all_rows.extend(rows)
            summaries.append(mode_summary(rows, config.name, mode, config.model))
            plain_eval.write_jsonl(output_dir / f"{config.name}_{mode}_results.jsonl", rows)

    plain_eval.write_jsonl(output_dir / "all_results.jsonl", all_rows)
    plain_eval.write_json(output_dir / "summary.json", {"modes": summaries})
    write_summary(
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
