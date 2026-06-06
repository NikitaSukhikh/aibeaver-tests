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
DEFAULT_QUESTIONS_PATH = Path("datasets/multihiertt-mini/qa_questions_50.jsonl")
DEFAULT_ANSWERS_PATH = Path("datasets/multihiertt-mini/answers.json")
DEFAULT_RESULTS_ROOT = Path("results/multihiertt_mini_original")
DEFAULT_OPENAI_MODEL = "gpt-5.4"
DEFAULT_ANTHROPIC_MODEL = "claude-opus-4-5"
DEFAULT_XAI_MODEL = "grok-4.3"
DEFAULT_MAX_OUTPUT_TOKENS = 12000
DEFAULT_JUDGE_MAX_OUTPUT_TOKENS = 2000
PROVIDERS = ["openai", "anthropic", "xai"]
MODES = ["plain_source", "harnessed_plain", "harnessed_tools"]
MULTIHIERTT_PROGRAM_OPS = {"add", "subtract", "multiply", "divide", "exp"}
QUESTION_STOPWORDS = {
    "a",
    "an",
    "and",
    "answer",
    "benchmark",
    "by",
    "continues",
    "current",
    "did",
    "does",
    "example",
    "for",
    "from",
    "if",
    "in",
    "is",
    "it",
    "its",
    "mini",
    "most",
    "multihiertt",
    "of",
    "on",
    "or",
    "question",
    "reach",
    "the",
    "to",
    "total",
    "was",
    "what",
    "which",
    "will",
    "with",
}


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
    parser.add_argument("--questions-path", type=Path, default=DEFAULT_QUESTIONS_PATH)
    parser.add_argument("--answers-path", type=Path, default=DEFAULT_ANSWERS_PATH)
    parser.add_argument("--results-root", type=Path, default=DEFAULT_RESULTS_ROOT)
    parser.add_argument("--modes", default="all", help="Comma-separated modes: all, plain_source, harnessed_plain, harnessed_tools.")
    parser.add_argument("--providers", nargs="+", choices=PROVIDERS, default=["openai", "anthropic"])
    parser.add_argument("--openai-model", default=os.getenv("OPENAI_MODEL", DEFAULT_OPENAI_MODEL))
    parser.add_argument("--anthropic-model", default=os.getenv("ANTHROPIC_MODEL", DEFAULT_ANTHROPIC_MODEL))
    parser.add_argument("--xai-model", default=os.getenv("XAI_MODEL", DEFAULT_XAI_MODEL))
    parser.add_argument("--questions", type=int, default=None, help="Run only the first N questions.")
    parser.add_argument("--max-tool-steps", type=int, default=20)
    parser.add_argument("--max-observation-chars", type=int, default=60000)
    parser.add_argument("--max-output-tokens", type=int, default=DEFAULT_MAX_OUTPUT_TOKENS)
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--timeout-seconds", type=int, default=120)
    parser.add_argument("--retries", type=int, default=2)
    parser.add_argument(
        "--scoring-mode",
        choices=["multihiertt", "programmatic", "llm_judge"],
        default="llm_judge",
        help="llm_judge is semantic; multihiertt mirrors upstream answer/program scoring; programmatic uses expected_contains.",
    )
    parser.add_argument("--judge-provider", choices=["same", "openai", "anthropic", "xai"], default=os.getenv("JUDGE_PROVIDER", "same"))
    parser.add_argument("--judge-model", default=os.getenv("JUDGE_MODEL"))
    parser.add_argument("--judge-max-output-tokens", type=int, default=DEFAULT_JUDGE_MAX_OUTPUT_TOKENS)
    parser.add_argument("--judge-temperature", type=float, default=0.0)
    parser.add_argument("--judge-timeout-seconds", type=int, default=120)
    parser.add_argument("--judge-retries", type=int, default=2)
    parser.add_argument("--dry-run", action="store_true")
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
    return [mode for mode in MODES if mode in requested]


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


