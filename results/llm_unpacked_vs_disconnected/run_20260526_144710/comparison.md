# LLM Unpacked vs Disconnected Comparison

- Created at: `2026-05-26T14:47:10`
- Provider: `openai`
- Model: `gpt-5.4`
- Eval mode: `kb_agent`
- Questions: `D:\aibeaver-tests\datasets\auto-manufacturer-tech-spec\qa_pilot_questions_20.jsonl`
- Connected dataset: `D:\aibeaver-tests\datasets\auto-manufacturer-tech-spec\unpacked`
- Disconnected dataset: `D:\aibeaver-tests\datasets\auto-manufacturer-tech-spec\unpacked_disconnected`

Pass totals: connected `19/20`, disconnected `10/20`.

| Token usage | Input | Output | Total |
| --- | ---: | ---: | ---: |
| Connected data | 120,222 | 10,083 | 130,305 |
| Disconnected data | 136,640 | 23,059 | 159,699 |
| Combined | 256,862 | 33,142 | 290,004 |

| Timing | Total | Avg per answer |
| --- | ---: | ---: |
| Connected data | 203.0 sec | 10.2 sec |
| Disconnected data | 454.9 sec | 22.7 sec |
| Combined | 657.9 sec | 16.4 sec |

| Tool calls | Total | Avg per question |
| --- | ---: | ---: |
| Connected data | 32 | 1.60 |
| Disconnected data | 93 | 4.65 |
| Combined | 125 | 3.12 |

| # | Connected data | Connected time | Connected calls | Disconnected data | Disconnected time | Disconnected calls |
| ---: | :---: | ---: | ---: | :---: | ---: | ---: |
| 1 | &#10003; | 8.2 sec | 1 | &#10003; | 4.2 sec | 1 |
| 2 | &#10003; | 8.9 sec | 1 | &#10003; | 22.5 sec | 2 |
| 3 | &#10003; | 7.6 sec | 1 | &#10007; | 33.3 sec | 8 |
| 4 | &#10003; | 7.2 sec | 2 | &#10003; | 9.1 sec | 2 |
| 5 | &#10003; | 6.3 sec | 1 | &#10003; | 6.3 sec | 1 |
| 6 | &#10003; | 8.5 sec | 1 | &#10007; | 26.2 sec | 8 |
| 7 | &#10003; | 10.3 sec | 2 | &#10007; | 34.1 sec | 8 |
| 8 | &#10003; | 9.8 sec | 2 | &#10007; | 29.7 sec | 8 |
| 9 | &#10003; | 4.6 sec | 1 | &#10003; | 8.6 sec | 1 |
| 10 | &#10003; | 5.8 sec | 1 | &#10007; | 47.1 sec | 8 |
| 11 | &#10003; | 7.1 sec | 2 | &#10007; | 23.9 sec | 8 |
| 12 | &#10003; | 4.6 sec | 1 | &#10007; | 10.3 sec | 2 |
| 13 | &#10003; | 8.0 sec | 2 | &#10003; | 8.5 sec | 2 |
| 14 | &#10003; | 22.5 sec | 2 | &#10007; | 43.9 sec | 8 |
| 15 | &#10003; | 22.3 sec | 2 | &#10007; | 46.4 sec | 8 |
| 16 | &#10003; | 15.3 sec | 2 | &#10003; | 16.2 sec | 3 |
| 17 | &#10007; | 7.1 sec | 2 | &#10007; | 30.9 sec | 8 |
| 18 | &#10003; | 21.3 sec | 2 | &#10003; | 10.8 sec | 2 |
| 19 | &#10003; | 13.1 sec | 2 | &#10003; | 33.5 sec | 3 |
| 20 | &#10003; | 4.6 sec | 2 | &#10003; | 9.4 sec | 2 |
