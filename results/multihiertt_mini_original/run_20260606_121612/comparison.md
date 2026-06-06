# MultiHierTT Mini Original Plain Harness

- Created at: `2026-06-06T12:16:12`
- Original package: `D:\aibeaver-tests\datasets\multihiertt-mini\original_disconnected`
- Original JSON: `D:\aibeaver-tests\datasets\multihiertt-mini\original_disconnected\dev_50.json`
- Prebuilt markdown/CSV source: `D:\aibeaver-tests\datasets\multihiertt-mini\original_md_csv`
- Questions: `7` from `D:\aibeaver-tests\datasets\multihiertt-mini\qa_questions_50.jsonl`
- Evaluator labels: `D:\aibeaver-tests\datasets\multihiertt-mini\answers.json`
- Source rule: this evaluator never opens or requires an MCD package.
- `plain_raw` supplies the full original raw JSON corpus after removing each record's `qa` block.
- `plain_chunked` supplies only a raw source.json file with the selected original record's raw paragraphs and raw HTML tables.
- `harness_plain_raw` supplies the full raw main.md text and all raw prebuilt table CSVs.
- `tools_plain_raw` uses the same full raw main.md and CSV corpus, exposed through list/read/search/table/calculator tools without an index.
- Harness excludes `qa` answers, programs, and evidence refs.
- Modes: `plain_raw`
- Scoring mode: `programmatic`

| Provider | Mode | Model | EM | F1 | Passed | Failed | Scored | Total | Scored pass rate | Overall pass rate | Errors | Tool calls |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| openai | plain_raw | `gpt-5.4` | 0.143 | 0.143 | 1 | 6 | 7 | 7 | 14.3% | 14.3% | 0 | 0 |

| Provider | Mode | Input tokens | Output tokens | Total tokens | Total seconds | Avg seconds |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| openai | plain_raw | 3,069,946 | 118 | 3,070,064 | 85.4 | 12.2 |

## openai Matrix

| # | Question ID | plain_raw |
| ---: | --- | --- |
| 1 | `multihiertt_mini_0001` | PASS |
| 2 | `multihiertt_mini_0002` | FAIL |
| 3 | `multihiertt_mini_0003` | FAIL |
| 4 | `multihiertt_mini_0004` | FAIL |
| 5 | `multihiertt_mini_0005` | FAIL |
| 6 | `multihiertt_mini_0006` | FAIL |
| 7 | `multihiertt_mini_0007` | FAIL |
