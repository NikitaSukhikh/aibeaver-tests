# LLM Unpacked vs Disconnected Comparison

- Created at: `2026-05-26T18:57:17`
- Provider: `openai`
- Model: `gpt-5.4`
- Eval mode: `kb_agent`
- Questions: `D:\aibeaver-tests\datasets\auto-manufacturer-tech-spec\qa_pilot_questions_20.jsonl`
- Connected dataset: `D:\aibeaver-tests\datasets\auto-manufacturer-tech-spec\unpacked`
- Disconnected dataset: `D:\aibeaver-tests\datasets\auto-manufacturer-tech-spec\disconnected`
- Token accounting: `provider API usage fields; provider/model native tokenizer; no local tokenizer or tiktoken estimate`

Pass totals: connected `16/20`, disconnected `16/20`.

| Token usage | Input | Output | Total |
| --- | ---: | ---: | ---: |
| Connected data | 214,295 | 10,150 | 224,445 |
| Disconnected data | 447,678 | 19,365 | 467,043 |
| Combined | 661,973 | 29,515 | 691,488 |

| Timing | Total | Avg per answer |
| --- | ---: | ---: |
| Connected data | 189.5 sec | 9.5 sec |
| Disconnected data | 357.4 sec | 17.9 sec |
| Combined | 546.9 sec | 13.7 sec |

| Tool calls | Total | Avg per question |
| --- | ---: | ---: |
| Connected data | 29 | 1.45 |
| Disconnected data | 60 | 3.00 |
| Combined | 89 | 2.23 |

| # | Connected data | Connected time | Connected calls | Disconnected data | Disconnected time | Disconnected calls |
| ---: | :---: | ---: | ---: | :---: | ---: | ---: |
| 1 | &#10003; | 5.8 sec | 1 | &#10003; | 4.7 sec | 1 |
| 2 | &#10003; | 7.5 sec | 1 | &#10003; | 4.6 sec | 1 |
| 3 | &#10003; | 6.4 sec | 1 | &#10003; | 14.0 sec | 3 |
| 4 | &#10003; | 6.8 sec | 1 | &#10003; | 14.1 sec | 3 |
| 5 | &#10003; | 8.3 sec | 1 | &#10003; | 15.2 sec | 3 |
| 6 | &#10003; | 10.7 sec | 2 | &#10003; | 14.5 sec | 3 |
| 7 | &#10003; | 6.4 sec | 2 | &#10003; | 13.7 sec | 3 |
| 8 | &#10003; | 15.9 sec | 3 | &#10003; | 20.4 sec | 4 |
| 9 | &#10003; | 6.0 sec | 1 | &#10003; | 17.6 sec | 3 |
| 10 | &#10003; | 7.1 sec | 1 | &#10003; | 14.0 sec | 3 |
| 11 | &#10003; | 6.0 sec | 1 | &#10003; | 10.6 sec | 2 |
| 12 | &#10003; | 11.9 sec | 1 | &#10003; | 23.0 sec | 3 |
| 13 | &#10003; | 10.0 sec | 2 | &#10003; | 16.0 sec | 3 |
| 14 | &#10007; | 8.2 sec | 1 | &#10007; | 12.1 sec | 2 |
| 15 | &#10003; | 12.4 sec | 1 | &#10003; | 22.8 sec | 2 |
| 16 | &#10003; | 7.1 sec | 1 | &#10003; | 15.4 sec | 3 |
| 17 | &#10003; | 10.8 sec | 2 | &#10007; | 37.1 sec | 8 |
| 18 | &#10007; | 10.9 sec | 2 | &#10003; | 15.5 sec | 4 |
| 19 | &#10007; | 16.2 sec | 2 | &#10007; | 41.7 sec | 3 |
| 20 | &#10007; | 15.2 sec | 2 | &#10007; | 30.2 sec | 3 |
