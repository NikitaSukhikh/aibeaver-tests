# MultiHierTT Mini Original Plain Harness

- Created at: `2026-06-06T02:01:47`
- Original package: `D:\aibeaver-tests\datasets\multihiertt-mini\original_disconnected`
- Original JSON: `D:\aibeaver-tests\datasets\multihiertt-mini\original_disconnected\dev_50.json`
- Questions: `7` from `D:\aibeaver-tests\datasets\multihiertt-mini\qa_questions_50.jsonl`
- Evaluator labels: `D:\aibeaver-tests\datasets\multihiertt-mini\answers.json`
- Source rule: this evaluator never opens or requires an MCD package.
- `plain_source` supplies the sanitized original JSON record only.
- `harnessed_plain` supplies compact neutral metadata only: table profiles, keyword locations, tool manifest, and a guide.
- `harnessed_tools` exposes compact metadata plus targeted paragraph/table/cell-description/calculator tools.
- Harness excludes `qa` answers, programs, and evidence refs.
- Modes: `plain_source, harnessed_plain, harnessed_tools`
- Scoring mode: `llm_judge`

| Provider | Mode | Model | EM | F1 | Passed | Failed | Scored | Total | Pass rate | Errors | Tool calls |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| openai | plain_source | `gpt-5.4` | 0.714 | 0.714 | 5 | 2 | 7 | 7 | 71.4% | 0 | 0 |
| openai | harnessed_plain | `gpt-5.4` | 0.000 | 0.000 | 0 | 7 | 7 | 7 | 0.0% | 0 | 0 |
| openai | harnessed_tools | `gpt-5.4` | 0.857 | 0.857 | 6 | 1 | 7 | 7 | 85.7% | 0 | 23 |
| anthropic | plain_source | `claude-opus-4-5` | 0.857 | 0.857 | 6 | 1 | 7 | 7 | 85.7% | 0 | 0 |
| anthropic | harnessed_plain | `claude-opus-4-5` | 0.143 | 0.143 | 1 | 6 | 7 | 7 | 14.3% | 0 | 0 |
| anthropic | harnessed_tools | `claude-opus-4-5` | 0.833 | 0.833 | 5 | 1 | 6 | 7 | 83.3% | 1 | 54 |

| Provider | Mode | Input tokens | Output tokens | Total tokens | Total seconds | Avg seconds |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| openai | plain_source | 73,841 | 824 | 74,665 | 8.6 | 1.2 |
| openai | harnessed_plain | 93,214 | 898 | 94,112 | 12.7 | 1.8 |
| openai | harnessed_tools | 191,809 | 2,088 | 193,897 | 188.1 | 26.9 |
| anthropic | plain_source | 83,359 | 3,621 | 86,980 | 57.2 | 8.2 |
| anthropic | harnessed_plain | 114,796 | 6,790 | 121,586 | 130.7 | 18.7 |
| anthropic | harnessed_tools | 528,222 | 4,307 | 532,529 | 158.6 | 22.7 |

## anthropic Matrix

| # | Question ID | plain_source | harnessed_plain | harnessed_tools |
| ---: | --- | --- | --- | --- |
| 1 | `multihiertt_mini_0001` | PASS | FAIL | PASS |
| 2 | `multihiertt_mini_0002` | PASS | FAIL | FAIL |
| 3 | `multihiertt_mini_0003` | FAIL | FAIL | PASS |
| 4 | `multihiertt_mini_0004` | PASS | FAIL | PASS |
| 5 | `multihiertt_mini_0005` | PASS | FAIL | PASS |
| 6 | `multihiertt_mini_0006` | PASS | PASS | ERR |
| 7 | `multihiertt_mini_0007` | PASS | FAIL | PASS |

## openai Matrix

| # | Question ID | plain_source | harnessed_plain | harnessed_tools |
| ---: | --- | --- | --- | --- |
| 1 | `multihiertt_mini_0001` | PASS | FAIL | PASS |
| 2 | `multihiertt_mini_0002` | FAIL | FAIL | PASS |
| 3 | `multihiertt_mini_0003` | PASS | FAIL | PASS |
| 4 | `multihiertt_mini_0004` | PASS | FAIL | PASS |
| 5 | `multihiertt_mini_0005` | PASS | FAIL | PASS |
| 6 | `multihiertt_mini_0006` | FAIL | FAIL | FAIL |
| 7 | `multihiertt_mini_0007` | PASS | FAIL | PASS |
