# Reasoning Questions Evaluation

- Created at: `2026-05-26T20:54:00`
- Question file: `D:\aibeaver-tests\datasets\auto-manufacturer-tech-spec\qa_reasoning_questions_10.jsonl`
- Question count: `5`
- Modes: `mcd, connected, disconnected`
- Scoring mode: `llm_judge`
- Judge provider: `same`
- Judge model override: `n/a`
- Token usage includes judge calls: `True`
- Timing rows exclude judge latency; judge latency is stored in `score.judge_elapsed_seconds`.

| Provider | Mode | Model | Passed | Failed | Scored | Total | Pass rate | Errors |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| openai | mcd | `gpt-5.4` | 3 | 2 | 5 | 5 | 60.0% | 0 |
| openai | connected | `gpt-5.4` | 4 | 1 | 5 | 5 | 80.0% | 0 |
| openai | disconnected | `gpt-5.4` | 4 | 1 | 5 | 5 | 80.0% | 0 |

| Provider | Mode | Input tokens | Output tokens | Total tokens | Tool calls | Avg calls | Total seconds |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| openai | mcd | 54,104 | 3,834 | 57,938 | 6 | 1.20 | 43.4 sec |
| openai | connected | 60,955 | 4,060 | 65,015 | 7 | 1.40 | 54.1 sec |
| openai | disconnected | 78,826 | 4,974 | 83,800 | 11 | 2.20 | 72.6 sec |

## openai Question Matrix

| # | Question ID | mcd | connected | disconnected |
| ---: | --- | --- | --- | --- |
| 1 | `auto_reasoning_aero_drag_cd_increase_calc_01` | PASS | PASS | PASS |
| 2 | `auto_reasoning_aero_drag_cd_increase_effect_01` | PASS | PASS | PASS |
| 3 | `auto_reasoning_brake_energy_payload_delta_calc_01` | FAIL | PASS | PASS |
| 4 | `auto_reasoning_brake_energy_payload_delta_validation_01` | PASS | PASS | PASS |
| 5 | `auto_reasoning_battery_usable_window_range_calc_01` | FAIL | FAIL | FAIL |

## Reference Notes

Some reference answers do not literally contain every `expected_contains` string. This is allowed for reasoning questions because the LLM judge compares both fields semantically.

- `auto_reasoning_aero_drag_cd_increase_calc_01`: missing literal expected strings in reference: `['drag_coefficient', '0.299']`
- `auto_reasoning_aero_drag_cd_increase_effect_01`: missing literal expected strings in reference: `['curb_mass_kg', 'drag_coefficient', 'frontal_area_m2']`
- `auto_reasoning_brake_energy_payload_delta_calc_01`: missing literal expected strings in reference: `['CHS-00190', 'curb_mass_kg']`
- `auto_reasoning_brake_energy_payload_delta_validation_01`: missing literal expected strings in reference: `['OAM-V0210']`
- `auto_reasoning_battery_usable_window_range_calc_01`: missing literal expected strings in reference: `['NMC811']`
