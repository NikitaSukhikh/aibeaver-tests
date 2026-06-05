# MultiHiertt Mini MCD vs Original

- Created at: `2026-06-05T15:07:58`
- MCD package: `D:\aibeaver-tests\datasets\multihiertt-mini\multihiertt-mini.mcd`
- Original package: `D:\aibeaver-tests\datasets\multihiertt-mini\original_disconnected`
- Original JSON: `D:\aibeaver-tests\datasets\multihiertt-mini\original_disconnected\dev_50.json`
- Questions: `10` from `D:\aibeaver-tests\datasets\multihiertt-mini\qa_questions_50.jsonl`
- Evaluator labels: `D:\aibeaver-tests\datasets\multihiertt-mini\answers.json`
- Evaluator: shared per-question payload from `answers.json`; both modes use the same evaluator hash.
- Format modes: `mcd` and `original` use one model call per question and no model-visible tools.
- Agent modes: `mcd_agent` uses MCD MCP tools; `original_agent` uses original JSON source-inspection tools.
- Modes: `mcd, original`
- Scoring mode: `llm_judge`

| Provider | Mode | Model | EM | F1 | Passed | Failed | Scored | Total | Pass rate | Errors | Tool calls |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| anthropic | mcd | `claude-opus-4-5` | 0.900 | 0.900 | 9 | 1 | 10 | 10 | 90.0% | 0 | 0 |
| anthropic | original | `claude-opus-4-5` | 0.800 | 0.800 | 8 | 2 | 10 | 10 | 80.0% | 0 | 0 |

| Provider | Mode | Input tokens | Output tokens | Total tokens | Total seconds | Avg seconds |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| anthropic | mcd | 136,631 | 4,622 | 141,253 | 79.5 | 7.9 |
| anthropic | original | 116,795 | 4,503 | 121,298 | 80.7 | 8.1 |

## anthropic Matrix

| # | Question ID | mcd | original |
| ---: | --- | --- | --- |
| 1 | `multihiertt_mini_0001` | PASS | PASS |
| 2 | `multihiertt_mini_0002` | PASS | PASS |
| 3 | `multihiertt_mini_0003` | FAIL | FAIL |
| 4 | `multihiertt_mini_0004` | PASS | PASS |
| 5 | `multihiertt_mini_0005` | PASS | PASS |
| 6 | `multihiertt_mini_0006` | PASS | PASS |
| 7 | `multihiertt_mini_0007` | PASS | FAIL |
| 8 | `multihiertt_mini_0008` | PASS | PASS |
| 9 | `multihiertt_mini_0009` | PASS | PASS |
| 10 | `multihiertt_mini_0010` | PASS | PASS |
