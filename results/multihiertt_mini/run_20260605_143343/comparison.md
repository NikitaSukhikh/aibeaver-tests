# MultiHiertt Mini MCD vs Original

- Created at: `2026-06-05T14:33:43`
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
| openai | mcd_agent | `gpt-5.4` | 7 | 3 | 10 | 10 | 70.0% | 0 | 14 |
| openai | original_agent | `gpt-5.4` | 7 | 3 | 10 | 10 | 70.0% | 0 | 35 |

| Provider | Mode | Input tokens | Output tokens | Total tokens | Total seconds | Avg seconds |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| openai | mcd_agent | 181,009 | 4,513 | 185,522 | 207.8 | 20.8 |
| openai | original_agent | 178,523 | 3,669 | 182,192 | 117.8 | 11.8 |

## openai Matrix

| # | Question ID | mcd_agent | original_agent |
| ---: | --- | --- | --- |
| 1 | `multihiertt_mini_0001` | PASS | PASS |
| 2 | `multihiertt_mini_0002` | FAIL | FAIL |
| 3 | `multihiertt_mini_0003` | PASS | PASS |
| 4 | `multihiertt_mini_0004` | FAIL | FAIL |
| 5 | `multihiertt_mini_0005` | PASS | PASS |
| 6 | `multihiertt_mini_0006` | FAIL | FAIL |
| 7 | `multihiertt_mini_0007` | PASS | PASS |
| 8 | `multihiertt_mini_0008` | PASS | PASS |
| 9 | `multihiertt_mini_0009` | PASS | PASS |
| 10 | `multihiertt_mini_0010` | PASS | PASS |
