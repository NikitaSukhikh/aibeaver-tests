#!/usr/bin/env python3
"""Evaluate LLM answers over an MCD package using the Python mcd library."""

from __future__ import annotations

import argparse
import json
import os
import queue
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import zipfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import mcd


REPO_ROOT = Path(__file__).resolve().parents[2]
PLAIN_EVAL_DIR = REPO_ROOT / "tests" / "llm_plain_eval"
sys.path.insert(0, str(PLAIN_EVAL_DIR))

import run_plain_eval as plain_eval  # noqa: E402
from benchmark_validation import (  # noqa: E402
    score_answer_llm_judge,
    score_answer_tolerant,
    validate_benchmark_questions,
)


DEFAULT_MCD_PATH = Path("datasets/auto-manufacturer-tech-spec/auto-manufacturer-tech-spec.mcd")
DEFAULT_QUESTIONS_PATH = Path("datasets/auto-manufacturer-tech-spec/qa_pilot_questions_20.jsonl")
DEFAULT_RESULTS_ROOT = Path("results/llm_mcd")
DEFAULT_OPENAI_MODEL = "gpt-5.4"
DEFAULT_ANTHROPIC_MODEL = "claude-opus-4-5"
DEFAULT_XAI_MODEL = "grok-4.3"
DEFAULT_MAX_OUTPUT_TOKENS = 12000
DEFAULT_JUDGE_MAX_OUTPUT_TOKENS = 2000
PROVIDERS = ["openai", "anthropic", "xai"]
DEFAULT_MCD_MCP = str(Path.home() / ".cargo" / "bin" / ("mcd-mcp.exe" if os.name == "nt" else "mcd-mcp"))
MCP_PROTOCOL_VERSION = "2025-06-18"
READ_ONLY_MCP_TOOLS = {
    "mcd_validate",
    "mcd_inspect",
    "mcd_agent_context",
    "mcd_markdown",
    "mcd_query",
    "mcd_queries",
    "mcd_search",
    "mcd_table",
    "mcd_schemas",
    "mcd_chart",
    "mcd_images",
    "mcd_annotations",
    "mcd_relationships",
    "mcd_external_data",
    "mcd_provenance",
}


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
    parser.add_argument("--max-tool-steps", type=int, default=20)
    parser.add_argument("--mcd-mcp", default=os.getenv("MCD_MCP", DEFAULT_MCD_MCP))
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
        default="programmatic",
        help="Use deterministic expected_contains scoring or an LLM judge over expected_contains/reference_answer.",
    )
    parser.add_argument(
        "--judge-provider",
        choices=["same", "openai", "anthropic", "xai"],
        default=os.getenv("JUDGE_PROVIDER", "same"),
        help="Provider for --scoring-mode llm_judge. 'same' uses each answer provider.",
    )
    parser.add_argument(
        "--judge-model",
        default=os.getenv("JUDGE_MODEL"),
        help="Model for --scoring-mode llm_judge. Defaults to the selected judge provider's answer model.",
    )
    parser.add_argument("--judge-max-output-tokens", type=int, default=DEFAULT_JUDGE_MAX_OUTPUT_TOKENS)
    parser.add_argument("--judge-temperature", type=float, default=0.0)
    parser.add_argument("--judge-timeout-seconds", type=int, default=120)
    parser.add_argument("--judge-retries", type=int, default=2)
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


def judge_provider_config(args: argparse.Namespace, answer_config: ProviderConfig) -> ProviderConfig:
    if args.judge_provider == "same":
        return ProviderConfig(
            answer_config.name,
            args.judge_model or answer_config.model,
            answer_config.api_key_env,
        )

    configs = {
        "openai": ProviderConfig("openai", args.judge_model or args.openai_model, "OPENAI_API_KEY"),
        "anthropic": ProviderConfig("anthropic", args.judge_model or args.anthropic_model, "ANTHROPIC_API_KEY"),
        "xai": ProviderConfig("xai", args.judge_model or args.xai_model, "XAI_API_KEY"),
    }
    return configs[args.judge_provider]


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
        if isinstance(metadata, dict):
            token_usage = metadata.get("token_usage")
            if isinstance(token_usage, dict):
                total = add_token_usage(total, {key: int_token(value) for key, value in token_usage.items()})
        score = row.get("score")
        if isinstance(score, dict):
            judge_metadata = score.get("judge_metadata")
            if isinstance(judge_metadata, dict):
                total = add_token_usage(total, token_usage_from_metadata(judge_metadata))
    return total


def format_tokens(value: int) -> str:
    return f"{value:,}"


def format_seconds(value: float) -> str:
    return f"{value:.1f} sec"


def tool_calls_from_trace(trace: list[dict[str, Any]]) -> int:
    """Count the number of tool calls in an agent trace."""
    return sum(
        1
        for item in trace
        if item.get("action", {}).get("sql")
        or item.get("action", {}).get("mcp")
        or item.get("action", {}).get("cli")
        or item.get("action", {}).get("python")
    )


def tool_calls_from_rows(rows: list[dict[str, Any]]) -> int:
    """Sum tool calls across all rows."""
    return sum(int(row.get("tool_calls") or 0) for row in rows)


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


def table_ids_from_agent_context(context: dict[str, Any]) -> list[str]:
    table_ids: list[str] = []
    for table in context.get("tables", []):
        if isinstance(table, str):
            table_ids.append(table)
        elif isinstance(table, dict):
            table_id = table.get("id") or table.get("table_id") or table.get("table")
            if table_id:
                table_ids.append(str(table_id))
    return table_ids


