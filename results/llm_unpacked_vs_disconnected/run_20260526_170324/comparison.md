# LLM Unpacked vs Disconnected Comparison

- Created at: `2026-05-26T17:03:24`
- Provider: `anthropic`
- Model: `claude-opus-4-5`
- Eval mode: `kb_agent`
- Questions: `D:\aibeaver-tests\datasets\auto-manufacturer-tech-spec\qa_pilot_questions_20.jsonl`
- Connected dataset: `D:\aibeaver-tests\datasets\auto-manufacturer-tech-spec\unpacked`
- Disconnected dataset: `D:\aibeaver-tests\datasets\auto-manufacturer-tech-spec\unpacked_disconnected`
- Token accounting: `provider API usage fields; provider/model native tokenizer; no local tokenizer or tiktoken estimate`

Pass totals: connected `15/20`, disconnected `18/20`.

| Token usage | Input | Output | Total |
| --- | ---: | ---: | ---: |
| Connected data | 341,382 | 6,142 | 347,524 |
| Disconnected data | 520,001 | 7,383 | 527,384 |
| Combined | 861,383 | 13,525 | 874,908 |

| Timing | Total | Avg per answer |
| --- | ---: | ---: |
| Connected data | 200.6 sec | 10.0 sec |
| Disconnected data | 271.6 sec | 13.6 sec |
| Combined | 472.2 sec | 11.8 sec |

| Tool calls | Total | Avg per question |
| --- | ---: | ---: |
| Connected data | 43 | 2.15 |
| Disconnected data | 69 | 3.45 |
| Combined | 112 | 2.80 |

| # | Connected data | Connected time | Connected calls | Disconnected data | Disconnected time | Disconnected calls |
| ---: | :---: | ---: | ---: | :---: | ---: | ---: |
| 1 | &#10003; | 5.9 sec | 1 | &#10003; | 5.7 sec | 1 |
| 2 | &#10003; | 6.0 sec | 1 | &#10003; | 14.8 sec | 3 |
| 3 | &#10003; | 6.2 sec | 1 | &#10003; | 15.3 sec | 4 |
| 4 | &#10003; | 9.8 sec | 2 | &#10003; | 15.6 sec | 4 |
| 5 | &#10007; | 9.0 sec | 2 | &#10003; | 14.9 sec | 4 |
| 6 | &#10003; | 6.4 sec | 1 | &#10003; | 9.3 sec | 3 |
| 7 | &#10007; | 8.2 sec | 2 | &#10007; | 13.8 sec | 4 |
| 8 | &#10003; | 11.0 sec | 2 | &#10003; | 18.1 sec | 4 |
| 9 | &#10007; | 9.2 sec | 2 | &#10003; | 20.8 sec | 4 |
| 10 | &#10007; | 12.2 sec | 2 | &#10003; | 13.5 sec | 4 |
| 11 | &#10003; | 12.7 sec | 1 | &#10003; | 4.2 sec | 1 |
| 12 | &#10003; | 10.9 sec | 2 | &#10003; | 11.6 sec | 3 |
| 13 | &#10007; | 6.9 sec | 2 | &#10007; | 9.0 sec | 3 |
| 14 | &#10003; | 12.1 sec | 2 | &#10003; | 14.3 sec | 3 |
| 15 | &#10003; | 15.4 sec | 5 | &#10003; | 15.5 sec | 4 |
| 16 | &#10003; | 13.1 sec | 3 | &#10003; | 18.1 sec | 4 |
| 17 | &#10003; | 10.4 sec | 3 | &#10003; | 16.4 sec | 5 |
| 18 | &#10003; | 13.2 sec | 4 | &#10003; | 18.5 sec | 5 |
| 19 | &#10003; | 12.6 sec | 4 | &#10003; | 17.5 sec | 5 |
| 20 | &#10003; | 9.4 sec | 1 | &#10003; | 4.8 sec | 1 |
