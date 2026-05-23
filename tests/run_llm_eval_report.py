"""
Run document-grounded LLM evaluations and produce graphics plus a text report.

This is the high-level entry point:
    1. Runs each QA suite on OpenAI, Claude, Grok, and Gemini.
    2. Writes raw JSONL and summary JSON artifacts.
    3. Renders metric charts and representative four-model output cards.
    4. Writes a Markdown report.

Example:
    python examples/run_llm_eval_report.py --samples 2

Dry run without using API keys:
    python examples/run_llm_eval_report.py --env-file .env.does-not-exist --skip-missing-keys
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
import textwrap
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any

import matplotlib.pyplot as plt

sys.path.insert(0, str(Path(__file__).resolve().parent))
import evaluate_sota_llms as evaluator  # noqa: E402
import lyapunov_blackbox_eval as lyapunov_eval  # noqa: E402
import visualize_llm_outputs as output_viz  # noqa: E402


PROVIDERS = ["openai", "anthropic", "xai", "gemini"]
PROVIDER_LABELS = output_viz.PROVIDER_LABELS
PROVIDER_COLORS = output_viz.PROVIDER_COLORS
DEFAULT_SUITES = [
    Path("datasets/auto-manufacturer-tech-spec/qa_suite.json"),
    Path("datasets/lord-of-the-rings/qa_suite.json"),
]


def slugify(value: str) -> str:
    cleaned = []
    for char in value.lower():
        if char.isalnum():
            cleaned.append(char)
        elif char in {"-", "_", " "}:
            cleaned.append("-")
    slug = "".join(cleaned).strip("-")
    while "--" in slug:
        slug = slug.replace("--", "-")
    return slug or "item"


def read_suite_id(path: Path) -> str:
    data = json.loads(path.read_text(encoding="utf-8"))
    return str(data.get("id", path.stem))


def format_value(value: Any, digits: int = 3) -> str:
    if value is None:
        return "n/a"
    if isinstance(value, float):
        return f"{value:.{digits}f}"
    return str(value)


def rel(path: Path, base: Path) -> str:
    try:
        return path.resolve().relative_to(base.resolve()).as_posix()
    except ValueError:
        return path.as_posix()


def make_eval_args(args: argparse.Namespace, suite: Path, result_path: Path, summary_path: Path) -> argparse.Namespace:
    return argparse.Namespace(
        suite=suite,
        tasks=None,
        out=result_path,
        summary_out=summary_path,
        providers=args.providers,
        openai_model=args.openai_model,
        anthropic_model=args.anthropic_model,
        xai_model=args.xai_model,
        gemini_model=args.gemini_model,
        max_tokens=args.max_tokens,
        temperature=args.temperature,
        samples=args.samples,
        timeout=args.timeout,
        lyapunov_tau=args.lyapunov_tau,
        system_prompt=evaluator.SYSTEM_PROMPT,
        batch_system_prompt=evaluator.BATCH_SYSTEM_PROMPT,
        skip_missing_keys=args.skip_missing_keys,
    )


def metric_for(summary: dict[str, Any], provider: str, metric: str) -> float | None:
    value = summary.get("providers", {}).get(provider, {}).get(metric)
    if value is None:
        return None
    return float(value)


def render_metrics_chart(summary: dict[str, Any], out: Path) -> None:
    providers = [provider for provider in PROVIDERS if provider in summary.get("providers", {})]
    if not providers:
        return

    metrics = [
        ("mean_score", "Correctness", "higher is better"),
        ("mean_answer_family_instability", "Answer instability", "lower is better"),
        ("mean_latency_seconds", "Latency", "seconds"),
    ]

    fig, axes = plt.subplots(1, 3, figsize=(15, 4.8), dpi=160)
    fig.patch.set_facecolor("white")
    fig.suptitle(f"Suite Metrics: {summary.get('suite', 'unknown')}", x=0.02, y=0.98, ha="left", fontsize=16, fontweight="bold")

    for ax, (metric, title, subtitle) in zip(axes, metrics):
        values = [metric_for(summary, provider, metric) for provider in providers]
        plotted = [0.0 if value is None else value for value in values]
        colors = [PROVIDER_COLORS.get(provider, "#666666") for provider in providers]
        labels = [PROVIDER_LABELS.get(provider, provider) for provider in providers]
        bars = ax.bar(labels, plotted, color=colors)
        ax.set_title(title, fontsize=12, fontweight="bold")
        ax.text(0.0, 1.02, subtitle, transform=ax.transAxes, fontsize=9, color="#666666")
        ax.spines[["top", "right"]].set_visible(False)
        ax.grid(axis="y", color="#e5e5e5", linewidth=0.8)
        ax.set_axisbelow(True)
        ax.tick_params(axis="x", labelrotation=25)
        for bar, value in zip(bars, values):
            label = "n/a" if value is None else f"{value:.2f}"
            ax.text(bar.get_x() + bar.get_width() / 2, bar.get_height(), label, ha="center", va="bottom", fontsize=9)

    out.parent.mkdir(parents=True, exist_ok=True)
    fig.subplots_adjust(left=0.05, right=0.98, top=0.82, bottom=0.18, wspace=0.28)
    fig.savefig(out, bbox_inches="tight")
    plt.close(fig)


def representative_task_ids(rows: list[dict[str, Any]], limit: int) -> list[str]:
    by_family: dict[str, list[str]] = defaultdict(list)
    for row in rows:
        if row.get("row_type") != "answer":
            continue
        family_id = str(row.get("family_id") or row.get("task_id"))
        task_id = str(row.get("task_id"))
        if task_id not in by_family[family_id]:
            by_family[family_id].append(task_id)
    selected = [task_ids[0] for _, task_ids in sorted(by_family.items()) if task_ids]
    return selected[:limit]


def answer_rows(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [row for row in rows if row.get("row_type") == "answer"]


def provider_answer_stats(rows: list[dict[str, Any]]) -> dict[str, dict[str, Any]]:
    stats: dict[str, dict[str, Any]] = {}
    for provider in PROVIDERS:
        provider_rows = [row for row in answer_rows(rows) if row.get("provider") == provider]
        scores = [float(row["score"]) for row in provider_rows if row.get("score") is not None]
        stats[provider] = {
            "answers": len(provider_rows),
            "mean_score": statistics.mean(scores) if scores else None,
            "min_score": min(scores) if scores else None,
        }
    return stats


def worst_questions(rows: list[dict[str, Any]], limit: int = 8) -> list[tuple[str, float, int]]:
    scores_by_task: dict[str, list[float]] = defaultdict(list)
    for row in answer_rows(rows):
        if row.get("score") is not None:
            scores_by_task[str(row["task_id"])].append(float(row["score"]))
    ranked = [
        (task_id, statistics.mean(scores), len(scores))
        for task_id, scores in scores_by_task.items()
        if scores
    ]
    ranked.sort(key=lambda item: (item[1], item[0]))
    return ranked[:limit]


def family_instability(rows: list[dict[str, Any]], limit: int = 8) -> list[tuple[str, str, float]]:
    ranked: list[tuple[str, str, float]] = []
    for row in rows:
        if row.get("row_type") != "family_summary":
            continue
        stability = row.get("stability") or {}
        value = stability.get("mean_pairwise_cosine_distance")
        if value is not None:
            ranked.append((str(row.get("provider")), str(row.get("family_id")), float(value)))
    ranked.sort(key=lambda item: item[2], reverse=True)
    return ranked[:limit]


def write_report(
    *,
    out: Path,
    base_dir: Path,
    run_id: str,
    args: argparse.Namespace,
    suite_results: list[dict[str, Any]],
) -> None:
    lines: list[str] = []
    lines.append(f"# LLM Document QA Evaluation Report")
    lines.append("")
    lines.append(f"- Run ID: `{run_id}`")
    lines.append(f"- Samples per suite/provider: `{args.samples}`")
    lines.append(f"- Temperature: `{args.temperature}`")
    lines.append(f"- Max output tokens: `{args.max_tokens}`")
    lines.append(f"- Providers: `{', '.join(args.providers)}`")
    lines.append("")

    for result in suite_results:
        suite_id = result["suite_id"]
        summary = result["summary"]
        rows = result["rows"]
        lines.append(f"## {suite_id}")
        lines.append("")
        lines.append(f"- Raw results: [{rel(result['results_path'], base_dir)}]({rel(result['results_path'], base_dir)})")
        lines.append(f"- Summary JSON: [{rel(result['summary_path'], base_dir)}]({rel(result['summary_path'], base_dir)})")
        if result.get("metrics_chart"):
            lines.append(f"- Metrics chart: [{rel(result['metrics_chart'], base_dir)}]({rel(result['metrics_chart'], base_dir)})")
        if result.get("lyapunov_report"):
            lines.append(f"- Perturbation amplification report: [{rel(result['lyapunov_report'], base_dir)}]({rel(result['lyapunov_report'], base_dir)})")
        if result.get("lyapunov_provider_chart"):
            lines.append(f"- Lyapunov provider chart: [{rel(result['lyapunov_provider_chart'], base_dir)}]({rel(result['lyapunov_provider_chart'], base_dir)})")
        if result.get("lyapunov_combined_chart"):
            lines.append(f"- Combined score chart: [{rel(result['lyapunov_combined_chart'], base_dir)}]({rel(result['lyapunov_combined_chart'], base_dir)})")
        lines.append("")
        lines.append("| Provider | Model | Mean Score | Instability | Mean Latency | Calls | Failures |")
        lines.append("|---|---|---:|---:|---:|---:|---:|")
        for provider in args.providers:
            provider_summary = summary.get("providers", {}).get(provider, {})
            lines.append(
                "| "
                + " | ".join(
                    [
                        PROVIDER_LABELS.get(provider, provider),
                        str(provider_summary.get("model", "n/a")),
                        format_value(provider_summary.get("mean_score")),
                        format_value(provider_summary.get("mean_answer_family_instability")),
                        format_value(provider_summary.get("mean_latency_seconds"), digits=2),
                        str(provider_summary.get("completed_calls", 0)),
                        str(provider_summary.get("failed_calls", 0)),
                    ]
                )
                + " |"
            )
        lines.append("")

        stats = provider_answer_stats(rows)
        lines.append("Answer rows by provider:")
        lines.append("")
        lines.append("| Provider | Answers | Mean Score | Min Score |")
        lines.append("|---|---:|---:|---:|")
        for provider in args.providers:
            item = stats.get(provider, {})
            lines.append(
                f"| {PROVIDER_LABELS.get(provider, provider)} | {item.get('answers', 0)} | "
                f"{format_value(item.get('mean_score'))} | {format_value(item.get('min_score'))} |"
            )
        lines.append("")

        unstable = family_instability(rows)
        if unstable:
            lines.append("Most unstable answer families:")
            lines.append("")
            lines.append("| Provider | Family | Mean Pairwise Cosine Distance |")
            lines.append("|---|---|---:|")
            for provider, family_id, value in unstable:
                lines.append(f"| {PROVIDER_LABELS.get(provider, provider)} | `{family_id}` | {value:.3f} |")
            lines.append("")

        weak = worst_questions(rows)
        if weak:
            lines.append("Lowest-scoring questions:")
            lines.append("")
            lines.append("| Task | Mean Score | Answer Count |")
            lines.append("|---|---:|---:|")
            for task_id, score, count in weak:
                lines.append(f"| `{task_id}` | {score:.3f} | {count} |")
            lines.append("")

        if result["output_graphics"]:
            lines.append("Representative output graphics:")
            lines.append("")
            for graphic in result["output_graphics"]:
                relative = rel(graphic, base_dir)
                lines.append(f"- [{relative}]({relative})")
            lines.append("")

        lyapunov_summary = result.get("lyapunov_summary", {})
        if lyapunov_summary.get("providers"):
            lines.append("Correctness-weighted perturbation amplification summary:")
            lines.append("")
            lines.append("| Provider | Pairs | Combined | Correctness | Stability Factor | Stable-Wrong Risk | Mean Lambda |")
            lines.append("|---|---:|---:|---:|---:|---:|---:|")
            for provider in args.providers:
                item = lyapunov_summary["providers"].get(provider)
                if not item:
                    continue
                lines.append(
                    f"| {PROVIDER_LABELS.get(provider, provider)} | {item['pair_count']} | "
                    f"{format_value(item.get('combined_score'))} | "
                    f"{format_value(item.get('mean_pair_correctness'))} | "
                    f"{format_value(item.get('mean_stability_factor'))} | "
                    f"{format_value(item.get('stable_wrong_risk'))} | "
                    f"{item['mean_lambda_ftle']:.3f} |"
                )
            lines.append("")

    lines.append("## Notes")
    lines.append("")
    lines.append(textwrap.fill(
        "Correctness is based on the expected fields in each JSONL question. "
        "Instability is the mean pairwise cosine distance between answers in the same perturbation family; lower values indicate more stable outputs. "
        "The current Lyapunov proxy is computed inside the evaluator only when there are enough non-empty answers in a family.",
        width=100,
    ))
    lines.append("")

    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text("\n".join(lines), encoding="utf-8")


def run(args: argparse.Namespace) -> Path:
    evaluator.load_env_file(args.env_file)
    run_id = args.run_id or datetime.now().strftime("%Y%m%d-%H%M%S")
    run_dir = args.out_dir / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    suite_results: list[dict[str, Any]] = []
    for suite_path in args.suites:
        suite_id = read_suite_id(suite_path)
        suite_slug = slugify(suite_id)
        results_path = run_dir / f"{suite_slug}_results.jsonl"
        summary_path = run_dir / f"{suite_slug}_summary.json"
        metrics_chart = run_dir / f"{suite_slug}_metrics.png"

        print(f"Running suite {suite_id}...")
        eval_args = make_eval_args(args, suite_path, results_path, summary_path)
        summary = evaluator.run_suite_eval(eval_args)
        rows = output_viz.load_jsonl(results_path)

        render_metrics_chart(summary, metrics_chart)
        lyapunov_dir = run_dir / f"{suite_slug}_lyapunov"
        lyapunov_result = lyapunov_eval.analyze(
            argparse.Namespace(
                results=results_path,
                out_dir=lyapunov_dir,
                distance_floor=args.lyapunov_distance_floor,
                min_prompt_distance=args.lyapunov_min_prompt_distance,
                max_features=args.lyapunov_max_features,
                stability_alpha=args.lyapunov_stability_alpha,
            )
        )

        output_graphics: list[Path] = []
        for task_id in representative_task_ids(rows, args.visuals_per_suite):
            graphic_path = run_dir / f"{suite_slug}_{slugify(task_id)}_outputs.png"
            output_viz.render_comparison(
                rows=rows,
                task_id=task_id,
                sample_index=args.sample_index,
                out=graphic_path,
                title=f"{suite_id}: {task_id}",
                max_chars=args.max_chars,
            )
            output_graphics.append(graphic_path)

        suite_results.append(
            {
                "suite_id": suite_id,
                "summary": summary,
                "rows": rows,
                "results_path": results_path,
                "summary_path": summary_path,
                "metrics_chart": metrics_chart if metrics_chart.exists() else None,
                "lyapunov_summary": lyapunov_result["summary"],
                "lyapunov_report": lyapunov_result["report_md"],
                "lyapunov_provider_chart": lyapunov_result["provider_chart"],
                "lyapunov_combined_chart": lyapunov_result["combined_chart"],
                "lyapunov_family_heatmap": lyapunov_result["family_heatmap"],
                "output_graphics": output_graphics,
            }
        )

    report_path = run_dir / "report.md"
    write_report(out=report_path, base_dir=Path.cwd(), run_id=run_id, args=args, suite_results=suite_results)
    print(f"Wrote report: {report_path}")
    return report_path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--suites", type=Path, nargs="+", default=DEFAULT_SUITES)
    parser.add_argument("--env-file", type=Path, default=Path(".env"))
    parser.add_argument("--out-dir", type=Path, default=Path("runs/full_llm_eval"))
    parser.add_argument("--run-id", default=None)
    parser.add_argument("--providers", nargs="+", choices=PROVIDERS, default=PROVIDERS)
    parser.add_argument("--openai-model", default=None)
    parser.add_argument("--anthropic-model", default=None)
    parser.add_argument("--xai-model", default=None)
    parser.add_argument("--gemini-model", default=None)
    parser.add_argument("--samples", type=int, default=2)
    parser.add_argument(
        "--temperature",
        type=evaluator.parse_optional_float,
        default=None,
        help="Sampling temperature, or 'none' to omit the provider parameter.",
    )
    parser.add_argument("--max-tokens", type=int, default=4000)
    parser.add_argument("--timeout", type=float, default=180.0)
    parser.add_argument("--lyapunov-tau", type=int, default=2)
    parser.add_argument("--lyapunov-distance-floor", type=float, default=1e-3)
    parser.add_argument("--lyapunov-min-prompt-distance", type=float, default=1e-6)
    parser.add_argument("--lyapunov-max-features", type=int, default=4096)
    parser.add_argument("--lyapunov-stability-alpha", type=float, default=1.0)
    parser.add_argument("--sample-index", type=int, default=0)
    parser.add_argument("--visuals-per-suite", type=int, default=6)
    parser.add_argument("--max-chars", type=int, default=1100)
    parser.add_argument("--skip-missing-keys", action="store_true")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    if args.samples < 1:
        raise ValueError("--samples must be >= 1.")
    if args.visuals_per_suite < 0:
        raise ValueError("--visuals-per-suite must be >= 0.")
    run(args)


if __name__ == "__main__":
    main()
