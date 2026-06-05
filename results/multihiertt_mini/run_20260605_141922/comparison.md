# MultiHiertt Mini MCD vs Original

- Created at: `2026-06-05T14:19:22`
- MCD package: `D:\aibeaver-tests\datasets\multihiertt-mini\multihiertt-mini.mcd`
- Original package: `D:\aibeaver-tests\datasets\multihiertt-mini\original_disconnected`
- Original JSON: `D:\aibeaver-tests\datasets\multihiertt-mini\original_disconnected\dev_50.json`
- Questions: `10` from `D:\aibeaver-tests\datasets\multihiertt-mini\qa_questions_50.jsonl`
- Evaluator labels: `D:\aibeaver-tests\datasets\multihiertt-mini\answers.json`
- Evaluator: shared per-question payload from `answers.json`; both modes use the same evaluator hash.
- Format modes: `mcd` and `original` use one model call per question and no model-visible tools.
- Agent modes: `mcd_agent` uses MCD MCP tools; `original_agent` uses original JSON source-inspection tools.
- Modes: `mcd_agent, original_agent`
- Scoring mode: `llm_judge`

| Provider | Mode | Model | Passed | Failed | Scored | Total | Pass rate | Errors | Tool calls |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| openai | mcd_agent | `gpt-5.4` | 7 | 3 | 10 | 10 | 70.0% | 0 | 12 |
| openai | original_agent | `gpt-5.4` | 0 | 0 | 0 | 10 | 0.0% | 10 | 0 |

| Provider | Mode | Input tokens | Output tokens | Total tokens | Total seconds | Avg seconds |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| openai | mcd_agent | 178,262 | 4,774 | 183,036 | 90.5 | 9.1 |
| openai | original_agent | 25,332 | 942 | 26,274 | 30.5 | 3.0 |

## openai Matrix

| # | Question ID | mcd_agent | original_agent |
| ---: | --- | --- | --- |
| 1 | `multihiertt_mini_0001` | PASS | ERR |
| 2 | `multihiertt_mini_0002` | FAIL | ERR |
| 3 | `multihiertt_mini_0003` | PASS | ERR |
| 4 | `multihiertt_mini_0004` | FAIL | ERR |
| 5 | `multihiertt_mini_0005` | PASS | ERR |
| 6 | `multihiertt_mini_0006` | FAIL | ERR |
| 7 | `multihiertt_mini_0007` | PASS | ERR |
| 8 | `multihiertt_mini_0008` | PASS | ERR |
| 9 | `multihiertt_mini_0009` | PASS | ERR |
| 10 | `multihiertt_mini_0010` | PASS | ERR |
