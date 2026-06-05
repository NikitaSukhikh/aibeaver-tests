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
        "original_disconnected",
        "qa_questions_50.jsonl",
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
    qa_rows: list[dict[str, Any]] = []
    original_examples: list[dict[str, Any]] = []
    selection_map_rows: list[dict[str, Any]] = []

    markdown_lines = [
        "# MultiHiertt Mini Financial Reasoning Package",
        "",
        "This package is a 50-example curated subset of the public MultiHiertt dev split. "
        "It is intended as an MCD example for hybrid reasoning over financial report prose, "
        "multiple source tables, cell-level evidence, and executable arithmetic programs.",
        "",
        "The source benchmark stores each document as paragraphs plus multiple HTML tables. "
        "This MCD package normalizes those records into queryable CSV tables while preserving "
        "the original example IDs, table indexes, row indexes, column indexes, and evidence refs.",
        "",
        "## Package Reference Map",
        "",
        "- `multihiertt_examples` stores one row per selected benchmark example.",
        "- `multihiertt_paragraphs` stores source paragraphs and marks text evidence rows.",
        "- `multihiertt_source_tables` stores one row per original HTML table.",
        "- `multihiertt_table_rows` stores each original table row as a fixed-width row matrix.",
        "- `multihiertt_cells` stores each table cell with the original `table-row-column` ref.",
        "- MultiHiertt cell refs use zero-based `table_index-row_index-col_index`, such as `0-2-4`.",
        "",
        "## Reasoning Notes",
        "",
        "For arithmetic questions, use `qa_program` from `multihiertt_examples` as the gold "
        "reasoning program when present. The program uses functions such as `add`, `subtract`, "
        "`multiply`, and `divide`; intermediate results are referenced as `#0`, `#1`, and so on.",
        "",
        "For evidence-grounded answers, inspect `multihiertt_paragraphs.is_text_evidence` and "
        "`multihiertt_cells.is_table_evidence`. The row matrix table is useful for scanning table "
        "shape, while the cell table is better for exact evidence references.",
        "",
    ]

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
                "answer": str(qa.get("answer", "")),
                "question_type": qa.get("question_type", ""),
                "source_record_index": index - 1,
            }
        )

        parsed_tables = [parse_table(markup) for markup in item.get("tables", [])]
        for table_index, parsed in enumerate(parsed_tables):
            source_table_id = f"{mini_id.lower().replace('-', '_')}_table_{table_index}"
            source_table_ids.append(source_table_id)
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
                            "is_table_evidence": str(cell_ref in table_evidence).lower(),
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
                    "is_text_evidence": str(paragraph_index in text_evidence).lower(),
                }
            )

        example_rows.append(
            {
                "example_id": mini_id,
                "source_uid": uid,
                "source_split": "dev",
                "question": qa.get("question", ""),
                "answer": str(qa.get("answer", "")),
                "question_type": qa.get("question_type", ""),
                "qa_program": qa.get("program", ""),
                "text_evidence_indices": ",".join(str(i) for i in sorted(text_evidence)),
                "table_evidence_refs": ",".join(sorted(table_evidence)),
                "paragraph_count": len(item.get("paragraphs", [])),
                "table_count": len(parsed_tables),
            }
        )

        qa_rows.append(
            {
                "id": f"multihiertt_mini_{index:04d}",
                "family_id": f"multihiertt_{qa.get('question_type', 'unknown')}",
                "prompt": f"In MultiHiertt mini example {mini_id}, answer the benchmark question: {qa.get('question', '')}",
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

        markdown_lines.extend(
            [
                f"## {mini_id}",
                "",
                f"Source UID: `{uid}`.",
                "",
                f"Question: {qa.get('question', '')}",
                "",
                f"Gold answer: `{qa.get('answer', '')}`.",
                "",
                f"Question type: `{qa.get('question_type', '')}`.",
                "",
            ]
        )
        if qa.get("program"):
            markdown_lines.extend(["Gold reasoning program:", "", f"`{qa['program']}`", ""])
        evidence_paragraphs = [item["paragraphs"][i] for i in sorted(text_evidence) if i < len(item["paragraphs"])]
        if evidence_paragraphs:
            markdown_lines.extend(["Evidence paragraphs:", ""])
            for paragraph_index in sorted(text_evidence):
                if paragraph_index < len(item["paragraphs"]):
                    markdown_lines.append(f"- Paragraph {paragraph_index}: {item['paragraphs'][paragraph_index]}")
            markdown_lines.append("")
        markdown_lines.extend(
            [
                f"Original table evidence refs: `{', '.join(sorted(table_evidence)) or 'none'}`.",
                "",
                f"Source tables for this example: `{', '.join(source_table_ids)}`.",
                "",
            ]
        )

    columns_by_table: dict[str, list[tuple[str, str, str, bool]]] = {
        "multihiertt_examples": [
            ("example_id", "string", "Example ID", False),
            ("source_uid", "string", "Source UID", False),
            ("source_split", "string", "Source Split", False),
            ("question", "string", "Question", False),
            ("answer", "string", "Answer", False),
            ("question_type", "string", "Question Type", False),
            ("qa_program", "string", "QA Program", True),
            ("text_evidence_indices", "string", "Text Evidence Indices", True),
            ("table_evidence_refs", "string", "Table Evidence Refs", True),
            ("paragraph_count", "integer", "Paragraph Count", False),
            ("table_count", "integer", "Table Count", False),
        ],
        "multihiertt_paragraphs": [
            ("paragraph_id", "string", "Paragraph ID", False),
            ("example_id", "string", "Example ID", False),
            ("source_uid", "string", "Source UID", False),
            ("paragraph_index", "integer", "Paragraph Index", False),
            ("paragraph_text", "string", "Paragraph Text", False),
            ("is_text_evidence", "boolean", "Is Text Evidence", False),
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
            ("is_table_evidence", "boolean", "Is Table Evidence", False),
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

    markdown_lines.extend(
        [
            "## Normalized Package Tables",
            "",
            ":::table",
            "ref: multihiertt-examples-table",
            "table: multihiertt_examples",
            "view: default",
            "display: table",
            "caption: MultiHiertt selected examples",
            "numbering: auto",
            ":::",
            "",
            ":::table",
            "ref: multihiertt-paragraphs-table",
            "table: multihiertt_paragraphs",
            "view: default",
            "display: table",
            "caption: MultiHiertt source paragraphs",
            "numbering: auto",
            ":::",
            "",
            ":::table",
            "ref: multihiertt-source-tables-table",
            "table: multihiertt_source_tables",
            "view: default",
            "display: table",
            "caption: MultiHiertt source table metadata",
            "numbering: auto",
            ":::",
            "",
            ":::table",
            "ref: multihiertt-table-rows-table",
            "table: multihiertt_table_rows",
            "view: default",
            "display: table",
            "caption: MultiHiertt row-matrix table data",
            "numbering: auto",
            ":::",
            "",
            ":::table",
            "ref: multihiertt-cells-table",
            "table: multihiertt_cells",
            "view: default",
            "display: table",
            "caption: MultiHiertt cell-level evidence table",
            "numbering: auto",
            ":::",
            "",
        ]
    )

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
            "answer",
            "question_type",
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
                "",
                "Use this directory for original-source or disconnected-source benchmark modes.",
                "",
                "The full upstream dataset is not vendored here.",
                "",
            ]
        ),
        encoding="utf-8",
    )

    with (output / "qa_questions_50.jsonl").open("w", encoding="utf-8") as f:
        for row in qa_rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    (output / "ABOUT.md").write_text(
        "\n".join(
            [
                "# MultiHiertt Mini",
                "",
                "This directory contains a 50-example MCD package derived from the public MultiHiertt dev split.",
                "",
                "The package is designed to test MCD usage on acknowledged benchmark data: financial-report prose, "
                "multiple source tables per example, cell-level evidence refs, and arithmetic reasoning programs.",
                "",
                "The full upstream dataset is not vendored here. Rebuild with:",
                "",
                "```powershell",
                "python datasets\\multihiertt-mini\\scripts\\build_multihiertt_mini.py",
                "mcd pack datasets\\multihiertt-mini\\unpacked --output datasets\\multihiertt-mini\\multihiertt-mini.mcd",
                "```",
                "",
                "`original_disconnected/` contains the same 50 examples in the original MultiHiertt JSON shape for MCD-vs-original benchmark comparisons.",
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
