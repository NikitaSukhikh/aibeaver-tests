# LLM Unpacked vs Disconnected Comparison

- Created at: `2026-05-26T15:30:46`
- Provider: `openai`
- Model: `gpt-5.4`
- Eval mode: `kb_agent`
- Questions: `D:\aibeaver-tests\datasets\auto-manufacturer-tech-spec\qa_pilot_questions_20.jsonl`
- Connected dataset: `D:\aibeaver-tests\datasets\auto-manufacturer-tech-spec\unpacked`
- Disconnected dataset: `D:\aibeaver-tests\datasets\auto-manufacturer-tech-spec\unpacked_disconnected`

Pass totals: connected `5/5`, disconnected `5/5`.

| Token usage | Input | Output | Total |
| --- | ---: | ---: | ---: |
| Connected data | 39,293 | 1,234 | 40,527 |
| Disconnected data | 50,615 | 2,055 | 52,670 |
| Combined | 89,908 | 3,289 | 93,197 |

| Timing | Total | Avg per answer |
| --- | ---: | ---: |
| Connected data | 27.8 sec | 5.6 sec |
| Disconnected data | 53.4 sec | 10.7 sec |
| Combined | 81.1 sec | 8.1 sec |

| Tool calls | Total | Avg per question |
| --- | ---: | ---: |
| Connected data | 6 | 1.20 |
| Disconnected data | 8 | 1.60 |
| Combined | 14 | 1.40 |

| # | Connected data | Connected time | Connected calls | Disconnected data | Disconnected time | Disconnected calls |
| ---: | :---: | ---: | ---: | :---: | ---: | ---: |
| 1 | &#10003; | 5.4 sec | 1 | &#10003; | 4.6 sec | 1 |
| 2 | &#10003; | 3.8 sec | 1 | &#10003; | 4.5 sec | 1 |
| 3 | &#10003; | 5.4 sec | 1 | &#10003; | 6.6 sec | 1 |
| 4 | &#10003; | 7.8 sec | 2 | &#10003; | 31.2 sec | 4 |
| 5 | &#10003; | 5.4 sec | 1 | &#10003; | 6.4 sec | 1 |
