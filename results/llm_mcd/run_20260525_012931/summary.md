# LLM MCD Evaluation

- Created at: `2026-05-25T01:29:31`
- MCD package: `D:\aibeaver-tests\datasets\auto-manufacturer-tech-spec\auto-manufacturer-tech-spec.mcd`
- Questions: `C:\Windows\Temp\mcd_q16_c28408bf8f3f498f9e1c7198f9304f19.jsonl`
- MCD CLI: `mcd`
- MCD CLI available: `True`
- MCD tool reference: aligned compact CLI docs with Python fallback
- Max tool steps: `8`

| Provider | Model | Passed | Failed | Scored | Total | Pass rate | Errors |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| openai | `gpt-5.4` | 0 | 1 | 1 | 1 | 0.0% | 0 |

| Provider | Input tokens | Output tokens | Total tokens | Total seconds | Avg seconds |
| --- | ---: | ---: | ---: | ---: | ---: |
| openai | 6,306 | 486 | 6,792 | 8.6 sec | 8.6 sec |

## openai Answers

| # | Status | Seconds | Question | Answer |
| ---: | --- | ---: | --- | --- |
| 1 | FAIL | 8.6 sec | Main.md says high-output V50D calibrations require battery coolant flow above 15 L/min. What is the highest-power V50D calibration, and how many battery packs exceed 15 L/min? Include the max-coolant pack. | High-output rule used: engine_family = V50D and battery coolant threshold coolant_flow_l_min > 15 L/min. Highest-power V50D calibration is calibration_id CAL-00017 on platform_code PX63 with peak_power_kw 1137.9. Battery packs exceeding coolant_flow_l_min > 15: 618. Max-coolant pack among those i... |
