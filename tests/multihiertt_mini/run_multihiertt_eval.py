#!/usr/bin/env python3
"""Compare MultiHiertt mini QA quality in MCD-extracted and original-JSON modes."""

from __future__ import annotations

import argparse
import copy
import csv
import html
import hashlib
import json
import os
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from html.parser import HTMLParser
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
MODES = ["mcd", "original", "mcd_agent", "original_agent"]
MATRIX_COLUMNS = [f"c{index}" for index in range(12)]


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
        "answer yes or no and include the compared source values. Final answers must be concise and include the "
        "example id plus the requested answer value."
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
        help="Comma-separated modes: all, mcd, original, mcd_agent, original_agent, or any subset.",
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
    parser.add_argument("--max-observation-chars", type=int, default=200000)
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


def sql_literal(value: str) -> str:
    return "'" + value.replace("'", "''") + "'"


def mcd_query_rows(doc: Any, sql: str) -> list[dict[str, Any]]:
    return [dict(row) for row in doc.query(sql).rows]


def load_mcd_source_records(mcd_path: Path, questions: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    doc = mcd_eval.mcd.open(mcd_path)
    records: dict[str, dict[str, Any]] = {}
    for question in questions:
        example_id = question["example_id"]
        example_literal = sql_literal(example_id)
        example_rows = mcd_query_rows(
            doc,
            (
                "select example_id, source_uid, source_split, question "
                "from multihiertt_examples "
                f"where example_id = {example_literal}"
            ),
        )
        if not example_rows:
            raise ValueError(f"MCD package is missing example {example_id}.")
        example = example_rows[0]

        paragraph_rows = mcd_query_rows(
            doc,
            (
                "select paragraph_index, paragraph_text "
                "from multihiertt_paragraphs "
                f"where example_id = {example_literal} "
                "order by paragraph_index"
            ),
        )
        table_rows = mcd_query_rows(
            doc,
            (
                "select source_table_id, table_index, row_count, max_column_count "
                "from multihiertt_source_tables "
                f"where example_id = {example_literal} "
                "order by table_index"
            ),
        )
        matrix_rows = mcd_query_rows(
            doc,
            (
                "select row_id, source_table_id, table_index, row_index, "
                f"{', '.join(MATRIX_COLUMNS)} "
                "from multihiertt_table_rows "
                f"where example_id = {example_literal} "
                "order by table_index, row_index"
            ),
        )
        cell_rows = mcd_query_rows(
            doc,
            (
                "select table_index, row_index, col_index, cell_ref, cell_text, cell_description "
                "from multihiertt_cells "
                f"where example_id = {example_literal} "
                "order by table_index, row_index, col_index"
            ),
        )

        rows_by_table: dict[int, list[dict[str, Any]]] = {}
        for row in matrix_rows:
            rows_by_table.setdefault(int(row["table_index"]), []).append(
                {
                    "row_id": row["row_id"],
                    "row_index": row["row_index"],
                    "cells": [row.get(column) for column in MATRIX_COLUMNS],
                }
            )

        tables: list[dict[str, Any]] = []
        for table in table_rows:
            table_index = int(table["table_index"])
            tables.append(
                {
                    "source_table_id": table["source_table_id"],
                    "table_index": table_index,
                    "row_count": table["row_count"],
                    "max_column_count": table["max_column_count"],
                    "rows": rows_by_table.get(table_index, []),
                }
            )

        records[example_id] = {
            "source_format": "mcd_extracted_row_matrix",
            "uid": example.get("source_uid"),
            "question": example.get("question"),
            "paragraphs": [row.get("paragraph_text") for row in paragraph_rows],
            "tables": tables,
            "table_description": {
                row["cell_ref"]: row.get("cell_description")
                for row in cell_rows
                if row.get("cell_ref") and row.get("cell_description")
            },
            "cells": cell_rows,
        }
    return records


def make_source_prompt(question: dict[str, Any], source_payload: dict[str, Any], source_access_note: str) -> str:
    payload = {
        "example_id": question["example_id"],
        "question": question["prompt"],
        "source_record": source_payload,
    }
    return (
        "You are answering one MultiHiertt mini benchmark question.\n\n"
        "Shared task rules:\n"
        f"{multihiertt_common_reasoning_rules()}\n\n"
        "Source access:\n"
        f"{source_access_note}\n\n"
        "Return exactly one JSON object with this shape:\n"
        '{"answer":"concise answer with the example id and answer value"}\n\n'
        "Source payload:\n"
        f"{json.dumps(payload, ensure_ascii=False, indent=2)}"
    )


def original_source_note() -> str:
    return (
        "The source record below is copied from the original MultiHiertt JSON shape with its `qa` evaluator object "
        "removed. Paragraph text, HTML table strings, and table descriptions are otherwise preserved. Use only this "
        "source record. Do not use outside knowledge and do not assume labels that are not in the source record."
    )


def mcd_source_note() -> str:
    return (
        "The source record below is extracted deterministically from the MCD package before the model call. It "
        "contains the same example's source paragraphs, source table row matrices, and cell descriptions from the "
        "MCD tables. Use only this source record. Do not call tools, use outside knowledge, or assume labels that "
        "are not in the source record."
    )


def build_original_agent_record(source_record: dict[str, Any], question: dict[str, Any]) -> dict[str, Any]:
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


def load_original_agent_records(
    records_by_example_id: dict[str, dict[str, Any]],
    questions: list[dict[str, Any]],
) -> dict[str, dict[str, Any]]:
    return {
        question["example_id"]: build_original_agent_record(records_by_example_id[question["example_id"]], question)
        for question in questions
    }


def original_agent_dataset_index(records_by_example_id: dict[str, dict[str, Any]]) -> str:
    rows = []
    for example_id, record in records_by_example_id.items():
        rows.append(
            {
                "example_id": example_id,
                "source_uid": record.get("source_uid"),
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
            }
        )
    return json.dumps({"source": "original_json_tools", "examples": rows}, ensure_ascii=False, indent=2)


def normalize_text(value: Any) -> str:
    return str(value or "").casefold()


def original_tool_overview(record: dict[str, Any]) -> dict[str, Any]:
    return {
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
    }


def original_tool_paragraphs(record: dict[str, Any], args: dict[str, Any]) -> dict[str, Any]:
    paragraphs = list(record.get("paragraphs", []))
    indexes = args.get("indexes")
    query = normalize_text(args.get("query"))
    limit = int(args.get("limit") or len(paragraphs) or 1)
    if isinstance(indexes, list):
        selected = [
            {"paragraph_index": int(index), "paragraph_text": paragraphs[int(index)]}
            for index in indexes
            if isinstance(index, int) and 0 <= int(index) < len(paragraphs)
        ]
    else:
        selected = []
        for index, text in enumerate(paragraphs):
            if not query or query in normalize_text(text):
                selected.append({"paragraph_index": index, "paragraph_text": text})
            if len(selected) >= limit:
                break
    return {
        "tool": "paragraphs",
        "returned": len(selected),
        "total_paragraphs": len(paragraphs),
        "rows": selected,
    }


def original_tool_table(record: dict[str, Any], args: dict[str, Any]) -> dict[str, Any]:
    table_index = int(args.get("table_index"))
    start_row = int(args.get("start_row") or 0)
    limit_arg = args.get("limit")
    table = next((item for item in record.get("tables", []) if int(item["table_index"]) == table_index), None)
    if table is None:
        raise ValueError(f"Unknown table_index {table_index}.")
    rows = table.get("rows", [])
    limit = int(limit_arg) if limit_arg is not None else len(rows)
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


def original_tool_search(record: dict[str, Any], args: dict[str, Any]) -> dict[str, Any]:
    query = normalize_text(args.get("query"))
    if not query:
        raise ValueError("search query is required.")
    scope = str(args.get("scope") or "all")
    limit = int(args.get("limit") or 20)
    matches: list[dict[str, Any]] = []
    if scope in {"all", "paragraphs"}:
        for paragraph_index, text in enumerate(record.get("paragraphs", [])):
            if query in normalize_text(text):
                matches.append(
                    {
                        "kind": "paragraph",
                        "paragraph_index": paragraph_index,
                        "text": text,
                    }
                )
                if len(matches) >= limit:
                    return {"tool": "search", "query": args.get("query"), "returned": len(matches), "rows": matches}
    if scope in {"all", "tables"}:
        for table in record.get("tables", []):
            for row in table.get("rows", []):
                for col_index, cell_text in enumerate(row.get("cells", [])):
                    if query in normalize_text(cell_text):
                        matches.append(
                            {
                                "kind": "table_cell",
                                "table_index": table["table_index"],
                                "row_index": row["row_index"],
                                "col_index": col_index,
                                "cell_text": cell_text,
                                "row_cells": row.get("cells"),
                            }
                        )
                        if len(matches) >= limit:
                            return {"tool": "search", "query": args.get("query"), "returned": len(matches), "rows": matches}
    if scope in {"all", "descriptions"}:
        for cell_ref, description in record.get("table_description", {}).items():
            if query in normalize_text(description) or query in normalize_text(cell_ref):
                matches.append(
                    {
                        "kind": "cell_description",
                        "cell_ref": cell_ref,
                        "description": description,
                    }
                )
                if len(matches) >= limit:
                    break
    return {"tool": "search", "query": args.get("query"), "returned": len(matches), "rows": matches}


def original_tool_cell_descriptions(record: dict[str, Any], args: dict[str, Any]) -> dict[str, Any]:
    refs = args.get("cell_refs")
    query = normalize_text(args.get("query"))
    limit = int(args.get("limit") or 50)
    descriptions = record.get("table_description", {})
    rows = []
    if isinstance(refs, list):
        for ref in refs:
            ref_text = str(ref)
            if ref_text in descriptions:
                rows.append({"cell_ref": ref_text, "description": descriptions[ref_text]})
    else:
        for ref, description in descriptions.items():
            if not query or query in normalize_text(ref) or query in normalize_text(description):
                rows.append({"cell_ref": ref, "description": description})
            if len(rows) >= limit:
                break
    return {"tool": "cell_descriptions", "returned": len(rows), "rows": rows}


def execute_original_agent_tool(record: dict[str, Any], tool: str, args: dict[str, Any]) -> dict[str, Any]:
    if tool == "overview":
        return original_tool_overview(record)
    if tool == "paragraphs":
        return original_tool_paragraphs(record, args)
    if tool == "table":
        return original_tool_table(record, args)
    if tool == "search":
        return original_tool_search(record, args)
    if tool == "cell_descriptions":
        return original_tool_cell_descriptions(record, args)
    raise ValueError(f"Unknown original source tool: {tool}")


def original_agent_tool_docs() -> dict[str, Any]:
    return {
        "overview": {"args": {}, "notes": "Return source counts and table inventory for the current example."},
        "paragraphs": {
            "args": {"indexes": "optional list of paragraph indexes", "query": "optional text", "limit": "optional integer"},
            "notes": "Read source paragraphs by index or substring search.",
        },
        "table": {
            "args": {"table_index": "integer", "start_row": "optional integer", "limit": "optional integer"},
            "notes": "Read parsed rows from an original HTML table. Rows contain row_index and cells.",
        },
        "search": {
            "args": {"query": "text", "scope": "all|paragraphs|tables|descriptions", "limit": "optional integer"},
            "notes": "Search paragraphs, parsed table cells, and cell descriptions.",
        },
        "cell_descriptions": {
            "args": {"cell_refs": "optional list like ['2-5-1']", "query": "optional text", "limit": "optional integer"},
            "notes": "Read original table_description entries by ref or search text.",
        },
    }


def make_original_agent_prompt(
    *,
    dataset_index: str,
    question: dict[str, Any],
    observations: list[dict[str, Any]],
) -> str:
    payload = {
        "id": question["id"],
        "example_id": question["example_id"],
        "source_uid": question.get("source_uid"),
        "question": question["prompt"],
    }
    return (
        "You are answering one MultiHiertt mini benchmark question using original JSON source tools.\n\n"
        "Shared task rules:\n"
        f"{multihiertt_common_reasoning_rules()}\n\n"
        "Tool protocol:\n"
        "Return exactly one JSON object and no prose. If you need source data, return "
        '{"tool":"tool_name","args":{...}}. When you know the answer, return '
        '{"answer":"concise answer with the example id and requested value"}. '
        "Do not return a tool call and an answer in the same response.\n\n"
        "Available original source tools:\n"
        f"{json.dumps(original_agent_tool_docs(), ensure_ascii=False, indent=2)}\n\n"
        "Dataset index:\n"
        f"{dataset_index}\n\n"
        "Question:\n"
        f"{json.dumps(payload, ensure_ascii=False, indent=2)}\n\n"
        "Previous tool observations:\n"
        f"{json.dumps(observations, ensure_ascii=False, indent=2)}"
    )


def parse_original_agent_action(text: str) -> dict[str, Any]:
    action = plain_eval.extract_json_object(text)
    if "answer" in action:
        return {"answer": str(action["answer"])}
    if "tool" in action:
        args = action.get("args", {})
        if not isinstance(args, dict):
            raise ValueError("Tool action 'args' must be an object.")
        return {"tool": str(action["tool"]), "args": args}
    raise ValueError("Agent response must contain either 'tool' or 'answer'.")


def original_agent_tool_calls_from_trace(trace: list[dict[str, Any]]) -> int:
    return sum(1 for item in trace if item.get("action", {}).get("tool"))


def run_original_agent_question(
    *,
    record: dict[str, Any],
    dataset_index: str,
    question: dict[str, Any],
    config: ProviderConfig,
    args: argparse.Namespace,
) -> tuple[str, dict[str, Any], list[dict[str, Any]], str | None]:
    if args.dry_run:
        return (
            "",
            {"dry_run": True, "token_usage": {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}},
            [],
            None,
        )

    observations: list[dict[str, Any]] = []
    trace: list[dict[str, Any]] = []
    call_usages: list[dict[str, int]] = []
    total_usage = {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}
    metadata: dict[str, Any] = {}
    for step in range(1, args.max_tool_steps + 1):
        prompt = make_original_agent_prompt(dataset_index=dataset_index, question=question, observations=observations)
        raw, metadata = plain_eval.call_with_retries(
            config.name,
            prompt,
            config.model,
            args.max_output_tokens,
            args.temperature,
            args.timeout_seconds,
            args.retries,
        )
        token_usage = mcd_eval.token_usage_from_metadata(metadata)
        call_usages.append(token_usage)
        total_usage = mcd_eval.add_token_usage(total_usage, token_usage)
        metadata = {**metadata, "token_usage": total_usage, "call_token_usage": call_usages}
        try:
            action = parse_original_agent_action(raw)
        except Exception as exc:  # noqa: BLE001
            trace.append({"step": step, "raw": raw, "error": str(exc)})
            return "", metadata, trace, f"Could not parse original agent action: {exc}"
        trace_item: dict[str, Any] = {"step": step, "raw": raw, "action": action}
        if "answer" in action:
            trace.append(trace_item)
            return action["answer"], metadata, trace, None
        try:
            observation = execute_original_agent_tool(record, action["tool"], action["args"])
        except Exception as exc:  # noqa: BLE001
            observation = {"tool": action["tool"], "error": str(exc)}
        trace_item["observation"] = observation
        trace.append(trace_item)
        observations.append(
            {
                "step": step,
                "tool": action["tool"],
                "args": action["args"],
                "observation": observation,
            }
        )
    return "", metadata, trace, f"Original agent did not answer within {args.max_tool_steps} tool steps."


def mcd_agent_table_map() -> str:
    return (
        "`multihiertt_examples`: one row per benchmark example. "
        "`multihiertt_paragraphs`: source prose with paragraph_index and paragraph_text. "
        "`multihiertt_source_tables`: original table inventory with table_index, row_count, and max_column_count. "
        "`multihiertt_table_rows`: parsed table row matrix with row_id, table_index, row_index, and c0..c11. "
        "`multihiertt_cells`: exact cell lookup with cell_ref, cell_text, and cell_description."
    )


def mcd_agent_tool_protocol() -> str:
    return (
        "Return exactly one JSON object and no prose. If you need source data, return "
        '{"mcp_tool":"mcd_query","arguments":{"sql":"single SELECT or WITH statement"}}. '
        "When you know the answer, return "
        '{"answer":"concise answer with the example id and requested value"}. '
        "Do not return a tool call and an answer in the same response. Use read-only SELECT/WITH SQL only."
    )


def make_mcd_agent_prompt(
    *,
    mcd_summary_text: str,
    mcp_status: dict[str, Any],
    question: dict[str, Any],
    observations: list[dict[str, Any]],
) -> str:
    payload = {
        "id": question["id"],
        "example_id": question["example_id"],
        "source_uid": question.get("source_uid"),
        "question": question["prompt"],
    }
    return (
        "You are answering one MultiHiertt mini benchmark question using MCD MCP tools.\n\n"
        "Shared task rules:\n"
        f"{multihiertt_common_reasoning_rules()}\n\n"
        "MCD table map:\n"
        f"{mcd_agent_table_map()}\n\n"
        "Tool protocol:\n"
        f"{mcd_agent_tool_protocol()}\n\n"
        "MCD source-access rules:\n"
        "Always filter source queries by the provided example_id. Use `multihiertt_source_tables` to identify "
        "candidate tables, `multihiertt_table_rows` to inspect row shape and headers, `multihiertt_cells` for exact "
        "cell refs/descriptions, and `multihiertt_paragraphs` for prose facts. If a computed SQL result is NULL, "
        "empty, failed, or contradicted by prior rows, do not answer from an earlier guess; issue a corrected query.\n\n"
        "Useful first queries:\n"
        "- select source_table_id, table_index, row_count, max_column_count from multihiertt_source_tables where "
        "example_id='<example_id>' order by table_index\n"
        "- select row_id, table_index, row_index, c0, c1, c2, c3, c4, c5, c6, c7, c8, c9, c10, c11 from "
        "multihiertt_table_rows where example_id='<example_id>' order by table_index, row_index\n"
        "- select paragraph_index, paragraph_text from multihiertt_paragraphs where example_id='<example_id>' "
        "and lower(paragraph_text) like lower('%term%')\n"
        "- select cell_ref, table_index, row_index, col_index, cell_text, cell_description from multihiertt_cells "
        "where example_id='<example_id>' and lower(cell_text) like lower('%term%')\n\n"
        "MCP status:\n"
        f"{json.dumps({'available': mcp_status.get('available_on_path_or_filesystem'), 'read_only_tools': mcp_status.get('read_only_tools')}, ensure_ascii=False, indent=2)}\n\n"
        "Dataset index:\n"
        f"{mcd_summary_text}\n\n"
        "Question:\n"
        f"{json.dumps(payload, ensure_ascii=False, indent=2)}\n\n"
        "Previous tool observations:\n"
        f"{json.dumps(observations, ensure_ascii=False, indent=2)}"
    )


def make_mcd_agent_compact_prompt(question: dict[str, Any], trace: list[dict[str, Any]], mcd_summary_text: str) -> str:
    observation_record = {"observation": trace[-1].get("observation", {})} if trace else {}
    has_rows = mcd_eval.observation_has_json_rows(observation_record)
    dataset_index = "" if has_rows else f"\n\nDataset index:\n{mcd_summary_text}"
    state = mcd_eval.build_mcd_agent_state(trace)
    payload = {
        "id": question["id"],
        "example_id": question["example_id"],
        "source_uid": question.get("source_uid"),
        "question": question["prompt"],
    }
    return (
        "Continue the same MultiHiertt mini MCD-agent task.\n\n"
        "Shared task rules:\n"
        f"{multihiertt_common_reasoning_rules()}\n\n"
        "MCD table map:\n"
        f"{mcd_agent_table_map()}\n\n"
        "Tool protocol:\n"
        f"{mcd_agent_tool_protocol()}\n\n"
        "Question:\n"
        f"{json.dumps(payload, ensure_ascii=False, indent=2)}\n\n"
        "Current state:\n"
        f"{json.dumps(state, ensure_ascii=False, indent=2)}"
        f"{dataset_index}"
    )


def make_mcd_agent_followup_prompt(observation_record: dict[str, Any]) -> str:
    return (
        "Tool observation for the previous MultiHiertt MCD-agent action:\n"
        f"{json.dumps(observation_record, ensure_ascii=False, indent=2)}\n\n"
        f"{mcd_agent_tool_protocol()} If this observation contains all needed evidence, answer now. "
        "If not, call one targeted MCD tool."
    )


def install_mcd_agent_prompt_patch() -> None:
    mcd_eval.make_mcd_agent_prompt = make_mcd_agent_prompt
    mcd_eval.make_mcd_agent_compact_prompt = make_mcd_agent_compact_prompt
    mcd_eval.make_mcd_agent_followup_prompt = make_mcd_agent_followup_prompt


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
    return evaluate_answer(
        answer=answer,
        evaluation_question=question["evaluation_question"],
        args=args,
        config=config,
    )


def evaluate_answer(
    *,
    answer: str,
    evaluation_question: dict[str, Any],
    args: argparse.Namespace,
    config: ProviderConfig,
) -> dict[str, Any]:
    if args.scoring_mode == "llm_judge":
        judge_config = judge_provider_config(args, config)
        return score_answer_llm_judge(
            answer=answer,
            question=evaluation_question,
            provider=judge_config.name,
            model=judge_config.model,
            max_output_tokens=args.judge_max_output_tokens,
            temperature=args.judge_temperature,
            timeout_seconds=args.judge_timeout_seconds,
            retries=args.judge_retries,
        )
    return score_answer_tolerant(answer, evaluation_question["expected_contains"])


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
                answer = str(parsed.get("answer") or "").strip()
                if not answer:
                    error = "Provider response JSON did not include a non-empty answer."
                trace = [{"step": 1, "raw": raw, "parsed": parsed}]
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
            "score": None,
            "error": error,
            "metadata": metadata,
            "trace": trace,
            "tool_calls": 0,
            "elapsed_seconds": round(time.perf_counter() - started, 3),
        }
        row["score"] = score_or_none(answer, question, error, args.dry_run, args, config)
        rows.append(row)
        print(f"{config.name} {mode} {index}/{len(questions)} {question['id']}: {status_label(row)}", flush=True)
    return rows


