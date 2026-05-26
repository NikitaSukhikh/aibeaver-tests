#!/usr/bin/env python3
"""Evaluate LLM answers over an MCD package using the Python mcd library."""

from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import time
import zipfile
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any

import mcd


REPO_ROOT = Path(__file__).resolve().parents[2]
PLAIN_EVAL_DIR = REPO_ROOT / "tests" / "llm_plain_eval"
sys.path.insert(0, str(PLAIN_EVAL_DIR))

import run_plain_eval as plain_eval  # noqa: E402


DEFAULT_MCD_PATH = Path("datasets/auto-manufacturer-tech-spec/auto-manufacturer-tech-spec.mcd")
DEFAULT_QUESTIONS_PATH = Path("datasets/auto-manufacturer-tech-spec/qa_pilot_questions_20.jsonl")
DEFAULT_RESULTS_ROOT = Path("results/llm_mcd")
DEFAULT_OPENAI_MODEL = "gpt-5.4"
DEFAULT_ANTHROPIC_MODEL = "claude-sonnet-4-5"
DEFAULT_XAI_MODEL = "grok-4.3"
DEFAULT_MAX_OUTPUT_TOKENS = 12000
PROVIDERS = ["openai", "anthropic", "xai"]


@dataclass(frozen=True)
class ProviderConfig:
    name: str
    model: str
    api_key_env: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--mcd-path", type=Path, default=DEFAULT_MCD_PATH)
    parser.add_argument("--questions", type=Path, default=DEFAULT_QUESTIONS_PATH)
    parser.add_argument("--results-root", type=Path, default=DEFAULT_RESULTS_ROOT)
    parser.add_argument("--providers", nargs="+", choices=PROVIDERS, default=["openai"])
    parser.add_argument("--openai-model", default=os.getenv("OPENAI_MODEL", DEFAULT_OPENAI_MODEL))
    parser.add_argument(
        "--anthropic-model", default=os.getenv("ANTHROPIC_MODEL", DEFAULT_ANTHROPIC_MODEL)
    )
    parser.add_argument("--xai-model", default=os.getenv("XAI_MODEL", DEFAULT_XAI_MODEL))
    parser.add_argument("--limit", type=int, default=None, help="Run only the first N questions.")
    parser.add_argument("--max-tool-steps", type=int, default=8)
    parser.add_argument("--mcd-cli", default=os.getenv("MCD_CLI", "mcd"))
    parser.add_argument("--cli-timeout-seconds", type=int, default=30)
    parser.add_argument("--python-timeout-seconds", type=int, default=30)
    parser.add_argument("--max-observation-chars", type=int, default=20000)
    parser.add_argument("--max-output-tokens", type=int, default=DEFAULT_MAX_OUTPUT_TOKENS)
    parser.add_argument("--temperature", type=float, default=0.0)
    parser.add_argument("--timeout-seconds", type=int, default=120)
    parser.add_argument("--retries", type=int, default=2)
    parser.add_argument(
        "--openai-stateful-responses",
        action="store_true",
        help=(
            "Use OpenAI previous_response_id chaining for follow-up tool steps. By default, follow-ups are "
            "compact stateless prompts because previous_response_id still counts prior context as input tokens."
        ),
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Write output structure without calling provider APIs or running tools.",
    )
    return parser.parse_args()


def provider_configs(args: argparse.Namespace) -> list[ProviderConfig]:
    configs = {
        "openai": ProviderConfig("openai", args.openai_model, "OPENAI_API_KEY"),
        "anthropic": ProviderConfig("anthropic", args.anthropic_model, "ANTHROPIC_API_KEY"),
        "xai": ProviderConfig("xai", args.xai_model, "XAI_API_KEY"),
    }
    return [configs[name] for name in args.providers]


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


def int_token(value: Any) -> int:
    try:
        if value is None:
            return 0
        return int(value)
    except (TypeError, ValueError):
        return 0


def token_usage_from_metadata(metadata: dict[str, Any]) -> dict[str, int]:
    usage = metadata.get("usage")
    if not isinstance(usage, dict):
        return {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}

    input_tokens = int_token(usage.get("input_tokens") or usage.get("prompt_tokens"))
    output_tokens = int_token(usage.get("output_tokens") or usage.get("completion_tokens"))
    input_tokens += int_token(usage.get("cache_creation_input_tokens"))
    input_tokens += int_token(usage.get("cache_read_input_tokens"))

    total_tokens = int_token(usage.get("total_tokens"))
    if not total_tokens:
        total_tokens = input_tokens + output_tokens

    return {
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "total_tokens": total_tokens,
    }


def add_token_usage(left: dict[str, int], right: dict[str, int]) -> dict[str, int]:
    return {
        "input_tokens": left.get("input_tokens", 0) + right.get("input_tokens", 0),
        "output_tokens": left.get("output_tokens", 0) + right.get("output_tokens", 0),
        "total_tokens": left.get("total_tokens", 0) + right.get("total_tokens", 0),
    }


def token_usage_from_rows(rows: list[dict[str, Any]]) -> dict[str, int]:
    total = {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}
    for row in rows:
        metadata = row.get("metadata", {})
        if not isinstance(metadata, dict):
            continue
        token_usage = metadata.get("token_usage")
        if isinstance(token_usage, dict):
            total = add_token_usage(total, {key: int_token(value) for key, value in token_usage.items()})
    return total


def format_tokens(value: int) -> str:
    return f"{value:,}"


def format_seconds(value: float) -> str:
    return f"{value:.1f} sec"


