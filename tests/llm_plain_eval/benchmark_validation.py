"""Shared validation and scoring helpers for benchmark question JSONL files."""

from __future__ import annotations

import json
import re
import time
from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from pathlib import Path
from typing import Any

import run_plain_eval as plain_eval


NUMERIC_TOKEN_RE = re.compile(r"(?<![A-Za-z0-9_-])[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?=$|[^A-Za-z0-9_])")
BUNDLED_QUERY_PATTERNS: tuple[tuple[re.Pattern[str], str], ...] = (
    (
        re.compile(r"\balso\s+(?:report|return|include|confirm)\b", re.IGNORECASE),
        "uses an additional 'also' request",
    ),
    (
        re.compile(r"\bhow many\b[^?]*\bwhich\b|\bwhich\b[^?]*\bhow many\b", re.IGNORECASE),
        "combines a count question with a row-selection question",
    ),
    (
        re.compile(r"\bfirst\b[^?]*\band\b[^?]*\bfirst\b", re.IGNORECASE),
        "asks for multiple first/example rows",
    ),
    (
        re.compile(r"\bbest\b[^?]*\band\b[^?]*\bworst\b|\bworst\b[^?]*\band\b[^?]*\bbest\b", re.IGNORECASE),
        "asks for both best and worst rows",
    ),
    (
        re.compile(
            r"\blargest\b[^?]*\band\b[^?]*\bsmallest\b|\bsmallest\b[^?]*\band\b[^?]*\blargest\b",
            re.IGNORECASE,
        ),
        "asks for both largest and smallest rows",
    ),
)


def parse_decimal_text(value: str) -> Decimal | None:
    cleaned = value.strip().replace(",", "")
    cleaned = cleaned.strip("()[]{}<>:;")
    if cleaned.endswith(".") and cleaned.count(".") == 1:
        cleaned = cleaned[:-1]
    if not re.fullmatch(r"[+-]?(?:\d+(?:\.\d*)?|\.\d+)", cleaned):
        return None
    try:
        return Decimal(cleaned)
    except InvalidOperation:
        return None


def decimal_places(value: str) -> int:
    cleaned = value.strip().replace(",", "")
    if "." not in cleaned:
        return 0
    return len(cleaned.rsplit(".", 1)[1].rstrip("()[]{}<>:;"))


def numeric_match_type(actual: Decimal, expected: Decimal, expected_text: str) -> str | None:
    if actual == expected:
        return "numeric_equivalent"
    places = decimal_places(expected_text)
    if places <= 0:
        return None
    quantum = Decimal(1).scaleb(-places)
    if actual.quantize(quantum, rounding=ROUND_HALF_UP) == expected:
        return "numeric_rounded"
    return None


def contains_expected_tolerant(answer: str, expected: str) -> tuple[bool, str]:
    expected_decimal = parse_decimal_text(expected)
    if expected_decimal is None:
        if plain_eval.contains_expected(answer, expected):
            return True, "substring"
        return False, "missing"

    for match in NUMERIC_TOKEN_RE.finditer(answer):
        actual_decimal = parse_decimal_text(match.group(0))
        if actual_decimal is None:
            continue
        match_type = numeric_match_type(actual_decimal, expected_decimal, expected)
        if match_type:
            return True, match_type
    return False, "missing"


def score_answer_tolerant(answer: str, expected_contains: list[Any]) -> dict[str, Any]:
    checks = []
    for expected in expected_contains:
        expected_text = str(expected)
        found, match_type = contains_expected_tolerant(answer, expected_text)
        checks.append(
            {
                "expected": expected_text,
                "found": found,
                "match_type": match_type,
            }
        )

    found_count = sum(1 for check in checks if check["found"])
    return {
        "passed": found_count == len(checks),
        "found_count": found_count,
        "expected_count": len(checks),
        "checks": checks,
        "scoring": "substring_or_numeric_equivalent_or_rounded",
    }


def make_llm_judge_prompt(question: dict[str, Any], answer: str) -> str:
    payload = {
        "question_id": question["id"],
        "question": question["prompt"],
        "expected_contains": question["expected_contains"],
        "reference_answer": question["reference_answer"],
        "candidate_answer": answer,
    }
    return (
        "You are a strict benchmark judging agent. Judge the candidate answer only against the supplied "
        "question, expected evidence, and reference answer. Do not use outside knowledge or infer a different "
        "answer.\n\n"
        "A candidate answer passes only if it is semantically consistent with the reference answer and covers "
        "the material facts requested by the question. Treat expected_contains as required evidence values, but "
        "accept equivalent formatting such as 34 and 34.00, rounded numeric values at the precision requested "
        "by the question, and harmless prose differences. Fail answers that omit a requested identifier, count, "
        "category, field value, or numeric result; contradict the reference answer; answer a different question; "
        "or claim no matching data when the reference has an answer.\n\n"
        "Return exactly one JSON object with this schema:\n"
        "{"
        '"passed":true|false,'
        '"confidence":"high|medium|low",'
        '"checks":[{"expected":"value","status":"present|equivalent|missing|contradicted","notes":"short note"}],'
        '"missing":["required facts missing from the candidate answer"],'
        '"incorrect":["facts contradicted or wrong in the candidate answer"],'
        '"reason":"one concise sentence"'
        "}\n\n"
        "Benchmark item:\n"
        f"{json_dumps(payload)}"
    )


