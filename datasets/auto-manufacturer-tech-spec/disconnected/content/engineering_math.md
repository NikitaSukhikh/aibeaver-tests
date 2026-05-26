# Engineering Math Reference

Use this page for unit-sensitive calculations. Convert inputs to the required units before substituting values into formulas; do not square or multiply source-display units directly when the formula requires SI units.

| Calculation | Formula | Required inputs | Output | SQL/Python expression |
| --- | --- | --- | --- | --- |
| Speed conversion | `v_m_s = speed_kmh / 3.6` | `speed_kmh` in km/h | m/s | `speed_kmh / 3.6` |
| Brake energy for one stop | `E_MJ = 0.5 * mass_kg * (speed_kmh / 3.6)^2 / 1e6` | `mass_kg`, `speed_kmh` | MJ | `0.5 * mass_kg * (speed_kmh / 3.6) * (speed_kmh / 3.6) / 1000000.0` |
| Added aero drag force | `F_N = 0.5 * rho * delta_Cd * frontal_area_m2 * (speed_kmh / 3.6)^2` | `rho`, `delta_Cd`, `frontal_area_m2`, `speed_kmh` | N | `0.5 * rho * delta_cd * area * (speed_kmh / 3.6) * (speed_kmh / 3.6)` |
| Added road-load power | `P_kW = force_N * (speed_kmh / 3.6) / 1000` | `force_N`, `speed_kmh` | kW | `force_n * (speed_kmh / 3.6) / 1000.0` |
| Battery gross energy | `E_kWh = series_cells * parallel_cells * cell_nominal_voltage_v * cell_capacity_ah / 1000` | cell topology and cell electrical values | kWh | `series_cells * parallel_cells * cell_nominal_voltage_v * cell_capacity_ah / 1000.0` |
| Usable window capacity | `usable_kWh = capacity_kwh * usable_ratio` | gross capacity and decimal ratio | kWh | `capacity_kwh * usable_ratio` |
| Range at unchanged consumption | `new_range_km = current_range_km * new_usable_kwh / current_usable_kwh` | current range, current usable capacity, new usable capacity | km | `current_range_km * new_usable_kwh / current_usable_kwh` |
| GCWR reserve | `reserve_kg = gcwr_kg - curb_mass_kg - max_payload_kg - braked_trailer_rating_kg` | kg fields | kg | `gcwr_kg - curb_mass_kg - max_payload_kg - braked_trailer_rating_kg` |
| Power from torque and rpm | `P_kW = torque_nm * rpm / 9549` | torque and rpm | kW | `torque_nm * rpm / 9549.0` |
| RPM from power and torque | `rpm = peak_power_kw * 9549 / peak_torque_nm` | power and torque | rpm | `peak_power_kw * 9549.0 / peak_torque_nm` |
| Percent scaling | `new_value = value * (1 + percent_change / 100)` | value and signed percent | same as value | `value * (1.0 + percent_change / 100.0)` |

Example brake-energy substitution for `curb_mass_kg = 3647` at `100 km/h`:

```text
v = 100 / 3.6 = 27.7778 m/s
E = 0.5 * 3647 * 27.7778^2 / 1,000,000 = 1.407 MJ
```

The value `18.235 MJ` is the result of incorrectly using `100` as metres per second. That is a unit error.