def build_mcd_summary(mcd_path: Path) -> str:
    doc = mcd.open(mcd_path)
    validation = doc.validate().as_dict()
    context = doc.to_agent_context(include_tables=False)
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
    table_id_rows = query_rows_or_empty(doc, "select table_id from mcd_tables order by table_id")
    table_ids = [str(row["table_id"]) for row in table_id_rows if row.get("table_id")]
    if not table_ids:
        table_ids = list(table_paths)
    if not table_ids:
        table_ids = table_ids_from_agent_context(context)
    if not table_ids:
        table_ids = table_ids_from_agent_context(doc.to_agent_context(include_tables=True))

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
    if isinstance(action.get("mcp"), dict):
        mcp_action = action["mcp"]
        tool_name = mcp_action.get("tool") or mcp_action.get("name")
        arguments = mcp_action.get("arguments", mcp_action.get("args", {}))
        if not tool_name:
            raise ValueError("MCP action must include a tool name.")
        if not isinstance(arguments, dict):
            raise ValueError("MCP action arguments must be an object.")
        return {"mcp": {"tool": str(tool_name), "arguments": arguments}}
    if action.get("mcp_tool") or str(action.get("tool") or "").startswith("mcd_"):
        tool_name = action.get("mcp_tool") or action.get("tool")
        arguments = action.get("arguments", action.get("args", {}))
        if not isinstance(arguments, dict):
            raise ValueError("MCP action arguments must be an object.")
        return {"mcp": {"tool": str(tool_name), "arguments": arguments}}
    if "sql" in action:
        return {"mcp": {"tool": "mcd_query", "arguments": {"sql": str(action["sql"]), "format": "json"}}}
    if "query" in action:
        return {"mcp": {"tool": "mcd_query", "arguments": {"sql": str(action["query"]), "format": "json"}}}
    if "cli" in action:
        return {"cli": str(action["cli"])}
    if "python" in action:
        return {"python": str(action["python"])}
    if "code" in action:
        return {"python": str(action["code"])}
    raise ValueError("Agent response must contain an MCP action or 'answer'.")


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


