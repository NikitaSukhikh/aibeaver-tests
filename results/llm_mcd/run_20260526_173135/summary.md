# LLM MCD Evaluation

- Created at: `2026-05-26T17:31:35`
- MCD package: `D:\aibeaver-tests\datasets\auto-manufacturer-tech-spec\auto-manufacturer-tech-spec.mcd`
- Questions: `D:\aibeaver-tests\datasets\auto-manufacturer-tech-spec\qa_pilot_questions_20.jsonl`
- Token accounting: `provider API usage fields; provider/model native tokenizer; no local tokenizer or tiktoken estimate`
- MCD MCP: `C:\Users\Nikita\.cargo\bin\mcd-mcp.exe`
- MCD MCP available: `True`
- MCD CLI: `mcd`
- MCD CLI available: `True`
- MCD tool reference: MCP-first read-only MCD tools with persistent state
- Max tool steps: `20`
- OpenAI stateful responses: `False`

| Provider | Model | Passed | Failed | Scored | Total | Pass rate | Errors |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| xai | `grok-4.3` | 12 | 8 | 20 | 20 | 60.0% | 0 |

| Provider | Input tokens | Output tokens | Total tokens | Total seconds | Avg seconds |
| --- | ---: | ---: | ---: | ---: | ---: |
| xai | 238,205 | 3,806 | 262,063 | 370.0 sec | 18.5 sec |

| Provider | Total tool calls | Avg per question |
| --- | ---: | ---: |
| xai | 37 | 1.85 |

## xai Answers

