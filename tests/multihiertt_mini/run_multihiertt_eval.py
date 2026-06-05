#!/usr/bin/env python3
"""Compare MultiHiertt mini QA quality in MCD-tool and original-JSON modes."""

from __future__ import annotations

import argparse
import copy
import csv
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
for import_dir in (PLAIN_EVAL_DIR, MCD_EVAL_DIR):
    sys.path.insert(0, str(import_dir))

import run_mcd_eval as mcd_eval  # noqa: E402
import run_plain_eval as plain_eval  # noqa: E402
from benchmark_validation import score_answer_llm_judge, score_answer_tolerant  # noqa: E402


DEFAULT_MCD_PATH = Path("datasets/multihiertt-mini/multihiertt-mini.mcd")
DEFAULT_ORIGINAL_DIR = Path("datasets/multihiertt-mini/original_disconnected")
DEFAULT_QUESTIONS_PATH = Path("datasets/multihiertt-mini/qa_questions_50.jsonl")
DEFAULT_ANSWERS_PATH = Path("datasets/multihiertt-mini/answers.json")
DEFAULT_RESULTS_ROOT = Path("results/multihiertt_mini")
DEFAULT_OPENAI_MODEL = "gpt-5.4"
DEFAULT_ANTHROPIC_MODEL = "claude-opus-4-5"
DEFAULT_XAI_MODEL = "grok-4.3"
DEFAULT_MAX_OUTPUT_TOKENS = 12000
DEFAULT_JUDGE_MAX_OUTPUT_TOKENS = 2000
PROVIDERS = ["openai", "anthropic", "xai"]
MODES = ["mcd", "original"]

MCD_MULTIHIERTT_GUIDANCE = (
    "MultiHiertt instructions: answer from the MCD package source paragraphs and tables only. "
    "Each prompt supplies the benchmark question and names an `example_id` such as MHDEV-0001; use that ID as the "
    "primary filter for all source queries. The full read-only MCD MCP tool surface is available: use "
    "`mcd_agent_context` or `mcd_inspect` for package overview, `mcd_markdown` for Markdown content, `mcd_search` "
    "for BM25 search across Markdown/schema/manifest/annotation/provenance, `mcd_schemas` for table schemas and "
    "relationships, `mcd_table` for table samples, `mcd_query` and `mcd_queries` for read-only SQL, "
    "`mcd_annotations` for annotations, `mcd_relationships` for declared relationships, `mcd_external_data` for "
    "external source references, `mcd_provenance` for provenance, and `mcd_chart`/`mcd_images` if visual assets are "
    "relevant. Prefer semantic MCD tools over treating the package as an opaque file. To read package text, call "
    "`mcd_markdown` for `content/main.md` context and use `mcd_search` with `kind='markdown'` to locate relevant "
    "prose quickly. For source-document prose, query "
    "`multihiertt_paragraphs` filtered by `example_id`; paragraph text is stored in `paragraph_text`. Inspect "
    "`multihiertt_source_tables` to identify the original table indexes for that example. Use `multihiertt_table_rows` "
    "to understand table shape and headers; "
    "it stores each original HTML table row as c0..c11. Use `multihiertt_cells` when exact cell lookup or a cell "
    "description is useful; cell refs are zero-based `table_index-row_index-col_index`. Use `multihiertt_paragraphs` "
    "for narrative facts and values that appear only in prose. Prefer `mcd_query` for exact lookup, filtering, "
    "sorting, aggregation, and arithmetic, casting numeric-looking text with SQLite `CAST(... AS REAL)` after "
    "removing `$`, `%`, commas, parentheses, or dash placeholders as needed. For arithmetic questions, retrieve the "
    "source numbers and compute the result explicitly in SQL where practical. Final answers should be concise and "
    "include the example id plus the requested answer value."
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
        help="Comma-separated modes: all, mcd, original, or mcd,original.",
    )
    parser.add_argument("--providers", nargs="+", choices=PROVIDERS, default=["openai"])
    parser.add_argument("--openai-model", default=os.getenv("OPENAI_MODEL", DEFAULT_OPENAI_MODEL))
    parser.add_argument("--anthropic-model", default=os.getenv("ANTHROPIC_MODEL", DEFAULT_ANTHROPIC_MODEL))
    parser.add_argument("--xai-model", default=os.getenv("XAI_MODEL", DEFAULT_XAI_MODEL))
    parser.add_argument("--questions", type=int, default=None, help="Run only the first N questions.")
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
        help="Use deterministic expected_contains scoring or an LLM judge over answers.json labels.",
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
        merged.append(
            {
                **question,
                "expected_contains": expected_contains,
                "reference_answer": reference_answer,
                "answer_label": answer,
            }
        )
    if errors:
        raise ValueError("Invalid MultiHiertt questions/answers:\n" + "\n".join(f"- {error}" for error in errors))
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