def mcd_mcp_status(mcd_mcp: str) -> dict[str, Any]:
    expanded_mcp = os.path.expanduser(os.path.expandvars(mcd_mcp))
    if any(separator in expanded_mcp for separator in ("/", "\\")):
        path = Path(expanded_mcp)
        resolved = str(path.resolve()) if path.exists() else None
    else:
        resolved = shutil.which(expanded_mcp)
    return {
        "configured_executable": mcd_mcp,
        "resolved_executable": resolved,
        "available_on_path_or_filesystem": bool(resolved),
        "protocol_version": MCP_PROTOCOL_VERSION,
        "read_only_tools": sorted(READ_ONLY_MCP_TOOLS),
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


def validate_select_sql(query: str) -> str:
    stripped = query.strip()
    if not stripped:
        raise ValueError("SQL query is empty.")
    lowered = stripped.casefold()
    if not (lowered.startswith("select ") or lowered.startswith("with ")):
        raise ValueError("Only read-only SELECT queries are supported.")
    if ";" in stripped.rstrip(";"):
        raise ValueError("Only one SQL statement is supported.")
    return stripped.rstrip(";")


def mcp_stdio_reader(stream: Any, output: queue.Queue[tuple[str, str]], label: str) -> None:
    for line in stream:
        output.put((label, line.rstrip("\n")))


def mcp_wait_for_response(
    output: queue.Queue[tuple[str, str]],
    response_id: int,
    *,
    timeout_seconds: int,
) -> tuple[dict[str, Any] | None, list[str]]:
    deadline = time.perf_counter() + timeout_seconds
    stderr_lines: list[str] = []
    while time.perf_counter() < deadline:
        try:
            label, line = output.get(timeout=0.1)
        except queue.Empty:
            continue
        if label == "stderr":
            stderr_lines.append(line)
            continue
        try:
            payload = json.loads(line)
        except json.JSONDecodeError:
            stderr_lines.append(f"non-json MCP stdout: {line}")
            continue
        if payload.get("id") == response_id:
            return payload, stderr_lines
    return None, stderr_lines


def normalize_mcp_arguments(tool_name: str, arguments: dict[str, Any], mcd_path: Path) -> dict[str, Any]:
    normalized = dict(arguments)
    if tool_name in READ_ONLY_MCP_TOOLS:
        package_path = normalized.get("path")
        if not package_path or str(package_path) in {"{MCD_PATH}", "$MCD_PATH", "%MCD_PATH%", "$env:MCD_PATH"}:
            normalized["path"] = str(mcd_path)
    if tool_name == "mcd_query":
        if "query" in normalized and "sql" not in normalized:
            normalized["sql"] = normalized.pop("query")
        normalized["sql"] = validate_select_sql(str(normalized.get("sql", "")))
        normalized["format"] = "json"
    elif tool_name == "mcd_queries":
        queries = normalized.get("queries")
        if not isinstance(queries, list):
            raise ValueError("mcd_queries requires a queries array.")
        normalized["queries"] = [validate_select_sql(str(query)) for query in queries]
    return normalized


def mcp_content_text(result: dict[str, Any]) -> str:
    structured = result.get("structuredContent")
    if structured is not None:
        return json.dumps(structured, ensure_ascii=False, indent=2)
    parts = []
    for item in result.get("content", []):
        if isinstance(item, dict) and item.get("type") == "text":
            parts.append(str(item.get("text") or ""))
    return "\n".join(parts)


def run_mcp_tool(
    *,
    tool_name: str,
    arguments: dict[str, Any],
    mcd_mcp: str,
    mcd_path: Path,
    timeout_seconds: int,
    max_observation_chars: int,
) -> dict[str, Any]:
    started = time.perf_counter()
    try:
        if tool_name not in READ_ONLY_MCP_TOOLS:
            raise ValueError(f"MCP tool is not allowed in this read-only eval harness: {tool_name}")
        normalized_arguments = normalize_mcp_arguments(tool_name, arguments, mcd_path)
    except ValueError as exc:
        return {
            "tool_type": f"mcp:{tool_name}",
            "tool_name": tool_name,
            "arguments": arguments,
            "exit_code": 2,
            "timed_out": False,
            "elapsed_seconds": round(time.perf_counter() - started, 3),
            "stdout": "",
            "stderr": str(exc),
            "stdout_truncated": False,
            "stderr_truncated": False,
        }

    env = {
        **os.environ,
        "MCD_PATH": str(mcd_path),
        "MCD_MCP": mcd_mcp,
        "PYTHONIOENCODING": "utf-8",
    }
    executable = os.path.expanduser(os.path.expandvars(mcd_mcp))
    process: subprocess.Popen[str] | None = None
    stdout = ""
    stderr = ""
    timed_out = False
    exit_code: int | None = 0
    try:
        process = subprocess.Popen(
            [executable, "--transport", "stdio"],
            cwd=str(REPO_ROOT),
            env=env,
            text=True,
            encoding="utf-8",
            errors="replace",
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            bufsize=1,
        )
        if process.stdin is None or process.stdout is None or process.stderr is None:
            raise OSError("MCP process did not expose stdio pipes.")

        output: queue.Queue[tuple[str, str]] = queue.Queue()
        threading.Thread(target=mcp_stdio_reader, args=(process.stdout, output, "stdout"), daemon=True).start()
        threading.Thread(target=mcp_stdio_reader, args=(process.stderr, output, "stderr"), daemon=True).start()

        def send(payload: dict[str, Any]) -> None:
            process.stdin.write(json.dumps(payload, ensure_ascii=False) + "\n")
            process.stdin.flush()

        send(
            {
                "jsonrpc": "2.0",
                "id": 1,
                "method": "initialize",
                "params": {
                    "protocolVersion": MCP_PROTOCOL_VERSION,
                    "capabilities": {},
                    "clientInfo": {"name": "llm-mcd-eval", "version": "0.1"},
                },
            }
        )
        init_response, init_stderr = mcp_wait_for_response(output, 1, timeout_seconds=timeout_seconds)
        if init_response is None:
            timed_out = True
            stderr = "\n".join(init_stderr) or "Timed out waiting for MCP initialize response."
            exit_code = None
        elif init_response.get("error"):
            stderr = json.dumps(init_response["error"], ensure_ascii=False)
            exit_code = 1
        else:
            send({"jsonrpc": "2.0", "method": "notifications/initialized", "params": {}})
            send(
                {
                    "jsonrpc": "2.0",
                    "id": 2,
                    "method": "tools/call",
                    "params": {"name": tool_name, "arguments": normalized_arguments},
                }
            )
            call_response, call_stderr = mcp_wait_for_response(output, 2, timeout_seconds=timeout_seconds)
            stderr = "\n".join([*init_stderr, *call_stderr])
            if call_response is None:
                timed_out = True
                stderr = stderr or "Timed out waiting for MCP tool response."
                exit_code = None
            elif call_response.get("error"):
                stderr = "\n".join(
                    part for part in [stderr, json.dumps(call_response["error"], ensure_ascii=False)] if part
                )
                exit_code = 1
            else:
                result = call_response.get("result", {})
                stdout = mcp_content_text(result if isinstance(result, dict) else {})
                if isinstance(result, dict) and result.get("isError"):
                    exit_code = 1
    except subprocess.TimeoutExpired as exc:
        timed_out = True
        exit_code = None
        stdout = (exc.stdout or "") if isinstance(exc.stdout, str) else ""
        stderr = (exc.stderr or "") if isinstance(exc.stderr, str) else ""
    except OSError as exc:
        exit_code = 127
        stderr = str(exc)
    finally:
        if process is not None and process.poll() is None:
            process.terminate()
            try:
                process.wait(timeout=2)
            except subprocess.TimeoutExpired:
                process.kill()

    return {
        "tool_type": f"mcp:{tool_name}",
        "tool_name": tool_name,
        "arguments": normalized_arguments,
        "exit_code": exit_code,
        "timed_out": timed_out,
        "elapsed_seconds": round(time.perf_counter() - started, 3),
        "stdout": stdout[:max_observation_chars],
        "stderr": stderr[:max_observation_chars],
        "stdout_truncated": len(stdout) > max_observation_chars,
        "stderr_truncated": len(stderr) > max_observation_chars,
    }


def run_sql_tool(
    *,
    query: str,
    mcd_cli: str,
    mcd_path: Path,
    timeout_seconds: int,
    max_observation_chars: int,
) -> dict[str, Any]:
    started = time.perf_counter()
    try:
        safe_query = validate_select_sql(query)
    except ValueError as exc:
        return {
            "tool_type": "sql",
            "query": query,
            "exit_code": 2,
            "timed_out": False,
            "elapsed_seconds": round(time.perf_counter() - started, 3),
            "stdout": "",
            "stderr": str(exc),
            "stdout_truncated": False,
            "stderr_truncated": False,
        }

    command = [mcd_cli, "query", "--format", "json", str(mcd_path), safe_query]
    env = {
        **os.environ,
        "MCD_PATH": str(mcd_path),
        "MCD_CLI": mcd_cli,
        "PYTHONIOENCODING": "utf-8",
    }
    try:
        completed = subprocess.run(
            command,
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
    except OSError as exc:
        timed_out = False
        exit_code = 127
        stdout = ""
        stderr = str(exc)

    return {
        "tool_type": "sql",
        "query": safe_query,
        "command": command,
        "exit_code": exit_code,
        "timed_out": timed_out,
        "elapsed_seconds": round(time.perf_counter() - started, 3),
        "stdout": stdout[:max_observation_chars],
        "stderr": stderr[:max_observation_chars],
        "stdout_truncated": len(stdout) > max_observation_chars,
        "stderr_truncated": len(stderr) > max_observation_chars,
    }


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
    mcp_status: dict[str, Any],
    question: dict[str, Any],
    observations: list[dict[str, Any]],
) -> str:
    tool_docs = {
        "sql_query": {
            "sql": (
                "select group_column, count(*) as row_count "
                "from table_id "
                "group by group_column order by row_count desc limit 3"
            )
        },
        "sql_join": {
            "sql": (
                "select a.id, a.foreign_id, a.metric_value, b.category, b.status "
                "from table_a a "
                "join table_b b on a.foreign_id = b.id "
                "order by cast(a.metric_value as real) asc limit 1"
            )
        },
        "sql_schema_metadata": {
            "sql": (
                "select table_id, column_name, type, label, nullable, unit_code, unit_label "
                "from mcd_columns "
                "order by table_id, ordinal"
            )
        },
        "sql_primary_keys": {
            "sql": (
                "select table_id, column_name, ordinal "
                "from mcd_primary_keys "
                "order by table_id, ordinal"
            )
        },
        "sql_foreign_keys": {
            "sql": (
                "select table_id, column_name, ordinal, ref_table_id, ref_column_name "
                "from mcd_foreign_keys "
                "order by table_id, ordinal"
            )
        },
        "sql_units": {
            "sql": (
                "select table_id, column_name, unit_code, unit_label, unit_custom "
                "from mcd_units "
                "order by table_id, column_name"
            )
        },
        "sql_pragma_foreign_keys": {
            "sql": "select [table], [from], [to] from pragma_foreign_key_list('table_id')"
        },
        "sql_pragma_table_keys": {
            "sql": "select name, type, pk from pragma_table_info('table_id') where pk > 0"
        },
        "mcp_markdown": {"mcp_tool": "mcd_markdown", "arguments": {"expandTables": False}},
        "mcp_schemas": {"mcp_tool": "mcd_schemas", "arguments": {}},
        "mcp_table_sample": {"mcp_tool": "mcd_table", "arguments": {"tableId": "table_id", "maxRows": 5}},
        "mcp_search": {"mcp_tool": "mcd_search", "arguments": {"query": "rule terms", "kind": "markdown", "limit": 5}},
        "prefix_rule_example": {
            "sql": (
                "select count(*) as violation_count "
                "from table_id "
                "where lower(substr(prefixed_code_column, 1, instr(prefixed_code_column, '-') - 1)) "
                "<> lower(expected_prefix_column)"
            )
        },
        "prefix_rule_count_plus_first_example": {
            "sql": (
                "with mismatches as ("
                "select id_column, expected_prefix_column, prefixed_code_column, "
                "substr(prefixed_code_column, 1, instr(prefixed_code_column, '-') - 1) as actual_prefix "
                "from table_id "
                "where lower(substr(prefixed_code_column, 1, instr(prefixed_code_column, '-') - 1)) "
                "<> lower(expected_prefix_column)"
                ") "
                "select (select count(*) from mismatches) as violation_count, * "
                "from mismatches order by id_column asc limit 1"
            )
        },
        "fixed_precision_example": {
            "sql": (
                "select id, printf('%.3f', decimal_metric_column) as decimal_metric_column "
                "from table_id "
                "order by cast(decimal_metric_column as real) desc limit 2"
            )
        },
        "boolean_predicate_example": {
            "sql": (
                "select id_column, boolean_flag "
                "from table_id "
                "where lower(cast(boolean_flag as text)) in ('false', '0')"
            )
        },
        "production_quality_gate_example": {
            "sql": (
                "with gate_rows as ("
                "select lot_id, release_status, ppap_status, containment_status, supplier_lot_traceability, "
                "cpk_min, ppk_min, msa_grr_pct, battery_health_score_pct "
                "from production_quality_measurements "
                "where lower(ppap_status)=lower('approved') and lower(release_status)<>lower('released')"
                "), battery_only as ("
                "select * from gate_rows "
                "where lower(containment_status)=lower('closed') "
                "and lower(supplier_lot_traceability)=lower('complete') "
                "and cast(cpk_min as real)>=1.33 and cast(ppk_min as real)>=1.20 "
                "and cast(msa_grr_pct as real)<=10 "
                "and cast(battery_health_score_pct as real)<96.5"
                ") "
                "select (select count(*) from battery_only) as battery_only_count, * "
                "from battery_only order by lot_id asc limit 1"
            )
        },
        "count_plus_first_row_example": {
            "sql": (
                "with matches as ("
                "select a.id, a.foreign_id, a.status, b.category, b.metric_value "
                "from table_a a "
                "join table_b b on a.foreign_id = b.id "
                "where lower(b.category)=lower('target_category') and cast(b.metric_value as real)>threshold "
                "and lower(a.status)<>lower('required_status')"
                ") "
                "select (select count(*) from matches) as violation_count, * "
                "from matches order by id asc limit 1"
            )
        },
        "top_row_all_columns_example": {
            "sql": (
                "select * from source_table "
                "where lower(category_column)=lower('target_category') "
                "order by cast(sort_metric_column as real) desc, id asc limit 1"
            )
        },
        "grouped_counts_with_total_example": {
            "sql": (
                "select count(*) as total_count, "
                "sum(case when lower(category_column)=lower('category_a') then 1 else 0 end) as category_a_count, "
                "sum(case when lower(category_column)=lower('category_b') then 1 else 0 end) as category_b_count "
                "from table_id "
                "where lower(category_column) in (lower('category_a'), lower('category_b')) "
                "and cast(metric_column as real)>threshold"
            )
        },
        "grouped_rows_with_total_example": {
            "sql": (
                "with grouped as ("
                "select category_column, count(*) as category_count "
                "from table_id "
                "where lower(category_column) in (lower('category_a'), lower('category_b')) "
                "and cast(metric_column as real)>threshold "
                "group by category_column"
                ") "
                "select (select sum(category_count) from grouped) as total_count, "
                "category_column, category_count "
                "from grouped order by category_column"
            )
        },
    }
    for example in tool_docs.values():
        if "sql" in example:
            example["mcp_tool"] = "mcd_query"
            example["arguments"] = {"sql": example.pop("sql")}
    return (
        "You are a document-grounded QA assistant evaluating an MCD package. "
        "Use the MCD MCP server to inspect the package and query tables. Do not guess from memory. "
        "Prefer the `mcd_query` MCP tool for table and metadata queries. The harness injects the package path, "
        "so omit `path` or set it to `{MCD_PATH}`; do not use `.`, `$MCD_PATH`, or `%MCD_PATH%`. "
        "Return MCP calls as `{\"mcp_tool\":\"mcd_query\",\"arguments\":{\"sql\":\"select ...\"}}`. "
        "Use `mcd_markdown`, `mcd_schemas`, `mcd_table`, and `mcd_search` for non-query MCD inspection. "
        "`mcd_search` is BM25 retrieval over package Markdown, schemas, manifest metadata, annotations, and "
        "provenance; it does not search CSV table rows, so use `mcd_query` for exact row-level counts, joins, "
        "filters, and extrema. Use `kind` filters such as `markdown`, `schema`, `manifest`, `annotation`, or "
        "`provenance` when the needed evidence type is clear. "
        "Prefer SQL for complex relational work, such as joins, aggregate counts, computed expressions, "
        "grouped counts, sorting, and top-k queries. `mcd_query` accepts read-only SELECT statements over "
        "manifest table IDs. The MCD SQL runtime is SQLite-backed and also exposes reserved metadata tables: "
        "`mcd_tables`, `mcd_columns`, `mcd_primary_keys`, `mcd_foreign_keys`, and `mcd_units`. Use these tables "
        "through `mcd_query` to discover exact table IDs, column names, data types, semantic units, primary keys, "
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
        "For boolean columns, values may surface as true/false text in CSV-backed views or as 1/0 in SQLite-backed "
        "MCD queries. Use robust predicates such as lower(cast(flag_column as text)) in ('true', '1') for true and "
        "lower(cast(flag_column as text)) in ('false', '0') for false; do not compare booleans only to the text "
        "'true' or 'false'. "
        "For text inequality, use lower(left) <> lower(right) or lower(left) != lower(right); reserve IS and IS NOT "
        "for NULL checks only. "
        "For prefix rules, compute the prefix from the field, for example "
        "substr(prefixed_code_column, 1, instr(prefixed_code_column, '-') - 1), and compare it to the expected "
        "prefix column; "
        "do not hardcode a list of allowed prefixes. "
        "For expected fixed-precision decimals, use printf formatting in SQL, such as printf('%.3f', decimal_metric_column). "
        "Use `mcd_search` before broad Markdown reads when the question names a rule, formula, domain phrase, "
        "source line, schema term, annotation, or provenance detail but the relevant section is uncertain. Use "
        "`mcd_markdown` when you already need nearby prose from a known page or section. Use "
        "`mcd_schemas` or metadata queries when the question depends on declared schema information, primary keys, foreign keys, "
        "units, or nullable/enum/type metadata. For narrative-rule "
        "questions, inspect the relevant markdown sentence or use table schemas, then include source columns whose "
        "names overlap with or are semantically tied to the rule terms. "
        "For unit-sensitive engineering formulas, retrieve `content/engineering_math.md` or the relevant formula "
        "prose, then encode unit conversions explicitly in SQL. For brake energy at 100 km/h, use "
        "`0.5 * mass_kg * (100.0 / 3.6) * (100.0 / 3.6) / 1000000.0` MJ; never treat 100 km/h as 100 m/s. "
        "When the question states explicit thresholds, formulas, or gate criteria, those question-stated values take "
        "precedence over narrative examples; copy the exact thresholds into the SQL predicate and final answer. For "
        "production-quality release gates in this dataset, unless the question states different gates, treat the gate "
        "set as ppap_status=approved, containment_status=closed, supplier_lot_traceability=complete, cpk_min>=1.33, "
        "ppk_min>=1.20, msa_grr_pct<=10, and battery_health_score_pct>=96.5. Do not add unrelated quality fields "
        "such as warranty_risk_index, end_of_line_pass_rate_pct, torque_rework_ppm, paint_defect_ppm, or "
        "water_leak_failures unless the question explicitly names them. "
        "Do not use CLI or Python actions; MCP observations are the "
        "primary source of truth. "
        "Do not guess from memory. MCP tools execute in the repository root and return stdout/stderr-style observations. "
        "Keep tool output concise. "
        "Return one tool action at a time. Do not submit "
        "semicolon-separated multiple SQL statements; `mcd_query` SQL must contain exactly one read-only SELECT or WITH "
        "statement. Use CTEs or scalar subqueries to combine multiple counts, examples, and grouped rows into one "
        "result. "
        "If a tool observation has nonzero exit_code, stderr, or timed_out=true, treat it as failed: do not answer "
        "from that observation. Retry once with a single SQL statement through `mcd_query`; after repeated MCP "
        "errors, try `mcd_schemas`, `mcd_table`, or `mcd_search` to inspect the package. "
        "If a result is capped or limited, do not compute final counts or extremes from capped samples unless "
        "the query sorted exactly by the required criterion. "
        "Before writing a query, form an answer contract from the question: every requested output field, every "
        "source field used in a derived expression, and every source field used in a rule/filter must be selected "
        "or otherwise returned in the same successful observation. If a question names a formula or expression "
        "such as X plus Y, select X, Y, and the computed value; do not return only the computed value. "
        "For each question, select and return all fields requested by the prompt, including example row details "
        "such as IDs, variants, category values, and numeric values, not only counts. "
        "For joined-row questions, include the stable row identifier from the row-producing/source table as well "
        "as any referenced entity ID from joined tables. If the question asks for a validation row, test, lot, "
        "calibration, pack, or variant row, include that table's primary or prefixed ID in the query result. "
        "When a question asks for a count plus a first/worst/best/top row, use a CTE or subqueries so the same "
        "successful observation includes both the total count and every field for that row. Do not use aggregate "
        "functions and ungrouped row fields together unless each row field is selected by an ordered subquery. "
        "When a question is phrased as `among ... which row/pack/lot/test has the highest/lowest/worst/best`, include "
        "the candidate-set count plus the selected row's stable ID, filter/category values, sort metric, and nearby "
        "domain context columns that describe the selected row. For battery-pack top rows, include pack_id, chemistry, "
        "peak_discharge_kw, capacity_kwh, and usable_capacity_kwh when those columns exist. "
        "When a question asks for the first listed row and gives no explicit sorting metric, preserve the listing "
        "order of the row-producing table. If the source order is represented by a monotonic prefixed ID, order by "
        "that source-row ID; do not order by a joined lookup/entity ID unless the question asks for that entity's "
        "first row. "
        "When a question asks for grouped counts, include the overall total count in both the SQL result and final "
        "answer as well as each group count. A question phrased as `how many ... by category/chemistry/status` "
        "requires both the total number of matching rows across all groups and the per-group counts; do not answer "
        "with only the breakdown. If the SQL groups rows, add a total column with a CTE, scalar subquery, or window "
        "aggregate so the same observation contains the total and the grouped rows. "
        "When a question asks for first examples by named category or status, filter the named source category/status "
        "column directly after discovering its exact values; do not look for those labels in unrelated columns. "
        "For production-quality wording, containment, hold, released, and non-released are release_status concepts; "
        "containment_status is the open/closed gate field. If a question asks for a containment example, include "
        "release_status, containment_status, ppap_status, and supplier_lot_traceability in the observation and final "
        "answer. "
        "When a question asks for a top source row, include the identifier plus every rule-related source field "
        "named or implied by the question and narrative, not only the sort metric. If the rule references another "
        "measurement, limit, threshold, date, status, or requirement column in the same source table, include that "
        "column in the query and final answer even when it is not the ordering column. For narrative-rule questions, "
        "prefer selecting all columns for the selected/top source row (`select * ... limit 1`) or first inspect the "
        "schema with `mcd_schemas` before deciding which columns to project; then summarize "
        "only the relevant fields in the final answer. "
        "In the final answer, include the key condition values and field names used to select the result, not only "
        "the numeric answer. "
        "Return exactly one JSON object and no prose. Do not return a tool call and an answer in the same response. "
        "All JSON string values must be valid single-line JSON strings: no literal line breaks inside strings. "
        "If a string needs a quote or newline, escape it as JSON, or keep the SQL/action text on one line.\n\n"
        "If you need data, return an MCP tool call, for example:\n"
        '{"mcp_tool":"mcd_query","arguments":{"sql":"select ..."}}\n'
        "For non-query MCD inspection, return:\n"
        '{"mcp_tool":"mcd_markdown","arguments":{"expandTables":false}}\n'
        "For BM25 retrieval over package text and metadata, return:\n"
        '{"mcp_tool":"mcd_search","arguments":{"query":"rule or schema terms","kind":"markdown","limit":5}}\n'
        "When you know the final answer, return:\n"
        '{"answer":"concise answer containing exact IDs, field names, condition values, and numbers"}\n\n'
        "Available tools and argument examples:\n"
        "The examples below are patterns. Replace placeholder table names, column names, threshold, and category "
        "values with actual names and values from the dataset index, question, and tool observations.\n"
        f"{json.dumps(tool_docs, ensure_ascii=False, indent=2)}\n\n"
        "MCP status:\n"
        f"{json.dumps({'available': mcp_status.get('available_on_path_or_filesystem'), 'mcd_mcp': mcp_status.get('configured_executable'), 'read_only_tools': mcp_status.get('read_only_tools')}, ensure_ascii=False, indent=2)}\n\n"
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
        "Return exactly one JSON object and no prose: either another MCP action or the final "
        "`answer`. Prefer `mcd_query` for MCD queries. JSON string values must be single-line valid JSON strings with no "
        "literal line breaks. Do not repeat a successful tool call unless a different query is needed."
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


def parsed_mcd_stdout(observation: dict[str, Any]) -> dict[str, Any] | None:
    stdout = str(observation.get("stdout") or "").strip()
    if not stdout:
        return None
    try:
        payload = json.loads(stdout)
    except json.JSONDecodeError:
        return None
    if isinstance(payload, dict):
        return payload
    return None


def summarize_mcd_observation(step: Any, action: dict[str, Any], observation: dict[str, Any]) -> dict[str, Any]:
    summary: dict[str, Any] = {
        "step": step,
        "action": action,
        "tool_type": observation.get("tool_type"),
        "exit_code": observation.get("exit_code"),
        "timed_out": observation.get("timed_out"),
        "stderr": observation.get("stderr"),
        "stdout_truncated": observation.get("stdout_truncated"),
    }
    payload = parsed_mcd_stdout(observation)
    if payload:
        rows = payload.get("rows")
        if isinstance(rows, list):
            summary.update(
                {
                    "columns": payload.get("columns"),
                    "row_count": payload.get("rowCount"),
                    "rows": rows[:5],
                }
            )
        else:
            summary["stdout_json"] = payload
    else:
        stdout = str(observation.get("stdout") or "")
        if stdout:
            summary["stdout_preview"] = stdout[:2000]
    return summary


def build_mcd_agent_state(trace: list[dict[str, Any]]) -> dict[str, Any]:
    steps: list[dict[str, Any]] = []
    successful_result_summaries: list[dict[str, Any]] = []
    failed_attempts: list[dict[str, Any]] = []
    ignored_response_objects: list[dict[str, Any]] = []
    provisional_answers: list[dict[str, Any]] = []
    observed_columns_by_query: list[dict[str, Any]] = []

    for item in trace:
        action = item.get("action", {})
        raw = str(item.get("raw") or "")
        response_objects = extract_json_objects(raw)
        if len(response_objects) > 1:
            ignored_response_objects.extend(
                {"step": item.get("step"), "object": value}
                for value in response_objects[1:]
            )
        for value in response_objects:
            if "answer" in value:
                provisional_answers.append(
                    {"step": item.get("step"), "answer": str(value.get("answer"))}
                )

        step_record: dict[str, Any] = {
            "step": item.get("step"),
            "model_response": raw,
            "parsed_action": action,
        }
        if "error" in item:
            step_record["parse_error"] = item["error"]
        observation = item.get("observation")
        if isinstance(observation, dict):
            observation_summary = summarize_mcd_observation(item.get("step"), action, observation)
            step_record["tool_observation_summary"] = observation_summary
            if tool_observation_failed(observation):
                failed_attempts.append(
                    {
                        "step": item.get("step"),
                        "action": action,
                        "error": observation.get("stderr") or observation.get("harness_hint") or "tool failed",
                    }
                )
            else:
                successful_result_summaries.append(observation_summary)
                if observation_summary.get("columns"):
                    observed_columns_by_query.append(
                        {
                            "step": item.get("step"),
                            "action": action,
                            "columns": observation_summary.get("columns"),
                            "row_count": observation_summary.get("row_count"),
                        }
                    )
        steps.append(step_record)

    return {
        "steps": steps,
        "successful_result_summaries": successful_result_summaries,
        "observed_columns_by_query": observed_columns_by_query,
        "failed_attempts": failed_attempts,
        "ignored_response_objects": ignored_response_objects,
        "provisional_answers": provisional_answers,
    }


def compact_mcd_tool_registry() -> dict[str, Any]:
    return {
        "response_shape": (
            'Return exactly one JSON object: {"mcp_tool":"mcd_query","arguments":{"sql":"single SELECT or WITH statement"}}, '
            '{"mcp_tool":"mcd_search","arguments":{"query":"...","kind":"markdown","limit":5}}, '
            '{"mcp_tool":"mcd_markdown","arguments":{"expandTables":false}}, or {"answer":"..."}. '
            "Do not emit multiple JSON objects. Keep JSON string values single-line and valid."
        ),
        "tools": {
            "mcd_query": {
                "notes": (
                    "Preferred for MCD table and metadata queries. The harness executes the call through "
                    "the MCD MCP server; do not include a CLI command, shell quotes, "
                    "semicolons, or multiple statements. Query manifest table IDs plus mcd_tables, mcd_columns, "
                    "mcd_primary_keys, mcd_foreign_keys, and mcd_units."
                ),
            },
            "mcd_markdown": {"notes": "Use for narrative rules and package markdown."},
            "mcd_schemas": {"notes": "Use for table schemas, keys, relationships, and units."},
            "mcd_table": {"notes": "Use for small table samples when schema or exact values are uncertain."},
            "mcd_search": {
                "notes": (
                    "Use for BM25 search over Markdown, schemas, manifest, annotations, and provenance. "
                    "It does not search CSV table rows; use mcd_query for exact row-level answers."
                ),
            },
        },
    }


def make_mcd_agent_compact_prompt(
    question: dict[str, Any],
    trace: list[dict[str, Any]],
    mcd_summary_text: str,
) -> str:
    observation_record = {"observation": trace[-1].get("observation", {})} if trace else {}
    has_rows = observation_has_json_rows(observation_record)
    dataset_index = "" if has_rows else f"\n\nCompact dataset index:\n{mcd_summary_text}"
    agent_state = build_mcd_agent_state(trace)
    return (
        "You are continuing an MCD package QA task. Use the current state below as persistent working memory for "
        "the same question. The state includes prior model responses, executed actions, tool observations, "
        "successful result summaries, failed attempts, ignored extra response objects, and provisional answer text.\n\n"
        "Rules: return exactly one JSON object and no prose. Use "
        '{"answer":"..."} for the final answer or '
        '{"mcp_tool":"mcd_query","arguments":{"sql":"select ..."}} for MCD queries. Use '
        '{"mcp_tool":"mcd_markdown","arguments":{"expandTables":false}}, '
        '{"mcp_tool":"mcd_schemas","arguments":{}}, {"mcp_tool":"mcd_table","arguments":{"tableId":"...","maxRows":5}}, '
        'or {"mcp_tool":"mcd_search","arguments":{"query":"...","limit":5}} for non-query MCD inspection. '
        "Only the first JSON object is executed, so never include a tool call and an "
        "answer in the same response. JSON string values must be single-line valid JSON strings with no literal "
        "line breaks. Prefer `mcd_query` for joins, aggregate counts, computed expressions, grouped counts, sorting, "
        "and top-k queries. Use read-only SQLite SELECT over manifest table IDs and MCD metadata tables. Submit "
        "exactly one SELECT or WITH statement; use CTEs or scalar subqueries instead of semicolon-separated "
        "statements. Use `mcd_search` for BM25 retrieval when the relevant rule, formula, schema term, annotation, "
        "or provenance detail is uncertain; do not use search results as a substitute for SQL row-level counts or "
        "extrema. Use `kind` filters such as `markdown`, `schema`, `manifest`, `annotation`, or `provenance` when useful. "
        "Use CAST(... AS REAL/INTEGER) for numeric filtering, sorting, and calculations. Use lower(...) "
        "for categorical comparisons unless exact case is required. For boolean columns, use "
        "lower(cast(flag_column as text)) in ('true', '1') for true and "
        "lower(cast(flag_column as text)) in ('false', '0') for false because SQLite-backed MCD queries may expose "
        "booleans as 1/0. Use <> or != for text inequality; reserve "
        "IS/IS NOT for NULL checks. For counts plus first/worst/best rows, use CTEs or ordered subqueries so the "
        "same successful observation contains the count and row details. "
        "Tool observations are source of truth; provisional answer text and ignored response objects are clues only "
        "and must be checked against observations. Carry forward every observed table name, column name, row value, "
        "count, and failure. Use only exact column names already observed for a table, or inspect metadata before "
        "using uncertain columns. Before writing a query, form an answer contract from the question: requested "
        "output fields, source fields used in derived expressions, and source fields used in rules/filters must all "
        "be present in the same successful observation. If a question names a formula or expression such as X plus "
        "Y, select X, Y, and the computed value; do not return only the computed value. For joined-row questions, "
        "include the stable row identifier from the row-producing/source table as well as referenced joined entity "
        "IDs. When a question states explicit thresholds, formulas, or gate criteria, use those exact values rather "
        "than substituting narrative examples. For unit-sensitive formulas, retrieve `content/engineering_math.md` "
        "or encode the documented conversion directly in SQL. For 100 km/h brake energy, use 100.0/3.6 m/s; never "
        "use 100 as m/s. For production-quality release gates in this dataset, unless the "
        "question states different gates, use ppap_status=approved, containment_status=closed, "
        "supplier_lot_traceability=complete, cpk_min>=1.33, ppk_min>=1.20, msa_grr_pct<=10, and "
        "battery_health_score_pct>=96.5; do not add unrelated quality metrics. If a question asks for a containment "
        "example, treat containment as release_status='containment' and also include containment_status, ppap_status, "
        "and supplier_lot_traceability. When a question is phrased as `among ... which row/pack/lot/test has the "
        "highest/lowest/worst/best`, include the candidate-set count plus the selected row's stable ID, "
        "filter/category values, sort metric, and nearby domain context columns. For battery-pack top rows, include "
        "pack_id, chemistry, peak_discharge_kw, capacity_kwh, and usable_capacity_kwh when observed. If a question "
        "asks for the first listed row and gives no explicit sorting metric, preserve the listing "
        "order of the row-producing table; if represented by a monotonic prefixed ID, order by that source-row ID, "
        "not a joined lookup/entity ID. If a prior action failed, do not retry the same invalid table name, column "
        "name, argument shape, JSON shape, or SQL pattern. If the current state already contains all fields "
        "requested by the question, answer now rather than calling another tool; otherwise call one more tool to "
        "retrieve missing answer-contract fields instead of omitting them. For grouped counts, include any overall "
        "total present in the observation; if grouped rows are exhaustive and untruncated, include the sum of group "
        "counts as an overall total. A question phrased as `how many ... by category/chemistry/status` requires both "
        "the total number of matching rows across all groups and the per-group counts; do not answer with only the "
        "breakdown. If the current grouped observation lacks an explicit total but is exhaustive and untruncated, "
        "sum the returned group counts in the final answer or call one more SQL query that adds the total. For "
        "prefix-style rules, derive the prefix from the data value and compare it "
        "directly to the expected field; do not enumerate possible categories. If two independent "
        "earliest/top/count facts are requested and no observed schema provides a join key, compute them "
        "independently rather than inventing a relationship. Final answers must include exact IDs, requested "
        "fields, key condition values, source fields used to compute derived values, and "
        "rule-related source fields present in observations.\n\n"
        "Tool registry:\n"
        f"{json.dumps(compact_mcd_tool_registry(), ensure_ascii=False, indent=2)}\n\n"
        "Question:\n"
        f"{json.dumps({'id': question['id'], 'question': question['prompt']}, ensure_ascii=False, indent=2)}\n\n"
        "Current state:\n"
        f"{json.dumps(agent_state, ensure_ascii=False, indent=2)}"
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
                "mcp_status": mcd_mcp_status(args.mcd_mcp),
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
    mcp_status = mcd_mcp_status(args.mcd_mcp)
    failed_cli_count = 0
    failed_mcp_count = 0
    use_stateful_openai = openai_stateful_enabled(provider, args)
    previous_response_id: str | None = None

    for step in range(1, args.max_tool_steps + 1):
        if step == 1:
            prompt = make_mcd_agent_prompt(
                mcd_summary_text=mcd_summary_text,
                mcp_status=mcp_status,
                question=question,
                observations=[],
            )
        elif use_stateful_openai:
            prompt = make_mcd_agent_followup_prompt(observations[-1])
        else:
            prompt = make_mcd_agent_compact_prompt(question, trace, mcd_summary_text)

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
            "mcp_status": mcp_status,
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

        if "mcp" in action:
            mcp_action = action["mcp"]
            observation = run_mcp_tool(
                tool_name=mcp_action["tool"],
                arguments=mcp_action["arguments"],
                mcd_mcp=args.mcd_mcp,
                mcd_path=mcd_path,
                timeout_seconds=args.mcp_timeout_seconds,
                max_observation_chars=args.max_observation_chars,
            )
            if tool_observation_failed(observation):
                failed_mcp_count += 1
                observation["harness_hint"] = (
                    "This MCP tool call failed. Do not answer from failed output. For mcd_query, submit exactly "
                    "one read-only SELECT or WITH statement over manifest table IDs or MCD metadata tables. Do "
                    "not include CLI commands, package paths, shell quotes, semicolon-separated statements, or "
                    f"CSV paths. Consecutive MCP failures: {failed_mcp_count}. After repeated query failures, "
                    "inspect with mcd_schemas, mcd_table, mcd_markdown, or mcd_search."
                )
            else:
                failed_mcp_count = 0
            observation_record = {
                "step": step,
                "tool_type": observation.get("tool_type"),
                "mcp": mcp_action,
                "observation": observation,
            }
        elif "sql" in action:
            observation = run_sql_tool(
                query=action["sql"],
                mcd_cli=args.mcd_cli,
                mcd_path=mcd_path,
                timeout_seconds=args.cli_timeout_seconds,
                max_observation_chars=args.max_observation_chars,
            )
            if tool_observation_failed(observation):
                failed_cli_count += 1
                observation["harness_hint"] = (
                    "This legacy SQL query failed. Do not answer from failed output. Prefer an MCP mcd_query "
                    "action for the retry."
                )
            else:
                failed_cli_count = 0
            observation_record = {"step": step, "tool_type": "sql", "sql": action["sql"], "observation": observation}
        elif "cli" in action:
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
            "reference_answer": question.get("reference_answer"),
            "answer": answer,
            "score": None,
            "error": error,
            "metadata": metadata,
            "trace": trace,
            "tool_calls": tool_calls,
            "elapsed_seconds": round(time.perf_counter() - started, 3),
        }
        row["score"] = score_or_none(answer, question, error, args.dry_run, args, config)
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
            "tokenizer": {"summary": plain_eval.TOKENIZER_SUMMARY, **plain_eval.TOKENIZER_INFO},
            "prompt_tool_reference": "MCD MCP tool docs with persistent state",
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
            "mcd_mcp_status": mcd_mcp_status(args.mcd_mcp),
            "mcp_timeout_seconds": args.mcp_timeout_seconds,
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
        f"- Token accounting: `{plain_eval.TOKENIZER_SUMMARY}`",
        f"- MCD MCP: `{args.mcd_mcp}`",
        f"- MCD MCP available: `{mcd_mcp_status(args.mcd_mcp)['available_on_path_or_filesystem']}`",
        f"- MCD CLI: `{args.mcd_cli}`",
        f"- MCD CLI available: `{mcd_cli_status(args.mcd_cli)['available_on_path_or_filesystem']}`",
        "- MCD tool reference: MCP-first read-only MCD tools with persistent state",
        f"- Scoring mode: `{args.scoring_mode}`",
        f"- Judge provider: `{args.judge_provider if args.scoring_mode == 'llm_judge' else 'n/a'}`",
        f"- Judge model override: `{args.judge_model or 'n/a'}`",
        f"- Token usage includes judge calls: `{args.scoring_mode == 'llm_judge'}`",
        "- Timing rows exclude judge latency; judge latency is stored in `score.judge_elapsed_seconds`.",
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
        env_configs = [
            plain_eval.ProviderConfig(config.name, config.model, config.api_key_env)
            for config in configs
        ]
        if args.scoring_mode == "llm_judge":
            env_configs.extend(
                plain_eval.ProviderConfig(
                    judge_config.name,
                    judge_config.model,
                    judge_config.api_key_env,
                )
                for judge_config in (judge_provider_config(args, config) for config in configs)
            )
        plain_eval.validate_provider_env(
            list({
                (item.name, item.model, item.api_key_env): item
                for item in env_configs
            }.values())
        )

    args.mcd_path = args.mcd_path.resolve()
    args.questions = args.questions.resolve()
    if not args.mcd_path.exists():
        raise FileNotFoundError(f"MCD package not found: {args.mcd_path}")

    questions = plain_eval.read_jsonl(args.questions)
    validate_benchmark_questions(questions, args.questions)
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
        provider_rows = rows_by_provider[config.name]
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
