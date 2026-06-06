#!/usr/bin/env python3
"""Evaluate MultiHierTT mini using only original plain source files plus a neutral harness."""

from __future__ import annotations

import argparse
import ast
import copy
import csv
import html
import hashlib
import json
import math
import os
import re
import string
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from html.parser import HTMLParser
from pathlib import Path
from typing import Any


REPO_ROOT = Path(__file__).resolve().parents[2]
PLAIN_EVAL_DIR = REPO_ROOT / "tests" / "llm_plain_eval"
sys.path.insert(0, str(PLAIN_EVAL_DIR))

import run_plain_eval as plain_eval  # noqa: E402
from benchmark_validation import score_answer_llm_judge, score_answer_tolerant  # noqa: E402


DEFAULT_ORIGINAL_DIR = Path("datasets/multihiertt-mini/original_disconnected")
DEFAULT_ORIGINAL_MD_CSV_DIR = Path("datasets/multihiertt-mini/original_md_csv")
DEFAULT_QUESTIONS_PATH = Path("datasets/multihiertt-mini/qa_questions_50.jsonl")
DEFAULT_ANSWERS_PATH = Path("datasets/multihiertt-mini/answers.json")
DEFAULT_RESULTS_ROOT = Path("results/multihiertt_mini_original")
DEFAULT_OPENAI_MODEL = "gpt-5.4"
DEFAULT_ANTHROPIC_MODEL = "claude-opus-4-5"
DEFAULT_XAI_MODEL = "grok-4.3"
DEFAULT_MAX_OUTPUT_TOKENS = 12000
DEFAULT_JUDGE_MAX_OUTPUT_TOKENS = 2000
PROVIDERS = ["openai", "anthropic", "xai"]
MODES = ["plain_raw", "plain_chunked", "harness_plain_raw", "tools_plain_raw"]
MODE_ALIASES = {
    "plain_source": "plain_raw",
    "json_source": "plain_chunked",
    "harnessed_plain": "harness_plain_raw",
    "harnessed_tools": "tools_plain_raw",
    "herness_plain_raw": "harness_plain_raw",
    "tolls_plain_raw": "tools_plain_raw",
}
MULTIHIERTT_PROGRAM_OPS = {"add", "subtract", "multiply", "divide", "exp"}


@dataclass(frozen=True)
class ProviderConfig:
    name: str
    model: str
    api_key_env: str


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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--original-dir", type=Path, default=DEFAULT_ORIGINAL_DIR)
    parser.add_argument(
        "--original-json",
        type=Path,
        default=None,
        help="Optional override for original MultiHierTT JSON. Defaults to --original-dir/dev_50.json.",
    )
    parser.add_argument(
        "--original-md-csv-dir",
        type=Path,
        default=DEFAULT_ORIGINAL_MD_CSV_DIR,
        help="Prebuilt plain markdown/CSV source directory used by harness_plain_raw.",
    )
    parser.add_argument("--questions-path", type=Path, default=DEFAULT_QUESTIONS_PATH)
    parser.add_argument("--answers-path", type=Path, default=DEFAULT_ANSWERS_PATH)
    parser.add_argument("--results-root", type=Path, default=DEFAULT_RESULTS_ROOT)
    parser.add_argument(
        "--modes",
        nargs="+",
        default="all",
        help="Comma-separated modes: all, plain_raw, plain_chunked, harness_plain_raw, tools_plain_raw.",
    )
    parser.add_argument(
        "--providers",
        nargs=1,
        choices=PROVIDERS,
        default=["openai"],
        metavar="PROVIDER",
        help="Provider to run. Run the script once per provider for cross-provider comparisons.",
    )
    parser.add_argument("--openai-model", default=os.getenv("OPENAI_MODEL", DEFAULT_OPENAI_MODEL))
    parser.add_argument("--anthropic-model", default=os.getenv("ANTHROPIC_MODEL", DEFAULT_ANTHROPIC_MODEL))
    parser.add_argument("--xai-model", default=os.getenv("XAI_MODEL", DEFAULT_XAI_MODEL))
    parser.add_argument("--questions", type=int, default=None, help="Run only the first N questions.")
    parser.add_argument("--max-tool-steps", type=int, default=20)
    parser.add_argument(
        "--tools-single-round",
        "--tools-single-shot",
        action="store_true",
        dest="tools_single_round",
        help=(
            "For tools_plain_raw, make one batched tool-request call, execute all requested tools, "
            "then make one final answer call. --max-tool-steps caps the batched tool-call count."
        ),
    )
    parser.add_argument("--max-observation-chars", type=int, default=60000)
    parser.add_argument("--max-output-tokens", type=int, default=DEFAULT_MAX_OUTPUT_TOKENS)
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--timeout-seconds", type=int, default=120)
    parser.add_argument("--retries", type=int, default=2)
    parser.add_argument(
        "--scoring-mode",
        choices=["multihiertt", "programmatic", "llm_judge"],
        default="programmatic",
        help="programmatic uses deterministic expected_contains scoring; llm_judge is semantic; multihiertt mirrors upstream answer/program scoring.",
    )
    parser.add_argument("--judge-provider", choices=["same", "openai", "anthropic", "xai"], default=os.getenv("JUDGE_PROVIDER", "same"))
    parser.add_argument("--judge-model", default=os.getenv("JUDGE_MODEL"))
    parser.add_argument("--judge-max-output-tokens", type=int, default=DEFAULT_JUDGE_MAX_OUTPUT_TOKENS)
    parser.add_argument("--judge-temperature", type=float, default=0.0)
    parser.add_argument("--judge-timeout-seconds", type=int, default=120)
    parser.add_argument("--judge-retries", type=int, default=2)
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def parse_modes(value: str | list[str]) -> list[str]:
    if isinstance(value, list):
        value = ",".join(value)
    value = value.strip()
    if value.startswith("[") and value.endswith("]"):
        value = value[1:-1]
    requested = [MODE_ALIASES.get(item.strip().casefold(), item.strip().casefold()) for item in value.split(",") if item.strip()]
    if not requested or requested == ["all"]:
        return list(MODES)
    if "all" in requested:
        raise ValueError("--modes may be 'all' or a comma-separated subset, not both.")
    invalid = [item for item in requested if item not in MODES]
    if invalid:
        raise ValueError(f"Unknown mode(s): {', '.join(invalid)}. Valid modes: all, {', '.join(MODES)}.")
    requested_set = set(requested)
    return [mode for mode in MODES if mode in requested_set]


def provider_configs(args: argparse.Namespace) -> list[ProviderConfig]:
    if len(args.providers) != 1:
        raise ValueError("--providers accepts exactly one provider. Run the script once per provider.")
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


def canonical_json(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), ensure_ascii=False)


def evaluation_hash(value: Any) -> str:
    return hashlib.sha256(canonical_json(value).encode("utf-8")).hexdigest()


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
        if question_id in seen_ids:
            errors.append(f"{questions_path}:{index} duplicate id {question_id!r}.")
        seen_ids.add(question_id)
        answer = answers.get(question_id)
        if not answer:
            errors.append(f"{questions_path}:{index} has no evaluator label in {answers_path}.")
            continue
        if not isinstance(answer.get("expected_contains"), list) or not answer.get("expected_contains"):
            errors.append(f"{answers_path} answer {question_id!r} requires expected_contains.")
        if not isinstance(answer.get("reference_answer"), str):
            errors.append(f"{answers_path} answer {question_id!r} requires reference_answer.")
        merged_question = dict(question)
        merged_question["expected_contains"] = [str(item) for item in answer.get("expected_contains", [])]
        merged_question["reference_answer"] = str(answer.get("reference_answer", ""))
        merged_question["evaluation_question"] = make_evaluation_question(question, answer)
        merged.append(merged_question)
    if errors:
        raise ValueError("Question/answer validation failed:\n" + "\n".join(errors))
    return merged


def sanitize_original_record(record: dict[str, Any]) -> dict[str, Any]:
    sanitized = copy.deepcopy(record)
    sanitized.pop("qa", None)
    return sanitized


