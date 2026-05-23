#!/usr/bin/env python3
"""Run a plain-context LLM eval over an unpacked MCD dataset."""

from __future__ import annotations

import argparse
import html
import json
import os
import re
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


DEFAULT_DATASET_DIR = Path("datasets/auto-manufacturer-tech-spec/unpacked")
DEFAULT_QUESTIONS_PATH = Path("datasets/auto-manufacturer-tech-spec/qa_pilot_questions.jsonl")
DEFAULT_RESULTS_ROOT = Path("results/llm_plain_eval")
DEFAULT_OPENAI_MODEL = "gpt-4.1-mini"
DEFAULT_ANTHROPIC_MODEL = "claude-sonnet-4-5"
DEFAULT_XAI_MODEL = "grok-4.3"
DEFAULT_MAX_OUTPUT_TOKENS = 12000


@dataclass(frozen=True)
class ProviderConfig:
    name: str
    model: str
    api_key_env: str


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Evaluate provider answers against expected_contains checks."
    )
    parser.add_argument("--dataset-dir", type=Path, default=DEFAULT_DATASET_DIR)
    parser.add_argument("--questions", type=Path, default=DEFAULT_QUESTIONS_PATH)
    parser.add_argument("--results-root", type=Path, default=DEFAULT_RESULTS_ROOT)
    parser.add_argument("--openai-model", default=os.getenv("OPENAI_MODEL", DEFAULT_OPENAI_MODEL))
    parser.add_argument(
        "--anthropic-model", default=os.getenv("ANTHROPIC_MODEL", DEFAULT_ANTHROPIC_MODEL)
    )
    parser.add_argument("--xai-model", default=os.getenv("XAI_MODEL", DEFAULT_XAI_MODEL))
    parser.add_argument(
        "--providers",
        nargs="+",
        choices=["openai", "anthropic", "xai"],
        default=["openai", "anthropic", "xai"],
    )
    parser.add_argument("--limit", type=int, default=None, help="Run only the first N questions.")
    parser.add_argument("--max-output-tokens", type=int, default=DEFAULT_MAX_OUTPUT_TOKENS)
    parser.add_argument("--timeout-seconds", type=int, default=120)
    parser.add_argument("--retries", type=int, default=2)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Build the result directory and reports without calling provider APIs.",
    )
    return parser.parse_args()


def load_dotenv(path: Path = Path(".env")) -> None:
    if not path.exists():
        return

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def read_jsonl(path: Path) -> list[dict[str, Any]]:
    questions: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line_number, line in enumerate(handle, start=1):
            stripped = line.strip()
            if not stripped:
                continue
            try:
                question = json.loads(stripped)
            except json.JSONDecodeError as exc:
                raise ValueError(f"Invalid JSON on {path}:{line_number}: {exc}") from exc
            for field in ("id", "prompt", "expected_contains"):
                if field not in question:
                    raise ValueError(f"Missing {field!r} on {path}:{line_number}")
            questions.append(question)
    return questions


def context_paths(dataset_dir: Path) -> list[Path]:
    manifest_path = dataset_dir / "manifest.json"
    if not manifest_path.exists():
        raise FileNotFoundError(f"Dataset manifest not found: {manifest_path}")

    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    paths = [dataset_dir / manifest["entrypoint"]]
    for table in manifest.get("tables", []):
        paths.append(dataset_dir / table["data"])
    return paths


def build_context(dataset_dir: Path) -> tuple[str, list[str]]:
    parts: list[str] = []
    included_paths: list[str] = []
    for path in context_paths(dataset_dir):
        if not path.exists():
            raise FileNotFoundError(f"Dataset context file not found: {path}")
        relative = path.relative_to(dataset_dir)
        included_paths.append(relative.as_posix())
        parts.append(f"## File: {relative.as_posix()}\n\n{path.read_text(encoding='utf-8')}")
    return "\n\n---\n\n".join(parts), included_paths


