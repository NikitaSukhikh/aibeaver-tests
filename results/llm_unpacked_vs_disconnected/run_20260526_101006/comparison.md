# LLM Unpacked vs Disconnected Comparison

- Created at: `2026-05-26T10:10:06`
- Provider: `openai`
- Model: `gpt-5.4`
- Eval mode: `kb_agent`
- Questions: `D:\aibeaver-tests\datasets\auto-manufacturer-tech-spec\qa_pilot_questions_20.jsonl`
- Connected dataset: `D:\aibeaver-tests\datasets\auto-manufacturer-tech-spec\unpacked`
- Disconnected dataset: `D:\aibeaver-tests\datasets\auto-manufacturer-tech-spec\unpacked_disconnected`

Pass totals: connected `20/20`, disconnected `20/20`.

| Token usage | Input | Output | Total |
| --- | ---: | ---: | ---: |
| Connected data | 241,267 | 10,606 | 251,873 |
| Disconnected data | 344,933 | 15,282 | 360,215 |
| Combined | 586,200 | 25,888 | 612,088 |

| Timing | Total | Avg per answer |
| --- | ---: | ---: |
| Connected data | 185.4 sec | 9.3 sec |
| Disconnected data | 272.6 sec | 13.6 sec |
| Combined | 458.0 sec | 11.4 sec |

| # | Connected data | Connected time | Disconnected data | Disconnected time |
| ---: | :---: | ---: | :---: | ---: |
| 1 | &#10003; | 5.1 sec | &#10003; | 4.2 sec |
| 2 | &#10003; | 5.6 sec | &#10003; | 14.7 sec |
| 3 | &#10003; | 6.7 sec | &#10003; | 22.5 sec |
| 4 | &#10003; | 9.0 sec | &#10003; | 18.0 sec |
| 5 | &#10003; | 6.8 sec | &#10003; | 6.6 sec |
| 6 | &#10003; | 8.1 sec | &#10003; | 9.6 sec |
| 7 | &#10003; | 7.6 sec | &#10003; | 8.8 sec |
| 8 | &#10003; | 8.3 sec | &#10003; | 16.5 sec |
| 9 | &#10003; | 4.9 sec | &#10003; | 4.6 sec |
| 10 | &#10003; | 5.8 sec | &#10003; | 18.6 sec |
| 11 | &#10003; | 8.4 sec | &#10003; | 6.7 sec |
| 12 | &#10003; | 5.3 sec | &#10003; | 9.3 sec |
| 13 | &#10003; | 9.8 sec | &#10003; | 13.1 sec |
| 14 | &#10003; | 19.5 sec | &#10003; | 20.4 sec |
| 15 | &#10003; | 12.6 sec | &#10003; | 20.0 sec |
| 16 | &#10003; | 20.1 sec | &#10003; | 32.2 sec |
| 17 | &#10003; | 11.3 sec | &#10003; | 13.2 sec |
| 18 | &#10003; | 11.8 sec | &#10003; | 8.3 sec |
| 19 | &#10003; | 12.0 sec | &#10003; | 18.2 sec |
| 20 | &#10003; | 6.7 sec | &#10003; | 7.0 sec |