def tool_calls_from_trace(trace: list[dict[str, Any]]) -> int:
    """Count the number of tool calls in an agent trace."""
    return sum(1 for item in trace if item.get("action", {}).get("cli") or item.get("action", {}).get("python"))


def tool_calls_from_rows(rows: list[dict[str, Any]]) -> int:
    """Sum tool calls across all rows."""
    return sum(int(row.get("tool_calls") or 0) for row in rows)


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


def contains_expected_tolerant(answer: str, expected: str) -> tuple[bool, str]:
    if plain_eval.contains_expected(answer, expected):
        return True, "substring"

    expected_decimal = parse_decimal_text(expected)
    if expected_decimal is None:
        return False, "missing"

    for match in re.finditer(r"(?<![A-Za-z0-9_-])[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?=$|[^A-Za-z0-9_])", answer):
        actual_decimal = parse_decimal_text(match.group(0))
        if actual_decimal is not None and actual_decimal == expected_decimal:
            return True, "numeric_equivalent"
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
        "scoring": "substring_or_numeric_equivalent",
    }


def score_or_none(answer: str, question: dict[str, Any], error: str | None, dry_run: bool) -> dict[str, Any] | None:
    if dry_run or error:
        return None
    return score_answer_tolerant(answer, question["expected_contains"])


def passed(row: dict[str, Any]) -> bool:
    return bool(row.get("score") and row["score"].get("passed"))


def status_label(row: dict[str, Any]) -> str:
    if row.get("error"):
        return "ERROR"
    if row.get("score") is None:
        return "DRY" if row.get("metadata", {}).get("dry_run") else "UNSCORED"
    return "PASS" if passed(row) else "FAIL"


def serializable(value: Any) -> Any:
    try:
        json.dumps(value)
        return value
    except TypeError:
        if isinstance(value, Path):
            return str(value)
        if isinstance(value, dict):
            return {str(key): serializable(item) for key, item in value.items()}
        if isinstance(value, list):
            return [serializable(item) for item in value]
        return str(value)


def query_rows_or_empty(doc: Any, sql: str) -> list[dict[str, Any]]:
    try:
        return list(doc.query(sql).rows)
    except Exception:  # noqa: BLE001 - older mcd builds may not expose every metadata table.
        return []


def build_mcd_summary(mcd_path: Path) -> str:
    doc = mcd.open(mcd_path)
    validation = doc.validate().as_dict()
    context = doc.to_agent_context(include_tables=False)
    table_ids = [table["id"] for table in doc.to_agent_context(include_tables=True).get("tables", [])]
    manifest: dict[str, Any] = {}
    files: list[str] = []
    try:
        with zipfile.ZipFile(mcd_path) as package:
            files = sorted(name for name in package.namelist() if not name.endswith("/"))
            if "manifest.json" in files:
                manifest = json.loads(package.read("manifest.json").decode("utf-8"))
    except (OSError, zipfile.BadZipFile, json.JSONDecodeError):
        manifest = {}
        files = []

    table_paths = {
        str(table.get("id")): str(table.get("data"))
        for table in manifest.get("tables", [])
        if isinstance(table, dict) and table.get("id")
    }
    tables: list[dict[str, Any]] = []
    for table_id in table_ids:
        table = doc.table(table_id)
        rows = table.rows()
        columns: list[str] = []
        for column in table.schema.columns:
            if isinstance(column, dict):
                column_name = str(column.get("name")) if column.get("name") is not None else str(column)
                columns.append(column_name)
            else:
                columns.append(str(column))
        tables.append(
            {
                "table": table_id,
                "path": table_paths.get(table_id),
                "row_count": len(rows),
                "columns": columns,
            }
        )
    primary_key_rows = query_rows_or_empty(
        doc,
        "select table_id, column_name, ordinal from mcd_primary_keys order by table_id, ordinal",
    )
    primary_keys: dict[str, list[str]] = {}
    for row in primary_key_rows:
        table_id = row.get("table_id")
        column_name = row.get("column_name")
        if table_id and column_name:
            primary_keys.setdefault(str(table_id), []).append(str(column_name))
    foreign_key_rows = query_rows_or_empty(
        doc,
        (
            "select table_id, column_name, ordinal, ref_table_id, ref_column_name "
            "from mcd_foreign_keys order by table_id, ordinal"
        ),
    )
    foreign_keys = [
        f"{row.get('table_id')}.{row.get('column_name')} -> {row.get('ref_table_id')}.{row.get('ref_column_name')}"
        for row in foreign_key_rows
        if row.get("table_id") and row.get("column_name") and row.get("ref_table_id") and row.get("ref_column_name")
    ]
    summary = {
        "title": manifest.get("title") or context.get("title"),
        "entrypoint": manifest.get("entrypoint"),
        "files": files,
        "tables": tables,
        "metadata_tables": ["mcd_tables", "mcd_columns", "mcd_primary_keys", "mcd_foreign_keys", "mcd_units"],
        "primary_keys": primary_keys,
        "foreign_keys": foreign_keys,
        "validation_valid": bool(validation.get("valid")),
    }
    return json.dumps(serializable(summary), ensure_ascii=False, indent=2)


def extract_first_json_object(text: str) -> dict[str, Any]:
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = stripped.strip("`").strip()
        if stripped.casefold().startswith("json"):
            stripped = stripped[4:].strip()

    start = stripped.find("{")
    if start == -1:
        raise ValueError("Provider response did not contain a JSON object.")

    decoder = json.JSONDecoder()
    value, _end = decoder.raw_decode(stripped[start:])
    if not isinstance(value, dict):
        raise ValueError("Provider response JSON must be an object.")
    return value


