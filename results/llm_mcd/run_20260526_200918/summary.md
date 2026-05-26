# LLM MCD Evaluation

- Created at: `2026-05-26T20:09:18`
- MCD package: `D:\aibeaver-tests\datasets\auto-manufacturer-tech-spec\auto-manufacturer-tech-spec.mcd`
- Questions: `D:\aibeaver-tests\datasets\auto-manufacturer-tech-spec\qa_pilot_questions_20.jsonl`
- Token accounting: `provider API usage fields; provider/model native tokenizer; no local tokenizer or tiktoken estimate`
- MCD MCP: `C:\Users\Nikita\.cargo\bin\mcd-mcp.exe`
- MCD MCP available: `True`
- MCD CLI: `mcd`
- MCD CLI available: `True`
- MCD tool reference: MCP-first read-only MCD tools with persistent state
- Scoring mode: `programmatic`
- Judge provider: `n/a`
- Judge model override: `n/a`
- Token usage includes judge calls: `False`
- Max tool steps: `20`
- OpenAI stateful responses: `False`

| Provider | Model | Passed | Failed | Scored | Total | Pass rate | Errors |
| --- | --- | ---: | ---: | ---: | ---: | ---: | ---: |
| openai | `gpt-5.4` | 19 | 1 | 20 | 20 | 95.0% | 0 |

| Provider | Input tokens | Output tokens | Total tokens | Total seconds | Avg seconds |
| --- | ---: | ---: | ---: | ---: | ---: |
| openai | 204,389 | 6,854 | 211,243 | 130.3 sec | 6.5 sec |

| Provider | Total tool calls | Avg per question |
| --- | ---: | ---: |
| openai | 25 | 1.25 |

## openai Answers

