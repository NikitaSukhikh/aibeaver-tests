# MultiHiertt Mini MCD CLI Tools vs Original Source Tools

- Created at: `2026-06-06T00:11:18`
- MCD package: `D:\aibeaver-tests\datasets\multihiertt-mini\multihiertt-mini.mcd`
- Original package: `D:\aibeaver-tests\datasets\multihiertt-mini\original_disconnected`
- Original JSON: `D:\aibeaver-tests\datasets\multihiertt-mini\original_disconnected\dev_50.json`
- Questions: `1` from `D:\aibeaver-tests\datasets\multihiertt-mini\qa_questions_50.jsonl`
- Evaluator labels: `D:\aibeaver-tests\datasets\multihiertt-mini\answers.json`
- Evaluator: shared per-question payload from `answers.json`; both modes use the same evaluator hash.
- `mcd_cli_tools` materializes source data from the packed MCD file with local `mcd query-batch`, then gives the model one source-pack call.
- Native remote MCP mode (`mcd_tools`) is skipped for now.
- MCD CLI: `mcd`
- MCD CLI available: `True`
- `original_tools` gives the model original JSON/table conceptual tool contracts plus pre-materialized parsed source data.
- `Tool calls` counts local MCD CLI query-batch materialization calls for `mcd_cli_tools`; `original_tools` is one-shot and should remain zero by design.
- Modes: `mcd_cli_tools, original_tools`
- Scoring mode: `llm_judge`

| Provider | Mode | Model | EM | F1 | Passed | Failed | Scored | Total | Pass rate | Errors | Tool calls |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| openai | mcd_cli_tools | `gpt-5.4` | 0.000 | 0.000 | 0 | 0 | 0 | 1 | 0.0% | 0 | 1 |
| openai | original_tools | `gpt-5.4` | 0.000 | 0.000 | 0 | 0 | 0 | 1 | 0.0% | 0 | 0 |

| Provider | Mode | Input tokens | Output tokens | Total tokens | Total seconds | Avg seconds |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| openai | mcd_cli_tools | 0 | 0 | 0 | 0.0 | 0.0 |
| openai | original_tools | 0 | 0 | 0 | 0.0 | 0.0 |

## openai Matrix

| # | Question ID | mcd_cli_tools | original_tools |
| ---: | --- | --- | --- |
| 1 | `multihiertt_mini_0001` | DRY | DRY |
