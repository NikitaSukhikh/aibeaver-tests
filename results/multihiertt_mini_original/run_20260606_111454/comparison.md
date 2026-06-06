# MultiHierTT Mini Original Plain Harness

- Created at: `2026-06-06T11:14:54`
- Original package: `D:\aibeaver-tests\datasets\multihiertt-mini\original_disconnected`
- Original JSON: `D:\aibeaver-tests\datasets\multihiertt-mini\original_disconnected\dev_50.json`
- Prebuilt markdown/CSV source: `D:\aibeaver-tests\datasets\multihiertt-mini\original_md_csv`
- Questions: `7` from `D:\aibeaver-tests\datasets\multihiertt-mini\qa_questions_50.jsonl`
- Evaluator labels: `D:\aibeaver-tests\datasets\multihiertt-mini\answers.json`
- Source rule: this evaluator never opens or requires an MCD package.
- `plain_source` supplies only the selected original record's raw paragraphs and raw HTML tables.
- `harnessed_plain` supplies only the full raw main.md file and all raw prebuilt table CSVs.
- `harnessed_tools` uses the same raw main.md and CSV corpus, exposed through read/search/table/calculator tools without an index.
- Harness excludes `qa` answers, programs, and evidence refs.
- Modes: `plain_source, harnessed_plain, harnessed_tools`
- Scoring mode: `llm_judge`

| Provider | Mode | Model | EM | F1 | Passed | Failed | Scored | Total | Pass rate | Errors | Tool calls |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| openai | plain_source | `gpt-5.4` | 0.857 | 0.857 | 6 | 1 | 7 | 7 | 85.7% | 0 | 0 |
| openai | harnessed_plain | `gpt-5.4` | 0.571 | 0.571 | 4 | 3 | 7 | 7 | 57.1% | 0 | 0 |
| openai | harnessed_tools | `gpt-5.4` | 0.667 | 0.667 | 4 | 2 | 6 | 7 | 66.7% | 1 | 73 |
| anthropic | plain_source | `claude-opus-4-5` | 0.857 | 0.857 | 6 | 1 | 7 | 7 | 85.7% | 0 | 0 |
| anthropic | harnessed_plain | `claude-opus-4-5` | 0.000 | 0.000 | 0 | 0 | 0 | 7 | 0.0% | 7 | 0 |
| anthropic | harnessed_tools | `claude-opus-4-5` | 0.857 | 0.857 | 6 | 1 | 7 | 7 | 85.7% | 0 | 68 |

| Provider | Mode | Input tokens | Output tokens | Total tokens | Total seconds | Avg seconds |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| openai | plain_source | 40,542 | 735 | 41,277 | 14.3 | 2.0 |
| openai | harnessed_plain | 1,249,835 | 753 | 1,250,588 | 40.6 | 5.8 |
| openai | harnessed_tools | 650,202 | 6,780 | 656,982 | 183.7 | 26.2 |
| anthropic | plain_source | 44,751 | 3,272 | 48,023 | 47.1 | 6.7 |
| anthropic | harnessed_plain | 0 | 0 | 0 | 41.4 | 5.9 |
| anthropic | harnessed_tools | 376,639 | 4,083 | 380,722 | 147.8 | 21.1 |

## anthropic Matrix

| # | Question ID | plain_source | harnessed_plain | harnessed_tools |
| ---: | --- | --- | --- | --- |
| 1 | `multihiertt_mini_0001` | PASS | ERR | PASS |
| 2 | `multihiertt_mini_0002` | FAIL | ERR | PASS |
| 3 | `multihiertt_mini_0003` | PASS | ERR | FAIL |
| 4 | `multihiertt_mini_0004` | PASS | ERR | PASS |
| 5 | `multihiertt_mini_0005` | PASS | ERR | PASS |
| 6 | `multihiertt_mini_0006` | PASS | ERR | PASS |
| 7 | `multihiertt_mini_0007` | PASS | ERR | PASS |

## openai Matrix

| # | Question ID | plain_source | harnessed_plain | harnessed_tools |
| ---: | --- | --- | --- | --- |
| 1 | `multihiertt_mini_0001` | PASS | PASS | PASS |
| 2 | `multihiertt_mini_0002` | PASS | FAIL | FAIL |
| 3 | `multihiertt_mini_0003` | PASS | PASS | PASS |
| 4 | `multihiertt_mini_0004` | PASS | PASS | PASS |
| 5 | `multihiertt_mini_0005` | PASS | FAIL | PASS |
| 6 | `multihiertt_mini_0006` | FAIL | FAIL | FAIL |
| 7 | `multihiertt_mini_0007` | PASS | PASS | ERR |
