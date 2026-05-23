# About the Auto Manufacturer Tech Spec Questions

This pilot question set is designed to test whether an LLM agent can reason across the full Orion Apex Motors source package, not just retrieve isolated values from one CSV. The ground truth is split across narrative rules in `main.md` and structured rows in the vehicle, chassis, powertrain, battery, and production tables. A correct answer often requires finding a relationship in the dossier text, then applying it to one or more tables.

## Why Cross-File Questions Matter

Single-table extrema such as "highest tow rating" or "lowest drag coefficient" mostly test lookup and sorting. Those are useful baseline checks, but they do not show whether an agent understands the specification as a connected technical dossier.

The revised pilot questions instead exercise skills that matter for real correctness evaluation:

- Resolving references, such as `chassis_brake_validation_specs.vehicle_variant` to `vehicle_variant_configuration_specs.variant_id`.
- Applying rules stated only in narrative text, such as braking thresholds for high-tow or Sport variants.
- Combining constraints across domains, such as powertrain cooling requirements with battery coolant capacity.
- Auditing data consistency, such as homologation prefixes, release thresholds, and date ordering.
- Producing answers with enough context to prove the join or rule was applied, not guessed from a single field.

## Question Families

### Chassis and Vehicle Joins

Families such as `auto_pilot_shortest_stop_variant_context`, `auto_pilot_validated_top_tow_context`, and `auto_pilot_max_lateral_grip_variant_context` require joining chassis validation rows to vehicle configuration rows. These questions verify that the agent can follow the dossier's primary row-level dependency and report both test data and inherited vehicle context.

### Rule-Based Brake Validation

Families such as `auto_pilot_tow_stop_rule_violations`, `auto_pilot_high_tow_best_pass`, and `auto_pilot_sport_stop_threshold` combine thresholds from `main.md` with numeric fields from chassis and vehicle tables. They test whether the agent can distinguish a raw best value from a value that passes or fails a specification rule.

### Mass, Payload, and Brake Energy

Families such as `auto_pilot_max_loaded_mass_spring_context` and `auto_pilot_brake_energy_heaviest_validated` require calculations after joining files. They check that the agent can compute derived engineering quantities, then tie the result back to the relevant source rows.

### Suspension and Variant Compatibility

Families such as `auto_pilot_pickup_leaf_solid_rule_violations` and `auto_pilot_air_multilink_exec_premium` apply body-style and trim-level rules from the dossier to chassis axle configuration data. These are useful for detecting agents that miss narrative constraints or answer from the chassis table alone.

### Referential and Metadata Integrity

Families such as `auto_pilot_chassis_variant_reference_integrity` and `auto_pilot_homologation_region_mismatch` evaluate whether the agent can audit consistency across identifiers and coded fields. These questions are important because real technical datasets often fail through broken references or inconsistent metadata, not only wrong numeric values.

### Production Quality Gates

Families such as `auto_pilot_released_quality_gate_check`, `auto_pilot_nonreleased_pass_quality_gate`, and `auto_pilot_earliest_build_vs_release` combine production records with release criteria or dates described in the dossier. They test whether the agent can reason from process rules to table-level exceptions.

### Powertrain, Battery, and Performance Support

Families such as `auto_pilot_v50d_coolant_candidates`, `auto_pilot_high_grip_battery_candidates`, `auto_pilot_performance_nmc811_support`, and `auto_pilot_lfp_fleet_alignment` connect powertrain, battery, vehicle trim, and chassis performance requirements. These questions check whether the model can use the dossier as a system specification rather than a set of independent tables.

### Plant-Level Production Context

The `auto_pilot_production_plant_volume` family uses plant codes introduced in the narrative and counts them in the production table. This is a lighter cross-file check, but it still verifies that the agent grounds coded production data in the documented manufacturing context.

## Evaluation Signal

The expected answers intentionally include identifiers and context fields, not just final counts. For example, a question may require a violation count plus the worst offending `test_id`, `variant_id`, threshold value, and measured value. This makes it harder for a model to pass through partial retrieval or coincidence.

A strong agent should:

- Locate the relevant rule or relationship in the markdown.
- Load the correct tables.
- Join or filter using the documented keys.
- Compute counts, maxima, minima, or derived values accurately.
- Return enough row context to demonstrate the reasoning path.

A weaker agent will often answer with a plausible single-table result, omit tied rows, ignore thresholds from the narrative, or provide counts without the source identifiers needed to verify them.
