# MultiHiertt Mini MCD CLI Tools vs Original Source Tools

- Created at: `2026-06-06T01:14:21`
- MCD package: `D:\aibeaver-tests\datasets\multihiertt-mini\multihiertt-mini.mcd`
- Original package: `D:\aibeaver-tests\datasets\multihiertt-mini\original_disconnected`
- Original JSON: `D:\aibeaver-tests\datasets\multihiertt-mini\original_disconnected\dev_50.json`
- Questions: `10` from `D:\aibeaver-tests\datasets\multihiertt-mini\qa_questions_50.jsonl`
- Evaluator labels: `D:\aibeaver-tests\datasets\multihiertt-mini\answers.json`
- Evaluator: shared per-question payload from `answers.json`; both modes use the same evaluator hash.
- `mcd_cli_tools` uses targeted local MCD tool calls; it does not preload all table rows, paragraphs, or cell descriptions.
- Native remote MCP mode (`mcd_tools`) is skipped for now.
- MCD CLI: `mcd`
- MCD CLI available: `True`
- `original_tools` gives the model original JSON/table conceptual tool contracts plus pre-materialized parsed source data.
- `Tool calls` counts model-requested targeted MCD tool calls for `mcd_cli_tools`; `original_tools` is one-shot and should remain zero by design.
- Modes: `mcd_cli_tools, original_tools`
- Scoring mode: `llm_judge`

| Provider | Mode | Model | EM | F1 | Passed | Failed | Scored | Total | Pass rate | Errors | Tool calls |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| openai | mcd_cli_tools | `gpt-5.4` | 0.900 | 0.900 | 9 | 1 | 10 | 10 | 90.0% | 0 | 24 |
| openai | original_tools | `gpt-5.4` | 0.800 | 0.800 | 8 | 2 | 10 | 10 | 80.0% | 0 | 0 |

| Provider | Mode | Input tokens | Output tokens | Total tokens | Total seconds | Avg seconds |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| openai | mcd_cli_tools | 276,066 | 4,595 | 280,661 | 87.6 | 8.8 |
| openai | original_tools | 109,011 | 1,189 | 110,200 | 13.5 | 1.4 |

## openai Matrix

| # | Question ID | mcd_cli_tools | original_tools |
| ---: | --- | --- | --- |
| 1 | `multihiertt_mini_0001` | PASS | PASS |
| 2 | `multihiertt_mini_0002` | PASS | FAIL |
| 3 | `multihiertt_mini_0003` | PASS | PASS |
| 4 | `multihiertt_mini_0004` | PASS | PASS |
| 5 | `multihiertt_mini_0005` | PASS | PASS |
| 6 | `multihiertt_mini_0006` | FAIL | FAIL |
| 7 | `multihiertt_mini_0007` | PASS | PASS |
| 8 | `multihiertt_mini_0008` | PASS | PASS |
| 9 | `multihiertt_mini_0009` | PASS | PASS |
| 10 | `multihiertt_mini_0010` | PASS | PASS |
