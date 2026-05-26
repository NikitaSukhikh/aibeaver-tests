# LLM Unpacked vs Disconnected Comparison

- Created at: `2026-05-26T17:43:34`
- Provider: `xai`
- Model: `grok-4.3`
- Eval mode: `kb_agent`
- Questions: `D:\aibeaver-tests\datasets\auto-manufacturer-tech-spec\qa_pilot_questions_20.jsonl`
- Connected dataset: `D:\aibeaver-tests\datasets\auto-manufacturer-tech-spec\unpacked`
- Disconnected dataset: `D:\aibeaver-tests\datasets\auto-manufacturer-tech-spec\unpacked_disconnected`
- Token accounting: `provider API usage fields; provider/model native tokenizer; no local tokenizer or tiktoken estimate`

Pass totals: connected `14/20`, disconnected `13/20`.

| Token usage | Input | Output | Total |
| --- | ---: | ---: | ---: |
| Connected data | 232,072 | 3,607 | 253,324 |
| Disconnected data | 408,903 | 4,019 | 436,882 |
| Combined | 640,975 | 7,626 | 690,206 |

| Timing | Total | Avg per answer |
| --- | ---: | ---: |
| Connected data | 461.8 sec | 23.1 sec |
| Disconnected data | 555.7 sec | 27.8 sec |
| Combined | 1017.5 sec | 25.4 sec |

| Tool calls | Total | Avg per question |
| --- | ---: | ---: |
| Connected data | 39 | 1.95 |
| Disconnected data | 68 | 3.40 |
| Combined | 107 | 2.67 |

| # | Connected data | Connected time | Connected calls | Disconnected data | Disconnected time | Disconnected calls |
| ---: | :---: | ---: | ---: | :---: | ---: | ---: |
| 1 | &#10003; | 6.0 sec | 1 | &#10003; | 5.4 sec | 1 |
| 2 | &#10003; | 19.8 sec | 1 | &#10003; | 13.0 sec | 3 |
| 3 | &#10003; | 7.3 sec | 1 | &#10003; | 9.0 sec | 1 |
| 4 | &#10003; | 9.1 sec | 1 | &#10003; | 33.0 sec | 4 |
| 5 | &#10003; | 6.5 sec | 1 | &#10003; | 7.4 sec | 1 |
| 6 | &#10007; | 9.4 sec | 2 | &#10007; | 42.0 sec | 5 |
| 7 | &#10003; | 6.9 sec | 1 | &#10007; | 26.5 sec | 3 |
| 8 | &#10003; | 9.0 sec | 2 | &#10003; | 30.5 sec | 4 |
| 9 | &#10003; | 6.3 sec | 1 | &#10003; | 9.2 sec | 1 |
| 10 | &#10007; | 17.6 sec | 3 | &#10003; | 30.6 sec | 4 |
| 11 | &#10003; | 6.3 sec | 1 | &#10003; | 51.3 sec | 3 |
| 12 | &#10003; | 11.0 sec | 1 | &#10003; | 19.2 sec | 4 |
| 13 | &#10007; | 8.1 sec | 1 | &#10007; | 10.5 sec | 2 |
| 14 | &#10007; | 28.5 sec | 4 | &#10007; | 19.2 sec | 4 |
| 15 | &#10007; | 231.6 sec | 4 | &#10007; | 22.1 sec | 6 |
| 16 | &#10003; | 20.6 sec | 4 | &#10007; | 21.1 sec | 5 |
| 17 | &#10007; | 14.1 sec | 3 | &#10007; | 139.2 sec | 6 |
| 18 | &#10003; | 19.7 sec | 4 | &#10003; | 31.6 sec | 6 |
| 19 | &#10003; | 19.2 sec | 2 | &#10003; | 30.3 sec | 4 |
| 20 | &#10003; | 4.5 sec | 1 | &#10003; | 4.8 sec | 1 |
