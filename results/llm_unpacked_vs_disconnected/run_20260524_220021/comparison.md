# LLM Unpacked vs Disconnected Comparison

- Created at: `2026-05-24T22:00:21`
- Provider: `openai`
- Model: `gpt-4.1-mini`
- Eval mode: `kb_agent`
- Questions: `D:\aibeaver-tests\datasets\auto-manufacturer-tech-spec\qa_pilot_questions_20.jsonl`
- Connected dataset: `D:\aibeaver-tests\datasets\auto-manufacturer-tech-spec\unpacked`
- Disconnected dataset: `D:\aibeaver-tests\datasets\auto-manufacturer-tech-spec\unpacked_disconnected`

Pass totals: connected `8/20`, disconnected `7/20`.

| Token usage | Input | Output | Total |
| --- | ---: | ---: | ---: |
| Connected data | 380,591 | 5,140 | 385,731 |
| Disconnected data | 345,434 | 7,191 | 352,625 |
| Combined | 726,025 | 12,331 | 738,356 |

| # | Connected data | Disconnected data |
| ---: | :---: | :---: |
| 1 | &#10003; | &#10003; |
| 2 | &#10003; | &#10003; |
| 3 | &#10007; | &#10003; |
| 4 | &#10003; | &#10003; |
| 5 | &#10007; | &#10007; |
| 6 | &#10003; | &#10003; |
| 7 | &#10007; | &#10007; |
| 8 | &#10007; | &#10007; |
| 9 | &#10007; | &#10007; |
| 10 | &#10007; | &#10007; |
| 11 | &#10003; | &#10007; |
| 12 | &#10007; | &#10007; |
| 13 | &#10003; | &#10007; |
| 14 | &#10003; | &#10003; |
| 15 | &#10003; | &#10003; |
| 16 | &#10007; | &#10007; |
| 17 | &#10007; | &#10007; |
| 18 | &#10007; | &#10007; |
| 19 | &#10007; | &#10007; |
| 20 | &#10007; | &#10007; |