def load_original_records(original_dir: Path, original_json: Path, questions: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    if original_json.resolve().parent != original_dir.resolve():
        raise ValueError(f"Original JSON must be inside the original package directory: {original_dir}")
    records = json.loads(original_json.read_text(encoding="utf-8"))
    if not isinstance(records, list):
        raise ValueError(f"Expected {original_json} to contain a JSON array.")

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


def model_question(question: dict[str, Any]) -> dict[str, str]:
    return {
        "id": str(question["id"]),
        "family_id": str(question.get("family_id") or ""),
        "example_id": str(question["example_id"]),
        "source_uid": str(question["source_uid"]),
        "prompt": str(question["prompt"]),
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
        "The payload is the original MultiHierTT JSON record after removing its `qa` evaluator object. HTML tables, "
        "paragraphs, and table descriptions are otherwise preserved. This mode intentionally has no added harness."
    )


def harness_source_note() -> str:
    return (
        "The payload is a neutral plain-file harness generated from the same original source record. It contains "
        "source.md, parsed table CSVs, table dimensions, likely header rows, numeric-cell coordinates, question "
        "keyword locations, and workflow guidance. It does not contain gold answers, programs, or evidence refs. "
        "Use the harness to navigate and verify the answer against source.md or the table CSVs."
    )


def make_prompt(question: dict[str, str], source_payload: dict[str, Any], source_access_note: str) -> str:
    payload = {
        "example_id": question["example_id"],
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
        '{"example_id":"the provided example id","predicted_ans":"requested answer value only","predicted_program":[]}\n\n'
        "`predicted_program` may be a MultiHierTT program token list only if you are certain it exactly represents "
        "the computation; otherwise return an empty list and put the answer value in `predicted_ans`.\n\n"
        "Question and source payload:\n"
        f"{json.dumps(payload, ensure_ascii=False, indent=2)}"
    )


def safe_filename(value: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", value).strip("_") or "item"


def normalize_for_match(text: Any) -> str:
    return re.sub(r"\s+", " ", str(text or "").casefold()).strip()


def question_keywords(prompt: str) -> list[str]:
    raw_tokens = re.findall(r"[A-Za-z][A-Za-z0-9&.-]*|\d{4}|\d+(?:\.\d+)?", prompt)
    keywords: list[str] = []
    seen: set[str] = set()
    for token in raw_tokens:
        normalized = token.casefold().strip(".")
        if len(normalized) < 3 and not normalized.isdigit():
            continue
        if normalized in QUESTION_STOPWORDS or normalized.startswith("mhdev"):
            continue
        if normalized not in seen:
            seen.add(normalized)
            keywords.append(normalized)
    return keywords[:24]


def table_to_markdown(rows: list[list[str]]) -> str:
    if not rows:
        return "_Empty table._"
    width = max(len(row) for row in rows)

    def padded(row: list[str]) -> list[str]:
        return [str(cell).replace("\n", " ").strip() for cell in [*row, *([""] * (width - len(row)))]]

    header = padded(rows[0])
    lines = [
        "| " + " | ".join(header) + " |",
        "| " + " | ".join("---" for _ in range(width)) + " |",
    ]
    for row in rows[1:]:
        lines.append("| " + " | ".join(padded(row)) + " |")
    return "\n".join(lines)


def looks_numeric(text: Any) -> bool:
    cleaned = str(text or "").strip().replace(",", "").replace("$", "").replace("%", "")
    cleaned = cleaned.strip("()")
    if cleaned in {"", "-", "--", "—", "n/a", "N/A"}:
        return False
    return bool(re.fullmatch(r"-?\d+(?:\.\d+)?", cleaned))


def profile_table(rows: list[list[str]]) -> dict[str, Any]:
    width = max((len(row) for row in rows), default=0)
    numeric_cells = []
    non_empty_by_row = []
    for row_index, row in enumerate(rows):
        non_empty_by_row.append(sum(1 for cell in row if str(cell).strip()))
        for col_index, cell in enumerate(row):
            if looks_numeric(cell):
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


def find_keyword_locations(
    *,
    keywords: list[str],
    paragraphs: list[str],
    tables: list[list[list[str]]],
    table_description: dict[str, Any],
) -> dict[str, Any]:
    paragraph_hits = []
    for paragraph_index, paragraph in enumerate(paragraphs):
        text = normalize_for_match(paragraph)
        matched = [keyword for keyword in keywords if keyword in text]
        if matched:
            paragraph_hits.append({"paragraph_index": paragraph_index, "matched_terms": matched})

    table_hits = []
    for table_index, rows in enumerate(tables):
        for row_index, row in enumerate(rows):
            row_text = normalize_for_match(" ".join(str(cell) for cell in row))
            matched = [keyword for keyword in keywords if keyword in row_text]
            if matched:
                table_hits.append({"table_index": table_index, "row_index": row_index, "matched_terms": matched})

    description_hits = []
    for cell_ref, description in table_description.items():
        text = normalize_for_match(description)
        matched = [keyword for keyword in keywords if keyword in text]
        if matched:
            description_hits.append({"cell_ref": str(cell_ref), "matched_terms": matched})

    return {
        "question_keywords": keywords,
        "paragraph_hits": paragraph_hits[:120],
        "table_row_hits": table_hits[:200],
        "table_description_hits": description_hits[:200],
        "notes": [
            "Hit lists show where question terms appear; they intentionally omit candidate answer values.",
            "A missing hit does not mean the answer is absent, because synonyms and merged headers may be used.",
        ],
    }


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def write_csv(path: Path, rows: list[list[str]]) -> None:
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerows(rows)


def materialize_harness_bundle(
    *,
    output_dir: Path,
    question: dict[str, Any],
    source_record: dict[str, Any],
) -> dict[str, Any]:
    example_dir = output_dir / "harness_files" / safe_filename(question["example_id"])
    tables_dir = example_dir / "tables"
    meta_dir = example_dir / "meta"
    tables_dir.mkdir(parents=True, exist_ok=True)
    meta_dir.mkdir(parents=True, exist_ok=True)

    paragraphs = [str(item) for item in source_record.get("paragraphs", [])]
    parsed_tables = [parse_html_table(str(markup)).rows for markup in source_record.get("tables", [])]
    table_description = dict(source_record.get("table_description", {}))

    source_lines = [
        f"# {question['example_id']} Original Source",
        "",
        f"Question: {question['prompt']}",
        "",
        "## Paragraphs",
        "",
    ]
    for paragraph_index, paragraph in enumerate(paragraphs):
        source_lines.extend([f"### Paragraph {paragraph_index}", "", paragraph, ""])
    source_lines.extend(["## Tables", ""])
    for table_index, rows in enumerate(parsed_tables):
        source_lines.extend([f"### Table {table_index}", "", table_to_markdown(rows), ""])
        write_csv(tables_dir / f"table_{table_index}.csv", rows)
        write_json(meta_dir / f"table_{table_index}_profile.json", profile_table(rows))

    keywords = question_keywords(question["prompt"])
    locations = find_keyword_locations(
        keywords=keywords,
        paragraphs=paragraphs,
        tables=parsed_tables,
        table_description=table_description,
    )
    guide = {
        "purpose": "Neutral navigation harness for the original MultiHierTT source.",
        "forbidden_fields": ["qa.answer", "qa.program", "qa.table_evidence", "qa.text_evidence"],
        "workflow": [
            "Use question_keywords and location hits to choose candidate paragraphs/tables.",
            "Inspect source.md or table CSVs to recover actual headers, row labels, units, and values.",
            "When running in harnessed_tools mode, prefer targeted source tools over reading the full source at once.",
            "Use the calculator tool for arithmetic after copying values from source observations.",
            "Confirm whether the question asks for a span, maximum/minimum, difference, ratio, percentage, or projection.",
            "Do arithmetic only after checking signs, currency/percent markers, and missing-value conventions.",
            "Return only the requested answer value in predicted_ans.",
        ],
        "coordinate_convention": "All table row and column coordinates are zero-based.",
    }
    overview = {
        "example_id": question["example_id"],
        "source_uid": question["source_uid"],
        "paragraph_count": len(paragraphs),
        "table_count": len(parsed_tables),
        "tables": [
            {
                "table_index": table_index,
                "csv": f"tables/table_{table_index}.csv",
                "profile": f"meta/table_{table_index}_profile.json",
                "row_count": len(rows),
                "max_column_count": max((len(row) for row in rows), default=0),
            }
            for table_index, rows in enumerate(parsed_tables)
        ],
        "table_description_count": len(table_description),
    }
    files = {
        "source.md": "\n".join(source_lines).rstrip() + "\n",
        "meta/overview.json": json.dumps(overview, ensure_ascii=False, indent=2) + "\n",
        "meta/question_locations.json": json.dumps(locations, ensure_ascii=False, indent=2) + "\n",
        "meta/harness_guide.json": json.dumps(guide, ensure_ascii=False, indent=2) + "\n",
        "meta/tool_manifest.json": json.dumps(harness_tool_docs(), ensure_ascii=False, indent=2) + "\n",
        "meta/table_descriptions.json": json.dumps(table_description, ensure_ascii=False, indent=2) + "\n",
    }
    for relative_path, content in files.items():
        path = example_dir / relative_path
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(content, encoding="utf-8")

    model_files = []
    for relative_path in [
        "source.md",
        "meta/overview.json",
        "meta/question_locations.json",
        "meta/harness_guide.json",
        "meta/tool_manifest.json",
        "meta/table_descriptions.json",
    ]:
        model_files.append({"path": relative_path, "content": (example_dir / relative_path).read_text(encoding="utf-8")})
    for table_index in range(len(parsed_tables)):
        for relative_path in [f"tables/table_{table_index}.csv", f"meta/table_{table_index}_profile.json"]:
            model_files.append({"path": relative_path, "content": (example_dir / relative_path).read_text(encoding="utf-8")})

    return {
        "source_format": "original_plain_file_harness",
        "bundle_dir": str(example_dir),
        "files": model_files,
    }


def plain_source_payload(source_record: dict[str, Any]) -> dict[str, Any]:
    return {
        "source_format": "original_json_without_qa",
        "record": source_record,
    }


def harness_tools_source_note() -> str:
    return (
        "The model can navigate the neutral harness through explicit JSON tools. Tools are read-only except for "
        "the calculator, which operates only on numbers supplied in the tool arguments. Tool observations are "
        "derived from the original source record and generated harness files, never from evaluator answers."
    )


def harness_tool_docs() -> dict[str, Any]:
    return {
        "overview": {
            "args": {},
            "notes": "Return source counts, table inventory, harness files, and question keyword hints.",
        },
        "read_file": {
            "args": {"path": "source.md or a path from the harness file list", "max_chars": "optional integer"},
            "notes": "Read a generated harness file by relative path.",
        },
        "search_text": {
            "args": {"query": "text", "path": "optional harness file path", "limit": "optional integer"},
            "notes": "Search generated harness files and return line-level matches.",
        },
        "paragraphs": {
            "args": {"indexes": "optional list of paragraph indexes", "query": "optional text", "limit": "optional integer"},
            "notes": "Read original paragraphs by index or substring search.",
        },
        "table": {
            "args": {"table_index": "integer", "start_row": "optional integer", "limit": "optional integer"},
            "notes": "Read a row window from a parsed original HTML table. Coordinates are zero-based.",
        },
        "find_rows": {
            "args": {"query": "text", "table_index": "optional integer", "limit": "optional integer"},
            "notes": "Find table rows whose cells contain a substring.",
        },
        "cell_descriptions": {
            "args": {"cell_refs": "optional list like ['0-2-4']", "query": "optional text", "limit": "optional integer"},
            "notes": "Read original table_description entries by ref or text search.",
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
    source_record: dict[str, Any],
    harness_payload: dict[str, Any],
) -> dict[str, Any]:
    files = {
        str(item["path"]): str(item["content"])
        for item in harness_payload.get("files", [])
        if isinstance(item, dict) and item.get("path") is not None
    }
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
        "paragraphs": [str(item) for item in source_record.get("paragraphs", [])],
        "tables": parsed_tables,
        "table_description": dict(source_record.get("table_description", {})),
        "files": files,
        "bundle_dir": harness_payload.get("bundle_dir"),
        "question_locations": json.loads(files.get("meta/question_locations.json", "{}")),
    }


def harness_tool_overview(record: dict[str, Any]) -> dict[str, Any]:
    return {
        "tool": "overview",
        "example_id": record["example_id"],
        "source_uid": record["source_uid"],
        "question": record["question"],
        "paragraph_count": len(record.get("paragraphs", [])),
        "tables": [
            {
                "table_index": table["table_index"],
                "row_count": table["row_count"],
                "max_column_count": table["max_column_count"],
            }
            for table in record.get("tables", [])
        ],
        "table_description_count": len(record.get("table_description", {})),
        "harness_files": sorted(record.get("files", {})),
        "question_locations": record.get("question_locations", {}),
    }


def bounded_limit(value: Any, default: int, maximum: int) -> int:
    try:
        parsed = int(value)
    except (TypeError, ValueError):
        parsed = default
    return max(1, min(parsed, maximum))


def harness_tool_read_file(record: dict[str, Any], args: dict[str, Any]) -> dict[str, Any]:
    path = str(args.get("path") or "")
    files = record.get("files", {})
    if path not in files:
        raise ValueError(f"Unknown harness file path: {path}")
    max_chars = bounded_limit(args.get("max_chars"), 12000, 50000)
    content = str(files[path])
    return {
        "tool": "read_file",
        "path": path,
        "chars": len(content),
        "truncated": len(content) > max_chars,
        "text": content[:max_chars],
    }


def harness_tool_search_text(record: dict[str, Any], args: dict[str, Any]) -> dict[str, Any]:
    query = normalize_for_match(args.get("query"))
    if not query:
        raise ValueError("search_text query is required.")
    files = record.get("files", {})
    paths = [str(args["path"])] if args.get("path") else sorted(files)
    limit = bounded_limit(args.get("limit"), 30, 200)
    matches = []
    for path in paths:
        if path not in files:
            raise ValueError(f"Unknown harness file path: {path}")
        for line_number, line in enumerate(str(files[path]).splitlines(), start=1):
            if query in normalize_for_match(line):
                matches.append({"path": path, "line": line_number, "text": line[:1000]})
                if len(matches) >= limit:
                    return {"tool": "search_text", "query": args.get("query"), "returned": len(matches), "matches": matches}
    return {"tool": "search_text", "query": args.get("query"), "returned": len(matches), "matches": matches}


def harness_tool_paragraphs(record: dict[str, Any], args: dict[str, Any]) -> dict[str, Any]:
    paragraphs = list(record.get("paragraphs", []))
    indexes = args.get("indexes")
    query = normalize_for_match(args.get("query"))
    limit = bounded_limit(args.get("limit"), len(paragraphs) or 1, 200)
    if isinstance(indexes, list):
        selected = [
            {"paragraph_index": int(index), "paragraph_text": paragraphs[int(index)]}
            for index in indexes
            if isinstance(index, int) and 0 <= int(index) < len(paragraphs)
        ]
    else:
        selected = []
        for index, text in enumerate(paragraphs):
            if not query or query in normalize_for_match(text):
                selected.append({"paragraph_index": index, "paragraph_text": text})
            if len(selected) >= limit:
                break
    return {"tool": "paragraphs", "returned": len(selected), "total_paragraphs": len(paragraphs), "rows": selected}


def harness_tool_table(record: dict[str, Any], args: dict[str, Any]) -> dict[str, Any]:
    table_index = int(args.get("table_index"))
    start_row = max(0, int(args.get("start_row") or 0))
    limit = bounded_limit(args.get("limit"), 30, 300)
    table = next((item for item in record.get("tables", []) if int(item["table_index"]) == table_index), None)
    if table is None:
        raise ValueError(f"Unknown table_index {table_index}.")
    rows = table.get("rows", [])
    selected = rows[start_row : start_row + limit]
    return {
        "tool": "table",
        "table_index": table_index,
        "row_count": table["row_count"],
        "max_column_count": table["max_column_count"],
        "returned": len(selected),
        "truncated": start_row + len(selected) < len(rows),
        "rows": selected,
    }


def harness_tool_find_rows(record: dict[str, Any], args: dict[str, Any]) -> dict[str, Any]:
    query = normalize_for_match(args.get("query"))
    if not query:
        raise ValueError("find_rows query is required.")
    limit = bounded_limit(args.get("limit"), 30, 200)
    requested_table = args.get("table_index")
    matches = []
    for table in record.get("tables", []):
        table_index = int(table["table_index"])
        if requested_table is not None and int(requested_table) != table_index:
            continue
        for row in table.get("rows", []):
            row_text = normalize_for_match(" ".join(str(cell) for cell in row.get("cells", [])))
            if query in row_text:
                matches.append(
                    {
                        "table_index": table_index,
                        "row_index": row["row_index"],
                        "cells": row.get("cells", []),
                    }
                )
                if len(matches) >= limit:
                    return {"tool": "find_rows", "query": args.get("query"), "returned": len(matches), "rows": matches}
    return {"tool": "find_rows", "query": args.get("query"), "returned": len(matches), "rows": matches}


def harness_tool_cell_descriptions(record: dict[str, Any], args: dict[str, Any]) -> dict[str, Any]:
    refs = args.get("cell_refs")
    query = normalize_for_match(args.get("query"))
    limit = bounded_limit(args.get("limit"), 50, 300)
    descriptions = record.get("table_description", {})
    rows = []
    if isinstance(refs, list):
        for ref in refs:
            ref_text = str(ref)
            if ref_text in descriptions:
                rows.append({"cell_ref": ref_text, "description": descriptions[ref_text]})
    else:
        for ref, description in descriptions.items():
            if not query or query in normalize_for_match(ref) or query in normalize_for_match(description):
                rows.append({"cell_ref": ref, "description": description})
            if len(rows) >= limit:
                break
    return {"tool": "cell_descriptions", "returned": len(rows), "rows": rows}


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
    if tool == "overview":
        return harness_tool_overview(record)
    if tool == "read_file":
        return harness_tool_read_file(record, args)
    if tool == "search_text":
        return harness_tool_search_text(record, args)
    if tool == "paragraphs":
        return harness_tool_paragraphs(record, args)
    if tool == "table":
        return harness_tool_table(record, args)
    if tool == "find_rows":
        return harness_tool_find_rows(record, args)
    if tool == "cell_descriptions":
        return harness_tool_cell_descriptions(record, args)
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


def parse_harness_agent_action(text: str) -> dict[str, Any]:
    objects = extract_json_objects(text)
    if not objects:
        raise ValueError("Agent response did not contain a JSON object.")
    action = objects[0]
    if "predicted_ans" in action:
        return {"answer": str(action["predicted_ans"]), "predicted_program": normalize_predicted_program(action.get("predicted_program", []))}
    if "answer" in action:
        return {"answer": str(action["answer"]), "predicted_program": normalize_predicted_program(action.get("predicted_program", []))}
    if "tool" in action:
        args = action.get("args", {})
        if not isinstance(args, dict):
            raise ValueError("Tool action 'args' must be an object.")
        return {"tool": str(action["tool"]), "args": args}
    raise ValueError("Agent response must contain either 'tool', 'answer', or 'predicted_ans'.")


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
    return sum(1 for item in trace if item.get("action", {}).get("tool"))


def make_harness_agent_prompt(
    *,
    record: dict[str, Any],
    question: dict[str, Any],
    observations: list[dict[str, Any]],
) -> str:
    payload = {
        "id": question["id"],
        "example_id": question["example_id"],
        "source_uid": question.get("source_uid"),
        "question": question["prompt"],
    }
    dataset_index = {
        "example_id": record["example_id"],
        "source_uid": record["source_uid"],
        "harness_files": sorted(record.get("files", {})),
        "paragraph_count": len(record.get("paragraphs", [])),
        "tables": [
            {
                "table_index": table["table_index"],
                "row_count": table["row_count"],
                "max_column_count": table["max_column_count"],
            }
            for table in record.get("tables", [])
        ],
        "question_locations": record.get("question_locations", {}),
    }
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
        "Do not return a tool call and an answer in the same response.\n\n"
        "Available harness tools:\n"
        f"{json.dumps(harness_tool_docs(), ensure_ascii=False, indent=2)}\n\n"
        "Harness index:\n"
        f"{json.dumps(dataset_index, ensure_ascii=False, indent=2)}\n\n"
        "Question:\n"
        f"{json.dumps(payload, ensure_ascii=False, indent=2)}\n\n"
        "Previous tool observations:\n"
        f"{json.dumps(observations, ensure_ascii=False, indent=2)}"
    )


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
    for step in range(1, args.max_tool_steps + 1):
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
            action = parse_harness_agent_action(raw)
        except Exception as exc:
            trace.append({"step": step, "raw": raw, "error": str(exc)})
            return "", [], metadata, trace, f"Could not parse harness tool action: {exc}"
        trace_item: dict[str, Any] = {"step": step, "raw": raw, "action": action}
        response_objects = extract_json_objects(raw)
        if len(response_objects) > 1:
            trace_item["ignored_response_objects"] = [
                {
                    "object_keys": sorted(str(key) for key in value),
                    "ignored_because": "Only the first JSON object in a model response is executed.",
                }
                for value in response_objects[1:]
            ]
        if "answer" in action:
            trace.append(trace_item)
            return action["answer"], action.get("predicted_program", []), metadata, trace, None
        try:
            observation = execute_harness_tool(record, action["tool"], action["args"])
        except Exception as exc:
            observation = {"tool": action["tool"], "error": str(exc)}
        trace_item["observation"] = observation
        trace.append(trace_item)
        observations.append(
            {
                "step": step,
                "tool": action["tool"],
                "args": action["args"],
                "observation": truncate_observation(observation, int(args.max_observation_chars)),
            }
        )
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
        if mode == "harnessed_tools":
            answer, predicted_program, metadata, trace, error = run_harness_tools_question(
                record=harness_tool_records_by_example_id[question["example_id"]],
                question=model_question(question),
                config=config,
                args=args,
            )
        else:
            if mode == "plain_source":
                payload = plain_source_payload(records_by_example_id[question["example_id"]])
                source_note = plain_source_note()
            else:
                payload = harness_payloads_by_example_id[question["example_id"]]
                source_note = harness_source_note()
            prompt = make_prompt(model_question(question), payload, source_note)
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
            "tool_calls": harness_agent_tool_calls_from_trace(trace) if mode == "harnessed_tools" else 0,
            "harness_bundle_dir": harness_payloads_by_example_id[question["example_id"]].get("bundle_dir"),
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
        f"- Questions: `{len(questions)}` from `{args.questions_path}`",
        f"- Evaluator labels: `{args.answers_path}`",
        "- Source rule: this evaluator never opens or requires an MCD package.",
        "- `plain_source` supplies the sanitized original JSON record only.",
        "- `harnessed_plain` supplies generated source.md, parsed table CSVs, table profiles, keyword locations, table descriptions, tool manifest, and a guide.",
        "- `harnessed_tools` exposes those harness files plus targeted paragraph/table/cell-description/calculator tools.",
        "- Harness excludes `qa` answers, programs, and evidence refs.",
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
    args.questions_path = args.questions_path.resolve()
    args.answers_path = args.answers_path.resolve()
    args.results_root = args.results_root.resolve()
    for path in (args.original_dir, args.original_json, args.questions_path, args.answers_path):
        if not path.exists():
            raise FileNotFoundError(path)

    questions = load_questions(args.questions_path, args.answers_path)
    if args.questions is not None:
        if args.questions < 1:
            raise ValueError("--questions must be a positive integer.")
        questions = questions[: args.questions]

    records_by_example_id = load_original_records(args.original_dir, args.original_json, questions)
    output_dir = make_output_dir(args.results_root)
    harness_payloads_by_example_id = {
        question["example_id"]: materialize_harness_bundle(
            output_dir=output_dir,
            question=question,
            source_record=records_by_example_id[question["example_id"]],
        )
        for question in questions
    }
    harness_tool_records_by_example_id = {
        question["example_id"]: build_harness_tool_record(
            question=question,
            source_record=records_by_example_id[question["example_id"]],
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
            "questions_path": str(args.questions_path),
            "answers_path": str(args.answers_path),
            "question_count": len(questions),
            "scoring_mode": args.scoring_mode,
            "judge_provider": args.judge_provider,
            "judge_model": args.judge_model,
            "max_tool_steps": args.max_tool_steps,
            "max_observation_chars": args.max_observation_chars,
            "max_output_tokens": args.max_output_tokens,
            "temperature": args.temperature,
            "dry_run": args.dry_run,
            "prompt_profile": "multihiertt_original_plain_source_with_neutral_harness",
            "mcd_usage": "none",
            "harness_files_root": str(output_dir / "harness_files"),
            "mode_profiles": {
                "plain_source": "single model call over sanitized original JSON source",
                "harnessed_plain": "single model call over generated source.md, parsed table CSVs, and neutral metadata harness",
                "harnessed_tools": "multi-step JSON tool loop over generated harness files, parsed tables, source paragraphs, cell descriptions, and calculator",
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
