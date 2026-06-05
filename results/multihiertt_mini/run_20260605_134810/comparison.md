# MultiHiertt Mini MCD vs Original

- Created at: `2026-06-05T13:48:10`
- MCD package: `D:\aibeaver-tests\datasets\multihiertt-mini\multihiertt-mini.mcd`
- Original package: `D:\aibeaver-tests\datasets\multihiertt-mini\original_disconnected`
- Original JSON: `D:\aibeaver-tests\datasets\multihiertt-mini\original_disconnected\dev_50.json`
- Questions: `10` from `D:\aibeaver-tests\datasets\multihiertt-mini\qa_questions_50.jsonl`
- Evaluator labels: `D:\aibeaver-tests\datasets\multihiertt-mini\answers.json`
- Evaluator: shared per-question payload from `answers.json`; both modes use the same evaluator hash.
- Modes: `mcd, original`
- Scoring mode: `llm_judge`

| Provider | Mode | Model | Passed | Failed | Scored | Total | Pass rate | Errors | Tool calls |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| openai | mcd | `gpt-5.4` | 7 | 3 | 10 | 10 | 70.0% | 0 | 14 |
| openai | original | `gpt-5.4` | 4 | 6 | 10 | 10 | 40.0% | 0 | 0 |

| Provider | Mode | Input tokens | Output tokens | Total tokens | Total seconds | Avg seconds |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| openai | mcd | 211,894 | 4,568 | 216,462 | 207.8 | 20.8 |
| openai | original | 101,136 | 1,200 | 102,336 | 11.9 | 1.2 |

## openai Matrix

| # | Question ID | mcd | original |
| ---: | --- | --- | --- |
| 1 | `multihiertt_mini_0001` | PASS | PASS |
| 2 | `multihiertt_mini_0002` | FAIL | FAIL |
| 3 | `multihiertt_mini_0003` | PASS | PASS |
| 4 | `multihiertt_mini_0004` | FAIL | FAIL |
| 5 | `multihiertt_mini_0005` | PASS | FAIL |
| 6 | `multihiertt_mini_0006` | FAIL | FAIL |
| 7 | `multihiertt_mini_0007` | PASS | FAIL |
| 8 | `multihiertt_mini_0008` | PASS | PASS |
| 9 | `multihiertt_mini_0009` | PASS | FAIL |
| 10 | `multihiertt_mini_0010` | PASS | PASS |