def parse_agent_action(text: str) -> dict[str, Any]:
    action = extract_first_json_object(text)
    if "answer" in action:
        return {"answer": str(action["answer"])}
    if "cli" in action:
        return {"cli": str(action["cli"])}
    if "python" in action:
        return {"python": str(action["python"])}
    if "code" in action:
        return {"python": str(action["code"])}
    raise ValueError("Agent response must contain 'cli', 'python', or 'answer'.")


def quote_cmd_arg(value: str) -> str:
    escaped = value.replace('"', '\\"')
    return f'"{escaped}"'


def mcd_cli_status(mcd_cli: str) -> dict[str, Any]:
    if any(separator in mcd_cli for separator in ("/", "\\")):
        path = Path(mcd_cli)
        resolved = str(path.resolve()) if path.exists() else None
    else:
        resolved = shutil.which(mcd_cli)
    return {
        "configured_executable": mcd_cli,
        "resolved_executable": resolved,
        "available_on_path_or_filesystem": bool(resolved),
        "placeholder_executable": "{MCD_CLI}",
        "placeholder_package": "{MCD_PATH}",
    }


def expand_cli_command(command: str, *, mcd_cli: str, mcd_path: Path) -> str:
    replacements = {
        "{MCD_CLI}": quote_cmd_arg(mcd_cli),
        "$MCD_CLI": quote_cmd_arg(mcd_cli),
        "%MCD_CLI%": quote_cmd_arg(mcd_cli),
        "$env:MCD_CLI": quote_cmd_arg(mcd_cli),
        "{MCD_PATH}": quote_cmd_arg(str(mcd_path)),
        "$MCD_PATH": quote_cmd_arg(str(mcd_path)),
        "%MCD_PATH%": quote_cmd_arg(str(mcd_path)),
        "$env:MCD_PATH": quote_cmd_arg(str(mcd_path)),
    }
    expanded = command
    for placeholder, replacement in replacements.items():
        expanded = expanded.replace(f'"{placeholder}"', replacement)
        expanded = expanded.replace(f"'{placeholder}'", replacement)
    for placeholder, replacement in replacements.items():
        expanded = expanded.replace(placeholder, replacement)
    return expanded


def run_cli_tool(
    *,
    command: str,
    mcd_cli: str,
    mcd_path: Path,
    timeout_seconds: int,
    max_observation_chars: int,
) -> dict[str, Any]:
    expanded_command = expand_cli_command(command, mcd_cli=mcd_cli, mcd_path=mcd_path)
    env = {
        **os.environ,
        "MCD_PATH": str(mcd_path),
        "MCD_CLI": mcd_cli,
        "PYTHONIOENCODING": "utf-8",
    }
    started = time.perf_counter()
    try:
        completed = subprocess.run(
            expanded_command,
            cwd=str(REPO_ROOT),
            env=env,
            text=True,
            encoding="utf-8",
            errors="replace",
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            timeout=timeout_seconds,
            shell=True,
            check=False,
        )
        timed_out = False
        exit_code = completed.returncode
        stdout = completed.stdout
        stderr = completed.stderr
    except subprocess.TimeoutExpired as exc:
        timed_out = True
        exit_code = None
        stdout = (exc.stdout or "") if isinstance(exc.stdout, str) else ""
        stderr = (exc.stderr or "") if isinstance(exc.stderr, str) else ""

    return {
        "tool_type": "cli",
        "command": command,
        "expanded_command": expanded_command,
        "exit_code": exit_code,
        "timed_out": timed_out,
        "elapsed_seconds": round(time.perf_counter() - started, 3),
        "stdout": stdout[:max_observation_chars],
        "stderr": stderr[:max_observation_chars],
        "stdout_truncated": len(stdout) > max_observation_chars,
        "stderr_truncated": len(stderr) > max_observation_chars,
    }


def run_python_tool(
    *,
    code: str,
    mcd_path: Path,
    timeout_seconds: int,
    max_observation_chars: int,
) -> dict[str, Any]:
    with tempfile.TemporaryDirectory(prefix="llm_mcd_") as temp_dir:
        script_path = Path(temp_dir) / "agent_code.py"
        script_path.write_text(code, encoding="utf-8")
        env = {
            **os.environ,
            "MCD_PATH": str(mcd_path),
            "PYTHONIOENCODING": "utf-8",
        }
        started = time.perf_counter()
        try:
            completed = subprocess.run(
                [sys.executable, str(script_path)],
                cwd=str(REPO_ROOT),
                env=env,
                text=True,
                encoding="utf-8",
                errors="replace",
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                timeout=timeout_seconds,
                check=False,
            )
            timed_out = False
            exit_code = completed.returncode
            stdout = completed.stdout
            stderr = completed.stderr
        except subprocess.TimeoutExpired as exc:
            timed_out = True
            exit_code = None
            stdout = (exc.stdout or "") if isinstance(exc.stdout, str) else ""
            stderr = (exc.stderr or "") if isinstance(exc.stderr, str) else ""

    observation = {
        "tool_type": "python",
        "exit_code": exit_code,
        "timed_out": timed_out,
        "elapsed_seconds": round(time.perf_counter() - started, 3),
        "stdout": stdout[:max_observation_chars],
        "stderr": stderr[:max_observation_chars],
        "stdout_truncated": len(stdout) > max_observation_chars,
        "stderr_truncated": len(stderr) > max_observation_chars,
    }
    return observation


