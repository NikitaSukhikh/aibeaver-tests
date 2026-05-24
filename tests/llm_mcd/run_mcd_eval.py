#!/usr/bin/env python3
"""Evaluate LLM answers over an MCD package using the Python mcd library."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from datetime import datetime
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

MCD_TOOL_REFERENCE = """Available MCD Python library tools:

Top-level:
- import mcd
- mcd.open(path) -> Document
- mcd.query(path, sql) -> QueryResult, if available in the installed package
- mcd.convert_pdf(input, output, title=None) -> Document, not needed for this eval
- mcd.pdf_to_mcd_bytes(pdf, title=None, source_filename=None) -> bytes, not needed for this eval

Document:
- doc.path
- doc.validate().as_dict()
- doc.blocks(); each block supports block.as_dict()
- doc.markdown(expand_tables=False)
- doc.to_agent_context(include_tables=True, include_layout=False)
- doc.table(table_id) -> Table
- doc.chart(chart_id) -> Chart, if the package has charts
- doc.image(image_id) -> Image, if the package has images
- doc.annotations()
- doc.annotation(annotation_id)
- doc.query(sql) -> QueryResult, if available in the installed package

Table:
- table.id
- table.source
- table.schema
- table.schema.id
- table.schema.columns
- table.schema.as_dict()
- table.rows()
- table.typed_rows()
- table.as_dict()
- table.dataframe(), only if optional pandas support is installed

QueryResult, if query support is available:
- result.columns
- result.rows
- result.row_count
- len(result)
- result.as_dict()
- result.to_json()
- result.to_csv()
- result.to_table()

Chart and view, if present:
- chart.table_id
- chart.view_id
- chart.placement_ref
- chart.view
- chart.rows()
- chart.layout()
- chart.as_dict()
- chart.to_markdown_table()
- view.id
- view.table_id
- view.display
- view.columns
- view.layout()
- view.as_dict()

Image and annotation, if present:
- image.id
- image.asset_path
- image.role
- image.alt
- image.caption
- image.intrinsic_size
- image.as_dict()
- annotation.id
- annotation.kind
- annotation.status
- annotation.body
- annotation.labels
- annotation.target()
- annotation.proposed_change()
- annotation.as_dict()

Recommended use for this eval:
- Open the package once with doc = mcd.open(os.environ["MCD_PATH"]).
- Validate with doc.validate().as_dict().
- Discover table IDs and schemas with doc.to_agent_context(include_tables=False) and doc.table(id).schema.columns.
- For numeric/table questions, use doc.query(...) or mcd.query(...) only if those methods exist.
- If query helpers are unavailable, use doc.table(id).rows() and ordinary Python joins, filters, grouping, sorting, and arithmetic.
- Return final answers with exact IDs, field names, condition values, and numeric values used.
"""

CLI_TOOL_REFERENCE = """Available MCD CLI usage:

- Prefer the CLI when it is available and can express the operation.
- Use {MCD_CLI} as a placeholder for the configured MCD CLI executable.
- Use {MCD_PATH} as a placeholder for the current package path.
- Start with help/inspection commands if you do not know the CLI syntax, for example:
  {"cli":"{MCD_CLI} --help"}
  {"cli":"{MCD_CLI} validate {MCD_PATH}"}
  {"cli":"{MCD_CLI} context {MCD_PATH}"}
  {"cli":"{MCD_CLI} markdown {MCD_PATH}"}
  {"cli":"{MCD_CLI} table {MCD_PATH} vehicle_variant_configuration_specs --help"}
  {"cli":"{MCD_CLI} query {MCD_PATH} \"select count(*) as rows from production_quality_measurements\""}