def load_original_json_array(original_dir: Path, original_json: Path) -> list[dict[str, Any]]:
    if original_json.resolve().parent != original_dir.resolve():
        raise ValueError(f"Original JSON must be inside the original package directory: {original_dir}")
    records = json.loads(original_json.read_text(encoding="utf-8"))
    if not isinstance(records, list):
        raise ValueError(f"Expected {original_json} to contain a JSON array.")
    if not all(isinstance(record, dict) for record in records):
        raise ValueError(f"Expected every item in {original_json} to be a JSON object.")
    return records


def load_original_corpus_payload(original_dir: Path, original_json: Path) -> dict[str, Any]:
    records = load_original_json_array(original_dir, original_json)
    return {"records": [sanitize_original_record(record) for record in records]}


def load_original_records(original_dir: Path, original_json: Path, questions: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    records = load_original_json_array(original_dir, original_json)

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
        by_example_id[example_id] = sanitize_original_record(records[record_index])

    missing = [question["example_id"] for question in questions if question["example_id"] not in by_example_id]
    if missing:
        raise ValueError(f"Missing example IDs in {selection_map_path}: {missing}")
    return by_example_id


def multihiertt_str_to_num(text: Any) -> float | str:
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
    except Exception:
        invalid_flag = 1
    return invalid_flag, result


def multihiertt_normalize_answer(text: Any) -> str:
    def is_number(value: str) -> bool:
        try:
            float(value)
            return True
        except ValueError:
            return False

    def remove_punc(value: str) -> str:
        if is_number(value):
            return value
        return "".join(char for char in value if char not in string.punctuation)

    def normalize_number(value: str) -> str:
        if is_number(value):
            return str(float(value))
        return value

    parts = [
        " ".join(
            re.sub(r"\b(a|an|the)\b", " ", normalize_number(remove_punc(token.lower())), flags=re.UNICODE).split()
        )
        for token in re.split(" |-", str(text))
    ]
    return " ".join(part for part in parts if part.strip()).strip()


def multihiertt_answer_to_bags(answer: Any) -> tuple[list[str], list[set[str]]]:
    raw_spans = answer if isinstance(answer, (list, tuple)) else [answer]
    normalized_spans = [multihiertt_normalize_answer(span) for span in raw_spans]
    return normalized_spans, [set(span.split()) for span in normalized_spans]


def multihiertt_span_selection_metrics(predicted: Any, gold: Any) -> tuple[float, float]:
    predicted_spans, predicted_bags = multihiertt_answer_to_bags(predicted)
    gold_spans, gold_bags = multihiertt_answer_to_bags(gold)
    exact_match = 1.0 if set(predicted_spans) == set(gold_spans) and len(predicted_spans) == len(gold_spans) else 0.0
    if not gold_bags:
        return exact_match, 0.0
    scores: list[float] = []
    for gold_bag in gold_bags:
        gold_numbers = {word for word in gold_bag if is_float_text(word)}
        best = 0.0
        for predicted_bag in predicted_bags:
            predicted_numbers = {word for word in predicted_bag if is_float_text(word)}
            if gold_numbers and not gold_numbers.intersection(predicted_numbers):
                continue
            intersection = len(gold_bag.intersection(predicted_bag))
            precision = 1.0 if not predicted_bag else intersection / float(len(predicted_bag))
            recall = 1.0 if not gold_bag else intersection / float(len(gold_bag))
            best = max(best, 0.0 if precision == 0.0 and recall == 0.0 else (2 * precision * recall) / (precision + recall))
        scores.append(best)
    return exact_match, round(sum(scores) / len(scores), 2)


def is_float_text(text: str) -> bool:
    try:
        float(text)
        return True
    except ValueError:
        return False


def multihiertt_evaluate_span_program_result(span_answer: Any, program_answer: Any) -> tuple[float, float]:
    parsed_span_answer = multihiertt_str_to_num(str(span_answer))
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


def raw_benchmark_question(prompt: str) -> str:
    match = re.fullmatch(
        r"In MultiHiertt mini example MHDEV-\d+, answer the benchmark question:\s*(.+)",
        prompt.strip(),
        flags=re.IGNORECASE | re.DOTALL,
    )
    return match.group(1).strip() if match else prompt.strip()


def model_question(question: dict[str, Any], *, raw_prompt: bool = False) -> dict[str, str]:
    return {
        "id": str(question["id"]),
        "family_id": str(question.get("family_id") or ""),
        "example_id": str(question["example_id"]),
        "source_uid": str(question["source_uid"]),
        "prompt": raw_benchmark_question(str(question["prompt"])) if raw_prompt else str(question["prompt"]),
    }


def token_usage_from_metadata(metadata: dict[str, Any]) -> dict[str, int]:
    usage = metadata.get("usage")
    if not isinstance(usage, dict):
        return {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}

    def int_token(value: Any) -> int:
        try:
            return int(value or 0)
        except (TypeError, ValueError):
            return 0

    input_tokens = int_token(usage.get("input_tokens") or usage.get("prompt_tokens"))
    output_tokens = int_token(usage.get("output_tokens") or usage.get("completion_tokens"))
    input_tokens += int_token(usage.get("cache_creation_input_tokens"))
    input_tokens += int_token(usage.get("cache_read_input_tokens"))
    total_tokens = int_token(usage.get("total_tokens")) or input_tokens + output_tokens
    return {"input_tokens": input_tokens, "output_tokens": output_tokens, "total_tokens": total_tokens}


def token_usage_from_rows(rows: list[dict[str, Any]]) -> dict[str, int]:
    total = {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}
    for row in rows:
        metadata = row.get("metadata", {})
        if isinstance(metadata, dict) and isinstance(metadata.get("token_usage"), dict):
            for key in total:
                total[key] += int(metadata["token_usage"].get(key) or 0)
        score = row.get("score")
        if isinstance(score, dict) and isinstance(score.get("judge_metadata"), dict):
            judge_usage = token_usage_from_metadata(score["judge_metadata"])
            for key in total:
                total[key] += judge_usage[key]
    return total


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
    if args.scoring_mode == "multihiertt":
        evaluation_question = question["evaluation_question"]
        return multihiertt_official_score(
            predicted_answer=answer,
            predicted_program=predicted_program,
            gold_answer=evaluation_question["answer"],
            gold_program=str(evaluation_question.get("program") or ""),
        )
    candidate_answer = f"{question['example_id']} {answer}"
    if args.scoring_mode == "llm_judge":
        judge_config = judge_provider_config(args, config)
        return score_answer_llm_judge(
            answer=candidate_answer,
            question=question["evaluation_question"],
            provider=judge_config.name,
            model=judge_config.model,
            max_output_tokens=args.judge_max_output_tokens,
            temperature=args.judge_temperature,
            timeout_seconds=args.judge_timeout_seconds,
            retries=args.judge_retries,
        )
    return score_answer_tolerant(candidate_answer, question["expected_contains"])


def common_reasoning_rules() -> str:
    return (
        "Answer from the supplied original source files only. The source may contain multiple tables and paragraphs. "
        "First identify the relevant example id, table index, row labels, header rows, year columns, and units. "
        "For numbers, remove currency signs, commas, percent signs, and parentheses before arithmetic. Treat blank "
        "or dash cells as missing unless the local table context clearly defines them as zero. Do not use evaluator "
        "answers, hidden evidence, outside knowledge, or unstated assumptions."
    )


def plain_source_note() -> str:
    return (
        "The payload contains the full original raw JSON corpus, with each record's raw paragraphs and raw HTML "
        "tables preserved. It does not include evaluator answers, programs, evidence refs, selected-example excerpts, "
        "source indexes, table inventories, or question-location metadata."
    )


def json_source_note() -> str:
    return (
        "The payload contains one raw JSON source file scoped to the selected original example. The JSON file "
        "contains only paragraphs and raw HTML tables. It does not include source IDs, table descriptions, schemas, "
        "profiles, evaluator answers, programs, evidence refs, or other metadata."
    )


def harness_source_note() -> str:
    return (
        "The payload contains only raw prebuilt source files: the full main.md text and all raw CSV table files. "
        "It does not include selected-example excerpts, source indexes, table inventories, paragraph mappings, "
        "question locations, gold answers, programs, or evidence refs."
    )


def make_prompt(question: dict[str, str], source_payload: dict[str, Any], source_access_note: str) -> str:
    payload = {
        "question": question["prompt"],
        "source_payload": source_payload,
    }
    return (
        "You are answering one MultiHierTT mini benchmark question.\n\n"
        "Task rules:\n"
        f"{common_reasoning_rules()}\n\n"
        "Source access:\n"
        f"{source_access_note}\n\n"
        "Return exactly one JSON object with this shape:\n"
        '{"predicted_ans":"requested answer value only","predicted_program":[]}\n\n'
        "`predicted_program` may be a MultiHierTT program token list only if you are certain it exactly represents "
        "the computation; otherwise return an empty list and put the answer value in `predicted_ans`.\n\n"
        "Question and source payload:\n"
        f"{json.dumps(payload, ensure_ascii=False, indent=2)}"
    )


def normalize_for_match(text: Any) -> str:
    return re.sub(r"\s+", " ", str(text or "").casefold()).strip()


def _unused_looks_numeric(text: Any) -> bool:
    cleaned = str(text or "").strip().replace(",", "").replace("$", "").replace("%", "")
    cleaned = cleaned.strip("()")
    if cleaned in {"", "-", "--", "—", "n/a", "N/A"}:
        return False
    return bool(re.fullmatch(r"-?\d+(?:\.\d+)?", cleaned))


def _unused_profile_table(rows: list[list[str]]) -> dict[str, Any]:
    width = max((len(row) for row in rows), default=0)
    numeric_cells = []
    non_empty_by_row = []
    for row_index, row in enumerate(rows):
        non_empty_by_row.append(sum(1 for cell in row if str(cell).strip()))
        for col_index, cell in enumerate(row):
            if _unused_looks_numeric(cell):
                numeric_cells.append({"row_index": row_index, "col_index": col_index})
    candidate_header_rows = [
        index
        for index, row in enumerate(rows[:5])
        if any(re.search(r"\b(?:19|20)\d{2}\b", str(cell)) for cell in row) or index == 0
    ]
    row_label_preview = [
        {
            "row_index": row_index,
            "left_cells": [cell for cell in row[: min(2, len(row))] if str(cell).strip()],
        }
        for row_index, row in enumerate(rows[:30])
        if any(str(cell).strip() for cell in row[:2])
    ]
    return {
        "row_count": len(rows),
        "max_column_count": width,
        "candidate_header_rows": sorted(set(candidate_header_rows)),
        "non_empty_cells_by_row": non_empty_by_row,
        "numeric_cell_count": len(numeric_cells),
        "numeric_cells": numeric_cells[:300],
        "row_label_preview": row_label_preview,
        "notes": [
            "Coordinates are zero-based.",
            "Numeric-cell coordinates are navigation hints only; inspect the source table before calculating.",
        ],
    }


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def read_prebuilt_csv_rows(csv_text: str) -> list[list[str]]:
    return [[str(cell) for cell in row] for row in csv.reader(csv_text.splitlines())]


def prebuilt_csv_table_index(path: Path) -> int:
    match = re.search(r"_table_(\d+)\.csv$", path.name)
    if not match:
        raise ValueError(f"Unexpected prebuilt MultiHierTT CSV filename: {path.name}")
    return int(match.group(1))


def load_raw_md_csv_payload(md_csv_dir: Path) -> dict[str, Any]:
    main_path = md_csv_dir / "main.md"
    if not main_path.exists():
        raise FileNotFoundError(main_path)
    csv_paths = sorted(md_csv_dir.glob("*.csv"), key=lambda path: path.name)
    if not csv_paths:
        raise FileNotFoundError(f"No CSV files found in {md_csv_dir}.")
    files = [{"path": "main.md", "content": main_path.read_text(encoding="utf-8")}]
    files.extend({"path": path.name, "content": path.read_text(encoding="utf-8")} for path in csv_paths)
    return {"files": files}


def load_prebuilt_harness_payloads(
    *,
    md_csv_dir: Path,
    questions: list[dict[str, Any]],
    records_by_example_id: dict[str, dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    del records_by_example_id
    payload = load_raw_md_csv_payload(md_csv_dir)
    return {question["example_id"]: payload for question in questions}


def plain_source_payload(source_record: dict[str, Any]) -> dict[str, Any]:
    return {
        "paragraphs": [str(item) for item in source_record.get("paragraphs", [])],
        "tables": [str(item) for item in source_record.get("tables", [])],
    }


def json_source_payload(source_record: dict[str, Any]) -> dict[str, Any]:
    raw_source = {
        "paragraphs": [str(item) for item in source_record.get("paragraphs", [])],
        "tables": [str(item) for item in source_record.get("tables", [])],
    }
    return {
        "files": [
            {
                "path": "source.json",
                "content": json.dumps(raw_source, ensure_ascii=False, indent=2),
            }
        ]
    }


def harness_tools_source_note() -> str:
    return (
        "The model can inspect only raw source files through explicit JSON tools. The corpus starts at the full "
        "main.md plus raw CSV table files. CSV filenames must be discovered from raw text/search results or by "
        "listing raw files. Tools do not expose source profiles, table inventories, paragraph mappings, question "
        "locations, evaluator answers, programs, or evidence refs."
    )


def harness_tool_docs() -> dict[str, Any]:
    return {
        "list_files": {
            "args": {"query": "optional filename substring", "limit": "optional integer"},
            "notes": "List raw file paths in the corpus. This is a directory listing only, not a source index.",
        },
        "read_file": {
            "args": {
                "path": "main.md or a CSV filename found in raw text",
                "max_chars": "optional integer",
                "offset": "optional character offset",
                "start_line": "optional 1-based line number",
                "line_count": "optional integer",
            },
            "notes": "Read raw source file text or a line window.",
        },
        "search_text": {
            "args": {
                "query": "text",
                "path": "optional main.md or discovered CSV filename",
                "limit": "optional integer",
                "context_lines": "optional number of nearby lines",
            },
            "notes": "Rank-search raw source lines by exact match or overlapping content terms and return file paths plus context.",
        },
        "table": {
            "args": {"path": "CSV filename found in raw text", "start_row": "optional integer", "limit": "optional integer"},
            "notes": "Read a raw CSV row window. Row coordinates are zero-based.",
        },
        "find_rows": {
            "args": {"query": "text", "path": "optional discovered CSV filename", "limit": "optional integer"},
            "notes": "Find raw CSV rows whose cells contain a substring.",
        },
        "calculator": {
            "args": {
                "expression": "optional arithmetic expression such as '(2280 - 2100) / 2100'",
                "operation": "optional add|subtract|multiply|divide|ratio|percent_change|max|min|round",
                "values": "numbers or numeric strings used with operation",
                "digits": "optional integer for round",
            },
            "notes": "Calculate with source numbers after they have been observed. Supports +, -, *, /, **, and parentheses.",
        },
    }


def build_harness_tool_record(
    *,
    question: dict[str, Any],
    harness_payload: dict[str, Any],
) -> dict[str, Any]:
    del question
    files = {
        str(item["path"]): str(item["content"])
        for item in harness_payload.get("files", [])
        if isinstance(item, dict) and item.get("path") is not None
    }
    parsed_tables = []
    csv_paths = sorted(
        [path for path in files if path.endswith(".csv")],
        key=lambda path: path,
    )
    for csv_path in csv_paths:
        table_index = prebuilt_csv_table_index(Path(csv_path))
        rows = read_prebuilt_csv_rows(files[csv_path])
        parsed_tables.append(
            {
                "table_index": table_index,
                "csv": csv_path,
                "row_count": len(rows),
                "max_column_count": max((len(row) for row in rows), default=0),
                "rows": [
                    {"row_index": row_index, "cells": row}
                    for row_index, row in enumerate(rows)
                ],
            }
        )
    return {
        "tables": parsed_tables,
        "files": files,
        "bundle_dir": harness_payload.get("bundle_dir"),
    }


def bounded_limit(value: Any, default: int, maximum: int) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        parsed = default
    return max(1, min(parsed, maximum))


def resolve_harness_path(record: dict[str, Any], path: Any) -> str:
    requested = str(path or "").strip()
    files = record.get("files", {})
    if requested in files:
        return requested
    lowered = requested.casefold()
    casefold_matches = [file_path for file_path in files if file_path.casefold() == lowered]
    if len(casefold_matches) == 1:
        return str(casefold_matches[0])
    return requested


SEARCH_STOPWORDS = {
    "a",
    "an",
    "and",
    "answer",
    "benchmark",
    "by",
    "does",
    "example",
    "for",
    "from",
    "if",
    "in",
    "is",
    "it",
    "mini",
    "of",
    "on",
    "or",
    "question",
    "the",
    "to",
    "what",
    "which",
    "with",
}


def search_tokens(text: Any) -> set[str]:
    cleaned_text = re.sub(r"\bmhdev-\d{4}\b", " ", str(text or ""), flags=re.IGNORECASE)
    tokens = set()
    for token in re.findall(r"[A-Za-z0-9]+", cleaned_text.casefold()):
        if len(token) < 3 and not token.isdigit():
            continue
        if token in SEARCH_STOPWORDS:
            continue
        tokens.add(token)
        if token.endswith("s") and len(token) > 4:
            tokens.add(token[:-1])
    return tokens


def line_context(lines: list[str], line_index: int, context_lines: int) -> list[dict[str, Any]]:
    start = max(0, line_index - context_lines)
    end = min(len(lines), line_index + context_lines + 1)
    return [
        {"line": index + 1, "text": lines[index][:1000]}
        for index in range(start, end)
    ]


def harness_tool_list_files(record: dict[str, Any], args: dict[str, Any]) -> dict[str, Any]:
    files = sorted(record.get("files", {}))
    query = normalize_for_match(args.get("query"))
    if query:
        files = [path for path in files if query in normalize_for_match(path)]
    limit = bounded_limit(args.get("limit"), 100, 1000)
    selected = files[:limit]
    return {
        "tool": "list_files",
        "query": args.get("query"),
        "returned": len(selected),
        "total_matching": len(files),
        "truncated": len(selected) < len(files),
        "files": selected,
    }


def harness_tool_read_file(record: dict[str, Any], args: dict[str, Any]) -> dict[str, Any]:
    path = resolve_harness_path(record, args.get("path"))
    files = record.get("files", {})
    if path not in files:
        raise ValueError(f"Unknown harness file path: {path}")
    max_chars = bounded_limit(args.get("max_chars"), 12000, 50000)
    content = str(files[path])
    if args.get("start_line") is not None:
        lines = content.splitlines()
        start_line = max(1, int(args.get("start_line") or 1))
        line_count = bounded_limit(args.get("line_count"), 80, 500)
        selected_lines = lines[start_line - 1 : start_line - 1 + line_count]
        text = "\n".join(selected_lines)
        if len(text) > max_chars:
            text = text[:max_chars]
        return {
            "tool": "read_file",
            "path": path,
            "start_line": start_line,
            "line_count": len(selected_lines),
            "total_lines": len(lines),
            "truncated": start_line - 1 + len(selected_lines) < len(lines) or len("\n".join(selected_lines)) > max_chars,
            "text": text,
        }
    offset = max(0, int(args.get("offset") or 0))
    text = content[offset : offset + max_chars]
    return {
        "tool": "read_file",
        "path": path,
        "chars": len(content),
        "offset": offset,
        "truncated": offset + len(text) < len(content),
        "text": text,
    }


def harness_tool_search_text(record: dict[str, Any], args: dict[str, Any]) -> dict[str, Any]:
    raw_query = str(args.get("query") or "")
    normalized_query = normalize_for_match(raw_query)
    query_tokens = search_tokens(raw_query)
    if not normalized_query and not query_tokens:
        raise ValueError("search_text query is required.")
    files = record.get("files", {})
    paths = [resolve_harness_path(record, args["path"])] if args.get("path") else sorted(files)
    limit = bounded_limit(args.get("limit"), 30, 200)
    context_lines = max(0, min(int(args.get("context_lines") or 1), 10))
    matches: list[dict[str, Any]] = []
    for path in paths:
        if path not in files:
            raise ValueError(f"Unknown harness file path: {path}")
        lines = str(files[path]).splitlines()
        for line_index, line in enumerate(lines):
            line_text = normalize_for_match(line)
            exact = bool(normalized_query and normalized_query in line_text)
            overlap = sorted(query_tokens.intersection(search_tokens(line)))
            if not exact and not overlap:
                continue
            score = (1000 if exact else 0) + len(overlap)
            matches.append(
                {
                    "path": path,
                    "line": line_index + 1,
                    "score": score,
                    "match_type": "exact" if exact else "token_overlap",
                    "matched_terms": overlap,
                    "text": line[:1000],
                    "context": line_context(lines, line_index, context_lines),
                }
            )
    matches.sort(key=lambda item: (-int(item["score"]), str(item["path"]), int(item["line"])))
    selected = matches[:limit]
    return {
        "tool": "search_text",
        "query": args.get("query"),
        "returned": len(selected),
        "total_matches": len(matches),
        "matches": selected,
    }


def harness_tool_table(record: dict[str, Any], args: dict[str, Any]) -> dict[str, Any]:
    path = resolve_harness_path(record, args.get("path"))
    if not path:
        raise ValueError("table requires a CSV filename in 'path'.")
    start_row = max(0, int(args.get("start_row") or 0))
    limit = bounded_limit(args.get("limit"), 30, 300)
    table = next((item for item in record.get("tables", []) if str(item.get("csv")) == path), None)
    if table is None:
        raise ValueError(f"Unknown CSV path: {path}")
    rows = table.get("rows", [])
    selected = rows[start_row : start_row + limit]
    return {
        "tool": "table",
        "path": path,
        "start_row": start_row,
        "truncated": start_row + len(selected) < len(rows),
        "rows": selected,
    }


def harness_tool_find_rows(record: dict[str, Any], args: dict[str, Any]) -> dict[str, Any]:
    raw_query = str(args.get("query") or "")
    normalized_query = normalize_for_match(raw_query)
    query_tokens = search_tokens(raw_query)
    if not normalized_query and not query_tokens:
        raise ValueError("find_rows query is required.")
    limit = bounded_limit(args.get("limit"), 30, 200)
    requested_path = resolve_harness_path(record, args.get("path")) if args.get("path") else ""
    matches = []
    for table in record.get("tables", []):
        csv_path = str(table.get("csv"))
        if requested_path and requested_path != csv_path:
            continue
        for row in table.get("rows", []):
            row_text = normalize_for_match(" ".join(str(cell) for cell in row.get("cells", [])))
            exact = bool(normalized_query and normalized_query in row_text)
            overlap = sorted(query_tokens.intersection(search_tokens(row_text)))
            if exact or overlap:
                matches.append(
                    {
                        "path": csv_path,
                        "row_index": row["row_index"],
                        "score": (1000 if exact else 0) + len(overlap),
                        "match_type": "exact" if exact else "token_overlap",
                        "matched_terms": overlap,
                        "cells": row.get("cells", []),
                    }
                )
    matches.sort(key=lambda item: (-int(item["score"]), str(item["path"]), int(item["row_index"])))
    selected = matches[:limit]
    return {"tool": "find_rows", "query": args.get("query"), "returned": len(selected), "total_matches": len(matches), "rows": selected}


def parse_decimal_value(value: Any) -> float:
    text = str(value).strip()
    negative = text.startswith("(") and text.endswith(")")
    cleaned = text.strip("()").replace("$", "").replace(",", "").replace("%", "").strip()
    cleaned = cleaned.replace("−", "-").replace("—", "-")
    number = float(cleaned)
    return -number if negative and number > 0 else number


def calculate_expression(expression: str) -> float:
    tree = ast.parse(expression, mode="eval")

    def eval_node(node: ast.AST) -> float:
        if isinstance(node, ast.Expression):
            return eval_node(node.body)
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return float(node.value)
        if isinstance(node, ast.UnaryOp) and isinstance(node.op, (ast.UAdd, ast.USub)):
            value = eval_node(node.operand)
            return value if isinstance(node.op, ast.UAdd) else -value
        if isinstance(node, ast.BinOp):
            left = eval_node(node.left)
            right = eval_node(node.right)
            if isinstance(node.op, ast.Add):
                return left + right
            if isinstance(node.op, ast.Sub):
                return left - right
            if isinstance(node.op, ast.Mult):
                return left * right
            if isinstance(node.op, ast.Div):
                return left / right
            if isinstance(node.op, ast.Pow):
                return left**right
        raise ValueError(f"Unsupported calculator expression node: {type(node).__name__}")

    return eval_node(tree)


def format_calculator_result(value: float) -> str:
    if math.isfinite(value) and abs(value - round(value)) < 1e-12:
        return str(int(round(value)))
    text = f"{value:.12f}".rstrip("0").rstrip(".")
    return text if text else "0"


def harness_tool_calculator(args: dict[str, Any]) -> dict[str, Any]:
    if args.get("expression"):
        expression = str(args["expression"])
        result = calculate_expression(expression)
        return {
            "tool": "calculator",
            "expression": expression,
            "result": format_calculator_result(result),
            "result_number": result,
        }

    operation = str(args.get("operation") or "").casefold()
    values = [parse_decimal_value(value) for value in args.get("values", [])]
    if not operation or not values:
        raise ValueError("calculator requires either expression or operation with values.")
    if operation == "add":
        result = sum(values)
    elif operation == "subtract":
        result = values[0] - sum(values[1:])
    elif operation == "multiply":
        result = 1.0
        for value in values:
            result *= value
    elif operation in {"divide", "ratio"}:
        if len(values) != 2:
            raise ValueError("divide/ratio requires exactly two values.")
        result = values[0] / values[1]
    elif operation == "percent_change":
        if len(values) != 2:
            raise ValueError("percent_change requires [new_value, old_value].")
        result = (values[0] - values[1]) / values[1] * 100.0
    elif operation == "max":
        result = max(values)
    elif operation == "min":
        result = min(values)
    elif operation == "round":
        digits = int(args.get("digits") or 0)
        result = round(values[0], digits)
    else:
        raise ValueError(f"Unknown calculator operation: {operation}")
    return {
        "tool": "calculator",
        "operation": operation,
        "values": values,
        "result": format_calculator_result(result),
        "result_number": result,
    }


def execute_harness_tool(record: dict[str, Any], tool: str, args: dict[str, Any]) -> dict[str, Any]:
    if tool == "list_files":
        return harness_tool_list_files(record, args)
    if tool == "read_file":
        return harness_tool_read_file(record, args)
    if tool == "search_text":
        return harness_tool_search_text(record, args)
    if tool == "table":
        return harness_tool_table(record, args)
    if tool == "find_rows":
        return harness_tool_find_rows(record, args)
    if tool == "calculator":
        return harness_tool_calculator(args)
    raise ValueError(f"Unknown harness tool: {tool}")


def extract_json_objects(text: str) -> list[dict[str, Any]]:
    decoder = json.JSONDecoder()
    objects: list[dict[str, Any]] = []
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = re.sub(r"^```(?:json)?\s*", "", stripped, flags=re.IGNORECASE)
        stripped = re.sub(r"\s*```$", "", stripped)
    for match in re.finditer(r"{", stripped):
        try:
            value, _end = decoder.raw_decode(stripped[match.start() :])
        except json.JSONDecodeError:
            continue
        if isinstance(value, dict):
            objects.append(value)
    return objects


def parse_harness_action_object(action: dict[str, Any]) -> dict[str, Any]:
    if "predicted_ans" in action:
        return {"answer": str(action["predicted_ans"]), "predicted_program": normalize_predicted_program(action.get("predicted_program", []))}
    if "answer" in action:
        return {"answer": str(action["answer"]), "predicted_program": normalize_predicted_program(action.get("predicted_program", []))}
    if "tool_calls" in action:
        calls = action.get("tool_calls")
        if not isinstance(calls, list):
            raise ValueError("Tool action 'tool_calls' must be an array.")
        parsed_calls = []
        for index, call in enumerate(calls, start=1):
            if not isinstance(call, dict):
                raise ValueError(f"Tool call {index} must be an object.")
            if "tool" not in call:
                raise ValueError(f"Tool call {index} must include 'tool'.")
            args = call.get("args", {})
            if not isinstance(args, dict):
                raise ValueError(f"Tool call {index} 'args' must be an object.")
            parsed_calls.append({"tool": str(call["tool"]), "args": args})
        return {"tool_calls": parsed_calls}
    if "tool" in action:
        args = action.get("args", {})
        if not isinstance(args, dict):
            raise ValueError("Tool action 'args' must be an object.")
        return {"tool": str(action["tool"]), "args": args}
    raise ValueError("Agent response must contain either 'tool', 'answer', or 'predicted_ans'.")


def parse_harness_agent_actions(text: str) -> list[dict[str, Any]]:
    objects = extract_json_objects(text)
    if not objects:
        raise ValueError("Agent response did not contain a JSON object.")
    actions = []
    for value in objects:
        if not any(key in value for key in ("tool", "tool_calls", "answer", "predicted_ans")):
            continue
        action = parse_harness_action_object(value)
        if "tool_calls" in action:
            actions.extend(action["tool_calls"])
        else:
            actions.append(action)
    if not actions:
        raise ValueError("Agent response did not contain an executable action JSON object.")
    return actions


def parse_harness_agent_action(text: str) -> dict[str, Any]:
    actions = parse_harness_agent_actions(text)
    if not actions:
        raise ValueError("Agent response did not contain an action.")
    return actions[0]


def parse_harness_single_round_action(text: str) -> dict[str, Any]:
    objects = extract_json_objects(text)
    if not objects:
        raise ValueError("Agent response did not contain a JSON object.")
    action = objects[0]
    if "answer" in action or "predicted_ans" in action:
        return parse_harness_agent_action(text)

    tool_calls = action.get("tool_calls")
    if tool_calls is None and len(objects) > 1:
        actions = parse_harness_agent_actions(text)
        if actions and all("tool" in item for item in actions):
            return {"tool_calls": actions}
    if not isinstance(tool_calls, list) or not tool_calls:
        raise ValueError("Single-round response must contain a non-empty 'tool_calls' array.")

    parsed_calls = []
    for index, call in enumerate(tool_calls, start=1):
        if not isinstance(call, dict):
            raise ValueError(f"Tool call {index} must be an object.")
        if "tool" not in call:
            raise ValueError(f"Tool call {index} must include 'tool'.")
        call_args = call.get("args", {})
        if not isinstance(call_args, dict):
            raise ValueError(f"Tool call {index} 'args' must be an object.")
        parsed_calls.append({"tool": str(call["tool"]), "args": call_args})
    return {"tool_calls": parsed_calls}


def truncate_observation(observation: dict[str, Any], max_chars: int) -> dict[str, Any]:
    text = json.dumps(observation, ensure_ascii=False)
    if len(text) <= max_chars:
        return observation
    return {
        "truncated": True,
        "original_chars": len(text),
        "preview_json": text[:max_chars],
    }


def harness_agent_tool_calls_from_trace(trace: list[dict[str, Any]]) -> int:
    total = 0
    for item in trace:
        actions = item.get("actions")
        if isinstance(actions, list):
            total += sum(1 for action in actions if isinstance(action, dict) and action.get("tool"))
            continue
        action = item.get("action", {})
        if not isinstance(action, dict):
            continue
        if action.get("tool"):
            total += 1
        tool_calls = action.get("tool_calls")
        if isinstance(tool_calls, list):
            total += len(tool_calls)
    return total


def make_harness_agent_prompt(
    *,
    record: dict[str, Any],
    question: dict[str, Any],
    observations: list[dict[str, Any]],
) -> str:
    payload = {
        "question": question["prompt"],
    }
    del record
    return (
        "You are answering one MultiHierTT mini benchmark question using original plain-source harness tools.\n\n"
        "Task rules:\n"
        f"{common_reasoning_rules()}\n\n"
        "Source access:\n"
        f"{harness_tools_source_note()}\n\n"
        "Tool protocol:\n"
        "Return exactly one JSON object and no prose. If you need source data or arithmetic, return "
        '{"tool":"tool_name","args":{...}}. When you know the answer, return '
        '{"answer":"requested answer value only","predicted_program":[]}. '
        "Do not return a tool call and an answer in the same response. Navigate the corpus by searching for "
        "distinctive content terms from the question, using short queries and context lines to discover nearby "
        "CSV links. Do not rely on the benchmark example id to locate a file unless it appears in raw source "
        "or directory-listing output.\n\n"
        "Available harness tools:\n"
        f"{json.dumps(harness_tool_docs(), ensure_ascii=False, indent=2)}\n\n"
        "Question:\n"
        f"{json.dumps(payload, ensure_ascii=False, indent=2)}\n\n"
        "Previous tool observations:\n"
        f"{json.dumps(observations, ensure_ascii=False, indent=2)}"
    )


def make_harness_single_round_tool_prompt(
    *,
    record: dict[str, Any],
    question: dict[str, Any],
) -> str:
    payload = {
        "question": question["prompt"],
    }
    del record
    return (
        "You are answering one MultiHierTT mini benchmark question using original plain-source harness tools.\n\n"
        "Task rules:\n"
        f"{common_reasoning_rules()}\n\n"
        "Source access:\n"
        f"{harness_tools_source_note()}\n\n"
        "Single-round tool protocol:\n"
        "Return exactly one JSON object and no prose. Choose every source lookup and arithmetic helper call needed "
        "for the answer now, because there will be no additional tool-request round. Return this shape:\n"
        '{"tool_calls":[{"tool":"tool_name","args":{...}}]}\n'
        "Use multiple tool calls when needed to inspect markdown text, table windows, CSV rows, and arithmetic. "
        "Prefer short content-term searches with context lines to discover relevant raw CSV links. Do not include "
        "an answer in this tool-request response unless no tool is needed.\n\n"
        "Available harness tools:\n"
        f"{json.dumps(harness_tool_docs(), ensure_ascii=False, indent=2)}\n\n"
        "Question:\n"
        f"{json.dumps(payload, ensure_ascii=False, indent=2)}"
    )


def make_harness_single_round_answer_prompt(
    *,
    record: dict[str, Any],
    question: dict[str, Any],
    observations: list[dict[str, Any]],
) -> str:
    payload = {
        "question": question["prompt"],
    }
    del record
    return (
        "You are answering one MultiHierTT mini benchmark question from already-executed harness tool observations.\n\n"
        "Task rules:\n"
        f"{common_reasoning_rules()}\n\n"
        "Final answer protocol:\n"
        "Return exactly one JSON object and no prose. Tool use is closed; do not request another tool. "
        "Use only successful tool observations as source evidence. Return this shape:\n"
        '{"answer":"requested answer value only","predicted_program":[]}\n\n'
        "Question:\n"
        f"{json.dumps(payload, ensure_ascii=False, indent=2)}\n\n"
        "Executed tool observations:\n"
        f"{json.dumps(observations, ensure_ascii=False, indent=2)}"
    )


def run_harness_tools_single_round_question(
    *,
    record: dict[str, Any],
    question: dict[str, Any],
    config: ProviderConfig,
    args: argparse.Namespace,
) -> tuple[str, list[str], dict[str, Any], list[dict[str, Any]], str | None]:
    tool_prompt = make_harness_single_round_tool_prompt(record=record, question=question)
    if args.dry_run:
        return (
            "",
            [],
            {
                "dry_run": True,
                "tools_single_round": True,
                "token_usage": {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0},
                "prompt_chars": len(tool_prompt),
                "prompt_char_counts": {"tool_request": len(tool_prompt), "answer": 0},
            },
            [],
            None,
        )

    total_usage = {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}
    call_token_usage: list[dict[str, int]] = []
    call_metadata: list[dict[str, Any]] = []
    trace: list[dict[str, Any]] = []

    raw, metadata = plain_eval.call_with_retries(
        config.name,
        tool_prompt,
        config.model,
        args.max_output_tokens,
        args.temperature,
        args.timeout_seconds,
        args.retries,
    )
    token_usage = token_usage_from_metadata(metadata)
    call_token_usage.append(token_usage)
    call_metadata.append(metadata)
    for key in total_usage:
        total_usage[key] += token_usage[key]
    try:
        action = parse_harness_single_round_action(raw)
    except Exception as exc:
        final_metadata = {
            **metadata,
            "tools_single_round": True,
            "token_usage": total_usage,
            "call_token_usage": call_token_usage,
            "call_metadata": call_metadata,
            "prompt_chars": len(tool_prompt),
            "prompt_char_counts": {"tool_request": len(tool_prompt), "answer": 0},
        }
        trace.append({"step": 1, "round": "tool_request", "raw": raw, "error": str(exc)})
        return "", [], final_metadata, trace, f"Could not parse single-round harness tool action: {exc}"

    trace_item: dict[str, Any] = {"step": 1, "round": "tool_request", "raw": raw, "action": action}
    if "answer" in action:
        trace.append(trace_item)
        final_metadata = {
            **metadata,
            "tools_single_round": True,
            "token_usage": total_usage,
            "call_token_usage": call_token_usage,
            "call_metadata": call_metadata,
            "prompt_chars": len(tool_prompt),
            "prompt_char_counts": {"tool_request": len(tool_prompt), "answer": 0},
        }
        return action["answer"], action.get("predicted_program", []), final_metadata, trace, None

    tool_calls = action["tool_calls"]
    if len(tool_calls) > int(args.max_tool_steps):
        trace_item["error"] = f"Requested {len(tool_calls)} tool calls, above --max-tool-steps={args.max_tool_steps}."
        trace.append(trace_item)
        final_metadata = {
            **metadata,
            "tools_single_round": True,
            "token_usage": total_usage,
            "call_token_usage": call_token_usage,
            "call_metadata": call_metadata,
            "prompt_chars": len(tool_prompt),
            "prompt_char_counts": {"tool_request": len(tool_prompt), "answer": 0},
        }
        return "", [], final_metadata, trace, trace_item["error"]

    observations: list[dict[str, Any]] = []
    for call_index, call in enumerate(tool_calls, start=1):
        try:
            observation = execute_harness_tool(record, call["tool"], call["args"])
        except Exception as exc:
            observation = {"tool": call["tool"], "error": str(exc)}
        observations.append(
            {
                "step": call_index,
                "tool": call["tool"],
                "args": call["args"],
                "observation": truncate_observation(observation, int(args.max_observation_chars)),
            }
        )
    trace_item["observations"] = observations
    trace.append(trace_item)

    answer_prompt = make_harness_single_round_answer_prompt(
        record=record,
        question=question,
        observations=observations,
    )
    raw_answer, answer_metadata = plain_eval.call_with_retries(
        config.name,
        answer_prompt,
        config.model,
        args.max_output_tokens,
        args.temperature,
        args.timeout_seconds,
        args.retries,
    )
    answer_token_usage = token_usage_from_metadata(answer_metadata)
    call_token_usage.append(answer_token_usage)
    call_metadata.append(answer_metadata)
    for key in total_usage:
        total_usage[key] += answer_token_usage[key]
    final_metadata = {
        **answer_metadata,
        "tools_single_round": True,
        "token_usage": total_usage,
        "call_token_usage": call_token_usage,
        "call_metadata": call_metadata,
        "prompt_chars": len(answer_prompt),
        "prompt_char_counts": {"tool_request": len(tool_prompt), "answer": len(answer_prompt)},
    }
    try:
        answer_action = parse_harness_agent_action(raw_answer)
    except Exception as exc:
        trace.append({"step": 2, "round": "answer", "raw": raw_answer, "error": str(exc)})
        return "", [], final_metadata, trace, f"Could not parse single-round final answer: {exc}"
    answer_trace_item: dict[str, Any] = {"step": 2, "round": "answer", "raw": raw_answer, "action": answer_action}
    trace.append(answer_trace_item)
    if "answer" not in answer_action:
        return "", [], final_metadata, trace, "Final single-round response requested another tool instead of answering."
    return answer_action["answer"], answer_action.get("predicted_program", []), final_metadata, trace, None


def run_harness_tools_question(
    *,
    record: dict[str, Any],
    question: dict[str, Any],
    config: ProviderConfig,
    args: argparse.Namespace,
) -> tuple[str, list[str], dict[str, Any], list[dict[str, Any]], str | None]:
    initial_prompt = make_harness_agent_prompt(record=record, question=question, observations=[])
    if args.dry_run:
        return (
            "",
            [],
            {
                "dry_run": True,
                "token_usage": {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0},
                "prompt_chars": len(initial_prompt),
            },
            [],
            None,
        )

    observations: list[dict[str, Any]] = []
    trace: list[dict[str, Any]] = []
    total_usage = {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}
    call_token_usage: list[dict[str, int]] = []
    metadata: dict[str, Any] = {}
    tool_step = 0
    model_step = 0
    while tool_step < args.max_tool_steps:
        model_step += 1
        prompt = make_harness_agent_prompt(record=record, question=question, observations=observations)
        raw, metadata = plain_eval.call_with_retries(
            config.name,
            prompt,
            config.model,
            args.max_output_tokens,
            args.temperature,
            args.timeout_seconds,
            args.retries,
        )
        token_usage = token_usage_from_metadata(metadata)
        call_token_usage.append(token_usage)
        for key in total_usage:
            total_usage[key] += token_usage[key]
        metadata = {
            **metadata,
            "token_usage": total_usage,
            "call_token_usage": call_token_usage,
            "prompt_chars": len(prompt),
        }
        try:
            actions = parse_harness_agent_actions(raw)
        except Exception as exc:
            trace.append({"step": model_step, "raw": raw, "error": str(exc)})
            return "", [], metadata, trace, f"Could not parse harness tool action: {exc}"
        trace_item: dict[str, Any] = {"step": model_step, "raw": raw, "actions": actions}
        if actions:
            trace_item["action"] = actions[0]
        response_tool_seen = False
        executed_any_tool = False
        bundled_answers_after_tool = []
        step_observations: list[dict[str, Any]] = []
        for action_index, action in enumerate(actions, start=1):
            if "answer" in action:
                if response_tool_seen:
                    bundled_answers_after_tool.append(
                        {
                            "action_index": action_index,
                            "answer": action["answer"],
                            "ignored_because": "Answer was bundled after a tool call in the same response.",
                        }
                    )
                    continue
                trace.append(trace_item)
                return action["answer"], action.get("predicted_program", []), metadata, trace, None
            if "tool" not in action:
                continue
            response_tool_seen = True
            if tool_step >= args.max_tool_steps:
                trace_item["error"] = f"Requested more than --max-tool-steps={args.max_tool_steps} tool calls."
                trace.append(trace_item)
                return "", [], metadata, trace, trace_item["error"]
            tool_step += 1
            try:
                observation = execute_harness_tool(record, action["tool"], action["args"])
            except Exception as exc:
                observation = {"tool": action["tool"], "error": str(exc)}
            step_observation = {
                "step": tool_step,
                "model_step": model_step,
                "action_index": action_index,
                "tool": action["tool"],
                "args": action["args"],
                "observation": truncate_observation(observation, int(args.max_observation_chars)),
            }
            step_observations.append(step_observation)
            observations.append(step_observation)
            executed_any_tool = True
        if bundled_answers_after_tool:
            trace_item["ignored_bundled_answers"] = bundled_answers_after_tool
        trace_item["observations"] = step_observations
        trace.append(trace_item)
        if not executed_any_tool:
            return "", [], metadata, trace, "Harness tools agent did not provide an answer or executable tool call."
    return "", [], metadata, trace, f"Harness tools agent did not answer within {args.max_tool_steps} tool steps."


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


def symbol(row: dict[str, Any] | None) -> str:
    if not row:
        return "n/a"
    if row.get("error"):
        return "ERR"
    if row.get("score") is None:
        return "DRY" if row.get("metadata", {}).get("dry_run") else "UNS"
    return "PASS" if row["score"].get("passed") else "FAIL"


def run_mode(
    *,
    mode: str,
    records_by_example_id: dict[str, dict[str, Any]],
    original_corpus_payload: dict[str, Any],
    harness_payloads_by_example_id: dict[str, dict[str, Any]],
    harness_tool_records_by_example_id: dict[str, dict[str, Any]],
    questions: list[dict[str, Any]],
    config: ProviderConfig,
    args: argparse.Namespace,
) -> list[dict[str, Any]]:
    rows = []
    for index, question in enumerate(questions, start=1):
        started = time.perf_counter()
        trace: list[dict[str, Any]] = []
        metadata: dict[str, Any] = {}
        answer = ""
        predicted_program: list[str] = []
        error = None
        if mode == "tools_plain_raw":
            tool_runner = (
                run_harness_tools_single_round_question
                if args.tools_single_round
                else run_harness_tools_question
            )
            answer, predicted_program, metadata, trace, error = tool_runner(
                record=harness_tool_records_by_example_id[question["example_id"]],
                question=model_question(question),
                config=config,
                args=args,
            )
        else:
            if mode == "plain_raw":
                payload = original_corpus_payload
                source_note = plain_source_note()
                question_payload = model_question(question, raw_prompt=True)
            elif mode == "plain_chunked":
                payload = json_source_payload(records_by_example_id[question["example_id"]])
                source_note = json_source_note()
                question_payload = model_question(question)
            else:
                payload = harness_payloads_by_example_id[question["example_id"]]
                source_note = harness_source_note()
                question_payload = model_question(question)
            prompt = make_prompt(question_payload, payload, source_note)
            if args.dry_run:
                metadata = {
                    "dry_run": True,
                    "token_usage": {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0},
                    "prompt_chars": len(prompt),
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
                    metadata = {
                        **metadata,
                        "token_usage": token_usage_from_metadata(metadata),
                        "prompt_chars": len(prompt),
                    }
                    parsed = plain_eval.extract_json_object(raw)
                    answer, predicted_program = parse_prediction_payload(parsed)
                    if not answer:
                        error = "Provider response JSON did not include a non-empty predicted_ans/answer."
                    trace = [{"step": 1, "raw": raw, "parsed": parsed, "predicted_program": predicted_program}]
                except Exception as exc:
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
            "predicted_program": predicted_program,
            "score": None,
            "error": error,
            "metadata": metadata,
            "trace": trace,
            "tool_calls": harness_agent_tool_calls_from_trace(trace) if mode == "tools_plain_raw" else 0,
            "harness_bundle_dir": (
                harness_tool_records_by_example_id[question["example_id"]].get("bundle_dir")
                if mode == "tools_plain_raw"
                else harness_payloads_by_example_id[question["example_id"]].get("bundle_dir")
                if mode == "harness_plain_raw"
                else None
            ),
            "elapsed_seconds": round(time.perf_counter() - started, 3),
        }
        row["score"] = score_or_none(answer, predicted_program, question, error, args.dry_run, args, config)
        rows.append(row)
        print(f"{config.name} {mode} {index}/{len(questions)} {question['id']}: {status_label(row)}", flush=True)
    return rows


def mode_summary(rows: list[dict[str, Any]], provider: str, mode: str, model: str) -> dict[str, Any]:
    scored = sum(1 for row in rows if row.get("score") is not None)
    passed = sum(1 for row in rows if isinstance(row.get("score"), dict) and row["score"].get("passed"))
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
        "overall_pass_rate": passed / len(rows) if rows else 0.0,
        "exact_match": exact_match_total / scored if scored else 0.0,
        "f1": f1_total / scored if scored else 0.0,
        "elapsed_seconds": round(elapsed, 3),
        "avg_elapsed_seconds": round(elapsed / len(rows), 3) if rows else 0.0,
        "tool_calls": sum(int(row.get("tool_calls") or 0) for row in rows),
        "token_usage": token_usage_from_rows(rows),
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
        "# MultiHierTT Mini Original Plain Harness",
        "",
        f"- Created at: `{created_at}`",
        f"- Original package: `{args.original_dir}`",
        f"- Original JSON: `{args.original_json}`",
        f"- Prebuilt markdown/CSV source: `{args.original_md_csv_dir}`",
        f"- Questions: `{len(questions)}` from `{args.questions_path}`",
        f"- Evaluator labels: `{args.answers_path}`",
        "- Source rule: this evaluator never opens or requires an MCD package.",
        "- `plain_raw` supplies the full original raw JSON corpus after removing each record's `qa` block.",
        "- `plain_chunked` supplies only a raw source.json file with the selected original record's raw paragraphs and raw HTML tables.",
        "- `harness_plain_raw` supplies the full raw main.md text and all raw prebuilt table CSVs.",
        "- `tools_plain_raw` uses the same full raw main.md and CSV corpus, exposed through list/read/search/table/calculator tools without an index.",
        "- Harness excludes `qa` answers, programs, and evidence refs.",
        f"- Modes: `{', '.join(modes)}`",
        f"- Scoring mode: `{args.scoring_mode}`",
        "",
        "| Provider | Mode | Model | EM | F1 | Passed | Failed | Scored | Total | Scored pass rate | Overall pass rate | Errors | Tool calls |",
        "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for item in summaries:
        lines.append(
            f"| {item['provider']} | {item['mode']} | `{item['model']}` | {item['exact_match']:.3f} | "
            f"{item['f1']:.3f} | {item['passed']} | {item['failed']} | {item['scored']} | {item['total']} | "
            f"{item['pass_rate']:.1%} | {item['overall_pass_rate']:.1%} | {item['errors']} | {item['tool_calls']} |"
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
    modes = parse_modes(args.modes)
    configs = provider_configs(args)

    if not args.dry_run:
        env_configs = [plain_eval.ProviderConfig(config.name, config.model, config.api_key_env) for config in configs]
        if args.scoring_mode == "llm_judge":
            env_configs.extend(
                plain_eval.ProviderConfig(judge.name, judge.model, judge.api_key_env)
                for judge in (judge_provider_config(args, config) for config in configs)
            )
        plain_eval.validate_provider_env(list({(item.name, item.model, item.api_key_env): item for item in env_configs}.values()))

    args.original_dir = args.original_dir.resolve()
    args.original_json = (args.original_json or (args.original_dir / "dev_50.json")).resolve()
    args.original_md_csv_dir = args.original_md_csv_dir.resolve()
    args.questions_path = args.questions_path.resolve()
    args.answers_path = args.answers_path.resolve()
    args.results_root = args.results_root.resolve()
    required_paths = [args.original_dir, args.original_json, args.questions_path, args.answers_path]
    if "harness_plain_raw" in modes or "tools_plain_raw" in modes:
        required_paths.append(args.original_md_csv_dir)
    for path in required_paths:
        if not path.exists():
            raise FileNotFoundError(path)

    questions = load_questions(args.questions_path, args.answers_path)
    if args.questions is not None:
        if args.questions < 1:
            raise ValueError("--questions must be a positive integer.")
        questions = questions[: args.questions]

    original_corpus_payload = load_original_corpus_payload(args.original_dir, args.original_json)
    records_by_example_id = load_original_records(args.original_dir, args.original_json, questions)
    output_dir = make_output_dir(args.results_root)
    harness_payloads_by_example_id: dict[str, dict[str, Any]] = {}
    harness_tool_records_by_example_id: dict[str, dict[str, Any]] = {}
    if "harness_plain_raw" in modes or "tools_plain_raw" in modes:
        harness_payloads_by_example_id = load_prebuilt_harness_payloads(
            md_csv_dir=args.original_md_csv_dir,
            questions=questions,
            records_by_example_id=records_by_example_id,
        )
    if "tools_plain_raw" in modes:
        harness_tool_records_by_example_id = {
            question["example_id"]: build_harness_tool_record(
                question=question,
                harness_payload=harness_payloads_by_example_id[question["example_id"]],
            )
            for question in questions
        }

    created_at = datetime.now().isoformat(timespec="seconds")
    write_json(
        output_dir / "run_config.json",
        {
            "created_at": created_at,
            "providers": [config.__dict__ for config in configs],
            "modes": modes,
            "original_dir": str(args.original_dir),
            "original_json": str(args.original_json),
            "original_md_csv_dir": str(args.original_md_csv_dir),
            "questions_path": str(args.questions_path),
            "answers_path": str(args.answers_path),
            "question_count": len(questions),
            "scoring_mode": args.scoring_mode,
            "judge_provider": args.judge_provider,
            "judge_model": args.judge_model,
            "max_tool_steps": args.max_tool_steps,
            "tools_single_round": args.tools_single_round,
            "max_observation_chars": args.max_observation_chars,
            "max_output_tokens": args.max_output_tokens,
            "temperature": args.temperature,
            "dry_run": args.dry_run,
            "prompt_profile": "multihiertt_original_plain_raw_with_neutral_harness",
            "mcd_usage": "none",
            "harness_plain_files_root": str(args.original_md_csv_dir) if "harness_plain_raw" in modes else None,
            "harness_tool_files_root": str(args.original_md_csv_dir) if "tools_plain_raw" in modes else None,
            "mode_profiles": {
                "plain_raw": "single model call over the full original raw JSON corpus with qa blocks removed and no selected-example prompt wrapper",
                "plain_chunked": "single model call over a raw source.json file for the selected original record, containing only paragraphs and raw HTML tables",
                "harness_plain_raw": "single model call over full raw original_md_csv main.md and all raw CSV files, without evaluator metadata",
                "tools_plain_raw": (
                    "one batched tool-request call plus one final answer call"
                    if args.tools_single_round
                    else "multi-step JSON tool loop over full raw original_md_csv main.md, raw CSV rows, ranked search, file listing, and calculator without a source index"
                ),
            },
            "harness_tool_docs": harness_tool_docs(),
            "shared_evaluator": {
                "answers_path": str(args.answers_path),
                "evaluation_hashes": {
                    question["id"]: evaluation_hash(question["evaluation_question"])
                    for question in questions
                },
                "note": "Evaluator labels are used only after provider answers are returned.",
            },
        },
    )

    all_rows: list[dict[str, Any]] = []
    summaries: list[dict[str, Any]] = []
    rows_by_key: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for config in configs:
        for mode in modes:
            rows = run_mode(
                mode=mode,
                records_by_example_id=records_by_example_id,
                original_corpus_payload=original_corpus_payload,
                harness_payloads_by_example_id=harness_payloads_by_example_id,
                harness_tool_records_by_example_id=harness_tool_records_by_example_id,
                questions=questions,
                config=config,
                args=args,
            )
            rows_by_key[(config.name, mode)] = rows
            all_rows.extend(rows)
            summaries.append(mode_summary(rows, config.name, mode, config.model))
            plain_eval.write_jsonl(output_dir / f"{config.name}_{mode}_results.jsonl", rows)

    plain_eval.write_jsonl(output_dir / "all_results.jsonl", all_rows)
    write_json(output_dir / "summary.json", {"modes": summaries})
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
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
