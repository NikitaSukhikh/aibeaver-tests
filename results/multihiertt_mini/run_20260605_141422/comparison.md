# MultiHiertt Mini MCD-Extracted vs Original

- Created at: `2026-06-05T14:14:22`
- MCD package: `D:\aibeaver-tests\datasets\multihiertt-mini\multihiertt-mini.mcd`
- Original package: `D:\aibeaver-tests\datasets\multihiertt-mini\original_disconnected`
- Original JSON: `D:\aibeaver-tests\datasets\multihiertt-mini\original_disconnected\dev_50.json`
- Questions: `10` from `D:\aibeaver-tests\datasets\multihiertt-mini\qa_questions_50.jsonl`
- Evaluator labels: `D:\aibeaver-tests\datasets\multihiertt-mini\answers.json`
- Evaluator: shared per-question payload from `answers.json`; both modes use the same evaluator hash.
- Model orchestration: one model call per question in both modes; no model-visible tools in either mode.
- MCD mode: source payload is deterministically extracted from MCD tables before the model call.
- Modes: `mcd, original`
- Scoring mode: `llm_judge`

| Provider | Mode | Model | Passed | Failed | Scored | Total | Pass rate | Errors | Tool calls |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| anthropic | mcd | `claude-opus-4-5` | 9 | 1 | 10 | 10 | 90.0% | 0 | 0 |
| anthropic | original | `claude-opus-4-5` | 9 | 1 | 10 | 10 | 90.0% | 0 | 0 |

| Provider | Mode | Input tokens | Output tokens | Total tokens | Total seconds | Avg seconds |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| anthropic | mcd | 344,225 | 3,465 | 347,690 | 61.8 | 6.2 |
| anthropic | original | 116,299 | 4,335 | 120,634 | 66.7 | 6.7 |

## anthropic Matrix

| # | Question ID | mcd | original |
| ---: | --- | --- | --- |
| 1 | `multihiertt_mini_0001` | PASS | PASS |
| 2 | `multihiertt_mini_0002` | PASS | PASS |
| 3 | `multihiertt_mini_0003` | FAIL | FAIL |
| 4 | `multihiertt_mini_0004` | PASS | PASS |
| 5 | `multihiertt_mini_0005` | PASS | PASS |
| 6 | `multihiertt_mini_0006` | PASS | PASS |
| 7 | `multihiertt_mini_0007` | PASS | PASS |
| 8 | `multihiertt_mini_0008` | PASS | PASS |
| 9 | `multihiertt_mini_0009` | PASS | PASS |
| 10 | `multihiertt_mini_0010` | PASS | PASS |