| # | Status | Seconds | Calls | Question | Answer |
| ---: | --- | ---: | ---: | --- | --- |
| 1 | PASS | 7.5 sec | 1 | Join chassis_brake_validation_specs to vehicle_variant_configuration_specs. Which validation test has the shortest stop_distance_100_0_m? Return test_id, vehicle_variant, stop distance, body_style, trim_level, and curb_mass_kg. | test_id=CHS-00542, vehicle_variant=OAM-V0320, stop_distance_100_0_m=34.0, body_style=wagon, trim_level=Performance, curb_mass_kg=2166 |
| 2 | PASS | 5.4 sec | 1 | Among vehicle variants that appear in chassis_brake_validation_specs, which referenced variant has the highest tow_rating_kg? Return the chassis test_id, variant_id, tow rating, stop distance, body_style, and trim_level. | Among vehicle variants referenced by chassis_brake_validation_specs (1000 referenced chassis tests), the highest tow_rating_kg is for chassis test_id CHS-00327, variant_id OAM-V0898. tow_rating_kg=6006, stop_distance_100_0_m=52.94, body_style=pickup, trim_level=Base. |
| 3 | PASS | 8.3 sec | 1 | For joined rows with tow_rating_kg above 2000 and at least one false validation flag, which row has the worst gcwr_stop_distance_m? | Among joined rows with tow_rating_kg > 2000 and at least one false validation flag, the worst gcwr_stop_distance_m is test_id CHS-00009 for vehicle_variant/variant_id OAM-V0583. candidate_count=141, tow_rating_kg=2677, gcwr_stop_distance_m=79.47, regulatory_brake_pass=1, fade_test_pass=0, trailer... |
| 4 | PASS | 5.3 sec | 1 | For joined rows with tow_rating_kg above 2000 where regulatory_brake_pass, fade_test_pass, trailer_stability_pass, and grade_launch_pass are all true, which row has the shortest stop_distance_100_0_m? Return test_id, variant_id, tow rating, stop distance, body_style, and trim_level. | test_id CHS-00127; variant_id OAM-V0102; tow_rating_kg 2025; stop_distance_100_0_m 36.67; body_style wagon; trim_level Sport. |
| 5 | PASS | 9.2 sec | 3 | After joining chassis tests to vehicle variants, which Sport row has the worst stop_distance_100_0_m? | The worst Sport row is test_id CHS-00577 for vehicle_variant/variant_id OAM-V0501, with trim_level Sport and stop_distance_100_0_m of 53.08. |
| 6 | PASS | 5.9 sec | 1 | Main.md defines gross battery energy as series_cells * parallel_cells * cell_nominal_voltage_v * cell_capacity_ah / 1000. Recompute this for every battery pack and find the row with the largest absolute difference from capacity_kwh due to rounding. Return pack_id, chemistry, series_cells, parallel_cells, cell_nominal_voltage_v, cell_capacity_ah, stored capacity_kwh, recomputed gross kWh rounded to three decimals, and the absolute difference rounded to four decimals. | The battery pack with the largest absolute difference is pack_id BAT-00807. chemistry: NMC622; series_cells: 192; parallel_cells: 4; cell_nominal_voltage_v: 3.65; cell_capacity_ah: 51.31; stored capacity_kwh: 143.85; recomputed gross kWh: 143.832; absolute difference: 0.0178. |
| 7 | PASS | 5.9 sec | 1 | In the chassis-to-vehicle join, find the validation row with the largest curb_mass_kg + max_payload_kg total. Return the row context and spring rates. | The chassis-to-vehicle joined validation row with the largest curb_mass_kg + max_payload_kg total is test_id CHS-00755 for vehicle_variant/variant_id OAM-V0391. Context: curb_mass_kg=3615, max_payload_kg=1584, total_loaded_mass_kg=5199.0, axle_config=leaf-solid, tire_size=235/65R16C, stop_distanc... |
| 8 | PASS | 12.0 sec | 3 | Using the brake-energy basis in main.md and the chassis-to-vehicle join, which validated vehicle has the highest curb_mass_kg? Return test_id, variant_id, curb mass, stop distance, rotor sizes, and brake energy in MJ rounded to three decimals. | Validated by regulatory_brake_pass and fade_test_pass, the vehicle with the highest curb_mass_kg is test_id CHS-00190 for variant_id OAM-V0210. Curb mass: 3647.0 kg; stop distance: 49.69 m; rotor sizes: 430.0 mm front / 385.0 mm rear; brake energy: 1.407 MJ. |
| 9 | FAIL | 4.9 sec | 1 | In the chassis-to-vehicle join, how many pickup or van rows with max_payload_kg above 750 use a non-leaf-solid axle_config? | 0 |
| 10 | PASS | 4.5 sec | 1 | Among joined rows where axle_config is air-multilink and trim_level is Executive or Premium, which row has the highest stability_margin_pct? | Among 228 joined rows with axle_config='air-multilink' and trim_level in ('Executive','Premium'), the highest stability_margin_pct is test_id CHS-00368 for vehicle_variant OAM-V0998, trim_level Executive, with stability_margin_pct 23.93. |
| 11 | PASS | 5.0 sec | 1 | Using vehicle_variant_configuration_specs, group AU, EU, NA, and UK variants by region and report each region count with its test_cycle and procedure_standard. | Total AU/EU/NA/UK variants: 503. By region: AU — 135 variants, test_cycle: ADR 81/02 WLTP transition, procedure_standard: Australian Design Rules fuel consumption procedure; EU — 121 variants, test_cycle: WLTP, procedure_standard: UNECE R154; NA — 127 variants, test_cycle: EPA FTP-75/HWFET/US06, ... |
| 12 | PASS | 6.3 sec | 2 | In vehicle_variant_configuration_specs, how many variants violate the rule that homologation_code prefixes match the region field? | 0 variants violate the rule that the homologation_code prefix must match the region field in vehicle_variant_configuration_specs. |
| 13 | PASS | 5.9 sec | 1 | Main.md says released production lots depend on PPAP status, containment status, traceability, capability indices, MSA result, and battery-health trend. How many released lots are there, and how many violate the gates ppap_status=approved, containment_status=closed, supplier_lot_traceability=complete, cpk_min>=1.33, ppk_min>=1.20, msa_grr_pct<=10, and battery_health_score_pct>=96.5? | There are 596 released lots in production_quality_measurements (release_status='released'). Of those, 0 violate the stated release gates: ppap_status='approved', containment_status='closed', supplier_lot_traceability='complete', cpk_min>=1.33, ppk_min>=1.20, msa_grr_pct<=10, and battery_health_sc... |
| 14 | PASS | 4.0 sec | 1 | Among non-released production lots with ppap_status=approved, what is the first containment example in file order? | There are 136 non-released production lots with ppap_status=approved. The first containment example in file order is lot_id LOT-00018 with release_status=containment, ppap_status=approved, containment_status=open, and supplier_lot_traceability=partial. |
| 15 | PASS | 7.2 sec | 1 | After joining chassis tests to vehicle variants, compute GCWR reserve as gcwr_kg - curb_mass_kg - max_payload_kg - braked_trailer_rating_kg. Which joined row has the largest reserve? | Among 1000 joined chassis-test/vehicle-variant rows, the largest GCWR reserve is on test_id CHS-00205 joined to vehicle_variant OAM-V0233 (variant_id OAM-V0233). Using gcwr_kg - curb_mass_kg - max_payload_kg - braked_trailer_rating_kg = 2434 - 1680 - 504 - 0, the GCWR reserve is 250.0 kg. |
| 16 | PASS | 10.9 sec | 1 | The revised dossier treats coolant flow and heat rejection as thermal-sizing evidence rather than a single engine-family threshold. What is the highest-power V50D calibration? Return calibration_id, engine_family, peak_power_kw, thermal_limit_deg_c, how many battery packs exceed 15 L/min coolant flow, the max-coolant pack, and the max heat-rejection pack. | calibration_id CAL-00498; engine_family V50D; peak_power_kw 429.3; thermal_limit_deg_c 121.8; battery packs exceeding 15 L/min coolant flow: 251; max-coolant pack: BAT-00066 (chemistry NMC622, peak_discharge_kw 1148.4, capacity_kwh 160.9, usable_capacity_kwh 148.02, coolant_flow_l_min 24.0); max ... |
| 17 | PASS | 4.2 sec | 1 | Among chassis tests with lateral_grip_g above 1.0, what is the trim_level distribution? | Among chassis tests with lateral_grip_g > 1.0, there are 111 tests total. Trim-level distribution: Performance 89, Sport 22. |
| 18 | PASS | 6.0 sec | 1 | Among NMC811 battery packs with peak_discharge_kw above 1000, which pack has the highest peak_discharge_kw? | Among NMC811 battery packs with peak_discharge_kw above 1000, the highest peak_discharge_kw pack is BAT-00124. Candidate count: 19. chemistry: NMC811; peak_discharge_kw: 1300.0; capacity_kwh: 157.06; usable_capacity_kwh: 142.92. |
| 19 | PASS | 4.3 sec | 1 | For each battery chemistry, compute the pack count and average usable_capacity_kwh / capacity_kwh ratio. | By chemistry (4 chemistry groups total): LFP — pack_count 218, avg usable_capacity_kwh/capacity_kwh ratio 0.9400041768885389; LMFP — pack_count 280, avg ratio 0.9399990780529383; NMC622 — pack_count 249, avg ratio 0.9199995840748367; NMC811 — pack_count 253, avg ratio 0.9099976240601215. |
| 20 | PASS | 7.5 sec | 1 | Among non-released production lots where an approved lot fails only the battery-health gate, what is the first such lot? | The first non-released production lot that is approved and fails only the battery-health gate is LOT-00069. It matches the other release gates with release_status=hold, ppap_status=approved, containment_status=closed, supplier_lot_traceability=complete, cpk_min=2.02, ppk_min=1.93, and msa_grr_pct... |
