# LLM Unpacked vs Disconnected Comparison

- Created at: `2026-05-26T20:36:51`
- Provider: `openai`
- Model: `gpt-5.4`
- Eval mode: `kb_agent`
- Scoring mode: `llm_judge`
- Judge provider: `openai`
- Judge model: `gpt-5.4`
- Token usage includes judge calls: `True`
- Timing rows exclude judge latency; judge latency is stored in `score.judge_elapsed_seconds`.
- Questions: `D:\aibeaver-tests\datasets\auto-manufacturer-tech-spec\qa_pilot_questions_20.jsonl`
- Connected dataset: `D:\aibeaver-tests\datasets\auto-manufacturer-tech-spec\unpacked`
- Disconnected dataset: `D:\aibeaver-tests\datasets\auto-manufacturer-tech-spec\disconnected`
- Token accounting: `provider API usage fields; provider/model native tokenizer; no local tokenizer or tiktoken estimate`

Pass totals: connected `18/20`, disconnected `19/20`.

| Token usage | Input | Output | Total |
| --- | ---: | ---: | ---: |
| Connected data | 191,591 | 9,049 | 200,640 |
| Disconnected data | 287,370 | 12,619 | 299,989 |
| Combined | 478,961 | 21,668 | 500,629 |

| Timing | Total | Avg per answer |
| --- | ---: | ---: |
| Connected data | 119.1 sec | 6.0 sec |
| Disconnected data | 184.6 sec | 9.2 sec |
| Combined | 303.7 sec | 7.6 sec |

| Tool calls | Total | Avg per question |
| --- | ---: | ---: |
| Connected data | 23 | 1.15 |
| Disconnected data | 42 | 2.10 |
| Combined | 65 | 1.62 |

| # | Connected data | Connected time | Connected calls | Disconnected data | Disconnected time | Disconnected calls |
| ---: | :---: | ---: | ---: | :---: | ---: | ---: |
| 1 | &#10003; | 5.0 sec | 1 | &#10003; | 3.5 sec | 1 |
| 2 | &#10003; | 5.5 sec | 1 | &#10003; | 11.4 sec | 3 |
| 3 | &#10003; | 9.2 sec | 2 | &#10003; | 16.0 sec | 3 |
| 4 | &#10003; | 5.0 sec | 1 | &#10003; | 11.1 sec | 3 |
| 5 | &#10003; | 6.7 sec | 1 | &#10003; | 10.1 sec | 3 |
| 6 | &#10003; | 5.1 sec | 1 | &#10003; | 14.2 sec | 3 |
| 7 | &#10003; | 10.0 sec | 2 | &#10003; | 15.3 sec | 3 |
| 8 | &#10003; | 9.4 sec | 2 | &#10003; | 18.7 sec | 4 |
| 9 | &#10003; | 3.7 sec | 1 | &#10003; | 3.7 sec | 1 |
| 10 | &#10003; | 7.5 sec | 2 | &#10007; | 7.6 sec | 2 |
| 11 | &#10003; | 5.1 sec | 1 | &#10003; | 4.3 sec | 1 |
| 12 | &#10003; | 3.3 sec | 1 | &#10003; | 3.7 sec | 1 |
| 13 | &#10003; | 4.5 sec | 1 | &#10003; | 4.5 sec | 1 |
| 14 | &#10007; | 1.9 sec | 0 | &#10003; | 4.7 sec | 1 |
| 15 | &#10003; | 5.8 sec | 1 | &#10003; | 11.8 sec | 3 |
| 16 | &#10003; | 12.6 sec | 1 | &#10003; | 22.8 sec | 3 |
| 17 | &#10003; | 5.8 sec | 2 | &#10003; | 7.9 sec | 3 |
| 18 | &#10007; | 2.1 sec | 0 | &#10003; | 4.0 sec | 1 |
| 19 | &#10003; | 4.1 sec | 1 | &#10003; | 4.5 sec | 1 |
| 20 | &#10003; | 6.7 sec | 1 | &#10003; | 4.8 sec | 1 |
