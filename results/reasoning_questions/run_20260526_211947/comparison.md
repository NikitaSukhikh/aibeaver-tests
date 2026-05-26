# Reasoning Questions Evaluation

- Created at: `2026-05-26T21:19:47`
- Question file: `D:\aibeaver-tests\datasets\auto-manufacturer-tech-spec\qa_reasoning_questions_20.jsonl`
- Question count: `7`
- Modes: `mcd, connected, disconnected`
- Scoring mode: `llm_judge`
- Judge provider: `same`
- Judge model override: `n/a`
- Token usage includes judge calls: `True`
- Timing rows exclude judge latency; judge latency is stored in `score.judge_elapsed_seconds`.

| Provider | Mode | Model | Passed | Failed | Scored | Total | Pass rate | Errors |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| openai | mcd | `gpt-5.4` | 7 | 0 | 7 | 7 | 100.0% | 0 |
| openai | connected | `gpt-5.4` | 7 | 0 | 7 | 7 | 100.0% | 0 |
| openai | disconnected | `gpt-5.4` | 6 | 1 | 7 | 7 | 85.7% | 0 |

| Provider | Mode | Input tokens | Output tokens | Total tokens | Tool calls | Avg calls | Total seconds |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| openai | mcd | 94,075 | 5,824 | 99,899 | 9 | 1.29 | 72.4 sec |
| openai | connected | 93,556 | 6,433 | 99,989 | 10 | 1.43 | 82.3 sec |
| openai | disconnected | 103,178 | 7,685 | 110,863 | 14 | 2.00 | 98.6 sec |

## openai Question Matrix

| # | Question ID | mcd | connected | disconnected |
| ---: | --- | --- | --- | --- |
| 1 | `auto_reasoning_aero_drag_cd_increase_calc_01` | PASS | PASS | PASS |
| 2 | `auto_reasoning_aero_drag_cd_increase_effect_01` | PASS | PASS | FAIL |
| 3 | `auto_reasoning_brake_energy_payload_delta_calc_01` | PASS | PASS | PASS |
| 4 | `auto_reasoning_brake_energy_payload_delta_validation_01` | PASS | PASS | PASS |
| 5 | `auto_reasoning_battery_usable_window_range_calc_01` | PASS | PASS | PASS |
| 6 | `auto_reasoning_battery_usable_window_tradeoff_01` | PASS | PASS | PASS |
| 7 | `auto_reasoning_gcwr_reserve_calc_01` | PASS | PASS | PASS |

## Reference Notes

Some reference answers do not literally contain every `expected_contains` string. This is allowed for reasoning questions because the LLM judge compares both fields semantically.

- `auto_reasoning_aero_drag_cd_increase_calc_01`: missing literal expected strings in reference: `['drag_coefficient', '0.299']`
- `auto_reasoning_aero_drag_cd_increase_effect_01`: missing literal expected strings in reference: `['curb_mass_kg', 'drag_coefficient', 'frontal_area_m2']`
- `auto_reasoning_brake_energy_payload_delta_calc_01`: missing literal expected strings in reference: `['CHS-00190', 'curb_mass_kg']`
- `auto_reasoning_brake_energy_payload_delta_validation_01`: missing literal expected strings in reference: `['OAM-V0210']`
- `auto_reasoning_battery_usable_window_range_calc_01`: missing literal expected strings in reference: `['NMC811']`
- `auto_reasoning_battery_usable_window_tradeoff_01`: missing literal expected strings in reference: `['usable_capacity_kwh', '146.07']`
- `auto_reasoning_gcwr_reserve_calc_01`: missing literal expected strings in reference: `['CHS-00009', 'gcwr_kg', 'curb_mass_kg', 'max_payload_kg', 'braked_trailer_rating_kg']`
