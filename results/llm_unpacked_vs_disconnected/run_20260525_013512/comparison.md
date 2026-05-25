# LLM Unpacked vs Disconnected Comparison

- Created at: `2026-05-25T01:35:12`
- Provider: `openai`
- Model: `gpt-5.4`
- Eval mode: `kb_agent`
- Questions: `D:\aibeaver-tests\datasets\auto-manufacturer-tech-spec\qa_pilot_questions_20.jsonl`
- Connected dataset: `D:\aibeaver-tests\datasets\auto-manufacturer-tech-spec\unpacked`
- Disconnected dataset: `D:\aibeaver-tests\datasets\auto-manufacturer-tech-spec\unpacked_disconnected`

Pass totals: connected `19/20`, disconnected `20/20`.

| Token usage | Input | Output | Total |
| --- | ---: | ---: | ---: |
| Connected data | 213,310 | 9,970 | 223,280 |
| Disconnected data | 329,306 | 15,552 | 344,858 |
| Combined | 542,616 | 25,522 | 568,138 |

| Timing | Total | Avg per answer |
| --- | ---: | ---: |
| Connected data | 163.9 sec | 8.2 sec |
| Disconnected data | 240.2 sec | 12.0 sec |
| Combined | 404.1 sec | 10.1 sec |

| # | Connected data | Connected time | Disconnected data | Disconnected time |
| ---: | :---: | ---: | :---: | ---: |
| 1 | &#10003; | 4.6 sec | &#10003; | 5.3 sec |
| 2 | &#10003; | 7.2 sec | &#10003; | 11.4 sec |
| 3 | &#10003; | 5.9 sec | &#10003; | 6.7 sec |
| 4 | &#10003; | 7.5 sec | &#10003; | 7.7 sec |
| 5 | &#10003; | 6.9 sec | &#10003; | 5.5 sec |
| 6 | &#10003; | 7.3 sec | &#10003; | 6.3 sec |
| 7 | &#10003; | 6.1 sec | &#10003; | 11.2 sec |
| 8 | &#10003; | 10.5 sec | &#10003; | 13.7 sec |
| 9 | &#10003; | 6.3 sec | &#10003; | 17.8 sec |
| 10 | &#10003; | 5.8 sec | &#10003; | 19.4 sec |
| 11 | &#10003; | 8.0 sec | &#10003; | 6.4 sec |
| 12 | &#10003; | 8.7 sec | &#10003; | 7.0 sec |
| 13 | &#10003; | 4.1 sec | &#10003; | 9.9 sec |
| 14 | &#10007; | 17.5 sec | &#10003; | 24.7 sec |
| 15 | &#10003; | 11.8 sec | &#10003; | 15.3 sec |
| 16 | &#10003; | 17.8 sec | &#10003; | 22.2 sec |
| 17 | &#10003; | 8.9 sec | &#10003; | 11.1 sec |
| 18 | &#10003; | 6.5 sec | &#10003; | 16.0 sec |
| 19 | &#10003; | 6.7 sec | &#10003; | 16.7 sec |
| 20 | &#10003; | 5.8 sec | &#10003; | 6.1 sec |