| # | Status | Seconds | Calls | Question | Answer |
| ---: | --- | ---: | ---: | --- | --- |
| 1 | PASS | 22.3 sec | 2 | Join chassis_brake_validation_specs to vehicle_variant_configuration_specs. Which validation test has the shortest stop_distance_100_0_m? Return test_id, vehicle_variant, stop distance, body_style, trim_level, and curb_mass_kg. | test_id=CHS-00982, vehicle_variant=OAM-V0307, stop_distance_100_0_m=32.81, body_style=suv, trim_level=Sport, curb_mass_kg=1979 |
| 2 | PASS | 9.1 sec | 1 | Among vehicle variants that appear in chassis_brake_validation_specs, which referenced variant has the highest tow_rating_kg? Return the chassis test_id, variant_id, tow rating, stop distance, body_style, and trim_level. | test_id: CHS-00551, variant_id: OAM-V0202, tow_rating_kg: 3447, stop_distance_100_0_m: 36.93, body_style: liftback, trim_level: Executive |
| 3 | FAIL | 32.7 sec | 1 | The dossier says variants with tow_rating_kg above 2000 must demonstrate stop_distance_100_0_m below 40 m. After joining chassis tests to vehicle variants, how many rows violate that rule, and which violating row has the worst stop distance? | 61 rows violate the rule. The violating row with the worst stop distance is variant_id=OAM-V0108, test_id=CHS-00251 (tow_rating_kg=3069, stop_distance_100_0_m=42.49) |
| 4 | PASS | 10.5 sec | 1 | For variants with tow_rating_kg above 2000 that satisfy the dossier's below-40 m braking rule, which joined chassis row has the shortest stop distance? Include test_id, variant_id, tow rating, stop distance, body_style, and trim_level. | test_id=CHS-00037, variant_id=OAM-V0524, tow_rating_kg=2758, stop_distance_100_0_m=32.82, body_style=sedan, trim_level=Performance |
| 5 | PASS | 7.2 sec | 1 | The dossier says Sport trim variants must stop below 35 m. After joining chassis tests to vehicle variants, how many Sport rows fail that threshold, and which failure has the worst stop distance? | 95 Sport rows fail; worst is OAM-V0042 (CHS-00027) at 42.49 m |
| 6 | PASS | 10.9 sec | 2 | Which chassis validation tests share the maximum lateral_grip_g, and what trim_level and body_style do their referenced vehicle variants have? | CHS-00246 (OAM-V0873, Base, wagon) and CHS-00833 (OAM-V0990, Executive, liftback) share max lateral_grip_g=1.08 |
| 7 | FAIL | 88.6 sec | 2 | The dossier says spring rates scale with curb_mass_kg plus max_payload_kg. In the chassis-to-vehicle join, which validation row has the largest curb+payload total, and what are its front and rear spring rates? | CHS-00022 (OAM-V0459) with total_mass 3037, front 43.9 n/mm, rear 53.1 n/mm |
| 8 | PASS | 8.5 sec | 2 | Using the brake-energy basis in main.md and the chassis-to-vehicle join, which validated vehicle has the highest curb_mass_kg? Return test_id, variant_id, curb mass, stop distance, rotor sizes, and brake energy in MJ rounded to three decimals. | test_id=CHS-00443, variant_id=OAM-V0733, curb_mass_kg=2441, stop_distance_100_0_m=41.49, rotor_front_mm=420, rotor_rear_mm=380, brake_energy_mj=0.942 |
| 9 | FAIL | 42.3 sec | 2 | The dossier says leaf-solid configurations are mandatory for pickup variants with tow_rating_kg above 2000. In the chassis-to-vehicle join, how many pickup rows violate this, and what is the first listed violation? | 24 violations; first listed: test_id=CHS-00004, variant_id=OAM-V0313, tow_rating_kg=2166, axle_config=doublewishbone-multilink |
| 10 | FAIL | 12.8 sec | 2 | The dossier says air-multilink suspensions pair with Executive and Premium trims. After joining chassis tests to vehicle trims, how many rows are air-multilink with Executive/Premium, and which of those has the highest stability_margin_pct? | 66 rows; CHS-00939 (OAM-V0850, Premium, 22.11%) |
| 11 | PASS | 7.6 sec | 1 | Main.md says each chassis validation test must reference a valid vehicle variant. How many chassis rows resolve to vehicle_variant_configuration_specs.variant_id, and how many invalid references are there? | 1000 chassis rows resolve to vehicle_variant_configuration_specs.variant_id (all valid); 0 invalid references |
| 12 | FAIL | 11.2 sec | 2 | Main.md says homologation_code prefixes must match the region field. In vehicle_variant_configuration_specs, how many variants violate that rule, and what is the first listed mismatch? | 897 variants violate the rule; first listed mismatch is variant_id OAM-V0001 (region KR, homologation_code AU-2025-3016) |
| 13 | FAIL | 10.2 sec | 1 | Main.md says lots achieve release_status=released only when battery_health_score_pct exceeds 96 and warranty_risk_index is below 2.0. How many released lots violate either threshold? | 0 |
| 14 | FAIL | 10.0 sec | 2 | Using the same production release thresholds from main.md, how many non-released lots still pass battery_health_score_pct > 96 and warranty_risk_index < 2.0? Include the first containment example and first hold example in file order. | 18 non-released lots pass (battery_health_score_pct > 96 and warranty_risk_index < 2.0). First containment: LOT-00074. First hold: LOT-00246. |
| 15 | FAIL | 17.8 sec | 4 | Main.md says production build_date must follow calibration production_release_date. Compare the earliest production lot build date to the earliest calibration release date. Is any production lot earlier than the earliest calibration release, and which rows establish this? | Yes, earliest production build 2024-01-01 (LOT-00363 from production_quality_measurements) precedes earliest calibration release 2024-01-02 (from powertrain_calibration_specs). |
| 16 | PASS | 18.8 sec | 3 | Main.md says high-output V50D calibrations require battery coolant flow above 15 L/min and ties coolant sizing to thermal_limit_deg_c. What is the highest-power V50D calibration? Return calibration_id, engine_family, peak_power_kw, thermal_limit_deg_c, how many battery packs exceed 15 L/min, and the max-coolant pack. | CAL-00017 \| V50D \| 1137.9 kW \| 118.8 °C \| 618 packs \| BAT-00026 (24.0 L/min) |
| 17 | PASS | 19.0 sec | 3 | Main.md says chassis tests with lateral_grip_g above 1.0 require NMC811 or NMC622 battery packs with peak_discharge_kw above 1500. How many high-grip chassis tests are there, and how many battery packs meet that chemistry/discharge condition by chemistry? | 327 high-grip chassis tests; 136 battery packs total (NMC622:65, NMC811:71) |
| 18 | PASS | 7.7 sec | 1 | Main.md says NMC811 packs support Performance trim vehicles requiring peak_discharge_kw above 1000. How many Performance variants exist, how many NMC811 packs exceed 1000 kW, and which NMC811 pack has the highest peak discharge? | 156 Performance variants; 134 NMC811 packs exceed 1000 kW; BAT-00293 (NMC811, 4298.4 kW) has the highest peak discharge |
| 19 | PASS | 16.5 sec | 3 | Main.md says LFP packs are specified for Fleet trim variants. How many Fleet vehicle variants and LFP battery packs are present, and which LFP pack has the highest estimated_range_km? | 140 Fleet vehicle variants, 218 LFP battery packs; BAT-00187 (3630 km) |
| 20 | PASS | 6.2 sec | 1 | Main.md lists the six manufacturing plants. Using production_quality_measurements, which three plant_code values have the most production lots and what are their counts? | KOB1:174, DET1:173, MEX2:172 |