def make_eval_prompt(context: str, questions: list[dict[str, Any]]) -> str:
    question_payload = [
        {
            "id": question["id"],
            "question": question["prompt"],
        }
        for question in questions
    ]
    return (
        "Use only the dataset context below to answer every question in the question set. "
        "Prefer exact IDs, field names, and numeric values from the tables. "
        "Keep each answer concise and include enough detail for a substring-based evaluator.\n"
        "Return JSON only, with this exact shape:\n"
        '{"answers":[{"id":"question id","answer":"concise answer"}]}\n\n'
        "<dataset_context>\n"
        f"{context}\n"
        "</dataset_context>\n\n"
        "<question_set>\n"
        f"{json.dumps(question_payload, ensure_ascii=False, indent=2)}\n"
        "</question_set>"
    )


def http_json(
    url: str,
    headers: dict[str, str],
    payload: dict[str, Any],
    timeout_seconds: int,
) -> tuple[dict[str, Any], dict[str, str]]:
    data = json.dumps(payload).encode("utf-8")
    request = Request(url, data=data, headers=headers, method="POST")
    try:
        with urlopen(request, timeout=timeout_seconds) as response:
            body = response.read().decode("utf-8")
            response_headers = dict(response.headers.items())
    except HTTPError as exc:
        error_body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"HTTP {exc.code} from {url}: {error_body}") from exc
    except URLError as exc:
        raise RuntimeError(f"Request failed for {url}: {exc}") from exc

    return json.loads(body), response_headers


def extract_openai_text(response: dict[str, Any]) -> str:
    if isinstance(response.get("output_text"), str):
        return response["output_text"]

    chunks: list[str] = []
    for item in response.get("output", []):
        for content in item.get("content", []):
            text = content.get("text")
            if isinstance(text, str):
                chunks.append(text)
    return "\n".join(chunks).strip()


def call_openai(
    prompt: str,
    model: str,
    max_output_tokens: int,
    timeout_seconds: int,
) -> tuple[str, dict[str, Any]]:
    api_key = require_env("OPENAI_API_KEY")
    payload = {
        "model": model,
        "input": prompt,
        "max_output_tokens": max_output_tokens,
    }
    response, headers = http_json(
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
    }
    return extract_openai_text(response), metadata


def call_anthropic(
    prompt: str,
    model: str,
    max_output_tokens: int,
    timeout_seconds: int,
) -> tuple[str, dict[str, Any]]:
    api_key = require_env("ANTHROPIC_API_KEY")
    payload = {
        "model": model,
        "max_tokens": max_output_tokens,
        "messages": [{"role": "user", "content": prompt}],
    }
    response, headers = http_json(
        "https://api.anthropic.com/v1/messages",
        {
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01",
            "Content-Type": "application/json",
        },
        payload,
        timeout_seconds,
    )
    chunks = [
        content.get("text", "")
        for content in response.get("content", [])
        if content.get("type") == "text"
    ]
    metadata = {
        "id": response.get("id"),
        "usage": response.get("usage"),
        "request_id": headers.get("request-id"),
    }
    return "\n".join(chunks).strip(), metadata


