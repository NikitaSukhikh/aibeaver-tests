# LLM Unpacked vs Disconnected Comparison

- Created at: `2026-05-26T20:02:25`
- Provider: `openai`
- Model: `gpt-5.4`
- Eval mode: `kb_agent`
- Scoring mode: `programmatic`
- Judge provider: `n/a`
- Judge model: `n/a`
- Token usage includes judge calls: `False`
- Questions: `D:\aibeaver-tests\datasets\auto-manufacturer-tech-spec\qa_pilot_questions_20.jsonl`
- Connected dataset: `D:\aibeaver-tests\datasets\auto-manufacturer-tech-spec\unpacked`
- Disconnected dataset: `D:\aibeaver-tests\datasets\auto-manufacturer-tech-spec\disconnected`
- Token accounting: `provider API usage fields; provider/model native tokenizer; no local tokenizer or tiktoken estimate`

Pass totals: connected `19/20`, disconnected `18/20`.

| Token usage | Input | Output | Total |
| --- | ---: | ---: | ---: |
| Connected data | 196,437 | 6,690 | 203,127 |
| Disconnected data | 299,017 | 10,103 | 309,120 |
| Combined | 495,454 | 16,793 | 512,247 |

| Timing | Total | Avg per answer |
| --- | ---: | ---: |
| Connected data | 168.2 sec | 8.4 sec |
| Disconnected data | 204.2 sec | 10.2 sec |
| Combined | 372.3 sec | 9.3 sec |

| Tool calls | Total | Avg per question |
| --- | ---: | ---: |
| Connected data | 26 | 1.30 |
| Disconnected data | 45 | 2.25 |
| Combined | 71 | 1.77 |

| # | Connected data | Connected time | Connected calls | Disconnected data | Disconnected time | Disconnected calls |
| ---: | :---: | ---: | ---: | :---: | ---: | ---: |
| 1 | &#10003; | 10.1 sec | 1 | &#10003; | 5.0 sec | 1 |
| 2 | &#10003; | 8.0 sec | 1 | &#10003; | 10.9 sec | 3 |
| 3 | &#10003; | 12.8 sec | 2 | &#10003; | 15.0 sec | 3 |
| 4 | &#10003; | 7.8 sec | 1 | &#10003; | 13.7 sec | 3 |
| 5 | &#10003; | 13.9 sec | 2 | &#10003; | 12.2 sec | 3 |
| 6 | &#10003; | 9.8 sec | 1 | &#10003; | 13.2 sec | 3 |
| 7 | &#10003; | 14.4 sec | 2 | &#10003; | 14.9 sec | 3 |
| 8 | &#10003; | 10.1 sec | 2 | &#10003; | 16.7 sec | 4 |
| 9 | &#10007; | 3.8 sec | 1 | &#10007; | 8.3 sec | 3 |
| 10 | &#10003; | 7.5 sec | 2 | &#10007; | 8.1 sec | 2 |
| 11 | &#10003; | 4.4 sec | 1 | &#10003; | 4.5 sec | 1 |
| 12 | &#10003; | 3.2 sec | 1 | &#10003; | 3.3 sec | 1 |
| 13 | &#10003; | 5.1 sec | 1 | &#10003; | 6.3 sec | 1 |
| 14 | &#10003; | 5.7 sec | 1 | &#10003; | 8.4 sec | 1 |
| 15 | &#10003; | 6.9 sec | 1 | &#10003; | 12.0 sec | 3 |
| 16 | &#10003; | 15.3 sec | 1 | &#10003; | 22.1 sec | 3 |
| 17 | &#10003; | 6.9 sec | 2 | &#10003; | 10.9 sec | 3 |
| 18 | &#10003; | 5.6 sec | 1 | &#10003; | 5.3 sec | 1 |
| 19 | &#10003; | 9.6 sec | 1 | &#10003; | 7.7 sec | 2 |
| 20 | &#10003; | 7.4 sec | 1 | &#10003; | 5.7 sec | 1 |