def tool_observation_failed(observation: dict[str, Any]) -> bool:
    if observation.get("timed_out"):
        return True
    exit_code = observation.get("exit_code")
    if exit_code not in (0, None):
        return True
    return bool(str(observation.get("stderr") or "").strip())


def make_mcd_agent_prompt(
    *,
    mcd_summary_text: str,
    cli_status: dict[str, Any],
    question: dict[str, Any],
    observations: list[dict[str, Any]],
) -> str:
    tool_docs = {
        "cli_query": {
            "cli": (
                "{MCD_CLI} query --format json {MCD_PATH} "
                '"select group_column, count(*) as row_count '
                "from table_id "
                "group by group_column order by row_count desc limit 3\""
            )
        },
        "cli_join": {
            "cli": (
                "{MCD_CLI} query --format json {MCD_PATH} "
                '"select a.id, a.foreign_id, a.metric_value, b.category, b.status '
                "from table_a a "
                "join table_b b on a.foreign_id = b.id "
                "order by cast(a.metric_value as real) asc limit 1\""
            )
        },
        "cli_schema_metadata": {
            "cli": (
                "{MCD_CLI} query --format json {MCD_PATH} "
                '"select table_id, column_name, type, label, nullable, unit_code, unit_label '
                "from mcd_columns "
                "order by table_id, ordinal\""
            )
        },
        "cli_primary_keys": {
            "cli": (
                "{MCD_CLI} query --format json {MCD_PATH} "
                '"select table_id, column_name, ordinal '
                "from mcd_primary_keys "
                "order by table_id, ordinal\""
            )
        },
        "cli_foreign_keys": {
            "cli": (
                "{MCD_CLI} query --format json {MCD_PATH} "
                '"select table_id, column_name, ordinal, ref_table_id, ref_column_name '
                "from mcd_foreign_keys "
                "order by table_id, ordinal\""
            )
        },
        "cli_units": {
            "cli": (
                "{MCD_CLI} query --format json {MCD_PATH} "
                '"select table_id, column_name, unit_code, unit_label, unit_custom '
                "from mcd_units "
                "order by table_id, column_name\""
            )
        },
        "cli_pragma_foreign_keys": {
            "cli": (
                "{MCD_CLI} query --format json {MCD_PATH} "
                '"select [table], [from], [to] from pragma_foreign_key_list(\'table_id\')"'
            )
        },
        "cli_pragma_table_keys": {
            "cli": (
                "{MCD_CLI} query --format json {MCD_PATH} "
                '"select name, type, pk from pragma_table_info(\'table_id\') where pk > 0"'
            )
        },
        "cli_markdown": {"cli": "{MCD_CLI} extract --markdown {MCD_PATH}"},
        "cli_schemas": {"cli": "{MCD_CLI} extract --schemas {MCD_PATH}"},
        "cli_tools": {"cli": "{MCD_CLI} tools --format json {MCD_PATH}"},
        "python_fallback": {
            "python": (
                "import os, json, mcd\n"
                "doc = mcd.open(os.environ['MCD_PATH'])\n"
                "rows = doc.table('table_id').rows()\n"
                "print(json.dumps(rows[:5], ensure_ascii=False))"
            )
        },
        "prefix_rule_example": {
            "cli": (
                "{MCD_CLI} query --format json {MCD_PATH} "
                '"select count(*) as violation_count '
                "from table_id "
                "where lower(substr(prefixed_code_column, 1, instr(prefixed_code_column, '-') - 1)) "
                "!= lower(expected_prefix_column)\""
            )
        },
        "fixed_precision_example": {
            "cli": (
                "{MCD_CLI} query --format json {MCD_PATH} "
                '"select id, printf(\'%.3f\', decimal_metric_column) as decimal_metric_column '
                "from table_id "
                "order by cast(decimal_metric_column as real) desc limit 2\""
            )
        },
        "count_plus_first_row_example": {
            "cli": (
                "{MCD_CLI} query --format json {MCD_PATH} "
                '"with matches as ('
                "select a.id, a.foreign_id, a.status, b.category, b.metric_value "
                "from table_a a "
                "join table_b b on a.foreign_id = b.id "
                "where lower(b.category)=lower('target_category') and cast(b.metric_value as real)>threshold "
                "and lower(a.status)<>lower('required_status')"
                ") "
                "select (select count(*) from matches) as violation_count, * "
                "from matches order by id asc limit 1\""
            )
        },
        "top_row_all_columns_example": {
            "cli": (
                "{MCD_CLI} query --format json {MCD_PATH} "
                '"select * from source_table '
                "where lower(category_column)=lower('target_category') "
                "order by cast(sort_metric_column as real) desc, id asc limit 1\""
            )
        },
        "grouped_counts_with_total_example": {
            "cli": (
                "{MCD_CLI} query --format json {MCD_PATH} "
                '"select count(*) as total_count, '
                "sum(case when lower(category_column)=lower('category_a') then 1 else 0 end) as category_a_count, "
                "sum(case when lower(category_column)=lower('category_b') then 1 else 0 end) as category_b_count "
                "from table_id "
                "where lower(category_column) in (lower('category_a'), lower('category_b')) "
                "and cast(metric_column as real)>threshold\""
            )
        },
    }
    return (
        "You are a document-grounded QA assistant evaluating an MCD package. "
        "Use the MCD CLI to inspect the package and query tables. Do not guess from memory. "
        "Always use `{MCD_PATH}` for the package path in CLI commands; do not use `.`, `$MCD_PATH`, or `%MCD_PATH%`. "
        "Prefer cli_query for complex relational work, such as joins, aggregate counts, computed expressions, "
        "grouped counts, sorting, and top-k queries. cli_query accepts read-only SQL SELECT statements over "
        "manifest table IDs. The MCD SQL runtime is SQLite-backed and also exposes reserved metadata tables: "
        "`mcd_tables`, `mcd_columns`, `mcd_primary_keys`, `mcd_foreign_keys`, and `mcd_units`. Use these tables "
        "through `mcd query` to discover exact table IDs, column names, data types, semantic units, primary keys, "
        "and foreign-key relationships before writing uncertain SQL. "
        "When a question requires a join and the relationship is not already certain from the dataset index, first "
        "query `mcd_foreign_keys` and join on the returned `table_id.column_name = ref_table_id.ref_column_name`; "
        "do not infer joins only from similar column names. Use `mcd_primary_keys` to identify stable row IDs to "
        "return in final answers. SQLite table constraints are created for declared keys where possible, so "
        "`pragma_table_info('table_id')` and `pragma_foreign_key_list('table_id')` are also valid read-only "
        "introspection queries. "
        "Use CAST(column AS REAL) or CAST(column AS INTEGER) for numeric comparisons, "
        "calculations, and ordering. For categorical string comparisons, use lower(column) = lower('value') "
        "or lower(column) IN (...), unless exact case is explicitly required. "
        "For prefix rules, compute the prefix from the field, for example "
        "substr(prefixed_code_column, 1, instr(prefixed_code_column, '-') - 1), and compare it to the expected "
        "prefix column; "
        "do not hardcode a list of allowed prefixes. "
        "For expected fixed-precision decimals, use printf formatting in SQL, such as printf('%.3f', decimal_metric_column). "
        "Use cli_markdown when the question depends on narrative rules in the dossier. Use cli_schemas or "
        "cli_schema_metadata when the question depends on declared schema information, primary keys, foreign keys, "
        "units, or nullable/enum/type metadata. For narrative-rule "
        "questions, inspect the relevant markdown sentence or use table schemas, then include source columns whose "
        "names overlap with or are semantically tied to the rule terms. "
        "Use Python only as a fallback if the CLI cannot express the needed calculation cleanly or if a metadata "
        "query is unavailable in the installed CLI; Python `doc.query(...)` exposes the same SQL metadata tables "
        "in updated `mcdee` builds. "
        "Do not guess from memory. Both tools execute in the repository root and return stdout/stderr. "
        "Keep tool output concise. "
        "If a tool observation has nonzero exit_code, stderr, or timed_out=true, treat it as failed: do not answer "
        "from that observation. Retry once with `{MCD_PATH}` and a single SQL statement; after repeated CLI errors, "
        "use Python fallback. "
        "If a result is capped or limited, do not compute final counts or extremes from capped samples unless "
        "the query sorted exactly by the required criterion. "
        "For each question, select and return all fields requested by the prompt, including example row details "
        "such as IDs, variants, category values, and numeric values, not only counts. "
        "When a question asks for a count plus a first/worst/best/top row, use a CTE or subqueries so the same "
        "successful observation includes both the total count and every field for that row. Do not use aggregate "
        "functions and ungrouped row fields together unless each row field is selected by an ordered subquery. "
        "When a question asks for grouped counts, include the overall total count as well as each group count. "
        "When a question asks for a top source row, include the identifier plus every rule-related source field "
        "named or implied by the question and narrative, not only the sort metric. If the rule references another "
        "measurement, limit, threshold, date, status, or requirement column in the same source table, include that "
        "column in the query and final answer even when it is not the ordering column. For narrative-rule questions, "
        "prefer selecting all columns for the selected/top source row (`select * ... limit 1`) or first inspect the "
        "schema with `mcd tools --format json {MCD_PATH}` before deciding which columns to project; then summarize "
        "only the relevant fields in the final answer. "
        "In the final answer, include the key condition values and field names used to select the result, not only "
        "the numeric answer. "
        "Return exactly one JSON object and no prose. Do not return a tool call and an answer in the same response.\n\n"
        "If you need data, return: "
        '{"cli":"{MCD_CLI} query --format json {MCD_PATH} \\"select ...\\""}\n'
        "If CLI is insufficient, return: "
        '{"python":"import os, json, mcd\\ndoc = mcd.open(os.environ[\'MCD_PATH\'])\\n..."}\n'
        "When you know the final answer, return:\n"
        '{"answer":"concise answer containing exact IDs, field names, condition values, and numbers"}\n\n'
        "Available tools and argument examples:\n"
        "The examples below are patterns. Replace placeholder table names, column names, threshold, and category "
        "values with actual names and values from the dataset index, question, and tool observations.\n"
        f"{json.dumps(tool_docs, ensure_ascii=False, indent=2)}\n\n"
        "CLI status:\n"
        f"{json.dumps({'available': cli_status.get('available_on_path_or_filesystem'), 'mcd_cli': cli_status.get('configured_executable')}, ensure_ascii=False, indent=2)}\n\n"
        "Dataset index:\n"
        f"{mcd_summary_text}\n\n"
        "Question:\n"
        f"{json.dumps({'id': question['id'], 'question': question['prompt']}, ensure_ascii=False, indent=2)}\n\n"
        "Previous tool observations:\n"
        f"{json.dumps(observations, ensure_ascii=False, indent=2)}"
    )