def json_dumps(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, indent=2)


def normalize_llm_judge_result(raw: str, metadata: dict[str, Any]) -> dict[str, Any]:
    try:
        data = plain_eval.extract_json_object(raw)
    except Exception as exc:  # noqa: BLE001
        return {
            "passed": False,
            "found_count": 0,
            "expected_count": 0,
            "checks": [],
            "scoring": "llm_judge",
            "judge_error": f"Could not parse judge JSON: {exc}",
            "judge_raw": raw,
            "judge_metadata": metadata,
        }

    checks = data.get("checks")
    if not isinstance(checks, list):
        checks = []
    normalized_checks = []
    for item in checks:
        if not isinstance(item, dict):
            continue
        normalized_checks.append(
            {
                "expected": str(item.get("expected", "")),
                "status": str(item.get("status", "")),
                "notes": str(item.get("notes", "")),
            }
        )

    missing = data.get("missing")
    incorrect = data.get("incorrect")
    if not isinstance(missing, list):
        missing = []
    if not isinstance(incorrect, list):
        incorrect = []

    found_count = sum(
        1
        for check in normalized_checks
        if check["status"] in {"present", "equivalent"}
    )
    return {
        "passed": bool(data.get("passed")),
        "found_count": found_count,
        "expected_count": len(normalized_checks),
        "checks": normalized_checks,
        "missing": [str(item) for item in missing],
        "incorrect": [str(item) for item in incorrect],
        "confidence": str(data.get("confidence", "")),
        "reason": str(data.get("reason", "")),
        "scoring": "llm_judge",
        "judge_raw": raw,
        "judge_metadata": metadata,
    }


def score_answer_llm_judge(
    *,
    answer: str,
    question: dict[str, Any],
    provider: str,
    model: str,
    max_output_tokens: int,
    temperature: float,
    timeout_seconds: int,
    retries: int,
) -> dict[str, Any]:
    prompt = make_llm_judge_prompt(question, answer)
    started = time.perf_counter()
    try:
        raw, metadata = plain_eval.call_with_retries(
            provider,
            prompt,
            model,
            max_output_tokens,
            temperature,
            timeout_seconds,
            retries,
        )
    except Exception as exc:  # noqa: BLE001
        return {
            "passed": False,
            "found_count": 0,
            "expected_count": len(question.get("expected_contains", [])),
            "checks": [],
            "scoring": "llm_judge",
            "judge_error": str(exc),
            "judge_elapsed_seconds": round(time.perf_counter() - started, 3),
        }
    score = normalize_llm_judge_result(raw, metadata)
    score["judge_elapsed_seconds"] = round(time.perf_counter() - started, 3)
    return score


def single_task_prompt_errors(prompt: str) -> list[str]:
    errors: list[str] = []
    if prompt.count("?") > 1:
        errors.append("prompt must contain at most one question mark")

    for pattern, reason in BUNDLED_QUERY_PATTERNS:
        if pattern.search(prompt):
            errors.append(f"prompt appears to contain bundled queries: {reason}")
    return errors


def validate_benchmark_questions(questions: list[dict[str, Any]], path: Path) -> None:
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
        if isinstance(question.get("prompt"), str):
            for error in single_task_prompt_errors(question["prompt"]):
                errors.append(f"{location} {error}.")

        expected_contains = question.get("expected_contains")
        if not isinstance(expected_contains, list) or not expected_contains:
            errors.append(f"{location} requires a non-empty expected_contains array.")
            continue
        for expected_index, expected in enumerate(expected_contains, start=1):
            if not isinstance(expected, str) or not expected.strip():
                errors.append(
                    f"{location} expected_contains[{expected_index}] must be a non-empty string."
                )

        if not isinstance(question.get("reference_answer"), str):
            continue
        reference_score = score_answer_tolerant(question["reference_answer"], expected_contains)
        if not reference_score["passed"]:
            missing = [
                check["expected"]
                for check in reference_score["checks"]
                if not check["found"]
            ]
            errors.append(
                f"{location} reference_answer does not contain expected values: {missing}"
            )
    if errors:
        raise ValueError("Invalid benchmark questions:\n" + "\n".join(f"- {error}" for error in errors))