def run_mcd_agent_mode(
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
            "mode": "mcd_agent",
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
            "score": None,
            "error": error,
            "metadata": metadata,
            "trace": trace,
            "tool_calls": mcd_eval.tool_calls_from_trace(trace),
            "elapsed_seconds": round(time.perf_counter() - started, 3),
        }
        row["score"] = score_or_none(answer, question, error, args.dry_run, args, config)
        rows.append(row)
        print(f"{config.name} mcd_agent {index}/{len(questions)} {question['id']}: {status_label(row)}", flush=True)
    return rows


def run_original_agent_mode(
    *,
    records_by_example_id: dict[str, dict[str, Any]],
    dataset_index: str,
    questions: list[dict[str, Any]],
    config: ProviderConfig,
    args: argparse.Namespace,
) -> list[dict[str, Any]]:
    rows = []
    for index, question in enumerate(questions, start=1):
        started = time.perf_counter()
        answer, metadata, trace, error = run_original_agent_question(
            record=records_by_example_id[question["example_id"]],
            dataset_index=dataset_index,
            question=model_question(question),
            config=config,
            args=args,
        )
        row = {
            "mode": "original_agent",
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
            "score": None,
            "error": error,
            "metadata": metadata,
            "trace": trace,
            "tool_calls": original_agent_tool_calls_from_trace(trace),
            "elapsed_seconds": round(time.perf_counter() - started, 3),
        }
        row["score"] = score_or_none(answer, question, error, args.dry_run, args, config)
        rows.append(row)
        print(f"{config.name} original_agent {index}/{len(questions)} {question['id']}: {status_label(row)}", flush=True)
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
        "- Evaluator: shared per-question payload from `answers.json`; both modes use the same evaluator hash.",
        "- Format modes: `mcd` and `original` use one model call per question and no model-visible tools.",
        "- Agent modes: `mcd_agent` uses MCD MCP tools; `original_agent` uses original JSON source-inspection tools.",
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
    if any(mode in modes for mode in ("mcd", "mcd_agent")) and not args.mcd_path.exists():
        raise FileNotFoundError(args.mcd_path)
    if any(mode in modes for mode in ("original", "original_agent")):
        if not args.original_dir.exists():
            raise FileNotFoundError(args.original_dir)
        if not args.original_json.exists():
            raise FileNotFoundError(args.original_json)

    questions = load_questions(args.questions_path, args.answers_path)
    if args.questions is not None:
        if args.questions < 1:
            raise ValueError("--questions must be a positive integer.")
        questions = questions[: args.questions]

    original_records_by_example_id = (
        load_original_records(args.original_dir, args.original_json, questions)
        if any(mode in modes for mode in ("original", "original_agent"))
        else {}
    )
    mcd_records_by_example_id = (
        load_mcd_source_records(args.mcd_path, questions)
        if "mcd" in modes
        else {}
    )
    original_agent_records_by_example_id = (
        load_original_agent_records(original_records_by_example_id, questions)
        if "original_agent" in modes
        else {}
    )
    original_agent_index = (
        original_agent_dataset_index(original_agent_records_by_example_id)
        if "original_agent" in modes
        else ""
    )
    mcd_agent_summary_text = mcd_eval.build_mcd_summary(args.mcd_path) if "mcd_agent" in modes else ""
    if "mcd_agent" in modes:
        install_mcd_agent_prompt_patch()
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
            "judge_provider": args.judge_provider,
            "judge_model": args.judge_model,
            "format_modes": {
                "mcd": "single model call over deterministic pre-model extraction from MCD tables",
                "original": "single model call over original JSON source record",
            },
            "agent_modes": {
                "mcd_agent": "multi-step agent using MCD MCP tools",
                "original_agent": "multi-step agent using original JSON source-inspection tools",
            },
            "max_tool_steps": args.max_tool_steps,
            "mcd_mcp": args.mcd_mcp,
            "mcd_mcp_status": mcd_eval.mcd_mcp_status(args.mcd_mcp),
            "mcd_cli": args.mcd_cli,
            "mcd_cli_status": mcd_eval.mcd_cli_status(args.mcd_cli),
            "max_observation_chars": args.max_observation_chars,
            "max_output_tokens": args.max_output_tokens,
            "temperature": args.temperature,
            "dry_run": args.dry_run,
            "prompt_profile": "multihiertt_format_and_agentic_modes",
        },
    )

    all_rows: list[dict[str, Any]] = []
    summaries: list[dict[str, Any]] = []
    rows_by_key: dict[tuple[str, str], list[dict[str, Any]]] = {}
    for config in configs:
        for mode in modes:
            if mode == "mcd":
                rows = run_source_mode(
                    mode="mcd",
                    source_records_by_example_id=mcd_records_by_example_id,
                    source_access_note=mcd_source_note(),
                    questions=questions,
                    config=config,
                    args=args,
                )
            elif mode == "original":
                rows = run_source_mode(
                    mode="original",
                    source_records_by_example_id=original_records_by_example_id,
                    source_access_note=original_source_note(),
                    questions=questions,
                    config=config,
                    args=args,
                )
            elif mode == "mcd_agent":
                rows = run_mcd_agent_mode(
                    mcd_path=args.mcd_path,
                    mcd_summary_text=mcd_agent_summary_text,
                    questions=questions,
                    config=config,
                    args=args,
                )
            else:
                rows = run_original_agent_mode(
                    records_by_example_id=original_agent_records_by_example_id,
                    dataset_index=original_agent_index,
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