def make_mcd_agent_followup_prompt(observation_record: dict[str, Any]) -> str:
    return (
        "Tool observation for the previous action:\n"
        f"{json.dumps(observation_record, ensure_ascii=False, indent=2)}\n\n"
        "Continue answering the same question using the original instructions and dataset index. "
        "Return exactly one JSON object and no prose: either another `cli`/`python` action or the final `answer`. "
        "Do not repeat a successful tool call unless a different query is needed."
    )


def observation_has_json_rows(observation_record: dict[str, Any]) -> bool:
    observation = observation_record.get("observation", {})
    if not isinstance(observation, dict) or tool_observation_failed(observation):
        return False
    stdout = str(observation.get("stdout") or "").strip()
    try:
        payload = json.loads(stdout)
    except json.JSONDecodeError:
        return False
    return int_token(payload.get("rowCount")) > 0


def make_mcd_agent_compact_prompt(
    question: dict[str, Any],
    observation_record: dict[str, Any],
    mcd_summary_text: str,
) -> str:
    has_rows = observation_has_json_rows(observation_record)
    dataset_index = "" if has_rows else f"\n\nCompact dataset index:\n{mcd_summary_text}"
    return (
        "You are continuing an MCD package QA task. Use the latest tool observation below and answer the same "
        "question, or request one more concise tool call if more data is required.\n\n"
        "Rules: return exactly one JSON object and no prose. Use "
        '`{"answer":"..."}` for the final answer, '
        '`{"cli":"{MCD_CLI} query --format json {MCD_PATH} \\"select ...\\""}` for SQL, '
        "or `python` only if SQL is insufficient. Use `{MCD_PATH}` literally in CLI commands. "
        "Use read-only SQLite SELECT over manifest table IDs. Use CAST(... AS REAL/INTEGER) for numeric "
        "filtering, sorting, and calculations. For counts plus first/worst/best rows, use CTEs or ordered "
        "subqueries so the same successful observation contains the count and row details. Final answers must "
        "include exact IDs, requested fields, key condition values, and rule-related source fields present in "
        "the observation.\n\n"
        "Question:\n"
        f"{json.dumps({'id': question['id'], 'question': question['prompt']}, ensure_ascii=False, indent=2)}\n\n"
        "Latest tool observation:\n"
        f"{json.dumps(observation_record, ensure_ascii=False, indent=2)}"
        f"{dataset_index}"
    )


