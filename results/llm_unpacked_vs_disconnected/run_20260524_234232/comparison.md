# LLM Unpacked vs Disconnected Comparison

- Created at: `2026-05-24T23:42:32`
- Provider: `openai`
- Model: `gpt-5.4`
- Eval mode: `kb_agent`
- Questions: `D:\aibeaver-tests\datasets\auto-manufacturer-tech-spec\qa_pilot_questions_20.jsonl`
- Connected dataset: `D:\aibeaver-tests\datasets\auto-manufacturer-tech-spec\unpacked`
- Disconnected dataset: `D:\aibeaver-tests\datasets\auto-manufacturer-tech-spec\unpacked_disconnected`

Pass totals: connected `18(UPD:20)/20`, disconnected `18/20`.

| Token usage | Input | Output | Total |
| --- | ---: | ---: | ---: |
| Connected data | 284,350 | 10,687 | 295,037 |
| Disconnected data | 366,959 | 16,241 | 383,200 |
| Combined | 651,309 | 26,928 | 678,237 |

| Timing | Total | Avg per answer |
| --- | ---: | ---: |
| Connected data | 243.7 sec | 12.2 sec |
| Disconnected data | 339.5 sec | 17.0 sec |
| Combined | 583.2 sec | 14.6 sec |

| # | Connected data | Connected time | Disconnected data | Disconnected time |
| ---: | :---: | ---: | :---: | ---: |
| 1 | &#10003; | 7.0 sec | &#10003; | 13.2 sec |
| 2 | &#10003; | 11.5 sec | &#10003; | 13.3 sec |
| 3 | &#10003; | 11.1 sec | &#10003; | 19.5 sec |
| 4 | &#10003; | 9.0 sec | &#10003; | 12.0 sec |
| 5 | &#10003; | 11.6 sec | &#10003; | 16.0 sec |
| 6 | &#10007; | 10.2 sec | &#10007; | 14.0 sec |
| 7 | &#10003; | 13.0 sec | &#10003; | 15.0 sec |
| 8 | &#10003; | 10.8 sec | &#10003; | 18.4 sec |
| 9 | &#10007; | 9.3 sec | &#10003; | 17.7 sec |
| 10 | &#10003; | 15.0 sec | &#10003; | 20.2 sec |
| 11 | &#10003; | 4.7 sec | &#10003; | 11.6 sec |
| 12 | &#10003; | 7.3 sec | &#10003; | 7.4 sec |
| 13 | &#10003; | 7.8 sec | &#10003; | 37.0 sec |
| 14 | &#10003; | 20.2 sec | &#10007; | 20.8 sec |
| 15 | &#10003; | 16.5 sec | &#10003; | 21.4 sec |
| 16 | &#10003; | 18.0 sec | &#10003; | 19.5 sec |
| 17 | &#10003; | 15.4 sec | &#10003; | 16.2 sec |
| 18 | &#10003; | 18.5 sec | &#10003; | 17.8 sec |
| 19 | &#10003; | 18.1 sec | &#10003; | 20.7 sec |
| 20 | &#10003; | 8.8 sec | &#10003; | 7.7 sec |
