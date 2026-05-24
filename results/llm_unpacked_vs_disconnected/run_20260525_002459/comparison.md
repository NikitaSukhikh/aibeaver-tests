# LLM Unpacked vs Disconnected Comparison

- Created at: `2026-05-25T00:24:59`
- Provider: `openai`
- Model: `gpt-5.4`
- Eval mode: `kb_agent`
- Questions: `D:\aibeaver-tests\results\llm_unpacked_vs_disconnected\qa_q6_q9_tmp.jsonl`
- Connected dataset: `D:\aibeaver-tests\datasets\auto-manufacturer-tech-spec\unpacked`
- Disconnected dataset: `D:\aibeaver-tests\datasets\auto-manufacturer-tech-spec\unpacked_disconnected`

Pass totals: connected `2/2`, disconnected `2/2`.

| Token usage | Input | Output | Total |
| --- | ---: | ---: | ---: |
| Connected data | 22,243 | 1,446 | 23,689 |
| Disconnected data | 25,665 | 1,894 | 27,559 |
| Combined | 47,908 | 3,340 | 51,248 |

| Timing | Total | Avg per answer |
| --- | ---: | ---: |
| Connected data | 26.5 sec | 13.3 sec |
| Disconnected data | 34.0 sec | 17.0 sec |
| Combined | 60.5 sec | 15.1 sec |

| # | Connected data | Connected time | Disconnected data | Disconnected time |
| ---: | :---: | ---: | :---: | ---: |
| 1 | &#10003; | 12.3 sec | &#10003; | 16.9 sec |
| 2 | &#10003; | 14.2 sec | &#10003; | 17.1 sec |
