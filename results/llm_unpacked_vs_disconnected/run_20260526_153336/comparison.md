# LLM Unpacked vs Disconnected Comparison

- Created at: `2026-05-26T15:33:36`
- Provider: `openai`
- Model: `gpt-5.4`
- Eval mode: `kb_agent`
- Questions: `D:\aibeaver-tests\datasets\auto-manufacturer-tech-spec\qa_pilot_questions_20.jsonl`
- Connected dataset: `D:\aibeaver-tests\datasets\auto-manufacturer-tech-spec\unpacked`
- Disconnected dataset: `D:\aibeaver-tests\datasets\auto-manufacturer-tech-spec\unpacked_disconnected`

Pass totals: connected `20/20`, disconnected `20/20`.

| Token usage | Input | Output | Total |
| --- | ---: | ---: | ---: |
| Connected data | 208,479 | 7,462 | 215,941 |
| Disconnected data | 395,669 | 11,235 | 406,904 |
| Combined | 604,148 | 18,697 | 622,845 |

| Timing | Total | Avg per answer |
| --- | ---: | ---: |
| Connected data | 165.2 sec | 8.3 sec |
| Disconnected data | 271.8 sec | 13.6 sec |
| Combined | 437.0 sec | 10.9 sec |

| Tool calls | Total | Avg per question |
| --- | ---: | ---: |
| Connected data | 30 | 1.50 |
| Disconnected data | 61 | 3.05 |
| Combined | 91 | 2.27 |

| # | Connected data | Connected time | Connected calls | Disconnected data | Disconnected time | Disconnected calls |
| ---: | :---: | ---: | ---: | :---: | ---: | ---: |
| 1 | &#10003; | 4.0 sec | 1 | &#10003; | 4.2 sec | 1 |
| 2 | &#10003; | 3.5 sec | 1 | &#10003; | 4.3 sec | 1 |
| 3 | &#10003; | 7.4 sec | 1 | &#10003; | 15.0 sec | 4 |
| 4 | &#10003; | 6.6 sec | 2 | &#10003; | 15.1 sec | 4 |
| 5 | &#10003; | 5.6 sec | 1 | &#10003; | 6.0 sec | 1 |
| 6 | &#10003; | 5.1 sec | 1 | &#10003; | 8.8 sec | 3 |
| 7 | &#10003; | 7.6 sec | 2 | &#10003; | 11.7 sec | 3 |
| 8 | &#10003; | 9.3 sec | 2 | &#10003; | 14.2 sec | 2 |
| 9 | &#10003; | 5.4 sec | 1 | &#10003; | 18.0 sec | 4 |
| 10 | &#10003; | 6.1 sec | 1 | &#10003; | 14.5 sec | 4 |
| 11 | &#10003; | 5.9 sec | 2 | &#10003; | 21.4 sec | 4 |
| 12 | &#10003; | 3.7 sec | 1 | &#10003; | 9.0 sec | 3 |
| 13 | &#10003; | 6.1 sec | 2 | &#10003; | 10.0 sec | 3 |
| 14 | &#10003; | 15.8 sec | 2 | &#10003; | 24.8 sec | 4 |
| 15 | &#10003; | 26.3 sec | 2 | &#10003; | 13.5 sec | 4 |
| 16 | &#10003; | 10.4 sec | 1 | &#10003; | 15.7 sec | 4 |
| 17 | &#10003; | 10.3 sec | 2 | &#10003; | 10.2 sec | 2 |
| 18 | &#10003; | 10.3 sec | 2 | &#10003; | 20.5 sec | 4 |
| 19 | &#10003; | 10.0 sec | 2 | &#10003; | 24.7 sec | 4 |
| 20 | &#10003; | 5.8 sec | 1 | &#10003; | 10.3 sec | 2 |
