"""Build the MultiHiertt mini MCD example dataset.

The script downloads or reads the public MultiHiertt dev split, selects a
deterministic 50-example subset, and emits an unpacked MCD package plus a
JSONL QA file. It intentionally does not vendor the full upstream dataset.
"""

from __future__ import annotations

import argparse
import csv
import html
import json
import re
import shutil
import tempfile
import urllib.request
from dataclasses import dataclass
from html.parser import HTMLParser
from pathlib import Path
from typing import Any


SOURCE_URL = (
    "https://huggingface.co/datasets/yilunzhao/MultiHiertt/resolve/main/"
    "multihiertt_data/dev.json"
)
CREATED_AT = "2026-06-05T00:00:00Z"
MAX_MATRIX_COLUMNS = 12


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


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--source", type=Path, help="Path to MultiHiertt dev.json")
    parser.add_argument("--output", type=Path, default=Path("datasets/multihiertt-mini"))
    parser.add_argument("--count", type=int, default=50)
    parser.add_argument("--arithmetic", type=int, default=40)
    parser.add_argument("--span-selection", type=int, default=10)
    return parser.parse_args()


def reset_generated_outputs(output: Path) -> None:
    for relative in [
        "unpacked",
        "qa_questions_50.jsonl",
        "answers.json",
        "ABOUT.md",
        "multihiertt-mini.mcd",
    ]:
        target = output / relative
        if target.is_dir():
            shutil.rmtree(target)
        elif target.exists():
            target.unlink()


def load_source(source: Path | None) -> list[dict[str, Any]]:
    if source is None:
        source = Path(tempfile.gettempdir()) / "multihiertt_dev.json"
        if not source.exists():
            print(f"Downloading MultiHiertt dev split to {source}")
            urllib.request.urlretrieve(SOURCE_URL, source)
    with source.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError("Expected MultiHiertt JSON split to be a list")
    return data


def select_examples(
    data: list[dict[str, Any]],
    *,
    count: int,
    arithmetic_count: int,
    span_count: int,
) -> list[dict[str, Any]]:
    selected: list[dict[str, Any]] = []
    type_limits = {"arithmetic": arithmetic_count, "span_selection": span_count}
    type_seen = {key: 0 for key in type_limits}

    for item in data:
        qtype = item.get("qa", {}).get("question_type")
        if qtype in type_limits and type_seen[qtype] < type_limits[qtype]:
            selected.append(item)
            type_seen[qtype] += 1
        if len(selected) == count:
            break

    if len(selected) != count:
        raise ValueError(f"Only selected {len(selected)} examples, expected {count}")
    return selected


def clean_id(value: str) -> str:
    return re.sub(r"[^a-zA-Z0-9_]+", "_", value).strip("_").lower()


def parse_table(markup: str) -> TableParse:
    parser = SimpleTableParser()
    parser.feed(markup)
    parser.close()
    return TableParse(rows=parser.rows)


def source_table_columns(parsed: TableParse) -> list[tuple[str, str, str, bool]]:
    width = max((len(row) for row in parsed.rows), default=0)
    header = parsed.rows[0] if parsed.rows else []
    columns: list[tuple[str, str, str, bool]] = [("row_index", "integer", "Row Index", False)]
    for index in range(width):
        label = " ".join(header[index].split()) if index < len(header) and header[index].strip() else f"Column {index}"
        columns.append((f"c{index}", "string", label, True))
    return columns


def source_table_csv_rows(parsed: TableParse) -> list[dict[str, Any]]:
    if not parsed.rows:
        return []
    width = max(len(row) for row in parsed.rows)
    body_rows = parsed.rows[1:]
    rows: list[dict[str, Any]] = []
    for row_index, parsed_row in enumerate(body_rows, start=1):
        row: dict[str, Any] = {"row_index": row_index}
        for col_index in range(width):
            row[f"c{col_index}"] = parsed_row[col_index] if col_index < len(parsed_row) else ""
        rows.append(row)
    return rows