def make_original_prompt(question: dict[str, Any], source_record: dict[str, Any]) -> str:
    payload = {
        "example_id": question["example_id"],
        "question": question["prompt"],
        "source_record": source_record,
    }
    return (
        "Answer the MultiHierTT benchmark question using only the source record below. "
        "The question comes from the shared benchmark question file. The source record is copied from the original "
        "MultiHierTT JSON shape with its `qa` evaluator object removed; paragraph text, HTML table strings, and "
        "table descriptions are otherwise preserved. Do not use outside knowledge and do not assume labels that are "
        "not in the source record. "
        "For arithmetic questions, calculate from the visible source numbers.\n\n"
        "Return exactly one JSON object with this shape:\n"
        '{"answer":"concise answer with the example id and answer value"}\n\n'
        "Source payload:\n"
        f"{json.dumps(payload, ensure_ascii=False, indent=2)}"
    )


def install_mcd_prompt_patch() -> None:
    original_prompt = mcd_eval.make_mcd_agent_prompt
    original_compact = mcd_eval.make_mcd_agent_compact_prompt
    original_followup = mcd_eval.make_mcd_agent_followup_prompt

    def inject(prompt: str) -> str:
        for marker in ("\n\nQuestion:\n", "\n\nTool observation for the previous action:\n"):
            if marker in prompt:
                before, after = prompt.split(marker, 1)
                return f"{before}\n\n{MCD_MULTIHIERTT_GUIDANCE}{marker}{after}"
        return f"{prompt}\n\n{MCD_MULTIHIERTT_GUIDANCE}"

    def patched_prompt(**kwargs: Any) -> str:
        return inject(original_prompt(**kwargs))

    def patched_compact(*args: Any, **kwargs: Any) -> str:
        return inject(original_compact(*args, **kwargs))

    def patched_followup(*args: Any, **kwargs: Any) -> str:
        return inject(original_followup(*args, **kwargs))

    mcd_eval.make_mcd_agent_prompt = patched_prompt
    mcd_eval.make_mcd_agent_compact_prompt = patched_compact
    mcd_eval.make_mcd_agent_followup_prompt = patched_followup


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
    question: dict[str, Any],
    error: str | None,
    dry_run: bool,
    args: argparse.Namespace,
    config: ProviderConfig,
) -> dict[str, Any] | None:
    if dry_run or error:
        return None
    if args.scoring_mode == "llm_judge":
        judge_config = judge_provider_config(args, config)
        return score_answer_llm_judge(
            answer=answer,
            question=question,
            provider=judge_config.name,
            model=judge_config.model,
            max_output_tokens=args.judge_max_output_tokens,
            temperature=args.judge_temperature,
            timeout_seconds=args.judge_timeout_seconds,
            retries=args.judge_retries,
        )
    return score_answer_tolerant(answer, question["expected_contains"])


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


def run_mcd_mode(
    *,
    mcd_path: Path,
    mcd_summary_text: str,
    questions: list[dict[str, Any]],
    config: ProviderConfig,
    args: argparse.Namespace,
) -> list[dict[str, Any]]:
    rows = []
    for index, question in enumerate(questions, start=1):
        started = time.perf_counter()
        answer, metadata, trace, error = mcd_eval.run_mcd_agent_question(
            mcd_path=mcd_path,
            mcd_summary_text=mcd_summary_text,
            provider=config.name,
            model=config.model,
            question=model_question(question),
            args=args,
        )
        row = {
            "mode": "mcd",
            "provider": config.name,
            "model": config.model,
            "question_index": index,
            "question_id": question["id"],
            "example_id": question["example_id"],
            "family_id": question.get("family_id"),
            "question": question["prompt"],
            "expected_contains": question["expected_contains"],
            "reference_answer": question["reference_answer"],
            "answer": answer,
            "score": None,
            "error": error,
            "metadata": metadata,
            "trace": trace,
            "tool_calls": mcd_eval.tool_calls_from_trace(trace),
            "elapsed_seconds": round(time.perf_counter() - started, 3),
        }
        row["score"] = score_or_none(answer, question, error, args.dry_run, args, config)
        rows.append(row)
        print(f"{config.name} mcd {index}/{len(questions)} {question['id']}: {status_label(row)}", flush=True)
    return rows


