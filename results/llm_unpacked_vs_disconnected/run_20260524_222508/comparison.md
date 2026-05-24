# LLM Unpacked vs Disconnected Comparison

- Created at: `2026-05-24T22:25:08`
- Provider: `openai`
- Model: `gpt-4.1-mini`
- Eval mode: `kb_agent`
- Questions: `D:\aibeaver-tests\datasets\auto-manufacturer-tech-spec\qa_pilot_questions_20.jsonl`
- Connected dataset: `D:\aibeaver-tests\datasets\auto-manufacturer-tech-spec\unpacked`
- Disconnected dataset: `D:\aibeaver-tests\datasets\auto-manufacturer-tech-spec\unpacked_disconnected`

Pass totals: connected `10/20`, disconnected `9/20`.

| Token usage | Input | Output | Total |
| --- | ---: | ---: | ---: |
| Connected data | 159,188 | 3,789 | 162,977 |
| Disconnected data | 146,667 | 5,120 | 151,787 |
| Combined | 305,855 | 8,909 | 314,764 |

| # | Connected data | Disconnected data |
| ---: | :---: | :---: |
| 1 | &#10003; | &#10003; |
| 2 | &#10003; | &#10003; |
| 3 | &#10007; | &#10007; |
| 4 | &#10003; | &#10003; |
| 5 | &#10007; | &#10007; |
| 6 | &#10007; | &#10007; |
| 7 | &#10007; | &#10007; |
| 8 | &#10003; | &#10003; |
| 9 | &#10007; | &#10007; |
| 10 | &#10007; | &#10007; |
| 11 | &#10003; | &#10003; |
| 12 | &#10003; | &#10007; |
| 13 | &#10003; | &#10003; |
| 14 | &#10007; | &#10007; |
| 15 | &#10007; | &#10007; |
| 16 | &#10007; | &#10007; |
| 17 | &#10007; | &#10007; |
| 18 | &#10003; | &#10003; |
| 19 | &#10003; | &#10003; |
| 20 | &#10003; | &#10003; |
