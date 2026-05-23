# Straightforward tests for evaluating LLM output correctness quality against given dataset (unpacked MCD file)

- simple direct LLM api call
- LLM api call with provided tools
- LangGraph wrapper

## Plain provider eval

Run OpenAI, Anthropic, and xAI against the auto-manufacturer pilot questions:

```powershell
$env:OPENAI_API_KEY="..."
$env:ANTHROPIC_API_KEY="..."
$env:XAI_API_KEY="..."
python tests\llm_plain_eval\run_plain_eval.py
```

Defaults:

- Dataset context: `datasets\auto-manufacturer-tech-spec\unpacked`
- Questions: `datasets\auto-manufacturer-tech-spec\qa_pilot_questions.jsonl`
- Results root: `results\llm_plain_eval`
- Output folder: `unpacked_YYYYMMDD_HHMMSS`
- OpenAI model: `gpt-4.1-mini`, override with `--openai-model` or `OPENAI_MODEL`
- Anthropic model: `claude-sonnet-4-5`, override with `--anthropic-model` or `ANTHROPIC_MODEL`
- xAI model: `grok-4.3`, override with `--xai-model` or `XAI_MODEL`
- Temperature: `0.0`, override with `--temperature`

Useful smoke test:

```powershell
python tests\llm_plain_eval\run_plain_eval.py --dry-run --limit 2
```

Each provider call receives the shared unpacked dataset context plus a small batch of questions. The default `--batch-size 1` avoids asking a model to solve all 100 table-reasoning questions in one response. It does not write per-question prompt files.

Each run writes:

- `run_config.json`
- `{provider}_results.jsonl`
- `all_results.jsonl`
- `summary.json`
- `summary.md`
- `comparison.svg`
- `comparison.html`
- `raw_responses\{provider}_raw.jsonl`
