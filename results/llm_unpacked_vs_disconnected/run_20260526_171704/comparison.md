# LLM Unpacked vs Disconnected Comparison

- Created at: `2026-05-26T17:17:04`
- Provider: `openai`
- Model: `gpt-5.4`
- Eval mode: `kb_agent`
- Questions: `D:\aibeaver-tests\datasets\auto-manufacturer-tech-spec\qa_pilot_questions_20.jsonl`
- Connected dataset: `D:\aibeaver-tests\datasets\auto-manufacturer-tech-spec\unpacked`
- Disconnected dataset: `D:\aibeaver-tests\datasets\auto-manufacturer-tech-spec\unpacked_disconnected`
- Token accounting: `provider API usage fields; provider/model native tokenizer; no local tokenizer or tiktoken estimate`

Pass totals: connected `20/20`, disconnected `20/20`.

| Token usage | Input | Output | Total |
| --- | ---: | ---: | ---: |
| Connected data | 202,559 | 7,948 | 210,507 |
| Disconnected data | 427,301 | 12,109 | 439,410 |
| Combined | 629,860 | 20,057 | 649,917 |

| Timing | Total | Avg per answer |
| --- | ---: | ---: |
| Connected data | 171.4 sec | 8.6 sec |
| Disconnected data | 289.3 sec | 14.5 sec |
| Combined | 460.6 sec | 11.5 sec |

| Tool calls | Total | Avg per question |
| --- | ---: | ---: |
| Connected data | 29 | 1.45 |
| Disconnected data | 64 | 3.20 |
| Combined | 93 | 2.33 |

| # | Connected data | Connected time | Connected calls | Disconnected data | Disconnected time | Disconnected calls |
| ---: | :---: | ---: | ---: | :---: | ---: | ---: |
| 1 | &#10003; | 5.5 sec | 1 | &#10003; | 5.0 sec | 1 |
| 2 | &#10003; | 4.5 sec | 1 | &#10003; | 4.5 sec | 1 |
| 3 | &#10003; | 10.5 sec | 1 | &#10003; | 18.5 sec | 4 |
| 4 | &#10003; | 8.8 sec | 2 | &#10003; | 13.9 sec | 4 |
| 5 | &#10003; | 7.5 sec | 1 | &#10003; | 6.0 sec | 1 |
| 6 | &#10003; | 4.7 sec | 1 | &#10003; | 10.9 sec | 3 |
| 7 | &#10003; | 7.8 sec | 2 | &#10003; | 11.4 sec | 3 |
| 8 | &#10003; | 9.2 sec | 2 | &#10003; | 13.5 sec | 4 |
| 9 | &#10003; | 5.9 sec | 1 | &#10003; | 13.6 sec | 4 |
| 10 | &#10003; | 5.5 sec | 1 | &#10003; | 21.1 sec | 5 |
| 11 | &#10003; | 4.0 sec | 1 | &#10003; | 27.0 sec | 4 |
| 12 | &#10003; | 4.8 sec | 1 | &#10003; | 11.0 sec | 3 |
| 13 | &#10003; | 4.7 sec | 1 | &#10003; | 14.1 sec | 3 |
| 14 | &#10003; | 24.1 sec | 2 | &#10003; | 19.1 sec | 3 |
| 15 | &#10003; | 17.2 sec | 2 | &#10003; | 17.6 sec | 4 |
| 16 | &#10003; | 9.8 sec | 1 | &#10003; | 19.3 sec | 4 |
| 17 | &#10003; | 11.2 sec | 2 | &#10003; | 9.9 sec | 2 |
| 18 | &#10003; | 9.5 sec | 2 | &#10003; | 18.9 sec | 4 |
| 19 | &#10003; | 9.4 sec | 2 | &#10003; | 21.7 sec | 4 |
| 20 | &#10003; | 6.6 sec | 2 | &#10003; | 12.1 sec | 3 |