- Exact command names may differ by CLI build. Use --help output to adapt.
- If the CLI is unavailable, a command is not supported, or the CLI cannot express the needed join/calculation cleanly, use the Python fallback.
"""


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


def score_or_none(answer: str, question: dict[str, Any], error: str | None, dry_run: bool) -> dict[str, Any] | None:
    if dry_run or error:
        return None
    return plain_eval.score_answer(answer, question["expected_contains"])


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


def build_mcd_summary(mcd_path: Path) -> str:
    doc = mcd.open(mcd_path)
    validation = doc.validate().as_dict()
    context = doc.to_agent_context(include_tables=False)
    table_ids = [table["id"] for table in doc.to_agent_context(include_tables=True).get("tables", [])]
    tables: list[dict[str, Any]] = []
    for table_id in table_ids:
        table = doc.table(table_id)
        rows = table.rows()
        tables.append(
            {
                "id": table_id,
                "row_count": len(rows),
                "columns": table.schema.columns,
                "sample_rows": rows[:2],
            }
        )
    summary = {
        "path": str(mcd_path),
        "validation": validation,
        "title": context.get("title"),
        "blocks": context.get("blocks", []),
        "tables": tables,
        "available_document_methods": [
            name for name in ["validate", "blocks", "table", "chart", "image", "annotation", "annotations", "markdown", "to_agent_context"] if hasattr(doc, name)
        ],
        "runtime_note": (
            "This installed mcd package does not expose Document.query() or top-level mcd.query(). "
            "Use doc.table(...).rows(), doc.table(...).schema.columns, doc.markdown(), and ordinary Python "
            "calculations over table rows in the python tool."
        ),
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
    return (
        command.replace("{MCD_CLI}", quote_cmd_arg(mcd_cli))
        .replace("{MCD_PATH}", quote_cmd_arg(str(mcd_path)))
    )


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


def make_mcd_agent_prompt(
    *,
    mcd_summary_text: str,
    cli_status: dict[str, Any],
    question: dict[str, Any],
    observations: list[dict[str, Any]],
) -> str:
    return (
        "You are a document-grounded QA assistant evaluating an MCD package. "
        "Prefer the MCD CLI when it is available and can express the needed operation. "
        "Use the Python `mcd` library as a fallback for calculations, joins, or commands the CLI cannot handle. "
        "Do not guess from memory. Both tools execute in the repository root and return stdout/stderr. "
        "Print concise JSON or table-like output from tools so the next step can answer. "
        "Return exactly one JSON object and no prose. Do not return a tool call and an answer in the same response.\n\n"
        "If you need data from the CLI, return:\n"
        '{"cli":"{MCD_CLI} --help"}\n\n'
        "If the CLI is unavailable or insufficient and you need Python data access, return:\n"
        '{"python":"import os, json, mcd\\ndoc = mcd.open(os.environ[\'MCD_PATH\'])\\n# inspect or compute\\nprint(json.dumps(result, ensure_ascii=False))"}\n\n'
        "When you know the final answer, return:\n"
        '{"answer":"concise answer containing exact IDs, field names, condition values, and numbers"}\n\n'
        "CLI status:\n"
        f"{json.dumps(cli_status, ensure_ascii=False, indent=2)}\n\n"
        "MCD CLI tool reference:\n"
        f"{CLI_TOOL_REFERENCE}\n\n"
        "Python runtime note: the local installed mcd package may not expose every documented method. "
        "Check with hasattr(...) when using optional query, chart, image, dataframe, or conversion helpers. "
        "If a method is missing, use `doc.table(table_id).rows()` and ordinary Python joins, filters, "
        "grouping, sorting, and arithmetic.\n\n"
        "MCD Python tool reference:\n"
        f"{MCD_TOOL_REFERENCE}\n\n"
        "MCD package summary:\n"
        f"{mcd_summary_text}\n\n"
        "Question:\n"
        f"{json.dumps({'id': question['id'], 'question': question['prompt']}, ensure_ascii=False, indent=2)}\n\n"
        "Previous tool observations:\n"
        f"{json.dumps(observations, ensure_ascii=False, indent=2)}"
    )


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

    for step in range(1, args.max_tool_steps + 1):
        prompt = make_mcd_agent_prompt(
            mcd_summary_text=mcd_summary_text,
            cli_status=cli_status,
            question=question,
            observations=observations,
        )
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
            observation_record = {"step": step, "tool_type": "cli", "cli": action["cli"], "observation": observation}
        else:
            observation = run_python_tool(
                code=action["python"],
                mcd_path=mcd_path,
                timeout_seconds=args.python_timeout_seconds,
                max_observation_chars=args.max_observation_chars,
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
            "prompt_tool_reference": "embedded MCD_TOOL_REFERENCE",
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
        "- MCD tool references: embedded compact CLI and Python API lists",
        f"- Max tool steps: `{args.max_tool_steps}`",
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

    for provider, rows in rows_by_provider.items():
        lines.extend(
            [
                "",
                f"## {provider} Answers",
                "",
                "| # | Status | Seconds | Question | Answer |",
                "| ---: | --- | ---: | --- | --- |",
            ]
        )
        for row in rows:
            question = str(row["question"]).replace("|", "\\|")
            answer = str(row.get("answer") or row.get("error") or "").replace("\n", " ").replace("|", "\\|")
            if len(answer) > 300:
                answer = answer[:297] + "..."
            lines.append(
                f"| {row['question_index']} | {status_label(row)} | "
                f"{format_seconds(float(row.get('elapsed_seconds') or 0.0))} | {question} | {answer} |"
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
