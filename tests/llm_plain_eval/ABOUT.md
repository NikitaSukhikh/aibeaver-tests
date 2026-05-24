# Straightforward tests for evaluating LLM output correctness quality against given dataset (unpacked MCD file)

- simple direct LLM api call
- LLM api call with provided tools
- LangGraph wrapper

## Knowledge-base assistant eval

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
- Eval mode: `kb_agent`
- OpenAI model: `gpt-4.1-mini`, override with `--openai-model` or `OPENAI_MODEL`
- Anthropic model: `claude-sonnet-4-5`, override with `--anthropic-model` or `ANTHROPIC_MODEL`
- xAI model: `grok-4.3`, override with `--xai-model` or `XAI_MODEL`
- Temperature: `0.0`, override with `--temperature`

Useful smoke test:

```powershell
python tests\llm_plain_eval\run_plain_eval.py --dry-run --limit 2
```

By default, each model works as a knowledge-base assistant. It receives a dataset index and can call JSON tools to inspect text files, search files, query CSV tables, and join CSV tables. This evaluates whether the model can navigate the unpacked dataset and use tools to answer the questions, instead of whether it can scan a huge raw prompt.

The old raw-context behavior is still available for comparison:

```powershell
python tests\llm_plain_eval\run_plain_eval.py --eval-mode plain_context --limit 2
```

It does not write per-question prompt files.

Each run writes:

- `run_config.json`
- `{provider}_results.jsonl`
- `all_results.jsonl`
- `summary.json`
- `summary.md`
- `comparison.svg`
- `comparison.html`
- `raw_responses\{provider}_raw.jsonl` with tool traces or raw provider responses