def openai_stateful_enabled(provider: str, args: argparse.Namespace) -> bool:
    return provider == "openai" and args.openai_stateful_responses


def call_openai_stateful(
    *,
    prompt: str,
    previous_response_id: str | None,
    model: str,
    max_output_tokens: int,
    temperature: float,
    timeout_seconds: int,
) -> tuple[str, dict[str, Any]]:
    api_key = plain_eval.require_env("OPENAI_API_KEY")
    payload: dict[str, Any] = {
        "model": model,
        "input": prompt,
        "max_output_tokens": max_output_tokens,
        "temperature": temperature,
    }
    if previous_response_id:
        payload["previous_response_id"] = previous_response_id

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
        "previous_response_id": previous_response_id,
        "stateful_response": True,
    }
    return plain_eval.extract_openai_text(response), metadata


def call_openai_stateful_with_retries(
    *,
    prompt: str,
    previous_response_id: str | None,
    model: str,
    max_output_tokens: int,
    temperature: float,
    timeout_seconds: int,
    retries: int,
) -> tuple[str, dict[str, Any]]:
    last_error: Exception | None = None
    for attempt in range(retries + 1):
        try:
            return call_openai_stateful(
                prompt=prompt,
                previous_response_id=previous_response_id,
                model=model,
                max_output_tokens=max_output_tokens,
                temperature=temperature,
                timeout_seconds=timeout_seconds,
            )
        except Exception as exc:  # noqa: BLE001 - preserve provider errors in result files.
            last_error = exc
            if attempt < retries:
                time.sleep(2**attempt)
    assert last_error is not None
    raise last_error


