# LLM Unpacked vs Disconnected Comparison

- Created at: `2026-05-26T10:42:43`
- Provider: `openai`
- Model: `gpt-5.4`
- Eval mode: `kb_agent`
- Questions: `D:\aibeaver-tests\datasets\auto-manufacturer-tech-spec\qa_pilot_questions_20.jsonl`
- Connected dataset: `D:\aibeaver-tests\datasets\auto-manufacturer-tech-spec\unpacked`
- Disconnected dataset: `D:\aibeaver-tests\datasets\auto-manufacturer-tech-spec\unpacked_disconnected`

Pass totals: connected `20/20`, disconnected `20/20`.

| Token usage | Input | Output | Total |
| --- | ---: | ---: | ---: |
| Connected data | 244,900 | 9,660 | 254,560 |
| Disconnected data | 343,920 | 15,008 | 358,928 |
| Combined | 588,820 | 24,668 | 613,488 |

| Timing | Total | Avg per answer |
| --- | ---: | ---: |
| Connected data | 193.2 sec | 9.7 sec |
| Disconnected data | 296.0 sec | 14.8 sec |
| Combined | 489.1 sec | 12.2 sec |

| Tool calls | Total | Avg per question |
| --- | ---: | ---: |
| Connected data | 33 | 1.65 |
| Disconnected data | 57 | 2.85 |
| Combined | 90 | 2.25 |

| # | Connected data | Connected time | Connected calls | Disconnected data | Disconnected time | Disconnected calls |
| ---: | :---: | ---: | ---: | :---: | ---: | ---: |
| 1 | &#10003; | 5.5 sec | 1 | &#10003; | 26.5 sec | 1 |
| 2 | &#10003; | 8.0 sec | 1 | &#10003; | 12.0 sec | 3 |
| 3 | &#10003; | 5.7 sec | 1 | &#10003; | 20.7 sec | 4 |
| 4 | &#10003; | 8.4 sec | 2 | &#10003; | 8.6 sec | 2 |
| 5 | &#10003; | 10.7 sec | 1 | &#10003; | 6.2 sec | 1 |
| 6 | &#10003; | 12.6 sec | 1 | &#10003; | 18.9 sec | 3 |
| 7 | &#10003; | 5.0 sec | 1 | &#10003; | 10.9 sec | 3 |
| 8 | &#10003; | 11.1 sec | 2 | &#10003; | 19.9 sec | 4 |
| 9 | &#10003; | 4.6 sec | 1 | &#10003; | 6.2 sec | 1 |
| 10 | &#10003; | 5.0 sec | 1 | &#10003; | 18.8 sec | 4 |
| 11 | &#10003; | 10.4 sec | 2 | &#10003; | 16.6 sec | 4 |
| 12 | &#10003; | 8.5 sec | 2 | &#10003; | 10.5 sec | 3 |
| 13 | &#10003; | 9.4 sec | 2 | &#10003; | 11.4 sec | 3 |
| 14 | &#10003; | 27.4 sec | 3 | &#10003; | 20.6 sec | 3 |
| 15 | &#10003; | 15.9 sec | 2 | &#10003; | 16.6 sec | 4 |
| 16 | &#10003; | 10.3 sec | 2 | &#10003; | 25.4 sec | 4 |
| 17 | &#10003; | 9.2 sec | 2 | &#10003; | 10.3 sec | 2 |
| 18 | &#10003; | 9.5 sec | 2 | &#10003; | 10.4 sec | 2 |
| 19 | &#10003; | 9.2 sec | 2 | &#10003; | 17.3 sec | 4 |
| 20 | &#10003; | 6.7 sec | 2 | &#10003; | 8.1 sec | 2 |
