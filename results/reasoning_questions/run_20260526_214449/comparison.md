# Reasoning Questions Evaluation

- Created at: `2026-05-26T21:44:49`
- Question file: `D:\aibeaver-tests\datasets\auto-manufacturer-tech-spec\qa_reasoning_questions_20.jsonl`
- Question count: `20`
- Modes: `mcd, connected, disconnected`
- Scoring mode: `llm_judge`
- Judge provider: `same`
- Judge model override: `n/a`
- Token usage includes judge calls: `True`
- Timing rows exclude judge latency; judge latency is stored in `score.judge_elapsed_seconds`.

| Provider | Mode | Model | Passed | Failed | Scored | Total | Pass rate | Errors |
| --- | --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| openai | mcd | `gpt-5.4` | 15 | 5 | 20 | 20 | 75.0% | 0 |
| openai | connected | `gpt-5.4` | 19 | 1 | 20 | 20 | 95.0% | 0 |
| openai | disconnected | `gpt-5.4` | 18 | 2 | 20 | 20 | 90.0% | 0 |

| Provider | Mode | Input tokens | Output tokens | Total tokens | Tool calls | Avg calls | Total seconds |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| openai | mcd | 261,232 | 15,335 | 276,567 | 26 | 1.30 | 196.9 sec |
| openai | connected | 241,149 | 14,468 | 255,617 | 26 | 1.30 | 203.2 sec |
| openai | disconnected | 259,199 | 16,543 | 275,742 | 36 | 1.80 | 238.8 sec |

## openai Question Matrix

| # | Question ID | mcd | connected | disconnected |
| ---: | --- | --- | --- | --- |
| 1 | `auto_reasoning_aero_drag_cd_increase_calc_01` | PASS | PASS | PASS |
| 2 | `auto_reasoning_aero_drag_cd_increase_effect_01` | FAIL | FAIL | FAIL |
| 3 | `auto_reasoning_brake_energy_payload_delta_calc_01` | PASS | PASS | PASS |
| 4 | `auto_reasoning_brake_energy_payload_delta_validation_01` | PASS | PASS | PASS |
| 5 | `auto_reasoning_battery_usable_window_range_calc_01` | PASS | PASS | PASS |
| 6 | `auto_reasoning_battery_usable_window_tradeoff_01` | PASS | PASS | PASS |
| 7 | `auto_reasoning_gcwr_reserve_calc_01` | FAIL | PASS | PASS |
| 8 | `auto_reasoning_gcwr_tow_payload_tradeoff_01` | PASS | PASS | FAIL |
| 9 | `auto_reasoning_high_tow_validation_flags_01` | FAIL | PASS | PASS |
| 10 | `auto_reasoning_wltp_co2_rule_count_01` | PASS | PASS | PASS |
| 11 | `auto_reasoning_wltp_co2_rule_engine_family_01` | FAIL | PASS | PASS |
| 12 | `auto_reasoning_quality_battery_health_release_calc_01` | PASS | PASS | PASS |
| 13 | `auto_reasoning_quality_battery_health_release_gates_01` | PASS | PASS | PASS |
| 14 | `auto_reasoning_traceability_containment_blockers_01` | PASS | PASS | PASS |
| 15 | `auto_reasoning_traceability_containment_release_01` | PASS | PASS | PASS |
| 16 | `auto_reasoning_thermal_heat_rejection_flow_calc_01` | PASS | PASS | PASS |
| 17 | `auto_reasoning_thermal_heat_rejection_validation_01` | PASS | PASS | PASS |
| 18 | `auto_reasoning_final_drive_tractive_effort_calc_01` | PASS | PASS | PASS |
| 19 | `auto_reasoning_final_drive_tractive_effort_tradeoff_01` | FAIL | PASS | PASS |
| 20 | `auto_reasoning_torque_power_calibration_delta_01` | PASS | PASS | PASS |

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
