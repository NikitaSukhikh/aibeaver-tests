# LLM Unpacked vs Disconnected Comparison

- Created at: `2026-05-24T23:24:01`
- Provider: `openai`
- Model: `gpt-5.4`
- Eval mode: `kb_agent`
- Questions: `D:\aibeaver-tests\datasets\auto-manufacturer-tech-spec\qa_pilot_questions_20.jsonl`
- Connected dataset: `D:\aibeaver-tests\datasets\auto-manufacturer-tech-spec\unpacked`
- Disconnected dataset: `D:\aibeaver-tests\datasets\auto-manufacturer-tech-spec\unpacked_disconnected`

Pass totals: connected `20/20`, disconnected `20/20`.

| Token usage | Input | Output | Total |
| --- | ---: | ---: | ---: |
| Connected data | 338,160 | 13,191 | 351,351 |
| Disconnected data | 369,354 | 16,471 | 385,825 |
| Combined | 707,514 | 29,662 | 737,176 |

| Timing | Total | Avg per answer |
| --- | ---: | ---: |
| Connected data | 239.4 sec | 12.0 sec |
| Disconnected data | 301.3 sec | 15.1 sec |
| Combined | 540.7 sec | 13.5 sec |

| # | Connected data | Connected time | Disconnected data | Disconnected time |
| ---: | :---: | ---: | :---: | ---: |
| 1 | &#10003; | 6.9 sec | &#10003; | 10.7 sec |
| 2 | &#10003; | 8.5 sec | &#10003; | 11.3 sec |
| 3 | &#10003; | 14.2 sec | &#10003; | 17.5 sec |
| 4 | &#10003; | 11.9 sec | &#10003; | 11.1 sec |
| 5 | &#10003; | 11.5 sec | &#10003; | 17.8 sec |
| 6 | &#10003; | 11.6 sec | &#10003; | 14.9 sec |
| 7 | &#10003; | 9.8 sec | &#10003; | 14.4 sec |
| 8 | &#10003; | 15.2 sec | &#10003; | 15.9 sec |
| 9 | &#10003; | 8.2 sec | &#10003; | 19.7 sec |
| 10 | &#10003; | 12.9 sec | &#10003; | 15.9 sec |
| 11 | &#10003; | 17.6 sec | &#10003; | 16.9 sec |
| 12 | &#10003; | 3.7 sec | &#10003; | 6.3 sec |
| 13 | &#10003; | 10.9 sec | &#10003; | 12.4 sec |
| 14 | &#10003; | 20.9 sec | &#10003; | 19.8 sec |
| 15 | &#10003; | 12.2 sec | &#10003; | 16.0 sec |
| 16 | &#10003; | 16.9 sec | &#10003; | 17.0 sec |
| 17 | &#10003; | 10.0 sec | &#10003; | 15.8 sec |
| 18 | &#10003; | 15.1 sec | &#10003; | 19.3 sec |
| 19 | &#10003; | 15.3 sec | &#10003; | 18.9 sec |
| 20 | &#10003; | 6.1 sec | &#10003; | 9.8 sec |
