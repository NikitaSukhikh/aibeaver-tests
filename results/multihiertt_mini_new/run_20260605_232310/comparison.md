# MultiHiertt Mini MCD Tools vs Original Source Tools

- Created at: `2026-06-05T23:23:10`
- MCD package: `D:\aibeaver-tests\datasets\multihiertt-mini\multihiertt-mini.mcd`
- Original package: `D:\aibeaver-tests\datasets\multihiertt-mini\original_disconnected`
- Original JSON: `D:\aibeaver-tests\datasets\multihiertt-mini\original_disconnected\dev_50.json`
- Questions: `10` from `D:\aibeaver-tests\datasets\multihiertt-mini\qa_questions_50.jsonl`
- Evaluator labels: `D:\aibeaver-tests\datasets\multihiertt-mini\answers.json`
- Evaluator: shared per-question payload from `answers.json`; both modes use the same evaluator hash.
- `mcd_tools` uses one OpenAI Responses call with native remote MCP tools against the packed MCD file.
- MCD remote MCP URL: `https://headlines-alias-reggae-paris.trycloudflare.com/mcp`
- `original_tools` gives the model original JSON/table conceptual tool contracts plus pre-materialized parsed source data.
- `Tool calls` counts native remote MCP calls reported by OpenAI. `original_tools` is one-shot and should remain zero by design.
- Modes: `mcd_tools, original_tools`
- Scoring mode: `llm_judge`

| Provider | Mode | Model | EM | F1 | Passed | Failed | Scored | Total | Pass rate | Errors | Tool calls |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| openai | mcd_tools | `gpt-5.4` | 0.700 | 0.700 | 7 | 3 | 10 | 10 | 70.0% | 0 | 32 |
| openai | original_tools | `gpt-5.4` | 0.700 | 0.700 | 7 | 3 | 10 | 10 | 70.0% | 0 | 0 |

| Provider | Mode | Input tokens | Output tokens | Total tokens | Total seconds | Avg seconds |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| openai | mcd_tools | 70,825 | 3,525 | 74,350 | 109.5 | 11.0 |
| openai | original_tools | 108,703 | 1,185 | 109,888 | 15.9 | 1.6 |

## openai Matrix

| # | Question ID | mcd_tools | original_tools |
| ---: | --- | --- | --- |
| 1 | `multihiertt_mini_0001` | PASS | PASS |
| 2 | `multihiertt_mini_0002` | FAIL | FAIL |
| 3 | `multihiertt_mini_0003` | PASS | PASS |
| 4 | `multihiertt_mini_0004` | PASS | PASS |
| 5 | `multihiertt_mini_0005` | PASS | PASS |
| 6 | `multihiertt_mini_0006` | FAIL | FAIL |
| 7 | `multihiertt_mini_0007` | FAIL | FAIL |
| 8 | `multihiertt_mini_0008` | PASS | PASS |
| 9 | `multihiertt_mini_0009` | PASS | PASS |
| 10 | `multihiertt_mini_0010` | PASS | PASS |
