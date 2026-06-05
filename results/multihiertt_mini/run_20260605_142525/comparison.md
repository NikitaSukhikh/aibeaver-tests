# MultiHiertt Mini MCD vs Original

- Created at: `2026-06-05T14:25:25`
- MCD package: `D:\aibeaver-tests\datasets\multihiertt-mini\multihiertt-mini.mcd`
- Original package: `D:\aibeaver-tests\datasets\multihiertt-mini\original_disconnected`
- Original JSON: `D:\aibeaver-tests\datasets\multihiertt-mini\original_disconnected\dev_50.json`
- Questions: `1` from `D:\aibeaver-tests\datasets\multihiertt-mini\qa_questions_50.jsonl`
- Evaluator labels: `D:\aibeaver-tests\datasets\multihiertt-mini\answers.json`
- Evaluator: shared per-question payload from `answers.json`; both modes use the same evaluator hash.
- Format modes: `mcd` and `original` use one model call per question and no model-visible tools.
- Agent modes: `mcd_agent` uses MCD MCP tools; `original_agent` uses original JSON source-inspection tools.
- Modes: `original_agent`
- Scoring mode: `llm_judge`

| Provider | Mode | Model | Passed | Failed | Scored | Total | Pass rate | Errors | Tool calls |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| openai | original_agent | `gpt-5.4` | 1 | 0 | 1 | 1 | 100.0% | 0 | 3 |

| Provider | Mode | Input tokens | Output tokens | Total tokens | Total seconds | Avg seconds |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| openai | original_agent | 6,276 | 225 | 6,501 | 7.1 | 7.1 |

## openai Matrix

| # | Question ID | original_agent |
| ---: | --- | --- |
| 1 | `multihiertt_mini_0001` | PASS |
