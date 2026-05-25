# LLM MCD Evaluation

- Created at: `2026-05-25T01:32:11`
- MCD package: `D:\aibeaver-tests\datasets\auto-manufacturer-tech-spec\auto-manufacturer-tech-spec.mcd`
- Questions: `C:\Windows\Temp\mcd_q16_99d6d183d8604052878a9eb333c1704f.jsonl`
- MCD CLI: `mcd`
- MCD CLI available: `True`
- MCD tool reference: aligned compact CLI docs with Python fallback
- Max tool steps: `8`

| Provider | Model | Passed | Failed | Scored | Total | Pass rate | Errors |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| openai | `gpt-5.4` | 1 | 0 | 1 | 1 | 100.0% | 0 |

| Provider | Input tokens | Output tokens | Total tokens | Total seconds | Avg seconds |
| --- | ---: | ---: | ---: | ---: | ---: |
| openai | 6,957 | 631 | 7,588 | 9.9 sec | 9.9 sec |

## openai Answers

| # | Status | Seconds | Question | Answer |
| ---: | --- | ---: | --- | --- |
| 1 | PASS | 9.9 sec | Main.md says high-output V50D calibrations require battery coolant flow above 15 L/min. What is the highest-power V50D calibration, and how many battery packs exceed 15 L/min? Include the max-coolant pack. | Main.md rule used: high-output V50D calibrations require battery coolant_flow_l_min > 15 L/min. Highest-power V50D calibration: calibration_id CAL-00017, engine_family V50D, platform_code PX63, peak_power_kw 1137.9, boost_pressure_kpa 117.3, thermal_limit_deg_c 118.8, production_release_date 2025... |
