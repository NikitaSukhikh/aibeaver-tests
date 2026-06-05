# MultiHiertt Mini MCD vs Original

- Created at: `2026-06-05T15:02:12`
- MCD package: `D:\aibeaver-tests\datasets\multihiertt-mini\multihiertt-mini.mcd`
- Original package: `D:\aibeaver-tests\datasets\multihiertt-mini\original_disconnected`
- Original JSON: `D:\aibeaver-tests\datasets\multihiertt-mini\original_disconnected\dev_50.json`
- Questions: `10` from `D:\aibeaver-tests\datasets\multihiertt-mini\qa_questions_50.jsonl`
- Evaluator labels: `D:\aibeaver-tests\datasets\multihiertt-mini\answers.json`
- Evaluator: shared per-question payload from `answers.json`; both modes use the same evaluator hash.
- Format modes: `mcd` and `original` use one model call per question and no model-visible tools.
- Agent modes: `mcd_agent` uses MCD MCP tools; `original_agent` uses original JSON source-inspection tools.
- Modes: `mcd, original`
- Scoring mode: `multihiertt`

| Provider | Mode | Model | EM | F1 | Passed | Failed | Scored | Total | Pass rate | Errors | Tool calls |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| openai | mcd | `gpt-5.4` | 0.700 | 0.700 | 7 | 3 | 10 | 10 | 70.0% | 0 | 0 |
| openai | original | `gpt-5.4` | 0.600 | 0.600 | 6 | 4 | 10 | 10 | 60.0% | 0 | 0 |

| Provider | Mode | Input tokens | Output tokens | Total tokens | Total seconds | Avg seconds |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| openai | mcd | 112,840 | 281 | 113,121 | 24.8 | 2.5 |
| openai | original | 99,985 | 284 | 100,269 | 16.7 | 1.7 |

## openai Matrix

| # | Question ID | mcd | original |
| ---: | --- | --- | --- |
| 1 | `multihiertt_mini_0001` | PASS | PASS |
| 2 | `multihiertt_mini_0002` | FAIL | FAIL |
| 3 | `multihiertt_mini_0003` | PASS | PASS |
| 4 | `multihiertt_mini_0004` | PASS | PASS |
| 5 | `multihiertt_mini_0005` | PASS | PASS |
| 6 | `multihiertt_mini_0006` | PASS | FAIL |
| 7 | `multihiertt_mini_0007` | FAIL | FAIL |
| 8 | `multihiertt_mini_0008` | FAIL | FAIL |
| 9 | `multihiertt_mini_0009` | PASS | PASS |
| 10 | `multihiertt_mini_0010` | PASS | PASS |
