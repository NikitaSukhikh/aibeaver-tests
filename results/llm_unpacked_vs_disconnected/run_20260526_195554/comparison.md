# LLM Unpacked vs Disconnected Comparison

- Created at: `2026-05-26T19:55:54`
- Provider: `openai`
- Model: `gpt-5.4`
- Eval mode: `kb_agent`
- Scoring mode: `llm_judge`
- Judge provider: `openai`
- Judge model: `gpt-5.4`
- Questions: `D:\aibeaver-tests\datasets\auto-manufacturer-tech-spec\qa_pilot_questions_20.jsonl`
- Connected dataset: `D:\aibeaver-tests\datasets\auto-manufacturer-tech-spec\unpacked`
- Disconnected dataset: `D:\aibeaver-tests\datasets\auto-manufacturer-tech-spec\disconnected`
- Token accounting: `provider API usage fields; provider/model native tokenizer; no local tokenizer or tiktoken estimate`

Pass totals: connected `0/1`, disconnected `0/1`.

| Token usage | Input | Output | Total |
| --- | ---: | ---: | ---: |
| Connected data | 0 | 0 | 0 |
| Disconnected data | 0 | 0 | 0 |
| Combined | 0 | 0 | 0 |

| Timing | Total | Avg per answer |
| --- | ---: | ---: |
| Connected data | 0.0 sec | 0.0 sec |
| Disconnected data | 0.0 sec | 0.0 sec |
| Combined | 0.0 sec | 0.0 sec |

| Tool calls | Total | Avg per question |
| --- | ---: | ---: |
| Connected data | 0 | 0.00 |
| Disconnected data | 0 | 0.00 |
| Combined | 0 | 0.00 |

| # | Connected data | Connected time | Connected calls | Disconnected data | Disconnected time | Disconnected calls |
| ---: | :---: | ---: | ---: | :---: | ---: | ---: |
| 1 | &#10007; | 0.0 sec | 0 | &#10007; | 0.0 sec | 0 |
