# Reasoning Questions Evaluation

- Created at: `2026-05-26T22:51:40`
- Question file: `D:\aibeaver-tests\datasets\auto-manufacturer-tech-spec\qa_reasoning_questions_20.jsonl`
- Question count: `2`
- Modes: `connected`
- Scoring mode: `llm_judge`
- Judge provider: `same`
- Judge model override: `n/a`
- Token usage includes judge calls: `True`
- Timing rows exclude judge latency; judge latency is stored in `score.judge_elapsed_seconds`.

| Provider | Mode | Model | Passed | Failed | Scored | Total | Pass rate | Errors |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| openai | connected | `gpt-5.4` | 2 | 0 | 2 | 2 | 100.0% | 0 |

| Provider | Mode | Input tokens | Output tokens | Total tokens | Tool calls | Avg calls | Total seconds |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| openai | connected | 32,127 | 1,597 | 33,724 | 4 | 2.00 | 20.3 sec |

## Tool Call Diagnostics

Tool distribution is `tool calls per question: question count`. Ignored response objects are extra JSON objects emitted after the first executable object in the same model response; only the first object is executed by the harness.

| Provider | Mode | Tool distribution | Rows with extra JSON | Extra JSON objects | Ignored answer objects |
| --- | --- | --- | ---: | ---: | ---: |
| openai | connected | `2: 2` | 1 | 1 | 1 |

## openai Question Matrix

| # | Question ID | connected |
| ---: | --- | --- |
| 1 | `auto_reasoning_aero_drag_cd_increase_calc_01` | PASS |
| 2 | `auto_reasoning_aero_drag_cd_increase_effect_01` | PASS |

## Reference Notes

Some reference answers do not literally contain every `expected_contains` string. This is allowed for reasoning questions because the LLM judge compares both fields semantically.

- `auto_reasoning_aero_drag_cd_increase_calc_01`: missing literal expected strings in reference: `['drag_coefficient', '0.299']`
- `auto_reasoning_aero_drag_cd_increase_effect_01`: missing literal expected strings in reference: `['curb_mass_kg', 'drag_coefficient', 'frontal_area_m2']`