def run_original_mode(
    *,
    records_by_example_id: dict[str, dict[str, Any]],
    questions: list[dict[str, Any]],
    config: ProviderConfig,
    args: argparse.Namespace,
) -> list[dict[str, Any]]:
    rows = []
    for index, question in enumerate(questions, start=1):
        started = time.perf_counter()
        source_record = records_by_example_id[question["example_id"]]
        prompt = make_original_prompt(model_question(question), source_record)
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
                answer = str(parsed.get("answer") or "").strip()
                if not answer:
                    error = "Provider response JSON did not include a non-empty answer."
                trace = [{"step": 1, "raw": raw, "parsed": parsed}]
            except Exception as exc:  # noqa: BLE001
                error = str(exc)
        row = {
            "mode": "original",
            "provider": config.name,
            "model": config.model,
            "question_index": index,
            "question_id": question["id"],
            "example_id": question["example_id"],
            "family_id": question.get("family_id"),
            "question": question["prompt"],
            "expected_contains": question["expected_contains"],
            "reference_answer": question["reference_answer"],
            "answer": answer,
            "score": None,
            "error": error,
            "metadata": metadata,
            "trace": trace,
            "tool_calls": 0,
            "elapsed_seconds": round(time.perf_counter() - started, 3),
        }
        row["score"] = score_or_none(answer, question, error, args.dry_run, args, config)
        rows.append(row)
        print(f"{config.name} original {index}/{len(questions)} {question['id']}: {status_label(row)}", flush=True)
    return rows


def mode_summary(rows: list[dict[str, Any]], provider: str, mode: str, model: str) -> dict[str, Any]:
    scored = sum(1 for row in rows if row.get("score") is not None)
    passed = sum(
        1
        for row in rows
        if isinstance(row.get("score"), dict) and row["score"].get("passed")
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
        "# MultiHiertt Mini MCD vs Original",
        "",
        f"- Created at: `{created_at}`",
        f"- MCD package: `{args.mcd_path}`",
        f"- Original package: `{args.original_dir}`",
        f"- Original JSON: `{args.original_json}`",
        f"- Questions: `{len(questions)}` from `{args.questions_path}`",
        f"- Evaluator labels: `{args.answers_path}`",
        f"- Modes: `{', '.join(modes)}`",
        f"- Scoring mode: `{args.scoring_mode}`",
        "",
        "| Provider | Mode | Model | Passed | Failed | Scored | Total | Pass rate | Errors | Tool calls |",
        "| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for item in summaries:
        lines.append(
            f"| {item['provider']} | {item['mode']} | `{item['model']}` | {item['passed']} | {item['failed']} | "
            f"{item['scored']} | {item['total']} | {item['pass_rate']:.1%} | {item['errors']} | {item['tool_calls']} |"
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
    install_mcd_prompt_patch()
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
    if "mcd" in modes and not args.mcd_path.exists():
        raise FileNotFoundError(args.mcd_path)
    if "original" in modes:
        if not args.original_dir.exists():
            raise FileNotFoundError(args.original_dir)
        if not args.original_json.exists():
            raise FileNotFoundError(args.original_json)

    questions = load_questions(args.questions_path, args.answers_path)
    if args.questions is not None:
        if args.questions < 1:
            raise ValueError("--questions must be a positive integer.")
        questions = questions[: args.questions]

    records_by_example_id = (
        load_original_records(args.original_dir, args.original_json, questions)
        if "original" in modes
        else {}
    )
    mcd_summary_text = mcd_eval.build_mcd_summary(args.mcd_path) if "mcd" in modes else ""
    output_dir = make_output_dir(args.results_root)
    created_at = datetime.now().isoformat(timespec="seconds")
    plain_eval.write_json(
        output_dir / "run_config.json",
        {
            "created_at": created_at,
            "providers": [config.__dict__ for config in configs],
            "modes": modes,
            "mcd_path": str(args.mcd_path),
            "original_dir": str(args.original_dir),
            "original_json": str(args.original_json),
            "questions_path": str(args.questions_path),
            "answers_path": str(args.answers_path),
            "question_count": len(questions),
            "scoring_mode": args.scoring_mode,
            "judge_provider": args.judge_provider,
            "judge_model": args.judge_model,
            "max_tool_steps": args.max_tool_steps,
            "mcd_mcp": args.mcd_mcp,
            "mcd_mcp_status": mcd_eval.mcd_mcp_status(args.mcd_mcp),
            "mcd_cli": args.mcd_cli,
            "mcd_cli_status": mcd_eval.mcd_cli_status(args.mcd_cli),
            "max_output_tokens": args.max_output_tokens,
            "temperature": args.temperature,
            "dry_run": args.dry_run,
            "prompt_profile": "multihiertt_mini_source_only",
        },
    )

    all_rows: list[dict[str, Any]] = []
    summaries: list[dict[str, Any]] = []
    rows_by_key: dict[tuple[str, str], list[dict[str, Any]]] = {}
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
                rows = run_original_mode(
                    records_by_example_id=records_by_example_id,
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
