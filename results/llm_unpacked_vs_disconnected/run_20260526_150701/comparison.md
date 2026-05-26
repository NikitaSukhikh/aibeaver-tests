# LLM Unpacked vs Disconnected Comparison

- Created at: `2026-05-26T15:07:01`
- Provider: `openai`
- Model: `gpt-5.4`
- Eval mode: `kb_agent`
- Questions: `D:\aibeaver-tests\datasets\auto-manufacturer-tech-spec\qa_pilot_questions_20.jsonl`
- Connected dataset: `D:\aibeaver-tests\datasets\auto-manufacturer-tech-spec\unpacked`
- Disconnected dataset: `D:\aibeaver-tests\datasets\auto-manufacturer-tech-spec\unpacked_disconnected`

Pass totals: connected `18/20`, disconnected `16/20`.

| Token usage | Input | Output | Total |
| --- | ---: | ---: | ---: |
| Connected data | 149,161 | 9,200 | 158,361 |
| Disconnected data | 242,160 | 19,477 | 261,637 |
| Combined | 391,321 | 28,677 | 419,998 |

| Timing | Total | Avg per answer |
| --- | ---: | ---: |
| Connected data | 191.6 sec | 9.6 sec |
| Disconnected data | 407.3 sec | 20.4 sec |
| Combined | 599.0 sec | 15.0 sec |

| Tool calls | Total | Avg per question |
| --- | ---: | ---: |
| Connected data | 34 | 1.70 |
| Disconnected data | 103 | 5.15 |
| Combined | 137 | 3.42 |

| # | Connected data | Connected time | Connected calls | Disconnected data | Disconnected time | Disconnected calls |
| ---: | :---: | ---: | ---: | :---: | ---: | ---: |
| 1 | &#10003; | 5.6 sec | 1 | &#10003; | 7.1 sec | 1 |
| 2 | &#10003; | 5.2 sec | 1 | &#10003; | 8.4 sec | 2 |
| 3 | &#10003; | 5.6 sec | 1 | &#10003; | 15.4 sec | 2 |
| 4 | &#10003; | 6.3 sec | 2 | &#10003; | 10.3 sec | 2 |
| 5 | &#10003; | 7.0 sec | 1 | &#10003; | 10.3 sec | 2 |
| 6 | &#10003; | 8.4 sec | 2 | &#10007; | 67.7 sec | 20 |
| 7 | &#10003; | 21.2 sec | 1 | &#10007; | 59.8 sec | 20 |
| 8 | &#10003; | 12.1 sec | 2 | &#10003; | 29.2 sec | 8 |
| 9 | &#10003; | 4.6 sec | 1 | &#10003; | 10.3 sec | 1 |
| 10 | &#10003; | 10.2 sec | 2 | &#10003; | 8.0 sec | 2 |
| 11 | &#10003; | 8.3 sec | 2 | &#10003; | 8.5 sec | 2 |
| 12 | &#10007; | 10.3 sec | 2 | &#10003; | 12.5 sec | 3 |
| 13 | &#10003; | 8.4 sec | 2 | &#10003; | 11.0 sec | 3 |
| 14 | &#10003; | 10.3 sec | 2 | &#10003; | 33.0 sec | 5 |
| 15 | &#10003; | 18.9 sec | 2 | &#10007; | 67.7 sec | 20 |
| 16 | &#10003; | 14.6 sec | 2 | &#10003; | 7.2 sec | 2 |
| 17 | &#10007; | 6.1 sec | 2 | &#10007; | 10.1 sec | 2 |
| 18 | &#10003; | 12.9 sec | 2 | &#10003; | 15.1 sec | 2 |
| 19 | &#10003; | 9.6 sec | 2 | &#10003; | 8.6 sec | 2 |
| 20 | &#10003; | 6.2 sec | 2 | &#10003; | 7.2 sec | 2 |