def run_mcd_agent_question(
    *,
    mcd_path: Path,
    mcd_summary_text: str,
    provider: str,
    model: str,
    question: dict[str, Any],
    args: argparse.Namespace,
) -> tuple[str, dict[str, Any], list[dict[str, Any]], str | None]:
    if args.dry_run:
        return (
            "",
            {
                "dry_run": True,
                "cli_status": mcd_cli_status(args.mcd_cli),
                "token_usage": {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0},
            },
            [],
            None,
        )

    observations: list[dict[str, Any]] = []
    trace: list[dict[str, Any]] = []
    call_usages: list[dict[str, int]] = []
    total_usage = {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0}
    metadata: dict[str, Any] = {}
    cli_status = mcd_cli_status(args.mcd_cli)
    failed_cli_count = 0
    use_stateful_openai = openai_stateful_enabled(provider, args)
    previous_response_id: str | None = None

    for step in range(1, args.max_tool_steps + 1):
        if step == 1:
            prompt = make_mcd_agent_prompt(
                mcd_summary_text=mcd_summary_text,
                cli_status=cli_status,
                question=question,
                observations=[],
            )
        elif use_stateful_openai:
            prompt = make_mcd_agent_followup_prompt(observations[-1])
        else:
            prompt = make_mcd_agent_compact_prompt(question, observations[-1], mcd_summary_text)

        if use_stateful_openai:
            raw, metadata = call_openai_stateful_with_retries(
                prompt=prompt,
                previous_response_id=previous_response_id,
                model=model,
                max_output_tokens=args.max_output_tokens,
                temperature=args.temperature,
                timeout_seconds=args.timeout_seconds,
                retries=args.retries,
            )
            if metadata.get("id"):
                previous_response_id = str(metadata["id"])
        else:
            raw, metadata = plain_eval.call_with_retries(
                provider,
                prompt,
                model,
                args.max_output_tokens,
                args.temperature,
                args.timeout_seconds,
                args.retries,
            )
        token_usage = token_usage_from_metadata(metadata)
        call_usages.append(token_usage)
        total_usage = add_token_usage(total_usage, token_usage)
        metadata = {
            **metadata,
            "cli_status": cli_status,
            "token_usage": total_usage,
            "call_token_usage": call_usages,
            "stateful_openai_responses": use_stateful_openai,
        }

        try:
            action = parse_agent_action(raw)
        except Exception as exc:  # noqa: BLE001
            trace.append({"step": step, "raw": raw, "error": str(exc)})
            return "", metadata, trace, f"Could not parse agent action: {exc}"

        trace_item: dict[str, Any] = {"step": step, "raw": raw, "action": action}
        if "answer" in action:
            trace.append(trace_item)
            return action["answer"], metadata, trace, None

        if "cli" in action:
            observation = run_cli_tool(
                command=action["cli"],
                mcd_cli=args.mcd_cli,
                mcd_path=mcd_path,
                timeout_seconds=args.cli_timeout_seconds,
                max_observation_chars=args.max_observation_chars,
            )
            if tool_observation_failed(observation):
                failed_cli_count += 1
                observation["harness_hint"] = (
                    "This CLI command failed. Do not answer from failed output. Use `{MCD_PATH}` as the package "
                    "path, avoid `.` as the package path, and submit exactly one SQL statement. "
                    f"Consecutive CLI failures: {failed_cli_count}. After repeated CLI failures, use the Python "
                    "fallback with mcd.open(os.environ['MCD_PATH'])."
                )
            else:
                failed_cli_count = 0
            observation_record = {"step": step, "tool_type": "cli", "cli": action["cli"], "observation": observation}
        else:
            observation = run_python_tool(
                code=action["python"],
                mcd_path=mcd_path,
                timeout_seconds=args.python_timeout_seconds,
                max_observation_chars=args.max_observation_chars,
            )
            if tool_observation_failed(observation):
                observation["harness_hint"] = (
                    "This Python fallback failed. Do not answer from failed output. Open the MCD package with "
                    "mcd.open(os.environ['MCD_PATH']) or read package members with zipfile if direct file paths "
                    "inside the .mcd are needed."
                )
            observation_record = {
                "step": step,
                "tool_type": "python",
                "python": action["python"],
                "observation": observation,
            }
        trace_item["observation"] = observation
        trace.append(trace_item)
        observations.append(observation_record)

    return "", metadata, trace, f"Agent did not answer within {args.max_tool_steps} tool steps."


def run_provider(
    *,
    mcd_path: Path,
    mcd_summary_text: str,
    questions: list[dict[str, Any]],
    config: ProviderConfig,
    args: argparse.Namespace,
) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    for index, question in enumerate(questions, start=1):
        started = time.perf_counter()
        answer, metadata, trace, error = run_mcd_agent_question(
            mcd_path=mcd_path,
            mcd_summary_text=mcd_summary_text,
            provider=config.name,
            model=config.model,
            question=question,
            args=args,
        )
        score = score_or_none(answer, question, error, args.dry_run)
        tool_calls = tool_calls_from_trace(trace)
        row = {
            "dataset": "mcd",
            "mcd_path": str(mcd_path),
            "provider": config.name,
            "model": config.model,
            "question_index": index,
            "question_id": question["id"],
            "family_id": question.get("family_id"),
            "question": question["prompt"],
            "expected_contains": question["expected_contains"],
            "answer": answer,
            "score": score,
            "error": error,
            "metadata": metadata,
            "trace": trace,
            "tool_calls": tool_calls,
            "elapsed_seconds": round(time.perf_counter() - started, 3),
        }
        rows.append(row)
        print(f"{config.name} {index}/{len(questions)} {question['id']}: {status_label(row)}", flush=True)
    return rows


def provider_summary(rows: list[dict[str, Any]], config: ProviderConfig) -> dict[str, Any]:
    passed_count = sum(1 for row in rows if passed(row))
    errors = sum(1 for row in rows if row.get("error"))
    scored = sum(1 for row in rows if row.get("score") is not None)
    elapsed = sum(float(row.get("elapsed_seconds") or 0.0) for row in rows)
    tokens = token_usage_from_rows(rows)
    total_tool_calls = tool_calls_from_rows(rows)
    return {
        "name": config.name,
        "model": config.model,
        "total": len(rows),
        "passed": passed_count,
        "failed": scored - passed_count,
        "scored": scored,
        "errors": errors,
        "pass_rate": passed_count / scored if scored else 0.0,
        "elapsed_seconds": round(elapsed, 3),
        "avg_elapsed_seconds": round(elapsed / len(rows), 3) if rows else 0.0,
        "token_usage": tokens,
        "tool_calls": total_tool_calls,
        "avg_tool_calls": round(total_tool_calls / len(rows), 2) if rows else 0.0,
    }