def source_table_view(table_id: str, columns: list[tuple[str, str, str, bool]]) -> dict[str, Any]:
    return {
        "id": "default",
        "table": table_id,
        "display": "table",
        "style": {"prominence": "primary"},
        "columns": [
            {"name": name, "label": label}
            for name, _typ, label, _nullable in columns
            if name != "row_index"
        ],
    }


def append_table_directive(markdown_lines: list[str], *, mini_id: str, table_index: int, source_table_id: str) -> None:
    markdown_lines.extend(
        [
            f"### Table {table_index}",
            "",
            ":::table",
            f"ref: {source_table_id}",
            f"table: {source_table_id}",
            "view: default",
            "display: table",
            f"caption: {mini_id} Table {table_index}",
            "numbering: auto",
            ":::",
            "",
        ]
    )


def append_source_document(
    markdown_lines: list[str],
    *,
    mini_id: str,
    paragraphs: list[str],
    parsed_tables: list[TableParse],
    source_table_ids: list[str],
) -> None:
    markdown_lines.extend(
        [
            f"## {mini_id}",
            "",
        ]
    )

    emitted_tables: set[int] = set()
    for text in paragraphs:
        table_marker = re.fullmatch(r"\s*##\s*Table\s+(\d+)\s*##\s*", text)
        if table_marker:
            table_index = int(table_marker.group(1))
            if table_index < len(parsed_tables):
                append_table_directive(
                    markdown_lines,
                    mini_id=mini_id,
                    table_index=table_index,
                    source_table_id=source_table_ids[table_index],
                )
                emitted_tables.add(table_index)
            else:
                markdown_lines.extend([text, ""])
            continue

        markdown_lines.extend([text, ""])

    for table_index, parsed in enumerate(parsed_tables):
        if table_index in emitted_tables:
            continue
        append_table_directive(
            markdown_lines,
            mini_id=mini_id,
            table_index=table_index,
            source_table_id=source_table_ids[table_index],
        )


def write_json(path: Path, data: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, Any]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        writer.writeheader()
        for row in rows:
            writer.writerow({key: row.get(key, "") for key in fieldnames})


def schema(table_id: str, primary_key: list[str], columns: list[tuple[str, str, str, bool]]) -> dict[str, Any]:
    return {
        "id": table_id,
        "primaryKey": primary_key,
        "columns": [
            {"name": name, "type": typ, "label": label, "nullable": nullable}
            for name, typ, label, nullable in columns
        ],
    }


def view(table_id: str, columns: list[tuple[str, str, str, bool]]) -> dict[str, Any]:
    return {
        "id": "default",
        "table": table_id,
        "display": "table",
        "style": {"prominence": "primary"},
        "columns": [{"name": name, "label": label} for name, _typ, label, _nullable in columns],
    }