def call_xai(
    prompt: str,
    model: str,
    max_output_tokens: int,
    timeout_seconds: int,
) -> tuple[str, dict[str, Any]]:
    api_key = require_env("XAI_API_KEY")
    payload = {
        "model": model,
        "messages": [{"role": "user", "content": prompt}],
        "max_tokens": max_output_tokens,
        "stream": False,
    }
    response, headers = http_json(
        "https://api.x.ai/v1/chat/completions",
        {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        payload,
        timeout_seconds,
    )
    choices = response.get("choices") or []
    message = choices[0].get("message", {}) if choices else {}
    metadata = {
        "id": response.get("id"),
        "usage": response.get("usage"),
        "request_id": headers.get("x-request-id") or headers.get("request-id"),
        "finish_reason": choices[0].get("finish_reason") if choices else None,
    }
    return str(message.get("content") or "").strip(), metadata


def require_env(name: str) -> str:
    value = os.getenv(name)
    if not value:
        raise RuntimeError(f"Missing required environment variable: {name}")
    return value


def normalize(text: str) -> str:
    return re.sub(r"\s+", " ", text.casefold())


def contains_expected(answer: str, expected: str) -> bool:
    normalized_answer = normalize(answer)
    normalized_expected = normalize(expected)
    if normalized_expected in normalized_answer:
        return True

    comma_free_answer = normalized_answer.replace(",", "")
    comma_free_expected = normalized_expected.replace(",", "")
    return comma_free_expected in comma_free_answer


def score_answer(answer: str, expected_contains: list[Any]) -> dict[str, Any]:
    checks = []
    for expected in expected_contains:
        expected_text = str(expected)
        checks.append(
            {
                "expected": expected_text,
                "found": contains_expected(answer, expected_text),
            }
        )

    found_count = sum(1 for check in checks if check["found"])
    return {
        "passed": found_count == len(checks),
        "found_count": found_count,
        "expected_count": len(checks),
        "checks": checks,
    }


def extract_json_object(text: str) -> dict[str, Any]:
    stripped = text.strip()
    if stripped.startswith("```"):
        stripped = re.sub(r"^```(?:json)?\s*", "", stripped, flags=re.IGNORECASE)
        stripped = re.sub(r"\s*```$", "", stripped)

    try:
        value = json.loads(stripped)
    except json.JSONDecodeError:
        start = stripped.find("{")
        end = stripped.rfind("}")
        if start == -1 or end == -1 or end <= start:
            raise
        value = json.loads(stripped[start : end + 1])

    if not isinstance(value, dict):
        raise ValueError("Provider response JSON must be an object.")
    return value


def parse_answer_map(text: str) -> dict[str, str]:
    data = extract_json_object(text)
    answers = data.get("answers")
    if not isinstance(answers, list):
        raise ValueError("Provider response JSON must contain an 'answers' array.")

    answer_map: dict[str, str] = {}
    for item in answers:
        if not isinstance(item, dict):
            continue
        question_id = item.get("id")
        answer = item.get("answer")
        if question_id is None or answer is None:
            continue
        answer_map[str(question_id)] = str(answer).strip()
    return answer_map


def call_with_retries(
    provider: str,
    prompt: str,
    model: str,
    max_output_tokens: int,
    timeout_seconds: int,
    retries: int,
) -> tuple[str, dict[str, Any]]:
    calls = {
        "openai": call_openai,
        "anthropic": call_anthropic,
        "xai": call_xai,
    }
    call = calls[provider]
    last_error: Exception | None = None
    for attempt in range(retries + 1):
        try:
            return call(prompt, model, max_output_tokens, timeout_seconds)
        except Exception as exc:  # noqa: BLE001 - preserve provider errors in result files.
            last_error = exc
            if attempt < retries:
                time.sleep(2**attempt)
    assert last_error is not None
    raise last_error


def make_output_dir(results_root: Path, dataset_dir: Path) -> Path:
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_name = f"{dataset_dir.name}_{timestamp}"
    for suffix in ["", *[f"_{index:02d}" for index in range(1, 100)]]:
        output_dir = results_root / f"{base_name}{suffix}"
        try:
            output_dir.mkdir(parents=True, exist_ok=False)
            return output_dir
        except FileExistsError:
            continue
    raise RuntimeError(f"Could not create a unique output directory under {results_root}")


def write_json(path: Path, value: Any) -> None:
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def write_jsonl(path: Path, rows: list[dict[str, Any]]) -> None:
    with path.open("w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def write_summary_markdown(path: Path, summary: dict[str, Any]) -> None:
    lines = [
        "# LLM Plain Eval Summary",
        "",
        f"- Dataset: `{summary['dataset_dir']}`",
        f"- Questions: `{summary['questions_path']}`",
        f"- Question count: {summary['question_count']}",
        f"- Created at: {summary['created_at']}",
        "",
        "| Provider | Model | Passed | Failed | Scored | Total | Pass rate | Errors |",
        "| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |",
    ]
    for provider in summary["providers"]:
        lines.append(
            "| {name} | `{model}` | {passed} | {failed} | {scored} | {total} | {rate:.1%} | {errors} |".format(
                name=provider["name"],
                model=provider["model"],
                passed=provider["passed"],
                failed=provider.get("failed", 0),
                scored=provider.get("scored", provider["total"]),
                total=provider["total"],
                rate=provider["pass_rate"],
                errors=provider["errors"],
            )
        )
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def provider_palette(index: int) -> dict[str, str]:
    palettes = [
        {"main": "#2563eb", "soft": "#dbeafe"},
        {"main": "#16a34a", "soft": "#dcfce7"},
        {"main": "#9333ea", "soft": "#f3e8ff"},
        {"main": "#ea580c", "soft": "#ffedd5"},
    ]
    return palettes[index % len(palettes)]


def short_family_id(family_id: str | None) -> str:
    if not family_id:
        return "unknown"
    return family_id.replace("auto_pilot_", "").replace("_", " ")


def family_breakdown(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    families: dict[tuple[str, str], dict[str, Any]] = {}
    for row in rows:
        provider = row["provider"]
        family_id = row.get("family_id") or "unknown"
        key = (family_id, provider)
        if key not in families:
            families[key] = {
                "family_id": family_id,
                "provider": provider,
                "passed": 0,
                "failed": 0,
                "errors": 0,
                "scored": 0,
                "total": 0,
            }
        family = families[key]
        family["total"] += 1
        if row["error"]:
            family["errors"] += 1
        elif row["score"] is not None:
            family["scored"] += 1
            if row["score"]["passed"]:
                family["passed"] += 1
            else:
                family["failed"] += 1

    breakdown = list(families.values())
    breakdown.sort(key=lambda item: (item["family_id"], item["provider"]))
    return breakdown


def write_comparison_svg(path: Path, summary: dict[str, Any]) -> None:
    providers = summary["providers"]
    width = 1120
    card_height = 128
    top = 120
    gap = 24
    height = top + len(providers) * (card_height + gap) + 95
    max_total = max((provider["total"] for provider in providers), default=1)

    elements = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">',
        '<rect width="100%" height="100%" fill="#f8fafc"/>',
        '<text x="48" y="58" font-family="Arial, sans-serif" font-size="30" font-weight="700" fill="#0f172a">LLM Plain Eval Comparison</text>',
        f'<text x="48" y="88" font-family="Arial, sans-serif" font-size="15" fill="#475569">{html.escape(summary["created_at"])} | {summary["question_count"]} questions</text>',
    ]

    for index, provider in enumerate(providers):
        palette = provider_palette(index)
        y = top + index * (card_height + gap)
        scored = provider.get("scored", provider["total"])
        passed = provider["passed"]
        failed = provider.get("failed", max(scored - passed, 0))
        errors = provider["errors"]
        unscored = max(provider["total"] - scored - errors, 0)
        pass_rate = passed / scored if scored else 0.0
        bar_x = 360
        bar_y = y + 57
        bar_width = 690
        bar_height = 28
        passed_width = round(bar_width * passed / max_total)
        failed_width = round(bar_width * failed / max_total)
        error_width = round(bar_width * errors / max_total)
        unscored_width = max(round(bar_width * unscored / max_total), 0)
        failed_x = bar_x + passed_width
        error_x = failed_x + failed_width
        unscored_x = error_x + error_width

        elements.extend(
            [
                f'<rect x="40" y="{y}" width="1040" height="{card_height}" rx="8" fill="#ffffff" stroke="#e2e8f0"/>',
                f'<rect x="40" y="{y}" width="8" height="{card_height}" rx="4" fill="{palette["main"]}"/>',
                f'<text x="72" y="{y + 38}" font-family="Arial, sans-serif" font-size="22" font-weight="700" fill="#0f172a">{html.escape(provider["name"])}</text>',
                f'<text x="72" y="{y + 66}" font-family="Arial, sans-serif" font-size="13" fill="#64748b">{html.escape(provider["model"])}</text>',
                f'<text x="72" y="{y + 100}" font-family="Arial, sans-serif" font-size="24" font-weight="700" fill="{palette["main"]}">{pass_rate:.1%}</text>',
                f'<text x="170" y="{y + 99}" font-family="Arial, sans-serif" font-size="13" fill="#475569">pass rate over scored answers</text>',
                f'<rect x="{bar_x}" y="{bar_y}" width="{bar_width}" height="{bar_height}" rx="6" fill="#e2e8f0"/>',
                f'<rect x="{bar_x}" y="{bar_y}" width="{passed_width}" height="{bar_height}" rx="6" fill="#22c55e"/>',
                f'<rect x="{failed_x}" y="{bar_y}" width="{failed_width}" height="{bar_height}" fill="#ef4444"/>',
                f'<rect x="{error_x}" y="{bar_y}" width="{error_width}" height="{bar_height}" fill="#f59e0b"/>',
                f'<rect x="{unscored_x}" y="{bar_y}" width="{unscored_width}" height="{bar_height}" fill="#94a3b8"/>',
                f'<text x="{bar_x}" y="{y + 38}" font-family="Arial, sans-serif" font-size="14" font-weight="700" fill="#334155">passed {passed}</text>',
                f'<text x="{bar_x + 145}" y="{y + 38}" font-family="Arial, sans-serif" font-size="14" font-weight="700" fill="#334155">failed {failed}</text>',
                f'<text x="{bar_x + 280}" y="{y + 38}" font-family="Arial, sans-serif" font-size="14" font-weight="700" fill="#334155">errors {errors}</text>',
                f'<text x="{bar_x + 415}" y="{y + 38}" font-family="Arial, sans-serif" font-size="14" font-weight="700" fill="#334155">unscored {unscored}</text>',
                f'<text x="{bar_x + bar_width - 110}" y="{y + 105}" font-family="Arial, sans-serif" font-size="13" fill="#64748b">total {provider["total"]}</text>',
            ]
        )

    legend_y = height - 43
    legend_items = [("Passed", "#22c55e"), ("Failed", "#ef4444"), ("Error", "#f59e0b"), ("Unscored", "#94a3b8")]
    legend_x = 48
    for label, color in legend_items:
        elements.append(f'<rect x="{legend_x}" y="{legend_y - 12}" width="14" height="14" rx="3" fill="{color}"/>')
        elements.append(f'<text x="{legend_x + 22}" y="{legend_y}" font-family="Arial, sans-serif" font-size="13" fill="#475569">{label}</text>')
        legend_x += 116

    elements.append("</svg>")
    path.write_text("\n".join(elements) + "\n", encoding="utf-8")


def write_comparison_html(
    path: Path,
    summary: dict[str, Any],
    rows: list[dict[str, Any]],
    svg_filename: str,
) -> None:
    families = family_breakdown(rows)
    provider_names = [provider["name"] for provider in summary["providers"]]
    family_ids = sorted({family["family_id"] for family in families})
    by_family_provider = {(item["family_id"], item["provider"]): item for item in families}

    provider_cards = []
    for index, provider in enumerate(summary["providers"]):
        palette = provider_palette(index)
        scored = provider.get("scored", provider["total"])
        passed = provider["passed"]
        failed = provider.get("failed", max(scored - passed, 0))
        errors = provider["errors"]
        unscored = max(provider["total"] - scored - errors, 0)
        rate = passed / scored if scored else 0.0
        provider_cards.append(
            f"""
            <section class="card" style="--accent:{palette['main']}; --accent-soft:{palette['soft']}">
              <div class="card-top">
                <div>
                  <h2>{html.escape(provider['name'])}</h2>
                  <p>{html.escape(provider['model'])}</p>
                </div>
                <strong>{rate:.1%}</strong>
              </div>
              <div class="bar" aria-label="Result split">
                <span class="passed" style="width:{(passed / max(provider['total'], 1)) * 100:.2f}%"></span>
                <span class="failed" style="width:{(failed / max(provider['total'], 1)) * 100:.2f}%"></span>
                <span class="error" style="width:{(errors / max(provider['total'], 1)) * 100:.2f}%"></span>
                <span class="unscored" style="width:{(unscored / max(provider['total'], 1)) * 100:.2f}%"></span>
              </div>
              <dl>
                <div><dt>Passed</dt><dd>{passed}</dd></div>
                <div><dt>Failed</dt><dd>{failed}</dd></div>
                <div><dt>Errors</dt><dd>{errors}</dd></div>
                <div><dt>Scored</dt><dd>{scored}</dd></div>
              </dl>
            </section>
            """
        )

    family_rows = []
    for family_id in family_ids:
        cells = [f"<th>{html.escape(short_family_id(family_id))}</th>"]
        for provider_name in provider_names:
            item = by_family_provider.get((family_id, provider_name))
            if not item or not item["scored"]:
                cells.append('<td><span class="empty">n/a</span></td>')
                continue
            rate = item["passed"] / item["scored"]
            cells.append(
                f"""
                <td>
                  <div class="mini-bar"><span style="width:{rate * 100:.2f}%"></span></div>
                  <strong>{rate:.0%}</strong>
                  <small>{item['passed']}/{item['scored']}</small>
                </td>
                """
            )
        family_rows.append(f"<tr>{''.join(cells)}</tr>")

    html_text = f"""<!doctype html>
<html lang="en">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>LLM Plain Eval Comparison</title>
  <style>
    :root {{
      color-scheme: light;
      font-family: Arial, Helvetica, sans-serif;
      background: #f8fafc;
      color: #0f172a;
    }}
    body {{ margin: 0; }}
    main {{ max-width: 1180px; margin: 0 auto; padding: 40px 24px 56px; }}
    header {{ margin-bottom: 28px; }}
    h1 {{ margin: 0 0 8px; font-size: 34px; letter-spacing: 0; }}
    p {{ margin: 0; color: #475569; }}
    .cards {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)); gap: 18px; }}
    .card {{
      background: #fff;
      border: 1px solid #e2e8f0;
      border-top: 6px solid var(--accent);
      border-radius: 8px;
      padding: 18px;
    }}
    .card-top {{ display: flex; justify-content: space-between; gap: 16px; align-items: flex-start; }}
    h2 {{ margin: 0 0 4px; font-size: 22px; }}
    .card strong {{ font-size: 30px; color: var(--accent); }}
    .bar {{
      display: flex;
      width: 100%;
      height: 24px;
      overflow: hidden;
      background: #e2e8f0;
      border-radius: 6px;
      margin: 22px 0 16px;
    }}
    .passed {{ background: #22c55e; }}
    .failed {{ background: #ef4444; }}
    .error {{ background: #f59e0b; }}
    .unscored {{ background: #94a3b8; }}
    dl {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; margin: 0; }}
    dt {{ color: #64748b; font-size: 12px; }}
    dd {{ margin: 3px 0 0; font-weight: 700; }}
    .visual, .table-wrap {{
      margin-top: 22px;
      background: #fff;
      border: 1px solid #e2e8f0;
      border-radius: 8px;
      padding: 18px;
    }}
    .visual img {{ display: block; width: 100%; height: auto; }}
    h3 {{ margin: 0 0 14px; font-size: 20px; }}
    table {{ width: 100%; border-collapse: collapse; }}
    th, td {{ border-top: 1px solid #e2e8f0; padding: 12px; text-align: left; vertical-align: middle; }}
    thead th {{ border-top: 0; color: #475569; font-size: 13px; }}
    tbody th {{ width: 42%; font-weight: 600; color: #334155; }}
    td strong {{ display: inline-block; min-width: 44px; }}
    td small {{ color: #64748b; }}
    .mini-bar {{
      display: inline-block;
      width: 120px;
      height: 10px;
      margin-right: 10px;
      border-radius: 999px;
      background: #e2e8f0;
      overflow: hidden;
      vertical-align: middle;
    }}
    .mini-bar span {{ display: block; height: 100%; background: #22c55e; }}
    .empty {{ color: #94a3b8; }}
    .legend {{ display: flex; flex-wrap: wrap; gap: 14px; margin-top: 14px; color: #475569; font-size: 13px; }}
    .legend span::before {{
      content: "";
      display: inline-block;
      width: 12px;
      height: 12px;
      border-radius: 3px;
      margin-right: 6px;
      vertical-align: -1px;
      background: var(--legend-color);
    }}
  </style>
</head>
<body>
  <main>
    <header>
      <h1>LLM Plain Eval Comparison</h1>
      <p>{html.escape(summary['created_at'])} | {summary['question_count']} questions | {html.escape(summary['dataset_dir'])}</p>
    </header>
    <section class="cards">
      {''.join(provider_cards)}
    </section>
    <section class="visual">
      <h3>Provider Result Split</h3>
      <img src="{html.escape(svg_filename)}" alt="LLM provider comparison infographic">
      <div class="legend">
        <span style="--legend-color:#22c55e">Passed</span>
        <span style="--legend-color:#ef4444">Failed</span>
        <span style="--legend-color:#f59e0b">Error</span>
        <span style="--legend-color:#94a3b8">Unscored</span>
      </div>
    </section>
    <section class="table-wrap">
      <h3>Family Pass Rates</h3>
      <table>
        <thead>
          <tr>
            <th>Question family</th>
            {''.join(f'<th>{html.escape(name)}</th>' for name in provider_names)}
          </tr>
        </thead>
        <tbody>
          {''.join(family_rows)}
        </tbody>
      </table>
    </section>
  </main>
</body>
</html>
"""
    path.write_text(html_text, encoding="utf-8")


def provider_configs(args: argparse.Namespace) -> list[ProviderConfig]:
    configs = {
        "openai": ProviderConfig("openai", args.openai_model, "OPENAI_API_KEY"),
        "anthropic": ProviderConfig("anthropic", args.anthropic_model, "ANTHROPIC_API_KEY"),
        "xai": ProviderConfig("xai", args.xai_model, "XAI_API_KEY"),
    }
    return [configs[name] for name in args.providers]


def validate_provider_env(configs: list[ProviderConfig]) -> None:
    missing = [config.api_key_env for config in configs if not os.getenv(config.api_key_env)]
    if missing:
        formatted = ", ".join(sorted(set(missing)))
        raise RuntimeError(
            f"Missing required environment variable(s): {formatted}. "
            "Set them in the shell or .env, or use --providers to run a subset."
        )


def main() -> int:
    load_dotenv()
    args = parse_args()
    dataset_dir = args.dataset_dir.resolve()
    questions_path = args.questions.resolve()
    configs = provider_configs(args)
    if not args.dry_run:
        validate_provider_env(configs)

    questions = read_jsonl(questions_path)
    if args.limit is not None:
        questions = questions[: args.limit]
    context, included_context_paths = build_context(dataset_dir)
    output_dir = make_output_dir(args.results_root, dataset_dir)

    all_rows: list[dict[str, Any]] = []
    summary_providers: list[dict[str, Any]] = []
    raw_responses_dir = output_dir / "raw_responses"
    raw_responses_dir.mkdir()

    run_config = {
        "dataset_dir": str(dataset_dir),
        "questions_path": str(questions_path),
        "included_context_paths": included_context_paths,
        "question_count": len(questions),
        "providers": [config.__dict__ for config in configs],
        "max_output_tokens": args.max_output_tokens,
        "timeout_seconds": args.timeout_seconds,
        "retries": args.retries,
        "dry_run": args.dry_run,
    }
    write_json(output_dir / "run_config.json", run_config)

    for config in configs:
        provider_rows: list[dict[str, Any]] = []
        eval_prompt = make_eval_prompt(context, questions)
        started = time.perf_counter()
        raw_response_path = raw_responses_dir / f"{config.name}.txt"

        if args.dry_run:
            raw_answer = json.dumps({"answers": []}, ensure_ascii=False)
            metadata: dict[str, Any] = {"dry_run": True}
            provider_error = None
            answer_map: dict[str, str] = {}
        else:
            try:
                raw_answer, metadata = call_with_retries(
                    config.name,
                    eval_prompt,
                    config.model,
                    args.max_output_tokens,
                    args.timeout_seconds,
                    args.retries,
                )
                provider_error = None
            except Exception as exc:  # noqa: BLE001 - write failed question and continue.
                raw_answer = ""
                metadata = {}
                provider_error = str(exc)

            if provider_error:
                answer_map = {}
            else:
                try:
                    answer_map = parse_answer_map(raw_answer)
                except Exception as exc:  # noqa: BLE001 - keep parse failure in result rows.
                    answer_map = {}
                    provider_error = f"Could not parse provider JSON response: {exc}"

        raw_response_path.write_text(raw_answer, encoding="utf-8")
        elapsed_seconds = round(time.perf_counter() - started, 3)

        for index, question in enumerate(questions, start=1):
            answer = answer_map.get(question["id"], "")
            error = provider_error
            if not error and not answer and not args.dry_run:
                error = "Provider response did not include an answer for this question."

            score = (
                score_answer(answer, question["expected_contains"])
                if not error and not args.dry_run
                else None
            )
            row = {
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
                "metadata": {
                    **metadata,
                    "raw_response_path": raw_response_path.relative_to(output_dir).as_posix(),
                },
                "elapsed_seconds": elapsed_seconds,
            }
            provider_rows.append(row)
            all_rows.append(row)

            if args.dry_run:
                status = "DRY"
            elif error:
                status = "ERROR"
            else:
                status = "PASS" if score and score["passed"] else "FAIL"
            print(f"{config.name} {index}/{len(questions)} {question['id']}: {status}", flush=True)

        passed = sum(1 for row in provider_rows if row["score"] and row["score"]["passed"])
        scored = sum(1 for row in provider_rows if row["score"] is not None)
        failed = scored - passed
        errors = sum(1 for row in provider_rows if row["error"])
        summary_providers.append(
            {
                "name": config.name,
                "model": config.model,
                "passed": passed,
                "failed": failed,
                "scored": scored,
                "total": len(provider_rows),
                "pass_rate": passed / scored if scored else 0.0,
                "errors": errors,
            }
        )
        write_jsonl(output_dir / f"{config.name}_results.jsonl", provider_rows)

    summary = {
        "created_at": datetime.now().isoformat(timespec="seconds"),
        "dataset_dir": str(dataset_dir),
        "questions_path": str(questions_path),
        "question_count": len(questions),
        "providers": summary_providers,
    }
    write_jsonl(output_dir / "all_results.jsonl", all_rows)
    write_json(output_dir / "summary.json", summary)
    write_summary_markdown(output_dir / "summary.md", summary)
    write_comparison_svg(output_dir / "comparison.svg", summary)
    write_comparison_html(output_dir / "comparison.html", summary, all_rows, "comparison.svg")

    print(f"Results written to {output_dir}")
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as exc:  # noqa: BLE001 - command-line entrypoint should be concise.
        print(f"ERROR: {exc}", file=sys.stderr)
        sys.exit(1)
