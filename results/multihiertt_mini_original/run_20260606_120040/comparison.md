# MultiHierTT Mini Original Plain Harness

- Created at: `2026-06-06T12:00:40`
- Original package: `D:\aibeaver-tests\datasets\multihiertt-mini\original_disconnected`
- Original JSON: `D:\aibeaver-tests\datasets\multihiertt-mini\original_disconnected\dev_50.json`
- Prebuilt markdown/CSV source: `D:\aibeaver-tests\datasets\multihiertt-mini\original_md_csv`
- Questions: `7` from `D:\aibeaver-tests\datasets\multihiertt-mini\qa_questions_50.jsonl`
- Evaluator labels: `D:\aibeaver-tests\datasets\multihiertt-mini\answers.json`
- Source rule: this evaluator never opens or requires an MCD package.
- `plain_raw` supplies only the selected original record's raw paragraphs and raw HTML tables.
- `plain_chunked` supplies only a raw source.json file with the selected original record's raw paragraphs and raw HTML tables.
- `harness_plain_raw` supplies the full raw main.md text and all raw prebuilt table CSVs.
- `tools_plain_raw` uses the same full raw main.md and CSV corpus, exposed through list/read/search/table/calculator tools without an index.
- Harness excludes `qa` answers, programs, and evidence refs.
- Modes: `plain_raw, tools_plain_raw`
- Scoring mode: `programmatic`

| Provider | Mode | Model | EM | F1 | Passed | Failed | Scored | Total | Scored pass rate | Overall pass rate | Errors | Tool calls |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| openai | plain_raw | `gpt-5.4` | 0.571 | 0.571 | 4 | 3 | 7 | 7 | 57.1% | 57.1% | 0 | 0 |
| openai | tools_plain_raw | `gpt-5.4` | 0.600 | 0.600 | 3 | 2 | 5 | 7 | 60.0% | 42.9% | 2 | 33 |

| Provider | Mode | Input tokens | Output tokens | Total tokens | Total seconds | Avg seconds |
| --- | --- | ---: | ---: | ---: | ---: | ---: |
| openai | plain_raw | 37,600 | 122 | 37,722 | 13.3 | 1.9 |
| openai | tools_plain_raw | 511,514 | 1,531 | 513,045 | 80.8 | 11.5 |

## openai Matrix

| # | Question ID | plain_raw | tools_plain_raw |
| ---: | --- | --- | --- |
| 1 | `multihiertt_mini_0001` | PASS | PASS |
| 2 | `multihiertt_mini_0002` | FAIL | FAIL |
| 3 | `multihiertt_mini_0003` | PASS | PASS |
| 4 | `multihiertt_mini_0004` | PASS | PASS |
| 5 | `multihiertt_mini_0005` | PASS | ERR |
| 6 | `multihiertt_mini_0006` | FAIL | FAIL |
| 7 | `multihiertt_mini_0007` | FAIL | ERR |