def build(output: Path, examples: list[dict[str, Any]]) -> None:
    reset_generated_outputs(output)

    unpacked = output / "unpacked"
    tables_dir = unpacked / "tables"
    content_dir = unpacked / "content"
    annotations_dir = unpacked / "annotations"
    provenance_dir = unpacked / "provenance"
    original_dir = output / "original_disconnected"

    example_rows: list[dict[str, Any]] = []
    paragraph_rows: list[dict[str, Any]] = []
    source_table_rows: list[dict[str, Any]] = []
    matrix_rows: list[dict[str, Any]] = []
    cell_rows: list[dict[str, Any]] = []
    question_rows: list[dict[str, Any]] = []
    answer_rows: list[dict[str, Any]] = []
    original_examples: list[dict[str, Any]] = []
    selection_map_rows: list[dict[str, Any]] = []
    source_document_tables: dict[str, dict[str, Any]] = {}

    markdown_lines: list[str] = []

    for index, item in enumerate(examples, start=1):
        mini_id = f"MHDEV-{index:04d}"
        uid = item["uid"]
        qa = item["qa"]
        text_evidence = {int(i) for i in qa.get("text_evidence", [])}
        table_evidence = set(qa.get("table_evidence", []))
        source_table_ids: list[str] = []
        original_examples.append(item)
        selection_map_rows.append(
            {
                "example_id": mini_id,
                "source_uid": uid,
                "source_split": "dev",
                "question": qa.get("question", ""),
                "source_record_index": index - 1,
            }
        )

        parsed_tables = [parse_table(markup) for markup in item.get("tables", [])]
        cell_refs_seen: set[str] = set()
        for table_index, parsed in enumerate(parsed_tables):
            source_table_id = f"{mini_id.lower().replace('-', '_')}_table_{table_index}"
            source_table_ids.append(source_table_id)
            document_columns = source_table_columns(parsed)
            source_document_tables[source_table_id] = {
                "id": source_table_id,
                "data": f"tables/source/{source_table_id}.csv",
                "schema": f"tables/source/{source_table_id}.schema.json",
                "view": f"tables/source/{source_table_id}.view.json",
                "columns": document_columns,
                "rows": source_table_csv_rows(parsed),
            }
            source_table_rows.append(
                {
                    "source_table_id": source_table_id,
                    "example_id": mini_id,
                    "source_uid": uid,
                    "table_index": table_index,
                    "row_count": len(parsed.rows),
                    "max_column_count": max((len(row) for row in parsed.rows), default=0),
                }
            )
            for row_index, parsed_row in enumerate(parsed.rows):
                row_id = f"{source_table_id}_row_{row_index}"
                row_record: dict[str, Any] = {
                    "row_id": row_id,
                    "source_table_id": source_table_id,
                    "example_id": mini_id,
                    "source_uid": uid,
                    "table_index": table_index,
                    "row_index": row_index,
                }
                for col_index in range(MAX_MATRIX_COLUMNS):
                    row_record[f"c{col_index}"] = parsed_row[col_index] if col_index < len(parsed_row) else ""
                matrix_rows.append(row_record)
                for col_index, cell_text in enumerate(parsed_row):
                    cell_ref = f"{table_index}-{row_index}-{col_index}"
                    cell_refs_seen.add(cell_ref)
                    cell_rows.append(
                        {
                            "cell_id": f"{source_table_id}_r{row_index}_c{col_index}",
                            "source_table_id": source_table_id,
                            "example_id": mini_id,
                            "source_uid": uid,
                            "table_index": table_index,
                            "row_index": row_index,
                            "col_index": col_index,
                            "cell_ref": cell_ref,
                            "cell_text": cell_text,
                            "cell_description": item.get("table_description", {}).get(cell_ref, ""),
                        }
                    )
        for cell_ref, description in item.get("table_description", {}).items():
            if cell_ref in cell_refs_seen:
                continue
            try:
                table_index_text, row_index_text, col_index_text = cell_ref.split("-", 2)
                table_index = int(table_index_text)
                row_index = int(row_index_text)
                col_index = int(col_index_text)
            except ValueError:
                continue
            if table_index >= len(source_table_ids):
                continue
            source_table_id = source_table_ids[table_index]
            cell_rows.append(
                {
                    "cell_id": f"{source_table_id}_r{row_index}_c{col_index}_description",
                    "source_table_id": source_table_id,
                    "example_id": mini_id,
                    "source_uid": uid,
                    "table_index": table_index,
                    "row_index": row_index,
                    "col_index": col_index,
                    "cell_ref": cell_ref,
                    "cell_text": "",
                    "cell_description": description,
                }
            )

        for paragraph_index, text in enumerate(item.get("paragraphs", [])):
            paragraph_rows.append(
                {
                    "paragraph_id": f"{mini_id.lower().replace('-', '_')}_p{paragraph_index}",
                    "example_id": mini_id,
                    "source_uid": uid,
                    "paragraph_index": paragraph_index,
                    "paragraph_text": text,
                }
            )

        example_rows.append(
            {
                "example_id": mini_id,
                "source_uid": uid,
                "source_split": "dev",
                "question": qa.get("question", ""),
                "paragraph_count": len(item.get("paragraphs", [])),
                "table_count": len(parsed_tables),
            }
        )

        question_rows.append(
            {
                "id": f"multihiertt_mini_{index:04d}",
                "family_id": f"multihiertt_{qa.get('question_type', 'unknown')}",
                "example_id": mini_id,
                "source_uid": uid,
                "prompt": f"In MultiHiertt mini example {mini_id}, answer the benchmark question: {qa.get('question', '')}",
            }
        )
        answer_rows.append(
            {
                "id": f"multihiertt_mini_{index:04d}",
                "family_id": f"multihiertt_{qa.get('question_type', 'unknown')}",
                "example_id": mini_id,
                "source_uid": uid,
                "source_split": "dev",
                "question": qa.get("question", ""),
                "answer": str(qa.get("answer", "")),
                "question_type": qa.get("question_type", ""),
                "program": qa.get("program", ""),
                "text_evidence": sorted(text_evidence),
                "table_evidence": sorted(table_evidence),
                "expected_contains": [mini_id, str(qa.get("answer", ""))],
                "reference_answer": (
                    f"For {mini_id}, the answer is {qa.get('answer', '')}. "
                    f"Question type: {qa.get('question_type', '')}. "
                    f"Gold program: {qa.get('program', '') or 'not provided'}. "
                    f"Table evidence refs: {', '.join(sorted(table_evidence)) or 'none'}. "
                    f"Text evidence paragraph indexes: {', '.join(str(i) for i in sorted(text_evidence)) or 'none'}."
                ),
            }
        )

        append_source_document(
            markdown_lines,
            mini_id=mini_id,
            paragraphs=item.get("paragraphs", []),
            parsed_tables=parsed_tables,
            source_table_ids=source_table_ids,
        )

    columns_by_table: dict[str, list[tuple[str, str, str, bool]]] = {
        "multihiertt_examples": [
            ("example_id", "string", "Example ID", False),
            ("source_uid", "string", "Source UID", False),
            ("source_split", "string", "Source Split", False),
            ("question", "string", "Question", False),
            ("paragraph_count", "integer", "Paragraph Count", False),
            ("table_count", "integer", "Table Count", False),
        ],
        "multihiertt_paragraphs": [
            ("paragraph_id", "string", "Paragraph ID", False),
            ("example_id", "string", "Example ID", False),
            ("source_uid", "string", "Source UID", False),
            ("paragraph_index", "integer", "Paragraph Index", False),
            ("paragraph_text", "string", "Paragraph Text", False),
        ],
        "multihiertt_source_tables": [
            ("source_table_id", "string", "Source Table ID", False),
            ("example_id", "string", "Example ID", False),
            ("source_uid", "string", "Source UID", False),
            ("table_index", "integer", "Table Index", False),
            ("row_count", "integer", "Row Count", False),
            ("max_column_count", "integer", "Max Column Count", False),
        ],
        "multihiertt_table_rows": [
            ("row_id", "string", "Row ID", False),
            ("source_table_id", "string", "Source Table ID", False),
            ("example_id", "string", "Example ID", False),
            ("source_uid", "string", "Source UID", False),
            ("table_index", "integer", "Table Index", False),
            ("row_index", "integer", "Row Index", False),
            *[(f"c{i}", "string", f"Column {i}", True) for i in range(MAX_MATRIX_COLUMNS)],
        ],
        "multihiertt_cells": [
            ("cell_id", "string", "Cell ID", False),
            ("source_table_id", "string", "Source Table ID", False),
            ("example_id", "string", "Example ID", False),
            ("source_uid", "string", "Source UID", False),
            ("table_index", "integer", "Table Index", False),
            ("row_index", "integer", "Row Index", False),
            ("col_index", "integer", "Column Index", False),
            ("cell_ref", "string", "Cell Ref", False),
            ("cell_text", "string", "Cell Text", True),
            ("cell_description", "string", "Cell Description", True),
        ],
    }
    primary_keys = {
        "multihiertt_examples": ["example_id"],
        "multihiertt_paragraphs": ["paragraph_id"],
        "multihiertt_source_tables": ["source_table_id"],
        "multihiertt_table_rows": ["row_id"],
        "multihiertt_cells": ["cell_id"],
    }
    table_rows_by_id = {
        "multihiertt_examples": example_rows,
        "multihiertt_paragraphs": paragraph_rows,
        "multihiertt_source_tables": source_table_rows,
        "multihiertt_table_rows": matrix_rows,
        "multihiertt_cells": cell_rows,
    }

    for table_id, columns in columns_by_table.items():
        fieldnames = [name for name, _typ, _label, _nullable in columns]
        write_csv(tables_dir / f"{table_id}.csv", fieldnames, table_rows_by_id[table_id])
        write_json(tables_dir / f"{table_id}.schema.json", schema(table_id, primary_keys[table_id], columns))
        write_json(tables_dir / f"{table_id}.view.json", view(table_id, columns))

    for table_id, table_def in source_document_tables.items():
        columns = table_def["columns"]
        fieldnames = [name for name, _typ, _label, _nullable in columns]
        write_csv(unpacked / table_def["data"], fieldnames, table_def["rows"])
        write_json(unpacked / table_def["schema"], schema(table_id, ["row_index"], columns))
        write_json(unpacked / table_def["view"], source_table_view(table_id, columns))

    content_dir.mkdir(parents=True, exist_ok=True)
    (content_dir / "main.md").write_text("\n".join(markdown_lines), encoding="utf-8")

    manifest_tables = [
        {
            "id": table_id,
            "data": f"tables/{table_id}.csv",
            "schema": f"tables/{table_id}.schema.json",
            "views": {"default": f"tables/{table_id}.view.json"},
        }
        for table_id in columns_by_table
    ]
    manifest_tables.extend(
        {
            "id": table_id,
            "data": table_def["data"],
            "schema": table_def["schema"],
            "views": {"default": table_def["view"]},
        }
        for table_id, table_def in source_document_tables.items()
    )

    write_json(
        unpacked / "manifest.json",
        {
            "format": "MCD",
            "version": "0.1",
            "profile": "MCD-Core",
            "conformance": ["MCD-Core"],
            "entrypoint": "content/main.md",
            "title": "MultiHiertt Mini Financial Reasoning Package",
            "tables": manifest_tables,
            "annotations": [
                {
                    "id": "source-license-note",
                    "metadata": "annotations/source-license-note.annotation.json",
                }
            ],
            "externalData": [
                {
                    "id": "multihiertt-dev-json",
                    "uri": SOURCE_URL,
                    "mediaType": "application/json",
                    "description": "Public MultiHiertt dev split used to derive the 50-example mini package.",
                    "access": {
                        "requiresNetwork": True,
                        "requiresAuthentication": False,
                    },
                }
            ],
            "provenance": "provenance/provenance.json",
        },
    )

    write_json(
        annotations_dir / "source-license-note.annotation.json",
        {
            "id": "source-license-note",
            "target": {"type": "path", "path": "content/main.md"},
            "kind": "comment",
            "status": "resolved",
            "body": "This mini package is derived from the public MIT-licensed MultiHiertt dataset and keeps only a small selected subset.",
            "author": "mcd-example-builder",
            "created": CREATED_AT,
            "labels": ["source", "license", "benchmark"],
        },
    )

    generated_assets = [
        {
            "id": clean_id(path.as_posix()),
            "path": path.as_posix(),
            "mediaType": "application/json" if path.suffix == ".json" else "text/csv" if path.suffix == ".csv" else "text/markdown",
            "createdAt": CREATED_AT,
            "sourceRefs": ["multihiertt-dev-json"],
            "toolRefs": ["multihiertt-mini-builder"],
            "actorRefs": ["mcd-example-builder"],
        }
        for path in [
            Path("content/main.md"),
            *[Path(f"tables/{table_id}.csv") for table_id in columns_by_table],
            *[Path(f"tables/{table_id}.schema.json") for table_id in columns_by_table],
            *[Path(f"tables/{table_id}.view.json") for table_id in columns_by_table],
            *[
                Path(path)
                for table_def in source_document_tables.values()
                for path in (table_def["data"], table_def["schema"], table_def["view"])
            ],
        ]
    ]
    write_json(
        provenance_dir / "provenance.json",
        {
            "sources": [
                {
                    "id": "multihiertt-dev-json",
                    "uri": SOURCE_URL,
                    "mediaType": "application/json",
                    "title": "MultiHiertt dev split",
                    "createdAt": "2022-06-02T00:00:00Z",
                }
            ],
            "actors": [
                {
                    "id": "mcd-example-builder",
                    "kind": "agent",
                    "name": "MCD MultiHiertt mini builder",
                }
            ],
            "tools": [
                {
                    "id": "multihiertt-mini-builder",
                    "name": "build_multihiertt_mini.py",
                    "version": "0.1.0",
                }
            ],
            "generatedAssets": generated_assets,
        },
    )

    (unpacked / "mimetype").write_text("application/vnd.mcd+zip\n", encoding="utf-8")

    output.mkdir(parents=True, exist_ok=True)
    original_dir.mkdir(parents=True, exist_ok=True)
    write_json(original_dir / "dev_50.json", original_examples)
    write_csv(
        original_dir / "selection_map.csv",
        [
            "example_id",
            "source_uid",
            "source_split",
            "question",
            "source_record_index",
        ],
        selection_map_rows,
    )
    (original_dir / "ABOUT.md").write_text(
        "\n".join(
            [
                "# MultiHiertt Mini Original Disconnected Source",
                "",
                "This directory contains the same 50 selected examples as `../multihiertt-mini.mcd`, "
                "but in the original MultiHiertt JSON record shape instead of the normalized MCD package.",
                "",
                "- `dev_50.json` is a direct JSON array of the selected upstream dev records.",
                "- `selection_map.csv` maps local `MHDEV-000x` IDs to upstream `uid` values and source record indexes.",
                "- `../answers.json` is the evaluator-only gold-label file for these examples.",
                "",
                "Use this directory for original-source or disconnected-source benchmark modes. When prompting a model, "
                "strip evaluator fields from each record's `qa` object and provide only the source paragraphs, tables, "
                "table descriptions, and question text.",
                "",
                "The full upstream dataset is not vendored here.",
                "",
            ]
        ),
        encoding="utf-8",
    )

    with (output / "qa_questions_50.jsonl").open("w", encoding="utf-8") as f:
        for row in question_rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    write_json(
        output / "answers.json",
        {
            "dataset": "multihiertt-mini",
            "source_split": "dev",
            "created_at": CREATED_AT,
            "source_url": SOURCE_URL,
            "notes": (
                "Evaluator-only gold labels. Do not include this file in model prompts, MCD packages, "
                "or original-source context."
            ),
            "answers": answer_rows,
        },
    )

    (output / "ABOUT.md").write_text(
        "\n".join(
            [
                "# MultiHiertt Mini",
                "",
                "This directory contains a 50-example MCD package derived from the public MultiHiertt dev split.",
                "",
                "The package is designed to test MCD usage on acknowledged benchmark data: financial-report prose "
                "and multiple source tables per example.",
                "",
                "Model-facing files are answer-free. Evaluator labels, programs, and evidence refs live only in "
                "`answers.json`, which is evaluator-only and must not be included in prompts.",
                "",
                "The full upstream dataset is not vendored here. Rebuild with:",
                "",
                "```powershell",
                "python datasets\\multihiertt-mini\\scripts\\build_multihiertt_mini.py",
                "mcd pack datasets\\multihiertt-mini\\unpacked --output datasets\\multihiertt-mini\\multihiertt-mini.mcd",
                "```",
                "",
                "`original_disconnected/` contains the same 50 examples in the original MultiHiertt JSON shape for MCD-vs-original benchmark comparisons. "
                "For model prompts, use the original paragraphs, tables, table descriptions, and question text while excluding evaluator fields from `qa`.",
                "",
                "Upstream source: https://huggingface.co/datasets/yilunzhao/MultiHiertt",
                "",
                "Paper/repo: https://arxiv.org/abs/2206.01347 and https://github.com/psunlpgroup/MultiHiertt",
                "",
                "License: MIT, as declared by the upstream Hugging Face dataset and GitHub repository.",
                "",
            ]
        ),
        encoding="utf-8",
    )


def main() -> None:
    args = parse_args()
    data = load_source(args.source)
    examples = select_examples(
        data,
        count=args.count,
        arithmetic_count=args.arithmetic,
        span_count=args.span_selection,
    )
    build(args.output, examples)
    print(f"Wrote {len(examples)} examples to {args.output}")


if __name__ == "__main__":
    main()
