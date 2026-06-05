# MultiHiertt Mini MCD Tools vs Original Source Tools

- Created at: `2026-06-05T23:21:55`
- MCD package: `D:\aibeaver-tests\datasets\multihiertt-mini\multihiertt-mini.mcd`
- Original package: `D:\aibeaver-tests\datasets\multihiertt-mini\original_disconnected`
- Original JSON: `D:\aibeaver-tests\datasets\multihiertt-mini\original_disconnected\dev_50.json`
- Questions: `1` from `D:\aibeaver-tests\datasets\multihiertt-mini\qa_questions_50.jsonl`
- Evaluator labels: `D:\aibeaver-tests\datasets\multihiertt-mini\answers.json`
- Evaluator: shared per-question payload from `answers.json`; both modes use the same evaluator hash.
- `mcd_tools` uses one OpenAI Responses call with native remote MCP tools against the packed MCD file.
- MCD remote MCP URL: `https://headlines-alias-reggae-paris.trycloudflare.com/mcp`
- `original_tools` gives the model original JSON/table conceptual tool contracts plus pre-materialized parsed source data.
- `Tool calls` counts native remote MCP calls reported by OpenAI. `original_tools` is one-shot and should remain zero by design.
- Modes: `mcd_tools`
- Scoring mode: `llm_judge`

| Provider | Mode | Model | EM | F1 | Passed | Failed | Scored | Total | Pass rate | Errors | Tool calls |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| openai | mcd_tools | `gpt-5.4` | 1.000 | 1.000 | 1 | 0 | 1 | 1 | 100.0% | 0 | 2 |

| Provider | Mode | Input tokens | Output tokens | Total tokens | Total seconds | Avg seconds |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| openai | mcd_tools | 7,026 | 246 | 7,272 | 8.6 | 8.6 |

## openai Matrix

| # | Question ID | mcd_tools |
| ---: | --- | --- |
| 1 | `multihiertt_mini_0001` | PASS |