def write_run_config(
    *,
    path: Path,
    args: argparse.Namespace,
    configs: list[ProviderConfig],
    question_count: int,
    created_at: str,
) -> None:
    plain_eval.write_json(
        path,
        {
            "created_at": created_at,
            "providers": [config.__dict__ for config in configs],
            "mcd_path": str(args.mcd_path),
            "questions": str(args.questions),
            "prompt_tool_reference": "aligned compact MCD CLI tool docs",
            "question_count": question_count,
            "max_tool_steps": args.max_tool_steps,
            "mcd_cli": args.mcd_cli,
            "mcd_cli_status": mcd_cli_status(args.mcd_cli),
            "cli_timeout_seconds": args.cli_timeout_seconds,
            "python_timeout_seconds": args.python_timeout_seconds,
            "max_observation_chars": args.max_observation_chars,
            "max_output_tokens": args.max_output_tokens,
            "temperature": args.temperature,
            "timeout_seconds": args.timeout_seconds,
            "retries": args.retries,
            "openai_stateful_responses": args.openai_stateful_responses,
            "dry_run": args.dry_run,
        },
    )


def write_summary_markdown(
    *,
    path: Path,
    created_at: str,
    args: argparse.Namespace,
    provider_summaries: list[dict[str, Any]],
    rows_by_provider: dict[str, list[dict[str, Any]]],
) -> None:
    lines = [
        "# LLM MCD Evaluation",
        "",
        f"- Created at: `{created_at}`",
        f"- MCD package: `{args.mcd_path}`",
        f"- Questions: `{args.questions}`",
        f"- MCD CLI: `{args.mcd_cli}`",
        f"- MCD CLI available: `{mcd_cli_status(args.mcd_cli)['available_on_path_or_filesystem']}`",
        "- MCD tool reference: aligned compact CLI docs with Python fallback",
        f"- Max tool steps: `{args.max_tool_steps}`",
        f"- OpenAI stateful responses: `{args.openai_stateful_responses}`",
        "",
        "| Provider | Model | Passed | Failed | Scored | Total | Pass rate | Errors |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for item in provider_summaries:
        lines.append(
            f"| {item['name']} | `{item['model']}` | {item['passed']} | {item['failed']} | "
            f"{item['scored']} | {item['total']} | {item['pass_rate']:.1%} | {item['errors']} |"
        )

    lines.extend(
        [
            "",
            "| Provider | Input tokens | Output tokens | Total tokens | Total seconds | Avg seconds |",
            "| --- | ---: | ---: | ---: | ---: | ---: |",
        ]
    )
    for item in provider_summaries:
        tokens = item["token_usage"]
        lines.append(
            f"| {item['name']} | {format_tokens(tokens['input_tokens'])} | "
            f"{format_tokens(tokens['output_tokens'])} | {format_tokens(tokens['total_tokens'])} | "
            f"{format_seconds(item['elapsed_seconds'])} | {format_seconds(item['avg_elapsed_seconds'])} |"
        )

    lines.extend(
        [
            "",
            "| Provider | Total tool calls | Avg per question |",
            "| --- | ---: | ---: |",
        ]
    )
    for item in provider_summaries:
        lines.append(
            f"| {item['name']} | {item['tool_calls']} | {item['avg_tool_calls']:.2f} |"
        )

    for provider, rows in rows_by_provider.items():
        lines.extend(
            [
                "",
                f"## {provider} Answers",
                "",
                "| # | Status | Seconds | Calls | Question | Answer |",
                "| ---: | --- | ---: | ---: | --- | --- |",
            ]
        )
        for row in rows:
            question = str(row["question"]).replace("|", "\\|")
            answer = str(row.get("answer") or row.get("error") or "").replace("\n", " ").replace("|", "\\|")
            if len(answer) > 300:
                answer = answer[:297] + "..."
            lines.append(
                f"| {row['question_index']} | {status_label(row)} | "
                f"{format_seconds(float(row.get('elapsed_seconds') or 0.0))} | {row.get('tool_calls') or 0} | {question} | {answer} |"
            )

    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    plain_eval.load_dotenv()
    args = parse_args()
    configs = provider_configs(args)
    if not args.dry_run:
        plain_eval.validate_provider_env(
            [plain_eval.ProviderConfig(config.name, config.model, config.api_key_env) for config in configs]
        )

    args.mcd_path = args.mcd_path.resolve()
    args.questions = args.questions.resolve()
    if not args.mcd_path.exists():
        raise FileNotFoundError(f"MCD package not found: {args.mcd_path}")

    questions = plain_eval.read_jsonl(args.questions)
    if args.limit is not None:
        questions = questions[: args.limit]

    mcd_summary_text = build_mcd_summary(args.mcd_path)
    output_dir = make_output_dir(args.results_root)
    created_at = datetime.now().isoformat(timespec="seconds")
    write_run_config(
        path=output_dir / "run_config.json",
        args=args,
        configs=configs,
        question_count=len(questions),
        created_at=created_at,
    )

    all_rows: list[dict[str, Any]] = []
    rows_by_provider: dict[str, list[dict[str, Any]]] = {}
    provider_summaries: list[dict[str, Any]] = []
    for config in configs:
        provider_rows = run_provider(
            mcd_path=args.mcd_path,
            mcd_summary_text=mcd_summary_text,
            questions=questions,
            config=config,
            args=args,
        )
        rows_by_provider[config.name] = provider_rows
        all_rows.extend(provider_rows)
        provider_summaries.append(provider_summary(provider_rows, config))
        plain_eval.write_jsonl(output_dir / f"{config.name}_results.jsonl", provider_rows)

    plain_eval.write_jsonl(output_dir / "all_results.jsonl", all_rows)
    plain_eval.write_json(output_dir / "summary.json", {"providers": provider_summaries})
    write_summary_markdown(
        path=output_dir / "summary.md",
        created_at=created_at,
        args=args,
        provider_summaries=provider_summaries,
        rows_by_provider=rows_by_provider,
    )

    print(f"Results written to {output_dir}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:  # noqa: BLE001
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
