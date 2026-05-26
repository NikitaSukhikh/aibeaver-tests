# Reasoning Questions Evaluation

- Created at: `2026-05-26T22:52:28`
- Question file: `D:\aibeaver-tests\datasets\auto-manufacturer-tech-spec\qa_reasoning_questions_20.jsonl`
- Question count: `20`
- Modes: `connected`
- Scoring mode: `llm_judge`
- Judge provider: `same`
- Judge model override: `n/a`
- Token usage includes judge calls: `True`
- Timing rows exclude judge latency; judge latency is stored in `score.judge_elapsed_seconds`.

| Provider | Mode | Model | Passed | Failed | Scored | Total | Pass rate | Errors |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| openai | connected | `gpt-5.4` | 20 | 0 | 20 | 20 | 100.0% | 0 |

| Provider | Mode | Input tokens | Output tokens | Total tokens | Tool calls | Avg calls | Total seconds |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| openai | connected | 248,776 | 13,068 | 261,844 | 25 | 1.25 | 174.0 sec |

## Tool Call Diagnostics

Tool distribution is `tool calls per question: question count`. Ignored response objects are extra JSON objects emitted after the first executable object in the same model response; only the first object is executed by the harness.

| Provider | Mode | Tool distribution | Rows with extra JSON | Extra JSON objects | Ignored answer objects |
| --- | --- | --- | ---: | ---: | ---: |
| openai | connected | `1: 17, 2: 1, 3: 2` | 9 | 10 | 9 |

## openai Question Matrix

| # | Question ID | connected |
| ---: | --- | --- |
| 1 | `auto_reasoning_aero_drag_cd_increase_calc_01` | PASS |
| 2 | `auto_reasoning_aero_drag_cd_increase_effect_01` | PASS |
| 3 | `auto_reasoning_brake_energy_payload_delta_calc_01` | PASS |
| 4 | `auto_reasoning_brake_energy_payload_delta_validation_01` | PASS |
| 5 | `auto_reasoning_battery_usable_window_range_calc_01` | PASS |
| 6 | `auto_reasoning_battery_usable_window_tradeoff_01` | PASS |
| 7 | `auto_reasoning_gcwr_reserve_calc_01` | PASS |
| 8 | `auto_reasoning_gcwr_tow_payload_tradeoff_01` | PASS |
| 9 | `auto_reasoning_high_tow_validation_flags_01` | PASS |
| 10 | `auto_reasoning_wltp_co2_rule_count_01` | PASS |
| 11 | `auto_reasoning_wltp_co2_rule_engine_family_01` | PASS |
| 12 | `auto_reasoning_quality_battery_health_release_calc_01` | PASS |
| 13 | `auto_reasoning_quality_battery_health_release_gates_01` | PASS |
| 14 | `auto_reasoning_traceability_containment_blockers_01` | PASS |
| 15 | `auto_reasoning_traceability_containment_release_01` | PASS |
| 16 | `auto_reasoning_thermal_heat_rejection_flow_calc_01` | PASS |
| 17 | `auto_reasoning_thermal_heat_rejection_validation_01` | PASS |
| 18 | `auto_reasoning_final_drive_tractive_effort_calc_01` | PASS |
| 19 | `auto_reasoning_final_drive_tractive_effort_tradeoff_01` | PASS |
| 20 | `auto_reasoning_torque_power_calibration_delta_01` | PASS |

## Reference Notes

Some reference answers do not literally contain every `expected_contains` string. This is allowed for reasoning questions because the LLM judge compares both fields semantically.

- `auto_reasoning_aero_drag_cd_increase_calc_01`: missing literal expected strings in reference: `['drag_coefficient', '0.299']`
- `auto_reasoning_aero_drag_cd_increase_effect_01`: missing literal expected strings in reference: `['curb_mass_kg', 'drag_coefficient', 'frontal_area_m2']`
- `auto_reasoning_brake_energy_payload_delta_calc_01`: missing literal expected strings in reference: `['CHS-00190', 'curb_mass_kg']`
- `auto_reasoning_brake_energy_payload_delta_validation_01`: missing literal expected strings in reference: `['OAM-V0210']`
- `auto_reasoning_battery_usable_window_range_calc_01`: missing literal expected strings in reference: `['NMC811']`
- `auto_reasoning_battery_usable_window_tradeoff_01`: missing literal expected strings in reference: `['usable_capacity_kwh', '146.07']`
- `auto_reasoning_gcwr_reserve_calc_01`: missing literal expected strings in reference: `['CHS-00009', 'gcwr_kg', 'curb_mass_kg', 'max_payload_kg', 'braked_trailer_rating_kg']`
- `auto_reasoning_gcwr_tow_payload_tradeoff_01`: missing literal expected strings in reference: `['braked_trailer_rating_kg', '2677', '206']`
- `auto_reasoning_high_tow_validation_flags_01`: missing literal expected strings in reference: `['tow_rating_kg', '2677', 'braked_trailer_rating_kg']`
- `auto_reasoning_wltp_co2_rule_count_01`: missing literal expected strings in reference: `['engineering review']`
- `auto_reasoning_wltp_co2_rule_engine_family_01`: missing literal expected strings in reference: `['engineering-review']`
- `auto_reasoning_traceability_containment_blockers_01`: missing literal expected strings in reference: `['release_status']`
- `auto_reasoning_traceability_containment_release_01`: missing literal expected strings in reference: `['ppap_status', 'cpk_min', 'ppk_min', 'msa_grr_pct', 'battery_health_score_pct', 'released']`
- `auto_reasoning_thermal_heat_rejection_validation_01`: missing literal expected strings in reference: `['validation']`
- `auto_reasoning_torque_power_calibration_delta_01`: missing literal expected strings in reference: `['peak_torque_nm']`
