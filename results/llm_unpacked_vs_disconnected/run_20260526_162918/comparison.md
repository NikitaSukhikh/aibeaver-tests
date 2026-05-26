# LLM Unpacked vs Disconnected Comparison

- Created at: `2026-05-26T16:29:18`
- Provider: `openai`
- Model: `gpt-5.4-mini`
- Eval mode: `kb_agent`
- Questions: `D:\aibeaver-tests\datasets\auto-manufacturer-tech-spec\qa_pilot_questions_20.jsonl`
- Connected dataset: `D:\aibeaver-tests\datasets\auto-manufacturer-tech-spec\unpacked`
- Disconnected dataset: `D:\aibeaver-tests\datasets\auto-manufacturer-tech-spec\unpacked_disconnected`

Pass totals: connected `16/20`, disconnected `12/20`.

| Token usage | Input | Output | Total |
| --- | ---: | ---: | ---: |
| Connected data | 459,897 | 10,404 | 470,301 |
| Disconnected data | 655,537 | 14,591 | 670,128 |
| Combined | 1,115,434 | 24,995 | 1,140,429 |

| Timing | Total | Avg per answer |
| --- | ---: | ---: |
| Connected data | 163.1 sec | 8.2 sec |
| Disconnected data | 229.9 sec | 11.5 sec |
| Combined | 392.9 sec | 9.8 sec |

| Tool calls | Total | Avg per question |
| --- | ---: | ---: |
| Connected data | 51 | 2.55 |
| Disconnected data | 75 | 3.75 |
| Combined | 126 | 3.15 |

| # | Connected data | Connected time | Connected calls | Disconnected data | Disconnected time | Disconnected calls |
| ---: | :---: | ---: | ---: | :---: | ---: | ---: |
| 1 | &#10003; | 3.4 sec | 1 | &#10003; | 3.9 sec | 1 |
| 2 | &#10003; | 3.4 sec | 1 | &#10007; | 6.1 sec | 3 |
| 3 | &#10003; | 3.2 sec | 1 | &#10003; | 3.1 sec | 1 |
| 4 | &#10003; | 4.3 sec | 1 | &#10003; | 4.7 sec | 2 |
| 5 | &#10003; | 7.6 sec | 1 | &#10003; | 6.1 sec | 3 |
| 6 | &#10003; | 3.6 sec | 1 | &#10007; | 12.8 sec | 4 |
| 7 | &#10003; | 4.1 sec | 1 | &#10003; | 7.0 sec | 3 |
| 8 | &#10003; | 7.0 sec | 3 | &#10003; | 16.1 sec | 4 |
| 9 | &#10003; | 3.3 sec | 1 | &#10003; | 6.5 sec | 3 |
| 10 | &#10003; | 4.4 sec | 1 | &#10007; | 6.2 sec | 3 |
| 11 | &#10003; | 5.4 sec | 2 | &#10003; | 12.7 sec | 3 |
| 12 | &#10003; | 6.2 sec | 2 | &#10003; | 6.4 sec | 3 |
| 13 | &#10003; | 4.6 sec | 2 | &#10003; | 6.1 sec | 3 |
| 14 | &#10007; | 8.2 sec | 3 | &#10007; | 19.9 sec | 3 |
| 15 | &#10007; | 50.5 sec | 20 | &#10003; | 9.2 sec | 4 |
| 16 | &#10003; | 9.2 sec | 2 | &#10007; | 6.1 sec | 3 |
| 17 | &#10007; | 13.8 sec | 2 | &#10007; | 4.5 sec | 2 |
| 18 | &#10003; | 10.9 sec | 2 | &#10007; | 78.4 sec | 20 |
| 19 | &#10007; | 3.9 sec | 2 | &#10007; | 8.3 sec | 4 |
| 20 | &#10003; | 6.0 sec | 2 | &#10003; | 5.7 sec | 3 |
